"""工場向け仕様書（構想文 → 工場が見積に使う項目）の形と、品目別の項目・工場への質問。

- 全製品に共通の項目（COMMON）と、品目ごとに工場が見積前に聞く項目（CATS）を持つ。
  品目の項目は、比較ビズの公開案件 約250件と工場・OEM側の公開情報の分析（2026-11-14）に出てきたものだけ。
- 画面（template.html の __FSPEC__）・AIへの質問文の貼り戻し・KATACHI MCP が同じ形を使う。
  `python3 tools/fspec.py .` で data/fspec.json（MCPやほかの道具が読む）を書き出す。
- 文言は (日本語, 英語, 中国語) の組。assemble.py が日本語を __FSPEC__ に入れ、i18n.py が英中を辞書に足す。
- 値の確かさ: 原文（利用者の文章に書いてある）・回答（選択式で答えた）・DB（製品DB・公的機関の出典）・仮（わからない→似た製品の目安）・要確認。
  根拠のない値は作らない。「仮」は必ず仮と書き、工場への質問に回す。
"""
import json, sys, os

UNK = ('わからない', "I don't know", '不清楚')

# k: 項目キー, t: 見出し, req: 見積に要る（工場に出せる度に数える）, q: 利用者への質問, ch: 選択肢, multi: 複数選べる,
# fq: その項目が「仮」「要確認」のときに工場へ聞く文, sx: 貼り戻しJSONのキー
COMMON = [
    dict(k='name', t=('製品名', 'Product name', '产品名称'), req=1, sx='product_name'),
    dict(k='purpose', t=('何に使うか', 'What it is for', '用途'), req=1, sx='purpose',
         q=('何に使いますか', 'What will it be used for?', '用来做什么？'),
         ch=[('自社・自分の商品として売る', 'Sell it as our / my own product', '作为自己的商品销售'),
             ('お店・施設で使う', 'Use it in a shop or facility', '在店铺、设施中使用'),
             ('配る（ノベルティ・記念品）', 'Give it away (novelty, souvenir)', '赠送（赠品、纪念品）'),
             ('自分・家族で使う', 'Use it myself / with family', '自己、家人使用')]),
    dict(k='size', t=('大きさ', 'Size', '尺寸'), req=1, sx='size',
         q=('大きさはどのくらいですか', 'About how big is it?', '大概多大？'),
         ch=[('手のひらに乗る（〜10cm）', 'Fits in a palm (up to 10 cm)', '能放在手掌上（约10cm以内）'),
             ('両手で持てる（〜30cm）', 'Can be held in two hands (up to 30 cm)', '双手可拿（约30cm以内）'),
             ('机に置ける（〜60cm）', 'Fits on a desk (up to 60 cm)', '可放在桌上（约60cm以内）'),
             ('それより大きい', 'Larger than that', '比这更大')],
         fq=('この用途で現実的な大きさ（外形寸法）の目安を教えてください。', 'What overall dimensions are realistic for this use?', '请告诉我们这种用途下实际可行的外形尺寸参考。')),
    dict(k='mat', t=('素材', 'Material', '材质'), req=1, sx='materials',
         q=('素材の希望はありますか', 'Do you have a material in mind?', '对材质有要求吗？'),
         fq=('この用途に合う素材の候補と、素材による費用の違いを教えてください。', 'Which materials suit this use, and how do they change the cost?', '请告诉我们适合该用途的材质候选，以及不同材质的费用差异。')),
    dict(k='parts', t=('構成・部品', 'Components', '构成・零部件'), req=0, sx='components',
         fq=('部品の構成（部品表）の案をいただけますか。', 'Could you propose a component list (BOM)?', '能否提供零部件构成（BOM）的方案？')),
    dict(k='scope', t=('どこまで頼むか', 'Scope of the request', '委托范围'), req=1, sx='scope',
         q=('どこまで頼みますか', 'How much do you want to request?', '委托到哪一步？'),
         ch=[('設計から（図面がない）', 'From design (no drawings)', '从设计开始（没有图纸）'),
             ('図面・データがあり、作るだけ', 'I have drawings / data; just make it', '有图纸、数据，只需制作'),
             ('試作だけ先に', 'Prototype first', '先只做试制'),
             ('量産だけ（試作は済んでいる）', 'Mass production only (prototype done)', '只做量产（已完成试制）')]),
    dict(k='fit', t=('体・場所に合わせる調整', 'Fitting to a body or place', '按身体或场所调整'), req=0,
         q=('体や置く場所に合わせて、採寸・試着・調整が要りますか', 'Does it need measuring, trying on or adjusting to fit a body or a place?', '是否需要按身体或摆放位置进行测量、试穿、调整？'),
         ch=[('要る（体・場所に合わせる）', 'Yes (fitted to a body or place)', '需要（按身体或场所调整）'),
             ('要らない（決まった形・サイズ）', 'No (fixed shape and size)', '不需要（固定形状、尺寸）')]),
    dict(k='docs', t=('手元の資料', 'What you have', '手头资料'), req=1, multi=1, sx='docs',
         q=('手元にある資料はどれですか（いくつでも）', 'Which of these do you have? (choose any)', '手头有哪些资料？（可多选）'),
         ch=[('図面', 'Drawings', '图纸'), ('3Dデータ', '3D data', '3D数据'), ('手書きのスケッチ', 'Hand sketch', '手绘草图'),
             ('写真', 'Photos', '照片'), ('現物を送れる', 'A physical sample I can send', '可寄送实物'),
             ('型紙・パターン', 'Sewing pattern', '纸样'), ('配合・レシピ', 'Formula / recipe', '配方'),
             ('入稿データ（ロゴ・デザイン）', 'Print-ready artwork (logo, design)', '印刷数据（标志、设计）'), ('ない', 'Nothing yet', '没有')]),
    dict(k='qs', t=('試作・サンプルの数', 'Prototype / sample quantity', '试制・样品数量'), req=1, sx='quantity_proto',
         q=('試作・サンプルは何個ほしいですか', 'How many prototypes or samples do you want?', '需要多少个试制品、样品？'),
         ch=[('1個', '1', '1个'), ('2〜5個', '2–5', '2～5个'), ('6〜20個', '6–20', '6～20个'), ('試作はいらない', 'No prototype needed', '不需要试制')],
         fq=('試作は何個から頼めますか。', 'From how many units can you take a prototype order?', '试制从几个起可以委托？')),
    dict(k='qf', t=('初回の数', 'First order quantity', '首批数量'), req=1, sx='quantity_mass',
         q=('最初に作る数はどのくらいですか', 'How many for the first run?', '首批大概做多少？'),
         ch=[('〜100個', 'Up to 100', '100个以内'), ('〜500個', 'Up to 500', '500个以内'), ('〜3,000個', 'Up to 3,000', '3,000个以内'),
             ('それ以上', 'More than that', '更多'), ('まだ決めていない', 'Not decided yet', '还没决定')],
         fq=('最小ロットはいくつですか。数による単価の違いも教えてください。', 'What is the minimum order quantity, and how does the unit price change with quantity?', '最小起订量是多少？也请告诉我们不同数量的单价差异。')),
    dict(k='qc', t=('継続して作る数（月あたり）', 'Ongoing quantity (per month)', '持续生产数量（每月）'), req=0, sx='quantity_cont',
         q=('そのあと続けて作りますか', 'Will you keep making it after that?', '之后会持续生产吗？'),
         ch=[('続けない', 'No', '不持续'), ('月〜100個', 'Up to 100 a month', '每月100个以内'), ('月〜1,000個', 'Up to 1,000 a month', '每月1,000个以内'),
             ('それ以上', 'More than that', '更多'), ('まだ決めていない', 'Not decided yet', '还没决定')]),
    dict(k='due', t=('希望の時期', 'When you need it', '希望时间'), req=1, sx='due',
         q=('いつまでにほしいですか', 'When do you need it?', '希望什么时候拿到？'),
         ch=[('1か月以内', 'Within 1 month', '1个月以内'), ('3か月以内', 'Within 3 months', '3个月以内'), ('半年以内', 'Within 6 months', '半年以内'),
             ('1年以内', 'Within a year', '1年以内'), ('決まっていない', 'No fixed date', '未定')],
         fq=('試作と量産、それぞれの期間の目安を教えてください。', 'How long do the prototype and mass production usually take?', '请告诉我们试制和量产各自所需时间的参考。')),
    dict(k='budget', t=('予算・目標の単価', 'Budget / target unit price', '预算・目标单价'), req=0, sx='budget',
         fq=('この内容での概算の費用（試作・初回）を教えてください。', 'What is a rough cost for this (prototype and first run)?', '请告诉我们按此内容的大致费用（试制・首批）。')),
    dict(k='sure', t=('発注の確度', 'How firm the order is', '下单确定程度'), req=0, sx='certainty',
         q=('発注はいつごろになりそうですか', 'When are you likely to place the order?', '大概什么时候下单？'),
         ch=[('すぐ発注したい', 'Ready to order now', '想马上下单'), ('数か月以内に発注', 'Within a few months', '几个月内下单'),
             ('資金や販路が決まってから', 'After funding or sales channels are set', '资金或销路确定之后'), ('情報を集めている段階', 'Still gathering information', '还在收集信息')]),
    dict(k='reg', t=('規格・法規制', 'Standards and regulations', '标准・法规'), req=0, sx='regulations',
         fq=('この製品で必要な認証・表示と、その手続きを頼めるか教えてください。', 'Which certifications and labels does this product need, and can you handle them?', '请告诉我们该产品需要的认证、标示，以及能否委托办理。')),
    dict(k='env', t=('使う環境', 'Where it is used', '使用环境'), req=0, sx='environment'),
]

