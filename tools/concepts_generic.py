"""製品イメージ案の「汎用ロジック」用のデータ（concepts.py の典型例に当たらない入力でも、必ず案を出す）。

画面側（template.html の genConcept）が、
  1. 文章の「形の言葉」（スロープ・台・箱・カバー…）から SHAPES を1つ選ぶ（どれにも当たらなければ product）
  2. 文章から読める条件 CONDS（水まわり・プール・ペット・揺れない・折りたたみ・子ども…）を全部拾う
  3. 乗る重さ（80kg など）・寸法（高さ76cm など）・犬の大きさを数字で読む
を組み合わせて、図・寸法・素材・機能・試作で確かめることを組み立てる。条件は典型例（concepts.py）の案にも足す。
文言は (日本語, 英語, 中国語)。数字は画面で組み立てる（日本語を含めないので翻訳の対象外）。
"""

# 寸法・重さの部品（画面で「幅」「約」「60cm」のように小さな部品を並べ、部品ごとに翻訳する）
WORDS = [
    ("幅", "W", "宽"), ("長さ", "L", "长"), ("高さ", "H", "高"), ("奥行", "D", "深"), ("約", "approx. ", "约"),
    ("乗る重さ", "Load", "承重"), ("設計の目安", "Design load", "设计参考"), ("（安全率2倍）", "(2× safety factor)", "（安全系数2倍）"),
    ("傾き", "Incline", "坡度"), ("本体の重さ", "Weight", "本体重量"),
    ("あなたの文章から読み取った条件", "Conditions read from your text", "从您的描述中读取的条件"),
    ("文章から組み立てた案", "Built from your text", "根据描述组合的方案"),
    ("高さは、お使いのものに合わせて測ってください（図は例）。", "Measure the height on your own item (the drawing is an example).", "高度请按您实际使用的物品测量（图为示例）。"),
]

