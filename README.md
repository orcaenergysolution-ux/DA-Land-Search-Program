# NEM Generation Map

Interactive map of every generation project in the National Electricity Market — Enquiry, Application, DA Submitted, DA Approved, Anticipated, Committed, Commissioning, Retiring, Existing — with project name, capacity, owner, technology, stage, and a transmission-line base layer. Designed to be a more complete and current view than AEMO's quarterly generation map.

Open `outputs/nem_map.html` in any browser to use the map.

## What's in the box

- **1,801 projects** across NSW · VIC · QLD · SA · TAS
- **1,743 geocoded** to real coordinates (97%); 58 hidden (no location found in any source)
- **220 projects flagged as on the AEMO map** (text-match + vision pass)
- **19,779 transmission-line segments** ≥132 kV from OpenStreetMap
- **2,052 substations** ≥66 kV
- **Filter sidebar**: search, stage, state, capacity slider, technology, base-layer toggles
- **Dashboard tab**: live MW pipeline by stage × state, MW by technology, totals cards

## Brief mapping

| Brief layer | Source | Implementation |
| --- | --- | --- |
| 1. Broad project list | KCI Datafile Compiled NEM | `build_map.py` |
| 2. Stage classification (Existing → Enquiry) | NEM Generation Information | `build_map.py::classify_stage` |
| 3. DA stages (DA Approved / DA Submitted / Anticipated) | NSW / VIC / QLD / TAS planning portals + CER | `fetch_cer_da.py` |
| 4. AEMO map presence + approx location | AEMO state PDFs (vision pass) | `integrate_vision.py` |

Stage logic summary:
- NEM Gen Info `unit_status` is always authoritative for NEM-registered projects
- In KCI **and** NEM Gen Info → stage from NEM unit_status
- In KCI only, not on AEMO map → **Enquiry**
- In KCI only, on AEMO map → **Application**
- DA sources add **DA Approved / DA Submitted / Anticipated / Committed** for non-NEM projects
- Vision pass can set **Application** for non-NEM projects; Operational/Commissioning from vision is capped at Application

## Folder layout

```
AEMO_map/
├── README.md
├── .gitignore
├── src/                                    # pipeline scripts (run via pipeline.py)
│   ├── pipeline.py                         # orchestrator — runs all steps in order
│   ├── build_map.py                        # KCI + NEM → projects.json (base unified table)
│   ├── extract_aemo_pdfs.py                # match AEMO PDF text → projects.json names
│   ├── render_aemo_overlays.py             # render state PDFs as georeferenced PNGs
│   ├── integrate_vision.py                 # merge AEMO map vision extracts → projects.json
│   ├── fetch_cer_da.py                     # CER + NSW/VIC/QLD/TAS DA + capacity supplement
│   ├── fetch_capacity_supplement.py        # WRI GPPD + OSM capacity gap-fill
│   ├── fetch_vic_permits.py                # VIC planning permit data
│   ├── fetch_qld_sara.py                   # QLD SARA decision register
│   ├── fetch_rez.py                        # Renewable Energy Zone boundaries
│   ├── geocode.py                          # Nominatim geocoder (rate-limited, cached)
│   ├── apply_manual_overrides.py           # apply data/inputs/manual_overrides.json
│   ├── fetch_transmission_lines.py         # OSM Overpass → transmission lines + substations
│   ├── slim_transmission.py                # filter to ≥66 kV backbone
│   ├── build_leaflet.py                    # assemble final standalone Leaflet HTML
│   ├── icp_warp.py                         # ICP warp for AEMO PDF alignment
│   ├── refine_aemo_alignment.py            # refine PDF georeferencing
│   ├── verify_warp.py                      # verify warp quality
│   └── helpers/                            # per-state vision extract scripts (replayable)
│       ├── append_vision_extracts.py
│       ├── _extract_{nsw,vic,qld,sa,tas}.py   # v1 extracts
│       └── _extract_{nsw,vic,qld,sa,tas}_v2.py  # v2 extracts
├── scripts/                                # one-off utilities (not part of pipeline)
│   ├── update_csvs.py                      # regenerate outputs/projects_all.csv
│   └── (various probe/audit/debug scripts)
├── data/
│   ├── inputs/                             # raw user-supplied data (committed)
│   │   ├── KCI Datafile Compiled NEM<timestamp>.xlsx   # current quarter
│   │   ├── NEM Generation Information <Quarter Year>.xlsx  # current quarter
│   │   ├── manual_overrides.json           # field-level patches applied after geocoding
│   │   ├── manual_exclusions.json          # projects to drop from the map
│   │   ├── manual_capacities.json          # hand-curated MW fallbacks
│   │   ├── nem_name_renames.json           # site name corrections
│   │   ├── qld_sara_decisions.json         # cached QLD SARA decisions
│   │   ├── vic_permit_index.json           # cached VIC permit index
│   │   └── aemo_maps/                      # PDFs manually downloaded from AEMO
│   │       ├── nem_regional_boundaries.pdf
│   │       └── {nsw,vic,qld,sa,tas}-map.pdf
│   ├── image/                              # technology icon PNGs (base64-embedded in HTML)
│   │   └── sun.png  wind.png  battery.png  hydro.png  pumphydro.png  ocgt.png  ccgt.png …
│   └── intermediate/                       # derived JSON / caches (rebuildable)
│       ├── projects.json                   # unified table — the canonical data
│       ├── aemo_pdf_matches.json           # AEMO PDF text matches
│       ├── aemo_overlays.json              # PNG bounds for Leaflet ImageOverlay
│       ├── aemo_vision_extracts.json       # vision pass over AEMO map tiles (216 markers)
│       ├── vision_match_report.json        # how vision markers mapped to projects
│       ├── geocode_cache.json              # Nominatim cache (preserves rate-limited work)
│       ├── transmission_lines.geojson      # raw OSM dump (~15 MB)
│       ├── transmission_lines.slim.geojson # ≥66 kV backbone (~5 MB)
│       ├── substations.geojson
│       └── manual_tx_lines.geojson         # optional hand-drawn transmission additions
└── outputs/
    ├── nem_map.html                        # CANONICAL output — fully self-contained (~7 MB)
    ├── projects_all.csv                    # all projects (regenerate: python scripts/update_csvs.py)
    └── null_locations.csv                  # projects missing coordinates
```

