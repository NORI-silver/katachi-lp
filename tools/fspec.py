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
# 「おまかせ」も答え（工場が提案する）。見積に要る6点は、わからない・おまかせでもそろったことにする
OMAKASE = ('おまかせ（工場の提案で）', 'Leave it to the factory', '交给工厂提议')

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
         multi=1, ch=[('金属', 'Metal', '金属'), ('樹脂（プラスチック）', 'Plastic', '树脂（塑料）'), ('木', 'Wood', '木材'), ('布・革', 'Fabric / leather', '布・皮革'),
                      ('紙', 'Paper', '纸'), ('ガラス・陶器', 'Glass / ceramic', '玻璃・陶瓷'), ('シリコーン・ゴム', 'Silicone / rubber', '硅胶・橡胶')],
         fq=('この用途に合う素材の候補と、素材による費用の違いを教えてください。', 'Which materials suit this use, and how do they change the cost?', '请告诉我们适合该用途的材质候选，以及不同材质的费用差异。')),
    dict(k='fin', t=('仕上げ（色・表面・ロゴ）', 'Finish (colour, surface, logo)', '表面处理（颜色・表面・标志）'), req=0, multi=1, sx='finish',
         q=('仕上げはどうしますか（いくつでも）', 'What finish? (choose any)', '表面怎么处理？（可多选）'),
         ch=[('そのまま（素材の色・素地）', 'As is (natural material)', '保持原样（材料本色）'), ('色を付ける（塗装・染め・着色）', 'Add colour (paint, dye)', '上色（喷涂・染色）'),
             ('ロゴ・文字を入れる（印刷・刻印・刺繍）', 'Add a logo or text (print, engrave, embroider)', '加标志・文字（印刷・刻印・刺绣）'), ('磨く・つやを出す', 'Polish / gloss', '抛光・上光')],
         fq=('この製品で一般的な仕上げ（色・表面・ロゴの入れ方）と、費用の違いを教えてください。', 'What finishes (colour, surface, logo) are usual for this product, and how do they change the cost?', '请告诉我们该产品常见的表面处理（颜色・表面・标志），以及费用差异。')),
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
             ('写真', 'Photos', '照片'), ('現物を送れる', 'A physical sample I can send', '可寄送实物'), ('ない', 'Nothing yet', '没有'),
             ('型紙・パターン', 'Sewing pattern', '纸样'), ('配合・レシピ', 'Formula / recipe', '配方'),
             ('入稿データ（ロゴ・デザイン）', 'Print-ready artwork (logo, design)', '印刷数据（标志、设计）')]),
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
    dict(k='dueflex', t=('納期の幅', 'Timing flexibility', '交期弹性'), req=0, sx='due_flex',
         q=('その時期は、どのくらいずらせますか', 'How flexible is that timing?', '这个时间可以调整多少？'),
         ch=[('この日までに必要（動かせない）', 'Needed by this date (fixed)', '必须在此日期前（不能调整）'), ('1か月ほど前後してもよい', 'About a month either way is fine', '前后1个月左右可以'),
             ('2〜3か月のうち、いつでもよい', 'Any time within 2–3 months', '2～3个月内任何时候都可以'), ('急がない（工場の空き時期でよい）', 'No rush (whenever the factory has capacity)', '不急（工厂空闲时即可）')],
         fq=('工場の空いている時期に合わせられます。安く・早く作れる時期があれば教えてください。', 'The timing is flexible. Let us know if there is a period when you can make it cheaper or sooner.', '时间可以配合工厂。如有能更便宜或更快制作的时期，请告诉我们。')),
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
                     ch=[('ある', 'Yes', '有'), ('ない', 'No', '没有')])
                ,dict(k='edata', t=('回路・基板の設計データ', 'Circuit / PCB design data', '电路・电路板设计数据'), key=0, q=('回路図・基板のデータ（ガーバー）・部品表はありますか', 'Do you have schematics, PCB data (Gerber) or a parts list (BOM)?', '有电路图、电路板数据（Gerber）或物料清单（BOM）吗？'),
                     ch=[('ある', 'Yes', '有'), ('一部ある', 'Some of it', '有一部分'), ('ない（設計から頼む）', 'No (design is needed)', '没有（从设计开始委托）')]),
                dict(k='psup', t=('部品の支給', 'Parts supply', '零部件供应'), key=0, q=('部品はどうしますか', 'Who supplies the parts?', '零部件怎么解决？'),
                     ch=[('工場に任せる', 'Factory sources them', '交给工厂'), ('一部こちらで用意する', 'We supply some', '部分由我方提供'), ('全部こちらで用意する', 'We supply all', '全部由我方提供')])],
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
                     ch=[('工場に任せる', 'Factory supplies it', '交给工厂'), ('こちらで用意する', 'We supply it', '我方提供')])
                ,dict(k='insp', t=('検査・成績書', 'Inspection report', '检验・检验报告'), key=0, q=('検査の書類は要りますか', 'Do you need inspection documents?', '需要检验文件吗？'),
                     ch=[('要らない', 'Not needed', '不需要'), ('寸法の検査表', 'Dimensional inspection report', '尺寸检验表'), ('材料の証明（ミルシート）も', 'Also material certificate (mill sheet)', '还需材料证明（材质证明书）')])],
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
                     fq=('この数なら、削り出し・3Dプリントと金型のどちらが安いですか。金型の費用と持ち主も教えてください。', 'At this quantity, is machining / 3D printing or a mould cheaper? What does the mould cost and who owns it?', '这个数量下，切削/3D打印和模具哪个便宜？也请告诉我们模具费用及归属。'))
                ,dict(k='look', t=('見える面の見た目', 'Appearance of visible faces', '外观面的外观要求'), key=0, q=('人に見える面の見た目はどのくらい大事ですか', 'How much does the look of visible faces matter?', '外露面的外观有多重要？'),
                     ch=[('見えない部品（見た目は問わない）', 'Hidden part (looks do not matter)', '内部零件（不在乎外观）'), ('見える面はきれいに（傷・跡なし）', 'Visible faces clean (no marks)', '外露面要干净（无划痕、痕迹）'), ('全体を製品の外観で', 'Whole part at product-grade look', '整体按产品外观要求')])],
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
                     ch=[('通販（EC）', 'Online', '网店'), ('ふるさと納税', 'Furusato nozei', '故乡纳税'), ('店舗', 'Shops', '店铺'), ('イベント', 'Events', '活动')])
                ,dict(k='fuse', t=('市販用か業務用か', 'Retail or professional use', '零售用还是业务用'), key=0, q=('売る商品ですか、お店で使う物ですか', 'Will it be sold, or used in your shop?', '是用于销售，还是店内使用？'),
                     ch=[('市販用（売る）', 'Retail (to sell)', '零售用（销售）'), ('業務用（お店・施設で使う）', 'Professional (used in a shop or facility)', '业务用（店铺、设施使用）'), ('両方', 'Both', '两者')]),
                dict(k='shelf', t=('賞味期限の目安', 'Target shelf life', '保质期参考'), key=0, q=('賞味期限はどのくらい欲しいですか', 'How long a shelf life do you need?', '希望保质期多长？'),
                     ch=[('〜1週間', 'Up to 1 week', '1周以内'), ('〜1か月', 'Up to 1 month', '1个月以内'), ('〜6か月', 'Up to 6 months', '6个月以内'), ('1年以上', '1 year or more', '1年以上')]),
                dict(k='fpack', t=('包装', 'Packaging', '包装'), key=0, multi=1, q=('どんな包装にしますか（いくつでも）', 'What packaging? (choose any)', '用什么包装？（可多选）'),
                     ch=[('袋', 'Bag / pouch', '袋'), ('箱', 'Box', '盒'), ('瓶・缶', 'Jar / can', '瓶・罐'), ('ボトル', 'Bottle', '瓶装'), ('個包装', 'Individually wrapped', '独立包装')])],
         asks=[('初回の最小ロット（kg・個・食）と、包装・表示（ラベル）まで頼めるかを教えてください。', 'What is the minimum first lot (kg / units / servings), and can you handle packaging and labelling?', '请告诉我们首批最小批量（kg・个・份），以及能否包办包装和标签。')]),
    dict(id='cosme', t=('化粧品', 'Cosmetics', '化妆品'), proc=['cosmetics'], ind=['cosme'],
         re=r'化粧品|コスメ|美容液|化粧水|クリーム|シャンプー|石けん|せっけん|ボディ',
         items=[dict(k='ctype', t=('品目', 'Product type', '品类'), key=1, q=('どの種類ですか', 'Which type?', '哪个品类？'),
                     ch=[('スキンケア', 'Skincare', '护肤'), ('ヘアケア', 'Haircare', '护发'), ('ボディケア', 'Body care', '身体护理'), ('メイク', 'Make-up', '彩妆')]),
                dict(k='vol', t=('容量', 'Volume', '容量'), key=1, q=('1本の容量はどのくらいですか', 'What volume per unit?', '每瓶容量多少？'),
                     ch=[('〜30mL', 'Up to 30 mL', '30mL以内'), ('〜100mL', 'Up to 100 mL', '100mL以内'), ('〜300mL', 'Up to 300 mL', '300mL以内'), ('それ以上', 'More', '更多')]),
                dict(k='box', t=('容器・箱', 'Container and box', '容器・包装盒'), key=0, q=('容器と箱はどうしますか', 'Container and box?', '容器和盒子怎么办？'),
                     ch=[('既製の容器でよい', 'Stock container is fine', '现成容器即可'), ('オリジナルの容器', 'Custom container', '定制容器'), ('箱も作る', 'Also make a box', '也做包装盒')])
                ,dict(k='cuse', t=('店販用か業務用か', 'Retail or professional use', '零售用还是业务用'), key=0, q=('お店で売る物ですか、施術などで使う物ですか', 'Will it be sold, or used in treatments?', '是用于销售，还是用于店内护理？'),
                     ch=[('店販用（売る）', 'Retail (to sell)', '零售用（销售）'), ('業務用（サロン・施設で使う）', 'Professional (salon / facility)', '业务用（沙龙、设施使用）'), ('両方', 'Both', '两者')]),
                dict(k='cref', t=('参考にしたい商品・入れたい成分', 'Reference product / key ingredients', '参考商品・希望成分'), key=0, multi=1, q=('参考にしたい商品や、入れたい成分はありますか（いくつでも）', 'Is there a product to model it on, or ingredients you want? (choose any)', '有想参考的商品或想添加的成分吗？（可多选）'),
                     ch=[('参考にしたい商品がある（依頼文に書く）', 'A reference product (written in the request)', '有参考商品（写在委托内容中）'), ('入れたい成分がある（依頼文に書く）', 'Key ingredients (written in the request)', '有希望添加的成分（写在委托内容中）'), ('どちらもない（提案してほしい）', 'Neither (please suggest)', '都没有（希望提议）')]),
                dict(k='csup', t=('容器・ラベルの支給', 'Supplying containers / labels', '容器・标签供应'), key=0, q=('容器やラベルを持ち込みますか', 'Will you supply containers or labels?', '是否自带容器或标签？'),
                     ch=[('工場に任せる', 'Factory sources them', '交给工厂'), ('容器を持ち込む', 'We supply containers', '自带容器'), ('ラベルを持ち込む', 'We supply labels', '自带标签')])],
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
                     ch=[('家庭', 'Home', '家庭'), ('店舗', 'Shop', '店铺'), ('施設', 'Facility', '设施'), ('子ども用', 'For children', '儿童用')])
                ,dict(k='carry', t=('搬入の経路', 'Delivery route', '搬入路线'), key=0, q=('置く場所まで、どう運び入れますか', 'How will it get to where it goes?', '怎么搬到放置位置？'),
                     ch=[('1階・入口は広い', 'Ground floor, wide entrance', '一楼・入口宽'), ('階段で運ぶ', 'By stairs', '走楼梯'), ('エレベーターで運ぶ', 'By lift', '坐电梯')],
                     fq=('搬入できる一番大きい部品の大きさと、分割が要るかを教えてください。', 'What is the largest piece that can be carried in, and does it need to be split?', '请告诉我们能搬入的最大部件尺寸，以及是否需要分体。')),
                dict(k='inst', t=('設置まで頼むか', 'Installation', '是否委托安装'), key=0, q=('設置まで頼みますか', 'Do you need it installed?', '需要安装吗？'),
                     ch=[('届けるだけでよい', 'Delivery only', '只需送达'), ('組み立て・設置まで', 'Assembly and placement', '组装・摆放'), ('壁・床への取り付け工事まで', 'Fixing to wall / floor', '包括墙面・地面固定施工')])],
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
                     ch=[('1種類', 'One', '1种'), ('2〜5種類', '2–5', '2～5种'), ('6種類以上', '6 or more', '6种以上')])
                ,dict(k='gdeco', t=('特殊な加工', 'Special finishing', '特殊加工'), key=0, multi=1, q=('特殊な加工はしますか（いくつでも）', 'Any special finishing? (choose any)', '需要特殊加工吗？（可多选）'),
                     ch=[('なし', 'None', '无'), ('箔押し', 'Foil stamping', '烫金'), ('エンボス', 'Embossing', '压纹'), ('窓あけ', 'Window cut-out', '开窗')]),
                dict(k='gwt', t=('中に入れる物の重さ（箱・袋）', 'Weight of contents (boxes / bags)', '内容物重量（盒・袋）'), key=0, q=('箱や袋なら、中に入れる物の重さは', 'For boxes or bags, how heavy are the contents?', '如果是盒子或袋子，内容物有多重？'),
                     ch=[('箱・袋ではない', 'Not a box or bag', '不是盒子或袋子'), ('〜100g', 'Up to 100 g', '100g以内'), ('〜1kg', 'Up to 1 kg', '1kg以内'), ('1kgより重い', 'Over 1 kg', '超过1kg')])],
         asks=[('種類ごとの最小数と、使う日（イベント日）に間に合う日程かを教えてください。', 'What is the minimum per design, and can you meet the event date?', '请告诉我们每款的最小数量，以及能否赶上使用日（活动日）。')]),
    # 大きな物・据え付け（台・スロープ・架台など）。重さがかかる・置く場所・設置まで頼むかで、作り方と見積が大きく変わる（Nori の実依頼で分かり、どの大型品にも効くので足した 2026-11-16）
    dict(id='struct', t=('大きな物・据え付け', 'Large / installed items', '大型・安装类'), proc=[], ind=[],
         re=r'スロープ|架台|台車|リフト|昇降|ステージ|手すり|手摺|柵|フェンス|小屋|ゲート|門扉|デッキ|乗る|乗せ|載せ|耐荷重|体重',
         items=[dict(k='load', t=('載せる重さ', 'Load it must carry', '承重'), key=1, q=('人・動物・物が乗りますか。重さはどのくらいですか', 'Will people, animals or things go on it? How heavy?', '会有人、动物或物品放在上面吗？多重？'),
                     ch=[('乗らない（重さはかからない）', 'Nothing goes on it', '不承重'), ('〜20kg', 'Up to 20 kg', '20kg以内'), ('〜100kg', 'Up to 100 kg', '100kg以内'), ('100kgより重い', 'Over 100 kg', '超过100kg')],
                     fq=('載せる重さと使い方（毎日使う・人や動物が乗るなど）から、必要な強さと安全の考え方を提案してください。', 'From the load and how it is used (daily use, people or animals on it), please propose the strength and safety approach.', '请根据承重和使用方式（每天使用、人或动物站上去等），提出所需强度和安全方面的方案。')),
                dict(k='where', t=('置く場所', 'Where it stands', '放置场所'), key=1, q=('どこに置きますか', 'Where will it stand?', '放在哪里？'),
                     ch=[('屋内', 'Indoors', '室内'), ('屋外（雨が当たる）', 'Outdoors (in the rain)', '室外（会淋雨）'), ('水の中・水まわり', 'In or near water', '水中・用水处')]),
                dict(k='inst', t=('据え付け・設置', 'Installation', '安装'), key=1, q=('設置まで頼みますか', 'Do you need it installed?', '需要安装吗？'),
                     ch=[('届けるだけでよい（自分で置く）', 'Delivery only (I will set it up)', '只需送达（自己摆放）'), ('組み立て・設置まで', 'Assembly and placement', '组装・摆放'), ('取り付け工事まで（壁・床・車など）', 'Fixing work (wall, floor, vehicle, etc.)', '包括固定施工（墙、地面、车辆等）')])],
         asks=[('大きさの上限（置く場所・運ぶ道・車に積めるか）と、分割して運ぶ必要があるかを教えてください。', 'What size limits apply (site, delivery route, vehicle), and does it need to be split for transport?', '请告诉我们尺寸上限（放置场所、搬运路线、能否装车），以及是否需要分体运输。')]),
]