SHAPES = [
  dict(id='slope', kw=r'スロープ|坂道|傾斜板|渡り板|ramp|slope',
    fig='slope', dims=(500, 1900, 760), scale='load',
    name=("スロープ（傾斜のある通り道）", "Ramp (sloped walkway)", "坡道（带坡度的通道）"),
    lead=("段差の上と下を、ゆるい坂でつなぐ通り道です。乗る重さ・高さ・傾きから、幅と長さ、骨組みの太さが決まります。",
          "A walkway that links a higher and lower level with a gentle incline. Load, height and angle decide the width, length and frame size.",
          "用缓坡连接高低两处的通道。承重、高度和坡度决定宽度、长度和骨架粗细。"),
    mat=("骨組み：アルミの角パイプまたは鋼（塗装）／踏み面：合板・樹脂板に滑り止め／脚：ゴム足", "Frame: aluminium square tube or painted steel · Deck: plywood or plastic board with anti-slip surface · Feet: rubber", "骨架：铝方管或钢（涂装）／踏面：胶合板・树脂板加防滑面／脚：橡胶脚垫"),
    matw=("骨組み：アルミの角パイプ（さびにくい）／踏み面：樹脂板（HDPE）またはFRP、表面にゴムマットや人工芝／脚：ゴム足・ステンレスの金具", "Frame: aluminium square tube (rust-resistant) · Deck: HDPE plastic board or FRP, topped with rubber matting or artificial turf · Feet: rubber, stainless fittings", "骨架：铝方管（不易生锈）／踏面：HDPE 树脂板或玻璃钢（FRP），表面铺橡胶垫或人工草皮／脚：橡胶脚垫・不锈钢配件"),
    feats=[("滑りにくい踏み面（溝・ゴム・人工芝）", "Non-slip deck (grooves, rubber or artificial turf)", "防滑踏面（凹槽・橡胶・人工草皮）"),
           ("横から落ちないための縁", "Side edges so nothing falls off", "防止从侧面掉落的边缘"),
           ("上の端・下の端がずれない固定（フック・ゴム足）", "Top and bottom ends that do not slip (hooks, rubber feet)", "上下两端不会移位的固定（挂钩・橡胶脚）")],
    check=[("最大の重さを乗せたときのたわみと揺れ", "Deflection and wobble at the maximum load", "最大载重时的弯曲和晃动"),
           ("濡れたときの滑りにくさ", "Grip when wet", "沾湿时的防滑性"),
           ("上り下りしやすい傾き（急すぎないか）", "An incline that is easy to walk (not too steep)", "上下是否方便的坡度（是否太陡）")],
    vars=[(("A. 一体型", "A. One piece", "A. 一体式"), ("丈夫で揺れにくい。置きっぱなしにする場所向け", "Strong and stable. For places where it stays put", "结实不易晃动。适合长期放置的地方")),
          (("B. 折りたたみ型", "B. Folding", "B. 折叠式"), ("しまえて運べる。ちょうつがいの強さと揺れの確認が要る", "Can be stored and carried. Hinge strength and wobble need checking", "可收纳搬运。需要确认铰链强度和晃动")),
          (("C. 階段＋スロープ", "C. Steps + ramp", "C. 台阶＋坡道"), ("長さを短くできる。足の短い動物や高齢者には坂だけの方が楽", "Shorter overall. For short-legged animals or older people, a ramp alone is easier", "可以缩短长度。对腿短的动物或老人，只用坡道更轻松"))],
    proto=("アルミの角パイプと板を切って組み、1台作って実際に乗せて確かめる", "Cut and assemble aluminium tube and board into one unit, then test it with the real load", "用铝方管和板材切割组装做1台，实际承重测试"),
    mass=("アルミの押出し材と曲げ・溶接、踏み面は樹脂板の切削や成形。数十台から", "Aluminium extrusions with bending and welding; deck by machining or moulding plastic board. From a few dozen units", "铝型材加折弯・焊接，踏面用树脂板切削或成型。几十台起")),

  dict(id='step', kw=r'ステップ|踏み台|ふみ台|階段|はしご|梯子|脚立|step|stairs|ladder',
    fig='step', dims=(450, 600, 450), scale='load',
    name=("ステップ（踏み台・階段）", "Step / small stairs", "踏台・台阶"),
    lead=("段差を2〜4段に分けて上り下りしやすくする台です。1段の高さと奥行、乗る重さで、形と骨組みが決まります。",
          "A unit that splits a height into 2–4 steps so it is easy to go up and down. Step height, depth and load decide the shape and frame.",
          "把高度分成2–4级、方便上下的台子。每级高度、深度和承重决定形状和骨架。"),
    mat=("骨組み：アルミまたは鋼の板金／踏み面：滑り止めの樹脂やゴム", "Frame: aluminium or steel sheet metal · Treads: anti-slip plastic or rubber", "骨架：铝或钢钣金／踏面：防滑树脂或橡胶"),
    matw=("骨組み：アルミ・ステンレス（さびにくい）／踏み面：樹脂（HDPE）に滑り止め", "Frame: aluminium or stainless (rust-resistant) · Treads: HDPE plastic with anti-slip surface", "骨架：铝・不锈钢（不易生锈）／踏面：HDPE 树脂加防滑"),
    feats=[("1段の高さをそろえる（つまずきにくい）", "Even step heights (less tripping)", "每级高度一致（不易绊倒）"),
           ("滑りにくい踏み面", "Non-slip treads", "防滑踏面"),
           ("床を傷つけないゴム足", "Rubber feet that protect the floor", "不伤地面的橡胶脚垫")],
    check=[("最大の重さを乗せたときの揺れ", "Wobble at the maximum load", "最大载重时的晃动"),
           ("1段の高さが使う人・動物に合うか", "Whether the step height suits the user or animal", "每级高度是否适合使用者或动物")],
    vars=[(("A. 固定型", "A. Fixed", "A. 固定式"), ("丈夫で揺れにくい", "Strong and stable", "结实不易晃动")),
          (("B. 折りたたみ型", "B. Folding", "B. 折叠式"), ("しまえるが、ロックの確かさが要る", "Stores away, but needs a reliable lock", "可收纳，但需要可靠的锁定"))],
    proto=("板金または木で1台作り、実際に上り下りして確かめる", "Make one in sheet metal or wood and test going up and down", "用钣金或木材做1台，实际上下测试"),
    mass=("板金の曲げ・溶接、または樹脂の成形。数十台から", "Sheet-metal bending and welding, or plastic moulding. From a few dozen units", "钣金折弯・焊接，或树脂成型。几十台起")),

  dict(id='house', kw=r'ハウス|小屋|ケージ|キャリー|ケンネル|サークル|クレート|巣箱|kennel|cage|crate|carrier',
    fig='house', dims=(600, 800, 650), scale='pet',
    name=("ハウス・ケージ（中に入るもの）", "House / cage / crate", "小屋・笼子"),
    lead=("動物や物が中に入る囲いです。中で立って向きを変えられる大きさと、出入り口・換気・掃除のしやすさが決め手になります。",
          "An enclosure that an animal or object goes inside. Room to stand and turn around, plus the door, ventilation and easy cleaning, are what matter.",
          "让动物或物品进入的围合空间。能在里面站立转身的大小，以及出入口、通风、方便清洁是关键。"),
    mat=("骨組み：鋼線・アルミ・木／屋根と壁：樹脂板・木／床：取り外せるトレー", "Frame: steel wire, aluminium or wood · Roof and walls: plastic board or wood · Floor: removable tray", "骨架：钢丝・铝・木／屋顶和墙：树脂板・木／底部：可拆卸托盘"),
    matw=("骨組み：アルミ・ステンレス／屋根と壁：樹脂（PP・HDPE）／床：水が抜けるすのこ", "Frame: aluminium or stainless · Roof and walls: PP or HDPE plastic · Floor: draining slats", "骨架：铝・不锈钢／屋顶和墙：PP・HDPE 树脂／底部：可排水的格栅"),
    feats=[("出入り口の扉と鍵", "Door with a latch", "带锁的门"), ("風が通る窓・すき間", "Windows or gaps for airflow", "通风的窗口・缝隙"),
           ("掃除しやすい取り外せる床", "Removable floor for easy cleaning", "便于清洁的可拆卸底板")],
    check=[("中で向きを変えられる大きさか", "Enough room to turn around inside", "里面是否能转身"),
           ("暑さ・寒さ・雨への強さ", "Resistance to heat, cold and rain", "耐热・耐寒・防雨性能"),
           ("かじられても壊れないか", "Whether it survives chewing", "被啃咬是否会坏")],
    vars=[(("A. 組み立て式", "A. Flat-pack", "A. 组装式"), ("送料が安く、しまえる", "Cheaper shipping, can be stored", "运费低，可收纳")),
          (("B. 一体型", "B. One piece", "B. 一体式"), ("丈夫で、すき間ができにくい", "Strong, with fewer gaps", "结实，不易出现缝隙"))],
    proto=("木や板金で1台作り、実際に入ってもらって確かめる", "Make one from wood or sheet metal and test it with the real occupant", "用木材或钣金做1台，实际让动物进去测试"),
    mass=("板金・線材の溶接、または樹脂の成形。数十〜数百台から", "Welded sheet metal and wire, or plastic moulding. From tens to hundreds of units", "钣金・线材焊接，或树脂成型。几十到几百台起")),

  dict(id='fence', kw=r'柵|フェンス|ゲート|仕切り|パーテーション|パーティション|囲い|fence|gate|partition',
    fig='fence', dims=(1200, 50, 900), scale=None,
    name=("柵・ゲート・仕切り", "Fence / gate / partition", "围栏・门・隔断"),
    lead=("場所を区切ったり、出入りを止めたりするパネルです。高さ・すき間の幅・倒れにくさ・開け閉めのしやすさを決めます。",
          "Panels that divide a space or stop passage. Decide the height, gap width, resistance to tipping and how easily it opens.",
          "用于分隔空间或阻止出入的面板。需要确定高度、缝隙宽度、防倾倒性能和开关是否方便。"),
    mat=("枠：スチール（粉体塗装）またはアルミ／面：格子・パネル・メッシュ", "Frame: powder-coated steel or aluminium · Infill: bars, panels or mesh", "框架：钢（粉末喷涂）或铝／面：格栅・面板・网"),
    matw=("枠：アルミ・ステンレス（さびにくい）／面：樹脂パネル・メッシュ", "Frame: aluminium or stainless (rust-resistant) · Infill: plastic panels or mesh", "框架：铝・不锈钢（不易生锈）／面：树脂板・网"),
    feats=[("倒れにくい脚、または壁への固定", "Stable feet or wall fixing", "防倒的支脚或固定在墙上"), ("開け閉めできる扉とロック", "Opening door with a lock", "可开关的门和锁"),
           ("指や頭が挟まらないすき間の幅", "Gaps sized so fingers and heads cannot get stuck", "不会卡住手指或头部的缝隙宽度")],
    check=[("押したり飛びついたりしたときに倒れないか", "Whether it stays up when pushed or jumped on", "被推或扑上来时是否会倒"), ("すき間の幅が安全か", "Whether the gap width is safe", "缝隙宽度是否安全")],
    vars=[(("A. 置くだけ", "A. Freestanding", "A. 直接摆放"), ("工事不要。重さや脚の広さで倒れにくくする", "No installation; stability from weight and wide feet", "无需施工。靠重量和宽脚防倒")),
          (("B. 固定式", "B. Fixed", "B. 固定式"), ("壁・床に留める。いちばん丈夫", "Fixed to wall or floor. The strongest option", "固定在墙或地面。最结实"))],
    proto=("1枚分を作り、押す・飛びつく力で確かめる", "Make one panel and test it with pushing and jumping loads", "做1片，用推力和扑力测试"),
    mass=("パイプの曲げ・溶接と塗装。数十枚から", "Tube bending, welding and painting. From a few dozen panels", "管材折弯・焊接和涂装。几十片起")),

  dict(id='bed', kw=r'ベッド|クッション|マットレス|座布団|寝床|ソファ|bed|cushion',
    fig='bed', dims=(900, 700, 200), scale='pet',
    name=("ベッド・クッション", "Bed / cushion", "床・垫子"),
    lead=("体を預けて休む、やわらかい台です。大きさ・クッションの硬さ・カバーの洗いやすさが決め手になります。",
          "A soft base to rest on. Size, cushion firmness and a washable cover are what matter.",
          "用来休息的柔软垫子。尺寸、垫子软硬度和外套是否好洗是关键。"),
    mat=("中材：ウレタンフォーム・綿／カバー：ポリエステル・綿（ファスナーで外せる）／底：滑り止め", "Filling: urethane foam or fibre · Cover: polyester or cotton (removable with a zip) · Base: anti-slip", "填充：聚氨酯泡沫・棉／外套：涤纶・棉（拉链可拆）／底部：防滑"),
    matw=("中材：水を吸いにくいフォーム／カバー：撥水・速乾の生地／底：滑り止め", "Filling: water-resistant foam · Cover: water-repellent quick-dry fabric · Base: anti-slip", "填充：不易吸水的泡沫／外套：防泼水速干面料／底部：防滑"),
    feats=[("洗えるカバー", "Washable cover", "可洗外套"), ("へたりにくいクッション", "Cushion that keeps its shape", "不易塌陷的垫芯"), ("床で滑らない底", "Non-slip base", "防滑底部")],
    check=[("硬さ・へたり方", "Firmness and how it flattens over time", "软硬度和塌陷情况"), ("洗濯での縮み・型くずれ", "Shrinkage and loss of shape in washing", "洗涤后缩水・变形")],
    vars=[(("A. 平らなマット型", "A. Flat mat", "A. 平垫式"), ("安く、どこにでも置ける", "Cheap, fits anywhere", "便宜，放哪都行")),
          (("B. ふち付きの包まれる型", "B. Bolstered", "B. 带边包围式"), ("安心して休める。生地と縫製が増える", "Cosier; more fabric and sewing", "更有安全感；面料和缝制更多"))],
    proto=("見本を1〜3個縫い、実際に使って確かめる", "Sew 1–3 samples and test them in use", "缝制1–3个样品，实际使用测试"),
    mass=("縫製工場で数十〜数百個から", "Sewing factory from tens to hundreds of units", "在缝制工厂几十到几百个起")),

  dict(id='mat', kw=r'マット|シート|敷物|ラグ|カーペット|滑り止め|mat|rug',
    fig='mat', dims=(900, 600, 10), scale=None,
    name=("マット・シート", "Mat / sheet", "垫子・片材"),
    lead=("床や地面に敷く板状のものです。大きさ・厚さ・表面の滑りにくさ・水や汚れへの強さを決めます。",
          "A flat item laid on a floor or ground. Decide the size, thickness, surface grip and resistance to water and dirt.",
          "铺在地板或地面上的片状物。需要确定尺寸、厚度、表面防滑性和防水防污性能。"),
    mat=("ゴム・EVA・PVC・TPE、または布＋裏面の滑り止め", "Rubber, EVA, PVC or TPE, or fabric with an anti-slip back", "橡胶・EVA・PVC・TPE，或布料＋背面防滑"),
    matw=("水に強いゴム・TPE・EVA（水はけの穴つき）", "Water-resistant rubber, TPE or EVA (with drainage holes)", "耐水橡胶・TPE・EVA（带排水孔）"),
    feats=[("表面の滑り止めの模様", "Anti-slip surface pattern", "表面防滑纹理"), ("裏面がずれない", "Back that does not slide", "背面不移位"), ("切って大きさを合わせられる", "Can be cut to size", "可裁剪调整尺寸")],
    check=[("濡れたときの滑りにくさ", "Grip when wet", "沾湿时的防滑性"), ("におい・色移り", "Odour and colour transfer", "气味・掉色")],
    vars=[(("A. 既製の型に合わせる", "A. Standard sizes", "A. 现成尺寸"), ("早く安い", "Quick and cheap", "快速便宜")),
          (("B. 形から作る", "B. Custom shape", "B. 定制形状"), ("場所にぴったり合うが、型の費用がかかる", "Fits exactly, but tooling costs apply", "完全贴合，但需要模具费"))],
    proto=("既製の素材を切って1〜数枚", "Cut 1–a few pieces from stock material", "用现成材料裁剪1到几片"),
    mass=("型抜き・成形で数百枚から", "Die-cutting or moulding from a few hundred", "冲裁或成型，几百片起")),

  dict(id='cover', kw=r'カバー|覆い|屋根|日よけ|日除け|シェード|テント|タープ|傘|cover|shade|tent|canopy',
    fig='cover', dims=(1200, 800, 1000), scale=None,
    name=("カバー・屋根・日よけ", "Cover / roof / shade", "罩子・顶棚・遮阳"),
    lead=("物や場所を雨・日差し・ほこりから守る覆いです。覆う大きさ・生地や板の素材・風での飛ばされにくさを決めます。",
          "A covering that protects an object or area from rain, sun and dust. Decide the size, the fabric or panel material and how well it resists wind.",
          "保护物品或场所免受雨淋、日晒、灰尘的覆盖物。需要确定覆盖尺寸、面料或板材以及抗风性能。"),
    mat=("生地：ポリエステル（撥水・UVカット）／骨組み：アルミパイプ・グラスファイバー", "Fabric: polyester (water-repellent, UV-blocking) · Frame: aluminium tube or fibreglass", "面料：涤纶（防泼水・防紫外线）／骨架：铝管・玻璃纤维"),
    matw=None,
    feats=[("風で飛ばない固定（ペグ・おもり・ベルト）", "Fixings that resist wind (pegs, weights, straps)", "防风固定（地钉・配重・绑带）"), ("雨が溜まらない傾き", "Slope so rain does not pool", "不积水的倾斜"), ("たためて、しまえる", "Folds away for storage", "可折叠收纳")],
    check=[("強い風・雨での強さ", "Strength in strong wind and rain", "强风大雨下的强度"), ("日差しでの色あせ・劣化", "Fading and degradation in sunlight", "日晒褪色・老化")],
    vars=[(("A. 生地＋骨組み", "A. Fabric + frame", "A. 面料＋骨架"), ("軽く、たためる", "Light and foldable", "轻便可折叠")),
          (("B. 板・成形品", "B. Rigid panels", "B. 板材・成型件"), ("丈夫で長持ちするが、重く場所を取る", "Durable, but heavy and bulky", "结实耐用，但重且占地方"))],
    proto=("生地と市販のパイプで1つ作り、屋外で確かめる", "Make one with fabric and stock tubes and test it outdoors", "用面料和市售管材做1个，在室外测试"),
    mass=("縫製・パイプ加工の会社で数十〜数百から", "Sewing and tube-working companies, from tens to hundreds", "缝制和管材加工公司，几十到几百起")),

  dict(id='platform', kw=r'(?<![台])台(?![車所風湾湾帳本詞紙数])|デッキ|ステージ|置き台|作業台|platform|deck',
    fig='platform', dims=(900, 600, 400), scale='load',
    name=("台・デッキ（上に乗せる・乗るもの）", "Platform / deck", "平台・台面"),
    lead=("上に物や人・動物を乗せる平らな台です。天板の大きさ・高さ・乗る重さで、脚の数と骨組みの太さが決まります。",
          "A flat platform that holds objects, people or animals. Top size, height and load decide the number of legs and frame size.",
          "在上面放置物品或承载人・动物的平台。台面尺寸、高度和承重决定支脚数量和骨架粗细。"),
    mat=("骨組み：鋼またはアルミの角パイプ／天板：合板・樹脂板・縞鋼板", "Frame: steel or aluminium square tube · Top: plywood, plastic board or checker plate", "骨架：钢或铝方管／台面：胶合板・树脂板・花纹钢板"),
    matw=("骨組み：アルミ・ステンレス／天板：樹脂板（HDPE）・FRP・すのこ", "Frame: aluminium or stainless · Top: HDPE board, FRP or slatted deck", "骨架：铝・不锈钢／台面：HDPE 树脂板・FRP・格栅"),
    feats=[("高さを合わせられる脚（アジャスター）", "Height-adjustable feet", "可调高度的支脚"), ("滑りにくい天板", "Non-slip top", "防滑台面"), ("角を丸める", "Rounded corners", "圆角处理")],
    check=[("最大の重さでのたわみ・揺れ", "Deflection and wobble at the maximum load", "最大载重时的弯曲和晃动"), ("でこぼこの床・地面での安定", "Stability on uneven floors or ground", "在不平地面上的稳定性")],
    vars=[(("A. 脚4本の一体型", "A. Four-leg fixed", "A. 四脚一体式"), ("丈夫でシンプル", "Strong and simple", "结实简单")),
          (("B. 連結できるユニット型", "B. Modular units", "B. 可拼接单元式"), ("広さを変えられる。つなぎ目の強さの確認が要る", "Size can change; joint strength needs checking", "可改变面积；需要确认连接处强度"))],
    proto=("角パイプと板で1台作り、実際に乗せて確かめる", "Make one from square tube and board and test it with the real load", "用方管和板材做1台，实际承重测试"),
    mass=("パイプの切断・溶接と塗装、天板の切削。数十台から", "Tube cutting, welding and painting, top machining. From a few dozen", "管材切割・焊接和涂装，台面切削。几十台起")),

  dict(id='box', kw=r'箱|ボックス|収納|容器|コンテナ|トレー|トレイ|入れ物|ケース|box|container|tray',
    fig='box', dims=(400, 300, 250), scale=None,
    name=("箱・収納・容器", "Box / storage / container", "箱子・收纳・容器"),
    lead=("物を入れて運ぶ・しまうための箱です。中に入れる物の大きさと重さ、ふたの有無、重ねられるかを決めます。",
          "A box for carrying or storing things. Decide the inside size and weight, whether it has a lid and whether it stacks.",
          "用于装放、搬运或收纳物品的箱子。需要确定内部尺寸和重量、是否有盖、能否堆叠。"),
    mat=("樹脂（PP・ABS）・木・段ボール・板金から用途で選ぶ", "Choose from plastic (PP, ABS), wood, cardboard or sheet metal depending on use", "根据用途从树脂（PP・ABS）、木材、瓦楞纸、钣金中选择"),
    matw=("水に強い樹脂（PP・PE）またはステンレス、ふたにパッキン", "Water-resistant plastic (PP, PE) or stainless, with a gasket in the lid", "耐水树脂（PP・PE）或不锈钢，盖子带密封圈"),
    feats=[("ふた・取っ手", "Lid and handles", "盖子・提手"), ("重ねられる形", "Stackable shape", "可堆叠的形状"), ("中の仕切り", "Inner dividers", "内部隔板")],
    check=[("入れる物がちょうど収まるか", "Whether the contents fit well", "物品是否恰好放得下"), ("持ったとき・落としたときの強さ", "Strength when carried or dropped", "提拿或摔落时的强度")],
    vars=[(("A. 既製品＋加工", "A. Stock box + customising", "A. 现成品＋加工"), ("印刷・仕切りだけ足す。早く安い", "Just add printing or dividers. Quick and cheap", "只加印刷或隔板。快速便宜")),
          (("B. 形から作る", "B. Custom design", "B. 从形状开始做"), ("ぴったり作れるが、型の費用がかかる", "Exact fit, but tooling costs apply", "可以完全贴合，但需要模具费"))],
    proto=("3Dプリントや板材で1〜数個", "1–a few units by 3D printing or from sheet material", "用3D打印或板材做1到几个"),
    mass=("樹脂の成形・板金・紙器の会社で数百個から", "Plastic moulding, sheet metal or carton makers, from a few hundred", "在树脂成型・钣金・纸盒公司几百个起")),

  dict(id='holder', kw=r'フック|ハンガー|掛け|取付|取り付け|ブラケット|マウント|固定具|クリップ|hook|hanger|mount|bracket|clip',
    fig='holder', dims=(60, 80, 100), scale=None,
    name=("取付金具・フック・ホルダー", "Mount / hook / holder", "安装件・挂钩・支架"),
    lead=("何かを壁・机・機械などに留めたり、掛けたりする小さな部品です。留める相手の形と、掛ける重さで形と材料が決まります。",
          "A small part that fixes or hangs something on a wall, desk or machine. The shape of what it attaches to and the load decide its form and material.",
          "把东西固定或挂在墙、桌子、机器等上的小零件。安装对象的形状和挂载重量决定其形状和材料。"),
    mat=("鋼・ステンレスの板金、アルミの切削、または樹脂（ナイロン・POM）", "Steel or stainless sheet metal, machined aluminium, or plastic (nylon, POM)", "钢・不锈钢钣金、铝切削件，或树脂（尼龙・POM）"),
    matw=("ステンレス（SUS304）またはアルミ（アルマイト）", "Stainless (SUS304) or anodised aluminium", "不锈钢（SUS304）或铝（阳极氧化）"),
    feats=[("相手の形に合わせた取付穴・はさむ部分", "Mounting holes or clamps that fit the target", "配合安装对象形状的安装孔・夹持部"), ("傷つけないゴムのあて", "Rubber pads to prevent scratches", "防刮的橡胶垫")],
    check=[("掛ける重さでの曲がり・外れ", "Bending or slipping under load", "挂载时是否弯曲・脱落"), ("取り付けのしやすさ", "Ease of installation", "安装是否方便")],
    vars=[(("A. 板金で作る", "A. Sheet metal", "A. 钣金"), ("丈夫で、数が多いと安い", "Strong, and cheap in volume", "结实，量大便宜")),
          (("B. 樹脂で作る", "B. Plastic", "B. 树脂"), ("軽く、形の自由がきく", "Light, with more freedom of shape", "轻巧，形状自由度高"))],
    proto=("3Dプリントか切削で数個", "A few units by 3D printing or machining", "用3D打印或切削做几个"),
    mass=("板金のプレス、または射出成形で数百個から", "Sheet-metal pressing or injection moulding from a few hundred", "钣金冲压或注塑，几百个起")),

  dict(id='bowl', kw=r'食器|皿|ボウル|カップ|コップ|マグ|給水|給餌|水入れ|bowl|cup|plate',
    fig='bowl', dims=(180, 180, 70), scale=None,
    name=("食器・ボウル・給水器", "Bowl / dish / water feeder", "餐具・碗・饮水器"),
    lead=("食べ物や水を入れる器です。容量・ひっくり返りにくさ・洗いやすさと、口に触れても安全な素材が決め手です。",
          "A container for food or water. Capacity, resistance to tipping, easy washing and mouth-safe materials are what matter.",
          "装食物或水的器皿。容量、不易打翻、方便清洗，以及接触口部也安全的材料是关键。"),
    mat=("ステンレス・陶磁器・食品に使える樹脂（PP・トライタン）・シリコーン", "Stainless, ceramic, food-safe plastic (PP, Tritan) or silicone", "不锈钢・陶瓷・食品级树脂（PP・Tritan）・硅胶"),
    matw=None,
    feats=[("ひっくり返りにくい重さ・底の滑り止め", "Weight and non-slip base to resist tipping", "不易打翻的重量・底部防滑"), ("食洗機で洗える", "Dishwasher-safe", "可用洗碗机清洗")],
    check=[("食品衛生法などに合う素材か", "Whether materials meet food-contact rules", "材料是否符合食品卫生相关规定"), ("割れ・かじりへの強さ", "Resistance to breaking and chewing", "耐摔・耐啃咬")],
    vars=[(("A. 既製の器に名入れ", "A. Stock item with logo", "A. 现成品加印标志"), ("早く安い", "Quick and cheap", "快速便宜")),
          (("B. 形から作る", "B. Original shape", "B. 从形状开始做"), ("独自の形にできるが、型の費用がかかる", "Unique shape, but tooling costs apply", "可做独特形状，但需要模具费"))],
    proto=("3Dプリントの形見本と、既製品の加工で数個", "A few units from 3D-printed shape models and modified stock items", "用3D打印形状样品和现成品加工做几个"),
    mass=("プレス（ステンレス）・成形（樹脂・シリコーン）・焼き物の会社で数百個から", "Pressing (stainless), moulding (plastic, silicone) or ceramics makers, from a few hundred", "在冲压（不锈钢）・成型（树脂・硅胶）・陶瓷公司几百个起")),

  dict(id='toy', kw=r'おもちゃ|玩具|知育|パズル|ゲーム|フィギュア|模型|toy|puzzle|figure',
    fig='toy', dims=(150, 150, 150), scale=None,
    name=("おもちゃ・知育グッズ", "Toy / educational item", "玩具・益智用品"),
    lead=("遊ぶ・学ぶための製品です。対象の年齢、壊れにくさ、口に入れても危なくないかで、形と素材が決まります。",
          "A product for play or learning. Target age, durability and safety if put in the mouth decide the shape and materials.",
          "用于玩耍或学习的产品。适用年龄、耐用性以及放进嘴里是否安全决定形状和材料。"),
    mat=("樹脂（ABS・PP）・木・布・シリコーン", "Plastic (ABS, PP), wood, fabric or silicone", "树脂（ABS・PP）・木・布・硅胶"),
    matw=None,
    feats=[("角を丸め、小さな部品が外れない作り", "Rounded edges and no small detachable parts", "圆角处理，小零件不会脱落"), ("ブランドの色・ロゴ", "Brand colours and logo", "品牌颜色・标志")],
    check=[("対象年齢の安全基準（例：STマーク）に合うか", "Whether it meets toy safety standards for the age group (e.g. ST mark in Japan)", "是否符合适龄安全标准（例：日本 ST 标志）"), ("投げる・かむ・引っぱるへの強さ", "Strength against throwing, biting and pulling", "耐摔・耐咬・耐拉扯")],
    vars=[(("A. 既製品にデザインを足す", "A. Stock toy + your design", "A. 现成品加设计"), ("早く、少ない数から", "Quick, from small quantities", "快速，小批量即可")),
          (("B. 形から作る", "B. Original design", "B. 从形状开始做"), ("独自にできるが、型と安全試験の費用がかかる", "Unique, but tooling and safety-test costs apply", "可独创，但需要模具和安全测试费用"))],
    proto=("3Dプリントで形を作り、数個で遊んで確かめる", "3D-print the shape and test a few units in play", "用3D打印做出形状，做几个实际玩测试"),
    mass=("樹脂の成形・木工・縫製の会社で数百個から", "Plastic moulding, woodwork or sewing companies, from a few hundred", "在树脂成型・木工・缝制公司几百个起")),

  dict(id='tool', kw=r'工具|道具|ツール|治具|器具|トング|ハサミ|はさみ|tool|jig',
    fig='tool', dims=(40, 250, 30), scale=None,
    name=("道具・工具・治具", "Tool / jig", "工具・治具"),
    lead=("手で使う道具や、作業を正確にするための治具です。持ちやすさ・力のかかる部分の強さ・使う回数で、素材と作り方が決まります。",
          "A hand tool or a jig that makes work accurate. Grip, strength where force is applied and frequency of use decide the materials and method.",
          "手用工具或让作业更精准的治具。握持感、受力部位强度和使用频率决定材料和制作方式。"),
    mat=("力のかかる部分：鋼・ステンレス・アルミ／持ち手：樹脂・ゴム", "Load-bearing parts: steel, stainless or aluminium · Grip: plastic or rubber", "受力部位：钢・不锈钢・铝／手柄：树脂・橡胶"),
    matw=("ステンレス・アルミ（アルマイト）／持ち手：滑りにくいゴム", "Stainless or anodised aluminium · Grip: non-slip rubber", "不锈钢・铝（阳极氧化）／手柄：防滑橡胶"),
    feats=[("手に合う持ち手", "Comfortable grip", "顺手的手柄"), ("力のかかる部分の強さ", "Strength where force is applied", "受力部位的强度")],
    check=[("繰り返し使ったときの摩耗・曲がり", "Wear and bending with repeated use", "反复使用后的磨损・弯曲"), ("手の疲れにくさ", "Hand fatigue", "手是否容易疲劳")],
    vars=[(("A. 切削で少量", "A. Machined, small batch", "A. 切削小批量"), ("金型なしで数個から", "No tooling, from a few units", "无需模具，几个起")),
          (("B. 鍛造・成形で量産", "B. Forged or moulded", "B. 锻造・成型量产"), ("1個あたりが安いが、型の費用がかかる", "Lower unit cost, but tooling costs apply", "单价低，但需要模具费"))],
    proto=("切削・3Dプリントで数個", "A few units by machining or 3D printing", "用切削或3D打印做几个"),
    mass=("鍛造・プレス・成形の会社で数百個から", "Forging, pressing or moulding companies, from a few hundred", "在锻造・冲压・成型公司几百个起")),

  dict(id='product', kw='', fig='product', dims=(200, 150, 100), scale=None,
    name=("オリジナル製品（汎用のたたき台）", "Original product (general starting point)", "原创产品（通用初稿）"),
    lead=("文章から製品の種類までは読めなかったため、どんな製品にも共通する「形・大きさ・素材・使い方」の組み立てで案を出しています。下の条件と、AI相談で形を具体的にしていくのがおすすめです。",
          "We could not tell the product type from your text, so this draft is built from what every product has in common: shape, size, materials and use. Refine it with the conditions below and the AI consultation.",
          "未能从描述中判断产品类型，因此按所有产品共通的“形状・尺寸・材料・用法”组合出方案。建议结合下方条件和 AI 咨询把形状具体化。"),
    mat=("樹脂（ABS・PP）・金属（アルミ・ステンレス）・木・布から、使う場所と強さで選ぶ", "Choose from plastic (ABS, PP), metal (aluminium, stainless), wood or fabric depending on where it is used and how strong it must be", "根据使用场所和强度要求，从树脂（ABS・PP）、金属（铝・不锈钢）、木材、布料中选择"),
    matw=("水に強い樹脂（PP・PE）・ステンレス・アルミから選ぶ", "Choose from water-resistant plastic (PP, PE), stainless or aluminium", "从耐水树脂（PP・PE）、不锈钢、铝中选择"),
    feats=[("使う人に合わせた大きさと持ちやすさ", "Size and grip suited to the user", "适合使用者的尺寸和握持感"), ("ロゴ・色などブランドの見た目", "Brand look: logo and colours", "品牌外观：标志・颜色")],
    check=[("実際の使い方で困るところがないか", "Whether anything is awkward in real use", "实际使用中是否有不便之处"), ("壊れやすいところ", "Weak points", "容易损坏的地方")],
    vars=[(("A. 既製品を加工する", "A. Modify a stock product", "A. 加工现成品"), ("早く安く、少ない数から", "Quick and cheap, from small quantities", "快速便宜，小批量即可")),
          (("B. 形から作る", "B. Original design", "B. 从形状开始做"), ("思い通りにできるが、設計と型の費用がかかる", "Exactly what you want, but design and tooling costs apply", "可以随心设计，但需要设计和模具费用"))],
    proto=("3Dプリントや手作りで1〜数個作って確かめる", "Make 1–a few by 3D printing or by hand and test them", "用3D打印或手工做1到几个进行确认"),
    mass=("形と素材が決まったら、その加工が得意な会社で数十〜数百個から", "Once shape and material are set, a company good at that process, from tens to hundreds of units", "形状和材料确定后，找擅长该工艺的公司，几十到几百个起")),
]

