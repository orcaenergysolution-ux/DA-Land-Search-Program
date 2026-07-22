from append_vision_extracts import append

markers = [
    # vic_r0c0 - NW VIC (Murraylink/Red Cliffs/Horsham)
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":81,"capacity_conf":"high","nearest_label":"Red Cliffs / Buronga","label_conf":"high","notes":"Karadoc Solar"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":190,"capacity_conf":"high","nearest_label":"Red Cliffs","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","fuel_conf":"medium","stage":"Registration","stage_conf":"medium","capacity_mw":150,"capacity_conf":"high","nearest_label":"Red Cliffs","label_conf":"high","notes":"green battery"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":88,"capacity_conf":"high","nearest_label":"Wemen","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":88,"capacity_conf":"high","nearest_label":"Wemen","label_conf":"high","notes":"second 88 MW solar"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":200,"capacity_conf":"high","nearest_label":"Wemen","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Pre-Registration","stage_conf":"high","capacity_mw":150,"capacity_conf":"high","nearest_label":"Wemen","label_conf":"high","notes":"yellow-green sun"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","fuel_conf":"medium","stage":"Registration","stage_conf":"medium","capacity_mw":220,"capacity_conf":"high","nearest_label":"Wemen","label_conf":"high","notes":"green battery"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":185,"capacity_conf":"high","nearest_label":"Balranald area","label_conf":"medium","notes":"dark blue battery"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":25,"capacity_conf":"high","nearest_label":"Murray River area","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":50,"capacity_conf":"high","nearest_label":"Murray River area","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","fuel_conf":"medium","stage":"Registration","stage_conf":"medium","capacity_mw":171,"capacity_conf":"high","nearest_label":"Murray River area","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":7,"capacity_conf":"high","nearest_label":"Kiata","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":31,"capacity_conf":"high","nearest_label":"Kiata","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":203,"capacity_conf":"high","nearest_label":"Horsham","label_conf":"high","notes":"Murra Warra Wind Farm"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":225,"capacity_conf":"high","nearest_label":"Horsham","label_conf":"high","notes":"Murra Warra 2"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"OCGT","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":178,"capacity_conf":"high","nearest_label":"Horsham","label_conf":"high","notes":"orange flame"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":20,"capacity_conf":"high","nearest_label":"V3 zone","label_conf":"low"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","fuel_conf":"medium","stage":"Pre-Registration","stage_conf":"medium","capacity_mw":119,"capacity_conf":"high","nearest_label":"Horsham","label_conf":"high"},

    # vic_r0c1 - North VIC (cross-border, dense small)
    {"state":"VIC","tile":"vic_r0c1","fuel":"Solar","fuel_conf":"low","stage":"Operational","stage_conf":"low","capacity_mw":70,"capacity_conf":"low","nearest_label":"Hay/Deniliquin area","label_conf":"low","notes":"cluster - low resolution"},
    {"state":"VIC","tile":"vic_r0c1","fuel":"Solar","fuel_conf":"low","stage":"Operational","stage_conf":"low","capacity_mw":95,"capacity_conf":"low","nearest_label":"Hay/Deniliquin area","label_conf":"low"},
    {"state":"VIC","tile":"vic_r0c1","fuel":"Solar","fuel_conf":"low","stage":"Operational","stage_conf":"low","capacity_mw":200,"capacity_conf":"low","nearest_label":"Mulwala/Corowa","label_conf":"low"},

    # vic_r0c2 - NE VIC (mostly cross-border, legend in this region)
    # Limited markers visible

    # vic_r1c0 - SW VIC (Heywood / Portland)
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":420,"capacity_conf":"medium","nearest_label":"Macarthur","label_conf":"high","notes":"Macarthur Wind Farm"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":192,"capacity_conf":"medium","nearest_label":"Portland","label_conf":"high","notes":"Portland Wind"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":107,"capacity_conf":"medium","nearest_label":"Heywood","label_conf":"high","notes":"Cape Bridgewater"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":67,"capacity_conf":"medium","nearest_label":"Heywood","label_conf":"high","notes":"Cape Nelson"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":376,"capacity_conf":"medium","nearest_label":"Tarrone / Mortlake","label_conf":"medium","notes":"Dundonnell Wind"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":556,"capacity_conf":"medium","nearest_label":"Mortlake","label_conf":"high","notes":"Mortlake OCGT"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":220,"capacity_conf":"medium","nearest_label":"Terang area","label_conf":"medium"},

    # vic_r1c1 - Melbourne + Latrobe Valley (huge coal)
    {"state":"VIC","tile":"vic_r1c1","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":2210,"capacity_conf":"medium","nearest_label":"Loy Yang","label_conf":"high","notes":"Loy Yang A"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1100,"capacity_conf":"medium","nearest_label":"Loy Yang","label_conf":"high","notes":"Loy Yang B"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1480,"capacity_conf":"medium","nearest_label":"Yallourn","label_conf":"high","notes":"Yallourn W"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Hydro","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":386,"capacity_conf":"medium","nearest_label":"Mt Beauty / Kiewa","label_conf":"medium","notes":"Kiewa scheme"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Hydro","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":305,"capacity_conf":"medium","nearest_label":"Eildon","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":160,"capacity_conf":"high","nearest_label":"Melbourne CBD ref #1","label_conf":"high","notes":"Key to Melbourne legend"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":344,"capacity_conf":"high","nearest_label":"Melbourne CBD ref #2","label_conf":"high","notes":"Newport"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":386,"capacity_conf":"high","nearest_label":"Melbourne CBD ref #3","label_conf":"high","notes":"Jeeralang"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":300,"capacity_conf":"medium","nearest_label":"Moorabool","label_conf":"medium","notes":"Victorian Big Battery (Geelong)"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":1600,"capacity_conf":"medium","nearest_label":"Hazelwood","label_conf":"high","notes":"large pipeline battery"},

    # vic_r1c2 - East Gippsland + legend
    {"state":"VIC","tile":"vic_r1c2","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":94,"capacity_conf":"high","nearest_label":"Bairnsdale / V5","label_conf":"medium","notes":"Bairnsdale gas"},
    {"state":"VIC","tile":"vic_r1c2","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":50,"capacity_conf":"high","nearest_label":"V5 Gippsland","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c2","fuel":"Hydro","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":150,"capacity_conf":"low","nearest_label":"East VIC","label_conf":"low","notes":"hydro icon at top, cut off"},
]
append("VIC", markers)
