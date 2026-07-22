"""
Tier C batch 2 — additional manual override entries.
"""
import json

entries = [
    # NSW - missed from batch 1
    {
        "_comment": "Murrumbidgee Council LGA, NSW — Boags Creek area (location_desc = 'Murrumbidgee Council Local Government Area'); using Jerilderie as LGA reference point",
        "match": {"site_name": "Boags Creek Solar Power Station", "state": "NSW"},
        "overrides": {"lat": -35.357, "lon": 145.720, "geocode_source": "manual",
                      "geocode_display": "Murrumbidgee LGA, NSW"}
    },
    {
        "_comment": "Dubbo area NSW — 'MNC000116 Dubbo Firming Power Station' project name indicates Dubbo",
        "match": {"site_name": "MNC000116 - Dubbo Firming Power Station", "state": "NSW"},
        "overrides": {"lat": -32.241, "lon": 148.601, "geocode_source": "manual",
                      "geocode_display": "Dubbo NSW"}
    },
    # QLD — KCI substation references and project names
    {
        "_comment": "Middle Ridge substation area, Toowoomba QLD — from KCI 'MIDDLE RIDGE TO STR-2975'",
        "match": {"site_name": "Blenheim BESS - KCI", "state": "QLD"},
        "overrides": {"lat": -27.590, "lon": 151.980, "geocode_source": "manual",
                      "geocode_display": "Middle Ridge substation area, Toowoomba QLD"}
    },
    {
        "_comment": "Middle Ridge substation area, Toowoomba QLD — from KCI 'MIDDLE RIDGE TO STR-2975'",
        "match": {"site_name": "Blenheim Solar Farm - KCI", "state": "QLD"},
        "overrides": {"lat": -27.590, "lon": 151.980, "geocode_source": "manual",
                      "geocode_display": "Middle Ridge substation area, Toowoomba QLD"}
    },
    {
        "_comment": "TURAWULLA is a locality near Rolleston/Springsure, Central QLD — Capricornia Energy Hub PHES",
        "match": {"site_name": "Capricornia Energy Hub (CEH) PHES", "state": "QLD"},
        "overrides": {"lat": -24.450, "lon": 148.550, "geocode_source": "manual",
                      "geocode_display": "Turawulla, Central QLD"}
    },
    {
        "_comment": "Halys substation area QLD — 'HALYS' is a Powerlink transmission node in the Surat Basin/Darling Downs",
        "match": {"site_name": "Halys BESS - Iberdrola", "state": "QLD"},
        "overrides": {"lat": -26.900, "lon": 150.200, "geocode_source": "manual",
                      "geocode_display": "Halys substation area, Darling Downs QLD"}
    },
    {
        "_comment": "Halys substation area QLD — co-located BESS (Akaysha)",
        "match": {"site_name": "Halys BESS 2 (Akaysha)", "state": "QLD"},
        "overrides": {"lat": -26.900, "lon": 150.200, "geocode_source": "manual",
                      "geocode_display": "Halys substation area, Darling Downs QLD"}
    },
    {
        "_comment": "Halys Hybrid Facility BESS — same Halys substation area",
        "match": {"site_name": "Halys Hybrid Facility - BESS", "state": "QLD"},
        "overrides": {"lat": -26.900, "lon": 150.200, "geocode_source": "manual",
                      "geocode_display": "Halys substation area, Darling Downs QLD"}
    },
    {
        "_comment": "Halys Hybrid Facility Solar — same Halys substation area",
        "match": {"site_name": "Halys Hybrid Facility - Solar", "state": "QLD"},
        "overrides": {"lat": -26.900, "lon": 150.200, "geocode_source": "manual",
                      "geocode_display": "Halys substation area, Darling Downs QLD"}
    },
    {
        "_comment": "Halys to Chinchilla transmission corridor QLD — between Halys (~-26.9, 150.2) and Chinchilla (-26.741, 150.629)",
        "match": {"site_name": "Halys to Chinchilla DCA Battery - KCI", "state": "QLD"},
        "overrides": {"lat": -26.820, "lon": 150.400, "geocode_source": "manual",
                      "geocode_display": "Halys-Chinchilla corridor, Darling Downs QLD"}
    },
    {
        "_comment": "Strathmore station area, NQ QLD — from KCI 'STRATHMORE TO STR-4558'; Strathmore is near Charters Towers/Townsville",
        "match": {"site_name": "Supernode North BESS 2", "state": "QLD"},
        "overrides": {"lat": -19.900, "lon": 146.100, "geocode_source": "manual",
                      "geocode_display": "Strathmore substation area, North QLD"}
    },
    # SA substations needing research
    {
        "_comment": "ElectraNet South East 275kV Substation SA — serves SE region (Limestone Coast); substation near Keith/Bordertown area",
        "match": {"site_name": "South East BESS - Storage - KCI", "state": "SA"},
        "overrides": {"lat": -36.300, "lon": 140.300, "geocode_source": "manual",
                      "geocode_display": "Near South East 275kV Substation, SA"}
    },
    {
        "_comment": "Adjacent to South East 275kV Substation SA — Pacific Green Limestone Coast North",
        "match": {"site_name": "Pacific Green Energy Park - Limestone Coast North", "state": "SA"},
        "overrides": {"lat": -36.300, "lon": 140.300, "geocode_source": "manual",
                      "geocode_display": "Near South East 275kV Substation, SA"}
    },
    {
        "_comment": "Limestone Coast West area SA — no specific location given; using Naracoorte as LGA reference",
        "match": {"site_name": "Pacific Green Energy Park - Limestone Coast West", "state": "SA"},
        "overrides": {"lat": -36.958, "lon": 140.742, "geocode_source": "manual",
                      "geocode_display": "Limestone Coast, SA"}
    },
    {
        "_comment": "Riverland Solar Storage co-located with Riverland BESS near NWB substation, Morgan SA",
        "match": {"site_name": "Riverland Solar Storage - Solar", "state": "SA"},
        "overrides": {"lat": -34.034, "lon": 139.674, "geocode_source": "manual",
                      "geocode_display": "Near North West Bend Substation, Riverland SA"}
    },
    {
        "_comment": "Solar River Project in the Murray-Darling Basin SA — likely near the Murray River in the Riverland",
        "match": {"site_name": "The Solar River Project - Stage 1", "state": "SA"},
        "overrides": {"lat": -34.200, "lon": 140.100, "geocode_source": "manual",
                      "geocode_display": "Murray-Darling, Riverland SA"}
    },
    {
        "_comment": "Solar River Project Stage 2 — co-located or adjacent to Stage 1",
        "match": {"site_name": "The Solar River Project - Stage 2", "state": "SA"},
        "overrides": {"lat": -34.200, "lon": 140.100, "geocode_source": "manual",
                      "geocode_display": "Murray-Darling, Riverland SA"}
    },
]

with open("data/inputs/manual_overrides.json") as f:
    existing = json.load(f)

existing_keys = set()
for e in existing:
    m = e.get("match", {})
    existing_keys.add((m.get("site_name",""), m.get("state",""), m.get("technology","")))

added = 0
for e in entries:
    m = e.get("match", {})
    key = (m.get("site_name",""), m.get("state",""), m.get("technology",""))
    if key not in existing_keys:
        existing.append(e)
        existing_keys.add(key)
        added += 1
        print(f"  + {m.get('site_name')} [{m.get('state')}]")
    else:
        print(f"  = SKIP: {m.get('site_name')}")

print(f"\nAdded {added} new entries (total: {len(existing)})")
with open("data/inputs/manual_overrides.json", "w") as f:
    json.dump(existing, f, indent=2)
print("Saved.")