# 文章から読む条件。chip=画面の「読み取った条件」、feats/check=案に足す項目、water=素材を水まわり用にする
CONDS = [
  dict(id='pool', kw=r'プール|pool', water=True, chip=("プール", "Pool", "泳池"),
    feats=[("プールの壁に体重をかけない自立式（家庭用プールの壁や枠は横からの力に弱いことが多い）", "Self-supporting, so no weight rests on the pool wall (home pool walls and frames are often weak against sideways force)", "自立式，不把重量压在泳池壁上（家用泳池的池壁和框架往往不耐侧向力）"),
           ("プールの底やシートを傷つけない、やわらかい脚", "Soft feet that do not damage the pool floor or liner", "不会划伤泳池底部或内衬的柔软支脚")],
    check=[("水に入る側が浮かないか（樹脂は水に浮くものがある）・固定の方法", "Whether the in-water end floats (some plastics float) and how it is held in place", "入水一侧是否会漂浮（部分树脂会浮在水上）・固定方法"),
           ("プールの縁の高さ（実物を測る）", "Pool wall height (measure the real pool)", "泳池边缘高度（实测）")]),
  dict(id='water', kw=r'防水|水回り|水まわり|水辺|海|川|風呂|浴室|浴槽|雨|濡れ|水中|水に|waterproof|wet|bath|rain', water=True, chip=("水まわり", "Wet use", "用水环境"),
    feats=[("水が溜まらない穴・すき間", "Drain holes and gaps so water does not pool", "不积水的孔・缝隙")],
    check=[("さび・カビ・水を吸っての劣化", "Rust, mould and water absorption", "生锈・发霉・吸水老化")]),
  dict(id='outdoor', kw=r'屋外|野外|(?<!家)庭|ベランダ|キャンプ|アウトドア|外で|外に|畑|公園|outdoor|garden|camp', water=True, chip=("屋外", "Outdoors", "户外"),
    feats=[], check=[("紫外線・暑さ寒さでの劣化", "Degradation from UV, heat and cold", "紫外线・冷热导致的老化")]),
  dict(id='pet', kw=r'犬|いぬ|イヌ|猫|ねこ|ネコ|ペット|わんちゃん|愛犬|愛猫|dog|cat|pet', chip=("ペット用", "For pets", "宠物用"),
    feats=[("爪が引っかかりにくく、滑らない表面", "Surface that grips paws without catching claws", "不勾爪且防滑的表面"),
           ("横から落ちない縁（高さ5〜10cm）", "Side rails so the animal cannot step off (5–10 cm high)", "防止从侧面掉落的边缘（高5–10cm）")],
    check=[("動物が怖がらずに使えるか（傾き・足ざわり・音）", "Whether the animal uses it without fear (angle, feel underfoot, noise)", "动物是否不害怕地使用（坡度・脚感・声音）"),
           ("かじられても危なくない素材か", "Whether materials stay safe if chewed", "被啃咬时材料是否安全")]),
  dict(id='stable', kw=r'揺れない|ゆれない|安定|ぐらつかない|ガタつかない|がたつかない|しっかり|頑丈|丈夫|倒れない|stable|sturdy', chip=("揺れない", "Stable", "稳固"),
    feats=[("脚を広く取り、高さを合わせられるアジャスター", "Wide-set legs with height-adjustable feet", "支脚间距加宽，带可调高度脚垫"),
           ("床・地面・相手に留められる固定金具", "Fixing brackets to anchor it to the floor, ground or adjoining object", "可固定在地面或相邻物体上的固定件"),
           ("たわみにくい太めの骨組み・補強", "Heavier frame and bracing to limit deflection", "加粗骨架和加强筋，减少弯曲")],
    check=[("最大の重さで、揺れ・たわみが気にならないか", "Whether wobble and deflection are acceptable at the maximum load", "最大载重时晃动和弯曲是否可接受")]),
  dict(id='fold', kw=r'折りたたみ|折り畳み|折畳|持ち運び|運べる|軽い|軽量|コンパクト|しまえる|収納できる|foldable|portable|lightweight', chip=("折りたたみ・軽い", "Foldable / light", "可折叠・轻便"),
    feats=[("折りたたみ・分解して、しまえる", "Folds or comes apart for storage", "可折叠・拆分收纳"), ("軽いアルミ・樹脂を中心にする", "Mostly lightweight aluminium and plastic", "以轻质铝和树脂为主")],
    check=[("ちょうつがい・ロックの強さ", "Strength of hinges and locks", "铰链・锁扣的强度")]),
  dict(id='kids', kw=r'子ども|子供|こども|赤ちゃん|幼児|キッズ|乳児|kids|child|baby', chip=("子ども向け", "For children", "儿童用"),
    feats=[("角を丸め、指をはさまない作り", "Rounded corners and no finger traps", "圆角处理，不夹手指")],
    check=[("子ども向けの安全基準に合うか", "Whether it meets safety standards for children's products", "是否符合儿童用品安全标准")]),
  dict(id='elder', kw=r'高齢|介護|お年寄り|シニア|車いす|車椅子|elderly|wheelchair', chip=("高齢者・介護", "Older people / care", "老人・护理"),
    feats=[("手すり・つかまる所", "Handrails or grab points", "扶手・可抓握处")],
    check=[("つまずき・転倒の起きにくさ", "Low risk of tripping and falling", "不易绊倒・跌倒")]),
  dict(id='power', kw=r'電動|自動|センサー|センサ|ライト|充電|電池|アプリ|スマホで|bluetooth|led|motor', chip=("電気で動く", "Powered", "电动"),
    feats=[("電源（電池またはコンセント）と操作スイッチ", "Power source (battery or mains) and controls", "电源（电池或插座）和操作开关")],
    check=[("電気の安全・熱・防水", "Electrical safety, heat and water resistance", "用电安全・发热・防水")]),
  dict(id='food', kw=r'食べ|食品|口に入|口に触|食器|給餌|food', chip=("口に触れる", "Food contact", "接触口部"),
    feats=[], check=[("食品に触れても安全な素材か（食品衛生法など）", "Whether materials are safe for food contact (food sanitation rules)", "材料接触食品是否安全（食品卫生相关规定）")]),
  dict(id='load', kw='', chip=("重さに耐える", "Load-bearing", "承重"), feats=[], check=[]),
]

