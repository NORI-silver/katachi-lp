"""製品イメージ案（文章入力の結果画面の「製品イメージ案」カード）。

KATACHI は AI の API を使わないので、製品の種類ごとの典型例（テンプレート）から、
外観の図・サイズ・重さ・素材・動力・想定スペック・主な機能・方向性・試作で確かめること・作り方を出す。
画面では「AI推定（たたき台）」と明記し、最終判断は工場・専門家とする。

- 文言は (日本語, 英語, 中国語) の組で持つ。assemble.py が日本語だけを template.html の __CONCEPTS__ に入れ、
  i18n.py が T_CONCEPT を辞書に足す（画面の翻訳は辞書の完全一致で効く）。
- kw は文章（小文字化済み）に当てる正規表現。上から順に見て、最初に当たったものを使う。
- fig は template.html の図（CFIG）の種類と、図に書く寸法（mm。数字だけで、日本語を入れない）。
- 数字は製品の種類としての典型的な目安。実在企業の見積・性能ではない。
"""
import json

LABELS = [
    ("製品イメージ案", "Product concept", "产品构想"),
    ("AI推定・たたき台", "AI estimate · starting point", "AI推测・初稿"),
    ("サイズ（目安）", "Size (rough)", "尺寸（参考）"),
    ("重さ（目安）", "Weight (rough)", "重量（参考）"),
    ("主な素材", "Main materials", "主要材料"),
    ("動力・電源", "Power", "动力・电源"),
    ("想定スペック", "Target specs", "设想规格"),
    ("主な機能", "Main functions", "主要功能"),
    ("方向性を選ぶ", "Pick a direction", "选择方向"),
    ("試作で確かめること", "What to check in the prototype", "试制时要确认的事项"),
    ("作り方の目安", "How it is typically made", "制作方式参考"),
    ("試作", "Prototype", "试制"),
    ("量産", "Mass production", "量产"),
    ("選んだ方向性は、AI相談の質問文にも入ります。", "The direction you pick is also added to the question for your AI.", "所选方向也会写入给 AI 的提问中。"),
    ("この案をもとにAIで詰める", "Refine this with AI", "以此为基础用 AI 细化"),
    ("製品の種類ごとの典型例から、KATACHIが組み立てた案です（AIの推定）。寸法・素材・性能は、工場・専門家との打ち合わせと試作で決まります。図は大きさと形の目安で、設計図ではありません。",
     "KATACHI put this together from typical examples of this kind of product (an AI estimate). Dimensions, materials and performance are decided in discussions with factories and experts, and through prototyping. The drawing shows rough size and shape, not a design drawing.",
     "这是 KATACHI 根据同类产品的典型例子整理的方案（AI 推测）。尺寸、材料和性能需要通过与工厂、专家的沟通和试制来决定。图示只表示大致尺寸和形状，不是设计图。"),
    ("この文章からは、製品の種類を特定できませんでした。下の「AIで相談」を開くと、外観・サイズ・素材・機能の案も作ってもらえます。",
     "We couldn't tell the type of product from your text. Open \"Consult with AI\" below and your AI can also draft the look, size, materials and functions.",
     "未能从描述中判断产品类型。打开下方的“用 AI 咨询”，也可以让 AI 起草外观、尺寸、材料和功能方案。"),
]

C = []
def concept(id, kw, fig, name, lead, size, weight, mat, power, spec, feats, vars, check, proto, mass):
    C.append(dict(id=id, kw=kw, fig=fig, name=name, lead=lead, size=size, weight=weight, mat=mat, power=power,
                  spec=spec, feats=feats, vars=vars, check=check, proto=proto, mass=mass))

# ---------------------------------------------------------------- 法面・斜面の草刈機
concept('slope_mower', r'(法面|のり面|斜面|傾斜|土手|堤防|畦畔|あぜ|slope).{0,30}(草|刈|除草|mow)|(草|刈|除草|mow).{0,30}(法面|のり面|斜面|傾斜|土手|堤防|畦畔|あぜ|slope)',
  dict(k='crawler', w='800', l='1000', h='500', ang='30–40°'),
  ("法面用のリモコン・自動草刈機（ゴムクローラー式）", "Remote-controlled / autonomous slope mower (rubber crawler)", "坡面用遥控・自动割草机（橡胶履带式）"),
  ("低い車体を左右のゴムクローラーで斜面に張りつかせ、車体の下の回転刃で草を刈る小型の作業車です。最初は人が離れた場所からリモコンで動かし、慣れたら決めた範囲を自動で往復させる、という段階で作ると無理がありません。",
   "A small, low work vehicle that grips the slope with left and right rubber crawlers and cuts grass with a rotary blade underneath. A sensible path is to start with remote control from a safe distance, then add automatic back-and-forth runs over a set area.",
   "一种车身低矮的小型作业车，用左右橡胶履带贴住坡面行走，用车身下方的旋转刀片割草。比较稳妥的做法是先由人在远处遥控操作，熟练后再让它在设定范围内自动往返。"),
  ("幅 約80cm × 長さ 約100cm × 高さ 約50cm（刈幅 約50〜60cm）", "approx. W 80 cm × L 100 cm × H 50 cm (cutting width approx. 50–60 cm)", "宽约80cm × 长约100cm × 高约50cm（割幅约50–60cm）"),
  ("約60〜120kg。重心を低くし、斜面で横転しにくい形にする", "approx. 60–120 kg, with a low centre of gravity so it does not roll over on slopes", "约60–120kg。重心放低，在坡面上不易侧翻"),
  ("フレーム：鋼板・ステンレスの板金（防錆塗装）／刃のカバー：厚めの鋼板／走行部：ゴムクローラー／制御部：防水ケース（樹脂または板金）",
   "Frame: sheet steel / stainless (rust-proof coating) · Blade guard: thick steel plate · Tracks: rubber crawlers · Controls: waterproof box (plastic or sheet metal)",
   "车架：钢板・不锈钢钣金（防锈涂装）／刀罩：较厚钢板／行走部：橡胶履带／控制部：防水外壳（树脂或钣金）"),
  ("48Vのリチウムイオン電池（交換式）＋走行モーター2個＋刈刃モーター1個。長時間ならエンジン式も選べる",
   "48 V swappable lithium-ion battery + 2 drive motors + 1 blade motor. An engine version is an option for long working hours",
   "48V 锂离子电池（可更换）＋行走电机2个＋割刀电机1个。需要长时间作业时也可选发动机式"),
  ("登れる傾斜 30〜40度、1回の充電で約1〜2時間、刈る高さ 3〜10cmで調整、速さ 時速約1〜3km、リモコンの届く距離 約100m",
   "Climbs 30–40° slopes, approx. 1–2 hours per charge, cutting height adjustable 3–10 cm, speed approx. 1–3 km/h, remote range approx. 100 m",
   "可爬坡度30–40度，充一次电约1–2小时，割草高度3–10cm可调，速度约1–3km/h，遥控距离约100m"),
  [("離れた場所からのリモコン操作", "Remote control from a distance", "远距离遥控操作"),
   ("傾きを検知して、危ない角度で自動停止", "Tilt sensing with automatic stop at dangerous angles", "检测倾斜，到危险角度时自动停止"),
   ("持ち上げ・転倒・電波が切れたときに刃を止める", "Stops the blade when lifted, tipped over or the radio link drops", "被抬起、翻倒或信号中断时停止刀片"),
   ("非常停止ボタン（本体とリモコンの両方）", "Emergency stop buttons on both the machine and the remote", "紧急停止按钮（机身和遥控器都有）"),
   ("GPS（RTK）で範囲を決めて自動で往復（発展版）", "Automatic back-and-forth runs over an area set with GPS (RTK) (advanced version)", "用 GPS（RTK）设定范围后自动往返（进阶版）"),
   ("前方の障害物・人を検知して止まる（発展版）", "Stops when it detects obstacles or people ahead (advanced version)", "检测到前方障碍物或行人时停止（进阶版）")],
  [(("A. リモコン式", "A. Remote-controlled", "A. 遥控式"), ("まず確実に動くものを作る。開発費と期間をいちばん抑えられる", "Get a machine that reliably works first. Lowest development cost and time", "先做出能可靠运行的机器。开发费用和周期最低")),
   (("B. 自動走行式", "B. Autonomous", "B. 自动行驶式"), ("RTK-GNSSと傾斜センサーで決めた範囲を自動で刈る。人手は減るが、開発と安全の確認が重い", "Mows a set area automatically using RTK-GNSS and tilt sensors. Saves labour, but development and safety checks are heavy", "利用 RTK-GNSS 和倾斜传感器自动割设定范围。省人力，但开发和安全验证工作量大")),
   (("C. エンジン＋電動", "C. Engine + electric", "C. 发动机＋电动"), ("刈刃はエンジン、走行は電動。広い法面を長時間刈りたいとき向け", "Engine for the blade, electric drive for the tracks. For mowing large slopes for long hours", "割刀用发动机，行走用电动。适合长时间割大面积坡面"))],
  [("濡れた草の斜面で滑らないか、何度まで横転しないか", "Whether it slips on wet grassy slopes, and up to what angle it stays upright", "在湿草坡面上是否打滑，多少度以内不会侧翻"),
   ("刃の安全：石の跳ね返り、人が近づいたときの止まり方", "Blade safety: flying stones, and how it stops when people come near", "刀片安全：石子飞溅，有人靠近时如何停止"),
   ("電池の持ちと、刈る負荷が大きいときのモーターの発熱", "Battery life, and motor heat under heavy cutting loads", "电池续航，以及割草负荷大时电机的发热"),
   ("雨・泥・草の汁に対する防水・防塵", "Water and dust resistance against rain, mud and plant sap", "对雨水、泥土和草汁的防水防尘")],
  ("板金・溶接のフレームに、市販のモーター・クローラー・刈刃を組み合わせて1〜2台", "1–2 units: a welded sheet-metal frame combined with off-the-shelf motors, crawlers and blades", "用钣金焊接车架，组合市售电机、履带和刀片，做1–2台"),
  ("板金のプレス・溶接の治具をそろえ、制御基板とリモコンを専用に設計", "Sheet-metal pressing and welding jigs, with a dedicated control board and remote", "准备钣金冲压和焊接夹具，专门设计控制板和遥控器"))

