from append_vision_v2 import append

markers = [
    # sa_r0c0 - NW (Davenport cluster on right edge)
    {"state":"SA","tile":"sa_r0c0","fuel":"Battery","stage":"Application","capacity_mw":144,"nearest_label":"Davenport","x_pct":93,"y_pct":82,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Solar","stage":"Pre-Registration","capacity_mw":30,"nearest_label":"Davenport","x_pct":89,"y_pct":86,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Battery","stage":"Application","capacity_mw":270,"nearest_label":"Davenport","x_pct":85,"y_pct":89,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Battery","stage":"Application","capacity_mw":100,"nearest_label":"Davenport","x_pct":84,"y_pct":92,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Wind","stage":"Operational","capacity_mw":212,"nearest_label":"Davenport","x_pct":83,"y_pct":94,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},

    # sa_r1c0 - Eyre/Yorke
    {"state":"SA","tile":"sa_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":70,"nearest_label":"Yadnarie","x_pct":43,"y_pct":30,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c0","fuel":"OCGT","stage":"Operational","capacity_mw":78,"nearest_label":"Port Lincoln","x_pct":27,"y_pct":67,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":66,"nearest_label":"Port Lincoln (south)","x_pct":13,"y_pct":76,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Battery","stage":"Operational","capacity_mw":30,"nearest_label":"Dalrymple","x_pct":88,"y_pct":75,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Wind","stage":"Operational","capacity_mw":91,"nearest_label":"Yorke Peninsula south","x_pct":84,"y_pct":87,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Battery","stage":"Application","capacity_mw":100,"nearest_label":"Whyalla Central / Stony Point","x_pct":68,"y_pct":4,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},

    # sa_r1c1 - Adelaide region (dense, approximate cluster positions)
    {"state":"SA","tile":"sa_r1c1","fuel":"Battery","stage":"Application","capacity_mw":256,"nearest_label":"Robertstown","x_pct":52,"y_pct":22,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Battery","stage":"Application","capacity_mw":250,"nearest_label":"Robertstown","x_pct":56,"y_pct":22,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"medium"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Wind","stage":"Operational","capacity_mw":99,"nearest_label":"Snowtown","x_pct":30,"y_pct":7,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"medium","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Battery","stage":"Application","capacity_mw":140,"nearest_label":"Snowtown","x_pct":33,"y_pct":12,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"low","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Wind","stage":"Operational","capacity_mw":270,"nearest_label":"Hallett area","x_pct":58,"y_pct":18,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"low","label_conf":"medium"},

    # sa_r2c0 - Adelaide CBD legend (no real positions - inherit from Adelaide centroid)
    # These markers are labelled '#2 Pelican Point' etc. - they're at Torrens Island / Pelican Point in real life
    # Place them at approximate Adelaide CBD position in this legend tile (~80, 80) but they really live elsewhere
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","stage":"Operational","capacity_mw":210,"nearest_label":"Adelaide CBD ref #2","x_pct":40,"y_pct":2,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high","notes":"legend entry - position is legend not map"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","stage":"Operational","capacity_mw":237,"nearest_label":"Adelaide CBD ref #3","x_pct":40,"y_pct":8,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high","notes":"legend entry"},
    {"state":"SA","tile":"sa_r2c0","fuel":"CCGT","stage":"Operational","capacity_mw":529,"nearest_label":"Adelaide CBD ref #4","x_pct":40,"y_pct":13,"fuel_conf":"medium","stage_conf":"high","capacity_conf":"high","label_conf":"high","notes":"legend entry - Pelican Point CCGT"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","stage":"Operational","capacity_mw":204,"nearest_label":"Adelaide CBD ref #5","x_pct":40,"y_pct":18,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high","notes":"legend entry"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","stage":"Operational","capacity_mw":150,"nearest_label":"Adelaide CBD ref #6","x_pct":40,"y_pct":22,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high","notes":"legend entry"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","stage":"Operational","capacity_mw":156,"nearest_label":"Adelaide CBD ref #7","x_pct":40,"y_pct":27,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high","notes":"legend entry"},

    # sa_r2c1 - SE SA / Mt Gambier
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","stage":"Operational","capacity_mw":35,"nearest_label":"SE SA coast","x_pct":8,"y_pct":1,"fuel_conf":"high","stage_conf":"medium","capacity_conf":"high","label_conf":"low"},
    {"state":"SA","tile":"sa_r2c1","fuel":"OCGT","stage":"Operational","capacity_mw":86,"nearest_label":"Kincraig / Tantanoola","x_pct":88,"y_pct":68,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"medium"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","stage":"Operational","capacity_mw":77,"nearest_label":"Mayura","x_pct":80,"y_pct":82,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","stage":"Operational","capacity_mw":46,"nearest_label":"Mayura","x_pct":78,"y_pct":86,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","stage":"Operational","capacity_mw":25,"nearest_label":"Mayura","x_pct":78,"y_pct":92,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","stage":"Operational","capacity_mw":279,"nearest_label":"Mt Gambier","x_pct":83,"y_pct":95,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","stage":"Application","capacity_mw":250,"nearest_label":"South East","x_pct":93,"y_pct":90,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","stage":"Application","capacity_mw":250,"nearest_label":"South East","x_pct":98,"y_pct":90,"fuel_conf":"high","stage_conf":"high","capacity_conf":"high","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","stage":"Application","capacity_mw":125,"nearest_label":"Mt Gambier","x_pct":92,"y_pct":95,"fuel_conf":"medium","stage_conf":"medium","capacity_conf":"high","label_conf":"high"},
]
append("SA", markers)