## How to run

From the project root:

```bash
python src/pipeline.py
```

Or step-by-step (any step is rerunnable; nothing destructive):

```bash
python src/build_map.py              # 1. KCI + NEM → projects.json (base table)
python src/extract_aemo_pdfs.py      # 2. AEMO PDF text matches
python src/build_map.py              # 3. rerun so matches feed stage classification
python src/render_aemo_overlays.py   # 4. render state PDFs as raster underlays
python src/tile_aemo_pdfs.py         # 5. cut tiles for vision review
# 6. MANUAL: have Claude/GPT vision enumerate markers from each tile,
#    save to data/intermediate/aemo_vision_extracts.json. Existing extract is preserved.
python src/integrate_vision.py       # 7. merge vision into projects.json
python src/fetch_cer_da.py           # 8. CER + NSW/VIC/QLD/TAS DA sources + capacity supplement
python src/geocode.py                # 9. Nominatim ~30 min, cached
python src/apply_manual_overrides.py # 10. apply data/inputs/manual_overrides.json patches
python src/fetch_transmission_lines.py  # 11. OSM Overpass, ~5 min, chunked by state
python src/slim_transmission.py      # 12. shrink to ≥132 kV
python src/build_leaflet.py          # 13. final standalone HTML
```

## Quarterly update process

KCI and NEM Generation Information are released quarterly. All DA sources (NSW, VIC, QLD, TAS, CER) are live web fetches and update automatically on each pipeline run. The only manual steps are swapping the two Excel input files and updating two filename constants.

### What's automatic vs. manual

| Component | Effort | Notes |
|---|---|---|
| NSW / VIC / QLD / TAS / CER DA data | Zero — auto-fetched | Live HTTP at run time; always current |
| Geocode cache | Zero — preserved | Only genuinely new projects hit Nominatim |
| Manual overrides | Zero — preserved | Survive full reruns unchanged |
| AEMO PDF vision extracts | Zero (usually) | Cached; only redo if AEMO releases new state PDFs |
| New KCI file | Two steps | Drop file + update one line |
| New NEM file | Two steps | Drop file + update one line |

### Steps each quarter

**1 — Drop the new input files**

```
data/inputs/KCI Datafile Compiled NEM<new_timestamp>.xlsx
data/inputs/NEM Generation Information <Quarter> <Year>.xlsx
```

Keep the old files — they are ignored unless referenced.

**2 — Update the two filename constants in `src/build_map.py`** (lines 40–41)

```python
# Example: updating to July 2026 quarter
KCI_FILE = INPUTS / "KCI Datafile Compiled NEM202606201000.xlsx"
NEM_FILE = INPUTS / "NEM Generation Information Jul 2026.xlsx"
```

> **Tip:** these two lines are the only thing that needs changing each quarter. If you want to eliminate this step entirely, the filenames could be auto-detected with a glob — open an issue or ask Claude Code to make the change.

**3 — Run the pipeline**

```bash
python src/pipeline.py --no-vision
```

`--no-vision` reuses the cached AEMO PDF extracts and skips the ~30-minute vision pass. Use a full `python src/pipeline.py` only when AEMO has released updated state PDFs.

