from append_vision_extracts import append

markers = [
    # sa_r0c0 - NW SA (Davenport cluster on right edge)
    {"state":"SA","tile":"sa_r0c0","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":144,"capacity_conf":"medium","nearest_label":"Davenport","label_conf":"high","notes":"orange battery, edge of tile"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Solar","fuel_conf":"high","stage":"Pre-Registration","stage_conf":"high","capacity_mw":30,"capacity_conf":"high","nearest_label":"Davenport","label_conf":"high","notes":"yellow-green sun"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Battery","fuel_conf":"high","stage":"Application","stage_conf":"high","capacity_mw":270,"capacity_conf":"high","nearest_label":"Davenport","label_conf":"high","notes":"orange battery"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Battery","fuel_conf":"high","stage":"Application","stage_conf":"high","capacity_mw":100,"capacity_conf":"high","nearest_label":"Davenport","label_conf":"high"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":212,"capacity_conf":"high","nearest_label":"Davenport","label_conf":"high","notes":"Lincoln Gap area"},
    {"state":"SA","tile":"sa_r0c0","fuel":"Coal","fuel_conf":"low","stage":"Operational","stage_conf":"low","capacity_mw":770,"capacity_conf":"low","nearest_label":"Davenport","label_conf":"medium","notes":"77/201 dual label - low confidence"},

    # sa_r1c0 - Eyre + Yorke
    {"state":"SA","tile":"sa_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":70,"capacity_conf":"high","nearest_label":"Yadnarie","label_conf":"high"},
    {"state":"SA","tile":"sa_r1c0","fuel":"OCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":78,"capacity_conf":"high","nearest_label":"Port Lincoln","label_conf":"high","notes":"dark blue flame near Port Lincoln"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":66,"capacity_conf":"high","nearest_label":"Port Lincoln (south)","label_conf":"high","notes":"Cathedral Rocks"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":30,"capacity_conf":"high","nearest_label":"Dalrymple","label_conf":"high","notes":"Dalrymple ESCRI BESS"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":91,"capacity_conf":"high","nearest_label":"Yorke Peninsula south","label_conf":"high","notes":"Wattle Point"},
    {"state":"SA","tile":"sa_r1c0","fuel":"Battery","fuel_conf":"high","stage":"Application","stage_conf":"high","capacity_mw":100,"capacity_conf":"high","nearest_label":"Stony Point / Whyalla Central","label_conf":"high","notes":"orange battery"},

    # sa_r1c1 - Adelaide region (high density, lower confidence)
    {"state":"SA","tile":"sa_r1c1","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":256,"capacity_conf":"medium","nearest_label":"Robertstown","label_conf":"medium","notes":"orange battery in dense cluster"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":250,"capacity_conf":"medium","nearest_label":"Robertstown","label_conf":"medium"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Wind","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":99,"capacity_conf":"medium","nearest_label":"Snowtown","label_conf":"high","notes":"Snowtown cluster"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":140,"capacity_conf":"low","nearest_label":"Snowtown","label_conf":"high","notes":"14X partial number"},
    {"state":"SA","tile":"sa_r1c1","fuel":"Wind","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":270,"capacity_conf":"low","nearest_label":"Hallett area","label_conf":"medium","notes":"approximate wind farm cluster"},

    # sa_r2c0 - Adelaide CBD key
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":210,"capacity_conf":"high","nearest_label":"Adelaide CBD ref #2","label_conf":"high","notes":"from Key to Adelaide legend"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":237,"capacity_conf":"high","nearest_label":"Adelaide CBD ref #3","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c0","fuel":"CCGT","fuel_conf":"medium","stage":"Operational","stage_conf":"high","capacity_mw":529,"capacity_conf":"high","nearest_label":"Adelaide CBD ref #4","label_conf":"high","notes":"likely Pelican Point CCGT"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":204,"capacity_conf":"high","nearest_label":"Adelaide CBD ref #5","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":150,"capacity_conf":"high","nearest_label":"Adelaide CBD ref #6","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c0","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":156,"capacity_conf":"high","nearest_label":"Adelaide CBD ref #7","label_conf":"high"},

    # sa_r2c1 - SE SA / Mt Gambier
    {"state":"SA","tile":"sa_r2c1","fuel":"OCGT","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":86,"capacity_conf":"high","nearest_label":"Kincraig","label_conf":"medium","notes":"Tantanoola gas"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":77,"capacity_conf":"high","nearest_label":"Mayura","label_conf":"high","notes":"Lake Bonney"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":46,"capacity_conf":"high","nearest_label":"Mayura","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","fuel_conf":"medium","stage":"Operational","stage_conf":"medium","capacity_mw":25,"capacity_conf":"high","nearest_label":"Mayura","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"high","capacity_mw":279,"capacity_conf":"high","nearest_label":"Mt Gambier","label_conf":"high","notes":"Lake Bonney 3"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","fuel_conf":"high","stage":"Application","stage_conf":"high","capacity_mw":250,"capacity_conf":"high","nearest_label":"South East / Mt Gambier","label_conf":"high","notes":"orange battery"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","fuel_conf":"high","stage":"Application","stage_conf":"high","capacity_mw":250,"capacity_conf":"high","nearest_label":"South East / Mt Gambier","label_conf":"high","notes":"second orange battery"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Battery","fuel_conf":"medium","stage":"Application","stage_conf":"medium","capacity_mw":125,"capacity_conf":"high","nearest_label":"Mt Gambier","label_conf":"high"},
    {"state":"SA","tile":"sa_r2c1","fuel":"Wind","fuel_conf":"high","stage":"Operational","stage_conf":"medium","capacity_mw":35,"capacity_conf":"high","nearest_label":"SE SA coast","label_conf":"low","notes":"top of tile, label cut off"},
]
append("SA", markers)