def _strings():
    yield from WORDS
    for s in SHAPES:
        for f in ('name', 'lead', 'mat', 'proto', 'mass'):
            yield s[f]
        if s['matw']:
            yield s['matw']
        yield from s['feats']; yield from s['check']
        for a, b in s['vars']:
            yield a; yield b
    for c in CONDS:
        yield c['chip']; yield from c['feats']; yield from c['check']


T_GENERIC = {ja: (en, zh) for ja, en, zh in _strings()}


def data():
    j = lambda x: x[0] if x else None
    return {
        'shapes': [{'id': s['id'], 'kw': s['kw'], 'fig': s['fig'], 'dims': s['dims'], 'scale': s['scale'], 'name': j(s['name']), 'lead': j(s['lead']),
                    'mat': j(s['mat']), 'matw': j(s['matw']), 'feats': [j(x) for x in s['feats']], 'check': [j(x) for x in s['check']],
                    'vars': [[j(a), j(b)] for a, b in s['vars']], 'proto': j(s['proto']), 'mass': j(s['mass'])} for s in SHAPES],
        'conds': [{'id': c['id'], 'kw': c['kw'], 'water': c.get('water', False), 'chip': j(c['chip']),
                   'feats': [j(x) for x in c['feats']], 'check': [j(x) for x in c['check']]} for c in CONDS],
    }

