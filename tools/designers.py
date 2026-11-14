"""設計の相談先（Nori 2026-11-14「設計を相談先もkatachiに入れましょう。ユーザの内容によってどこに相談したらいいかをレコメンドするようにして」）。

図面がない依頼は、工場がそのまま作れる製作図（部材の寸法・つなぎ方・強さ・公差）がないので、
多くの工場は「設計から受ける（設計費は別）」か「図面がないと見積できない」と答える（カブクの返答の実例）。
③「会社を選ぶ」で、図面がない依頼には「まず設計」の箱を出し、内容に合う相談先の種類を★で1つすすめる。

- 種類（TYPES）: 設計から作るまで受ける工場／製品設計の会社／電子機器の開発を受ける会社／工業デザインの事務所／
  型紙から受ける縫製工場／個人の設計者（ネットで頼む）／無料の公的な相談窓口。
- どれをすすめるかは template.html の dsPlan（電子部品の有無・大きさ・乗る重さ・素材の種類・数量・個人か）。
- 会社の行の形は data/companies.json と同じ（社名, 国, 都道府県, 市区町村, 公式サイト, 工程, 試作, 図面なし, 最小ロット, 材料, 確かさ, 概要, 出典URL, 確認日, 列14）。
  ここに書くのは手で集めた会社。ほかに企業DB（companies.json）から、種類ごとの条件（db_caps・db_re）に合う会社を画面で足す。
- 確かさ: 'pub' は公式サイト（または公的機関・会社自身の掲載ページ）で確かめた会社。'unk' は報道・記事だけ。
- 概要には出典に書いてあることだけを書く。図面なしで受けるか・個人の依頼を受けるかは、書いてなければ書かない（見積の依頼で確かめる）。
- 列14の proc: 手で集めた会社が受ける工程（設計込みの工場で、依頼の工程に合う会社を先に出すため）。ind: 個人の依頼を受けると書いてある。
- 受け持つ範囲（Nori 2026-11-14「工場に相談できるところもあるよね？」「それもわかるようにして」）: 列14の scope＝'design'（設計だけ）／'make'（設計から製作まで）／'install'（設置工事まで）。
  書いていない行は、種類の scope と概要の言葉（施工・据付・取付→install、製造・製作・加工・実装・量産・試作→make）で画面が決める（dsScope）。
- link: 会社ではなく「探す場所」の行（ココナラ・ランサーズ・よろず支援拠点など）。見積の送り先には入れず、ボタンで開く。
  公設試は都道府県ごとに違うので、届け先の都道府県の名前で検索するリンクにする（search=1）。
- 料金は書かない（公開された料金表の出典がないため）。
"""
import json

D = '2026-11-14'


def row(name, pref, city, web, lv, summary, src, x=None):
    return [name, 'JP', pref, city, web, [], 1, 1, None, None, lv, summary, src, D, dict({'ds': 1}, **(x or {}))]


def link(name, url, summary, src, search=0):
    return {'n': name, 'u': url, 's': summary, 'src': src, 'q': search}


