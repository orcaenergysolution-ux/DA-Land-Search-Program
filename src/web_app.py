"""Local web GUI for the transmission-line property finder.

Serves web/index.html and runs the find_properties pipeline behind it, so a
non-technical user can set parameters in a browser and click Run. The Apify
token stays on this machine (never sent to the browser).

Start it with run_app.bat, or:
    python src/web_app.py
then open http://localhost:8000
"""
from __future__ import annotations
import json
import sys
import threading
import traceback
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
import find_properties as fp    # noqa: E402
import find_parcels as fpar    # noqa: E402

WEB = ROOT / "web"
TOKEN_FILE = ROOT / "data" / "apify_token.txt"
PORT = 8000
USD_PER_RESULT = 0.0047   # measured from real runs

JOB = {"running": False, "done": False, "log": [], "results": [], "error": None,
       "files": {}, "cost_note": "", "mode": "parcels"}


LOG_KEEP = 200   # keep the tail only: status polling sends the whole log each time


def log(msg):
    JOB["log"].append(str(msg))
    if len(JOB["log"]) > LOG_KEEP:
        del JOB["log"][:-LOG_KEEP]
    print(msg, file=sys.stderr)


def get_token():
    import os
    tok = os.environ.get("APIFY_TOKEN", "").strip()
    if tok:
        return tok
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ""


def parse_locations(p, state):
    """Locations from the derived 66 kV town list, or a custom textarea."""
    if p.get("location_mode") == "custom" and p.get("custom_locations", "").strip():
        raw = [x.strip() for x in p["custom_locations"].replace("\n", ",").split(",")]
    else:
        f = ROOT / "data" / "intermediate" / f"lines_suburbs_{state}.txt"
        if not f.exists():
            raise RuntimeError(
                f"No derived town list for {state}. Run:  "
                f"python src/lines_to_suburbs.py --state {state}")
        raw = [x.strip() for x in f.read_text(encoding="utf-8").splitlines()]
    locs, seen = [], set()
    for part in raw:
        if not part or part in seen or part.startswith("#"):
            continue
        seen.add(part)
        if ":" in part:
            sub, st = part.split(":", 1)
            locs.append({"suburb": sub.strip(), "state": st.strip()})
        else:
            locs.append({"suburb": part, "state": state})
    return locs