# ---------------------------------------------------------------- 平地の草刈・芝刈ロボット
concept('lawn_mower', r'草刈|草かり|芝刈|芝かり|除草|刈払|mower|mowing',
  dict(k='lawn', w='550', l='700', h='300'),
  ("自動で走る草刈・芝刈ロボット（車輪式）", "Self-driving grass / lawn mowing robot (wheeled)", "自动行驶的割草・剪草机器人（轮式）"),
  ("平らな庭・グラウンド・果樹園の下草を、決めた範囲の中で自動で走って刈る車輪式のロボットです。刃は本体の中に隠し、持ち上げると止まる作りにします。",
   "A wheeled robot that drives itself within a set area and cuts grass in gardens, sports fields or under orchard trees. The blade sits inside the body and stops when the robot is lifted.",
   "一种轮式机器人，在设定范围内自动行驶，修剪平坦庭院、运动场或果园下的杂草。刀片藏在机身内部，被抬起时自动停止。"),
  ("幅 約55cm × 長さ 約70cm × 高さ 約30cm（刈幅 約20〜40cm）", "approx. W 55 cm × L 70 cm × H 30 cm (cutting width approx. 20–40 cm)", "宽约55cm × 长约70cm × 高约30cm（割幅约20–40cm）"),
  ("約10〜20kg", "approx. 10–20 kg", "约10–20kg"),
  ("外装：耐候性の樹脂（ASA・PPなど）／下回り：アルミまたは鋼板／刃：鋼", "Shell: weather-resistant plastic (ASA, PP, etc.) · Chassis: aluminium or sheet steel · Blades: steel", "外壳：耐候树脂（ASA・PP 等）／底盘：铝或钢板／刀片：钢"),
  ("リチウムイオン電池（18〜36V）。充電ステーションに自分で戻る", "Lithium-ion battery (18–36 V). Returns to its charging station by itself", "锂离子电池（18–36V）。自动返回充电座"),
  ("1回の充電で約1〜3時間、登れる傾斜 約20度まで、刈る高さ 2〜6cm、雨の中でも動く程度の防水（IPX4〜5）", "Approx. 1–3 hours per charge, slopes up to about 20°, cutting height 2–6 cm, splash-proof enough to run in rain (IPX4–5)", "充一次电约1–3小时，可爬坡度约20度以内，割草高度2–6cm，可在雨中运行的防水等级（IPX4–5）"),
  [("決めた範囲の中を自動で走る（境界ワイヤーまたはGPS）", "Drives itself within a set area (boundary wire or GPS)", "在设定范围内自动行驶（边界线或 GPS）"),
   ("充電ステーションへ自動で戻る", "Returns to the charging station automatically", "自动返回充电座"),
   ("持ち上げ・転倒で刃が止まる", "Blade stops when lifted or tipped over", "被抬起或翻倒时刀片停止"),
   ("ぶつかったら向きを変える", "Changes direction when it bumps into something", "碰到障碍物会转向"),
   ("スマホで予定と範囲を設定", "Schedule and area set from a smartphone", "用手机设置时间和范围")],
  [(("A. 境界ワイヤー式", "A. Boundary wire", "A. 边界线式"), ("地面に線を張って範囲を決める。安くて確実", "A wire laid on the ground marks the area. Cheap and reliable", "在地面铺线确定范围。便宜可靠")),
   (("B. GPS（RTK）式", "B. GPS (RTK)", "B. GPS（RTK）式"), ("線を張らずに地図で範囲を決める。広い場所向けだが部品代が上がる", "Area set on a map without wires. Suits large sites, but parts cost more", "不用铺线，在地图上设定范围。适合大场地，但零件成本较高"))],
  [("刈り残し・刈りすぎの出方", "How much grass is missed or over-cut", "漏割和割过头的情况"),
   ("子ども・ペットが近づいたときの刃の止まり方", "How the blade stops when children or pets come near", "儿童或宠物靠近时刀片如何停止"),
   ("雨・夏の直射日光での動作と電池の温度", "Operation in rain and summer sun, and battery temperature", "雨天和夏季直射阳光下的运行情况及电池温度")],
  ("3Dプリントの外装と市販のモーター・電池で1〜3台", "1–3 units with a 3D-printed shell and off-the-shelf motors and batteries", "用3D打印外壳和市售电机、电池做1–3台"),
  ("外装は樹脂の射出成形（金型）、制御基板を専用に設計", "Injection-moulded plastic shell (with moulds) and a dedicated control board", "外壳用树脂注塑（开模），专门设计控制板"))

# ---------------------------------------------------------------- 電動台車・搬送ロボット
concept('cart', r'台車|搬送|運搬|配膳|agv|amr|(?<!ス)カート|荷物を運|\bcart\b',
  dict(k='cart', w='600', l='900', h='400'),
  ("電動アシスト台車・搬送ロボット", "Powered cart / transport robot", "电动助力推车・搬运机器人"),
  ("倉庫・工場・店舗の中で荷物を運ぶ、平らな荷台の電動台車です。最初は押す力を助けるアシスト式、次に人について行く・決めた道を走る自動式へ広げられます。",
   "A flat-deck powered cart for moving goods inside warehouses, factories or shops. Start with a power-assist cart, then extend it to follow a person or drive a set route on its own.",
   "一种平板电动推车，用于在仓库、工厂或店铺内运送货物。先做助力推行式，之后可扩展为跟随人或按设定路线自动行驶。"),
  ("荷台 幅 約60cm × 長さ 約90cm、高さ 約40cm（取っ手を除く）", "Deck approx. W 60 cm × L 90 cm, height approx. 40 cm (without handle)", "货台宽约60cm × 长约90cm，高约40cm（不含把手）"),
  ("本体 約30〜60kg、積める重さ 約100〜300kg", "Body approx. 30–60 kg, payload approx. 100–300 kg", "车身约30–60kg，载重约100–300kg"),
  ("フレーム：鋼またはアルミの角パイプ・板金／荷台：アルミ板または樹脂／車輪：ウレタン", "Frame: steel or aluminium square tube and sheet metal · Deck: aluminium plate or plastic · Wheels: urethane", "车架：钢或铝方管・钣金／货台：铝板或树脂／车轮：聚氨酯"),
  ("24Vの電池＋車輪の中に入ったモーター（インホイールモーター）2個", "24 V battery + 2 in-wheel motors", "24V 电池＋2个轮毂电机"),
  ("速さ 時速約3〜5km（人の歩く速さ）、1回の充電で約4〜8時間、段差 約1〜2cmまで", "Speed approx. 3–5 km/h (walking pace), approx. 4–8 hours per charge, steps up to approx. 1–2 cm", "速度约3–5km/h（人步行速度），充一次电约4–8小时，可越过约1–2cm的台阶"),
  [("押す力のアシスト・坂道で下がらないブレーキ", "Push assist and a brake that holds on slopes", "推行助力・坡道防溜刹车"),
   ("人について行く／床のテープに沿って走る", "Follows a person / follows tape on the floor", "跟随人／沿地面胶带行驶"),
   ("前の障害物で止まる（バンパー・距離センサー）", "Stops for obstacles ahead (bumper and distance sensors)", "前方有障碍物时停止（防撞条・距离传感器）"),
   ("非常停止ボタン", "Emergency stop button", "紧急停止按钮")],
  [(("A. アシスト式", "A. Power assist", "A. 助力式"), ("人が押す前提。安全の確認が軽く、早く安く作れる", "Pushed by a person. Lighter safety checks, quick and cheap to build", "以人推为前提。安全验证较轻，可快速低成本制作")),
   (("B. 追従・自動走行式", "B. Follow-me / autonomous", "B. 跟随・自动行驶式"), ("人の手が空く。センサーと安全の設計・確認が要る", "Frees people's hands. Needs sensor and safety design and testing", "解放人手。需要传感器和安全方面的设计与验证"))],
  [("最大の荷物を積んだときの止まる距離", "Stopping distance with a full load", "满载时的制动距离"),
   ("段差・床の継ぎ目での揺れと荷崩れ", "Shaking and load shifting over steps and floor joints", "过台阶和地面接缝时的晃动和货物倒塌"),
   ("人や棚の近くでの止まり方", "How it stops near people and shelves", "靠近人和货架时如何停止")],
  ("角パイプの溶接フレームに市販の車輪モーター・電池をのせて1〜2台", "1–2 units: welded square-tube frame with off-the-shelf wheel motors and batteries", "在方管焊接车架上装市售轮毂电机和电池，做1–2台"),
  ("板金のプレス・曲げと溶接の治具、制御基板を専用に設計", "Sheet-metal pressing and bending with welding jigs, and a dedicated control board", "钣金冲压折弯和焊接夹具，专门设计控制板"))

