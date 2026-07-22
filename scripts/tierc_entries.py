"""
Generate Tier C manual_overrides.json entries using location_desc clues,
known substation coordinates, and geographic knowledge.
Run: python tierc_entries.py
"""
import json, math

def offset(lat, lon, bearing_deg, dist_km):
    """Return (lat, lon) offset by dist_km in bearing_deg degrees (0=N, 90=E)."""
    b = math.radians(bearing_deg)
    dlat = dist_km / 111.0 * math.cos(b)
    dlon = dist_km / (111.0 * math.cos(math.radians(lat))) * math.sin(b)
    return round(lat + dlat, 3), round(lon + dlon, 3)

def mid(lat1, lon1, lat2, lon2):
    return round((lat1+lat2)/2, 3), round((lon1+lon2)/2, 3)

# Known substation coords (ElectraNet SA, Transgrid NSW)
PARA_SUB        = (-34.754, 138.693)   # Para 132kV substation, Para Hills SA
BLYTH_WEST_SUB  = (-33.834, 138.437)   # Blyth West 275kV, Blyth SA  (from existing Blyth BESS)
DAVENPORT_SUB   = (-32.558, 137.864)   # Davenport 275kV, Port Augusta SA
BUNGAMA_SUB     = (-33.194, 138.081)   # Bungama 275kV, near Port Pirie SA
CRYSTAL_BROOK   = (-33.358, 138.213)   # Crystal Brook town
MURRAY_BRIDGE   = (-35.117, 139.272)   # Murray Bridge town
MONARTO_TOWN    = (-35.094, 139.095)   # Monarto town
ROBERTSTOWN     = (-33.988, 139.089)   # Robertstown SA
NWB_SUB         = (-34.034, 139.667)   # North West Bend substation (Morgan area SA)
GEORGE_TOWN_TAS = (-41.083, 146.893)   # George Town / Bell Bay TAS
KIDSTON_QLD     = (-18.873, 144.156)   # Kidston, NW QLD

entries = []

# ─────────────────────── NSW ───────────────────────────────────────────────