TYPES = [
  {'k': 'fab', 'scope': 'make', 'name': '設計から作るまで受ける工場', 'short': '設計込みの工場',
   'good': '形と寸法を決めるところから作るまで1社。直しが出ても同じ会社で済みます。',
   'gets': '図面・作り方の提案・見積',
   # 企業DBから足す会社：概要に「設計〜製作・製造」「図面なし・手書き・スケッチから」などがあり、作る工程を持つ会社
   'db_re': r'(設計|デザイン)[^。、]{0,8}(製作|製造|加工|組立|組み立て|量産|一貫)|設計製作|図面(なし|がなくても|が無くても|不要)|手書き|ポンチ絵|スケッチ(から|をもと)|アイデアを(形|カタチ)',
   # 自社製品の「設計・製造・販売」だけの会社を外すため、受託の言葉もあること
   'db_need': r'受託|請負|オーダー|特注|別注|一品|1品|一点|1点|試作|要望|お客様|顧客|依頼|図面(なし|がなくても|が無くても|不要)|手書き|スケッチ|OEM|ODM|相談|設計製作|設計・製作',
   'db_not': r'プラント|半導体製造装置|自動車部品|発電|変電|鉄骨|橋梁|建築|土木|医薬品|医療機器',
   'rows': [
     row('株式会社フジムラ製作所', '埼玉県', '川口市', None, 'unk', '個人向けのフルオーダー金属製品「デジタルストラクチャー」。図面がなくても手書きのラフや写真から、同社の設計者が図面を作り1点から製作（レーザー切断・曲げ・溶接・塗装）。相談はLINE・専用フォーム',
         'https://monoist.itmedia.co.jp/mn/spv/2512/24/news005.html', {'ind': 1, 'proc': ['manufacturing.sheet_metal', 'crafts.metal_goods']}),
     row('株式会社浜野製作所', '東京都', '墨田区', 'https://hamano-products.co.jp/', 'pub', '3次元CADでの機械設計・製作、構想段階から試作・量産までの筐体設計・製造。精密板金・切削・金型プレス。スタートアップや新規事業のものづくりを多く支援',
         'https://hamano-products.co.jp/', {'proc': ['manufacturing.sheet_metal', 'manufacturing.cnc', 'mechanical', 'manufacturing.assembly']}),
     row('株式会社三松', '福岡県', '筑紫野市', 'https://www.sanmatsu.com/', 'pub', '技術営業・設計開発・機械加工・組立・品質保証まで。アイデアやスケッチからの依頼、1個からの注文に対応',
         'https://www.sanmatsu.com/', {'proc': ['manufacturing.cnc', 'manufacturing.sheet_metal', 'manufacturing.assembly', 'crafts.metal_goods']}),
     row('株式会社ユーバー', '大阪府', '八尾市', 'https://www.uber-corp.co.jp/', 'pub', '筐体・ケースの機構設計を加工に詳しい専任スタッフが担当し、試作から量産まで1台から対応。電源・ファンなどの組込配線も',
         'https://pr.mono.ipros.com/uber-corp/product/detail/2000247159/', {'proc': ['manufacturing.sheet_metal', 'mechanical.enclosure_design', 'manufacturing.assembly']}),
     row('株式会社カブク（Kabuku Connect）', None, None, 'https://www.kabuku.io/', 'pub', '切削・旋削・板金・製缶（溶接）・3Dプリント（金属・樹脂）の受託。簡易設計・図面化・リバースエンジニアリングにも対応',
         'https://www.kabuku.io/', {'proc': ['manufacturing.cnc', 'manufacturing.sheet_metal', 'manufacturing.rapid_proto', 'crafts.metal_goods']}),
   ]},
  {'k': 'inst', 'scope': 'install', 'name': '設計から設置工事まで受ける会社', 'short': '工事もする会社',
   'good': '庭・家・お店・車に据え付ける物は、設計・製作・取り付け工事まで1社に頼むと、寸法の食い違いが起きません。',
   'gets': '図面・作り方の提案・設置工事を含む見積',
   # 企業DBから足す会社：概要に「設計・製作・施工」「据付」「取付」などがあり、作る工程を持つ会社
   'db_re': r'(設計|製作|製造)[^。]{0,12}(施工|据付|据え付け|取付|取り付け|設置)|設計施工|設計・施工',
   'db_not': r'プラント|半導体|自動車|発電|変電|鉄骨|橋梁|土木|ガス|水処理|廃棄物|医薬品|医療機器|製鋼|圧延|タンク|貯槽|生産設備|生産ライン|工作機械|農業|畜産',
   'rows': [],
   'links': [
     link('ホームプロ（リフォーム会社の紹介）', 'https://www.homepro.jp/', '外構・エクステリア（ウッドデッキなど）を含むリフォームの工事会社を、匿名・無料で紹介してもらえます', 'https://www.homepro.jp/'),
     link('くらしのマーケット', 'https://curama.jp/', 'カーポート・宅配ボックスの設置や外構工事など、取り付け・設置の工事を地域の事業者に予約できます', 'https://curama.jp/'),
   ]},
  {'k': 'prod', 'scope': 'design', 'name': '製品設計の会社（形・しくみ）', 'short': '製品設計の会社',
   'good': '量産まで見すえて、形・しくみ・部品の分け方を決めます。あとで作り直しにくい物に向きます。',
   'gets': '3Dデータ・図面・部品表',
   'db_caps': ['mechanical.enclosure_design', 'mechanical.industrial_design'],
   'rows': [
     row('いなばテクノ・エボリューション株式会社', '鳥取県', '鳥取市', 'https://it-evo.jp/', 'pub', '機構・メカ設計（成形品・板金）、回路設計、ソフト開発、プロダクトデザイン。1台からの試作と評価、小ロットの量産',
         'https://mono.ipros.com/product/detail/2000813350'),
     row('株式会社フォルム', None, None, 'https://form.co.jp/', 'pub', '調査・企画、デザイン、CADでの設計（試作用の図面・金型に使える製品図面）、試作、金型・量産のサポートまで',
         'https://mono.ipros.com/product/detail/2000538616', {'scope': 'design'}),
     row('株式会社テクノラボ', None, None, None, 'unk', 'プラスチック筐体の設計・試作・金型・量産。IoT機器のスタートアップ向けに、メカ・デザインの開発費を定価表で示す受託開発（2019年の発表）',
         'https://monoist.itmedia.co.jp/mn/articles/1908/29/news028.html'),
   ]},
  {'k': 'elec', 'scope': 'make', 'name': '電子機器の開発を受ける会社', 'short': '電子機器の開発会社',
   'good': '回路・基板・中のソフトと、外の形を一緒に決めます。電子部品が入る物はここから。',
   'gets': '回路図・基板データ・ソフト・筐体の図面',
   'db_caps': ['electronics.pcb_design'], 'db_need': r'設計|開発',
   'rows': [
     row('株式会社倭技術研究所', None, None, None, 'pub', '電子回路設計・マイコンのファームウェア・筐体とパネルの設計から、部品調達・試作・小ロット製造・検査まで。仕様が固まる前の「初回相談・仕様整理」から受ける',
         'https://pr.mono.ipros.com/yamatogi/product/detail/2001226170/'),
     row('株式会社Braveridge', '福岡県', '福岡市', 'https://www.braveridge.com/', 'pub', 'IoT機器の企画・開発・製造をワンストップで支援（OEM・ODM・EMS）。自社の糸島工場',
         'https://www.braveridge.com/'),
     row('大和エレテック．株式会社', '奈良県', '生駒郡三郷町', None, 'pub', '電子機器の開発受託・実装・組立。開発設計から製造までの1工程からでも受ける',
         'https://www.ipros.com/company/detail/2064267/'),
     row('株式会社アレクソン', None, None, 'https://www.alexon.co.jp/', 'pub', '電子回路・プリント基板・組込みマイコン・筐体・アプリの受託開発。企画〜設計〜製造のワンストップでODM/OEM、試作から量産まで',
         'https://pr.mono.ipros.com/alexon/product/detail/2000542712/'),
     row('株式会社KYOWAエンジニアリング・ラボラトリー', None, None, 'https://www.kywo.co.jp/', 'pub', '基板設計・ソフトウェア開発・製品試作・3Dプリンタのモックアップ、試作品と小ロット製作',
         'https://mono.ipros.com/product/detail/2000407780'),
     row('JOHNAN DMS株式会社', None, None, 'https://www.johnan.com/dms/', 'pub', '電子部品・電子機器のアナログからデジタルまでの商品設計の技術支援。試作から量産まで一貫',
         'https://mono.ipros.com/product/detail/2001220551'),
     row('いなばテクノ・エボリューション株式会社', '鳥取県', '鳥取市', 'https://it-evo.jp/', 'pub', '回路設計（製品構想から試作・評価・量産まで）、機構・メカ設計、ソフト開発。1台からの試作',
         'https://mono.ipros.com/product/detail/2000813350'),
     row('P板.com（株式会社ピーバンドットコム）', None, None, 'https://www.p-ban.com/', 'pub', 'プリント基板の製造・実装と、回路設計・基板設計のサービス。試作やスポットの案件にも対応',
         'https://www.p-ban.com/'),
   ]},
  {'k': 'id', 'scope': 'design', 'name': '工業デザインの事務所', 'short': '工業デザイン',
   'good': '見た目・持ちやすさ・使い心地を決めます。売る商品で、見た目が大事なときに。',
   'gets': 'デザイン案・外観の3Dデータ',
   'db_caps': ['mechanical.industrial_design'],
   'rows': [
     row('株式会社フォルム', None, None, 'https://form.co.jp/', 'pub', '調査・企画、デザイン要件の整理、デザイン展開、設計・試作、金型・量産のサポートまで',
         'https://mono.ipros.com/product/detail/2000538616', {'scope': 'design'}),
   ],
   'links': [
     link('日本インダストリアルデザイン協会（JIDA）の会員', 'https://www.jida.or.jp/members', '工業デザイナー・デザイン事務所の団体。会員の一覧から探せます', 'https://www.jida.or.jp/'),
   ]},
  {'k': 'pattern', 'scope': 'make', 'name': '型紙（パターン）から受ける縫製工場', 'short': '型紙からの縫製工場',
   'good': '服・布もの・バッグは、型紙づくりから縫製まで同じ工場で受けるのがふつうです。',
   'gets': '型紙・仕様書・サンプル',
   'db_caps': ['apparel.garment_oem', 'apparel.leather'],
   'rows': []},
  {'k': 'free', 'scope': 'design', 'name': '個人の設計者（ネットで頼む）', 'short': '個人の設計者',
   'good': '小さな物・1点物の図面や3Dデータを、個人の設計者に頼めます。手軽に始めたいときに。',
   'gets': '3Dデータ・図面（工場の見積に使える形）',
   'rows': [],
   'links': [
     link('ココナラ「製品設計・プロダクトデザイン」', 'https://coconala.com/categories/671', 'アイデア・手書きのスケッチ・写真から、工場で使える3Dデータや見積用の図面を作る出品があります', 'https://coconala.com/services/3696546'),
     link('ランサーズ「プロダクトデザイン」', 'https://www.lancers.jp/menu/browse/graphics_design/product_design_services', '3D CADでの試作品の設計・モデリング、3Dプリント用データの出品があります', 'https://www.lancers.jp/menu/browse/graphics_design/product_design_services/blender'),
   ]},
  {'k': 'pub', 'scope': 'advice', 'name': '無料の公的な相談窓口', 'short': '無料の公的窓口',
   'good': '作り方や頼み先を、まず無料で相談できます。費用をかける前に方向を決めたいときに。',
   'gets': '作り方・頼み先の助言',
   'rows': [],
   'links': [
     link('工業技術センター（公設試）', 'https://www.google.com/search?q=', '都道府県の技術の相談窓口。試作・設計・デザインの相談、機器の利用、試験。相談は基本無料（予約制）', 'https://www.kansai.meti.go.jp/2giki/sangiren/susume/2023kousetsushinosusume.pdf', 1),
     link('よろず支援拠点', 'https://yorozu.smrj.go.jp/', '国が47都道府県に置く経営の相談所。中小企業・小規模事業者・創業予定の人が何度でも無料で相談できます', 'https://yorozu.smrj.go.jp/'),
   ]},
]

