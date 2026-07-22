from append_vision_v2 import append

markers = [
    # vic_r0c0 - NW VIC (Murraylink / Red Cliffs / Wemen / Horsham)
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":81,"nearest_label":"Red Cliffs / Buronga","x_pct":42,"y_pct":15,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":190,"nearest_label":"Red Cliffs","x_pct":52,"y_pct":18,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","stage":"Registration","capacity_mw":150,"nearest_label":"Red Cliffs","x_pct":50,"y_pct":22,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":88,"nearest_label":"Wemen (east)","x_pct":63,"y_pct":30,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":88,"nearest_label":"Wemen","x_pct":55,"y_pct":34,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":200,"nearest_label":"Wemen","x_pct":43,"y_pct":40,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Pre-Registration","capacity_mw":150,"nearest_label":"Wemen","x_pct":42,"y_pct":45,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","stage":"Registration","capacity_mw":220,"nearest_label":"Wemen","x_pct":50,"y_pct":45,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","stage":"Operational","capacity_mw":185,"nearest_label":"Balranald (west)","x_pct":70,"y_pct":57,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":25,"nearest_label":"Murray River","x_pct":73,"y_pct":66,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":50,"nearest_label":"Murray River","x_pct":80,"y_pct":68,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","stage":"Registration","capacity_mw":171,"nearest_label":"Murray River (east)","x_pct":98,"y_pct":66,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":7,"nearest_label":"Kiata","x_pct":22,"y_pct":86,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":31,"nearest_label":"Kiata","x_pct":30,"y_pct":87,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":203,"nearest_label":"Horsham (north)","x_pct":50,"y_pct":82,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":225,"nearest_label":"Horsham (north)","x_pct":52,"y_pct":87,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"OCGT","stage":"Application","capacity_mw":178,"nearest_label":"Horsham (north)","x_pct":50,"y_pct":90,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":20,"nearest_label":"V3 zone","x_pct":78,"y_pct":90,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"low"},
    {"state":"VIC","tile":"vic_r0c0","fuel":"Battery","stage":"Pre-Registration","capacity_mw":119,"nearest_label":"Horsham","x_pct":52,"y_pct":97,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},

    # vic_r0c1 - North VIC (Hay/Deniliquin border)
    {"state":"VIC","tile":"vic_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":70,"nearest_label":"Mulwala area","x_pct":20,"y_pct":68,"fuel_conf":"low","stage_conf":"low","capacity_conf":"low","label_conf":"low"},
    {"state":"VIC","tile":"vic_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":95,"nearest_label":"Corowa area","x_pct":35,"y_pct":75,"fuel_conf":"low","stage_conf":"low","capacity_conf":"low","label_conf":"low"},

    # vic_r0c2 - NE VIC (legend tile, minimal markers)
    {"state":"VIC","tile":"vic_r0c2","fuel":"Solar","stage":"Operational","capacity_mw":185,"nearest_label":"Bega","x_pct":25,"y_pct":80,"fuel_conf":"low","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},

    # vic_r1c0 - SW VIC (Heywood / Portland / Macarthur)
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":420,"nearest_label":"Macarthur","x_pct":35,"y_pct":40,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":192,"nearest_label":"Portland","x_pct":15,"y_pct":50,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":107,"nearest_label":"Cape Bridgewater","x_pct":13,"y_pct":54,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":67,"nearest_label":"Cape Nelson","x_pct":17,"y_pct":62,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":376,"nearest_label":"Tarrone / Mortlake","x_pct":50,"y_pct":40,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"OCGT","stage":"Operational","capacity_mw":556,"nearest_label":"Mortlake","x_pct":56,"y_pct":48,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c0","fuel":"Wind","stage":"Application","capacity_mw":220,"nearest_label":"Terang area","x_pct":75,"y_pct":42,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},

    # vic_r1c1 - Melbourne + Latrobe Valley
    {"state":"VIC","tile":"vic_r1c1","fuel":"Coal","stage":"Operational","capacity_mw":2210,"nearest_label":"Loy Yang","x_pct":68,"y_pct":50,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Coal","stage":"Operational","capacity_mw":1100,"nearest_label":"Loy Yang","x_pct":72,"y_pct":52,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Coal","stage":"Operational","capacity_mw":1480,"nearest_label":"Yallourn","x_pct":65,"y_pct":48,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":386,"nearest_label":"Mt Beauty / Kiewa","x_pct":80,"y_pct":15,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":305,"nearest_label":"Eildon","x_pct":55,"y_pct":22,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"OCGT","stage":"Operational","capacity_mw":160,"nearest_label":"Melbourne #1","x_pct":40,"y_pct":50,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"OCGT","stage":"Operational","capacity_mw":344,"nearest_label":"Melbourne #2 Newport","x_pct":40,"y_pct":47,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"OCGT","stage":"Operational","capacity_mw":386,"nearest_label":"Melbourne #3 Jeeralang","x_pct":68,"y_pct":55,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Battery","stage":"Operational","capacity_mw":300,"nearest_label":"Moorabool","x_pct":25,"y_pct":48,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c1","fuel":"Battery","stage":"Application","capacity_mw":1600,"nearest_label":"Hazelwood","x_pct":65,"y_pct":50,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},

    # vic_r1c2 - East Gippsland (mostly legend, sparse)
    {"state":"VIC","tile":"vic_r1c2","fuel":"OCGT","stage":"Operational","capacity_mw":94,"nearest_label":"V5 Gippsland / Bairnsdale","x_pct":12,"y_pct":33,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c2","fuel":"Battery","stage":"Operational","capacity_mw":50,"nearest_label":"V5 Gippsland","x_pct":10,"y_pct":33,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"medium"},
    {"state":"VIC","tile":"vic_r1c2","fuel":"Hydro","stage":"Operational","capacity_mw":150,"nearest_label":"East VIC","x_pct":2,"y_pct":2,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"low","label_conf":"low"},
]
append("VIC", markers)