# ---------------------------------------------------------------- ドローン
concept('drone', r'ドローン|drone|マルチコプター',
  dict(k='drone', w='450', l='450', h='150'),
  ("業務用の小型ドローン（4枚プロペラ）", "Small commercial drone (quadcopter)", "小型业务用无人机（四旋翼）"),
  ("4本の腕の先にモーターとプロペラを付けた機体に、カメラやセンサーを積んで点検・撮影・測量をする小型ドローンです。重さ・飛ぶ場所で必要な手続きが変わるので、早めに決めておきます。",
   "A small drone with motors and propellers at the ends of four arms, carrying a camera or sensors for inspection, filming or surveying. Required procedures change with weight and where it flies, so decide these early.",
   "一种小型无人机，在四根机臂末端装电机和螺旋桨，搭载相机或传感器进行巡检、拍摄或测量。所需手续会因重量和飞行地点而不同，需要尽早确定。"),
  ("対角 約45cm（プロペラを除く）、高さ 約15cm", "approx. 45 cm diagonal (without propellers), height approx. 15 cm", "对角约45cm（不含螺旋桨），高约15cm"),
  ("約1〜2kg（積む機器を含む）", "approx. 1–2 kg including payload", "约1–2kg（含搭载设备）"),
  ("フレーム：カーボン板・パイプ／外装：樹脂（PC・ナイロン）／プロペラ：樹脂またはカーボン", "Frame: carbon plate and tube · Shell: plastic (PC, nylon) · Propellers: plastic or carbon", "机架：碳板・碳管／外壳：树脂（PC・尼龙）／螺旋桨：树脂或碳纤维"),
  ("リチウムポリマー電池（4〜6セル）、ブラシレスモーター4個", "Lithium-polymer battery (4–6 cells), 4 brushless motors", "锂聚合物电池（4–6节），4个无刷电机"),
  ("飛べる時間 約20〜30分、積める重さ 約0.3〜0.5kg、届く距離 約1〜2km", "Flight time approx. 20–30 min, payload approx. 0.3–0.5 kg, range approx. 1–2 km", "续航约20–30分钟，载重约0.3–0.5kg，通信距离约1–2km"),
  [("GPSでその場に止まる・決めた道を飛ぶ", "Holds position with GPS and flies set routes", "GPS 定点悬停・按设定航线飞行"),
   ("電池が減ったら自動で戻る", "Returns home automatically on low battery", "电量不足时自动返航"),
   ("カメラ・センサーの映像を手元に送る", "Sends camera and sensor feeds to the operator", "把相机和传感器画面传回操作端"),
   ("リモートIDなど、登録に必要な機能", "Functions needed for registration, such as Remote ID", "远程识别（Remote ID）等注册所需功能")],
  [(("A. 市販の飛行制御を使う", "A. Off-the-shelf flight controller", "A. 使用市售飞控"), ("飛ぶ部分は実績のある部品にまかせ、積む機器と用途に集中する", "Rely on proven parts for flight and focus on the payload and use case", "飞行部分交给成熟零件，专注于搭载设备和用途")),
   (("B. 専用に設計する", "B. Fully custom", "B. 专门设计"), ("形・重さを詰められるが、飛行の安全確認と電波の認証が重い", "Shape and weight can be optimised, but flight safety checks and radio certification are heavy", "可以优化形状和重量，但飞行安全验证和无线电认证工作量大"))],
  [("風の中での安定と、積んだ機器の重さでの飛べる時間", "Stability in wind, and flight time with the payload", "有风时的稳定性，以及搭载设备后的续航"),
   ("電波が切れたときの動き", "Behaviour when the radio link is lost", "信号中断时的动作"),
   ("落ちたときに壊れにくい形", "Shape that survives a crash", "坠落时不易损坏的结构")],
  ("市販のフレーム・飛行制御に、積む機器と外装を3Dプリントで足して2〜3機", "2–3 units: off-the-shelf frame and flight controller, with payload mounts and shell 3D-printed", "在市售机架和飞控上，用3D打印加装搭载设备和外壳，做2–3台"),
  ("カーボン板の切削、外装は樹脂の射出成形、基板を専用に設計", "Machined carbon plates, injection-moulded shell and a dedicated board", "碳板切削加工，外壳树脂注塑，专门设计电路板"))

# ---------------------------------------------------------------- ペットの首輪型デバイス
concept('collar', r'首輪|ハーネス|\bcollar\b|harness|(犬|猫|ペット).{0,20}(センサ|gps|見守|健康|デバイス)',
  dict(k='collar', w='45', l='30', h='15'),
  ("首輪に付けるペット用の小型デバイス", "Small device that clips onto a pet collar", "装在项圈上的宠物小型设备"),
  ("首輪のベルトに小さな本体を通し、活動量・位置・体温の目安などを測ってスマホに送る機器です。軽さと、濡れても壊れないことがいちばん大事です。",
   "A small unit threaded onto a collar strap that measures activity, location or an indication of body temperature and sends it to a smartphone. Light weight and surviving water matter most.",
   "一种穿在项圈带上的小型设备，测量活动量、位置或体温参考值等并发送到手机。最重要的是轻巧，以及沾水也不会坏。"),
  ("本体 約45×30×15mm、ベルト幅 約2〜2.5cm", "Unit approx. 45 × 30 × 15 mm, strap width approx. 2–2.5 cm", "主机约45×30×15mm，带宽约2–2.5cm"),
  ("本体 約15〜30g（小型犬なら首の負担を考えて軽く）", "Unit approx. 15–30 g (keep it light for small dogs)", "主机约15–30g（小型犬要更轻，减轻颈部负担）"),
  ("本体：樹脂（PC・ABS）＋防水パッキン／ベルト：ナイロンまたはシリコーン", "Unit: plastic (PC, ABS) + waterproof seal · Strap: nylon or silicone", "主机：树脂（PC・ABS）＋防水密封圈／带子：尼龙或硅胶"),
  ("小型のリチウム電池（充電式）。磁石でくっつく充電端子", "Small rechargeable lithium battery with a magnetic charging connector", "小型充电锂电池，磁吸充电接口"),
  ("電池の持ち 約3〜7日、防水 IP67程度（雨・水たまり）、スマホとBluetoothでつなぐ", "Battery approx. 3–7 days, waterproof to about IP67 (rain, puddles), connects to a phone by Bluetooth", "续航约3–7天，防水约 IP67（雨水、水洼），通过蓝牙连接手机"),
  [("歩数・活動量・寝ている時間の記録", "Records steps, activity and sleep time", "记录步数、活动量、睡眠时间"),
   ("迷子のときの位置（GPS版）", "Location if the pet gets lost (GPS version)", "走失时的位置（GPS 版）"),
   ("スマホのアプリでグラフを見る", "Graphs in a smartphone app", "在手机应用中查看图表"),
   ("首輪のサイズ違いに付け替えられる", "Moves between collars of different sizes", "可更换到不同尺寸的项圈")],
  [(("A. Bluetoothだけ", "A. Bluetooth only", "A. 仅蓝牙"), ("小さく軽く電池が長持ち。家の中・散歩の記録向け", "Small, light and long battery life. For recording at home and on walks", "小巧轻便、续航长。适合记录室内和散步")),
   (("B. GPS＋通信つき", "B. With GPS and cellular", "B. 带 GPS＋通信"), ("迷子に強いが、大きく重くなり、通信の月額と電波の認証が要る", "Better for lost pets, but bigger, heavier, with monthly data fees and radio certification", "走失时更有用，但更大更重，需要月租通信费和无线电认证"))],
  [("首に付けたときの重さ・形の違和感", "Whether the weight and shape bother the pet", "戴在脖子上时的重量和形状是否让宠物不适"),
   ("水・泥・かじられたときの強さ", "Resistance to water, mud and chewing", "对水、泥和啃咬的耐受性"),
   ("測った値が実際の動きと合っているか", "Whether the readings match actual movement", "测量值是否与实际活动一致")],
  ("3Dプリントの本体と試作基板で5〜10個。実際に犬に付けて試す", "5–10 units with 3D-printed housings and prototype boards, tested on real dogs", "用3D打印外壳和试制电路板做5–10个，在真实的狗身上试戴"),
  ("本体は射出成形（金型）、基板は量産の実装、電波の認証を取る", "Injection-moulded housing, mass-produced boards and radio certification", "外壳注塑（开模），电路板量产贴片，取得无线电认证"))