def run_job(p):
    try:
        JOB.update(running=True, done=False, error=None, log=[], results=[], files={})
        state = p["state"]
        voltages = [float(v) for v in p["voltages"]]
        min_land = float(p["min_land"])
        max_dist = float(p["max_distance"])
        max_nb = int(p["max_neighbors"])
        nb_radius = float(p["neighbor_radius"])

        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

        # ---- cadastral parcels: every block of land, on-market or not (free)
        # (handled first: find_parcels.scan loads the lines itself)
        if p["source"] == "parcels":
            JOB["mode"] = "parcels"
            towns = []
            if p.get("location_mode") == "custom" and p.get("custom_locations", "").strip():
                towns = [t.strip() for t in
                         p["custom_locations"].replace("\n", ",").split(",") if t.strip()]
            a = SimpleNamespace(
                state=state, voltages=voltages, voltage_tol=0.5,
                min_land=min_land, max_distance=max_dist,
                tile=float(p.get("tile", 0.02)), step=50.0,
                max_tiles=int(p.get("max_tiles", 0)),
                towns=towns, town_radius=float(p.get("town_radius", 10)),
                max_results=int(p.get("max_results", 100) or 0),
                max_neighbors=max_nb, neighbor_radius=nb_radius)
            rows = fpar.scan(a, progress=log)
            md, cs = fpar.write_reports(rows, a, stamp)
            JOB["files"] = {"md": md, "csv": cs}
            JOB["results"] = rows
            JOB["cost_note"] = "Free - Victorian open data. No credit used."
            log(f"Done - {len(rows)} parcels.")
            return

        JOB["mode"] = "listings"
        # Never fall through to the PAID path on an unrecognised source.
        if p["source"] not in ("saved", "scrape"):
            raise RuntimeError(f"Unknown data source {p['source']!r}. "
                               "Refusing to run (this would otherwise cost credit).")

        log(f"Loading {'/'.join(str(int(v)) for v in voltages)} kV lines for {state}...")
        segs, grid = fp.load_segments(voltages, 0.5, fp.STATE_BBOX[state])
        log(f"  {len(segs):,} line segments loaded.")
        if not segs:
            raise RuntimeError("No line segments for that voltage/state.")

        # ---- listings: saved file (free) or a fresh scrape (costs credit)
        if p["source"] == "saved":
            path = Path(p["raw_file"])
            if not path.is_absolute():
                path = fp.OUT_DIR / path.name
            items = json.loads(path.read_text(encoding="utf-8"))
            log(f"  Loaded {len(items)} saved listings from {path.name} (no cost).")
            JOB["cost_note"] = "Used saved data - $0.00 spent."
        else:
            token = get_token()
            if not token:
                raise RuntimeError(
                    "No Apify token. Put it in data/apify_token.txt or set APIFY_TOKEN.")
            locations = parse_locations(p, state)
            cap = int(p["max_listings"])
            log(f"  Scraping {len(locations)} locations, max {cap} listings "
                f"(est. ${cap * USD_PER_RESULT:.2f})...")
            args = SimpleNamespace(
                listing_type=p["listing_type"], date_range="6months",
                include_surrounding=bool(p["include_surrounding"]),
                max_listings=cap, max_pages=int(p["max_pages"]),
                property_types=p["property_types"],
                min_price=int(p["min_price"]) if p.get("min_price") else None,
                max_price=int(p["max_price"]) if p.get("max_price") else None)
            items = fp.apify_run(token, fp.build_input(args, locations))
            raw = fp.OUT_DIR / f"apify_raw_{state}_{stamp}.json"
            fp.OUT_DIR.mkdir(exist_ok=True)
            raw.write_text(json.dumps(items), encoding="utf-8")
            log(f"  Scraped {len(items)} listings -> {raw.name}")
            JOB["cost_note"] = (f"Scraped {len(items)} listings "
                                f"(~${len(items) * USD_PER_RESULT:.2f} of Apify credit).")

        # ---- filter on land + distance to line
        near, no_geo, too_small = [], 0, 0
        for it in items:
            r = fp.extract(it)
            if r["lat"] is None or r["lon"] is None:
                no_geo += 1
                continue
            if r["land"] is None or r["land"] < min_land:
                too_small += 1
                continue
            d, props = fp.nearest_line(r["lat"], r["lon"], segs, grid, max_dist)
            if d is None:
                continue
            r["dist"] = d
            r["line_v"] = (props or {}).get("voltage_kv", "")
            r["line_name"] = (props or {}).get("name", "")
            near.append(r)
        log(f"  {len(near)} pass land + distance "
            f"({too_small} too small, {no_geo} without coordinates).")

        # ---- neighbours
        rows = []
        for i, r in enumerate(near, 1):
            if max_nb < 0:
                r["neighbours"] = None
            else:
                log(f"  Checking neighbours {i}/{len(near)}...")
                r["neighbours"] = fp.neighbour_count(r["lat"], r["lon"], nb_radius)
                import time
                time.sleep(1)
                if r["neighbours"] is not None and r["neighbours"] > max_nb:
                    continue
            rows.append(r)

        rows.sort(key=lambda r: (r["price"] is None, r["price"] or 0.0))
        cap = int(p.get("max_results", 100) or 0)
        if cap and len(rows) > cap:
            log(f"  Keeping the {cap} cheapest of {len(rows)} matches.")
            rows = rows[:cap]

        rep_args = SimpleNamespace(state=state, voltages=voltages, min_land=min_land,
                                   max_distance=max_dist, max_neighbors=max_nb,
                                   neighbor_radius=nb_radius)
        fp.write_reports(rows, rep_args, stamp)
        JOB["files"] = {"md": f"property_candidates_{state}_{stamp}.md",
                        "csv": f"property_candidates_{state}_{stamp}.csv"}
        JOB["results"] = rows
        log(f"Done - {len(rows)} matching properties.")
    except Exception as e:
        JOB["error"] = f"{e}"
        log("ERROR: " + str(e))
        traceback.print_exc()
    finally:
        JOB["running"] = False
        JOB["done"] = True


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else str(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass   # quiet

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            return self._send(200, (WEB / "index.html").read_bytes(),
                              "text/html; charset=utf-8")
        if path == "/api/config":
            raws = sorted((f.name for f in fp.OUT_DIR.glob("apify_raw_*.json")),
                          reverse=True) if fp.OUT_DIR.exists() else []
            towns = {}
            for f in (ROOT / "data" / "intermediate").glob("lines_suburbs_*.txt"):
                st = f.stem.replace("lines_suburbs_", "")
                towns[st] = len([l for l in f.read_text(encoding="utf-8").splitlines()
                                 if l.strip()])
            return self._send(200, json.dumps({
                "states": sorted(fp.STATE_BBOX), "raw_files": raws,
                "town_lists": towns, "has_token": bool(get_token()),
                "usd_per_result": USD_PER_RESULT}))
        if path == "/api/status":
            return self._send(200, json.dumps({
                "running": JOB["running"], "done": JOB["done"], "log": JOB["log"],
                "error": JOB["error"], "results": JOB["results"],
                "files": JOB["files"], "cost_note": JOB["cost_note"],
                "mode": JOB.get("mode", "listings")}))
        if path.startswith("/outputs/"):
            f = fp.OUT_DIR / Path(path).name
            if f.exists():
                return self._send(200, f.read_bytes(), "text/plain; charset=utf-8")
            return self._send(404, "not found", "text/plain")
        return self._send(404, "not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path != "/api/run":
            return self._send(404, "not found", "text/plain")
        if JOB["running"]:
            return self._send(409, json.dumps({"error": "A search is already running."}))
        n = int(self.headers.get("Content-Length", 0))
        params = json.loads(self.rfile.read(n).decode("utf-8"))
        # Reply BEFORE starting work: the job's first step parses a large GeoJSON
        # in C (holding the GIL), which would otherwise stall this response.
        self._send(200, json.dumps({"started": True}))
        threading.Thread(target=run_job, args=(params,), daemon=True).start()


class Server(ThreadingHTTPServer):
    daemon_threads = True
    # Windows lets a second process bind the same port when this is on, which
    # silently stacks up zombie servers. Force a clean "port in use" instead.
    allow_reuse_address = False


def already_running():
    """True if a working Property Finder is already serving this port."""
    from urllib.request import urlopen as _open
    try:
        _open(f"http://127.0.0.1:{PORT}/api/config", timeout=2).read()
        return True
    except Exception:
        return False


def main():
    url = f"http://localhost:{PORT}"

    if already_running():
        print("\n  Property Finder is already running - opening it in your browser.")
        print("  (You only need one copy open.)\n")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return

    try:
        srv = Server(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"\n  Port {PORT} is being held by a program that is not responding.")
        print("  Close any leftover 'Property Finder' windows and try again.")
        print("  (If that does not help, restart the computer.)\n")
        input("  Press Enter to close...")
        return

    print(f"\n  Property Finder running at {url}")
    print("  Leave this window open. Close it to stop.\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
