"""Integrate vision-extracted AEMO marker list into projects.json.

For each vision marker we try to match it to an existing project record by:
  1. State match
  2. Fuzzy match: `nearest_label` token overlap with site name OR location description
  3. Capacity within ±15% (or ±5 MW for sub-50 MW projects)
  4. Technology family compatibility (Wind/Solar/Hydro/Battery/etc.)

When matched, we:
  - set `vision_stage` to the AEMO map's stage (Application, Pre-Registration,
    Registration, Commissioning, Operational)
  - upgrade `stage` per brief rules: AEMO map is authoritative

Unmatched vision markers are surfaced as new pseudo-projects so the map shows
them too. They get `source: "AEMO map (unmatched)"` and approximate region
centroid coords.

Output: updates projects.json in place and writes a match report.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
INTERMEDIATE = ROOT / "data" / "intermediate"
PROJECTS = INTERMEDIATE / "projects.json"
EXTRACTS = INTERMEDIATE / "aemo_vision_extracts.json"
EXTRACTS_V2 = INTERMEDIATE / "aemo_vision_extracts_v2.json"
MATCH_REPORT = INTERMEDIATE / "vision_match_report.json"

# Vision stage -> our display stage
VISION_STAGE_TO_DISPLAY = {
    "Operational": "Existing",
    "Commissioning": "Commissioning",
    "Registration": "Committed",
    "Pre-Registration": "Committed",
    "Application": "Application",
    "Enquiry": "Enquiry",
}

# Vision fuel -> compatibility groups
FUEL_FAMILY = {
    "Wind": "wind",
    "Solar": "solar",
    "Battery": "battery",
    "Hydro": "hydro",
    "Pumped Hydro Storage": "hydro",
    "OCGT": "gas",
    "CCGT": "gas",
    "Diesel": "gas",
    "Gas": "gas",
    "Coal": "coal",
    "Coal Mine Gas": "gas",
    "Biomass": "biomass",
    "Compressed Air": "storage",
}

REGION_FROM_STATE = {"NSW": "NSW1", "VIC": "VIC1", "QLD": "QLD1", "SA": "SA1", "TAS": "TAS1"}
REGION_CENTROID = {
    "NSW1": (-32.5, 147.0), "VIC1": (-36.8, 144.5), "QLD1": (-22.5, 145.5),
    "SA1": (-33.5, 138.6), "TAS1": (-42.0, 146.5),
}


def norm_tokens(s: str) -> set[str]:
    if not s:
        return set()
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return {t for t in s.split() if len(t) > 2 and t not in {"the", "and", "for", "with", "near", "south", "north", "east", "west"}}


def family_for(project_tech: str, project_fuel: str) -> str:
    t = (project_tech or "").lower() + " " + (project_fuel or "").lower()
    if "wind" in t: return "wind"
    if "solar" in t or "pv" in t: return "solar"
    if "battery" in t or "storage - battery" in t: return "battery"
    if "pumped hydro" in t: return "hydro"
    if "hydro" in t: return "hydro"
    if "ccgt" in t or "ocgt" in t or "gas" in t: return "gas"
    if "coal" in t: return "coal"
    if "biomass" in t: return "biomass"
    if "diesel" in t: return "gas"
    return "other"


def score(marker: dict, project: dict) -> tuple[float, float]:
    """Return (total_score, label_score). label_score=0 means no name/location overlap."""
    if marker["state"] != project.get("state"):
        return 0, 0
    fam_m = FUEL_FAMILY.get(marker.get("fuel"), "other")
    fam_p = family_for(project.get("technology"), project.get("fuel"))
    if fam_m != fam_p and fam_m != "other" and fam_p != "other":
        return 0, 0
    # capacity proximity
    cap_m = marker.get("capacity_mw") or 0
    cap_p = project.get("capacity_mw") or 0
    if cap_m <= 0 or cap_p <= 0:
        cap_score = 0.2
    else:
        ratio = min(cap_m, cap_p) / max(cap_m, cap_p)
        if cap_m < 50:
            cap_score = 1.0 if abs(cap_m - cap_p) <= 5 else max(0, ratio)
        else:
            cap_score = ratio
    # label overlap
    label_tokens = norm_tokens(marker.get("nearest_label", ""))
    name_tokens = norm_tokens(project.get("site_name", ""))
    loc_tokens = norm_tokens(project.get("location_desc", ""))
    overlap = len(label_tokens & (name_tokens | loc_tokens))
    label_score = min(1.0, overlap / max(1, len(label_tokens))) if label_tokens else 0
    return 0.6 * cap_score + 0.4 * label_score, label_score


def main():
    projects = json.loads(PROJECTS.read_text(encoding="utf-8"))
    # Prefer v2 (with pixel coords -> real lat/lon) if available
    if EXTRACTS_V2.exists():
        extracts = json.loads(EXTRACTS_V2.read_text(encoding="utf-8"))
        print("Using v2 vision extracts (with PDF-derived coords)")
    else:
        extracts = json.loads(EXTRACTS.read_text(encoding="utf-8"))
    markers = extracts.get("markers", [])
    print(f"Projects: {len(projects)}  Vision markers: {len(markers)}")

    # index projects by state for speed
    by_state = {}
    for p in projects:
        by_state.setdefault(p.get("state", ""), []).append(p)

    matches = []
    used_project_ids = set()
    unmatched: list[dict] = []
    for mi, m in enumerate(markers):
        cands = by_state.get(m["state"], [])
        scored = [((tot, lbl), pi) for pi, p in enumerate(cands) for tot, lbl in [score(m, p)]]
        scored = [s for s in scored if s[0][0] > 0.5]
        scored.sort(reverse=True)
        if scored:
            (best_score, best_label_score), pi = scored[0]
            project = cands[pi]
            pid = id(project)
            matches.append({
                "marker_idx": mi,
                "marker": m,
                "match_score": round(best_score, 3),
                "project_site": project.get("site_name"),
                "project_stage_before": project.get("stage"),
            })
            # Upgrade project: set vision_stage and reclassify stage
            project["on_aemo_map"] = True
            project["aemo_map_stage"] = m["stage"]
            project["aemo_map_capacity"] = m.get("capacity_mw")
            project["aemo_map_label"] = m.get("nearest_label")
            # Prefer AEMO icon position over Nominatim — AEMO is authoritative
            # for grid-connection location. Store Nominatim as a cross-reference.
            # But only trust vision coordinates when there is label/name evidence
            # (best_label_score > 0); a pure capacity match with no name link can
            # place a project hundreds of km away (e.g. Cattle Creek BESS at Toowoomba
            # matched to an Ingham South marker). Let geocode.py use location_desc instead.
            if m.get("lat") is not None and m.get("lon") is not None and best_label_score > 0:
                if project.get("geocoded"):
                    project["nominatim_lat"] = project.get("lat")
                    project["nominatim_lon"] = project.get("lon")
                project["lat"] = m["lat"]
                project["lon"] = m["lon"]
                project["coords_source"] = "aemo_map_vision"
                project["geocode_source"] = "vision"   # tells geocode.py not to overwrite
                project["geocoded"] = True  # treat AEMO icon as a real fix
            new_stage = VISION_STAGE_TO_DISPLAY.get(m["stage"], project.get("stage"))
            # NEM Gen Info unit_status is always authoritative. For non-NEM projects,
            # vision can set stage up to Application only — if a project were truly
            # Commissioning or Existing it would be registered in NEM Gen Info.
            # Mapping a KCI-only project to an "Operational" AEMO marker most likely
            # means the marker belongs to a co-located NEM project already captured
            # separately; calling the KCI entry "Existing" would be misleading.
            has_nem = "NEM" in (project.get("source") or "")
            if has_nem:
                # For NEM projects, only apply vision stage when it matches
                # what NEM already says (avoids PDF-reading errors overriding data).
                nem_stage = project.get("stage")
                if new_stage != nem_stage:
                    new_stage = nem_stage  # keep NEM's stage, vision provides location only
            elif best_label_score == 0:
                # No label/name overlap — pure capacity match. Don't change stage.
                new_stage = project.get("stage")
            else:
                # Non-NEM project with label evidence. Cap at Application:
                # vision confirms the project is real and visible on the AEMO map,
                # but not that it is operational or in commissioning.
                if new_stage in ("Existing", "Commissioning"):
                    new_stage = "Application"
            project["stage"] = new_stage
            project["vision_match_conf"] = round(best_score, 2)
            used_project_ids.add(pid)
        else:
            unmatched.append(m)

    # Append unmatched markers as standalone projects
    new_count = 0
    for m in unmatched:
        region = REGION_FROM_STATE.get(m["state"], "")
        # Prefer vision-derived coords if available, else region centroid
        if m.get("lat") is not None and m.get("lon") is not None:
            lat, lon = m["lat"], m["lon"]
            coords_source = "aemo_map_vision"
            geocoded = True  # treat as real location
        else:
            lat, lon = REGION_CENTROID.get(region, (None, None))
            coords_source = "region_centroid"
            geocoded = False
        new_count += 1
        projects.append({
            "site_name": f"{m.get('nearest_label','?')} {m.get('fuel','')} ({m.get('capacity_mw','?')} MW)",
            "region": region, "state": m["state"],
            "owner": "", "technology": m.get("fuel", ""), "fuel": "",
            "capacity_mw": m.get("capacity_mw"),
            "storage_mwh": None,
            "stage": VISION_STAGE_TO_DISPLAY.get(m.get("stage"), "Unknown"),
            "source": "AEMO map (vision; unmatched)",
            "on_aemo_map": True,
            "aemo_map_stage": m.get("stage"),
            "aemo_map_label": m.get("nearest_label"),
            "aemo_map_capacity": m.get("capacity_mw"),
            "location_desc": m.get("nearest_label", ""),
            "lat": lat, "lon": lon,
            "lat_approx": lat, "lon_approx": lon,
            "geocoded": geocoded,
            "coords_source": coords_source,
            "geocode_source": "vision" if coords_source == "aemo_map_vision" else "",
            "vision_match_conf": 0.0,
        })

    PROJECTS.write_text(json.dumps(projects, indent=2, default=str), encoding="utf-8")
    MATCH_REPORT.write_text(json.dumps({
        "matches": matches,
        "unmatched_count": len(unmatched),
        "matched_count": len(matches),
        "new_pseudo_projects": new_count,
        "summary_by_state": dict(Counter(m["marker"]["state"] for m in matches)),
    }, indent=2, default=str), encoding="utf-8")
    print(f"Matched: {len(matches)}  Unmatched: {len(unmatched)}  New pseudo-projects: {new_count}")
    print(f"Wrote {PROJECTS}")
    print(f"Wrote {MATCH_REPORT}")


if __name__ == "__main__":
    main()