# ---------------------------------------------------------------- ウェアラブル（腕・体に付ける）
concept('wearable', r'ウェアラブル|リストバンド|腕時計|スマートウォッチ|指輪|リング型|wearable|watch',
  dict(k='band', w='40', l='40', h='12'),
  ("腕に付けるウェアラブル機器", "Wrist-worn wearable device", "戴在手腕上的可穿戴设备"),
  ("腕時計の形で、心拍・歩数・体の動きなどを測ってスマホに送る機器です。肌に触れる時間が長いので、付け心地と肌への優しさを先に決めます。",
   "A watch-shaped device that measures heart rate, steps or movement and sends it to a smartphone. It touches the skin for long periods, so comfort and skin-friendliness come first.",
   "一种手表形状的设备，测量心率、步数或身体动作并发送到手机。由于长时间接触皮肤，要先确定佩戴舒适度和对皮肤的友好性。"),
  ("本体 約40×40×12mm、バンド幅 約2cm", "Unit approx. 40 × 40 × 12 mm, band width approx. 2 cm", "主机约40×40×12mm，表带宽约2cm"),
  ("約25〜50g（バンドを含む）", "approx. 25–50 g including band", "约25–50g（含表带）"),
  ("本体：樹脂（PC）またはアルミ／裏ぶた：肌に触れても安心な樹脂／バンド：シリコーン", "Body: plastic (PC) or aluminium · Back: skin-safe plastic · Band: silicone", "机身：树脂（PC）或铝／后盖：接触皮肤安全的树脂／表带：硅胶"),
  ("小型のリチウム電池（充電式）", "Small rechargeable lithium battery", "小型充电锂电池"),
  ("電池の持ち 約3〜7日、生活防水（IP67程度）、Bluetoothでスマホとつなぐ", "Battery approx. 3–7 days, everyday water resistance (about IP67), Bluetooth to phone", "续航约3–7天，生活防水（约 IP67），蓝牙连接手机"),
  [("心拍・歩数・睡眠の記録", "Records heart rate, steps and sleep", "记录心率、步数、睡眠"),
   ("小さな画面か、光・振動でお知らせ", "Small screen, or light and vibration alerts", "小屏幕，或用灯光・振动提醒"),
   ("スマホのアプリでグラフを見る", "Graphs in a smartphone app", "在手机应用中查看图表")],
  [(("A. 画面なし", "A. No screen", "A. 无屏幕"), ("小さく安く、電池が長持ち", "Smaller, cheaper, longer battery life", "更小更便宜，续航更长")),
   (("B. 画面あり", "B. With screen", "B. 带屏幕"), ("その場で数字を見られるが、部品代と電池の消費が増える", "Readings at a glance, but higher parts cost and power use", "可当场查看数值，但零件成本和耗电增加"))],
  [("一日中付けたときの付け心地とかぶれ", "Comfort and skin irritation over a full day", "全天佩戴的舒适度和皮肤过敏"),
   ("汗・水への強さ", "Resistance to sweat and water", "对汗水和水的耐受性"),
   ("測った値の正しさ（医療機器にならない範囲で）", "Accuracy of readings (staying outside medical-device scope)", "测量值的准确性（在不属于医疗器械的范围内）")],
  ("3Dプリントの本体と試作基板で5〜10個", "5–10 units with 3D-printed bodies and prototype boards", "用3D打印机身和试制电路板做5–10个"),
  ("本体は射出成形、バンドはシリコーン成形、電波の認証を取る", "Injection-moulded body, moulded silicone band, radio certification", "机身注塑，表带硅胶成型，取得无线电认证"))

# ---------------------------------------------------------------- 見守り・IoTセンサー
concept('sensor', r'見守|センサー|センサ|iot|温湿度|開閉|人感|モニタリング|sensor|監視',
  dict(k='sensor', w='60', l='60', h='25'),
  ("壁や家具に付ける小型のIoTセンサー", "Small IoT sensor mounted on a wall or furniture", "装在墙上或家具上的小型 IoT 传感器"),
  ("部屋の温度・湿度、ドアの開け閉め、人の動きなどを測って、離れた家族や担当者のスマホに知らせる小さな箱です。電池で長く動き、付けるのが簡単なことが大事です。",
   "A small box that measures room temperature and humidity, door opening or movement, and notifies family members or staff on their phones. Long battery life and easy installation matter most.",
   "一个小盒子，测量室内温湿度、门的开关或人员活动等，并通知远方家人或负责人的手机。重要的是电池续航长、安装简单。"),
  ("本体 約60×60×25mm", "Unit approx. 60 × 60 × 25 mm", "主机约60×60×25mm"),
  ("約50〜100g（電池を含む）", "approx. 50–100 g including batteries", "约50–100g（含电池）"),
  ("本体：樹脂（ABS・PC）、白など部屋になじむ色／取付：両面テープまたはねじ", "Body: plastic (ABS, PC) in a colour that blends into rooms · Mounting: adhesive tape or screws", "机身：树脂（ABS・PC），白色等与房间协调的颜色／安装：双面胶或螺丝"),
  ("乾電池（単3×2本など）で1年前後、またはUSB給電", "AA batteries (e.g. 2×AA) lasting about a year, or USB power", "干电池（如2节5号电池）约1年，或 USB 供电"),
  ("測る間隔 1〜10分ごと、Wi-Fi・LTE-M・LoRaなどで送る、届く範囲 家の中〜建物全体", "Measures every 1–10 min, sends over Wi-Fi, LTE-M or LoRa, covering a home up to a whole building", "每1–10分钟测量一次，通过 Wi-Fi・LTE-M・LoRa 等发送，覆盖从室内到整栋建筑"),
  [("温度・湿度・開け閉め・人の動きを測る", "Measures temperature, humidity, door opening and movement", "测量温度、湿度、开关和人员活动"),
   ("いつもと違うときにスマホへ知らせる", "Notifies a phone when something is unusual", "出现异常时通知手机"),
   ("電池の残りを知らせる", "Low-battery alerts", "电量不足提醒"),
   ("管理画面で複数の部屋をまとめて見る", "Dashboard to see many rooms at once", "在管理画面中集中查看多个房间")],
  [(("A. Wi-Fi式", "A. Wi-Fi", "A. Wi-Fi 式"), ("家のWi-Fiにつなぐ。安いが、Wi-Fiのない家では使えない", "Joins the home Wi-Fi. Cheap, but useless where there is no Wi-Fi", "连接家中 Wi-Fi。便宜，但没有 Wi-Fi 的家庭无法使用")),
   (("B. 通信内蔵式", "B. Built-in cellular", "B. 内置通信式"), ("どこでも置くだけで使える。通信の月額と電波の認証が要る", "Works anywhere straight away. Monthly data fees and radio certification needed", "放在哪里都能直接用。需要月租通信费和无线电认证"))],
  [("電池が実際に何か月持つか", "How many months the batteries really last", "电池实际能用几个月"),
   ("壁・家具・建物での電波の届き方", "Radio reach through walls, furniture and buildings", "穿过墙壁、家具和建筑时的信号情况"),
   ("お知らせの出すぎ・出なさすぎ", "Too many or too few alerts", "提醒过多或过少")],
  ("3Dプリントのケースと評価用の基板で10〜20個。実際の部屋に置いて試す", "10–20 units with 3D-printed cases and evaluation boards, tested in real rooms", "用3D打印外壳和评估电路板做10–20个，放在实际房间中测试"),
  ("ケースは射出成形、基板は量産の実装、電波の認証を取る", "Injection-moulded case, mass-produced boards, radio certification", "外壳注塑，电路板量产贴片，取得无线电认证"))

