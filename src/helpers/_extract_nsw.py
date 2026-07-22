from append_vision_extracts import append

markers = [
    # nsw_r0c0 - far NW, only legend
    # (none)

    # nsw_r0c1 - West central NSW (Nyngan/Dubbo/Wellington)
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":102,"capacity_conf":"high","nearest_label":"Nyngan","label_conf":"high","notes":"Nyngan Solar Plant"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":105,"capacity_conf":"high","nearest_label":"Narromine","label_conf":"high","notes":"Nevertire Solar"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":9,"capacity_conf":"high","nearest_label":"Narromine","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":80,"capacity_conf":"high","nearest_label":"Narromine","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":13,"capacity_conf":"high","nearest_label":"Narromine","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":64,"capacity_conf":"high","nearest_label":"Dubbo","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":55,"capacity_conf":"high","nearest_label":"Dubbo","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Battery","fuel_conf":"medium","stage":"Registration","stage_conf":"medium","capacity_mw":408,"capacity_conf":"high","nearest_label":"Dubbo / Wellington","label_conf":"medium","notes":"green battery"},
    {"state":"NSW","tile":"nsw_r0c1","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":300,"capacity_conf":"medium","nearest_label":"Wellington","label_conf":"medium"},

    # nsw_r0c2 - Northern NSW (New England REZ, Hunter)
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":100,"capacity_conf":"medium","nearest_label":"Tenterfield","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":207,"capacity_conf":"medium","nearest_label":"Glen Innes","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":270,"capacity_conf":"medium","nearest_label":"Inverell","label_conf":"high","notes":"Sapphire Wind Farm"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":175,"capacity_conf":"medium","nearest_label":"Inverell","label_conf":"high","notes":"White Rock Wind Farm"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":400,"capacity_conf":"medium","nearest_label":"Inverell","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":478,"capacity_conf":"medium","nearest_label":"Armidale","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":200,"capacity_conf":"medium","nearest_label":"Armidale","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":110,"capacity_conf":"medium","nearest_label":"Armidale","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":320,"capacity_conf":"medium","nearest_label":"Boggabri","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Wind","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":400,"capacity_conf":"medium","nearest_label":"Boggabri","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":117,"capacity_conf":"medium","nearest_label":"Gunnedah","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":450,"capacity_conf":"medium","nearest_label":"Tamworth","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":300,"capacity_conf":"medium","nearest_label":"south of Tamworth","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1320,"capacity_conf":"high","nearest_label":"Liddell / Muswellbrook","label_conf":"high","notes":"Liddell decommissioned but on map"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":450,"capacity_conf":"medium","nearest_label":"Muswellbrook","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r0c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":120,"capacity_conf":"medium","nearest_label":"Wollar","label_conf":"high"},

    # nsw_r1c0 - SW NSW (Buronga / Murraylink)
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":207,"capacity_conf":"medium","nearest_label":"Buronga","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":220,"capacity_conf":"medium","nearest_label":"Buronga","label_conf":"high","notes":"Beryl/Manildra cluster"},
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":200,"capacity_conf":"medium","nearest_label":"Buronga","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c0","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":110,"capacity_conf":"medium","nearest_label":"Hay","label_conf":"high","notes":"Coleambally / Hillston"},

    # nsw_r1c1 - Central NSW + Snowy region
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":85,"capacity_conf":"medium","nearest_label":"Hillston","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":131,"capacity_conf":"medium","nearest_label":"Forbes","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":50,"capacity_conf":"medium","nearest_label":"Forbes","label_conf":"high","notes":"Parkes Solar"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Solar","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":140,"capacity_conf":"medium","nearest_label":"Manildra","label_conf":"high","notes":"Manildra Solar"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":113,"capacity_conf":"medium","nearest_label":"Crookwell / Gunning","label_conf":"medium","notes":"Gullen Range / Crookwell"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":270,"capacity_conf":"medium","nearest_label":"Yass / Capital","label_conf":"high","notes":"Bango Wind"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":141,"capacity_conf":"medium","nearest_label":"Yass / Capital","label_conf":"high","notes":"Capital Wind Farm"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Hydro","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1500,"capacity_conf":"medium","nearest_label":"Snowy / Tumut","label_conf":"high","notes":"Tumut 3"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Hydro","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1100,"capacity_conf":"medium","nearest_label":"Murray","label_conf":"high","notes":"Murray 1+2"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Pumped Hydro Storage","fuel_conf":"high","stage":"Commissioning","stage_conf":"medium","capacity_mw":2000,"capacity_conf":"medium","nearest_label":"Snowy","label_conf":"high","notes":"Snowy 2.0 PHES - pink-ish icon"},
    {"state":"NSW","tile":"nsw_r1c1","fuel":"Wind","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":985,"capacity_conf":"medium","nearest_label":"Cooma area","label_conf":"medium","notes":"large wind project"},

    # nsw_r1c2 - Sydney + Hunter coast
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":2640,"capacity_conf":"medium","nearest_label":"Bayswater","label_conf":"high","notes":"Bayswater Power Station"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":2880,"capacity_conf":"medium","nearest_label":"Eraring","label_conf":"high","notes":"Eraring Power Station"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1320,"capacity_conf":"medium","nearest_label":"Vales Point","label_conf":"high"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Coal","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":1400,"capacity_conf":"medium","nearest_label":"Mt Piper / Wallerawang","label_conf":"high","notes":"Mt Piper PS"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","fuel_conf":"medium","stage":"Commissioning","stage_conf":"medium","capacity_mw":660,"capacity_conf":"medium","nearest_label":"Eraring","label_conf":"high","notes":"Eraring BESS (Origin)"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":850,"capacity_conf":"medium","nearest_label":"Liddell / Muswellbrook","label_conf":"high","notes":"Waratah Super Battery proximate"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Hydro","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":50,"capacity_conf":"medium","nearest_label":"Sydney West","label_conf":"medium","notes":"Warragamba hydro"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":665,"capacity_conf":"medium","nearest_label":"Sydney","label_conf":"high","notes":"Tallawarra"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"OCGT","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":660,"capacity_conf":"medium","nearest_label":"Kurri Kurri","label_conf":"medium","notes":"Snowy Hydro Kurri Kurri gas peaker"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":250,"capacity_conf":"medium","nearest_label":"Sydney South / Macarthur","label_conf":"medium"},
    {"state":"NSW","tile":"nsw_r1c2","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":440,"capacity_conf":"medium","nearest_label":"Liverpool / Macarthur","label_conf":"medium"},
]
append("NSW", markers)