entries += [
  {
    "_comment": "Back Henty Road, Culcairn NSW 2660 (from KCI location_desc)",
    "match": {"site_name": "Ashleigh Park BESS - KCI", "state": "NSW"},
    "overrides": {"lat": -35.667, "lon": 147.042,
                  "geocode_source": "manual", "geocode_display": "Back Henty Road, Culcairn NSW 2660"}
  },
  {
    "_comment": "526 Yanco Rd, Conargo NSW 2710 (from KCI location_desc)",
    "match": {"site_name": "Conargo Wind Farm - KCI", "state": "NSW"},
    "overrides": {"lat": -35.303, "lon": 145.168,
                  "geocode_source": "manual", "geocode_display": "526 Yanco Road, Conargo NSW 2710"}
  },
  {
    "_comment": "1938 Uriarra Road, Uriarra ACT 2611 (from KCI location_desc) — listed under NSW region",
    "match": {"site_name": "Flat Rock BESS - KCI", "state": "NSW"},
    "overrides": {"lat": -35.330, "lon": 148.970,
                  "geocode_source": "manual", "geocode_display": "1938 Uriarra Road, Uriarra ACT 2611"}
  },
  {
    "_comment": "563-571 Miles Franklin Drive, Talbingo NSW 2720 (from KCI location_desc)",
    "match": {"site_name": "Talbingo BESS", "state": "NSW"},
    "overrides": {"lat": -35.529, "lon": 148.316,
                  "geocode_source": "manual", "geocode_display": "Miles Franklin Drive, Talbingo NSW 2720"}
  },
  {
    "_comment": "377 Romani Rd, Booroorban NSW 2710 (from KCI location_desc)",
    "match": {"site_name": "Romani Standalone BESS", "state": "NSW"},
    "overrides": {"lat": -34.970, "lon": 144.900,
                  "geocode_source": "manual", "geocode_display": "Romani Road, Booroorban NSW 2710"}
  },
  {
    "_comment": "Substation Road, Murrumburrah NSW 2587 — Transgrid Harden Substation (from KCI location_desc)",
    "match": {"site_name": "Murrumburrah BESS - KCI", "state": "NSW"},
    "overrides": {"lat": -34.552, "lon": 148.376,
                  "geocode_source": "manual", "geocode_display": "Substation Road, Murrumburrah (Harden) NSW 2587"}
  },
  {
    "_comment": "Holbrook Road, Mangoplah NSW (from DA Planning description)",
    "match": {"site_name": "Mangoplah Battery Energy Storage System", "state": "NSW"},
    "overrides": {"lat": -35.330, "lon": 147.261,
                  "geocode_source": "manual", "geocode_display": "Holbrook Road, Mangoplah NSW"}
  },
  {
    "_comment": "731 Livingstone Gully Rd, Big Springs, Wagga Wagga NSW 2650 (from enquiry location_desc)",
    "match": {"site_name": "Livingstone Battery Energy Storage System", "state": "NSW"},
    "overrides": {"lat": -35.066, "lon": 147.736,
                  "geocode_source": "manual", "geocode_display": "Livingstone Gully Road, Big Springs NSW"}
  },
  {
    "_comment": "Calala Lane, Tamworth — Calala is a suburb of Tamworth NSW (from enquiry location_desc)",
    "match": {"site_name": "Calala Battery Energy Storage System 1 (CABESS1)", "state": "NSW"},
    "overrides": {"lat": -31.108, "lon": 150.917,
                  "geocode_source": "manual", "geocode_display": "Calala Lane, Tamworth NSW"}
  },
  {
    "_comment": "Lucas Heights NSW — ANSTO campus area (from project name, no other location given)",
    "match": {"site_name": "Lucas Heights Bioenergy Facility", "state": "NSW"},
    "overrides": {"lat": -34.053, "lon": 150.981,
                  "geocode_source": "manual", "geocode_display": "Lucas Heights NSW"}
  },
  {
    "_comment": "Off Old Dangelong Road, outside Cooma NSW (from enquiry location_desc)",
    "match": {"site_name": "Cooma Solar Farm", "state": "NSW"},
    "overrides": {"lat": -36.300, "lon": 149.124,
                  "geocode_source": "manual", "geocode_display": "Old Dangelong Road, Cooma NSW"}
  },
  {
    "_comment": "Wallgrove Substation, Rooty Hill NSW (from enquiry location_desc 'adjacent Wallgrove Substation')",
    "match": {"site_name": "NSW Grid BESS", "state": "NSW"},
    "overrides": {"lat": -33.730, "lon": 150.845,
                  "geocode_source": "manual", "geocode_display": "Wallgrove Substation, Rooty Hill NSW"}
  },
  {
    "_comment": "approx. 1.5km SW of Yanco, 6km S of Leeton NSW (from KCI location_desc)",
    "match": {"site_name": "Comet Park BESS - KCI", "state": "NSW"},
    "overrides": {"lat": -34.629, "lon": 146.408,
                  "geocode_source": "manual", "geocode_display": "Near Yanco, Leeton NSW"}
  },
  {
    "_comment": "2km East of Transgrid Muswellbrook 330kV Substation NSW",
    "match": {"site_name": "Muswellbrook Pumped Hydro", "state": "NSW"},
    "overrides": {"lat": -32.258, "lon": 150.916,
                  "geocode_source": "manual", "geocode_display": "Near Muswellbrook 330kV Substation, Muswellbrook NSW"}
  },
  {
    "_comment": "Transgrid Jindera Substation, Jindera NSW (from KCI location_desc)",
    "match": {"site_name": "Jindera BESS - Storage - KCI", "state": "NSW"},
    "overrides": {"lat": -35.943, "lon": 147.065,
                  "geocode_source": "manual", "geocode_display": "Jindera Substation, Jindera NSW"}
  },
  {
    "_comment": "~9km from Tamworth 330kV Substation NSW (from KCI location_desc) — direction not specified",
    "match": {"site_name": "Lambruk Solar Project", "state": "NSW"},
    "overrides": {"lat": -31.050, "lon": 150.870,
                  "geocode_source": "manual", "geocode_display": "Near Tamworth 330kV Substation, NSW"}
  },
  {
    "_comment": "~9km from Wallabadah NSW (from KCI location_desc) — Lindsay Gap area, Liverpool Range",
    "match": {"site_name": "Lindsay Gap BESS", "state": "NSW"},
    "overrides": {"lat": -31.460, "lon": 150.820,
                  "geocode_source": "manual", "geocode_display": "Near Wallabadah, NSW"}
  },
  {
    "_comment": "Oxley Highway between Bendemeer (-30.885, 151.162) and Walcha Road (-30.997, 151.490)",
    "match": {"site_name": "Tara Springs Wind Farm", "state": "NSW"},
    "overrides": {"lat": -30.941, "lon": 151.326,
                  "geocode_source": "manual", "geocode_display": "Oxley Highway between Bendemeer and Walcha Road, NSW"}
  },
  {
    "_comment": "20km NW of Tenterfield NSW (from enquiry location_desc '20km North West from Tenterfield substation')",
    "match": {"site_name": "Donnybrook project", "state": "NSW"},
    "overrides": {"lat": -28.927, "lon": 151.870,
                  "geocode_source": "manual", "geocode_display": "Near Tenterfield NSW"}
  },
  {
    "_comment": "Dubbo Regional LGA (approximate — only location given is 'Dubbo Regional LGA')",
    "match": {"site_name": "West Wellington Wind Farm", "state": "NSW"},
    "overrides": {"lat": -32.241, "lon": 148.601,
                  "geocode_source": "manual", "geocode_display": "Dubbo Regional LGA, NSW"}
  },
  {
    "_comment": "Hargraves township area, Mid-Western NSW (same area as Hargraves Energy Project)",
    "match": {"site_name": "Hargaves BESS", "state": "NSW"},
    "overrides": {"lat": -32.929, "lon": 149.451,
                  "geocode_source": "manual", "geocode_display": "Hargraves NSW"}
  },
  {
    "_comment": "Hargraves township area, Mid-Western NSW",
    "match": {"site_name": "Hargaves Wind Farm", "state": "NSW"},
    "overrides": {"lat": -32.929, "lon": 149.451,
                  "geocode_source": "manual", "geocode_display": "Hargraves NSW"}
  },
  {
    "_comment": "Near Hay NSW — project name indicates Hay Shire location",
    "match": {"site_name": "Hay Sun Farm", "state": "NSW"},
    "overrides": {"lat": -34.511, "lon": 144.843,
                  "geocode_source": "manual", "geocode_display": "Near Hay NSW"}
  },
  {
    "_comment": "Burroway locality, Warren-Narromine area, central western NSW",
    "match": {"site_name": "Burroway Energy Hub", "state": "NSW"},
    "overrides": {"lat": -32.021, "lon": 147.588,
                  "geocode_source": "manual", "geocode_display": "Burroway, Central Western NSW"}
  },
  {
    "_comment": "Deargee locality, New England Tablelands east of Glen Innes NSW",
    "match": {"site_name": "Deargee Solar And BESS", "state": "NSW"},
    "overrides": {"lat": -29.700, "lon": 151.490,
                  "geocode_source": "manual", "geocode_display": "Deargee, New England NSW"}
  },
  {
    "_comment": "Near Bookham village, Boorowa LGA, southern tablelands NSW",
    "match": {"site_name": "Bookham WF and BESS", "state": "NSW"},
    "overrides": {"lat": -34.638, "lon": 148.727,
                  "geocode_source": "manual", "geocode_display": "Bookham NSW"}
  },
  {
    "_comment": "Macleay River valley between Armidale and Kempsey (from DA description)",
    "match": {"site_name": "Oven Mountain Pumped Hydro Energy Storage", "state": "NSW"},
    "overrides": {"lat": -30.700, "lon": 152.100,
                  "geocode_source": "manual", "geocode_display": "Macleay River valley, NSW"}
  },
  # NSW offshore wind (approximate offshore positions)
  {
    "_comment": "Offshore Eden NSW (~30km E of Eden off the south coast)",
    "match": {"site_name": "Eden Offshore Wind Farm", "state": "NSW"},
    "overrides": {"lat": -37.100, "lon": 150.300,
                  "geocode_source": "manual", "geocode_display": "Offshore Eden, NSW"}
  },
  {
    "_comment": "Offshore Illawarra coast (~40km E of Wollongong)",
    "match": {"site_name": "Illawarra Offshore Wind Farm", "state": "NSW"},
    "overrides": {"lat": -34.400, "lon": 151.300,
                  "geocode_source": "manual", "geocode_display": "Offshore Illawarra coast, NSW"}
  },
  {
    "_comment": "17-35km offshore between Kiama and Currarong (from KCI location_desc)",
    "match": {"site_name": "South Pacific Offshore Wind Project", "state": "NSW"},
    "overrides": {"lat": -34.840, "lon": 151.350,
                  "geocode_source": "manual", "geocode_display": "Offshore Illawarra coast between Kiama and Currarong, NSW"}
  },
  {
    "_comment": "Offshore Ulladulla NSW (~30km E of Ulladulla)",
    "match": {"site_name": "Ulladulla Offshore Wind Farm", "state": "NSW"},
    "overrides": {"lat": -35.350, "lon": 151.100,
                  "geocode_source": "manual", "geocode_display": "Offshore Ulladulla, NSW"}
  },
  {
    "_comment": "Offshore Newcastle NSW (~40km E of Newcastle)",
    "match": {"site_name": "Novocastrian Offshore Wind Farm", "state": "NSW"},
    "overrides": {"lat": -32.900, "lon": 152.400,
                  "geocode_source": "manual", "geocode_display": "Offshore Newcastle, NSW"}
  },
]