Expected runtime: **5–10 minutes** (geocoding dominates, and most of that is cache hits).

**4 — Check the output**

Quick sanity check:

```bash
python - <<'EOF'
import json
from collections import Counter
p = json.load(open("data/intermediate/projects.json"))
print(f"Total: {len(p)}")
for stage, n in sorted(Counter(x["stage"] for x in p).items(), key=lambda x: -x[1]):
    print(f"  {stage}: {n}")
EOF
```

Watch for unexpected large swings in any stage — these usually mean a column layout change in the new Excel file.

**5 — Check for new project renames**

Scan the new NEM file for projects whose names differ from the previous quarter. If KCI or CER still uses the old name, add an exclusion entry to `data/inputs/manual_exclusions.json`:

```json
{
  "site_name": "Old Name From KCI/CER",
  "reason": "NEM rename YYYY-MM: 'Old Name' -> 'New NEM Name'. Keep NEM name."
}
```

Then rerun from `fetch_cer_da.py` onwards:

```bash
python src/fetch_cer_da.py && python src/geocode.py && python src/apply_manual_overrides.py && python src/build_leaflet.py
```

**6 — Handle new null locations**

New projects without coordinates appear in `outputs/null_locations.csv`. Research and add important ones to `manual_overrides.json`, then:

```bash
python src/apply_manual_overrides.py && python src/build_leaflet.py
```

Or use the in-map **Export missing locations / Upload fixed CSV** workflow to preview placements before committing to `manual_overrides.json`.

---

### When a DA dataset or geocoder now has a better location than a manual override

Manual overrides run last in the pipeline, so they have always "won" over DA spatial data or GA coordinates — even when the DA point is more accurate. As of the current pipeline, **coordinate fields in manual overrides are soft by default**: if the project already has a trusted DA-spatial or GA geocode source, the manual `lat`/`lon` (and related fields) are skipped and the authoritative source keeps its value.

**Trusted sources (highest quality) that manual coords defer to:**

| `geocode_source` | Dataset |
|---|---|
| `VIC_WFS` | VIC DataVic WFS facility centre points |
| `QLD_FS` | QLD Government ArcGIS FeatureServer |
| `TAS_FS` | TAS State Growth MapServer |
| `NSW_DA` | NSW Planning DA portal geometry |
| `GA` | Geoscience Australia power stations register |

**What this means in practice:**

- If you added a manual override for, say, a QLD solar farm because it wasn't in the QLD FeatureServer at the time, and the FeatureServer has since added it — the next pipeline run will automatically use the FeatureServer point and skip the manual `lat`/`lon`. You'll see a log line like:
  ```
  [manual_overrides] Skipped coord fields ['lat', 'lon', 'geocode_source'] for
  'Sunraysia Solar Farm' — existing source 'QLD_FS' is authoritative.
  ```

- Non-coordinate fields in the same override (e.g. `technology`, `capacity_mw`, `owner`) are still applied normally.

- To force a manual coordinate to win even against a trusted source — for example if you've verified the DA centroid lands on the wrong corner of a large property — add `"force_coords": true` to the override:

```json
{
  "_comment": "DA centroid is on the substation, not the solar field — confirmed via satellite",
  "match": {"site_name": "Example Solar Farm", "state": "NSW"},
  "overrides": {
    "force_coords": true,
    "lat": -33.123,
    "lon": 149.456,
    "geocode_source": "manual",
    "geocode_display": "Field boundary confirmed via Google Earth"
  }
}
```

**Periodic audit:** after running the quarterly update, scan the pipeline log for `Skipped coord fields` messages. Each one means a manual override has been superseded — you can optionally remove the coord fields from that entry in `manual_overrides.json` to keep it clean (the non-coord fields like `technology` are still worth keeping).

## Dependencies

```bash
pip install openpyxl pdfplumber pymupdf
```

Standard library only otherwise (`urllib`, `json`, `re`, `pathlib`).

## Map features

**Sidebar — Filters tab**
- Text search (name / owner / location)
- Stage checkboxes (colour-coded, AEMO conventions)
- State checkboxes
- Capacity slider (MW minimum)
- Technology dropdown
- Network base layer toggles (transmission lines, substations)
- "Only show projects on AEMO map" · "Only real-geocoded locations"

**Sidebar — Dashboard tab**
- Cards: project count, total MW, storage MWh, on-AEMO-map count
- Bar chart: MW by stage
- Table: stage × state MW pipeline
- Bar chart: MW by technology (top 10)
- All figures update live with filter changes

**Visual conventions**
- Marker colour by stage:
  | Stage | Colour |
  |---|---|
  | Existing | dark grey / black |
  | Retiring | orange |
  | Commissioning | purple |
  | Committed | green |
  | Anticipated | amber |
  | DA Approved | light green |
  | DA Submitted | violet |
  | Application | blue |
  | Enquiry | red |
  | Withdrawn | light grey |
