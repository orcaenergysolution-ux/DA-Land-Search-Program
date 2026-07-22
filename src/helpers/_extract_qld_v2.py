from append_vision_v2 import append

markers = [
    # qld_r0c0 - far NW (Kidston / Lakeland)
    {"state":"QLD","tile":"qld_r0c0","fuel":"Solar","stage":"Operational","capacity_mw":47,"nearest_label":"Kidston","x_pct":78,"y_pct":78,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c0","fuel":"Pumped Hydro Storage","stage":"Commissioning","capacity_mw":244,"nearest_label":"Kidston","x_pct":80,"y_pct":83,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":180,"nearest_label":"Lakeland","x_pct":96,"y_pct":16,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},

    # qld_r0c1 - North Coast (Cairns to Bowen)
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","stage":"Operational","capacity_mw":13,"nearest_label":"Cooktown","x_pct":3,"y_pct":11,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":66,"nearest_label":"Kamerunga","x_pct":33,"y_pct":22,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":62,"nearest_label":"Worree / Edmonton","x_pct":25,"y_pct":30,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Hydro","stage":"Operational","capacity_mw":178,"nearest_label":"Cairns / Kamerunga","x_pct":22,"y_pct":33,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Hydro","stage":"Operational","capacity_mw":152,"nearest_label":"Chalumbin","x_pct":12,"y_pct":47,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Wind","stage":"Operational","capacity_mw":311,"nearest_label":"Chalumbin","x_pct":17,"y_pct":48,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Wind","stage":"Operational","capacity_mw":95,"nearest_label":"Tully","x_pct":22,"y_pct":55,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","stage":"Registration","capacity_mw":300,"nearest_label":"Ingham South","x_pct":14,"y_pct":67,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":24,"nearest_label":"Cardwell","x_pct":38,"y_pct":66,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","stage":"Pre-Registration","capacity_mw":400,"nearest_label":"Ingham","x_pct":13,"y_pct":75,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":243,"nearest_label":"Yabulu South","x_pct":37,"y_pct":78,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":443,"nearest_label":"Townsville East","x_pct":50,"y_pct":85,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"OCGT","stage":"Operational","capacity_mw":414,"nearest_label":"Ross","x_pct":55,"y_pct":88,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":100,"nearest_label":"Garbutt / Townsville","x_pct":38,"y_pct":88,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Wind","stage":"Application","capacity_mw":67,"nearest_label":"Clare South","x_pct":58,"y_pct":93,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":200,"nearest_label":"Clare South","x_pct":55,"y_pct":97,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":100,"nearest_label":"Clare South","x_pct":50,"y_pct":97,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","stage":"Operational","capacity_mw":500,"nearest_label":"Bowen North","x_pct":32,"y_pct":98,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},

    # qld_r1c0 - West interior (Hughenden / Longreach)
    {"state":"QLD","tile":"qld_r1c0","fuel":"Solar","stage":"Operational","capacity_mw":18,"nearest_label":"Hughenden","x_pct":85,"y_pct":18,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":50,"nearest_label":"Hughenden","x_pct":85,"y_pct":22,"fuel_conf":"high","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c0","fuel":"Battery","stage":"Operational","capacity_mw":50,"nearest_label":"Hughenden","x_pct":88,"y_pct":22,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c0","fuel":"Solar","stage":"Operational","capacity_mw":15,"nearest_label":"Longreach","x_pct":84,"y_pct":82,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},

    # qld_r1c1 - Bowen Basin (coal + RE)
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","stage":"Operational","capacity_mw":55,"nearest_label":"King Creek / Strathmore","x_pct":32,"y_pct":4,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Wind","stage":"Operational","capacity_mw":453,"nearest_label":"Collinsville","x_pct":35,"y_pct":10,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"low","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","stage":"Operational","capacity_mw":146,"nearest_label":"Moranbah","x_pct":48,"y_pct":30,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","stage":"Application","capacity_mw":100,"nearest_label":"Lilyvale / Gregory","x_pct":70,"y_pct":67,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","stage":"Operational","capacity_mw":72,"nearest_label":"Clermont","x_pct":50,"y_pct":72,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Battery","stage":"Application","capacity_mw":440,"nearest_label":"Norwich Park / Dysart","x_pct":78,"y_pct":62,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","stage":"Operational","capacity_mw":273,"nearest_label":"Blackwater","x_pct":80,"y_pct":82,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Coal","stage":"Operational","capacity_mw":700,"nearest_label":"Stanwell area","x_pct":95,"y_pct":48,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"low","label_conf":"medium"},

    # qld_r1c2 - Central QLD coast (Rockhampton/Gladstone)
    {"state":"QLD","tile":"qld_r1c2","fuel":"Battery","stage":"Operational","capacity_mw":296,"nearest_label":"Hayes Point / Rockhampton","x_pct":3,"y_pct":42,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":1540,"nearest_label":"Stanwell","x_pct":14,"y_pct":52,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":1680,"nearest_label":"Gladstone","x_pct":48,"y_pct":67,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":1632,"nearest_label":"Biloela","x_pct":30,"y_pct":93,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"OCGT","stage":"Operational","capacity_mw":180,"nearest_label":"Yarwun","x_pct":47,"y_pct":62,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"OCGT","stage":"Operational","capacity_mw":80,"nearest_label":"Moura","x_pct":14,"y_pct":93,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":500,"nearest_label":"Boyne Island","x_pct":48,"y_pct":77,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Solar","stage":"Operational","capacity_mw":314,"nearest_label":"Calvale","x_pct":26,"y_pct":80,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Battery","stage":"Application","capacity_mw":220,"nearest_label":"Calvale","x_pct":28,"y_pct":86,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Battery","stage":"Application","capacity_mw":450,"nearest_label":"Larcom / Calliope","x_pct":42,"y_pct":75,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Solar","stage":"Operational","capacity_mw":97,"nearest_label":"Bundaberg","x_pct":62,"y_pct":98,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},

    # qld_r2c1 - West interior (Roma)
    {"state":"QLD","tile":"qld_r2c1","fuel":"Solar","stage":"Operational","capacity_mw":100,"nearest_label":"Roma","x_pct":83,"y_pct":40,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c1","fuel":"OCGT","stage":"Operational","capacity_mw":80,"nearest_label":"Roma","x_pct":80,"y_pct":42,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},

    # qld_r2c2 - SE QLD (Brisbane / Darling Downs)
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","stage":"Operational","capacity_mw":1400,"nearest_label":"Tarong","x_pct":35,"y_pct":50,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","stage":"Operational","capacity_mw":443,"nearest_label":"Tarong North","x_pct":37,"y_pct":48,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","stage":"Operational","capacity_mw":850,"nearest_label":"Millmerran","x_pct":25,"y_pct":80,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","stage":"Operational","capacity_mw":750,"nearest_label":"Kogan Creek","x_pct":30,"y_pct":75,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Pumped Hydro Storage","stage":"Operational","capacity_mw":500,"nearest_label":"Wivenhoe","x_pct":50,"y_pct":55,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"OCGT","stage":"Operational","capacity_mw":385,"nearest_label":"Swanbank","x_pct":50,"y_pct":58,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"OCGT","stage":"Operational","capacity_mw":655,"nearest_label":"Braemar","x_pct":40,"y_pct":62,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Wind","stage":"Operational","capacity_mw":453,"nearest_label":"Coopers Gap","x_pct":30,"y_pct":60,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Battery","stage":"Operational","capacity_mw":150,"nearest_label":"Western Downs","x_pct":40,"y_pct":68,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Solar","stage":"Operational","capacity_mw":110,"nearest_label":"Gatton","x_pct":45,"y_pct":68,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Solar","stage":"Operational","capacity_mw":480,"nearest_label":"Bulli Creek / Yarranlea","x_pct":22,"y_pct":82,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
]
append("QLD", markers)