# ─────────────────────── SA ────────────────────────────────────────────────

# Para Substation: both BESS projects (Enquiry and KCI Application)
entries += [
  {
    "_comment": "Para Substation 132kV, Para Hills SA (from KCI location_desc)",
    "match": {"site_name": "Blacktop BESS - KCI", "state": "SA"},
    "overrides": {"lat": PARA_SUB[0], "lon": PARA_SUB[1],
                  "geocode_source": "manual", "geocode_display": "Para 132kV Substation, Para Hills SA"}
  },
  {
    "_comment": "Para Substation SA (from Enquiry location_desc)",
    "match": {"site_name": "Blacktop BESS", "state": "SA"},
    "overrides": {"lat": PARA_SUB[0], "lon": PARA_SUB[1],
                  "geocode_source": "manual", "geocode_display": "Para Substation, Para Hills SA"}
  },
  {
    "_comment": "ElectraNet Bungama 275kV Substation, near Port Pirie SA",
    "match": {"site_name": "Bungama BESS (Risen)", "state": "SA"},
    "overrides": {"lat": BUNGAMA_SUB[0], "lon": BUNGAMA_SUB[1],
                  "geocode_source": "manual", "geocode_display": "Bungama 275kV Substation, Port Pirie SA"}
  },
  {
    "_comment": "Adjacent to Carmody's Hill Wind Farm, Campbell Range near Georgetown SA",
    "match": {"site_name": "Carmodys Hill BESS", "state": "SA"},
    "overrides": {"lat": -33.350, "lon": 138.430,
                  "geocode_source": "manual", "geocode_display": "Campbell Range, Georgetown SA"}
  },
  {
    "_comment": "Midpoint between Davenport sub (-32.558, 137.864) and Blyth West sub (-33.834, 138.437) — Hughes Gap area",
    "match": {"site_name": "Hughes Gap BESS - KCI", "state": "SA"},
    "overrides": {"lat": mid(DAVENPORT_SUB[0], DAVENPORT_SUB[1], BLYTH_WEST_SUB[0], BLYTH_WEST_SUB[1])[0],
                  "lon": mid(DAVENPORT_SUB[0], DAVENPORT_SUB[1], BLYTH_WEST_SUB[0], BLYTH_WEST_SUB[1])[1],
                  "geocode_source": "manual", "geocode_display": "Hughes Gap, Mid North SA"}
  },
  {
    "_comment": "Midpoint between Davenport sub and Blyth West sub — Hughes Gap area SA",
    "match": {"site_name": "Hughes Gap WF - KCI", "state": "SA"},
    "overrides": {"lat": mid(DAVENPORT_SUB[0], DAVENPORT_SUB[1], BLYTH_WEST_SUB[0], BLYTH_WEST_SUB[1])[0],
                  "lon": mid(DAVENPORT_SUB[0], DAVENPORT_SUB[1], BLYTH_WEST_SUB[0], BLYTH_WEST_SUB[1])[1],
                  "geocode_source": "manual", "geocode_display": "Hughes Gap, Mid North SA"}
  },
  {
    "_comment": "Blyth West 275kV Substation SA (same as Blyth BESS already on map)",
    "match": {"site_name": "Blyth West BESS", "state": "SA"},
    "overrides": {"lat": BLYTH_WEST_SUB[0], "lon": BLYTH_WEST_SUB[1],
                  "geocode_source": "manual", "geocode_display": "Blyth West 275kV Substation, Blyth SA"}
  },
  {
    "_comment": "~6km north of Crystal Brook SA (from enquiry: 'Cut-in switchyard 6km north of Crystal Brook')",
    "match": {"site_name": "Crystal Brook Energy Park", "state": "SA"},
    "overrides": {"lat": round(CRYSTAL_BROOK[0] + 6/111, 3), "lon": CRYSTAL_BROOK[1],
                  "geocode_source": "manual", "geocode_display": "North of Crystal Brook SA"}
  },
  {
    "_comment": "6.5km from Murray Bridge towards Monarto SA (from enquiry location_desc)",
    "match": {"site_name": "Murray Bridge Hahndorf Pumping Station 2 Solar", "state": "SA"},
    "overrides": {"lat": -35.076, "lon": 139.208,
                  "geocode_source": "manual", "geocode_display": "Near Murray Bridge, towards Monarto SA"}
  },
  {
    "_comment": "0.5km east of Robertstown Substation SA (from Application location_desc)",
    "match": {"site_name": "Bright BESS at Robertstown", "state": "SA"},
    "overrides": {"lat": ROBERTSTOWN[0], "lon": round(ROBERTSTOWN[1] + 0.5/(111*math.cos(math.radians(ROBERTSTOWN[0]))), 3),
                  "geocode_source": "manual", "geocode_display": "Robertstown Substation, Robertstown SA"}
  },
  {
    "_comment": "2km NW of Para Substation (-34.754, 138.693), Para Hills SA",
    "match": {"site_name": "Para Hill BESS", "state": "SA"},
    "overrides": {"lat": offset(PARA_SUB[0], PARA_SUB[1], 315, 2)[0],
                  "lon": offset(PARA_SUB[0], PARA_SUB[1], 315, 2)[1],
                  "geocode_source": "manual", "geocode_display": "Near Para Substation, Para Hills SA"}
  },
  {
    "_comment": "2.5km East of ElectraNet North West Bend substation, Riverland SA",
    "match": {"site_name": "Riverland BESS", "state": "SA"},
    "overrides": {"lat": NWB_SUB[0], "lon": round(NWB_SUB[1] + 2.5/(111*math.cos(math.radians(NWB_SUB[0]))), 3),
                  "geocode_source": "manual", "geocode_display": "Near North West Bend Substation, Riverland SA"}
  },
  {
    "_comment": "Near Nyrstar Smelter, Port Pirie SA (from KCI location_desc)",
    "match": {"site_name": "Port Pirie Solar Farm - KCI", "state": "SA"},
    "overrides": {"lat": -33.186, "lon": 138.010,
                  "geocode_source": "manual", "geocode_display": "Near Nyrstar Smelter, Port Pirie SA"}
  },
  {
    "_comment": "Leigh Creek SA — former coal town, Flinders Ranges (project name indicates location)",
    "match": {"site_name": "Leigh Creek Energy Project", "state": "SA"},
    "overrides": {"lat": -30.578, "lon": 138.408,
                  "geocode_source": "manual", "geocode_display": "Leigh Creek SA"}
  },
  {
    "_comment": "Near Whyalla SA (from KCI location_desc 'Whyalla BESS')",
    "match": {"site_name": "Whyalla BESS - KCI", "state": "SA"},
    "overrides": {"lat": -33.015, "lon": 137.567,
                  "geocode_source": "manual", "geocode_display": "Whyalla SA"}
  },
  {
    "_comment": "Mobilong 132kV Substation, Murray Bridge SA (from Application location_desc)",
    "match": {"site_name": "Mobilong BESS", "state": "SA"},
    "overrides": {"lat": -35.103, "lon": 139.265,
                  "geocode_source": "manual", "geocode_display": "Mobilong 132kV Substation, Murray Bridge SA"}
  },
  {
    "_comment": "Near ElectraNet NWB Substation (North West Bend), Morgan SA (from KCI location_desc)",
    "match": {"site_name": "Morgan Long Duration Energy Storage - KCI", "state": "SA"},
    "overrides": {"lat": NWB_SUB[0], "lon": NWB_SUB[1],
                  "geocode_source": "manual", "geocode_display": "Near NWB Substation, Morgan SA"}
  },
  {
    "_comment": "Tungkillo substation area SA — between Murray Bridge and Mannum",
    "match": {"site_name": "Tungkillo BESS - KCI", "state": "SA"},
    "overrides": {"lat": -34.997, "lon": 139.120,
                  "geocode_source": "manual", "geocode_display": "Tungkillo Substation, Tungkillo SA"}
  },
  {
    "_comment": "Baroota SA — southern Flinders Ranges, near Port Pirie (project name indicates location)",
    "match": {"site_name": "Baroota Pumped Hydro Project", "state": "SA"},
    "overrides": {"lat": -33.109, "lon": 137.955,
                  "geocode_source": "manual", "geocode_display": "Baroota, Southern Flinders Ranges SA"}
  },
  {
    "_comment": "Aurora Energy Project precinct ~20km N of Port Augusta SA (co-located with Vast Solar 1 precinct)",
    "match": {"site_name": "Aurora Solar Energy Project - Phase 1", "state": "SA"},
    "overrides": {"lat": -32.280, "lon": 137.768,
                  "geocode_source": "manual", "geocode_display": "Aurora Energy Project precinct, Port Augusta SA"}
  },
  {
    "_comment": "Adjacent to Bundey (Bundy) 275kV Substation SA — Goyder region near Burra",
    "match": {"site_name": "Bundy Energy Hub A", "state": "SA"},
    "overrides": {"lat": -33.683, "lon": 138.940,
                  "geocode_source": "manual", "geocode_display": "Near Bundey Substation, Burra SA"}
  },
  {
    "_comment": "Adjacent to Bundey substation to the north — Goyder North area SA",
    "match": {"site_name": "Goyder North BESS 2", "state": "SA"},
    "overrides": {"lat": -33.550, "lon": 139.100,
                  "geocode_source": "manual", "geocode_display": "North of Bundey Substation, Goyder SA"}
  },
  {
    "_comment": "Near ElectraNet Monash substation, Riverland SA (1km N of Monash substation near Barmera)",
    "match": {"site_name": "Monash Solar Farm - KCI", "state": "SA"},
    "overrides": {"lat": -34.357, "lon": 140.537,
                  "geocode_source": "manual", "geocode_display": "Near Monash Substation, Riverland SA"}
  },
]

