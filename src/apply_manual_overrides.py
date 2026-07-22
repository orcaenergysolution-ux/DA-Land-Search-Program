"""
Apply manual field overrides to projects.json.

Reads data/inputs/manual_overrides.json — a list of records, each with:
  "match":     dict of fields that must ALL match to identify the project
  "overrides": dict of fields to set on the matched project

Run after geocode.py so manual coordinates aren't overwritten by Nominatim,
but before build_leaflet.py.

Coordinate-soft behaviour
--------------------------
When an override contains coordinate fields (lat, lon, geocode_source, …) and
the project already has a trusted DA-spatial or GA geocode source, those
coordinate fields are skipped — the authoritative source wins.

Trusted sources (highest quality): VIC_WFS, QLD_FS, TAS_FS, NSW_DA, GA

To force a manual coordinate to win even against a trusted source, add
    "force_coords": true
to the override dict. Use this only when you have verified the manual coords
are more accurate than what the authoritative source provides (e.g. the DA
point lands on the wrong corner of a large property).
"""
from __future__ import annotations
import json
import pathlib

ROOT      = pathlib.Path(__file__).resolve().parent.parent
OVERRIDES = ROOT / "data" / "inputs" / "manual_overrides.json"
PROJECTS  = ROOT / "data" / "intermediate" / "projects.json"

# Coordinate fields that should not clobber authoritative DA / GA positions
_COORD_FIELDS = {"lat", "lon", "geocode_source", "geocode_display",
                 "coords_source", "geocoded", "nominatim_lat", "nominatim_lon"}

# Sources considered authoritative — manual coords defer to these by default
_TRUSTED_SOURCES = {"VIC_WFS", "QLD_FS", "TAS_FS", "NSW_DA", "GA"}


def apply(projects: list[dict], overrides: list[dict]) -> int:
    updated = 0
    for rule in overrides:
        if rule.get("_comment"):
            pass  # informational only
        match_fields = rule.get("match", {})
        fields       = rule.get("overrides", {})
        if not match_fields or not fields:
            continue

        matched = [
            p for p in projects
            if all(p.get(k) == v for k, v in match_fields.items())
        ]

        if not matched:
            print(f"  [manual_overrides] WARNING: no match for {match_fields}")
            continue
        if len(matched) > 1:
            print(f"  [manual_overrides] WARNING: {len(matched)} matches for {match_fields} — applying to all")

        force_coords = fields.get("force_coords", False)

        for p in matched:
            existing_source = p.get("geocode_source", "")
            has_better = existing_source in _TRUSTED_SOURCES and not force_coords
            skipped: list[str] = []

            for k, v in fields.items():
                if k == "force_coords":
                    continue
                if k in _COORD_FIELDS and has_better:
                    skipped.append(k)
                    continue
                p[k] = v

            updated += 1
            applied = [k for k in fields if k != "force_coords" and k not in skipped]
            if applied:
                print(f"  [manual_overrides] Applied to '{p['site_name']}': {applied}")
            if skipped:
                print(f"  [manual_overrides] Skipped coord fields {skipped} for "
                      f"'{p['site_name']}' — existing source '{existing_source}' is "
                      f"authoritative. Add \"force_coords\": true to override.")

    return updated


def main():
    if not OVERRIDES.exists():
        print("No manual_overrides.json found — skipping.")
        return

    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    projects  = json.loads(PROJECTS.read_text(encoding="utf-8"))

    print(f"\n=== apply_manual_overrides ({len(overrides)} rules, {len(projects)} projects) ===")
    n = apply(projects, overrides)
    print(f"  Updated {n} project(s)")

    PROJECTS.write_text(json.dumps(projects, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
