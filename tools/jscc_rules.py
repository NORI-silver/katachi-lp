"""日本標準商品分類（総務省、平成2年6月改定）の分類ごとの決まり（product_db.py が使う）

キーは分類コードの先頭（2桁以上。長いほうが優先）。値は
  ind  = 業界（product_db.IND のキー）
  proc = 主な工程（サイトの工程コード、空白区切り）
  reg  = 確かめる法規制（product_db.REG のキー、空白区切り）
None は取り込まない分類（原料・エネルギーそのもの、農水産物そのもの、スクラップ、
酒類・たばこ・医薬品・医療機器・武器・火薬・農薬・原子力。AGENTS.md と katachi-matching の対象外）。
工程と法規制は分類から決めた「よくある例」で、品目ごとの確認は要る（画面では製品DBの近い製品として出す）。
"""

MECH = 'mechanical.enclosure_design manufacturing.sheet_metal manufacturing.cnc manufacturing.assembly'
ELEC = 'electronics.pcb_design electronics.pcba electronics.firmware mechanical.enclosure_design manufacturing.injection_molding manufacturing.assembly'
FOOD = dict(ind='food', proc='food.processed_oem packaging.label_print packaging.box', reg='food_lic food_label haccp')

R = {
    # ---- 取り込まない分類
    '00': None, '01': None, '02': None, '03': None, '04': None, '05': None, '06': None, '07': None, '08': None, '09': None,
    '29': None,  # 原子力機器
    '53': None,  # プログラム（ソフトウェア。形のある製品ではない）
    '66': None,  # 医療用機器
    '67': None,  # 武器
    '69': None, '70': None, '71': None,  # 農産・畜産・水産の食品そのもの（加工品は 72〜75）
    '762': None,  # アルコールを含む飲料（酒類）
    '764': None,  # 製造たばこ
    '86': None,  # 医療用品（衛生マスク・乳児用品だけ下で戻す）
    '87': None,  # 医薬品
    '94': None,  # 美術品・収集品・骨とう品（作る製品ではない）
    '96': None, '99': None,  # スクラップ・分類不能
    '164': None,  # 火薬類
    '168': None,  # 農薬
    '504': None,  # 艦艇
    '5772': None,
    '9193': None,  # 射撃用具（銃・銃の部分品）  # ぱちんこ装置（遊技機の型式検定が要る）
    '6111': None, '6112': None, '6113': None, '6114': None, '6117': None, '6118': None,  # 医療用のX線装置

    # ---- 加工基礎材・中間製品（素材・部品）
    '10': dict(ind='material', proc='apparel.leather'),
    '11': dict(ind='parts', proc='manufacturing.silicone_molding'),
    '111': dict(ind='car', proc='manufacturing.silicone_molding', reg='pl'),
    '12': dict(ind='material', proc='crafts.wood_furniture'),
    '127': dict(ind='build', proc='crafts.wood_furniture'),
    '128': dict(ind='material', proc='crafts.wood_furniture'),
    '13': dict(ind='material', proc='packaging.box packaging.label_print'),
    '14': dict(ind='material', proc='manufacturing.textile apparel.knit apparel.print_embroidery', reg='fiber'),
    '15': dict(ind='chem'),
    '16': dict(ind='chem'),
    '162': dict(ind='chem', proc='cosmetics.oem'),
    '165': dict(ind='material', proc='manufacturing.injection_molding'),
    '166': dict(ind='chem', reg='zakka'),
    '167': dict(ind='garden'),
    '17': dict(ind='material', proc='crafts.ceramics_glass'),
    '18': dict(ind='material', proc='crafts.metal_goods manufacturing.cnc'),
    '19': dict(ind='material', proc='crafts.metal_goods'),
    '20': dict(ind='material', proc='crafts.metal_goods manufacturing.cnc'),
    '21': dict(ind='parts', proc='manufacturing.sheet_metal crafts.metal_goods'),
    '211': dict(ind='build', proc='manufacturing.sheet_metal crafts.metal_goods'),
    '212': dict(ind='build', proc='manufacturing.sheet_metal crafts.metal_goods'),
    '213': dict(ind='daily', proc='crafts.metal_goods manufacturing.sheet_metal', reg='zakka'),
    '22': dict(ind='parts', proc='electronics.pcba manufacturing.assembly'),
    '23': dict(ind='parts', proc='manufacturing.silicone_molding'),
    '24': dict(ind='build', proc='manufacturing.sheet_metal crafts.wood_furniture manufacturing.assembly', reg='pl'),
    '25': dict(ind='pack', proc='packaging.container'),
    '251': dict(ind='pack', proc='packaging.container manufacturing.sheet_metal', reg='food_pack'),
    '252': dict(ind='pack', proc='packaging.container crafts.ceramics_glass', reg='food_pack'),
    '253': dict(ind='pack', proc='packaging.container manufacturing.injection_molding', reg='food_pack'),
    '254': dict(ind='pack', proc='packaging.box packaging.label_print', reg='food_pack'),
    '255': dict(ind='pack', proc='crafts.wood_furniture packaging.box'),
    '256': dict(ind='pack', proc='manufacturing.textile', reg='fiber'),
    '257': dict(ind='pack', proc='packaging.container manufacturing.injection_molding', reg='food_pack'),
    '258': dict(ind='pack', proc='packaging.label_print'),
    '26': dict(ind='material'),
    '261': dict(ind='garden'), '262': dict(ind='garden'), '263': dict(ind='garden'), '264': dict(ind='garden'),
    '265': dict(ind='chem'), '266': dict(ind='chem'),
    '267': dict(ind='material', proc='apparel.leather'),
    '268': dict(ind='material', proc='apparel.leather'),

    # ---- 生産用の設備・機械
    '27': dict(ind='mech', proc=MECH, reg='pl'),
    '28': dict(ind='mech', proc=MECH, reg='pl'),
    '30': dict(ind='mech', proc=MECH + ' electronics.pcb_design', reg='pse pl'),
    '31': dict(ind='mech', proc=MECH, reg='pl'),
    '32': dict(ind='mech', proc=MECH, reg='pl'),
    '326': dict(ind='parts', proc='manufacturing.cnc'),
    '327': dict(ind='parts', proc='manufacturing.cnc manufacturing.sheet_metal'),
    '33': dict(ind='mech', proc=MECH + ' electronics.pcba electronics.firmware', reg='pl'),
    '34': dict(ind='parts', proc='manufacturing.cnc crafts.metal_goods'),
    '342': dict(ind='daily', proc='crafts.metal_goods manufacturing.cnc', reg='pl'),
    '343': dict(ind='parts', proc='manufacturing.cnc'),
    '344': dict(ind='mech', proc='manufacturing.rapid_proto manufacturing.cnc'),
    '35': dict(ind='mech', proc=MECH, reg='pl'),
    '36': dict(ind='mech', proc=MECH, reg='pl'),
    '37': dict(ind='mech', proc=MECH, reg='pl'),
    '38': dict(ind='mech', proc=MECH, reg='pl'),
    '39': dict(ind='mech', proc=MECH, reg='pl'),
    '40': dict(ind='garden', proc=MECH, reg='pl'),
    '41': dict(ind='mech', proc=MECH, reg='pl'),
    '411': dict(ind='apparel', proc='manufacturing.textile manufacturing.injection_molding', reg='pl'),
    '412': dict(ind='outdoor', proc='manufacturing.textile manufacturing.assembly', reg='pl'),
    '415': dict(ind='iot', proc=ELEC, reg='pse pl'),
    '42': dict(ind='garden', proc=MECH, reg='pl'),
    '43': dict(ind='mech', proc=MECH, reg='pl'),
    '44': dict(ind='parts', proc='manufacturing.cnc'),
    '45': dict(ind='parts', proc='manufacturing.cnc crafts.metal_goods'),

    # ---- 輸送用機械
    '46': dict(ind='vehicle', proc=MECH, reg='pl'),
    '47': dict(ind='vehicle', proc=MECH, reg='pl'),
    '478': dict(ind='car', proc='manufacturing.injection_molding manufacturing.sheet_metal manufacturing.cnc', reg='pl'),
    '48': dict(ind='car', proc='manufacturing.sheet_metal manufacturing.cnc manufacturing.assembly', reg='pl'),
    '49': dict(ind='vehicle', proc=MECH, reg='pl'),
    '50': dict(ind='vehicle', proc=MECH, reg='pl'),
    '51': dict(ind='vehicle', proc=MECH, reg='pl'),

    # ---- 情報通信・電気・電子
    '52': dict(ind='iot', proc=ELEC, reg='pse'),
    '54': dict(ind='iot', proc=ELEC + ' electronics.wireless testing.radio_cert', reg='giteki terminal pse'),
    '55': dict(ind='parts', proc='electronics.pcba'),
    '56': dict(ind='mech', proc=MECH + ' electronics.pcba', reg='pse pl'),
    '57': dict(ind='store', proc=MECH + ' electronics.pcba', reg='pse pl'),
    '58': dict(ind='store', proc=MECH + ' electronics.pcba electronics.firmware', reg='pse pl'),
    '59': dict(ind='iot', proc=ELEC, reg='pse'),
    '60': dict(ind='iot', proc=ELEC, reg='pse pl'),
    '604': dict(ind='daily', proc=ELEC, reg='pse pl'),
    '61': dict(ind='mech', proc=MECH + ' electronics.pcba', reg='pse pl'),
    '62': dict(ind='iot', proc=ELEC, reg='pse pl'),
    '621': dict(ind='store', proc='electronics.pcba manufacturing.assembly', reg='pse'),
    '622': dict(ind='store', proc='electronics.pcba manufacturing.sheet_metal manufacturing.assembly', reg='pse pl'),
    '623': dict(ind='iot', proc='electronics.low_power testing.battery_safety', reg='battery pse'),
    '626': dict(ind='car', proc='electronics.pcba manufacturing.assembly', reg='pl'),
    '63': dict(ind='measure', proc='electronics.pcba sensing mechanical.enclosure_design manufacturing.assembly', reg='pl'),
    '64': dict(ind='daily', proc='crafts.metal_goods electronics.pcba manufacturing.assembly', reg='zakka'),
    '65': dict(ind='measure', proc=MECH, reg='pl'),
    '653': dict(ind='iot', proc=ELEC, reg='pse'),
    '68': dict(ind='daily', proc='crafts.metal_goods manufacturing.cnc', reg='pl'),
    '681': dict(ind='kitchen', proc='crafts.metal_goods', reg='zakka pl'),

    # ---- 食料品・飲料（酒類・たばこを除く）
    '72': FOOD, '73': FOOD, '74': FOOD, '75': FOOD,
    '761': dict(ind='drink', proc='food.beverage_oem packaging.container packaging.label_print', reg='food_lic food_label haccp'),
    '763': FOOD,

    # ---- 生活・文化用品
    '77': dict(ind='kitchen', proc='crafts.metal_goods crafts.ceramics_glass manufacturing.injection_molding', reg='zakka food_pack'),
    '78': dict(ind='apparel', proc='apparel.garment_oem manufacturing.textile apparel.print_embroidery', reg='fiber'),
    '79': dict(ind='apparel', proc='manufacturing.textile apparel.leather', reg='fiber'),
    '795': dict(ind='bag', proc='manufacturing.textile apparel.leather', reg='bag'),
    '796': dict(ind='bag', proc='manufacturing.textile apparel.leather', reg='bag'),
    '797': dict(ind='daily', proc='manufacturing.textile crafts.metal_goods', reg='zakka'),
    '798': dict(ind='goods', proc='packaging.label_print crafts.wood_furniture', reg='premium'),
    '80': dict(ind='apparel', proc='apparel.leather manufacturing.silicone_molding', reg='zakka'),
    '81': dict(ind='goods', proc='crafts.metal_goods', reg='zakka'),
    '812': dict(ind='cosme', proc='manufacturing.injection_molding crafts.metal_goods', reg='zakka'),
    '82': dict(ind='daily', proc='manufacturing.textile', reg='fiber'),
    '83': dict(ind='wood', proc='crafts.wood_furniture manufacturing.sheet_metal', reg='zakka pl'),
    '84': dict(ind='kitchen', proc=MECH + ' electronics.pcba', reg='pse lpg pl'),
    '841': dict(ind='daily', proc=MECH + ' electronics.pcba', reg='pse lpg pl'),
    '842': dict(ind='daily', proc=MECH + ' electronics.pcba', reg='pse lpg pl'),
    '845': dict(ind='build', proc=MECH, reg='pse lpg pl'),
    '847': dict(ind='build', proc='crafts.ceramics_glass manufacturing.injection_molding', reg='pl'),
    '85': dict(ind='daily', proc='manufacturing.injection_molding crafts.metal_goods', reg='zakka'),
    '854': dict(ind='garden', proc='crafts.metal_goods manufacturing.injection_molding', reg='pl'),
    '855': dict(ind='goods', proc='crafts.ceramics_glass crafts.metal_goods crafts.wood_furniture', reg='zakka'),
    '856': dict(ind='wood', proc='manufacturing.textile crafts.metal_goods', reg='zakka'),
    '857': dict(ind='daily', proc='manufacturing.textile crafts.wood_furniture', reg='zakka'),
    '858': dict(ind='pet', proc='manufacturing.injection_molding manufacturing.textile', reg='pl'),
    '8615': dict(ind='daily', proc='manufacturing.textile', reg='zakka'),  # 衛生マスク
    '8676': dict(ind='kids', proc='manufacturing.injection_molding manufacturing.textile', reg='food_pack toy'),  # 乳児用品
    '88': dict(ind='cosme', proc='cosmetics.oem packaging.container packaging.label_print', reg='cosme'),
    '882': dict(ind='cosme', proc='cosmetics.oem packaging.container', reg='cosme'),
    '883': dict(ind='cosme', proc='cosmetics.household packaging.box', reg='soap'),
    '884': dict(ind='daily', proc='cosmetics.household packaging.container', reg='soap'),
    '885': dict(ind='daily', proc='cosmetics.household packaging.container', reg='zakka'),
    '89': dict(ind='kids', proc='manufacturing.injection_molding manufacturing.textile manufacturing.rapid_proto', reg='toy psc pl'),
    '891': dict(ind='store', proc=MECH, reg='pl'),
    '892': dict(ind='store', proc=MECH, reg='pl'),
    '893': dict(ind='goods', proc='crafts.metal_goods packaging.label_print', reg='premium'),
    '894': dict(ind='goods', proc='packaging.label_print manufacturing.injection_molding', reg='pl'),
    '90': dict(ind='instrument', proc='crafts.wood_furniture crafts.metal_goods manufacturing.assembly', reg='pl'),
    '906': dict(ind='instrument', proc=ELEC, reg='pse pl'),
    '91': dict(ind='outdoor', proc='manufacturing.injection_molding manufacturing.textile manufacturing.cnc', reg='pl'),
    '92': dict(ind='pack', proc='packaging.label_print'),
    '93': dict(ind='office', proc='packaging.label_print manufacturing.injection_molding', reg='zakka'),
    '937': dict(ind='office', proc='packaging.label_print'),
    '95': dict(ind='daily', proc='manufacturing.injection_molding crafts.metal_goods', reg='zakka'),
    '951': dict(ind='daily', proc='cosmetics.household packaging.box', reg='zakka'),
    '952': dict(ind='daily', proc='crafts.metal_goods manufacturing.textile', reg='zakka'),
    '953': dict(ind='store', proc='manufacturing.sheet_metal packaging.label_print', reg='pl'),
}