# 相談しながら詰める（AIなし版）：答えると「相談で決めたこと」として依頼の文章に足し、案と候補を組み直す。
# show: 'all' / 'load'（乗る・載せる形と、重さが要る種類）/ 'height'（スロープ・ステップ・台）
QUESTIONS = [
  dict(id='place', show='all', q=("どこで使いますか？", "Where will it be used?", "在哪里使用？"), skip=r'屋外|屋内|室内|プール|風呂|浴室|庭|ベランダ|車内|車の中|水まわり',
    opts=[(("屋内", "Indoors", "室内"), "屋内で使う"), (("屋外", "Outdoors", "户外"), "屋外で使う"), (("水まわり・プール", "Wet areas / pool", "用水环境・泳池"), "水まわり・プールで使う"), (("車・乗り物の中", "In a vehicle", "车内・交通工具内"), "車の中で使う")]),
  dict(id='user', show='all', q=("誰（何）が使いますか？", "Who (or what) will use it?", "谁（什么）使用？"), skip=r'犬|猫|ペット|子ども|子供|高齢|介護|大人|赤ちゃん',
    opts=[(("大人", "Adults", "成人"), "大人が使う"), (("子ども", "Children", "儿童"), "子どもが使う"), (("高齢者", "Older people", "老人"), "高齢者が使う"),
          (("小型犬・猫", "Small dog / cat", "小型犬・猫"), "小型犬・猫が使う"), (("中型犬", "Medium dog", "中型犬"), "中型犬が使う"), (("大型犬", "Large dog", "大型犬"), "大型犬が使う")]),
  dict(id='load', show='load', q=("上に乗る・かかる重さは？", "How much weight goes on it?", "上面承载的重量是多少？"), skip=r'\d\s*(kg|キロ)',
    opts=[(("10kgまで", "Up to 10 kg", "10kg 以内"), "乗る重さ 10kg"), (("30kgまで", "Up to 30 kg", "30kg 以内"), "乗る重さ 30kg"), (("80kgまで", "Up to 80 kg", "80kg 以内"), "乗る重さ 80kg"), (("150kgまで", "Up to 150 kg", "150kg 以内"), "乗る重さ 150kg")]),
  dict(id='height', show='height', q=("段差（上の面）の高さは？", "How high is the step (top surface)?", "台阶（上表面）有多高？"), skip=r'高さ[^\d]{0,6}\d|縁[^\d]{0,6}\d|段差[^\d]{0,6}\d',
    opts=[(("30cmまで", "Up to 30 cm", "30cm 以内"), "高さ 30cm"), (("60cmまで", "Up to 60 cm", "60cm 以内"), "高さ 60cm"), (("80cmまで", "Up to 80 cm", "80cm 以内"), "高さ 80cm"), (("120cmまで", "Up to 120 cm", "120cm 以内"), "高さ 120cm")]),
  dict(id='size', show='nosize', q=("いちばん大きいところの大きさは？", "How big is it at its largest?", "最大的地方有多大？"), skip=r'\d\s*(cm|mm|センチ|ミリ)|大きさ',
    opts=[(("手のひら（〜10cm）", "Palm-sized (up to 10 cm)", "手掌大小（10cm 以内）"), "大きさ 10cm"), (("両手で持つ（〜30cm）", "Two-handed (up to 30 cm)", "双手拿（30cm 以内）"), "大きさ 30cm"),
          (("机に置く（〜60cm）", "Desk-sized (up to 60 cm)", "放桌上（60cm 以内）"), "大きさ 60cm"), (("床に置く（〜1m）", "Floor-standing (up to 1 m)", "放地上（1m 以内）"), "大きさ 100cm"), (("それ以上", "Larger", "更大"), "大きさ 150cm")]),
  dict(id='prio', show='all', q=("いちばん大事にしたいことは？", "What matters most?", "最看重什么？"), skip=r'揺れない|安定|丈夫|頑丈|軽い|軽量|折りたたみ|安く|安い',
    opts=[(("丈夫さ・安定", "Strength / stability", "结实・稳固"), "丈夫で揺れないこと"), (("軽さ・持ち運び", "Light / portable", "轻便・便携"), "軽くて持ち運べること"),
          (("安さ", "Low cost", "便宜"), "安く作れること"), (("見た目", "Looks", "外观"), "見た目がよいこと"), (("安全", "Safety", "安全"), "安全なこと")]),
  dict(id='budget', show='all', q=("1個あたりの予算は？", "Budget per unit?", "每个的预算是多少？"), skip=r'予算|円',
    opts=[(("〜1千円", "Up to ¥1,000", "1千日元以内"), "1個あたりの予算 1千円まで"), (("〜1万円", "Up to ¥10,000", "1万日元以内"), "1個あたりの予算 1万円まで"),
          (("〜10万円", "Up to ¥100,000", "10万日元以内"), "1個あたりの予算 10万円まで"), (("未定", "Not decided", "未定"), "1個あたりの予算は未定")]),
]
WORDS += [
    ("相談しながら詰める", "Refine it step by step", "边咨询边细化"),
    ("答えるたびに、製品イメージ案と候補の会社が変わります。答えた内容は見積の依頼にも入ります。", "Each answer updates the product concept and the candidate companies. Your answers also go into the quote request.", "每回答一次，产品构想和候选公司都会更新。回答内容也会写入询价单。"),
    ("自分の言葉で答える", "Answer in your own words", "用自己的话回答"), ("答える", "Answer", "回答"), ("とばす", "Skip", "跳过"),
    ("決めたこと", "Decided so far", "已决定的事项"), ("やり直す", "Start over", "重新开始"),
    ("質問は以上です。もっと自由に相談したいときは、下の「AIで相談」を使ってください。", "That's all the questions. To discuss more freely, use \"Consult with AI\" below.", "问题到此结束。想更自由地咨询，请使用下方的“用 AI 咨询”。"),
    ("相談で決めたこと", "Decided in consultation", "咨询中决定的事项"),
]