# ---------------------------------------------------------------- ライト・照明
concept('light', r'ライト|照明|ランプ|ランタン|懐中電灯|\bled\b|\blight\b|\blamp\b',
  dict(k='light', w='35', l='90', h='35'),
  ("防水の小型LEDライト", "Small waterproof LED light", "防水小型 LED 灯"),
  ("自転車・アウトドア・作業用に、筒形の本体にLEDと充電池を入れ、取付台で固定する小型ライトです。雨の中で使えることと、光の広がり方が使い勝手を決めます。",
   "A compact light for bikes, outdoor or work use: a tube-shaped body with LEDs and a rechargeable battery, held by a mount. Use in rain and the shape of the beam decide how good it is.",
   "一种用于自行车、户外或作业的小型灯：筒形机身内装 LED 和充电电池，用支架固定。能否在雨中使用和光线的分布决定了好不好用。"),
  ("直径 約3.5cm × 長さ 約9cm", "approx. 3.5 cm diameter × 9 cm long", "直径约3.5cm × 长约9cm"),
  ("約80〜150g", "approx. 80–150 g", "约80–150g"),
  ("本体：アルミ（切削・アルマイト）または樹脂（PC）／レンズ：PC・アクリル／取付台：ナイロン樹脂とゴム", "Body: aluminium (machined, anodised) or plastic (PC) · Lens: PC or acrylic · Mount: nylon and rubber", "机身：铝（切削・阳极氧化）或树脂（PC）／透镜：PC・亚克力／支架：尼龙树脂和橡胶"),
  ("リチウムイオン電池（USB-Cで充電）", "Lithium-ion battery (USB-C charging)", "锂离子电池（USB-C 充电）"),
  ("明るさ 約200〜800ルーメン、点く時間 約2〜10時間、防水 IPX4〜7", "Brightness approx. 200–800 lumens, runtime approx. 2–10 h, waterproof IPX4–7", "亮度约200–800流明，点亮时间约2–10小时，防水 IPX4–7"),
  [("明るさの切り替え・点滅", "Brightness modes and flashing", "亮度切换・闪烁"),
   ("電池の残りの表示", "Battery level indicator", "电量显示"),
   ("工具なしで付け外しできる取付台", "Tool-free mount", "无需工具即可拆装的支架")],
  [(("A. 樹脂の本体", "A. Plastic body", "A. 树脂机身"), ("軽く安い。量が多いと金型代を回収しやすい", "Light and cheap. Mould costs pay back at higher volumes", "轻便便宜。量大时容易收回模具费")),
   (("B. アルミの本体", "B. Aluminium body", "B. 铝机身"), ("熱を逃がしやすく高級感がある。小ロットでも切削で作れる", "Better heat dissipation and a premium feel. Can be machined in small lots", "散热好、有质感。小批量也可切削加工"))],
  [("一番明るくしたときの熱", "Heat at maximum brightness", "最高亮度时的发热"),
   ("雨・水しぶきでの防水", "Water resistance in rain and spray", "雨水和水花下的防水"),
   ("振動で取付台がずれないか", "Whether the mount slips under vibration", "振动时支架是否松动")],
  ("アルミの切削または3Dプリントの本体で5〜10個", "5–10 units with machined aluminium or 3D-printed bodies", "用铝切削或3D打印机身做5–10个"),
  ("樹脂は射出成形、アルミは押出しと切削。LED基板は量産の実装", "Plastic by injection moulding, aluminium by extrusion and machining; LED boards mass-assembled", "树脂用注塑，铝用挤压和切削；LED 电路板量产贴片"))

# ---------------------------------------------------------------- 樹脂の小物（ケース・スタンド・ホルダー）
concept('case', r'スマホケース|ケース|スタンド|ホルダー|フック|収納|カバー|\bcase\b|\bholder\b|\bstand\b',
  dict(k='case', w='75', l='155', h='12'),
  ("樹脂で作る小物（ケース・スタンド・ホルダー）", "Small plastic item (case, stand, holder)", "树脂小物件（外壳・支架・收纳夹）"),
  ("手に持つ・机に置く・壁に掛けるなどの小さな樹脂製品です。形は3Dプリントで確かめ、数がまとまったら金型で作ると1個あたりが大きく下がります。",
   "A small plastic product to hold, put on a desk or hang on a wall. Check the shape with 3D printing, then move to moulds once volumes grow and the unit cost drops sharply.",
   "一种手持、放在桌上或挂在墙上的小型树脂产品。先用3D打印确认形状，数量多了再开模生产，单价会大幅下降。"),
  ("例：約75×155×12mm（スマホケースの場合）", "e.g. approx. 75 × 155 × 12 mm (for a phone case)", "例：约75×155×12mm（手机壳的情况）"),
  ("約20〜80g", "approx. 20–80 g", "约20–80g"),
  ("PC・TPU（ケース）、ABS・PP（スタンド・ホルダー）、表面はシボ・塗装・印刷", "PC or TPU (cases), ABS or PP (stands and holders); textured, painted or printed finish", "PC・TPU（外壳）、ABS・PP（支架・收纳夹），表面可做咬花、喷涂或印刷"),
  ("なし", "None", "无"),
  ("肉厚 約1〜2mm、落としても割れにくい、色・ロゴは印刷か成形の色で", "Wall thickness approx. 1–2 mm, survives drops, colour and logo by printing or moulded colour", "壁厚约1–2mm，摔落不易裂，颜色和标志通过印刷或原料着色"),
  [("ぴったり合う形・ボタンや穴の位置", "Exact fit, with button and hole positions", "完全贴合的形状・按键和孔位"),
   ("ロゴ・柄の印刷", "Logo and pattern printing", "标志・图案印刷"),
   ("パッケージ（台紙・袋・箱）", "Packaging (card, bag or box)", "包装（卡纸・袋・盒）")],
  [(("A. 3Dプリントで小ロット", "A. 3D-printed small lots", "A. 3D打印小批量"), ("金型なし。数十個までならこちらが安い", "No moulds. Cheaper up to a few dozen units", "无需开模。几十个以内更便宜")),
   (("B. 金型で成形", "B. Moulded", "B. 开模成型"), ("金型代がかかるが、数百個からは1個あたりが大きく下がる", "Mould costs up front, but much lower unit cost from a few hundred", "需要模具费，但几百个起单价大幅下降"))],
  [("実物に付けたときの合い具合", "Fit on the real object", "装在实物上的贴合程度"),
   ("落としたとき・曲げたときの強さ", "Strength when dropped or bent", "摔落或弯折时的强度"),
   ("色・質感が思った通りか", "Whether colour and texture are as expected", "颜色和质感是否符合预期")],
  ("3Dプリントで1〜20個", "1–20 units by 3D printing", "3D打印1–20个"),
  ("射出成形（金型）、印刷・梱包まで同じ会社でまとめられることが多い", "Injection moulding; printing and packing are often handled by the same company", "注塑成型（开模），印刷和包装往往可由同一家公司完成"))

# ---------------------------------------------------------------- バッグ・袋物
concept('bag', r'バッグ|鞄|かばん|カバン|ポーチ|トート|リュック|財布|袋物|エコバッグ|\bbag\b|\bpouch\b',
  dict(k='bag', w='380', l='120', h='400'),
  ("オリジナルのバッグ・ポーチ", "Original bag or pouch", "原创包・收纳袋"),
  ("布や合成皮革を裁断・縫製して作るバッグです。生地・持ち手・金具・ロゴの入れ方を決めると、見積が取りやすくなります。",
   "A bag cut and sewn from fabric or synthetic leather. Deciding the fabric, handles, hardware and how the logo is applied makes quotes much easier to get.",
   "一种用布料或合成皮革裁剪缝制的包。确定面料、提手、五金和标志的做法后，更容易拿到报价。"),
  ("例：幅 約38cm × 高さ 約40cm × マチ 約12cm（トートバッグの場合）", "e.g. approx. W 38 cm × H 40 cm × gusset 12 cm (for a tote)", "例：宽约38cm × 高约40cm × 侧宽约12cm（托特包的情况）"),
  ("約200〜600g", "approx. 200–600 g", "约200–600g"),
  ("表地：帆布・ナイロン・合成皮革／裏地：ポリエステル／持ち手：同じ生地またはテープ／金具：ファスナー・ナスカン", "Outer: canvas, nylon or synthetic leather · Lining: polyester · Handles: same fabric or webbing · Hardware: zips, snap hooks", "面料：帆布・尼龙・合成皮革／里布：涤纶／提手：同面料或织带／五金：拉链・钩扣"),
  ("なし", "None", "无"),
  ("A4が入る大きさ、内ポケット1〜2個、ロゴは刺しゅう・プリント・型押し", "Fits A4, 1–2 inner pockets, logo by embroidery, print or embossing", "可放入 A4，内袋1–2个，标志可刺绣、印刷或压印"),
  [("ファスナーやマグネットの口", "Zip or magnetic closure", "拉链或磁扣开口"),
   ("内ポケット・仕切り", "Inner pockets and dividers", "内袋・隔层"),
   ("ロゴ・ブランドのタグ", "Logo and brand label", "标志・品牌标签")],
  [(("A. 既製の型にロゴを入れる", "A. Logo on a stock design", "A. 在现成款式上加标志"), ("早く安い。数十個から頼みやすい", "Quick and cheap. Easy to order from a few dozen", "快速便宜。几十个起就容易下单")),
   (("B. 型から作る", "B. Fully original pattern", "B. 从版型开始做"), ("形・生地を自由に決められるが、型紙と見本の費用がかかる", "Free choice of shape and fabric, but pattern and sample costs apply", "形状和面料可自由决定，但需要打版和样品费用"))],
  [("物を入れたときの形くずれと持ち手の強さ", "Shape when loaded and strength of the handles", "装东西后的变形和提手强度"),
   ("色・生地の手ざわり", "Colour and feel of the fabric", "颜色和面料手感"),
   ("縫い目・金具の仕上がり", "Finish of seams and hardware", "缝线和五金的做工")],
  ("見本（サンプル）を1〜3個", "1–3 samples", "样品1–3个"),
  ("縫製工場で数十〜数百個から。生地をまとめて買うと1個あたりが下がる", "Sewing factory from tens to hundreds of units; buying fabric in bulk lowers unit cost", "在缝制工厂几十到几百个起做；面料批量采购可降低单价"))