# 品目ごとの項目。proc: 製品DB・工程の読み取りで当てる工程コードの先頭、ind: 製品DBの業界、re: 文章の言葉。
# key=1 の項目は「この品目で見積に必要な点」として工場に出せる度に数える。asks: 工場に必ず聞くこと（費用を大きく分けるもの）
CATS = [
    dict(id='elec', t=('電子・基板', 'Electronics / PCB', '电子・电路板'), proc=['electronics', 'sensing', 'testing.radio_cert', 'testing.battery_safety', 'software'], ind=['iot', 'wear'],
         re=r'基板|回路|センサ|bluetooth|\bble\b|wi-?fi|充電|電池|バッテリー|アプリ|\biot\b|ウェアラブル|スマート',
         items=[dict(k='escope', t=('電子の部分でどこまで頼むか', 'Which electronics work to request', '电子部分委托到哪一步'), key=1, multi=1,
                     q=('電子の部分は、どこまで頼みますか（いくつでも）', 'Which parts of the electronics do you need? (choose any)', '电子部分要委托哪些？（可多选）'),
                     ch=[('回路の設計', 'Circuit design', '电路设计'), ('基板の設計・製造', 'PCB design and manufacturing', '电路板设计・制造'), ('ファームウェア', 'Firmware', '固件'),
                         ('筐体（ケース）', 'Enclosure', '外壳'), ('スマホのアプリ', 'Smartphone app', '手机应用')]),
                dict(k='power', t=('電源', 'Power', '电源'), key=1, q=('電源はどうしますか', 'How is it powered?', '电源怎么解决？'),
                     ch=[('乾電池', 'Dry-cell batteries', '干电池'), ('充電式', 'Rechargeable', '充电式'), ('コンセント', 'Mains outlet', '插座供电')],
                     fq=('電池の持ち（連続で何日動くか）の目安と、そのための電池の大きさを教えてください。', 'How long would the battery last, and what battery size does that need?', '请告诉我们电池续航（可连续工作几天）的参考，以及所需电池大小。')),
                dict(k='comm', t=('通信', 'Connectivity', '通信'), key=0, multi=1, q=('通信は使いますか（いくつでも）', 'Does it connect? (choose any)', '是否使用通信？（可多选）'),
                     ch=[('使わない', 'No connection', '不使用'), ('Bluetooth', 'Bluetooth', 'Bluetooth'), ('Wi-Fi', 'Wi-Fi', 'Wi-Fi'), ('LTE（携帯回線）', 'LTE (cellular)', 'LTE（移动网络）'), ('GPS', 'GPS', 'GPS')]),
                dict(k='have', t=('現物の試作品', 'Existing prototype', '现有试制品'), key=0, q=('手作りの試作品などはありますか', 'Do you have a homemade prototype?', '有自己做的试制品吗？'),
                     ch=[('ある', 'Yes', '有'), ('ない', 'No', '没有')])],
         asks=[('技適（電波法）・PSE（電気用品安全法）など、必要な認証と費用を教えてください。', 'Which certifications (Japan radio law, PSE, etc.) are needed, and at what cost?', '请告诉我们需要的认证（日本无线电法、PSE等）及费用。'),
               ('設計費は見積に含まれますか。別ならその目安を教えてください。', 'Is design included in the quote? If not, roughly how much is it?', '设计费是否包含在报价中？如果另算，请告诉我们大致金额。')]),
    dict(id='metal', t=('金属・切削', 'Metal / machining', '金属・切削'), proc=['manufacturing.sheet_metal', 'manufacturing.cnc', 'crafts.metal_goods', 'manufacturing.casting', 'manufacturing.welding'], ind=['parts', 'mech'],
         re=r'金属|ステンレス|アルミ|鉄|板金|切削|削り出し|溶接|\bsus\d|a5052|a6061',
         items=[dict(k='grade', t=('材質（記号）', 'Material grade', '材质（牌号）'), key=1, q=('金属の材質は決まっていますか', 'Is the metal grade decided?', '金属材质定了吗？'),
                     ch=[('ステンレス（SUS304など）', 'Stainless (e.g. SUS304)', '不锈钢（如SUS304）'), ('アルミ（A5052・A6061など）', 'Aluminium (e.g. A5052, A6061)', '铝（如A5052、A6061）'), ('鉄（SS400など）', 'Steel (e.g. SS400)', '钢（如SS400）')]),
                dict(k='tol', t=('公差（寸法の精度）', 'Tolerance', '公差（尺寸精度）'), key=1, q=('寸法の精度はどのくらい要りますか', 'How precise do the dimensions need to be?', '尺寸精度要求多高？'),
                     ch=[('ふつう（一般公差でよい）', 'Normal (general tolerance)', '一般（一般公差即可）'), ('高い（±0.05mm程度）', 'High (about ±0.05 mm)', '高（约±0.05mm）')]),
                dict(k='surf', t=('表面処理', 'Surface finish', '表面处理'), key=0, q=('表面の仕上げはどうしますか', 'What surface finish?', '表面怎么处理？'),
                     ch=[('なし', 'None', '无'), ('アルマイト', 'Anodising', '阳极氧化'), ('塗装', 'Painting', '喷涂'), ('メッキ', 'Plating', '电镀'), ('研磨', 'Polishing', '抛光')]),
                dict(k='supply', t=('材料の支給', 'Material supply', '材料供应'), key=0, q=('材料はどうしますか', 'Who supplies the material?', '材料怎么解决？'),
                     ch=[('工場に任せる', 'Factory supplies it', '交给工厂'), ('こちらで用意する', 'We supply it', '我方提供')])],
         asks=[('部品ごとの単価か一式の価格か、月あたりの数でどう変わるかを教えてください。', 'Is the price per part or per set, and how does monthly volume change it?', '请告诉我们是按零件单价还是整套价格，以及每月数量对价格的影响。')]),
    dict(id='resin', t=('樹脂・アクリル', 'Plastic / acrylic', '树脂・亚克力'), proc=['manufacturing.injection_molding', 'manufacturing.silicone_molding', 'manufacturing.rapid_proto', 'manufacturing.blow_molding'], ind=[],
         re=r'樹脂|プラスチック|アクリル|\babs\b|\bpp\b|ポリカ|シリコ|成形|金型|3dプリント',
         items=[dict(k='rgrade', t=('樹脂の種類', 'Plastic type', '树脂种类'), key=1, q=('樹脂の種類は決まっていますか', 'Is the plastic type decided?', '树脂种类定了吗？'),
                     ch=[('ABS', 'ABS', 'ABS'), ('PP', 'PP', 'PP'), ('PC（ポリカーボネート）', 'PC (polycarbonate)', 'PC（聚碳酸酯）'), ('アクリル（PMMA）', 'Acrylic (PMMA)', '亚克力（PMMA）'), ('POM', 'POM', 'POM'), ('シリコーン', 'Silicone', '硅胶')]),
                dict(k='color', t=('透明・色', 'Clear or coloured', '透明・颜色'), key=0, q=('色はどうしますか', 'What colour?', '颜色怎么定？'),
                     ch=[('透明', 'Clear', '透明'), ('1色', 'One colour', '单色'), ('複数の色', 'Several colours', '多种颜色')]),
                dict(k='finish', t=('塗装・メッキ・印刷', 'Paint, plating, printing', '喷涂・电镀・印刷'), key=0, q=('表面の加工はしますか', 'Any surface decoration?', '表面要加工吗？'),
                     ch=[('なし', 'None', '无'), ('塗装', 'Painting', '喷涂'), ('メッキ', 'Plating', '电镀'), ('ロゴの印刷', 'Logo printing', '标志印刷')]),
                dict(k='method', t=('作り方（削り出しか金型か）', 'Method (machined / printed or moulded)', '制作方式（切削还是模具）'), key=1, q=('作り方の希望はありますか', 'Any preferred method?', '对制作方式有要求吗？'),
                     ch=[('削り出し・3Dプリント（少量）', 'Machined / 3D printed (small runs)', '切削・3D打印（少量）'), ('金型で成形（数が多い）', 'Injection moulded (large runs)', '模具成型（数量多）'), ('数に合わせて相談', 'Decide based on quantity', '根据数量商量')],
                     fq=('この数なら、削り出し・3Dプリントと金型のどちらが安いですか。金型の費用と持ち主も教えてください。', 'At this quantity, is machining / 3D printing or a mould cheaper? What does the mould cost and who owns it?', '这个数量下，切削/3D打印和模具哪个便宜？也请告诉我们模具费用及归属。'))],
         asks=[('金型を作る場合、金型の費用と持ち主（こちらに残せるか）を教えてください。', 'If a mould is made, what does it cost and can we own it?', '如需制作模具，请告诉我们模具费用及归属（能否归我方）。')]),
    dict(id='apparel', t=('アパレル', 'Apparel', '服装'), proc=['manufacturing.textile', 'apparel'], ind=['apparel', 'bag'],
         re=r'服|シャツ|パーカー|ウェア(?!ラブル)|帽子|バッグ|生地|縫製|刺繍|アパレル|トート|エプロン',
         items=[dict(k='fabric', t=('生地', 'Fabric', '面料'), key=1, q=('生地の希望はありますか', 'Any fabric in mind?', '对面料有要求吗？'),
                     ch=[('綿', 'Cotton', '棉'), ('ポリエステル', 'Polyester', '涤纶'), ('ナイロン', 'Nylon', '尼龙'), ('ウール', 'Wool', '羊毛'), ('革', 'Leather', '皮革')]),
                dict(k='weave', t=('ニットか布帛か', 'Knit or woven', '针织还是梭织'), key=0, q=('生地の作りはどちらですか', 'Knit or woven?', '面料是哪种？'),
                     ch=[('ニット（Tシャツなど）', 'Knit (e.g. T-shirts)', '针织（如T恤）'), ('布帛（シャツなど）', 'Woven (e.g. shirts)', '梭织（如衬衫）')]),
                dict(k='sizes', t=('サイズ展開と色数', 'Sizes and colours', '尺码与颜色数'), key=1, q=('サイズと色は何種類ですか', 'How many sizes and colours?', '尺码和颜色有几种？'),
                     ch=[('1サイズ・1色', 'One size, one colour', '1个尺码・1种颜色'), ('3サイズ前後', 'About 3 sizes', '3个尺码左右'), ('5サイズ以上', '5 sizes or more', '5个尺码以上')]),
                dict(k='deco', t=('プリント・刺繍', 'Print / embroidery', '印花・刺绣'), key=0, q=('プリントや刺繍は入れますか', 'Any print or embroidery?', '要加印花或刺绣吗？'),
                     ch=[('なし', 'None', '无'), ('プリント', 'Print', '印花'), ('刺繍', 'Embroidery', '刺绣')]),
                dict(k='tag', t=('付属（タグ・ネーム）', 'Tags and labels', '辅料（吊牌・织标）'), key=0, q=('タグやネームは付けますか', 'Tags or labels?', '要加吊牌或织标吗？'),
                     ch=[('なし', 'None', '无'), ('下げ札', 'Hang tag', '吊牌'), ('織りネーム', 'Woven label', '织标')]),
                dict(k='fsup', t=('生地の支給', 'Fabric supply', '面料供应'), key=0, q=('生地はどうしますか', 'Who supplies the fabric?', '面料怎么解决？'),
                     ch=[('工場に任せる', 'Factory supplies it', '交给工厂'), ('こちらで用意する', 'We supply it', '我方提供')])],
         asks=[('型紙（パターン）とサンプルは作ってもらえますか。その費用と、1型あたりの最小枚数を教えてください。', 'Can you make the pattern and sample? What do they cost, and what is the minimum per style?', '能否制作纸样和样衣？请告诉我们费用和每款最少件数。')]),
    dict(id='pet', t=('ペット用品', 'Pet products', '宠物用品'), proc=['food.pet_food'], ind=['pet'],
         re=r'犬|猫|ペット|ドッグ|首輪|ハーネス|リード',
         items=[dict(k='target', t=('対象（犬猫・大きさ）', 'Target animals', '对象（犬猫・体型）'), key=1, multi=1, q=('どの子向けですか（いくつでも）', 'Which pets is it for? (choose any)', '面向哪些宠物？（可多选）'),
                     ch=[('小型犬', 'Small dogs', '小型犬'), ('中型犬', 'Medium dogs', '中型犬'), ('大型犬', 'Large dogs', '大型犬'), ('猫', 'Cats', '猫')]),
                dict(k='psize', t=('サイズ展開', 'Size range', '尺码范围'), key=1, q=('サイズは何種類にしますか', 'How many sizes?', '做几种尺码？'),
                     ch=[('1サイズ', 'One size', '1个尺码'), ('S・M・Lなど複数', 'Several (S, M, L…)', 'S・M・L等多个')]),
                dict(k='wash', t=('洗えるか', 'Washable', '可否清洗'), key=0, q=('洗えるようにしますか', 'Should it be washable?', '要可以清洗吗？'),
                     ch=[('洗えるようにしたい', 'Yes, washable', '希望可清洗'), ('洗えなくてよい', 'Not needed', '不需要')]),
                dict(k='chew', t=('誤飲・かじる対策', 'Chew / swallow safety', '防误吞・防啃咬'), key=0, q=('かじる・飲み込む対策は要りますか', 'Need chew / swallow safety?', '需要防啃咬、防误吞吗？'),
                     ch=[('必要', 'Yes', '需要'), ('不要', 'No', '不需要')])],
         asks=[('サンプルの型（同じような製品の型）はありますか。新しく作る場合の費用も教えてください。', 'Do you have an existing pattern / mould for a similar product? What does a new one cost?', '是否有类似产品的现成样板/模具？新做的话费用多少？')]),
    dict(id='food', t=('食品', 'Food', '食品'), proc=['food'], ind=['food', 'drink'],
         re=r'食品|お菓子|菓子|ソース|調味料|飲料|ジュース|パン|ケーキ|レトルト|冷凍|サプリ',
         items=[dict(k='recipe', t=('配合・レシピ', 'Recipe', '配方'), key=1, q=('配合・レシピはありますか', 'Do you have a recipe?', '有配方吗？'),
                     ch=[('ある', 'Yes', '有'), ('ない（作ってほしい）', 'No (please develop it)', '没有（希望代为开发）')]),
                dict(k='form', t=('形態', 'Form', '形态'), key=1, q=('どの形で売りますか', 'In what form?', '以什么形态销售？'),
                     ch=[('常温', 'Shelf-stable', '常温'), ('冷蔵', 'Chilled', '冷藏'), ('冷凍', 'Frozen', '冷冻'), ('レトルト', 'Retort pouch', '蒸煮袋'), ('乾燥・粉', 'Dried / powder', '干燥・粉末')]),
                dict(k='raw', t=('原料の持ち込み', 'Bringing your own ingredients', '自带原料'), key=0, q=('原料を持ち込みますか', 'Will you supply ingredients?', '是否自带原料？'),
                     ch=[('持ち込む', 'Yes', '自带'), ('工場に任せる', 'Factory sources them', '交给工厂')]),
                dict(k='sales', t=('売り先', 'Sales channels', '销售渠道'), key=0, multi=1, q=('どこで売りますか（いくつでも）', 'Where will you sell it? (choose any)', '在哪里销售？（可多选）'),
                     ch=[('通販（EC）', 'Online', '网店'), ('ふるさと納税', 'Furusato nozei', '故乡纳税'), ('店舗', 'Shops', '店铺'), ('イベント', 'Events', '活动')])],
         asks=[('初回の最小ロット（kg・個・食）と、包装・表示（ラベル）まで頼めるかを教えてください。', 'What is the minimum first lot (kg / units / servings), and can you handle packaging and labelling?', '请告诉我们首批最小批量（kg・个・份），以及能否包办包装和标签。')]),
    dict(id='cosme', t=('化粧品', 'Cosmetics', '化妆品'), proc=['cosmetics'], ind=['cosme'],
         re=r'化粧品|コスメ|美容液|化粧水|クリーム|シャンプー|石けん|せっけん|ボディ',
         items=[dict(k='ctype', t=('品目', 'Product type', '品类'), key=1, q=('どの種類ですか', 'Which type?', '哪个品类？'),
                     ch=[('スキンケア', 'Skincare', '护肤'), ('ヘアケア', 'Haircare', '护发'), ('ボディケア', 'Body care', '身体护理'), ('メイク', 'Make-up', '彩妆')]),
                dict(k='vol', t=('容量', 'Volume', '容量'), key=1, q=('1本の容量はどのくらいですか', 'What volume per unit?', '每瓶容量多少？'),
                     ch=[('〜30mL', 'Up to 30 mL', '30mL以内'), ('〜100mL', 'Up to 100 mL', '100mL以内'), ('〜300mL', 'Up to 300 mL', '300mL以内'), ('それ以上', 'More', '更多')]),
                dict(k='box', t=('容器・箱', 'Container and box', '容器・包装盒'), key=0, q=('容器と箱はどうしますか', 'Container and box?', '容器和盒子怎么办？'),
                     ch=[('既製の容器でよい', 'Stock container is fine', '现成容器即可'), ('オリジナルの容器', 'Custom container', '定制容器'), ('箱も作る', 'Also make a box', '也做包装盒')])],
         asks=[('最小ロットと、試作の回数・期間の目安を教えてください。', 'What is the minimum lot, and how many trial batches and how long does development take?', '请告诉我们最小批量，以及试制次数和周期的参考。'),
               ('表示（全成分・薬機法）の確認まで頼めますか。', 'Can you check the labelling (full ingredients, Japanese PMD Act)?', '能否代为确认标示（全成分、日本药机法）？')]),
    dict(id='wood', t=('木工・家具', 'Woodwork / furniture', '木工・家具'), proc=['crafts.wood_furniture'], ind=['wood', 'store'],
         re=r'木|家具|棚|テーブル|椅子|什器|ウッド',
         items=[dict(k='wood', t=('樹種', 'Wood type', '木材种类'), key=1, q=('木の種類は決まっていますか', 'Is the wood type decided?', '木材种类定了吗？'),
                     ch=[('パイン', 'Pine', '松木'), ('ナラ・オーク', 'Oak', '橡木'), ('ウォールナット', 'Walnut', '胡桃木'), ('合板', 'Plywood', '胶合板')]),
                dict(k='paint', t=('塗装', 'Finish', '涂装'), key=0, q=('塗装はどうしますか', 'What finish?', '怎么涂装？'),
                     ch=[('なし', 'None', '无'), ('オイル', 'Oil', '木蜡油'), ('ウレタン', 'Urethane', '聚氨酯'), ('着色', 'Stain', '着色')]),
                dict(k='kd', t=('組み立て式か', 'Flat-pack or assembled', '是否组装式'), key=0, q=('納品の形はどちらですか', 'How should it be delivered?', '以什么形式交付？'),
                     ch=[('組み立て式', 'Flat-pack', '组装式'), ('完成品で納品', 'Fully assembled', '成品交付')]),
                dict(k='place', t=('使う場所', 'Where it is used', '使用场所'), key=1, q=('どこで使いますか', 'Where will it be used?', '在哪里使用？'),
                     ch=[('家庭', 'Home', '家庭'), ('店舗', 'Shop', '店铺'), ('施設', 'Facility', '设施'), ('子ども用', 'For children', '儿童用')])],
         asks=[('設計から頼めますか。NC加工か手加工かで、費用がどう変わるかも教えてください。', 'Can you take it from design? How does cost differ between CNC and hand work?', '能否从设计开始委托？也请告诉我们数控加工和手工加工的费用差异。')]),
    dict(id='goods', t=('雑貨・ノベルティ', 'Goods / novelties', '杂货・赠品'), proc=['packaging.label_print', 'crafts.ceramics_glass', 'packaging'], ind=['goods', 'daily', 'pack', 'office', 'kitchen'],
         re=r'ノベルティ|グッズ|キーホルダー|ステッカー|缶バッジ|マグ|タオル|記念品|販促',
         items=[dict(k='colors', t=('印刷の色数', 'Print colours', '印刷颜色数'), key=1, q=('印刷は何色ですか', 'How many print colours?', '印刷几种颜色？'),
                     ch=[('1色', 'One colour', '单色'), ('2〜3色', '2–3 colours', '2～3色'), ('フルカラー', 'Full colour', '全彩')]),
                dict(k='art', t=('入稿データ', 'Artwork', '印刷数据'), key=1, q=('デザインのデータはありますか', 'Do you have the artwork?', '有设计数据吗？'),
                     ch=[('ある', 'Yes', '有'), ('ない（作ってほしい）', 'No (please make it)', '没有（希望代做）')]),
                dict(k='indiv', t=('個包装', 'Individual packaging', '独立包装'), key=0, q=('1個ずつの包装は要りますか', 'Individual packaging?', '需要单个包装吗？'),
                     ch=[('なし', 'None', '无'), ('OPP袋', 'OPP bag', 'OPP袋'), ('台紙付き', 'With backing card', '带卡纸')]),
                dict(k='kinds', t=('種類の数', 'Number of designs', '款式数量'), key=0, q=('デザインは何種類ですか', 'How many designs?', '设计有几种？'),
                     ch=[('1種類', 'One', '1种'), ('2〜5種類', '2–5', '2～5种'), ('6種類以上', '6 or more', '6种以上')])],
         asks=[('種類ごとの最小数と、使う日（イベント日）に間に合う日程かを教えてください。', 'What is the minimum per design, and can you meet the event date?', '请告诉我们每款的最小数量，以及能否赶上使用日（活动日）。')]),
]