def _qstrings():
    for q in QUESTIONS:
        yield q['q']
        for lab, _ in q['opts']:
            yield lab

T_GENERIC.update({ja: (en, zh) for ja, en, zh in list(_qstrings()) + WORDS})

def qdata():
    return [{'id': q['id'], 'show': q['show'], 'q': q['q'][0], 'skip': q['skip'], 'opts': [[lab[0], memo] for lab, memo in q['opts']]} for q in QUESTIONS]

# 内蔵AIと話す（パソコンのChromeの Prompt API。端末の中で動く）
T_GENERIC.update({ja: (en, zh) for ja, en, zh in [
    ("内蔵AIと話す", "Chat with built-in AI", "与内置 AI 对话"),
    ("内蔵AIと話しながら詰める", "Refine it by chatting with the built-in AI", "与内置 AI 对话来细化"),
    ("このパソコンのChromeに入っているAI（Gemini Nano）と話せます。文章はこの端末の中で処理され、KATACHIにもAIの会社にも送られません。答えるたびに、製品イメージ案と候補の会社が変わります。",
     "You can chat with the AI built into Chrome on this computer (Gemini Nano). Your text is processed on this device and is not sent to KATACHI or any AI company. Each reply updates the product concept and the candidate companies.",
     "可以与这台电脑的 Chrome 内置 AI（Gemini Nano）对话。文字只在本设备上处理，不会发送给 KATACHI 或任何 AI 公司。每次回复都会更新产品构想和候选公司。（内置 AI 暂不支持中文，将用英语回答。）"),
    ("初めて使うときは、AIの準備（ダウンロード）に数分かかります。", "The first time, preparing the AI (a download) takes a few minutes.", "首次使用时，准备 AI（下载）需要几分钟。"),
    ("AIを準備しています…", "Preparing the AI…", "正在准备 AI…"),
    ("考えています…", "Thinking…", "思考中…"),
    ("更新した製品イメージ案を見る ↑", "See the updated product concept ↑", "查看更新后的产品构想 ↑"),
    ("もっと具体的な案にして", "Make the concept more specific", "Make the concept more specific"),
    ("使う場所に合う素材は？", "Which materials suit where it will be used?", "Which materials suit where it will be used?"),
    ("もっと安く作るには？", "How can it be made cheaper?", "How can it be made cheaper?"),
    ("安全のために気をつけることは？", "What should I watch for safety?", "What should I watch for safety?"),
    ("例：庭で使うので、雨に強くしたい", "e.g. It will be used in a garden, so it should handle rain", "e.g. It will be used in a garden, so it should handle rain"),
    ("内蔵AIへのメッセージ", "Message to the built-in AI", "给内置 AI 的消息"),
    ("送る", "Send", "发送"),
    ("会話をやり直す", "Start the chat over", "重新开始对话"),
    ("AIの答えは推定です。寸法・素材・安全は、工場・専門家との打ち合わせと試作で決まります。", "The AI's answers are estimates. Dimensions, materials and safety are settled with the factory or experts and through prototyping.", "AI 的回答是推测。尺寸、材料和安全需与工厂、专家商讨并通过试制确定。"),
    ("AIが答えられませんでした。もう一度送るか、「AIに相談」を使ってください。", "The AI could not answer. Send again, or use \"Ask AI\".", "AI 未能回答。请再发送一次，或使用“问 AI”。"),
    ("内蔵AIと決めたこと", "Decided with the built-in AI", "与内置 AI 决定的事项"),
    ("内蔵AIと詰めた案", "Refined with built-in AI", "经内置 AI 细化"),
    ("いまの製品イメージ案", "Current product concept", "当前的产品构想"),
    ("更新", "Updated", "已更新"),
    ("機能・試作で確かめることも見る ↑", "See functions and what to test in the prototype ↑", "查看功能和试制时要确认的事项 ↑"),
    ("内蔵AIとの会話をもとに、案と候補の会社を更新しました。よければ、このまま会社選びへ進めます。", "Updated the concept and candidate companies from your chat with the built-in AI. If it looks right, go on to choosing companies.", "已根据与内置 AI 的对话更新了构想和候选公司。如果合适，可以直接去选公司。"),
    ("このパソコンのChromeに入っているAIとの会話をもとにした案です（AIの推定）。寸法・素材・性能は、工場・専門家との打ち合わせと試作で決まります。図は大きさと形の目安で、設計図ではありません。",
     "This concept is based on your chat with the AI built into Chrome on this computer (an AI estimate). Dimensions, materials and performance are settled with the factory or experts and through prototyping. The figure shows rough size and shape, not a design drawing.",
     "这是根据与本电脑 Chrome 内置 AI 的对话整理的构想（AI 推测）。尺寸、材料和性能需与工厂、专家商讨并通过试制确定。图示仅为大小和形状的参考，并非设计图。"),
]})