# 画面の文言（英語・中国語）。i18n.py が読み込む
T_DESIGN = {
  '設計から作るまで受ける工場': ('Factories that design and build', '从设计到制作都承接的工厂'),
  '設計込みの工場': ('Design-and-build factory', '含设计的工厂'),
  '形と寸法を決めるところから作るまで1社。直しが出ても同じ会社で済みます。': ('One company decides the shape and dimensions and then makes it. Any changes stay with the same company.', '从确定形状和尺寸到制作都由一家完成，需要修改时也由同一家处理。'),
  '図面・作り方の提案・見積': ('Drawings, a manufacturing proposal and a quote', '图纸、制作方法建议、报价'),
  '製品設計の会社（形・しくみ）': ('Product design firms (form and mechanism)', '产品设计公司（形状・结构）'),
  '製品設計の会社': ('Product design firm', '产品设计公司'),
  '量産まで見すえて、形・しくみ・部品の分け方を決めます。あとで作り直しにくい物に向きます。': ('They decide form, mechanism and how parts are split with mass production in mind. Good for things that are hard to redo later.', '着眼于量产，确定形状、结构和零件划分。适合以后难以返工的产品。'),
  '3Dデータ・図面・部品表': ('3D data, drawings, bill of materials', '3D数据・图纸・物料清单'),
  '電子機器の開発を受ける会社': ('Electronics development contractors', '承接电子设备开发的公司'),
  '電子機器の開発会社': ('Electronics developer', '电子设备开发公司'),
  '回路・基板・中のソフトと、外の形を一緒に決めます。電子部品が入る物はここから。': ('They design the circuit, board and firmware together with the outer shape. Start here if it has electronics inside.', '电路、电路板、内部软件和外形一起设计。含电子元件的产品从这里开始。'),
  '回路図・基板データ・ソフト・筐体の図面': ('Schematics, PCB data, firmware, enclosure drawings', '电路图・电路板数据・软件・外壳图纸'),
  '工業デザインの事務所': ('Industrial design studios', '工业设计事务所'),
  '工業デザイン': ('Industrial design', '工业设计'),
  '見た目・持ちやすさ・使い心地を決めます。売る商品で、見た目が大事なときに。': ('They decide the look, grip and feel. For products you sell where appearance matters.', '确定外观、握感和使用感。适合外观很重要的销售商品。'),
  'デザイン案・外観の3Dデータ': ('Design proposals and exterior 3D data', '设计方案・外观3D数据'),
  '型紙（パターン）から受ける縫製工場': ('Sewing factories that start from the pattern', '从纸样开始承接的缝制工厂'),
  '型紙からの縫製工場': ('Pattern-to-sewing factory', '从纸样开始的缝制工厂'),
  '服・布もの・バッグは、型紙づくりから縫製まで同じ工場で受けるのがふつうです。': ('For clothing, fabric goods and bags, the same factory usually makes the pattern and sews.', '服装、布制品和包，通常由同一家工厂从制作纸样到缝制都承接。'),
  '型紙・仕様書・サンプル': ('Pattern, spec sheet, sample', '纸样・规格书・样品'),
  '個人の設計者（ネットで頼む）': ('Freelance designers (online)', '个人设计师（网上委托）'),
  '個人の設計者': ('Freelance designer', '个人设计师'),
  '小さな物・1点物の図面や3Dデータを、個人の設計者に頼めます。手軽に始めたいときに。': ('Freelance designers can make drawings and 3D data for small or one-off items. An easy way to start.', '小物件、单件的图纸和3D数据可以委托个人设计师。适合想轻松开始时。'),
  '3Dデータ・図面（工場の見積に使える形）': ('3D data and drawings (ready for factory quotes)', '3D数据・图纸（可用于工厂报价）'),
  '無料の公的な相談窓口': ('Free public advisory centres', '免费的公共咨询窗口'),
  '無料の公的窓口': ('Free public advice', '免费公共窗口'),
  '作り方や頼み先を、まず無料で相談できます。費用をかける前に方向を決めたいときに。': ('Ask for free about how to make it and whom to ask. For deciding the direction before spending money.', '可以先免费咨询制作方法和委托对象。适合在花钱前确定方向。'),
  '作り方・頼み先の助言': ('Advice on how to make it and whom to ask', '关于制作方法和委托对象的建议'),
  '工業技術センター（公設試）': ('Prefectural industrial technology centre', '工业技术中心（公立试验研究机构）'),
  'よろず支援拠点': ('Yorozu Support Center', '万事支援据点（よろず支援拠点）'),
  '日本インダストリアルデザイン協会（JIDA）の会員': ('Members of the Japan Industrial Designers\' Association (JIDA)', '日本工业设计协会（JIDA）会员'),
  'ココナラ「製品設計・プロダクトデザイン」': ('coconala "Product design"', 'coconala「产品设计」'),
  'ランサーズ「プロダクトデザイン」': ('Lancers "Product design"', 'Lancers「产品设计」'),
  'まず設計': ('Design first', '先做设计'),
  '図面がないので、まず設計を頼みます': ('No drawings yet, so start by getting it designed', '还没有图纸，所以先委托设计'),
  '相談先の種類': ('Type of design partner', '咨询对象的类型'),
  '設計で受け取るもの：': ('What you get from design: ', '设计后拿到的东西：'),
  '選んだ会社には、見積の依頼で設計もあわせて頼みます。': ('Your quote request also asks the chosen company to do the design.', '在报价委托中，也会一并请所选公司做设计。'),
  'ここで作った図面・3Dデータは、見積の依頼にそのまま付けられます。': ('Drawings and 3D data made here can be attached to your quote request as they are.', '这里做好的图纸和3D数据可以直接附在报价委托中。'),
  'この工場にそのまま作ってもらうこともできます。': ('This factory can also go on to make it.', '也可以直接请这家工厂制作。'),
  '図面ができたら、下の会社が作ります。': ('Once the drawings are ready, the companies below make it.', '图纸完成后，由下面的公司制作。'),
  '設計（図面・3Dデータ）': ('Design (drawings, 3D data)', '设计（图纸・3D数据）'),
  '公式サイト ↗': ('Website ↗', '官网 ↗'),
  '報道・記事に掲載': ('Listed in news / articles', '见于报道・文章'),
  '電子部品が入るので、回路・基板・中のソフトと外の形を一緒に設計できる会社が向いています。': ('It has electronics inside, so a company that designs the circuit, board and firmware together with the outer shape suits it best.', '内含电子元件，适合能把电路、电路板、内部软件和外形一起设计的公司。'),
  '服・布もの・バッグは、型紙（パターン）づくりから縫製まで同じ工場に頼むのが近道です。': ('For clothing, fabric goods and bags, the shortest route is one factory that makes the pattern and sews.', '服装、布制品和包，最快的方式是请同一家工厂从制作纸样到缝制。'),
  '人や動物の重さがかかる物は、強さを計算して作り方まで考えられる工場に、設計から頼むのが安全です。': ('Things that carry the weight of people or animals are safest designed by a factory that can calculate strength and plan how to build it.', '要承受人或动物重量的东西，最安全的是从设计起就委托能计算强度、考虑制作方法的工厂。'),
  '大きい物は、作り方と運び方まで考えて設計するので、設計から作るまで受ける工場が向いています。': ('Large items need design that considers how they are built and transported, so a design-and-build factory suits them.', '大件物品的设计要考虑制作和运输方式，适合从设计到制作都承接的工厂。'),
  '金属・木の物は、加工を知っている工場が設計すると、作りやすく安い形になります。': ('Metal and wood items end up easier and cheaper to make when a factory that knows the processes designs them.', '金属、木制品由熟悉加工的工厂来设计，形状更易做、更便宜。'),
  '小さな物を少しだけ作るなら、個人の設計者に3Dデータを作ってもらい、試作で確かめるのが手軽です。': ('For a few small items, the easy route is to have a freelance designer make 3D data and check it with a prototype.', '少量制作小物件时，请个人设计师做3D数据再用试制确认，最省事。'),
  '数を作る物は、金型や量産の作り方まで考えて設計する会社に頼むと、あとで作り直さずに済みます。': ('For items made in quantity, a company that designs with moulds and mass production in mind saves you a redesign later.', '量产的东西，委托考虑到模具和量产方法来设计的公司，以后就不用返工。'),
  '工業デザイナー・デザイン事務所の団体。会員の一覧から探せます': ('Association of industrial designers and studios. Search its member list.', '工业设计师和设计事务所的团体。可在会员名单中查找'),
  'アイデア・手書きのスケッチ・写真から、工場で使える3Dデータや見積用の図面を作る出品があります': ('Listings that turn ideas, hand sketches or photos into factory-ready 3D data and drawings for quotes', '有根据创意、手绘草图、照片制作工厂可用的3D数据和报价用图纸的服务'),
  '3D CADでの試作品の設計・モデリング、3Dプリント用データの出品があります': ('Listings for 3D CAD prototype design, modelling and 3D-printing data', '有用3D CAD进行试制品设计、建模和3D打印数据的服务'),
  '都道府県の技術の相談窓口。試作・設計・デザインの相談、機器の利用、試験。相談は基本無料（予約制）': ('Prefectural technical advice centres: prototyping, design and styling advice, equipment use and testing. Consultations are basically free (by appointment).', '都道府县的技术咨询窗口。提供试制、设计咨询、设备使用和测试。咨询基本免费（需预约）'),
  '国が47都道府県に置く経営の相談所。中小企業・小規模事業者・創業予定の人が何度でも無料で相談できます': ('National business advice centres in all 47 prefectures. SMEs, small businesses and people planning to start one can consult for free as often as they like.', '国家在47个都道府县设立的经营咨询处。中小企业、小规模经营者和准备创业的人可多次免费咨询'),
  '設計から設置工事まで受ける会社': ('Companies that design, build and install', '从设计到安装施工都承接的公司'),
  '工事もする会社': ('Also installs', '也负责施工的公司'),
  '庭・家・お店・車に据え付ける物は、設計・製作・取り付け工事まで1社に頼むと、寸法の食い違いが起きません。': ('For things fixed to a garden, home, shop or vehicle, one company handling design, making and installation avoids size mismatches.', '固定在庭院、住宅、店铺或车上的东西，由一家公司负责设计、制作到安装，尺寸就不会对不上。'),
  '図面・作り方の提案・設置工事を含む見積': ('Drawings, a manufacturing proposal and a quote including installation', '图纸、制作方法建议、含安装施工的报价'),
  'ホームプロ（リフォーム会社の紹介）': ('HomePro (renovation contractor referrals)', 'HomePro（装修公司介绍）'),
  'くらしのマーケット': ('Kurashi no Market', 'Kurashi no Market（生活服务平台）'),
  '外構・エクステリア（ウッドデッキなど）を含むリフォームの工事会社を、匿名・無料で紹介してもらえます': ('Free, anonymous referrals to renovation contractors, including exterior work such as decks', '可匿名免费介绍包括外部构造（如木平台）在内的装修施工公司'),
  'カーポート・宅配ボックスの設置や外構工事など、取り付け・設置の工事を地域の事業者に予約できます': ('Book local contractors for installation work such as carports, parcel boxes and exterior work', '可向当地商家预约车棚、快递箱安装及外部构造等安装施工'),
  '受け持つ範囲': ('What they cover', '承接范围'),
  '設計': ('Design', '设计'),
  '製作': ('Making', '制作'),
  '設置工事': ('Installation', '安装施工'),
  '相談だけ（無料）': ('Advice only (free)', '仅咨询（免费）'),
  '設置・取り付けの工事が要る物は、2番目の「工事もする会社」から工事も受ける会社を選べます。': ('If it needs installation work, the second option "Also installs" lists companies that also do the installation.', '需要安装施工的东西，可以在第二个选项“包括安装施工”中选择也承接施工的公司。'),
  'この会社にそのまま作って取り付けてもらうこともできます。': ('This company can also go on to make and install it.', '也可以直接请这家公司制作并安装。'),
  '設計だけ': ('Design only', '仅设计'),
  '設計から製作まで': ('Design to making', '设计到制作'),
  '設計から設置工事まで': ('Design to installation', '设计到安装施工'),
  '設計を相談したい': ('I want design help', '想咨询设计'),
  '図面を作ってくれる相談先を、内容に合わせておすすめ': ('We recommend who can make your drawings, based on what you write', '根据内容推荐能帮你画图纸的咨询对象'),
  '作りたいものを書くだけ。図面を作ってくれる相談先（設計込みの工場・設計事務所・工事もする会社・無料の公的窓口など）を、内容に合わせて★でおすすめします。': ('Just describe what you want to make. We star the best place to get drawings made (design-and-build factories, design firms, companies that also install, free public advice and more) based on what you write.', '只需写下想做的东西。我们会根据内容用★推荐能帮你画图纸的咨询对象（含设计的工厂、设计事务所、也负责施工的公司、免费公共窗口等）。'),
  '何を作りたいですか？（例：家庭用プールに犬が入れるスロープ。大型犬2頭が乗る）': ('What do you want to make? (e.g. A ramp so dogs can get into a home pool. Two large dogs stand on it.)', '想做什么？（例：让狗能进入家用泳池的坡道，两只大型犬会站上去）'),
  '相談先を探す': ('Find design help', '查找咨询对象'),
  '設計の相談先': ('Where to get it designed', '设计咨询对象'),
  'この品は、作る会社が配合・処方から考えます': ('For this item, the maker works out the recipe or formula', '这类产品由生产公司从配方开始考虑'),
  '図面だけを先に頼む必要はありません。下のおすすめの会社に、そのまま相談してください。': ('There is no need to get drawings first. Talk directly to the recommended companies below.', '不需要先单独委托图纸，直接咨询下面推荐的公司即可。'),
  'この品は、専門のメーカーが設計から作ります': ('Specialist makers design and build this kind of item', '这类产品由专业厂家从设计开始制作'),
  '図面だけを先に頼む必要はありません。下のメーカーに、そのまま相談してください。': ('There is no need to get drawings first. Talk directly to the makers below.', '不需要先单独委托图纸，直接咨询下面的厂家即可。'),
}


def js():
    return json.dumps(TYPES, ensure_ascii=False)


if __name__ == '__main__':
    print(len(js()), sum(len(t['rows']) + len(t.get('links', [])) for t in TYPES))
