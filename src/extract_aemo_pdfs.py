"""
Extract text + position + colour from AEMO state map PDFs.

For each PDF we:
  1. Pull every word with its (x, y) on the page and the dominant text colour.
  2. Try to detect the legend (a column of coloured swatches with stage labels)
     to build a colour -> stage map specific to that PDF.
  3. Match every word/phrase against our merged project list (projects.json)
     to flag which projects appear on which AEMO map.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
import pdfplumber

ROOT = Path(__file__).parent.parent
AEMO_DIR = ROOT / "data" / "inputs" / "aemo_maps"
INTERMEDIATE = ROOT / "data" / "intermediate"
INTERMEDIATE.mkdir(parents=True, exist_ok=True)

STATE_FROM_FILE = {
    "nsw": "NSW", "vic": "VIC", "qld": "QLD", "sa": "SA", "tas": "TAS",
    "regional": "ALL",
}


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[​\xa0]", " ", s)
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def file_state(p: Path) -> str:
    stem = p.stem.lower()
    for k, v in STATE_FROM_FILE.items():
        if k in stem:
            return v
    return "?"


def colour_to_hex(c) -> str:
    """pdfplumber 'non_stroking_color' can be tuple/list/None/single float."""
    if c is None:
        return "none"
    if isinstance(c, (int, float)):
        v = int(round(float(c) * 255))
        return f"#{v:02x}{v:02x}{v:02x}"
    if isinstance(c, (list, tuple)):
        if len(c) == 1:
            v = int(round(float(c[0]) * 255))
            return f"#{v:02x}{v:02x}{v:02x}"
        if len(c) >= 3:
            r, g, b = [int(round(float(x) * 255)) for x in c[:3]]
            return f"#{r:02x}{g:02x}{b:02x}"
        if len(c) == 4:  # CMYK
            cy, m, y, k = [float(x) for x in c]
            r = int(round(255 * (1 - cy) * (1 - k)))
            g = int(round(255 * (1 - m) * (1 - k)))
            b = int(round(255 * (1 - y) * (1 - k)))
            return f"#{r:02x}{g:02x}{b:02x}"
    return str(c)


def word_dominant_colour(page, x0, x1, top, bottom) -> str:
    """Mode colour of chars inside the word's bbox."""
    cnt = Counter()
    for ch in page.chars:
        if x0 <= ch["x0"] <= x1 and top <= ch["top"] <= bottom:
            cnt[colour_to_hex(ch.get("non_stroking_color"))] += 1
    if not cnt:
        return "none"
    return cnt.most_common(1)[0][0]


def extract_words_with_colour(pdf_path: Path) -> list[dict]:
    out: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pi, page in enumerate(pdf.pages):
            words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
            for w in words:
                col = word_dominant_colour(page, w["x0"], w["x1"], w["top"], w["bottom"])
                out.append({
                    "text": w["text"],
                    "x": (w["x0"] + w["x1"]) / 2,
                    "y": (w["top"] + w["bottom"]) / 2,
                    "x0": w["x0"], "x1": w["x1"], "top": w["top"], "bottom": w["bottom"],
                    "colour": col,
                    "page": pi,
                    "page_w": page.width,
                    "page_h": page.height,
                })
    return out


def cluster_phrases(words: list[dict], max_gap_x: float = 15, max_gap_y: float = 3) -> list[dict]:
    """Cluster adjacent words on the same baseline into phrases (e.g. 'Snowy Hydro 2.0')."""
    # sort by y, then x
    words = sorted(words, key=lambda w: (round(w["y"]/2)*2, w["x"]))
    phrases = []
    cur = None
    for w in words:
        if cur is None:
            cur = {**w, "text": w["text"]}
            continue
        if (abs(w["y"] - cur["y"]) <= max_gap_y and
            w["x0"] - cur["x1"] <= max_gap_x and
            w["colour"] == cur["colour"]):
            cur["text"] = cur["text"] + " " + w["text"]
            cur["x1"] = w["x1"]
            cur["x"] = (cur["x0"] + cur["x1"]) / 2
            continue
        phrases.append(cur)
        cur = {**w, "text": w["text"]}
    if cur is not None:
        phrases.append(cur)
    return phrases


def main():
    projects = json.loads((INTERMEDIATE / "projects.json").read_text(encoding="utf-8"))
    # build name lookups: full normalized name + token-set for fuzzy
    proj_by_key = {norm(p["site_name"]): p for p in projects}

    # also tokenized key without "battery", "bess", "energy", "storage", "solar", "farm", "stage", "hub" etc
    GENERIC = {"battery", "bess", "energy", "storage", "solar", "wind", "farm",
               "stage", "hub", "park", "project", "facility", "renewable", "power", "station"}
    def core_tokens(name: str) -> frozenset:
        toks = [t for t in norm(name).split() if t not in GENERIC and len(t) > 2]
        return frozenset(toks)
    proj_by_core: dict[frozenset, list[dict]] = defaultdict(list)
    for p in projects:
        proj_by_core[core_tokens(p["site_name"])].append(p)

    results = {}
    for pdf_path in sorted(AEMO_DIR.glob("*.pdf")):
        state = file_state(pdf_path)
        print(f"\n## {pdf_path.name}  state={state}")
        words = extract_words_with_colour(pdf_path)
        phrases = cluster_phrases(words)
        # colour distribution
        col_ct = Counter(p["colour"] for p in phrases)
        print(f"   {len(words)} words, {len(phrases)} phrases. Top colours: {col_ct.most_common(8)}")

        # match phrases to projects. To avoid town-name collisions (e.g. "Warwick"
        # vs "Warwick Solar Farm"), require either:
        #   - exact normalised name match, OR
        #   - core-token match where the project's core tokens have >=2 tokens
        #     (so "warwick" alone won't match a 1-core-token project)
        matched = []
        for ph in phrases:
            text = ph["text"].strip()
            if len(text) < 3: continue
            nkey = norm(text)
            if not nkey: continue
            hit = proj_by_key.get(nkey)
            match_type = "exact"
            if not hit:
                ct = core_tokens(text)
                if ct and len(ct) >= 2 and ct in proj_by_core and len(proj_by_core[ct]) == 1:
                    hit = proj_by_core[ct][0]
                    match_type = "core"
            if hit:
                matched.append({
                    "label": text, "x": ph["x"], "y": ph["y"],
                    "colour": ph["colour"],
                    "page_w": ph["page_w"], "page_h": ph["page_h"],
                    "matched_site": hit["site_name"],
                    "matched_region": hit["region"],
                    "matched_stage": hit["stage"],
                    "match_type": match_type,
                })
        print(f"   Matched {len(matched)} project labels (exact={sum(1 for m in matched if m['match_type']=='exact')}, core={sum(1 for m in matched if m['match_type']=='core')})")
        # show sample
        for m in matched[:10]:
            print(f"     {m['colour']} ({m['x']:.0f},{m['y']:.0f}) {m['label']!r} -> {m['matched_site']} [{m['matched_stage']}]")
        results[pdf_path.name] = {"state": state, "matches": matched, "colour_counts": col_ct.most_common(20)}

    (INTERMEDIATE / "aemo_pdf_matches.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nWrote aemo_pdf_matches.json")


if __name__ == "__main__":
    main()