# ---------------------------------------------------------------- アパレル
concept('apparel', r'tシャツ|t シャツ|シャツ|スカート|ワンピース|ズボン|パンツ|エプロン|パーカー|スウェット|ユニフォーム|作業着|ジャージ|帽子|キャップ|靴下|アパレル|洋服|ウェア|shirt|hoodie|apparel',
  dict(k='shirt', w='520', l='0', h='700'),
  ("オリジナルのウェア（Tシャツ・パーカーなど）", "Original apparel (T-shirts, hoodies, etc.)", "原创服装（T恤・卫衣等）"),
  ("既製のボディにプリント・刺しゅうを入れる方法と、生地・形から作るOEMの2通りがあります。サイズ展開と数量で、どちらが合うかが決まります。",
   "Two routes: print or embroider on ready-made blanks, or OEM production from fabric and pattern. Size range and quantity decide which fits.",
   "有两种方式：在成衣上印花或刺绣，或从面料和版型开始做 OEM。尺码范围和数量决定哪种更合适。"),
  ("S〜XLの4〜5サイズ（例：Mで身幅 約52cm × 着丈 約70cm）", "4–5 sizes from S to XL (e.g. M: chest width approx. 52 cm × length 70 cm)", "S–XL 共4–5个尺码（例：M码胸宽约52cm × 衣长约70cm）"),
  ("Tシャツ 約150〜250g、パーカー 約400〜700g", "T-shirt approx. 150–250 g, hoodie approx. 400–700 g", "T恤约150–250g，卫衣约400–700g"),
  ("綿100％・綿とポリエステルの混紡・吸汗速乾のポリエステル", "100% cotton, cotton-polyester blend, or moisture-wicking polyester", "100%棉、棉涤混纺、吸湿速干涤纶"),
  ("なし", "None", "无"),
  ("生地の厚さ 約5〜10オンス、プリント・刺しゅうの位置と大きさ、洗濯での縮み", "Fabric weight approx. 5–10 oz, print/embroidery position and size, shrinkage in washing", "面料厚度约5–10盎司，印花・刺绣的位置和大小，洗涤缩水"),
  [("ロゴ・柄のプリントまたは刺しゅう", "Logo or pattern printing or embroidery", "标志・图案印花或刺绣"),
   ("首のタグ（ブランド名・洗濯表示）", "Neck label (brand and care label)", "领标（品牌名・洗涤标）"),
   ("個別の袋入れ・たたみ", "Individual bagging and folding", "单独装袋・折叠")],
  [(("A. 既製ボディ＋プリント", "A. Blank + print", "A. 成衣＋印花"), ("1枚〜数十枚から早く作れる", "Quick, from one to a few dozen pieces", "一件到几十件起即可快速制作")),
   (("B. 生地から作るOEM", "B. OEM from fabric", "B. 从面料做 OEM"), ("形・生地・色を自由に決められる。数十〜数百枚から", "Free choice of cut, fabric and colour. From tens to hundreds of pieces", "版型、面料、颜色可自由决定。几十到几百件起"))],
  [("サイズ感（試着）", "Fit (try-on)", "尺码感（试穿）"),
   ("洗ったあとの縮み・色落ち・プリントの割れ", "Shrinkage, fading and print cracking after washing", "洗后缩水、褪色、印花开裂"),
   ("生地の厚さと透け", "Fabric thickness and see-through", "面料厚度和透光度")],
  ("見本を各サイズ1枚", "One sample per size", "每个尺码1件样品"),
  ("縫製工場・プリント工場で数十〜数百枚から", "Sewing or printing factory from tens to hundreds of pieces", "在缝制厂・印花厂几十到几百件起"))

# ---------------------------------------------------------------- 化粧品
concept('cosme', r'化粧品|コスメ|美容液|化粧水|(?<!アイス)クリーム|乳液|シャンプー|リンス|ボディソープ|ハンドソープ|石けん|石鹸|スキンケア|(?<!ク)リップ|ヘアオイル|cosmetic|skincare|shampoo',
  dict(k='bottle', w='45', l='45', h='150'),
  ("オリジナルの化粧品・スキンケア（OEM）", "Original cosmetics / skincare (OEM)", "原创化妆品・护肤品（OEM）"),
  ("中身の処方は化粧品のOEM会社が既にある処方をもとに調整し、容器・ラベル・箱を合わせて作るのが一般的です。製造販売には許可が要るので、許可を持つOEM会社に頼む形が早道です。",
   "Usually an OEM maker adjusts one of its existing formulas, and the container, label and box are made to match. Selling cosmetics requires a licence, so working with a licensed OEM maker is the quickest route.",
   "一般做法是由化妆品 OEM 公司在现有配方基础上调整，再配合容器、标签和外盒制作。生产销售化妆品需要许可，委托持有许可的 OEM 公司是最快的途径。"),
  ("例：ボトル 直径 約4.5cm × 高さ 約15cm（内容量 100〜200mL）", "e.g. bottle approx. 4.5 cm diameter × 15 cm tall (100–200 mL)", "例：瓶身直径约4.5cm × 高约15cm（容量100–200mL）"),
  ("中身を含めて 約150〜300g", "approx. 150–300 g including contents", "含内容物约150–300g"),
  ("容器：PET・PE・ガラス／ポンプ・キャップ：PP／ラベル：フィルム・紙／箱：紙", "Container: PET, PE or glass · Pump/cap: PP · Label: film or paper · Box: paperboard", "容器：PET・PE・玻璃／泵头・瓶盖：PP／标签：薄膜・纸／外盒：纸"),
  ("なし", "None", "无"),
  ("内容量 30〜200mL、香り・使い心地・色の調整、全成分の表示", "Volume 30–200 mL, adjusted fragrance, texture and colour, full ingredient list", "容量30–200mL，调整香味、使用感和颜色，标示全成分"),
  [("既存の処方から香り・使い心地を調整", "Fragrance and texture adjusted from an existing formula", "在现有配方基础上调整香味和使用感"),
   ("容器・ラベル・箱のデザイン", "Container, label and box design", "容器・标签・外盒设计"),
   ("法律で決まった表示（全成分・製造販売元など）", "Legally required labelling (ingredients, marketing licence holder, etc.)", "法律规定的标示（全成分・生产销售商等）")],
  [(("A. 既存の処方をそのまま使う", "A. Use an existing formula as is", "A. 直接使用现有配方"), ("早く安い。少ないロットから頼みやすい", "Quick and cheap. Easy to order in small lots", "快速便宜。小批量也容易下单")),
   (("B. 処方を一から作る", "B. Develop a formula from scratch", "B. 从头开发配方"), ("差を出しやすいが、試作と安全性の確認に時間と費用がかかる", "Easier to differentiate, but prototyping and safety checks take time and money", "容易做出差异，但试制和安全性确认需要时间和费用"))],
  [("使い心地・香り（試作品を何度か比べる）", "Texture and fragrance (compare several samples)", "使用感和香味（多次比较试制品）"),
   ("容器との相性（漏れ・変質）", "Compatibility with the container (leaks, degradation)", "与容器的相容性（泄漏・变质）"),
   ("表示の内容が法律に合っているか", "Whether the labelling meets the law", "标示内容是否符合法律")],
  ("処方の見本を数回作って比べる", "Several rounds of formula samples to compare", "多次制作配方样品进行比较"),
  ("OEM会社で数百〜数千個から。容器を既製品にすると小ロットにしやすい", "OEM production from hundreds to thousands of units; stock containers make small lots easier", "在 OEM 公司几百到几千个起；使用现成容器更容易做小批量"))

