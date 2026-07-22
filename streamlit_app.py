"""Transmission Line Property Finder - Streamlit version.

Finds land near high-voltage power lines, either from the free Victorian
cadastre (every parcel, on-market or not) or from paid real-estate listings.

Run locally:   streamlit run streamlit_app.py
Deployed:      https://share.streamlit.io  (see DEPLOY.md)
"""
from __future__ import annotations
import csv
import io
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import streamlit as st

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
import find_properties as fp      # noqa: E402
import find_parcels as fpar       # noqa: E402

st.set_page_config(page_title="Transmission Line Property Finder",
                   page_icon="⚡", layout="wide")

USD_PER_RESULT = 0.0047
VOLTAGES = [66, 132, 220, 275, 330, 500]


def get_token() -> str:
    """Apify token from Streamlit secrets (never committed to git)."""
    try:
        return st.secrets.get("APIFY_TOKEN", "")
    except Exception:
        return ""


@st.cache_resource(show_spinner="Loading power line data...")
def load_lines(state: str, voltages: tuple, tol: float):
    """Parsed once per session - the GeoJSON is ~15 MB."""
    return fp.load_segments(list(voltages), tol, fp.STATE_BBOX[state])


def rows_to_csv(rows, mode) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    if mode == "parcels":
        w.writerow(["rank", "area_m2", "area_ha", "dist_to_line_m", "neighbours",
                    "spi", "lot", "plan", "lat", "lon", "google_maps"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, f"{r['area']:.0f}", f"{r['area']/10000:.3f}",
                        f"{r['dist']:.0f}",
                        "" if r["neighbours"] is None else r["neighbours"],
                        r["spi"], r["lot"], r["plan"], f"{r['lat']:.6f}",
                        f"{r['lon']:.6f}",
                        f"https://www.google.com/maps/search/?api=1&"
                        f"query={r['lat']:.6f},{r['lon']:.6f}"])
    else:
        w.writerow(["rank", "price", "display_price", "land_m2", "dist_to_line_m",
                    "neighbours", "type", "address", "suburb", "lat", "lon", "url"])
        for i, r in enumerate(rows, 1):
            w.writerow([i, r["price"] or "", r["display_price"],
                        "" if r["land"] is None else f"{r['land']:.0f}",
                        f"{r['dist']:.0f}",
                        "" if r["neighbours"] is None else r["neighbours"],
                        r["type"], r["address"], r["suburb"], r["lat"], r["lon"],
                        r["url"]])
    return buf.getvalue()


# ----------------------------------------------------------------- sidebar
st.title("⚡ Transmission Line Property Finder")
st.caption("Finds land close to high-voltage power lines.")

sb = st.sidebar
sb.header("Search settings")

token = get_token()
source_labels = {
    "parcels": "All land parcels — FREE (includes off-market)",
    "scrape": "Properties advertised for sale (uses paid credit)",
}
options = ["parcels"] + (["scrape"] if token else [])
source = sb.radio("What to search", options,
                  format_func=lambda k: source_labels[k])
if not token:
    sb.caption("Listings search is disabled because no Apify key is configured.")

state = sb.selectbox("State", sorted(fp.STATE_BBOX),
                     index=sorted(fp.STATE_BBOX).index("VIC"))
volts = sb.multiselect("Power line voltage (kV)", VOLTAGES, default=[66])

st.sidebar.divider()
sb.subheader("Property criteria")
max_results = sb.selectbox("How many results to find", [25, 50, 100, 250, 500, 0],
                           index=2,
                           format_func=lambda n: "No limit (slow)" if n == 0 else f"{n}")
min_land = sb.selectbox(
    "Minimum land size", [2000, 5000, 10000, 20000, 40000, 100000, 400000], index=2,
    format_func=lambda m: f"{m:,} m²  ({m/10000:g} ha)")
max_dist = sb.selectbox("Maximum distance to the line (m)",
                        [50, 100, 200, 300, 500, 1000, 2000], index=1,
                        format_func=lambda d: f"{d} m")

sb.divider()
sb.subheader("Neighbours (isolation)")
max_nb = sb.selectbox(
    "Maximum nearby buildings", [-1, 0, 2, 5, 10, 25], index=0,
    format_func=lambda n: "Don't check — fastest" if n < 0 else f"{n} or fewer")
nb_radius = sb.selectbox("Area to check", [100, 150, 250, 500], index=1,
                         format_func=lambda d: f"Within {d} m")
if max_nb >= 0:
    sb.warning("Uses a free public map service that is often busy. "
               "Can add several minutes; some results may come back unchecked.")

sb.divider()
if source == "parcels":
    sb.subheader("Where to search")
    town_mode = sb.radio("Towns", ["Everywhere along the lines", "Only towns I list"])
    towns_raw = ""
    town_radius = 10
    if town_mode == "Only towns I list":
        towns_raw = sb.text_area("Towns (one per line, or comma separated)",
                                 "Gisborne\nKilmore")
        town_radius = sb.selectbox("How far around each town (km)", [5, 10, 20, 50],
                                   index=1)
    max_tiles = sb.selectbox("How much of the state to scan",
                             [100, 400, 1200, 0], index=1,
                             format_func=lambda n: "Entire state (slowest)" if n == 0
                             else f"{n} areas")
