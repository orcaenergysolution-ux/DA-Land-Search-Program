from append_vision_v2 import append

# TAS markers with approximate (x_pct, y_pct) within each tile (0-100).
markers = [
    # tas_r0c0 - NW quadrant
    {"state":"TAS","tile":"tas_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":65,"nearest_label":"Woolnorth","x_pct":29,"y_pct":24,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":75,"nearest_label":"Woolnorth","x_pct":32,"y_pct":30,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Wind","stage":"Pre-Registration","capacity_mw":21,"nearest_label":"Port Latta","x_pct":54,"y_pct":25,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Solar","stage":"Application","capacity_mw":28,"nearest_label":"Sheffield / Railton","x_pct":94,"y_pct":50,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":31,"nearest_label":"Sheffield","x_pct":86,"y_pct":47,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":67,"nearest_label":"Sheffield","x_pct":86,"y_pct":52,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":33,"nearest_label":"Sheffield (south)","x_pct":80,"y_pct":62,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":100,"nearest_label":"Sheffield (south)","x_pct":85,"y_pct":66,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":54,"nearest_label":"Sheffield (south)","x_pct":88,"y_pct":72,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":46,"nearest_label":"Sheffield (south)","x_pct":90,"y_pct":77,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":11,"nearest_label":"Sheffield (south)","x_pct":90,"y_pct":82,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":89,"nearest_label":"Farrell","x_pct":62,"y_pct":78,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":88,"nearest_label":"Farrell","x_pct":66,"y_pct":83,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":92,"nearest_label":"Farrell / Newton","x_pct":68,"y_pct":90,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Hydro","stage":"Operational","capacity_mw":231,"nearest_label":"Rosebery","x_pct":40,"y_pct":80,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":111,"nearest_label":"Rosebery","x_pct":36,"y_pct":89,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},

    # tas_r0c1 - NE quadrant
    {"state":"TAS","tile":"tas_r0c1","fuel":"Wind","stage":"Operational","capacity_mw":168,"nearest_label":"Derby (north)","x_pct":54,"y_pct":28,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c1","fuel":"Battery","stage":"Application","capacity_mw":208,"nearest_label":"George Town","x_pct":15,"y_pct":47,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c1","fuel":"Hydro","stage":"Operational","capacity_mw":103,"nearest_label":"St Leonards / Mowbray","x_pct":17,"y_pct":62,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c1","fuel":"Hydro","stage":"Operational","capacity_mw":372,"nearest_label":"Palmerston","x_pct":11,"y_pct":86,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c1","fuel":"Solar","stage":"Application","capacity_mw":155,"nearest_label":"Palmerston","x_pct":7,"y_pct":94,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c1","fuel":"Battery","stage":"Application","capacity_mw":107,"nearest_label":"Palmerston","x_pct":18,"y_pct":89,"fuel_conf":"high","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r0c1","fuel":"Pumped Hydro Storage","stage":"Application","capacity_mw":155,"nearest_label":"Arthurs Lake","x_pct":21,"y_pct":94,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},

    # tas_r1c0 - SW quadrant (legend + Derwent Bridge cluster)
    {"state":"TAS","tile":"tas_r1c0","fuel":"Hydro","stage":"Operational","capacity_mw":144,"nearest_label":"Derwent Bridge / Tarraleah","x_pct":59,"y_pct":7,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c0","fuel":"Hydro","stage":"Operational","capacity_mw":15,"nearest_label":"Tungatinah","x_pct":78,"y_pct":18,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c0","fuel":"Hydro","stage":"Operational","capacity_mw":143,"nearest_label":"Tungatinah","x_pct":87,"y_pct":19,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c0","fuel":"Hydro","stage":"Operational","capacity_mw":94,"nearest_label":"Tungatinah (south)","x_pct":92,"y_pct":26,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c0","fuel":"Hydro","stage":"Operational","capacity_mw":45,"nearest_label":"Tungatinah (south)","x_pct":97,"y_pct":29,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c0","fuel":"Hydro","stage":"Operational","capacity_mw":28,"nearest_label":"Tungatinah (south)","x_pct":97,"y_pct":34,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c0","fuel":"Hydro","stage":"Operational","capacity_mw":432,"nearest_label":"south of Queenstown","label_conf":"high","x_pct":78,"y_pct":40,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high"},

    # tas_r1c1 - SE quadrant (Southern Tasmania)
    {"state":"TAS","tile":"tas_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":33,"nearest_label":"Waddamana","x_pct":1,"y_pct":10,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":54,"nearest_label":"Waddamana","x_pct":2,"y_pct":18,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":22,"nearest_label":"Waddamana","x_pct":4,"y_pct":24,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"TAS","tile":"tas_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":40,"nearest_label":"Waddamana","x_pct":7,"y_pct":29,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
]
append("TAS", markers)
