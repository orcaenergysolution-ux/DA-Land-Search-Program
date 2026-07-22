from append_vision_extracts import append

markers = [
    # qld_r0c0 - far NW QLD (Cape York / Kidston / Georgetown)
    {"state":"QLD","tile":"qld_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":47,"capacity_conf":"high","nearest_label":"Kidston","label_conf":"high","notes":"Kidston Solar"},
    {"state":"QLD","tile":"qld_r0c0","fuel":"Pumped Hydro Storage","fuel_conf":"high","stage":"Commissioning","stage_conf":"high","capacity_mw":244,"capacity_conf":"high","nearest_label":"Kidston","label_conf":"high","notes":"Kidston PHES - pink"},
    {"state":"QLD","tile":"qld_r0c0","fuel":"Wind","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":180,"capacity_conf":"medium","nearest_label":"Lakeland (east)","label_conf":"high","notes":"Mt Emerald Wind Farm proximity"},

    # qld_r0c1 - North Coast QLD (Cairns to Bowen)
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":13,"capacity_conf":"high","nearest_label":"Cooktown","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":66,"capacity_conf":"high","nearest_label":"Kamerunga","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":62,"capacity_conf":"high","nearest_label":"Worree / Edmonton","label_conf":"high","notes":"Mt Emerald or local solar"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Hydro","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":178,"capacity_conf":"high","nearest_label":"Cairns / Kamerunga","label_conf":"high","notes":"Barron Gorge + Kareeya"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Hydro","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":152,"capacity_conf":"high","nearest_label":"Chalumbin","label_conf":"high","notes":"Kareeya scheme"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":311,"capacity_conf":"high","nearest_label":"Chalumbin","label_conf":"high","notes":"Chalumbin Wind"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":95,"capacity_conf":"high","nearest_label":"Tully","label_conf":"high","notes":"Windy Hill / Tully"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","fuel_conf":"medium","stage":"Registration","stage_conf":"medium","capacity_mw":300,"capacity_conf":"high","nearest_label":"Ingham South","label_conf":"high","notes":"green battery"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":24,"capacity_conf":"high","nearest_label":"Cardwell","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","fuel_conf":"medium","stage":"Pre-Registration","stage_conf":"medium","capacity_mw":400,"capacity_conf":"high","nearest_label":"Ingham","label_conf":"medium","notes":"yellow-green battery"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":243,"capacity_conf":"high","nearest_label":"Yabulu South","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":443,"capacity_conf":"medium","nearest_label":"Townsville East","label_conf":"high","notes":"Sun Metals Solar"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":414,"capacity_conf":"medium","nearest_label":"Ross","label_conf":"high","notes":"Mt Stuart diesel/gas"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":100,"capacity_conf":"medium","nearest_label":"Garbutt / Townsville","label_conf":"high"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Wind","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":67,"capacity_conf":"medium","nearest_label":"Clare South","label_conf":"medium","notes":"Hervey Range / Burdekin area"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":200,"capacity_conf":"medium","nearest_label":"Clare South","label_conf":"high","notes":"Clare Solar Farm"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":100,"capacity_conf":"medium","nearest_label":"Clare South","label_conf":"high","notes":"Clare Solar 2"},
    {"state":"QLD","tile":"qld_r0c1","fuel":"Battery","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":500,"capacity_conf":"high","nearest_label":"Bowen North","label_conf":"high","notes":"large dark blue battery"},

    # qld_r1c0 - West QLD interior (Hughenden / Longreach)
    {"state":"QLD","tile":"qld_r1c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":18,"capacity_conf":"high","nearest_label":"Hughenden","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"medium","capacity_mw":50,"capacity_conf":"high","nearest_label":"Hughenden","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c0","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":50,"capacity_conf":"high","nearest_label":"Hughenden","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":15,"capacity_conf":"high","nearest_label":"Longreach","label_conf":"high","notes":"Longreach Solar"},

    # qld_r1c1 - Bowen Basin (coal heartland)
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":55,"capacity_conf":"medium","nearest_label":"King Creek / Strathmore","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Wind","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":453,"capacity_conf":"low","nearest_label":"Newlands / Collinsville","label_conf":"medium","notes":"likely Clarke Creek Wind"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":146,"capacity_conf":"medium","nearest_label":"Moranbah","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":100,"capacity_conf":"medium","nearest_label":"Lilyvale / Gregory","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":72,"capacity_conf":"medium","nearest_label":"Clermont","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":440,"capacity_conf":"medium","nearest_label":"Norwich Park / Dysart","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":273,"capacity_conf":"medium","nearest_label":"Blackwater","label_conf":"medium","notes":"Blackwater Solar"},
    {"state":"QLD","tile":"qld_r1c1","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":700,"capacity_conf":"low","nearest_label":"Stanwell area","label_conf":"medium","notes":"likely Stanwell coal stations"},

    # qld_r1c2 - Central QLD coast (Rockhampton/Gladstone) - DENSE COAL ZONE
    {"state":"QLD","tile":"qld_r1c2","fuel":"Battery","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":296,"capacity_conf":"high","nearest_label":"Hayes Point / Rockhampton","label_conf":"medium","notes":"Hayes Point BESS"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1460,"capacity_conf":"medium","nearest_label":"Stanwell","label_conf":"high","notes":"Stanwell PS"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1680,"capacity_conf":"medium","nearest_label":"Gladstone","label_conf":"high","notes":"Gladstone PS"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1632,"capacity_conf":"medium","nearest_label":"Biloela","label_conf":"high","notes":"Callide B+C combined"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":180,"capacity_conf":"high","nearest_label":"Yarwun","label_conf":"high","notes":"Yarwun cogen"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":80,"capacity_conf":"high","nearest_label":"Moura","label_conf":"high","notes":"Moura gas"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":500,"capacity_conf":"high","nearest_label":"Boyne Island","label_conf":"high","notes":"Boyne Smelter cogen"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":314,"capacity_conf":"high","nearest_label":"Calvale","label_conf":"high"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":220,"capacity_conf":"high","nearest_label":"Calvale","label_conf":"high","notes":"orange battery"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":450,"capacity_conf":"medium","nearest_label":"Larcom / Calliope","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r1c2","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":97,"capacity_conf":"high","nearest_label":"Bundaberg","label_conf":"high"},

    # qld_r2c1 - West interior (Roma)
    {"state":"QLD","tile":"qld_r2c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":100,"capacity_conf":"high","nearest_label":"Roma","label_conf":"high","notes":"Roma Solar"},
    {"state":"QLD","tile":"qld_r2c1","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":80,"capacity_conf":"high","nearest_label":"Roma","label_conf":"high","notes":"Roma gas"},

    # qld_r2c2 - SE QLD (Brisbane / Darling Downs) - very dense
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1400,"capacity_conf":"medium","nearest_label":"Tarong","label_conf":"high","notes":"Tarong PS"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":443,"capacity_conf":"medium","nearest_label":"Tarong North","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":850,"capacity_conf":"medium","nearest_label":"Millmerran","label_conf":"high"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":750,"capacity_conf":"medium","nearest_label":"Kogan Creek","label_conf":"high","notes":"Kogan Creek PS"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Pumped Hydro Storage","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":500,"capacity_conf":"medium","nearest_label":"Wivenhoe","label_conf":"high","notes":"Wivenhoe PHES"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":385,"capacity_conf":"medium","nearest_label":"Swanbank","label_conf":"high","notes":"Swanbank E"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":655,"capacity_conf":"medium","nearest_label":"Braemar","label_conf":"high","notes":"Braemar 1+2"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Wind","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":453,"capacity_conf":"medium","nearest_label":"Coopers Gap / Cooranga","label_conf":"medium","notes":"Coopers Gap Wind"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":150,"capacity_conf":"medium","nearest_label":"Western Downs","label_conf":"medium","notes":"Wandoan / Western Downs BESS"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":110,"capacity_conf":"medium","nearest_label":"Hayman / Gatton","label_conf":"medium"},
    {"state":"QLD","tile":"qld_r2c2","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":480,"capacity_conf":"medium","nearest_label":"Bulli Creek / Yarranlea","label_conf":"medium","notes":"Yarranlea/Bulli Creek solar cluster"},
]
append("QLD", markers)