- Marker radius ∝ log(capacity_mw)
- Transmission lines coloured by voltage (AEMO conventions: 500 kV yellow, 330 kV orange, 275 kV pink, 220 kV blue, 132 kV red, 66 kV brown)
- AEMO state PDFs render at 55% opacity as raster underlays

## Stage classification details

Stage is set by four pipeline scripts in order. Later scripts can only raise a stage, never lower one that was set by an authoritative earlier source.

### 1 — NEM Gen Info unit_status (`build_map.py::classify_stage`) — always authoritative

| NEM Gen Info `unit_status` | Display stage |
| --- | --- |
| `In Service` | Existing |
| `Announced Withdrawal` | Retiring |
| `In Commissioning` | Commissioning |
| `Committed` | Committed |
| `Anticipated` | Anticipated |
| `Publicly Announced` | Application |
| `Withdrawn` / `Withdrawn – Permanent` | Withdrawn |

KCI `Withdrawn` / `Cancelled` rows are dropped before merging.

### 2 — KCI-only projects (`build_map.py::merge`)

Projects in KCI but not in NEM Gen Info get a provisional stage based on AEMO map presence:

| Condition | Display stage |
| --- | --- |
| KCI-only, not on AEMO map | Enquiry |
| KCI-only, on AEMO map | Application |

### 3 — DA and supplementary sources (`fetch_cer_da.py`) — upgrades non-NEM projects only

NEM-registered projects are never downgraded by DA data. For projects without a NEM source, DA status can set or upgrade the stage:

| Source | Raw status | Display stage |
| --- | --- | --- |
| CER | Committed | Committed |
| CER | Probable | Anticipated |
| NSW DA | Approved | DA Approved |
| NSW DA | Under assessment | DA Submitted |
| NSW DA | Operational | Existing (NEM-registered only) |
| VIC WFS | Approved, not constructed | DA Approved |
| VIC WFS | Under consideration / Referred | DA Submitted |
| VIC WFS | Under construction | Committed |
| VIC WFS | Operating | Existing (NEM-registered only) |
| QLD FeatureServer | Proposed | DA Approved |
| QLD FeatureServer | Under construction | Committed |
| QLD FeatureServer | Existing | Existing (NEM-registered only) |
| TAS MapServer | Approved (AP) | DA Approved |
| TAS MapServer | State Assessment / Early Planning | DA Submitted |
| TAS MapServer | Operational (OP) | Existing (NEM-registered only) |

### 4 — AEMO PDF vision pass (`integrate_vision.py`) — last, lowest priority

Vision stage is only applied to non-NEM projects and is capped at Application:

| Vision marker stage | Project has NEM source? | Display stage applied |
| --- | --- | --- |
| Any | Yes | No change — NEM unit_status is kept |
| Operational / Commissioning | No | Capped at Application |
| Registration / Pre-Registration | No | Committed |
| Application | No | Application |
| Enquiry | No | Enquiry |

Vision with no label/name match (pure capacity match only) never changes the stage.

## How the vision pass works

`tile_aemo_pdfs.py` cuts each state PDF into 4–9 tiles at 4× DPI. A vision-capable LLM (Claude Opus 4.7 used here) reads each tile and enumerates every project marker, classifying:
- **Stage** by icon colour: orange Application / yellow-green Pre-Reg / green Registration / pink Commissioning / dark-blue Operational
- **Fuel** by icon shape: Wind / Solar / OCGT / Hydro / Pumped Hydro / Diesel / Coal / CCGT / Biomass / Battery / Substation
- **Capacity** from the adjacent number label
- **Nearest substation/town** from the closest text label

Each marker gets a per-field confidence rating (high/medium/low). `integrate_vision.py` matches markers to existing project records by (state, capacity ±15%, fuel-family compatibility, label-token overlap with site name or location description). 213/214 markers matched in the current run (1 unmatched added as a pseudo-project).