# ---------------------------------------------------------------------------
# 工場に依頼するときの必要情報の定義表（Nori 2026-11-16「何が必要情報かを整理できてない」）
#   need: must    = 見積・受けるかの判断に要る。文章に無ければ②の前に1問ずつ聞く（わからない・おまかせも可）
#         factory = 工場が決めてよい（素人には決めにくい）。聞かずに「ご提案ください」として工場に渡す
#         nice    = あると見積が正確になる。聞かない。書いてあれば工場に渡し、無ければ依頼文に出さない
#   rx: 文章から読む言葉 [選択肢の番号, 正規表現]（multi の項目は当たった選択肢を全部）。rv: rx が当たらないとき、値をそのまま抜く正規表現
#   根拠: 比較ビズの公開案件 約250件（2026-11-14）、各社の見積フォーム13件と国内の工場780社の問い合わせフォーム（2026-11-15、
#   katachi-research/quote-form-items.md）。画面の読み取り（fsBuild）・質問（cqBox）・工場向けの依頼文（fsText）が全部この表で動く。
# ---------------------------------------------------------------------------
NEED = {
    # 共通
    # 共通の項目の多くは、template.html の fsBuild に専用の読み方がある（rd=1。数字・寸法・時期など、選択肢に当てるより抜き出すほうがよいもの）
    'name': dict(need='must', rd=1), 'purpose': dict(need='must', rd=1), 'size': dict(need='must', rd=1), 'mat': dict(need='must', rd=1),
    'fin': dict(need='factory', rd=1), 'parts': dict(need='nice', rd=1), 'scope': dict(need='must', rd=1), 'fit': dict(need='nice', rd=1),
    'docs': dict(need='must', rd=1), 'qs': dict(need='must', rd=1), 'qf': dict(need='must', rd=1), 'qc': dict(need='nice'),
    'due': dict(need='must', rd=1), 'dueflex': dict(need='nice', rd=1), 'budget': dict(need='nice', rd=1), 'sure': dict(need='nice'),
    'reg': dict(need='nice', rd=1), 'env': dict(need='nice', rd=1),
    # 電子・基板
    'escope': dict(need='factory', rx=[[0, r'回路(の)?設計'], [1, r'基板'], [2, r'ファーム|プログラム|ソフト'], [3, r'ケース|筐体|ハウジング'], [4, r'アプリ']]),
    'power': dict(need='must', rx=[[0, r'乾電池|単[1-4１-４]電池|ボタン電池|コイン電池'], [1, r'充電|バッテリー|リチウム|USB.?給電'], [2, r'コンセント|AC電源|100V|家庭用電源'], [0, r'電池']]),  # ただの「電池」は乾電池として読む（充電・コンセントが先に当たる）
    'comm': dict(need='must', rx=[[0, r'通信(は|を)?(使わない|不要|しない|なし)|オフライン|単体で動く'], [1, r'bluetooth|(?<![a-z])ble(?![a-z])|ブルートゥース|スマホ(と|に)(つな|連携|接続)'], [2, r'wi-?fi|無線LAN'], [3, r'(?<![a-z])lte(?![a-z])|(?<![a-z0-9])[45]g(?![a-z])|sim|携帯回線|セルラー'], [4, r'gps|位置情報|居場所']],
                 rv=r'スマホ(に|へ|で|から)[^。\n、]{0,8}?(知らせる|通知する|通知|知らせ|見られる|見る|確認する|確認|操作する|操作)|アプリで[^。\n、]{0,8}?(見る|確認|操作|通知)|遠隔で[^。\n、]{0,8}?(見る|確認|操作)'),  # 方式が書いていなければ、書いた言葉のまま渡す（方式は工場の提案）
    'have': dict(need='nice', rx=[[0, r'試作品(が|は)?(ある|あります|できて)|自作(した|の)|手作りの試作']]),
    'edata': dict(need='nice', rx=[[0, r'回路図|ガーバー|gerber|(?<![a-z])bom(?![a-z])|部品表']]),
    'psup': dict(need='nice', rx=[[1, r'部品(は|を)?(一部)?(支給|持ち込|用意します)']]),
    # 金属
    'grade': dict(need='factory', rx=[[0, r'ステンレス|sus\d*'], [1, r'アルミ|a5052|a6061'], [2, r'(?<![a-z])鉄|ss400|スチール']]),
    'tol': dict(need='factory', rx=[[1, r'公差|±\s*0[.．]\d|高精度']]),
    'surf': dict(need='factory', rx=[[0, r'無処理|素地のまま'], [1, r'アルマイト'], [2, r'塗装|粉体'], [3, r'メッキ|めっき'], [4, r'研磨|鏡面|ヘアライン']]),
    'supply': dict(need='nice', rx=[[1, r'材料(は|を)?(支給|持ち込|用意します)']]),
    'insp': dict(need='nice', rx=[[1, r'検査表|測定(結果|データ)'], [2, r'ミルシート|材料証明']]),
    # 樹脂
    'rgrade': dict(need='factory', rx=[[0, r'(?<![a-z])abs(?![a-z])'], [1, r'(?<![a-z])pp(?![a-z])|ポリプロピレン'], [2, r'(?<![a-z])pc(?![a-z])|ポリカ'], [3, r'アクリル|pmma'], [4, r'(?<![a-z])pom(?![a-z])|ジュラコン'], [5, r'シリコ']]),
    'color': dict(need='nice', rx=[[0, r'透明|クリア'], [2, r'多色|複数の色|カラフル|[2-9２-９]色']]),
    'finish': dict(need='factory', rx=[[1, r'塗装'], [2, r'メッキ|めっき'], [3, r'ロゴ|印刷|刻印']]),
    'method': dict(need='factory', rx=[[0, r'3d.?プリ|削り出し|切削'], [1, r'金型|射出成形']]),
    'look': dict(need='must', rx=[[0, r'内部(の)?部品|見えない(部品|ところ)|中に入る部品'], [2, r'外観部品|見た目(が|を)?(大事|重視|きれい)|高級感|商品の顔']]),
    # 布・縫製
    'fabric': dict(need='must', rx=[[0, r'綿|コットン'], [1, r'ポリエステル|ドライ素材'], [2, r'ナイロン'], [3, r'ウール'], [4, r'革|レザー']]),
    'weave': dict(need='factory', rx=[[0, r't\s*シャツ|ｔシャツ|ニット|スウェット|パーカー|ポロ'], [1, r'(?<![tｔ])(?<![tｔ]\s)シャツ|ブラウス|ジャケット|ワンピース']]),
    'sizes': dict(need='must', rx=[[0, r'フリーサイズ|ワンサイズ|1サイズ|１サイズ'], [1, r's\s*[・/〜~-]\s*m\s*[・/〜~-]\s*l(?![a-z])|3サイズ|３サイズ'], [2, r'(?<![a-z])xs(?![a-z])|xxl|(?<![0-9])[34]l(?![a-z])|[5-9]サイズ|s\s*[〜~-]\s*xl']]),
    'deco': dict(need='must', rx=[[0, r'無地|プリント(は)?なし'], [1, r'プリント|シルク|転写|印刷'], [2, r'刺繍|ししゅう']]),
    'tag': dict(need='nice', rx=[[1, r'下げ札'], [2, r'織りネーム|ネームタグ|ブランドタグ']]),
    'fsup': dict(need='nice', rx=[[1, r'生地(は|を)?(支給|持ち込|用意します)']]),
    # ペット
    'target': dict(need='must', rx=[[0, r'小型犬|チワワ|トイプードル|ダックス|ポメラニアン|(?<![0-9])[1-9]\s*kgの犬'], [1, r'中型犬|柴犬|コーギー|[12]\d\s*kgの犬'], [2, r'大型犬|ゴールデン|ラブラドール|セントバーナード|シェパード|ハスキー|(?:[3-9]\d|1\d\d)\s*kgの犬'], [3, r'猫|ねこ|ネコ']]),
    'psize': dict(need='nice', rx=[[0, r'1サイズ|ワンサイズ'], [1, r'サイズ展開|複数(の)?サイズ|s\s*[・/]\s*m\s*[・/]\s*l']]),
    'wash': dict(need='nice', rx=[[0, r'洗える|洗濯|丸洗い']]),
    'chew': dict(need='nice', rx=[[0, r'誤飲|かじ|噛']]),
    # 食品
    'recipe': dict(need='must', rx=[[0, r'レシピ(が|は)?(ある|あります|決まって)|自家製|配合(が|は)?(ある|決まって)|自分のレシピ|うちの味|店の味|今(売って|出して)いる'], [1, r'レシピ(が|は)?(ない|ありません)|レシピ(から|も)(作|考)|開発から|一緒に(作|考)']]),
    'form': dict(need='must', rx=[[0, r'常温'], [1, r'冷蔵|チルド'], [2, r'冷凍'], [3, r'レトルト'], [4, r'乾燥|粉末|パウダー|フリーズドライ|グラノーラ|クッキー|焼き菓子|せんべい']]),
    'raw': dict(need='nice', rx=[[0, r'原料(は|を)?(持ち込|支給|用意します)|(自家|うちの)(畑|農園)']]),
    'sales': dict(need='nice', rx=[[0, r'通販|(?<![a-z])ec(?![a-z])|ネット(で)?販売'], [1, r'ふるさと納税'], [2, r'店舗|お店で売|店頭|道の駅'], [3, r'イベント|マルシェ']]),
    'fuse': dict(need='nice', rx=[[0, r'販売|売る|売りたい|通販'], [1, r'業務用|店で使う|店舗で使う']]),
    'shelf': dict(need='nice'),
    'fpack': dict(need='nice', rx=[[0, r'袋|パウチ'], [1, r'(?<![a-z])箱'], [2, r'瓶|缶'], [3, r'ボトル'], [4, r'個包装|小分け']]),
    # 化粧品
    'ctype': dict(need='must', rx=[[0, r'化粧水|美容液|乳液|クリーム|洗顔|スキンケア|美容オイル|フェイス'], [1, r'シャンプー|トリートメント|ヘア'], [2, r'ボディ|石けん|せっけん|石鹸|ハンドクリーム'], [3, r'リップ|ファンデ|メイク|アイシャドウ|口紅']]),
    'vol': dict(need='must', rv=r'\d+(?:[.．]\d+)?\s*(?:ml|mL|ｍｌ|ミリリットル|g(?![a-z]))'),
    'box': dict(need='must', rx=[[0, r'既製(品)?(の)?容器|既存の容器|容器は(何でも|おまかせ)'], [1, r'オリジナル(の)?(容器|ボトル)|容器から'], [2, r'箱も|化粧箱']]),
    'cuse': dict(need='nice', rx=[[0, r'販売|売る|売りたい|店販'], [1, r'業務用|サロンで使|施術']]),
    'cref': dict(need='nice'), 'csup': dict(need='nice', rx=[[1, r'容器(は|を)?(支給|持ち込)'], [2, r'ラベル(は|を)?(支給|持ち込)']]),
    # 木工・家具
    'wood': dict(need='factory', rx=[[0, r'パイン'], [1, r'ナラ|オーク'], [2, r'ウォールナット'], [3, r'合板|ベニヤ']]),
    'paint': dict(need='factory', rx=[[0, r'無塗装'], [1, r'オイル(仕上げ)?'], [2, r'ウレタン'], [3, r'着色|ステイン']]),
    'kd': dict(need='nice', rx=[[0, r'組み立て式|組立式|ノックダウン'], [1, r'完成品(で|の)(納品|届)']]),
    'place': dict(need='must', rx=[[0, r'家庭|自宅|家で|リビング|部屋'], [1, r'店|カフェ|ショップ|サロン|売り場'], [2, r'施設|ホテル|病院|オフィス|学校|事務所'], [3, r'子ども|子供|キッズ']]),
    'carry': dict(need='nice', rx=[[1, r'階段'], [2, r'エレベーター']]),
    'inst': dict(need='must', rx=[[0, r'配送だけ|届けるだけ|自分で(置|組み立て|取り付け|設置)'], [1, r'組み立て(て|まで)|設置(して|まで)'], [2, r'取り付け工事|(壁|床|車)に(固定|取り付け|付けて)']]),  # 木工・家具と大きな物で共通
    # 雑貨・ノベルティ
    'colors': dict(need='must', rx=[[0, r'1色|１色|単色|一色'], [1, r'[23２３]色'], [2, r'フルカラー|カラー印刷|写真']]),
    'art': dict(need='must', rx=[[0, r'(デザイン|ロゴ|入稿)(の)?データ(が|は)?(ある|あります)|入稿|aiデータ|イラストレーター|デザインは(決まって|でき)'], [1, r'デザインから|デザイン(して|を作って|も頼|もお願い)']]),
    'indiv': dict(need='nice', rx=[[1, r'opp|個包装'], [2, r'台紙']]),
    'kinds': dict(need='nice', rx=[[0, r'1種類|１種類'], [1, r'[2-5２-５]種類'], [2, r'([6-9]|\d\d)種類']]),
    'gdeco': dict(need='factory', rx=[[1, r'箔押し|箔'], [2, r'エンボス'], [3, r'窓']]),
    'gwt': dict(need='nice'),
    # 大きな物・据え付け
    'load': dict(need='must', rv=r'(?:\d+(?:[.．]\d+)?\s*(?:kg|キロ))(?:[^。\n]{0,6}(?:犬|人|物|荷物))?', rx=[[0, r'(人|物|何も)(は|が)?乗らない|乗せない']]),
    'where': dict(need='must', rx=[[0, r'室内|屋内|店内|部屋'], [1, r'屋外|庭|ベランダ|外に置|雨'], [2, r'プール|水中|水辺|浴室|水まわり|水回り|川|海']]),
}