# 画面の文言（日英中）
UI = [
    ('工場向け仕様書', 'Spec sheet for factories', '面向工厂的规格书'),
    ('工場に出せる度', 'Ready for factories', '可交给工厂的程度'),
    ('見積に出せます', 'Ready to request quotes', '可以申请报价'),
    ('設計の見積から始めます', 'Start with a design quote', '先从设计报价开始'),
    ('あと少しで見積に出せます', 'Almost ready for quotes', '再补充一点即可申请报价'),
    ('必要な項目がそろいました。この仕様書を見積の依頼に付けて送れます。', 'The key items are filled. You can attach this spec sheet to your quote request.', '必要项目已齐全。可将此规格书附在报价申请中发送。'),
    ('図面や3Dデータがないため、工場はまず設計（仕様を決める仕事）の費用を見積もります。この仕様書を設計の依頼書として送ります。', 'Without drawings or 3D data, factories first quote the design work (deciding the specs). This sheet is sent as the design request.', '由于没有图纸或3D数据，工厂会先报设计（确定规格的工作）费用。此规格书将作为设计委托书发送。'),
    ('下の質問に答えると、工場が見積に使える情報がそろいます。わからない所は「わからない」で大丈夫です。', 'Answer the questions below to give factories what they need for a quote. "I don\'t know" is fine.', '回答下面的问题，即可备齐工厂报价所需的信息。不清楚的可以选「不清楚」。'),
    ('質問に答える', 'Answer questions', '回答问题'),
    ('次の質問へ', 'Next questions', '下一组问题'),
    ('答えを反映する', 'Apply answers', '应用回答'),
    ('仕様書', 'Spec sheet', '规格书'),
    ('項目', 'Item', '项目'), ('内容', 'Details', '内容'), ('確かさ', 'Basis', '可信度'), ('根拠', 'Source', '依据'),
    ('原文', 'Your text', '原文'), ('回答', 'Your answer', '回答'), ('製品DB', 'Product DB', '产品DB'), ('仮', 'Provisional', '暂定'), ('要確認', 'To confirm', '待确认'),
    ('品目', 'Product category', '品类'),
    ('工場に聞くこと（自動で依頼書に付きます）', 'Questions for the factory (added to the request automatically)', '要问工厂的问题（自动附在委托书中）'),
    ('印刷・PDFで保存', 'Print / save as PDF', '打印・保存为PDF'),
    ('テキストをコピー', 'Copy as text', '复制文本'),
    ('コピーしました', 'Copied', '已复制'),
    ('設計の下書き', 'Design draft', '设计草稿'),
    ('製品イメージ案の3Dデータ（STL）を保存', 'Save the concept as 3D data (STL)', '将产品构想保存为3D数据（STL）'),
    ('寸法図（SVG）を保存', 'Save the dimension drawing (SVG)', '保存尺寸图（SVG）'),
    ('KATACHIが作る下書きです。単純な形なら3Dプリントの試作に出せます。回路・基板・強度・防水・金型は、設計者が仕上げる前提です。', 'This is a draft made by KATACHI. Simple shapes can go straight to 3D-printed prototypes. Circuits, PCBs, strength, waterproofing and moulds still need a designer.', '这是KATACHI制作的草稿。简单形状可直接用于3D打印试制。电路、电路板、强度、防水、模具仍需设计师完成。'),
    ('仮の値は、似た製品の目安です。工場との打ち合わせで決まります。', 'Provisional values are guides from similar products and are settled with the factory.', '暂定值是参考类似产品的估计，将与工厂商定。'),
    ('この仕様書を付けて見積を依頼', 'Request quotes with this spec sheet', '附上此规格书申请报价'),
    ('（KATACHIが整理した工場向け仕様書）', '(Spec sheet for factories, organised by KATACHI)', '（KATACHI整理的面向工厂的规格书）'),
    ('仮：', 'Provisional: ', '暂定：'),
    ('製品イメージ案', 'Product concept', '产品构想'),
    ('似た製品の目安', 'guide from similar products', '类似产品的参考'),
    ('工場の最小ロットに合わせて相談', 'Discuss based on the factory\'s minimum lot', '根据工厂最小批量商量'),
    ('工場のすすめる数で相談', 'Discuss the number the factory recommends', '按工厂建议的数量商量'),
    ('急がない（相談）', 'Not urgent (discuss)', '不急（商量）'),
    ('図面なしで、この仕様書から設計を受けられますか。設計費と期間の目安を教えてください。', 'Can you take on the design from this spec sheet without drawings? Roughly what are the design cost and time?', '没有图纸的情况下，能否根据此规格书承接设计？请告诉我们设计费和周期的参考。'),
    ('返事では、概算の費用・似た製品の実績・日程・量産まで手伝えるかを教えてください。', 'In your reply, please include a rough cost, similar past work, a schedule, and whether you can support mass production.', '回复时，请告诉我们大致费用、类似产品的实绩、日程，以及能否支持到量产。'),
    ('この項目が決まっていません。この製品での一般的な決め方と、費用への影響を教えてください。', 'This item is not decided. How is it usually decided for this product, and how does it affect cost?', '此项目尚未确定。请告诉我们该产品一般如何确定，以及对费用的影响。'),
    ('工場向け仕様書（KATACHIが整理）', 'Spec sheet for factories (organised by KATACHI)', '面向工厂的规格书（KATACHI整理）'),
    ('答えた項目', 'answered', '已回答项目'),
    ('の項目', ' items', '的项目'),
    # 既製品をもとに作る（参考品の値・変えるところ・採寸／スキャン・権利の確認）
    ('参考品', 'Reference product', '参考品'),
    ('参考にした既製品', 'Reference product', '参考的现有产品'),
    ('変えるところ', 'What to change', '要修改的地方'),
    ('権利の確認（特許・意匠・商標）', 'Rights check (patents, designs, trademarks)', '权利确认（专利、外观设计、商标）'),
    ('既製品をもとに作る手順', 'Making it from an existing product', '以现有产品为基础制作的步骤'),
    ('参考品の値を読み取る：大きさ・素材は「参考品」として表に入れました。あなたの製品の値ではないので、工場と決め直します。', 'Read the reference values: size and material are in the table as "Reference product". They are not your product\'s values and will be settled with the factory.', '读取参考品的数值：尺寸、材质已作为「参考品」填入表中。这不是你的产品的数值，将与工厂重新确定。'),
    ('変えるところを決める：変える点が少ないと、作れない・売れないことがあります。', 'Decide what to change: with too few changes, it may not be possible to make or sell.', '确定要修改的地方：修改太少的话，可能无法制作或销售。'),
    ('現物の採寸・3Dスキャン：図面がないときは、現物を測る・スキャンして図面や3Dデータにします（費用は別にかかります）。', 'Measure or 3D-scan the physical item: without drawings, the item is measured or scanned to make drawings or 3D data (charged separately).', '实物测量・3D扫描：没有图纸时，测量或扫描实物，制作图纸或3D数据（费用另计）。'),
    ('権利の確認：J-PlatPat（特許情報プラットフォーム、無料）で特許・意匠・商標を調べ、心配なら弁理士に相談します。KATACHIは「侵害しない」とは判断しません。', 'Check rights: search patents, designs and trademarks on J-PlatPat (free), and consult a patent attorney if unsure. KATACHI does not judge that something is non-infringing.', '确认权利：在J-PlatPat（日本专利信息平台，免费）查询专利、外观设计、商标，如有担心请咨询专利代理人。KATACHI不判断「不侵权」。'),
    ('J-PlatPatで調べる', 'Search J-PlatPat', '在J-PlatPat查询'),
    ('参考品をもとに、変えるところを入れたオリジナルとして作れますか。', 'Can you make this as an original product based on the reference, with the changes listed?', '能否以参考品为基础，加入修改点，作为原创产品制作？'),
    ('現物を採寸・3Dスキャンして、図面や3Dデータにできますか。費用と期間を教えてください（できない場合は、できる会社の紹介も歓迎です）。', 'Can you measure or 3D-scan the item and turn it into drawings or 3D data? Please give the cost and time (if not, a referral is welcome).', '能否测量・3D扫描实物，制作成图纸或3D数据？请告诉我们费用和周期（如无法承接，也欢迎介绍可以做的公司）。'),
    ('参考品の特許・意匠・商標にかからない形にするため、気をつける点があれば教えてください（権利の最終確認は依頼者が行います）。', 'If there is anything to watch for so the product avoids the reference\'s patents, designs or trademarks, please tell us (the requester makes the final rights check).', '为避免涉及参考品的专利、外观设计、商标，如有需要注意的地方请告诉我们（权利的最终确认由委托方进行）。'),
    # 法令の条文リンク・技適の検索
    ('条文（e-Gov法令検索）：', 'Law text (e-Gov): ', '法条原文（e-Gov法令检索）：'),
    ('技適（電波法）を調べる', 'Check radio certification (Giteki)', '查询技适（日本电波法认证）'),
    ('無線（Bluetooth・Wi-Fi・LTEなど）を使うなら、技適を取った無線モジュールを使うと、製品ごとの認証が要らないことがあります。使う予定のモジュールの型式を入れると、総務省の登録を調べます。', 'If the product uses radio (Bluetooth, Wi-Fi, LTE, etc.), using a module that already has Japanese radio certification (Giteki) may remove the need to certify the product itself. Enter the module model to check the Ministry\'s register.', '如使用无线（Bluetooth、Wi-Fi、LTE等），使用已取得技适的无线模块，有时可免去整机认证。输入计划使用的模块型号，即可查询总务省的登记。'),
    ('調べる', 'Check', '查询'),
    ('総務省の技適検索で調べる', 'Search on the Ministry\'s Giteki site', '在总务省技适检索中查询'),
    ('調べています…', 'Checking…', '正在查询…'),
    ('型式を3文字以上入れてください', 'Enter at least 3 characters of the model', '请输入至少3个字符的型号'),
    ('いまは調べられませんでした。下の「総務省の技適検索」で調べてください。', 'Could not check right now. Please use the Ministry\'s Giteki search below.', '暂时无法查询。请使用下方的「总务省技适检索」。'),
    ('この型式では見つかりませんでした。型式の書き方（ハイフン・末尾の英字）を変えるか、モジュールの販売元に技適番号を聞いてください。', 'Nothing found for this model. Try another spelling (hyphens, trailing letters) or ask the module seller for the certification number.', '未找到该型号。请尝试改变型号写法（连字符、末尾字母），或向模块销售商询问技适编号。'),
    ('型式・名称', 'Model / name', '型号・名称'), ('番号・日付', 'Number / date', '编号・日期'), ('取得した会社', 'Holder', '取得公司'),
    ('技適の有無の最終確認は、モジュールの販売元・工場と行ってください。製品の作り方（アンテナの変更など）によっては、追加の手続きが要ります。', 'Confirm the certification with the module seller and factory. Some design changes (such as a different antenna) need extra procedures.', '技适的最终确认请与模块销售商、工厂进行。根据产品的做法（如更换天线），可能需要额外手续。'),
    # 部品の参考価格（DigiKey）
    ('部品の参考価格を調べる（DigiKey）', 'Check reference part prices (DigiKey)', '查询零件参考价格（DigiKey）'),
    ('部品名か型番を入れると、電子部品の通販 DigiKey の単価（1個）と在庫を出します。量産の価格は工場の仕入れで変わるので、目安として使ってください。', 'Enter a part name or number to see the unit price (qty 1) and stock at the electronics distributor DigiKey. Mass-production prices depend on the factory\'s sourcing, so treat these as a guide.', '输入零件名称或型号，即可显示电子元件商城 DigiKey 的单价（1个）和库存。量产价格会因工厂采购而变化，请作为参考。'),
    ('部品名か型番を2文字以上入れてください', 'Enter at least 2 characters', '请输入至少2个字符的零件名称或型号'),
    ('いまは調べられませんでした。少し時間をおいてお試しください。', 'Could not check right now. Please try again later.', '暂时无法查询。请稍后再试。'),
    ('見つかりませんでした。英語の部品名や型番でお試しください。', 'Nothing found. Try an English part name or a part number.', '未找到。请尝试英文零件名称或型号。'),
    ('加速度センサー', 'Accelerometer', '加速度传感器'), ('心拍センサー', 'Heart-rate sensor', '心率传感器'), ('GPSモジュール', 'GPS module', 'GPS模块'),
    ('Bluetoothモジュール', 'Bluetooth module', '蓝牙模块'), ('Wi-Fiモジュール', 'Wi-Fi module', 'Wi-Fi模块'), ('温度センサー', 'Temperature sensor', '温度传感器'),
    ('振動モーター', 'Vibration motor', '振动马达'), ('マイコン', 'Microcontroller', '单片机'), ('充電IC', 'Charger IC', '充电IC'), ('ブザー', 'Buzzer', '蜂鸣器'),
    ('型番・メーカー', 'Part no. / maker', '型号・厂商'), ('説明', 'Description', '说明'), ('単価（1個）・在庫', 'Unit price (qty 1) / stock', '单价（1个）・库存'),
    ('質問', 'Question', '问题'),
    ('いくつでも選べます', 'Pick as many as apply', '可多选'),
    ('その他（自由に書く）', 'Other (type freely)', '其他（自由填写）'),
    ('次へ', 'Next', '下一步'),
    ('あとで', 'Later', '稍后'),
    ('直す', 'Edit', '修改'),
    ('選ぶか、書いてから「次へ」を押してください', 'Pick or type something, then press "Next".', '请先选择或填写，再按「下一步」。'),
]