# ─────────────────────── VIC ───────────────────────────────────────────────

entries += [
  {
    "_comment": "Near Barnawartha VIC — border area with NSW, near Wodonga/Albury",
    "match": {"site_name": "Barnawartha Solar and Energy Storage", "state": "VIC"},
    "overrides": {"lat": -36.173, "lon": 146.941,
                  "geocode_source": "manual", "geocode_display": "Barnawartha VIC"}
  },
  {
    "_comment": "Deer Park VIC — western Melbourne suburb, near Western Ring Rd industrial area",
    "match": {"site_name": "Deer Park BESS - Akaysha", "state": "VIC"},
    "overrides": {"lat": -37.782, "lon": 144.785,
                  "geocode_source": "manual", "geocode_display": "Deer Park VIC"}
  },
  {
    "_comment": "Near Terang VIC — Corangamite shire, south-west VIC (from KCI name 'East Terang')",
    "match": {"site_name": "East Terang BESS - KCI", "state": "VIC"},
    "overrides": {"lat": -38.249, "lon": 142.960,
                  "geocode_source": "manual", "geocode_display": "East Terang, Corangamite VIC"}
  },
  {
    "_comment": "Near Horsham VIC — Wimmera region (from KCI name 'EIWA Horsham')",
    "match": {"site_name": "EIWA Horsham BESS - KCI", "state": "VIC"},
    "overrides": {"lat": -36.713, "lon": 142.200,
                  "geocode_source": "manual", "geocode_display": "Horsham VIC"}
  },
  {
    "_comment": "North of Golden Plains Wind Farm substation, Rokewood VIC (Golden Plains BESS 2 is already at -37.900)",
    "match": {"site_name": "Golden Plains BESS North", "state": "VIC"},
    "overrides": {"lat": -37.800, "lon": 143.717,
                  "geocode_source": "manual", "geocode_display": "Near Golden Plains Wind Farm, Rokewood VIC"}
  },
  {
    "_comment": "Belgrave-Hallam Road, south-eastern Melbourne fringe — micro hydro on local waterway",
    "match": {"site_name": "HYMIVC06 Belgrave-Hallam Rd Micro Hydro", "state": "VIC"},
    "overrides": {"lat": -37.985, "lon": 145.319,
                  "geocode_source": "manual", "geocode_display": "Belgrave-Hallam Road, VIC"}
  },
  {
    "_comment": "Near Kerang VIC (same area as Kerang Solar Plant at -35.735, 143.920)",
    "match": {"site_name": "Kerang Battery Plant", "state": "VIC"},
    "overrides": {"lat": -35.735, "lon": 143.920,
                  "geocode_source": "manual", "geocode_display": "Kerang VIC"}
  },
  {
    "_comment": "Lovely Banks VIC — between Geelong and Ballarat on Midland Hwy",
    "match": {"site_name": "Lovely Banks Renewable Energy Hub - KCI", "state": "VIC"},
    "overrides": {"lat": -37.848, "lon": 144.225,
                  "geocode_source": "manual", "geocode_display": "Lovely Banks VIC"}
  },
  {
    "_comment": "Loy Yang area, Latrobe Valley VIC — 'LYA' likely refers to Loy Yang A",
    "match": {"site_name": "LYA BESS", "state": "VIC"},
    "overrides": {"lat": -38.232, "lon": 146.503,
                  "geocode_source": "manual", "geocode_display": "Loy Yang, Latrobe Valley VIC"}
  },
  {
    "_comment": "Near Mansfield VIC — alpine foothills, NE Victoria",
    "match": {"site_name": "Mansfield Solar Farm - Solar - KCI", "state": "VIC"},
    "overrides": {"lat": -37.055, "lon": 146.090,
                  "geocode_source": "manual", "geocode_display": "Mansfield VIC"}
  },
  {
    "_comment": "Near Mansfield VIC — co-located storage component of Mansfield Solar Farm",
    "match": {"site_name": "Mansfield Solar Farm - Storage - KCI", "state": "VIC"},
    "overrides": {"lat": -37.055, "lon": 146.090,
                  "geocode_source": "manual", "geocode_display": "Mansfield VIC"}
  },
  {
    "_comment": "Nowingi locality, Mallee VIC — north of Ouyen, near Big Desert",
    "match": {"site_name": "Nowingi Solar Storage - Solar", "state": "VIC"},
    "overrides": {"lat": -34.520, "lon": 142.010,
                  "geocode_source": "manual", "geocode_display": "Nowingi, Mallee VIC"}
  },
  {
    "_comment": "Nowingi locality, Mallee VIC — co-located storage component",
    "match": {"site_name": "Nowingi Solar Storage - Storage", "state": "VIC"},
    "overrides": {"lat": -34.520, "lon": 142.010,
                  "geocode_source": "manual", "geocode_display": "Nowingi, Mallee VIC"}
  },
  {
    "_comment": "Near Portland VIC — south-west VIC coast (from project name; Pacific Green have Portland projects)",
    "match": {"site_name": "Pacific Green Energy Park – Portland", "state": "VIC"},
    "overrides": {"lat": -38.365, "lon": 141.605,
                  "geocode_source": "manual", "geocode_display": "Portland VIC"}
  },
  {
    "_comment": "Near Portland VIC (from KCI name 'Portland Wind Farm')",
    "match": {"site_name": "Portland Wind Farm - KCI", "state": "VIC"},
    "overrides": {"lat": -38.365, "lon": 141.605,
                  "geocode_source": "manual", "geocode_display": "Portland VIC"}
  },
  {
    "_comment": "Strathbogie Ranges VIC — NE Victoria ranges between Mansfield and Euroa",
    "match": {"site_name": "Strathbogie Ranges Wind Farm", "state": "VIC"},
    "overrides": {"lat": -36.900, "lon": 145.800,
                  "geocode_source": "manual", "geocode_display": "Strathbogie Ranges VIC"}
  },
  {
    "_comment": "Tarrone VIC — near Port Fairy/Koroit, south-west VIC (peaking gas turbine site)",
    "match": {"site_name": "Tarrone GT", "state": "VIC"},
    "overrides": {"lat": -38.367, "lon": 142.517,
                  "geocode_source": "manual", "geocode_display": "Tarrone, SW VIC"}
  },
  {
    "_comment": "Wimmera Plains area VIC — between Horsham and Dimboola, Wimmera region",
    "match": {"site_name": "Wimmera Plains Wind Farm - KCI", "state": "VIC"},
    "overrides": {"lat": -36.400, "lon": 142.020,
                  "geocode_source": "manual", "geocode_display": "Wimmera Plains VIC"}
  },
  {
    "_comment": "Wimmera Plains area VIC — Stage 2 of Wimmera Plains Wind Farm",
    "match": {"site_name": "Wimmera Plains Energy Facility Stage 2 - KCI", "state": "VIC"},
    "overrides": {"lat": -36.400, "lon": 142.020,
                  "geocode_source": "manual", "geocode_display": "Wimmera Plains VIC"}
  },
  {
    "_comment": "Moorabool area VIC — near Lal Lal, between Geelong and Ballarat (Cordoba BESS / Moorabool Wind Farm)",
    "match": {"site_name": "Zero Moorabool BESS (Cordoba BESS)", "state": "VIC"},
    "overrides": {"lat": -37.693, "lon": 144.030,
                  "geocode_source": "manual", "geocode_display": "Near Moorabool, VIC"}
  },
  {
    "_comment": "Moorabool area VIC — KCI version of Cordoba/Zero Moorabool BESS",
    "match": {"site_name": "Zero Moorabool BESS (Cordoba BESS) - KCI", "state": "VIC"},
    "overrides": {"lat": -37.693, "lon": 144.030,
                  "geocode_source": "manual", "geocode_display": "Near Moorabool, VIC"}
  },
  # VIC offshore wind (approximate positions in Bass Strait / Gippsland offshore)
  {
    "_comment": "Gippsland Offshore — west of Deal Island, Bass Strait",
    "match": {"site_name": "Deal 1 (West) Off Shore Wind Farm", "state": "VIC"},
    "overrides": {"lat": -38.900, "lon": 146.800,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Gippsland Offshore — east of Deal Island, Bass Strait",
    "match": {"site_name": "Deal 2 (East) Off Shore Wind Farm", "state": "VIC"},
    "overrides": {"lat": -38.900, "lon": 147.800,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Gippsland Offshore — Bass Strait, off the Gippsland coast",
    "match": {"site_name": "Great Eastern Offshore Wind - KCI", "state": "VIC"},
    "overrides": {"lat": -39.100, "lon": 147.500,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Gippsland Offshore — southern Bass Strait",
    "match": {"site_name": "Greater Southern Offshore Wind - KCI", "state": "VIC"},
    "overrides": {"lat": -39.500, "lon": 147.000,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Gippsland Offshore — Bass Strait off the Gippsland coast",
    "match": {"site_name": "Southern Winds Offshore Wind", "state": "VIC"},
    "overrides": {"lat": -39.200, "lon": 147.800,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Gippsland Offshore — Orsted Gippsland 01 offshore wind project in Bass Strait",
    "match": {"site_name": "Orsted Gippsland 01 Windfarm", "state": "VIC"},
    "overrides": {"lat": -38.800, "lon": 147.500,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Kilcunda offshore — Site A, Bass Strait near Kilcunda VIC",
    "match": {"site_name": "Bass Strait Offshore Wind Farm - Site A", "state": "VIC"},
    "overrides": {"lat": -38.600, "lon": 145.600,
                  "geocode_source": "manual", "geocode_display": "Kilcunda Offshore, VIC"}
  },
  {
    "_comment": "Kilcunda offshore — Site B, Bass Strait near Kilcunda VIC",
    "match": {"site_name": "Bass Strait Offshore Wind Farm - Site B", "state": "VIC"},
    "overrides": {"lat": -38.700, "lon": 146.000,
                  "geocode_source": "manual", "geocode_display": "Kilcunda Offshore, VIC"}
  },
  {
    "_comment": "Gippsland offshore — Gippsland A&B wind project, Bass Strait",
    "match": {"site_name": "Gippsland A&B", "state": "VIC"},
    "overrides": {"lat": -39.000, "lon": 147.200,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Gippsland offshore — Greater Gippsland offshore wind project",
    "match": {"site_name": "Greater Gippsland Offshore Wind Project", "state": "VIC"},
    "overrides": {"lat": -39.300, "lon": 147.000,
                  "geocode_source": "manual", "geocode_display": "Gippsland Offshore, VIC"}
  },
  {
    "_comment": "Offshore Portland/south-west VIC coast — Blue Mackerel North",
    "match": {"site_name": "Blue Mackerel North Off Shore Wind Farm", "state": "VIC"},
    "overrides": {"lat": -38.700, "lon": 141.000,
                  "geocode_source": "manual", "geocode_display": "Offshore South-West VIC"}
  },
  {
    "_comment": "Offshore south-west VIC — Blue Mackerel North (Enquiry version)",
    "match": {"site_name": "Blue Mackerel North", "state": "VIC"},
    "overrides": {"lat": -38.700, "lon": 141.000,
                  "geocode_source": "manual", "geocode_display": "Offshore South-West VIC"}
  },
  {
    "_comment": "Offshore southern VIC — Cape Winds, approximately off Cape Liptrap / Wilson's Promontory area",
    "match": {"site_name": "Cape Winds Offshore Wind Farm", "state": "VIC"},
    "overrides": {"lat": -39.000, "lon": 145.800,
                  "geocode_source": "manual", "geocode_display": "Offshore Southern VIC"}
  },
]

# ─────────────────────── TAS ───────────────────────────────────────────────

entries += [
  {
    "_comment": "George Town BESS near Bell Bay, George Town TAS (same area as George Town Wind Farm)",
    "match": {"site_name": "George Town BESS - KCI", "state": "TAS"},
    "overrides": {"lat": GEORGE_TOWN_TAS[0], "lon": GEORGE_TOWN_TAS[1],
                  "geocode_source": "manual", "geocode_display": "Bell Bay area, George Town TAS"}
  },
  {
    "_comment": "Immediately east of George Town Substation, George Town LSA TAS (from KCI location_desc)",
    "match": {"site_name": "Northern Midlands Solar Farm - KCI", "state": "TAS"},
    "overrides": {"lat": GEORGE_TOWN_TAS[0], "lon": round(GEORGE_TOWN_TAS[1] + 0.02, 3),
                  "geocode_source": "manual", "geocode_display": "George Town Substation area, TAS"}
  },
  {
    "_comment": "Bell Bay industrial area, George Town TAS — proposed wind farm at Bell Bay",
    "match": {"site_name": "Bellbay Wind Farm", "state": "TAS"},
    "overrides": {"lat": -41.083, "lon": 146.893,
                  "geocode_source": "manual", "geocode_display": "Bell Bay, George Town TAS"}
  },
  {
    "_comment": "West Coast LGA TAS — near Queenstown/Zeehan area, western Tasmania",
    "match": {"site_name": "Whaleback Ridge Wind Farm - KCI", "state": "TAS"},
    "overrides": {"lat": -42.079, "lon": 145.551,
                  "geocode_source": "manual", "geocode_display": "West Coast, TAS"}
  },
  {
    "_comment": "Battery of the Nation Stage 2b — Hydro Tasmania highland development, Lake Cethana area",
    "match": {"site_name": "Battery of the Nation - Stage 2b", "state": "TAS"},
    "overrides": {"lat": -41.559, "lon": 145.959,
                  "geocode_source": "manual", "geocode_display": "Hydro Tasmania highlands (Lake Cethana area)"}
  },
  {
    "_comment": "Battery of the Nation Stage 3b — Hydro Tasmania highland development, Tarraleah area",
    "match": {"site_name": "Battery of the Nation - Stage 3b", "state": "TAS"},
    "overrides": {"lat": -42.290, "lon": 146.435,
                  "geocode_source": "manual", "geocode_display": "Hydro Tasmania highlands (Tarraleah area)"}
  },
  {
    "_comment": "Offshore in Bass Strait, landing point TBC — approximate central Bass Strait position",
    "match": {"site_name": "Bass Offshore Wind Energy Project", "state": "TAS"},
    "overrides": {"lat": -39.500, "lon": 145.000,
                  "geocode_source": "manual", "geocode_display": "Offshore Bass Strait"}
  },
]

# ─────────────────────── QLD ───────────────────────────────────────────────

entries += [
  {
    "_comment": "Same location as Kidston Pumped Hydro Phase 1 (-18.873, 144.156) — Phase Two solar co-located",
    "match": {"site_name": "Kidston Solar Project Phase Two", "state": "QLD"},
    "overrides": {"lat": KIDSTON_QLD[0], "lon": KIDSTON_QLD[1],
                  "geocode_source": "manual", "geocode_display": "Kennedy Energy Park, Kidston QLD"}
  },
  {
    "_comment": "Grosvenor Mine near Moranbah, Bowen Basin QLD — coal mine gas project",
    "match": {"site_name": "Grosvenor 2 Waste Coal Mine Gas Power Station", "state": "QLD"},
    "overrides": {"lat": -22.001, "lon": 148.046,
                  "geocode_source": "manual", "geocode_display": "Near Grosvenor Mine, Moranbah QLD"}
  },
  {
    "_comment": "Cressbrook Creek / Cressbrook Dam area, SE QLD — pumped hydro site",
    "match": {"site_name": "Cressbrook Pumped Hydro Project", "state": "QLD"},
    "overrides": {"lat": -27.023, "lon": 152.184,
                  "geocode_source": "manual", "geocode_display": "Cressbrook area, SE QLD"}
  },
  {
    "_comment": "Mt Cotton QLD — near Redland Bay, SE QLD (project name indicates location)",
    "match": {"site_name": "Mt Cotton Biomass Cogeneration Power Station", "state": "QLD"},
    "overrides": {"lat": -27.694, "lon": 153.234,
                  "geocode_source": "manual", "geocode_display": "Mt Cotton QLD"}
  },
  {
    "_comment": "Lockyer Valley QLD — near Gatton/Plainland (project name indicates location)",
    "match": {"site_name": "Lockyer Valley Energy Project", "state": "QLD"},
    "overrides": {"lat": -27.556, "lon": 152.282,
                  "geocode_source": "manual", "geocode_display": "Lockyer Valley QLD"}
  },
  {
    "_comment": "Near Gin Gin QLD — from KCI location_desc 'GIN GIN TO STR-6076 F814/1'",
    "match": {"site_name": "Rutherglen Battery - KCI", "state": "QLD"},
    "overrides": {"lat": -24.990, "lon": 151.121,
                  "geocode_source": "manual", "geocode_display": "Near Gin Gin QLD"}
  },
  {
    "_comment": "Near Gin Gin QLD — from KCI location_desc 'GIN GIN TO STR-6076 F814/1'",
    "match": {"site_name": "Rutherglen Solar Farm - KCI", "state": "QLD"},
    "overrides": {"lat": -24.990, "lon": 151.121,
                  "geocode_source": "manual", "geocode_display": "Near Gin Gin QLD"}
  },
  {
    "_comment": "Tara area, Darling Downs QLD — from KCI location_desc 'BRAEMAR TO BULLI CREEK' (Tara Wind Farm near Tara)",
    "match": {"site_name": "Tara Wind Farm - KCI", "state": "QLD"},
    "overrides": {"lat": -27.451, "lon": 149.900,
                  "geocode_source": "manual", "geocode_display": "Near Tara, Darling Downs QLD"}
  },
  {
    "_comment": "Woolooga township near Gympie, Wide Bay QLD — from KCI name",
    "match": {"site_name": "Woolooga BESS - KCI", "state": "QLD"},
    "overrides": {"lat": -26.070, "lon": 152.440,
                  "geocode_source": "manual", "geocode_display": "Woolooga, Gympie Region QLD"}
  },
  {
    "_comment": "Gemfields gemstone mining area, Central Highlands QLD — near Emerald",
    "match": {"site_name": "Gemfields Integrated Facility - Wind And Solar", "state": "QLD"},
    "overrides": {"lat": -23.270, "lon": 147.700,
                  "geocode_source": "manual", "geocode_display": "Gemfields, Central QLD"}
  },
  {
    "_comment": "Murilla locality near Miles QLD — gas pipeline area, Surat Basin",
    "match": {"site_name": "Murilla GPG", "state": "QLD"},
    "overrides": {"lat": -26.620, "lon": 150.010,
                  "geocode_source": "manual", "geocode_display": "Murilla, Miles QLD"}
  },
  {
    "_comment": "Lansdown Eco-Industrial Precinct near Townsville QLD — from KCI 'STR-4559 TO ROSS' (Ross substation, Townsville)",
    "match": {"site_name": "Lansdown Solar North", "state": "QLD"},
    "overrides": {"lat": -19.500, "lon": 146.900,
                  "geocode_source": "manual", "geocode_display": "Lansdown Industrial Precinct, Townsville QLD"}
  },
  {
    "_comment": "Burdekin region, North QLD — near Ayr/Home Hill (from KCI name 'Burdekin Solar Farm')",
    "match": {"site_name": "Burdekin Solar Farm - KCI", "state": "QLD"},
    "overrides": {"lat": -19.663, "lon": 147.408,
                  "geocode_source": "manual", "geocode_display": "Burdekin, North QLD"}
  },
  {
    "_comment": "Dugald River area, near Cloncurry, NW QLD — Dugald River Mine (zinc) is in that area",
    "match": {"site_name": "Dugald River Wind Faarm", "state": "QLD"},
    "overrides": {"lat": -20.800, "lon": 140.500,
                  "geocode_source": "manual", "geocode_display": "Dugald River area, NW QLD"}
  },
]

# ─── Load existing overrides, append new ones, write back ──────────────────
with open("data/inputs/manual_overrides.json") as f:
    existing = json.load(f)

# Avoid duplicates by checking (site_name, state) pairs
existing_keys = set()
for e in existing:
    m = e.get("match", {})
    existing_keys.add((m.get("site_name", ""), m.get("state", ""), m.get("technology", "")))

added = 0
for e in entries:
    m = e.get("match", {})
    key = (m.get("site_name", ""), m.get("state", ""), m.get("technology", ""))
    if key not in existing_keys:
        existing.append(e)
        existing_keys.add(key)
        added += 1
        print(f"  + {m.get('site_name')} [{m.get('state')}]")
    else:
        print(f"  = SKIP (already exists): {m.get('site_name')}")

print(f"\nAdded {added} new entries (total: {len(existing)})")

with open("data/inputs/manual_overrides.json", "w") as f:
    json.dump(existing, f, indent=2)
print("Saved data/inputs/manual_overrides.json")