# ---------------------------------------------------------------- 食品・菓子・サプリ
concept('food', r'食品|お菓子|菓子|アイス|ケーキ|パン|クッキー|焼き菓子|チョコ|ジャム|ソース|調味料|ドレッシング|レトルト|冷凍食品|飲料|ジュース|コーヒー|お茶|紅茶|サプリ|健康食品|ペットフード|おやつ|snack|food|supplement',
  dict(k='pouch', w='140', l='60', h='200'),
  ("オリジナルの食品（OEM）", "Original food product (OEM)", "原创食品（OEM）"),
  ("食品の工場が持っている作り方をもとに、味・量・パッケージを決めて作るのが一般的です。工場には営業の許可があり、表示（原材料・アレルギー・賞味期限）は一緒に決めます。",
   "Usually you start from a recipe the food factory already makes, then set the taste, portion and packaging. The factory holds the business licence, and the labelling (ingredients, allergens, best-before) is decided together.",
   "一般做法是以食品工厂现有的做法为基础，确定口味、分量和包装。工厂持有营业许可，标示（原材料・过敏原・保质期）一起决定。"),
  ("例：スタンドパウチ 幅 約14cm × 高さ 約20cm（内容量 50〜200g）", "e.g. stand-up pouch approx. W 14 cm × H 20 cm (50–200 g)", "例：自立袋宽约14cm × 高约20cm（内容量50–200g）"),
  ("内容量 約50〜500g", "Contents approx. 50–500 g", "内容量约50–500g"),
  ("中身：工場の既存の配合をもとに調整／袋：アルミ蒸着などのフィルム／箱：紙", "Contents: adjusted from the factory's existing recipe · Pouch: metallised film, etc. · Box: paperboard", "内容物：在工厂现有配方基础上调整／袋：镀铝膜等薄膜／外盒：纸"),
  ("なし", "None", "无"),
  ("賞味期限の目安、保存方法（常温・冷蔵・冷凍）、原材料・アレルギーの表示", "Target shelf life, storage (ambient, chilled or frozen), ingredient and allergen labelling", "保质期参考，保存方式（常温・冷藏・冷冻），原材料和过敏原标示"),
  [("味・量の調整", "Taste and portion adjustment", "口味和分量调整"),
   ("パッケージのデザインと法律で決まった表示", "Package design and legally required labelling", "包装设计和法律规定的标示"),
   ("ギフト箱・個包装", "Gift boxes and individual wrapping", "礼盒・独立包装")],
  [(("A. 工場の既存品に自社のラベル", "A. Your label on the factory's product", "A. 在工厂现有产品上贴自有标签"), ("いちばん早く、少ない数から作れる", "Fastest, and possible in small quantities", "最快，也能小批量制作")),
   (("B. 味から作る", "B. Develop the recipe", "B. 从口味开始做"), ("独自の味にできるが、試作と期限の確認に時間がかかる", "A unique recipe, but prototyping and shelf-life testing take time", "可以做独特口味，但试制和保质期验证需要时间"))],
  [("味（試作品を何度か比べる）", "Taste (compare several samples)", "口味（多次比较试制品）"),
   ("賞味期限まで品質が保てるか", "Whether quality holds until the best-before date", "能否保持品质到保质期"),
   ("表示の内容が法律に合っているか（効能はうたわない）", "Whether the labelling meets the law (no health claims)", "标示内容是否符合法律（不宣传功效）")],
  ("工場で試作品を数回作って比べる", "Several rounds of factory samples to compare", "在工厂多次制作试制品进行比较"),
  ("食品工場で数百〜数千個から", "Food factory from hundreds to thousands of units", "在食品工厂几百到几千个起"))

# ---------------------------------------------------------------- グッズ・ノベルティ
concept('goods', r'アクリル|アクスタ|キーホルダー|ステッカー|缶バッジ|ぬいぐるみ|ノベルティ|グッズ|マグカップ|タオル|うちわ|ピンバッジ|goods|merch|keychain|sticker',
  dict(k='acrylic', w='100', l='50', h='150'),
  ("オリジナルのグッズ（アクリル・ぬいぐるみ・ノベルティなど）", "Original merchandise (acrylic, plush, novelty items)", "原创周边（亚克力・毛绒・赠品等）"),
  ("イラストやロゴのデータを渡して作る、型が決まったグッズです。種類ごとに専門の会社があり、データの作り方と数量で値段が決まります。",
   "Standard-format merchandise made from your illustration or logo files. Each type has specialist makers, and price depends on how the artwork is prepared and the quantity.",
   "一种提供插画或标志数据即可制作的固定款式周边。每种都有专门的公司，价格取决于数据制作方式和数量。"),
  ("例：アクリルスタンド 高さ 約10〜15cm、台座 約5×10cm", "e.g. acrylic stand approx. 10–15 cm tall, base approx. 5 × 10 cm", "例：亚克力立牌高约10–15cm，底座约5×10cm"),
  ("約20〜100g", "approx. 20–100 g", "约20–100g"),
  ("アクリル板（厚さ 3〜5mm）、ぬいぐるみはポリエステルの布と綿、金具は鉄・ステンレス", "Acrylic sheet (3–5 mm thick); plush in polyester fabric and stuffing; metal fittings in steel or stainless", "亚克力板（厚3–5mm），毛绒用涤纶布和填充棉，五金用铁或不锈钢"),
  ("なし", "None", "无"),
  ("印刷はフルカラー（白を下に刷ると色がきれい）、個別の袋入れ", "Full-colour printing (a white underprint makes colours pop), individual bagging", "全彩印刷（底层印白色颜色更鲜艳），单独装袋"),
  [("イラスト・ロゴの印刷", "Illustration and logo printing", "插画・标志印刷"),
   ("形に合わせた切り抜き", "Die-cut to the outline", "按形状切割"),
   ("台紙・袋・箱の包装", "Backing card, bag or box packaging", "卡纸・袋・盒包装")],
  [(("A. 国内で小ロット", "A. Small lots in Japan", "A. 国内小批量"), ("数個〜数十個、早く届く", "A few to dozens of pieces, delivered fast", "几个到几十个，交货快")),
   (("B. 海外で数百個から", "B. Hundreds overseas", "B. 海外几百个起"), ("1個あたりは安いが、届くまでの日数と検品の手間が増える", "Lower unit cost, but longer lead time and more inspection work", "单价低，但交货周期更长，验货工作更多"))],
  [("色の出方（画面と印刷の違い）", "Colour reproduction (screen vs print)", "颜色效果（屏幕与印刷的差异）"),
   ("切り抜きの細かさ・角の安全", "Fineness of the cut and safe corners", "切割精细度・边角安全"),
   ("包装の見え方", "How the packaging looks", "包装效果")],
  ("見本を1〜数個", "One to a few samples", "样品1个到几个"),
  ("専門の会社で数十〜数百個から", "Specialist makers from tens to hundreds of pieces", "在专门公司几十到几百个起"))

# ---------------------------------------------------------------- 家具・木工
concept('furniture', r'家具|椅子|いす|テーブル|机|棚|ラック|木工|什器|ベンチ|furniture|chair|table|shelf',
  dict(k='furniture', w='1200', l='600', h='720'),
  ("オリジナルの家具・什器", "Original furniture / fixtures", "原创家具・陈列器具"),
  ("木材や金属の脚・板を組み合わせた家具・店舗の什器です。置く場所の寸法と、組み立てて届けるか分解して送るかで、作り方と送料が変わります。",
   "Furniture or shop fixtures combining wood or metal legs and panels. The space it goes in, and whether it ships assembled or flat-packed, change how it is made and shipped.",
   "一种组合木材或金属腿与板材的家具或店铺陈列器具。摆放空间的尺寸，以及组装后送达还是拆开发货，会影响制作方式和运费。"),
  ("例：テーブル 幅 約120cm × 奥行 約60cm × 高さ 約72cm", "e.g. table approx. W 120 cm × D 60 cm × H 72 cm", "例：桌子宽约120cm × 深约60cm × 高约72cm"),
  ("約15〜40kg", "approx. 15–40 kg", "约15–40kg"),
  ("天板：無垢材・集成材・合板＋化粧板／脚：スチール（粉体塗装）または木", "Top: solid wood, laminated wood or plywood with veneer · Legs: steel (powder-coated) or wood", "台面：实木・集成材・胶合板＋饰面板／腿：钢（粉末喷涂）或木"),
  ("なし", "None", "无"),
  ("耐える重さ、表面の仕上げ（オイル・ウレタン塗装）、分解して送れるか", "Load capacity, surface finish (oil or urethane), whether it can be flat-packed", "承重、表面处理（木蜡油・聚氨酯涂装）、能否拆装发货"),
  [("置く場所に合わせた寸法", "Sized to fit the space", "按摆放空间定制尺寸"),
   ("配線の穴・収納・キャスター", "Cable holes, storage, casters", "走线孔・收纳・脚轮"),
   ("ロゴの焼き印・刻印", "Branded or engraved logo", "烙印・刻印标志")],
  [(("A. 木工所でまとめて", "A. All-in-one at a woodshop", "A. 木工厂一站式"), ("木の質感を活かせる。1台から相談しやすい", "Makes the most of wood. Easy to discuss from one piece", "能发挥木材质感。一台起也好商量")),
   (("B. 天板と鉄脚を分けて", "B. Separate top and steel legs", "B. 台面和铁腿分开做"), ("脚は鉄工所、天板は木工所。量が増えると安くしやすい", "Legs from a metal shop, top from a woodshop. Cheaper as volumes grow", "腿找铁工厂，台面找木工厂。量大时更易降低成本"))],
  [("揺れ・たわみ", "Wobble and deflection", "晃动・弯曲"),
   ("表面の傷・汚れへの強さ", "Resistance to scratches and stains", "表面耐刮耐脏"),
   ("運ぶとき・組み立てのしやすさ", "Ease of delivery and assembly", "搬运和组装是否方便")],
  ("1台作って置き場所で確かめる", "Make one and check it in place", "先做1台在摆放处确认"),
  ("木工所・鉄工所で数台〜数十台から", "Woodshops and metal shops from a few to dozens of units", "在木工厂・铁工厂几台到几十台起"))