**Coordinate assignment rules in `integrate_vision.py`:**
- Vision coordinates are only written to a project when the match has `label_score > 0` (i.e. there is name/label token overlap between the PDF marker label and the project's site name or location). A pure capacity-only match could coincidentally link projects hundreds of km apart (e.g. two unrelated 300 MW batteries in different cities), so vision coordinates are withheld in that case.
- Stage from the vision pass is only applied to non-NEM projects. For NEM-registered projects, `unit_status` from NEM Gen Info always takes precedence over what Claude read off the PDF map.

## DA & supplementary data sources

`src/fetch_cer_da.py` runs after the base NEM+KCI table is built and enriches it with seven additional sources. For each external record it either upgrades an existing project (better stage, fills missing coordinates/capacity) or adds a new entry.

### 1 — CER (national)
| | |
|---|---|
| **What** | Clean Energy Regulator committed and probable power station lists |
| **URL** | `https://cer.gov.au/document/power-stations-and-projects-committed` and `…-probable` |
| **Format** | CSV download |
| **Fields used** | Project name, state, MW capacity, fuel source, committed date |
| **Stage mapping** | Committed → `Committed`; Probable → `Anticipated` |
| **Notes** | "Committed" CER projects already in NEM Gen Info are not re-added; "Probable" ones often missing from NEM so are added as new entries. Covers all NEM states including SA. |

### 2 — NSW Planning DA tracker
| | |
|---|---|
| **What** | NSW Planning renewable energy project tracker (all SSD renewable DAs) |
| **URL** | `https://www.planning.nsw.gov.au/policy-and-legislation/renewable-energy` |
| **Format** | HTML page — two structures scraped: dialog detail sections (105 projects, richest data including location suburb, MW, MWh, approval date) and simple loop-index table rows (all ~194 projects) |
| **Fields used** | Project name, type, status, location suburb, generating capacity (MW), storage capacity (MW/MWh) |
| **Stage mapping** | Operational → `Existing`; Approved → `DA Approved`; Under assessment → `DA Submitted`; Withdrawn → `Withdrawn` |

### 3 — VIC DataVic WFS
| | |
|---|---|
| **What** | Victoria renewable energy facility centre points |
| **URL** | `https://opendata.maps.vic.gov.au/geoserver/wfs?…typeNames=renewables_point` |
| **Format** | GeoJSON via WFS 2.0 |
| **Fields used** | Name, type, approval_status, construction_status, point geometry (lat/lon) |
| **Stage mapping** | Operating → `Existing`; Under construction → `Committed`; Approved + not constructed → `DA Approved`; Under consideration / referred → `DA Submitted` |
| **Notes** | Provides real coordinates for 252 Victorian facilities; capacity field is absent so MW comes from NEM/KCI match if one exists. |

### 4 — VIC Planning permits (`fetch_vic_permits.py`)
| | |
|---|---|
| **What** | Victoria planning permit register for renewable energy projects |
| **Format** | Supplementary script; updates stage and permit metadata on VIC projects already in the table |

### 5 — QLD Electricity Plants (ArcGIS)
| | |
|---|---|
| **What** | Queensland electricity plant locations from the QLD Government ArcGIS FeatureServer |
| **URL** | `https://services1.arcgis.com/vkTwD8kHw2woKBqV/arcgis/rest/services/Queensland_Electricity_Plants/FeatureServer/0/query` |
| **Format** | GeoJSON via ArcGIS REST API |
| **Fields used** | Name, fuel type, status, capacity (MW), point geometry |
| **Stage mapping** | Existing → `Existing`; Under construction → `Committed`; Proposed → `DA Approved`; Decommissioned → `Withdrawn` |
| **Notes** | Only renewable fuel types retained (coal, gas, diesel excluded). Provides real coordinates for ~200 QLD projects. |

### 6 — QLD SARA decisions (`fetch_qld_sara.py`)
| | |
|---|---|
| **What** | Queensland State Assessment and Referral Agency (SARA) decision register |
| **Format** | Supplementary script; records SARA decision date and outcome on QLD projects |

### 7 — TAS State Growth MapServer
| | |
|---|---|
| **What** | Tasmania State Growth generation and storage map layer |
| **Format** | ArcGIS MapServer REST |
| **Fields used** | Name, technology, capacity, coordinates |
| **Notes** | Supplements TAS coverage for projects not in NEM Gen Info. |

### DA stage mapping — consolidated reference

| Source | Raw status in source data | Display stage |
| --- | --- | --- |
| **CER** | Committed | Committed |
| **CER** | Probable | Anticipated |
| **NSW DA** | Operational | Existing |
| **NSW DA** | Approved | DA Approved |
| **NSW DA** | Under assessment | DA Submitted |
| **NSW DA** | Withdrawn | Withdrawn |
| **VIC WFS** | Operating / Constructed | Existing |
| **VIC WFS** | Under construction | Committed |
| **VIC WFS** | Approved + not constructed | DA Approved |
| **VIC WFS** | Under consideration / Referred | DA Submitted |
| **QLD FS** | Existing | Existing |
| **QLD FS** | Under construction | Committed |
| **QLD FS** | Proposed | DA Approved |
| **QLD FS** | Decommissioned | Withdrawn |
| **TAS** | Operational (OP) | Existing |
| **TAS** | Approved (AP) | DA Approved |
| **TAS** | State Assessment (SA) / Early Planning (EP) | DA Submitted |

> **Note:** "Committed" from DA sources means the state planning authority records physical works as underway ("under construction"), which is reliable evidence of commitment. It is distinct from NEM Gen Info `In Commissioning` → `Commissioning`, which means final testing before commercial operation.
>
> DA stage is only applied when the project has **no NEM source** (i.e. not yet in NEM Gen Info). If a project appears in both NEM and a DA source, the NEM `unit_status` takes precedence.

### SA
No accessible REST API was found for SA DA data (plan.sa.gov.au, energymining.sa.gov.au, SA EPA and SA CKAN all return 403). SA committed and probable projects are covered by the CER national feed.

### Capacity supplement (`fetch_capacity_supplement.py`)
When a project has no MW figure from NEM or the DA sources, capacity is filled from (in order):
1. **WRI Global Power Plant Database** (GitHub CSV)
2. **OpenStreetMap** `power=plant` nodes matched by name
3. **`data/inputs/manual_capacities.json`** — hand-curated fallback values

### Manual overrides (`apply_manual_overrides.py`)
After geocoding, `data/inputs/manual_overrides.json` applies field-level patches (technology, coordinates, etc.) that survive full pipeline reruns. Add a record with `"match"` (fields to identify the project) and `"overrides"` (fields to set).

### Manual exclusions (`fetch_cer_da.py`)
`data/inputs/manual_exclusions.json` lists projects that should be dropped from the final output. Every entry needs a `"site_name"` and a `"reason"`. The exclusions are applied at the end of `fetch_cer_da.py`, after all DA sources have been merged.

All current entries are **name-deduplication rules**: AEMO periodically renames projects in NEM Generation Information (e.g. "Palmerston Big Battery" → "Great Lakes Battery"), but KCI and CER continue using the old name for one or more quarters. Without an exclusion the old name survives normalisation and creates a ghost duplicate alongside the new NEM name.

**How to add an exclusion:**
```json
{
  "site_name": "Old Project Name",
  "reason": "NEM rename YYYY-MM: 'Old Project Name' -> 'New Project Name'. Keep NEM name."
}
```

**Quarterly maintenance:** when the new NEM file introduces renames, check whether KCI or CER still carries the old name. If so, add an exclusion entry. Conversely, if a project is no longer in KCI/CER at all, the exclusion entry becomes harmless but can be removed for tidiness.

---

## How location is determined

Every project marker on the map has a `geocode_source` field that records how its coordinates were obtained. Sources are applied in priority order — higher-tier sources are never overwritten by lower-tier ones.

### Source priority (highest → lowest)

| Priority | `geocode_source` | Description | Accuracy |
|---|---|---|---|
| 1 | `VIC_WFS` | VIC DataVic WFS facility centre points | Facility-level (exact) |
| 1 | `QLD_FS` | QLD Government ArcGIS FeatureServer | Facility-level (exact) |
| 1 | `TAS_FS` | TAS State Growth MapServer | Facility-level (exact) |
| 1 | `NSW_DA` | NSW Planning DA portal (lat/lon from DA geometry) | Facility or suburb-level |
| 1 | `manual` | Hand-researched coordinates (see below) | Varies — see comment |
| 2 | `GA` | Geoscience Australia power stations register, name-matched | Facility-level |
| 3 | `Nominatim` | Project name geocoded via Nominatim/OSM | Town / suburb-level |
| 3 | `suburb` | `location_desc` suburb extracted and geocoded | Town-level (dashed border shown on map) |
| 4 | `vision` | AEMO PDF vision pass coordinates — last resort fallback | Schematic PDF position (±10–30 km) |

**Priority rules:**
- **DA spatial datasets and `manual` (Priority 1)** — set by `fetch_cer_da.py` / `apply_manual_overrides.py`. `geocode.py` never touches them. `fetch_cer_da.py` also upgrades `vision` or `suburb` coords to DA facility-level when a DA spatial match exists.
- **GA (Priority 2)** — overwrites `vision` coordinates. GA's registered GPS positions are more accurate than the PDF affine-transform (TPS transform error can place projects 30+ km off, e.g. Eraring BESS was placed in the ocean). Does not overwrite DA or manual.
- **Nominatim (Priority 3)** — also overwrites `vision` coordinates. A specific `location_desc` suburb or project-name search is more accurate than a schematic PDF position. Does not overwrite GA or DA/manual.
- **Vision (Priority 4 / fallback)** — if neither GA nor Nominatim finds a project, the original PDF position is restored. Vision is never the first choice; it is only kept when nothing better is available.

### Tier 1 — Spatial datasets (automatic)

**VIC / QLD / TAS / NSW DA** (`fetch_cer_da.py`): Four state government datasets provide real facility coordinates for projects that appear in them. When `fetch_cer_da.py` matches a project to one of these datasets, it writes the point geometry directly into `projects.json`. A project with a `vision` or `suburb` geocode is also upgraded to the precise DA point at this stage.

### Tier 2 — Geoscience Australia name match (automatic)

`geocode.py` downloads the GA power stations register and attempts a fuzzy name match against every project not already located by a Priority 1 (DA/manual) source. Vision-located projects are included — GA is given the opportunity to replace the schematic PDF position with a precise GPS fix. A successful GA match gives facility-level accuracy (e.g. Liddell, Snowy Hydro, Hornsdale).

### Tier 3 — Nominatim geocoding (automatic)

For projects still unmatched after GA (including those whose vision coords were cleared to let Nominatim run), `geocode.py` builds up to four candidate queries. Vision-located projects participate here too — if a good `location_desc` or project-name match is found, the Nominatim result replaces the vision position.

**AEMO PDF vision fallback** (`integrate_vision.py`): The tile (x, y) position of each marker extracted from the AEMO state PDFs is converted to approximate lat/lon using the georeferenced affine transform for that state's PDF. Accuracy is roughly ±10–30 km. Vision coordinates are only written in the first place when the match has name/label evidence (`label_score > 0`); a pure capacity-only match is not enough. After `geocode.py` runs, vision position is kept only if neither GA nor Nominatim found something better.

Nominatim builds up to four candidate queries per project, in order:

1. **Full `location_desc`** — collapsed to a single line (newlines → commas).
2. **Individual lines of multi-line addresses** — e.g. `"Lot 5 Station Rd\nMolong NSW 2866"` tried line-by-line, last line first.
3. **Suburb extracted from a street address** — street-number prefix stripped, suburb component tried (e.g. `"Molong NSW 2866, Australia"`).
4. **Project site name** — e.g. `"Snowy 2.0 Pumped Hydro, NSW, Australia"`.

Queries 1–3 are classified as `suburb` (town-level accuracy; dashed marker border on map). Query 4 is classified as `Nominatim`. All results are cached in `data/intermediate/geocode_cache.json` so re-runs avoid redundant API calls.

### Tier 4 — Vision fallback (automatic)

After GA and Nominatim have run, any project that still has no coordinates but had a vision position (AEMO PDF affine-transform) has that position restored. Vision is the lowest-priority geocode source — it is only kept when nothing better is available.

### Tier 5 — Manual overrides

For projects that still lack coordinates after Tiers 1–4 (typically Application / Enquiry stage proposals with sparse public information), coordinates are hand-researched and added to `data/inputs/manual_overrides.json`. This file is a JSON array of patch rules that survive full pipeline reruns.

**How to add a manual override:**
```json
{
  "_comment": "Source note — where the coords came from",
  "match": {"site_name": "Example Solar Farm", "state": "NSW"},
  "overrides": {
    "lat": -33.123,
    "lon": 149.456,
    "geocode_source": "manual",
    "geocode_display": "Example Road, Molong NSW"
  }
}
```

**Sources used for manual coordinates (171 entries as of current run):**

| Source type | Examples |
|---|---|
| Street address from DA / planning portal | "563-571 Miles Franklin Drive Talbingo NSW 2720" |
| Substation reference + known substation coords | "Adjacent to Blyth West 275kV Substation" → -33.834, 138.437 |
| Substation midpoint calculation | Hughes Gap BESS: midpoint of Davenport (-32.558, 137.864) and Blyth West (-33.834, 138.437) |
| Project documentation / developer website | Kidston Pumped Hydro coordinates from NAIF project docs |
| Property records / YourSay / planning portals | Bulabul BESS 1: 6773 & 6909 Goolma Road, Wuuluman NSW 2820 |
| Satellite / OSM cross-reference | Co-located projects sharing a known facility point |
| Geographic description + offset arithmetic | "2km East of Muswellbrook 330kV Substation" → bearing offset applied |
| Approximate offshore position | Offshore wind farms: ~25–40 km from nearest coast point |

Projects with manually placed coordinates that are approximate (e.g. "near Hargraves NSW" rather than a confirmed site address) display a **"Manually placed location"** note in the map popup.

### Projects hidden from the map

Projects with no location from any tier (currently **58 projects**) are omitted from the map entirely. They appear in `outputs/null_locations.csv`. Most are Application or Enquiry stage proposals with no location information in any public source.

### Missing locations workflow (interactive)

The HTML map provides a self-contained workflow for researching and temporarily placing the hidden projects, without needing to re-run the pipeline.

**Step 1 — Export the list**

In the map sidebar, click **↓ Export missing locations**. This downloads a CSV with one row per hidden project (columns: `site_name`, `state`, `capacity_mw`, `technology`, `stage`, `source`, `location_desc`, `lat`, `lon`). The `lat` and `lon` columns are empty — those are the ones to fill in.

**Step 2 — Research and fill coordinates**

Open the CSV in Excel or any spreadsheet app. For each project, look up the location using planning portals, developer websites, AEMO connection queue, or OSM, then enter decimal-degree coordinates (`lat` negative for Australia, `lon` positive).

Tips:
- `location_desc` usually gives a suburb, region, or property reference — try pasting it into Google Maps first.
- NSW DA portal (`planning.nsw.gov.au`) and QLD SARA often have map views for Application-stage projects.
- For BESS / solar co-located with a substation, the substation's coordinates are a good fallback.

**Step 3 — Upload the fixed CSV**

Click **↑ Upload fixed CSV** (the blue button in the sidebar). Select your saved CSV file. Any row with a valid `lat`/`lon` pair will immediately appear on the map as a **white dashed circle** — visually distinct from normal project markers. Hover to see the project name and capacity.

The upload is ephemeral — refreshing the page clears the markers. This is intentional; the upload is for quick preview and verification, not permanent storage.

**Step 4 — Make coordinates permanent**

Once you are confident in a set of coordinates, add them to `data/inputs/manual_overrides.json`:

```json
{
  "_comment": "Source — where the coords came from",
  "match": {"site_name": "Example Solar Farm", "state": "NSW"},
  "overrides": {
    "lat": -33.123,
    "lon": 149.456,
    "geocode_source": "manual",
    "geocode_display": "Example Road, Molong NSW"
  }
}
```

Then re-run `python src/apply_manual_overrides.py && python src/build_leaflet.py` (or the full `pipeline.py`) to incorporate the fix permanently.

---

## Known limitations

1. **58 projects have no location.** These are mostly Application/Enquiry stage proposals with no location information in any public source (no DA geometry, no `location_desc`, no online project documentation found). They appear in `outputs/null_locations.csv` and are hidden from the map.
2. **~439 projects show at suburb/town level** (`geocode_source = "suburb"`, shown with a dashed marker border). These are placed at the nearest town or suburb centroid from the `location_desc` field — accurate to within ~5–20 km but not site-level. The on-screen popup notes "location estimated".
3. **174 manually placed coordinates** vary in precision. Site addresses are accurate to within metres; substation-adjacent approximations are typically within 1–3 km; "near [town]" approximations may be 5–20 km off. The `_comment` field in `manual_overrides.json` records the source and confidence for each entry.
4. **Run order matters.** `build_map.py` is destructive on `projects.json`. Always use `pipeline.py` to run everything in the correct order — running `build_map.py` in isolation will wipe DA stages until `fetch_cer_da.py` is re-run.

## Output statistics (current run)

- 1,801 unified projects across NEM
- Stage breakdown: Application 724 · Existing 486 · DA Approved 190 · Enquiry 170 · Anticipated 82 · Committed 62 · DA Submitted 56 · Commissioning 20 · Retiring 7 · Expired 3 · Withdrawn 1
- Location coverage: 1,743 on map (97%) · 58 hidden (no location)
  - Facility-level DA spatial: VIC WFS 230 + QLD FS 219 + TAS FS 38 + NSW DA (suburb-level) = 487
  - Facility-level GA name match: 393
  - Manual address / research: 174
  - Town/suburb-level (Nominatim 246 + suburb 439): 685
  - Vision fallback (schematic PDF, not upgraded): 4
- Manual overrides: 171 entries in `data/inputs/manual_overrides.json`
- Projects flagged as on AEMO map: 220
- Transmission lines ≥132 kV: 19,779 segments
- Substations ≥66 kV: 2,052
- Final HTML size: ~7 MB

## Future work

- **Web-search Tier C remainder.** 60 projects still have no location — mostly Application/Enquiry proposals. A web-search pass over public documents (developer websites, planning notices, news articles) could find approximate coordinates for many of them. Rate-limited search tooling is needed.
- **Real coordinates from AEMO tiles.** ✅ Done (v2 extracts): the affine transform from `render_aemo_overlays.py` is applied during vision extraction to convert each marker's tile (x, y) to approximate lat/lon. Vision coordinates are further upgraded to GA GPS positions where a GA name match exists (54 projects in current run).
- **SA DA spatial data.** No accessible REST API was found for SA (plan.sa.gov.au returns 403). SA projects are geocoded by Nominatim or manual override only. If SA opens an API, `fetch_cer_da.py` can be extended.
- **Lazy-load transmission GeoJSON** via fetch so the HTML stays small and transmission can be filtered by voltage progressively.
- **Stage colour calibration per AEMO PDF**: sample the legend colour swatches programmatically so vector-shape colours map to AEMO's published stage names deterministically.
- **Owner / proponent grouping** view (competitive intel).
- **Improve geocoder fallbacks**: parse "Xkm of Town" patterns and apply a bearing offset from the town centroid; tokenise site names against a national gazetteer for better Nominatim coverage.