# 製品イメージ案の3D表示
T_GENERIC.update({ja: (en, zh) for ja, en, zh in [
    ("寸法図", "Dimensions", "尺寸图"), ("表示", "View", "显示"),
    ("製品イメージ案の3D表示", "3D view of the product concept", "产品构想的 3D 显示"),
    ("ドラッグで回せます", "Drag to rotate", "拖动即可旋转"),
    ("3Dを準備しています…", "Preparing 3D…", "正在准备 3D…"),
    ("3Dを表示できませんでした。「寸法図」をご覧ください。", "Could not show 3D. Please see \"Dimensions\".", "无法显示 3D。请查看“尺寸图”。"),
    ("3Dを読み込めませんでした。「寸法図」をご覧ください。", "Could not load 3D. Please see \"Dimensions\".", "无法加载 3D。请查看“尺寸图”。"),
    ("拡大", "Zoom in", "放大"), ("縮小", "Zoom out", "缩小"), ("向きを戻す", "Reset view", "复原视角"),
]})

# AIの回答で製品の種類が変わりそうなときの確認
T_GENERIC.update({ja: (en, zh) for ja, en, zh in [
    ("AIの回答からは、別の種類の製品とも読めます。", "The AI's answer could also describe a different kind of product:", "从 AI 的回答来看，也可能是另一种产品："),
    ("製品の種類は変えずに、寸法・素材・条件だけを反映しました。", "We kept the product kind and only applied the dimensions, materials and conditions.", "产品种类保持不变，只反映了尺寸、材料和条件。"),
    ("この種類に切り替える", "Switch to this kind", "切换为这种产品"),
    ("AIの回答に合わせて、製品の種類を切り替えています。元の案：", "The product kind has been switched to match the AI's answer. Original concept:", "已按 AI 的回答切换产品种类。原来的构想："),
    ("元の種類に戻す", "Switch back", "恢复原来的种类"),
]})

# 長い仕様文から組み立てた案
T_GENERIC.update({ja: (en, zh) for ja, en, zh in [
    ("（仕様文に寸法がないため、構成から置いた仮の値）", "(provisional values from the listed components, as the spec gives no dimensions)", "（规格说明中没有尺寸，按构成暂定的数值）"),
    ("仕様文から読み取った製品名・構成をもとに、KATACHIが組み立てた案です（AIの推定）。寸法・素材・性能は、工場・専門家との打ち合わせと試作で決まります。図は大きさと形の目安で、設計図ではありません。",
     "KATACHI assembled this from the product name and components in your spec (an AI estimate). Dimensions, materials and performance are decided in discussions with factories and experts, and through prototyping. The drawing shows rough size and shape, not a design drawing.",
     "这是 KATACHI 根据规格说明中的产品名称和构成整理的方案（AI 推测）。尺寸、材料和性能需要通过与工厂、专家的沟通和试制来决定。图示只表示大致尺寸和形状，不是设计图。"),
]})