# ---------------------------------------------------------------- 機械・装置（ほかに当たらないとき）
concept('machine', '', dict(k='machine', w='600', l='800', h='700'),
  ("電動の機械・装置（汎用のたたき台）", "Electric machine / equipment (general starting point)", "电动机械・装置（通用初稿）"),
  ("金属のフレームにモーター・駆動部・センサー・制御箱を組み込んだ装置の、一般的な構成です。何を・どれくらいの速さで・どこで動かすかを決めると、大きさと部品が決まってきます。",
   "A typical layout: a metal frame holding motors, drive parts, sensors and a control box. Deciding what it moves, how fast and where it works determines the size and components.",
   "一般结构：金属框架内装电机、驱动部、传感器和控制箱。确定要移动什么、速度多快、在哪里运行后，尺寸和零件就能确定下来。"),
  ("例：幅 約60cm × 奥行 約80cm × 高さ 約70cm（用途で大きく変わる）", "e.g. approx. W 60 cm × D 80 cm × H 70 cm (varies greatly by use)", "例：宽约60cm × 深约80cm × 高约70cm（因用途差异很大）"),
  ("約20〜100kg", "approx. 20–100 kg", "约20–100kg"),
  ("フレーム：アルミの組み立て用フレームまたは鋼の板金／カバー：板金・樹脂／動く部分：鋼の切削部品", "Frame: aluminium extrusion or sheet steel · Covers: sheet metal or plastic · Moving parts: machined steel", "框架：铝型材或钢钣金／外罩：钣金・树脂／运动部件：钢切削件"),
  ("家庭用コンセント（100V）または電池（24〜48V）＋モーター", "Mains power (100 V) or battery (24–48 V) + motors", "家用电源（100V）或电池（24–48V）＋电机"),
  ("動かす重さ・速さ・1日に動かす時間、置く場所（屋内・屋外）", "Load, speed, hours per day and location (indoor or outdoor)", "负载、速度、每天运行时间、放置场所（室内・室外）"),
  [("ボタンまたはタッチパネルで操作", "Operated by buttons or a touch panel", "通过按钮或触摸屏操作"),
   ("センサーで状態を見て自動で動く", "Runs automatically using sensors", "用传感器监测状态自动运行"),
   ("非常停止・カバーを開けると止まる安全装置", "Emergency stop and interlocked covers", "紧急停止・打开外罩即停止的安全装置")],
  [(("A. 市販部品の組み合わせ", "A. Combine off-the-shelf parts", "A. 组合市售零件"), ("フレーム・モーターは市販品で早く作る", "Build fast with stock frames and motors", "框架和电机用市售品快速制作")),
   (("B. 専用に設計", "B. Fully custom design", "B. 专门设计"), ("小さく安くできるが、設計と試作の回数が増える", "Smaller and cheaper per unit, but more design and prototype rounds", "可以做得更小更便宜，但设计和试制次数增加"))],
  [("一番重い負荷での動きと発熱", "Operation and heat at the heaviest load", "最大负载下的运行和发热"),
   ("安全装置の効き", "How well safety devices work", "安全装置是否有效"),
   ("長時間動かしたときの壊れ方", "How it wears over long running", "长时间运行后的损坏情况")],
  ("アルミのフレームと市販の部品で1台", "One unit from aluminium extrusion and stock parts", "用铝型材和市售零件做1台"),
  ("板金・切削部品を専用にし、組立の手順と検査を決める", "Custom sheet-metal and machined parts, with defined assembly and inspection steps", "钣金和切削件专门设计，确定组装步骤和检验"))

# ---------------------------------------------------------------- 電子機器（ほかに当たらないとき）
concept('device', '', dict(k='device', w='100', l='70', h='30'),
  ("小型の電子機器（汎用のたたき台）", "Small electronic device (general starting point)", "小型电子设备（通用初稿）"),
  ("樹脂のケースに基板・電池・センサー・ボタンを入れ、スマホやパソコンとつなぐ機器の一般的な構成です。どこで・誰が・何を測る（動かす）かを決めると、大きさと部品が決まってきます。",
   "A typical layout: a plastic case holding a circuit board, battery, sensors and buttons, connected to a phone or computer. Deciding where it is used, by whom and what it measures or controls determines the size and parts.",
   "一般结构：树脂外壳内装电路板、电池、传感器和按键，与手机或电脑连接。确定在哪里、由谁使用、测量或控制什么之后，尺寸和零件就能确定下来。"),
  ("例：約100×70×30mm（手のひらサイズ）", "e.g. approx. 100 × 70 × 30 mm (palm-sized)", "例：约100×70×30mm（手掌大小）"),
  ("約80〜200g", "approx. 80–200 g", "约80–200g"),
  ("ケース：樹脂（ABS・PC）／中：基板・電池・センサー", "Case: plastic (ABS, PC) · Inside: board, battery, sensors", "外壳：树脂（ABS・PC）／内部：电路板・电池・传感器"),
  ("充電式の電池（USB-C）またはACアダプター", "Rechargeable battery (USB-C) or AC adapter", "充电电池（USB-C）或电源适配器"),
  ("つなぎ方（Bluetooth・Wi-Fi・有線）、電池の持ち、防水の程度", "Connectivity (Bluetooth, Wi-Fi or wired), battery life, water resistance", "连接方式（蓝牙・Wi-Fi・有线）、续航、防水等级"),
  [("センサーで測る・ボタンで操作する", "Measures with sensors, operated by buttons", "用传感器测量・用按键操作"),
   ("スマホのアプリで見る・設定する", "View and configure in a phone app", "用手机应用查看和设置"),
   ("LED・音・振動でお知らせ", "Alerts by LED, sound or vibration", "用 LED・声音・振动提醒")],
  [(("A. 評価用の基板を使う", "A. Use evaluation boards", "A. 使用评估板"), ("早く動くものを作り、使い方を確かめる", "Get a working unit quickly to test how it is used", "快速做出能用的东西，确认使用方式")),
   (("B. 専用の基板を設計", "B. Design a custom board", "B. 专门设计电路板"), ("小さく安くできるが、基板の設計と電波の認証が要る", "Smaller and cheaper, but needs board design and radio certification", "可以更小更便宜，但需要电路板设计和无线电认证"))],
  [("使う場所での電波・電池の持ち", "Radio and battery life where it is used", "使用场所的信号和续航"),
   ("落としたとき・水がかかったときの強さ", "Strength when dropped or splashed", "摔落或沾水时的耐受性"),
   ("アプリの使いやすさ", "Ease of use of the app", "应用是否好用")],
  ("3Dプリントのケースと評価用の基板で3〜10個", "3–10 units with 3D-printed cases and evaluation boards", "用3D打印外壳和评估板做3–10个"),
  ("ケースは射出成形、基板は量産の実装、電波の認証を取る", "Injection-moulded case, mass-produced boards, radio certification", "外壳注塑，电路板量产贴片，取得无线电认证"))


# 当てる順番: 細かい種類を先に（アクリル「スタンド」をケース・スタンドより先に、など）
ORDER = ['slope_mower', 'lawn_mower', 'cart', 'drone', 'collar', 'wearable', 'sensor', 'light', 'goods', 'case', 'bag', 'apparel', 'cosme', 'food', 'furniture', 'machine', 'device']
C.sort(key=lambda c: ORDER.index(c['id']))


def _all_strings():
    for c in C:
        for f in ('name', 'lead', 'size', 'weight', 'mat', 'power', 'spec', 'proto', 'mass'):
            yield c[f]
        yield from c['feats']
        yield from c['check']
        for a, b in c['vars']:
            yield a; yield b
    yield from LABELS


T_CONCEPT = {ja: (en, zh) for ja, en, zh in _all_strings()}


def js():
    """template.html の __CONCEPTS__ に入れる、日本語だけのデータ"""
    out = []
    for c in C:
        j = lambda x: x[0]
        out.append({'id': c['id'], 'kw': c['kw'], 'fig': c['fig'], 'name': j(c['name']), 'lead': j(c['lead']),
                    'rows': [[k, j(c[f])] for k, f in (('サイズ（目安）', 'size'), ('重さ（目安）', 'weight'), ('主な素材', 'mat'), ('動力・電源', 'power'), ('想定スペック', 'spec'))],
                    'feats': [j(x) for x in c['feats']], 'vars': [[j(a), j(b)] for a, b in c['vars']],
                    'check': [j(x) for x in c['check']], 'proto': j(c['proto']), 'mass': j(c['mass'])})
    return json.dumps(out, ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    import re
    for c in C:
        if c['kw']:
            re.compile(c['kw'])
    print(len(C), 'concepts,', len(T_CONCEPT), 'strings')