def _need():
    for d in COMMON + [i for c in CATS for i in c['items']]:
        o = NEED.get(d['k'])
        assert o, ('NEED に無い項目', d['k'])
        d.update(o)
        for n, _ in d.get('rx', []):
            assert 0 <= n < len(d.get('ch', [])), ('rx の番号が選択肢の外', d['k'], n)


_need()

# 画面の文言（日英中）
# 工場が見積を出すのに最低限要る6点（図面なしで聞く核）。keys のどれかがそろえばよい（all=1 は全部）。cat で品目ごとに置き換え、skip で外す
CORE = [
    dict(id='what', t=('何を作るか', 'What it is', '做什么'), keys=['name']),
    dict(id='qty', t=('数量', 'Quantity', '数量'), keys=['qf', 'qs']),
    dict(id='mat', t=('材料', 'Material', '材料'), keys=['mat'], cat={'food': ['recipe', 'mat'], 'cosme': ['ctype', 'mat']}),
    dict(id='size', t=('大きさ・形', 'Size and shape', '尺寸・形状'), keys=['size'], cat={'food': ['form', 'size'], 'cosme': ['vol', 'size']}),
    dict(id='fin', t=('仕上げ', 'Finish', '表面处理'), keys=['fin'], cat={'metal': ['fin', 'surf'], 'resin': ['fin', 'finish', 'color'], 'wood': ['fin', 'paint'], 'apparel': ['fin', 'deco'], 'goods': ['fin', 'colors'], 'cosme': ['box', 'fin']}, skip=['food']),
    dict(id='due', t=('納期', 'Timing', '交期'), keys=['due', 'dueflex'], all=1),
]

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
    ('形の要望', 'Shape requests', '形状需求'),
    ('図に足したい・変えたいところ', 'What to add or change in the drawing', '想在图中增加或修改的地方'),
    ('消す', 'Remove', '删除'),
    ('プールの中まで続ける', 'Continue into the pool', '延伸到泳池里'),
    ('2頭が並んで通れる幅にする', 'Wide enough for two dogs side by side', '加宽到两只狗能并排通过'),
    ('手すり・柵を付ける', 'Add rails or a fence', '加扶手或护栏'),
    ('滑り止めを付ける', 'Add anti-slip', '加防滑'),
    ('たためる・外せるようにする', 'Make it foldable or removable', '可折叠或可拆卸'),
    ('大きさを変える', 'Change the size', '改变尺寸'),
    ('角を丸くする', 'Round the corners', '把边角做圆'),
    ('部品を足す', 'Add a part', '增加零件'),
    ('分解できるようにする', 'Make it possible to take apart', '做成可拆分'),
    ('色・仕上げを変える', 'Change color or finish', '改变颜色或表面处理'),
    ('全体', 'Whole product', '整体'),
    ('足したい部品', 'Part to add', '想增加的零件'),
    ('例：スロープをプールの中まで続けて、水の中もゆるやかに下りたい', 'e.g. Continue the ramp into the pool so it slopes gently underwater too', '例：把坡道延伸到泳池里，水中也平缓向下'),
    ('足す', 'Add', '添加'),
    ('「プールの中まで続ける」は図にも出ます。ほかの要望は、仕様書と見積の依頼に入り、工場・設計者が図に起こします。', '"Continue into the pool" also shows in the drawing. Other requests go into the spec and quote request, and the factory or designer draws them.', '「延伸到泳池里」也会显示在图中。其他需求会写入规格书和报价委托，由工厂或设计师画成图。'),
    ('要望は図には自動で出ません。仕様書と見積の依頼に入り、工場・設計者が図に起こします。', 'Requests are not drawn automatically. They go into the spec and quote request, and the factory or designer draws them.', '需求不会自动画进图中。会写入规格书和报价委托，由工厂或设计师画成图。'),
    ('この3Dと寸法図は、見積の依頼にそのまま添付できます。', 'This 3D model and dimension drawing can be attached to your quote request as is.', '此3D和尺寸图可以直接附在报价委托中。'),
    ('この案の説明・素材・スペック', 'About this idea: materials and specs', '方案说明・材料・规格'),
    ('答えてください', 'Please answer', '请回答'),
    ('できました', 'Done', '完成'),
    ('✓ 質問はすべて答えました', '✓ All questions answered', '✓ 问题已全部回答'),
    ('答えは下の「工場向け仕様書」と見積の依頼に入ります。直すときは仕様書の表の「直す」から。', 'Your answers go into the factory spec below and the quote request. To change one, use "Edit" in the spec table.', '回答会写入下方的「面向工厂的规格书」和报价委托。要修改时，请点规格书表格中的「修改」。'),
    ('KATACHIの3D（STL）・寸法図（SVG）・仕様書を添付する', "Attach KATACHI's 3D (STL), dimension drawing (SVG) and spec", '附上KATACHI的3D（STL）、尺寸图（SVG）和规格书'),
    ('図面がなくても、工場がこの形をもとに見積・設計できます。どれも簡易なたたき台なので、工場から寸法・材質・作り方の確認や提案の連絡が来るのがふつうです。', 'Even without drawings, factories can quote and design from this shape. These are simple drafts, so expect the factory to contact you to confirm or suggest sizes, materials and methods.', '即使没有图纸，工厂也能据此形状报价和设计。这些都是简易草案，工厂通常会联系你确认或建议尺寸、材料和做法。'),
    ('上の質問に答えると、工場が見積に使える情報がそろいます。わからない所は「わからない」で大丈夫です。', 'Answer the questions above to give factories what they need for a quote. "I don\'t know" is fine.', '回答上面的问题，即可备齐工厂报价所需的信息。不清楚的可以选「不清楚」。'),
    ('図を見ながら直す', 'Edit while looking at the drawing', '边看图边修改'),
    ('例：幅を80cmに／もっとゆるやかに／プールの中にも続けて', 'e.g. Make the width 80cm / gentler slope / continue into the pool', '例：宽度改为80cm／坡度更缓／延伸到泳池里'),
    ('図に反映', 'Apply to drawing', '反映到图中'),
    ('プールの中にも続けて', 'Continue into the pool too', '也延伸到泳池里'),
    ('幅を80cmに', 'Width 80cm', '宽度改为80cm'),
    ('もっとゆるやかに', 'Gentler slope', '坡度更缓'),
    ('高さを70cmに', 'Height 70cm', '高度改为70cm'),
    ('手すりを付けて', 'Add rails', '加扶手'),
    ('幅を30cmに', 'Width 30cm', '宽度改为30cm'),
    ('高さを少し低く', 'A little lower', '稍微降低高度'),
    ('全体を2割大きく', '20% bigger overall', '整体放大20%'),
    ('幅', 'Width', '宽'),
    ('長さ', 'Length', '长'),
    ('高さ', 'Height', '高'),
    ('傾き', 'Slope', '坡度'),
    ('手すり', 'Rails', '扶手'),
    ('図に反映したこと', 'Applied to the drawing', '已反映到图中'),
    ('ひとつ戻す', 'Undo', '撤销一步'),
    ('図には出ない要望（工場に伝えます）', 'Requests not in the drawing (passed to the factory)', '图中未体现的需求（会转达给工厂）'),
    ('図は簡易なたたき台です。寸法・材質・作り方は、工場から確認や提案の連絡が来るのがふつうです。', 'The drawing is a simple draft. Expect the factory to contact you to confirm or suggest sizes, materials and methods.', '此图只是简易草案。工厂通常会联系你确认或建议尺寸、材料和做法。'),
    ('読み取れませんでした。どこのことですか？', 'Could not read that. Which part do you mean?', '无法识别。指的是哪里？'),
    ('図には出さず、要望として工場に伝える', 'Pass it to the factory as a request (not drawn)', '不画进图中，作为需求转达给工厂'),
    ('「傾き15度」のように書いてください。', 'Write it like "slope 15 degrees".', '请写成「坡度15度」这样的形式。'),
    ('下の数字を直すと、図に反映します。', 'Change the numbers below to update the drawing.', '修改下方数字即可反映到图中。'),
    ('✓ 要望として仕様書に入れました。工場・設計者が図に起こします。', '✓ Added to the spec as a request. The factory or designer will draw it.', '✓ 已作为需求写入规格书。由工厂或设计师画成图。'),
    ('いまの図と同じです。', 'That is the same as the current drawing.', '与当前的图相同。'),
    ('ひとつ前に戻しました。', 'Undid the last change.', '已撤销上一步。'),
    ('上の図と、下の答えから作ります', 'Built from the drawing above and your answers below', '根据上方的图和下方的回答生成'),
    ('図で決めた形', 'Shape decided on the drawing', '在图中确定的形状'),
    ('イメージ図', 'Drawing', '示意图'),
    ('仕様書から', 'From the spec:', '来自规格书：'),
    ('仮：似た製品の目安。数字を直すと図も変わります', 'Provisional: typical for similar products. Changing the numbers updates the drawing.', '暂定：类似产品的参考值。修改数字图也会改变'),
    ('答えは下の仕様書の表と見積の依頼に入ります。直すときは表の「直す」から。', 'Your answers go into the spec table below and the quote request. To change one, use "Edit" in the table.', '回答会写入下方的规格书表格和报价委托。要修改时，请点表格中的「修改」。'),
    ('✓ 図には描けない内容なので、要望として仕様書に入れました。工場・設計者が図に起こします。', '✓ This cannot be drawn, so it was added to the spec as a request. The factory or designer will draw it.', '✓ 此内容无法画进图中，已作为需求写入规格书。由工厂或设计师画成图。'),
    ('プールの中は階段に', 'Stairs inside the pool', '泳池内做成台阶'),
    ('外側も階段に', 'Stairs outside too', '外侧也做成台阶'),
    ('外側', 'Outside', '外侧'),
    ('プールの中', 'Inside the pool', '泳池内'),
    ('スロープ', 'Ramp', '坡道'),
    ('階段', 'Stairs', '台阶'),
    ('1段の高さ', 'Step height', '每级高度'),
    ('踏み面', 'Tread', '踏面'),
    ('段', 'steps', '级'),
    ('AIと相談して直す', 'Edit with your AI', '与AI商量修改'),
    ('上の欄の要望といまの図を、お使いのAIに渡して開きます。AIの答えの最後にある「KATACHIで開く」を押すと、ここに戻って図と仕様書が変わります（無料）。', 'Opens your AI with your request above and the current drawing. Press "Open in KATACHI" at the end of the AI\'s answer to come back here and update the drawing and spec (free).', '将上方的需求和当前的图交给你使用的AI并打开。点AI回答末尾的「在KATACHI中打开」，即可回到这里更新图和规格书（免费）。'),
    ('ChatGPTで直す', 'Edit with ChatGPT', '用ChatGPT修改'),
    ('Claudeで直す', 'Edit with Claude', '用Claude修改'),
    ('Geminiで直す', 'Edit with Gemini', '用Gemini修改'),
    ('AIの答えを貼る（リンクが開けなかったとき）', "Paste the AI's answer (if the link did not open)", '粘贴AI的回答（链接打不开时）'),
    ('AIの答え（KATACHIで開くリンクを含む）を貼り付け', "Paste the AI's answer (including the Open in KATACHI link)", '粘贴AI的回答（包含在KATACHI中打开的链接）'),
    ('図に入れる', 'Apply to drawing', '放入图中'),
    ('AIの答えから', "From the AI's answer:", '来自AI的回答：'),
    ('読めなかった・範囲外のため入れなかった値：', 'Values skipped (unreadable or out of range):', '无法识别或超出范围而未采用的值：'),
    ('AIの図の変更を受け取りました。', 'Received drawing changes from your AI.', '已收到AI的图修改。'),
    ('AIからの図の変更を受け取りました。', 'Received drawing changes from your AI.', '已收到AI的图修改。'),
    ('ただ、この端末・ブラウザには元の相談が残っていませんでした。AIへ行く前と同じブラウザで開くか、作りたいものを書き直して進んでください。AIの変更は、次の画面の図に入れます。', "But your earlier session is not on this device or browser. Open the link in the same browser you used before, or write what you want to make again and continue. The AI's changes will be applied to the drawing on the next screen.", '但此设备或浏览器中没有之前的内容。请用去AI之前的同一浏览器打开，或重新填写想做的东西后继续。AI的修改会放入下一画面的图中。'),
    ('KATACHIのリンク（kz=…）が見つかりませんでした。', 'No KATACHI link (kz=…) was found.', '未找到KATACHI的链接（kz=…）。'),
    ('リンクの中に、読み取れる数値がありませんでした。', 'The link had no readable values.', '链接中没有可识别的数值。'),
    ('AIに「KATACHIで開くリンクを、決まった形でもう一度出して」と頼んでください。', 'Ask your AI: "Give me the Open in KATACHI link again in the required format."', '请让AI「按规定格式再给一次在KATACHI中打开的链接」。'),
    ('を開きました。', 'opened.', '已打开。'),
    ('質問文をコピーしたので、貼り付けて送ってください。', 'The prompt is copied. Paste it and send.', '已复制提问文本，请粘贴后发送。'),
    ('質問文が入っていないときは、貼り付けて送ってください（コピー済み）。', 'If the prompt is not filled in, paste it and send (already copied).', '如果没有自动填入提问文本，请粘贴后发送（已复制）。'),
    ('AIの答えの最後にある「KATACHIで開く」を押すと、ここに戻ります。', 'Press "Open in KATACHI" at the end of the AI\'s answer to come back here.', '点AI回答末尾的「在KATACHI中打开」即可回到这里。'),
    ('変更なし', 'No change', '无变化'),
    ('見積に要る点', 'Needed for a quote', '报价所需项目'),
    ('見積に必要な質問', 'Questions needed for a quote', '报价所需的问题'),
    ('あと', 'left:', '还剩'),
    ('任意', 'Optional', '可选'),
    ('✓ 見積に要る点がそろいました。ここからは任意です。', '✓ Everything needed for a quote is in. The rest is optional.', '✓ 报价所需项目已齐全。以下为可选。'),
    ('おまかせ（工場の提案で）', 'Leave it to the factory', '交给工厂提议'),
    ('だいたいで大丈夫です。迷ったら近いものを選んでください。', 'A rough answer is fine. If unsure, pick the closest one.', '大概即可。拿不准时请选最接近的。'),
    ('似た製品の目安：', 'Typical for similar products:', '类似产品的参考：'),
    ('工場が見積に要る点はそろいました。図面や3Dデータがないため、工場はまず設計（仕様を決める仕事）の費用を見積もります。この仕様書を設計の依頼書として送ります。', 'Everything needed for a quote is in. Without drawings or 3D data, the factory will first quote for design work. This spec sheet goes as the design request.', '报价所需项目已齐全。由于没有图纸或3D数据，工厂会先报设计（确定规格的工作）费用。本规格书将作为设计委托书发送。'),
    ('工場が見積に要る点がそろいました。この仕様書を見積の依頼に付けて送れます。ほかの質問は任意です（答えると見積が正確になります）。', 'Everything needed for a quote is in. You can attach this spec sheet to your request. Other questions are optional (answering makes the quote more accurate).', '报价所需项目已齐全。可将本规格书附在委托中发送。其他问题为可选（回答后报价更准确）。'),
    ('工場が見積を出すのに要る点のうち、', 'Still missing for a factory quote: ', '工厂报价所需项目中，'),
    ('がまだです。', ' ', '尚未填写。'),
    ('材料・仕上げは「おまかせ」でも大丈夫です（工場が提案します）。', 'For material and finish, "Leave it to the factory" is fine (they will propose).', '材料・表面处理可以选「交给工厂提议」（工厂会提出建议）。'),
    ('だいたいで大丈夫です。', 'A rough answer is fine.', '大概即可。'),
    ('工場が見積に要ること', 'What the factory needs for a quote', '工厂报价所需'),
    ('大きさ・形（だいたいで大丈夫）', 'Size and shape (rough is fine)', '尺寸・形状（大概即可）'),
    ('例：幅30×奥行20×高さ10cmくらい、手のひらサイズ', 'e.g. about 30 × 20 × 10 cm, palm-sized', '例：宽30×深20×高10cm左右、手掌大小'),
    ('目安：', 'Typical: ', '参考：'),
    ('必須は、工場が見積を出すのに要る点と連絡先だけです。材料・仕上げは「おまかせ」でも大丈夫です（工場が提案します）。ほかは空けておけば「相談したい」として届きます。', 'Only what the factory needs for a quote and your contact are required. For material and finish, "Leave it to the factory" is fine. Anything left blank is sent as "want to discuss".', '必填的只有工厂报价所需项目和联系方式。材料・表面处理可以选「交给工厂提议」。其他留空则以「希望商量」发送。'),
    ('工場が見積に要る点', 'Needed for a factory quote', '工厂报价所需项目'),
    ('この点がそろうと、工場は見積を出せます。材料・仕上げがわからなければ「おまかせ」を選ぶと、工場が提案します。', 'With these, the factory can quote. If you are unsure of material or finish, choose "Leave it to the factory" and they will propose.', '这些齐全后工厂即可报价。不清楚材料或表面处理时，选「交给工厂提议」，工厂会提出建议。'),
    ('材料', 'Material', '材料'),
    ('大きさ・形', 'Size and shape', '尺寸・形状'),
    ('仕上げ', 'Finish', '表面处理'),
    ('納期', 'Timing', '交期'),
    ('納期の幅', 'Timing flexibility', '交期弹性'),
    ('何を作るか', 'What it is', '做什么'),
    ('数量', 'Quantity', '数量'),
    ('段階と数量', 'Stage and quantity', '阶段与数量'),
    ('希望の時期', 'When you need it', '希望时间'),
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
    return {'version': 1, 'unk': UNK[0], 'omakase': OMAKASE[0], 'core': _ja(CORE), 'common': _ja(COMMON), 'cats': _ja(CATS),
            'levels': {'原文': 1, '回答': 1, '製品DB': 1, '参考品': 0.5, '仮': 0.5, '要確認': 0}}


