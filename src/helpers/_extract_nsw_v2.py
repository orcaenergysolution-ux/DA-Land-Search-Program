from append_vision_v2 import append

markers = [
    # nsw_r0c1 - W central NSW (Nyngan/Dubbo/Wellington)
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":102,"nearest_label":"Nyngan","x_pct":38,"y_pct":72,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":105,"nearest_label":"Narromine","x_pct":46,"y_pct":79,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":9,"nearest_label":"Narromine","x_pct":63,"y_pct":87,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":80,"nearest_label":"Narromine","x_pct":67,"y_pct":87,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":13,"nearest_label":"Narromine","x_pct":74,"y_pct":89,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":64,"nearest_label":"Dubbo","x_pct":73,"y_pct":84,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","stage":"Operational","capacity_mw":55,"nearest_label":"Dubbo","x_pct":83,"y_pct":83,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Battery","stage":"Registration","capacity_mw":408,"nearest_label":"Dubbo / Wellington","x_pct":95,"y_pct":90,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Battery","stage":"Application","capacity_mw":300,"nearest_label":"Wellington","x_pct":78,"y_pct":95,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},

    # nsw_r0c2 - Northern NSW (New England REZ)
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","stage":"Application","capacity_mw":100,"nearest_label":"Tenterfield","x_pct":57,"y_pct":11,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","stage":"Application","capacity_mw":207,"nearest_label":"Glen Innes","x_pct":45,"y_pct":33,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","stage":"Operational","capacity_mw":270,"nearest_label":"Inverell","x_pct":37,"y_pct":42,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","stage":"Operational","capacity_mw":175,"nearest_label":"Inverell","x_pct":42,"y_pct":42,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","stage":"Application","capacity_mw":400,"nearest_label":"Inverell","x_pct":37,"y_pct":42,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","stage":"Application","capacity_mw":478,"nearest_label":"Armidale","x_pct":52,"y_pct":40,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","stage":"Application","capacity_mw":200,"nearest_label":"Armidale","x_pct":52,"y_pct":46,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","stage":"Application","capacity_mw":110,"nearest_label":"Armidale","x_pct":37,"y_pct":42,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","stage":"Application","capacity_mw":320,"nearest_label":"Boggabri","x_pct":15,"y_pct":55,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","stage":"Application","capacity_mw":400,"nearest_label":"Boggabri","x_pct":15,"y_pct":62,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","stage":"Application","capacity_mw":117,"nearest_label":"Gunnedah","x_pct":22,"y_pct":68,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","stage":"Application","capacity_mw":450,"nearest_label":"Tamworth","x_pct":30,"y_pct":76,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","stage":"Application","capacity_mw":300,"nearest_label":"Tamworth (south)","x_pct":32,"y_pct":82,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Coal","stage":"Operational","capacity_mw":1320,"nearest_label":"Liddell / Muswellbrook","x_pct":42,"y_pct":93,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","stage":"Application","capacity_mw":450,"nearest_label":"Muswellbrook","x_pct":42,"y_pct":93,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","stage":"Application","capacity_mw":120,"nearest_label":"Wollar","x_pct":25,"y_pct":99,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},

    # nsw_r1c0 - SW NSW (Buronga / Murraylink)
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","stage":"Operational","capacity_mw":207,"nearest_label":"Buronga","x_pct":39,"y_pct":40,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","stage":"Operational","capacity_mw":220,"nearest_label":"Buronga","x_pct":42,"y_pct":40,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","stage":"Application","capacity_mw":200,"nearest_label":"Buronga","x_pct":38,"y_pct":48,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","stage":"Operational","capacity_mw":110,"nearest_label":"Hay","x_pct":70,"y_pct":42,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},

    # nsw_r1c1 - Central NSW + Snowy (Tumut/Murray/Snowy 2.0)
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","stage":"Operational","capacity_mw":85,"nearest_label":"Hillston","x_pct":3,"y_pct":35,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","stage":"Application","capacity_mw":131,"nearest_label":"Forbes","x_pct":32,"y_pct":7,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","stage":"Operational","capacity_mw":50,"nearest_label":"Forbes / Parkes","x_pct":30,"y_pct":13,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","stage":"Operational","capacity_mw":140,"nearest_label":"Manildra","x_pct":37,"y_pct":15,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","stage":"Operational","capacity_mw":113,"nearest_label":"Crookwell / Gunning","x_pct":62,"y_pct":30,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","stage":"Operational","capacity_mw":270,"nearest_label":"Yass / Bango","x_pct":62,"y_pct":48,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","stage":"Operational","capacity_mw":141,"nearest_label":"Capital","x_pct":80,"y_pct":52,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":1500,"nearest_label":"Tumut","x_pct":63,"y_pct":52,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Hydro","stage":"Operational","capacity_mw":1100,"nearest_label":"Murray","x_pct":55,"y_pct":62,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Pumped Hydro Storage","stage":"Commissioning","capacity_mw":2000,"nearest_label":"Snowy","x_pct":62,"y_pct":68,"fuel_conf":"high","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","stage":"Application","capacity_mw":985,"nearest_label":"Cooma area","x_pct":85,"y_pct":75,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},

    # nsw_r1c2 - Sydney + Hunter coast
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":2640,"nearest_label":"Bayswater","x_pct":62,"y_pct":4,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":2880,"nearest_label":"Eraring","x_pct":50,"y_pct":18,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":1320,"nearest_label":"Vales Point","x_pct":50,"y_pct":24,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","stage":"Operational","capacity_mw":1400,"nearest_label":"Mt Piper / Wallerawang","x_pct":13,"y_pct":18,"fuel_conf":"high","stage_conf":"high","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","stage":"Commissioning","capacity_mw":660,"nearest_label":"Eraring","x_pct":50,"y_pct":18,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","stage":"Application","capacity_mw":850,"nearest_label":"Liddell","x_pct":62,"y_pct":4,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"OCGT","stage":"Operational","capacity_mw":665,"nearest_label":"Sydney","x_pct":35,"y_pct":48,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"medium","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"OCGT","stage":"Application","capacity_mw":660,"nearest_label":"Kurri Kurri","x_pct":45,"y_pct":15,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","stage":"Application","capacity_mw":250,"nearest_label":"Sydney South","x_pct":15,"y_pct":53,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","stage":"Application","capacity_mw":440,"nearest_label":"Macarthur","x_pct":15,"y_pct":58,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
]
append("NSW", markers)