else:
    sb.subheader("Listings options")
    ptypes = sb.multiselect("Property types",
                            ["land", "rural", "house", "townhouse", "apartment",
                             "villa", "commercial", "other"],
                            default=["land", "rural"])
    listing_type = sb.selectbox("Listing type", ["buy", "sold", "rent"])
    max_listings = sb.selectbox("Maximum listings to fetch (controls cost)",
                                [100, 200, 400, 800], index=1)
    towns_raw = sb.text_area("Towns (one per line)", "Gisborne:VIC\nKilmore:VIC")
    st.sidebar.info(f"Estimated cost: up to **${max_listings*USD_PER_RESULT:.2f}**")

run = sb.button("🔎 Search", type="primary", use_container_width=True)


# -------------------------------------------------------------------- run
if run:
    if not volts:
        st.error("Pick at least one voltage.")
        st.stop()

    segs, grid = load_lines(state, tuple(float(v) for v in volts), 0.5)
    if not segs:
        st.error(f"No {volts} kV lines found for {state}.")
        st.stop()

    log_box = st.empty()
    lines: list[str] = []

    def progress(msg):
        lines.append(str(msg))
        log_box.code("\n".join(lines[-12:]))

    try:
        if source == "parcels":
            towns = [t.strip() for t in towns_raw.replace("\n", ",").split(",")
                     if t.strip()] if town_mode == "Only towns I list" else []
            args = SimpleNamespace(
                state=state, voltages=[float(v) for v in volts], voltage_tol=0.5,
                min_land=float(min_land), max_distance=float(max_dist),
                tile=0.02, step=50.0, max_tiles=int(max_tiles),
                towns=towns, town_radius=float(town_radius),
                max_results=int(max_results),
                max_neighbors=int(max_nb), neighbor_radius=float(nb_radius))
            with st.spinner("Searching land parcels..."):
                rows = fpar.scan(args, progress=progress, segs=segs, grid=grid)
            mode = "parcels"
        else:
            locations = []
            for part in [t.strip() for t in towns_raw.replace("\n", ",").split(",")
                         if t.strip()]:
                if ":" in part:
                    s_, st_ = part.split(":", 1)
                    locations.append({"suburb": s_.strip(), "state": st_.strip()})
                else:
                    locations.append({"suburb": part, "state": state})
            a = SimpleNamespace(
                listing_type=listing_type, date_range="6months",
                include_surrounding=False, max_listings=int(max_listings),
                max_pages=1, property_types=ptypes, min_price=None, max_price=None)
            progress(f"Scraping {len(locations)} locations...")
            with st.spinner("Fetching listings (this costs credit)..."):
                items = fp.apify_run(token, fp.build_input(a, locations))
            progress(f"{len(items)} listings fetched. Filtering...")
            rows = []
            for it in items:
                r = fp.extract(it)
                if r["lat"] is None or r["land"] is None or r["land"] < min_land:
                    continue
                d, props = fp.nearest_line(r["lat"], r["lon"], segs, grid, max_dist)
                if d is None:
                    continue
                r["dist"] = d
                r["neighbours"] = None
                rows.append(r)
            rows.sort(key=lambda r: (r["price"] is None, r["price"] or 0.0))
            if max_results:
                rows = rows[:int(max_results)]
            mode = "listings"

        st.session_state["rows"] = rows
        st.session_state["mode"] = mode
        log_box.empty()
    except Exception as ex:
        st.error(f"Search failed: {ex}")
        st.stop()


# ---------------------------------------------------------------- results
rows = st.session_state.get("rows")
mode = st.session_state.get("mode", "parcels")

if rows is None:
    st.info("Set your criteria in the sidebar, then press **Search**.\n\n"
            "**All land parcels** searches every block of land in the Victorian "
            "cadastre — including land that is *not* for sale. It is free.")
elif not rows:
    st.warning("Nothing matched. Try a larger distance, a smaller minimum land "
               "size, or a bigger scan area.")
else:
    if mode == "parcels":
        st.success(f"Found **{len(rows)}** land parcels. "
                   "Free — Victorian open data, no credit used.")
        table = [{
            "#": i,
            "Area (m²)": round(r["area"]),
            "Hectares": round(r["area"] / 10000, 2),
            "Distance (m)": round(r["dist"]),
            "Neighbours": "—" if r["neighbours"] is None else r["neighbours"],
            "Parcel ID (SPI)": r["spi"] or f"Lot {r['lot']} {r['plan']}".strip(),
            "Map": f"https://www.google.com/maps/search/?api=1&"
                   f"query={r['lat']:.6f},{r['lon']:.6f}",
        } for i, r in enumerate(rows, 1)]
        st.dataframe(table, use_container_width=True, hide_index=True,
                     column_config={"Map": st.column_config.LinkColumn(
                         "Map", display_text="View ↗")})
        st.caption("These are land parcels, not listings — most are NOT for sale. "
                   "Use the SPI for a title search.")
    else:
        st.success(f"Found **{len(rows)}** properties for sale.")
        table = [{
            "#": i,
            "Price": f"${r['price']:,.0f}" if r["price"] else (
                r["display_price"] or "Contact agent"),
            "Land (m²)": round(r["land"]) if r["land"] else "—",
            "Distance (m)": round(r["dist"]),
            "Type": r["type"],
            "Address": f"{r['address']}, {r['suburb']}",
            "Listing": r["url"],
        } for i, r in enumerate(rows, 1)]
        st.dataframe(table, use_container_width=True, hide_index=True,
                     column_config={"Listing": st.column_config.LinkColumn(
                         "Listing", display_text="View ↗")})

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    st.download_button("⬇ Download CSV", rows_to_csv(rows, mode),
                       file_name=f"{mode}_{state}_{stamp}.csv", mime="text/csv")