def _j(x):
    return x[0] if isinstance(x, tuple) else x


def _ja(o):
    if isinstance(o, tuple):
        return o[0]
    if isinstance(o, list):
        return [_ja(x) for x in o]
    if isinstance(o, dict):
        return {k: _ja(v) for k, v in o.items()}
    return o


def data():
    """日本語だけの形（画面・MCP・貼り戻しで共有）"""
    return {'version': 1, 'unk': UNK[0], 'common': _ja(COMMON), 'cats': _ja(CATS),
            'levels': {'原文': 1, '回答': 1, '製品DB': 1, '参考品': 0.5, '仮': 0.5, '要確認': 0}}


def js():
    return json.dumps(data(), ensure_ascii=False, separators=(',', ':'))


def _pairs():
    out = [UNK]
    def walk(o):
        if isinstance(o, tuple) and len(o) == 3 and all(isinstance(s, str) for s in o):
            out.append(o)
        elif isinstance(o, list):
            for x in o: walk(x)
        elif isinstance(o, dict):
            for k, v in o.items():
                if k not in ('k', 'id', 'proc', 'ind', 're', 'sx'): walk(v)
    walk(COMMON); walk(CATS); out += UI
    return out


T_FSPEC = {ja: (en, zh) for ja, en, zh in _pairs()}

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(root + '/data', exist_ok=True)
    json.dump(data(), open(root + '/data/fspec.json', 'w'), ensure_ascii=False, indent=1)
    print('data/fspec.json', len(COMMON), 'common', len(CATS), 'cats', len(T_FSPEC), 'strings')