def js():
    return json.dumps(data(), ensure_ascii=False, separators=(',', ':'))


def _pairs():
    out = [UNK, OMAKASE]
    def walk(o):
        if isinstance(o, tuple) and len(o) == 3 and all(isinstance(s, str) for s in o):
            out.append(o)
        elif isinstance(o, list):
            for x in o: walk(x)
        elif isinstance(o, dict):
            for k, v in o.items():
                if k not in ('k', 'id', 'proc', 'ind', 're', 'sx', 'keys', 'cat', 'skip', 'need', 'rx', 'rv', 'rd'): walk(v)
    walk(COMMON); walk(CATS); walk(CORE); out += UI
    return out


T_FSPEC = {ja: (en, zh) for ja, en, zh in _pairs()}

def md():
    """必要情報の一覧（docs/factory-request-items.md）。定義表から作るので、手で直さない"""
    L = ['# 工場に依頼するときの必要情報（定義表 `tools/fspec.py` から自動で作る）', '',
         '画面の読み取り（文章から読む）・②の前の質問（1問ずつ、多くても6問）・工場に届く依頼の要点は、すべてこの表で動く。',
         '- **必須**：見積・受けるかの判断に要る。文章に無ければ聞く（「わからない」も可。そのときは工場に「まだ決まっていない点」として渡す）',
         '- **工場に任せる**：素人には決めにくい。聞かずに「ご提案ください」として工場に渡す',
         '- **あると良い**：聞かない。書いてあれば工場に渡し、無ければ依頼文に出さない', '',
         '根拠：比較ビズの公開案件 約250件（2026-11-14）、各社の見積フォーム13件と国内の工場780社の問い合わせフォーム（2026-11-15、`katachi-research/quote-form-items.md`）。', '']
    lab = {'must': '必須', 'factory': '工場に任せる', 'nice': 'あると良い'}
    def rows(items):
        out = ['| 項目 | 区分 | 文章から読むか | 選択肢 |', '|---|---|---|---|']
        for d in items:
            how = '読む' if d.get('rx') or d.get('rv') or d.get('rd') else ''
            out.append('| %s | %s | %s | %s |' % (_j(d['t']), lab[d['need']], how, ' / '.join(_j(c) for c in d.get('ch', [])) or '（自由に書く）'))
        return out
    L += ['## どの製品でも共通', ''] + rows(COMMON) + ['']
    L += ['見積に最低限要る6点（工場が見積を出すのに要る核）：' + '、'.join(_j(c['t']) for c in CORE) + '（食品は配合・形態、化粧品は品目・容量・容器に置き換え）', '']
    for c in CATS:
        L += ['## ' + _j(c['t']), ''] + rows(c['items'])
        if c.get('asks'):
            L += ['', '工場に必ず聞くこと：'] + ['- ' + _j(a) for a in c['asks']]
        L.append('')
    return '\n'.join(L)


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(root + '/data', exist_ok=True)
    json.dump(data(), open(root + '/data/fspec.json', 'w'), ensure_ascii=False, indent=1)
    os.makedirs(root + '/docs', exist_ok=True)
    open(root + '/docs/factory-request-items.md', 'w').write(md())
    print('data/fspec.json', len(COMMON), 'common', len(CATS), 'cats', len(T_FSPEC), 'strings')
