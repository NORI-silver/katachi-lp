"""作るものを思いつける入口（トップの作例ギャラリー）と、作例ごとの詳しいページ /idea/<k>/。

- 実在の他社事例ではなく「作例（モデルケース）」。実在企業の見積・口コミ・評価は作らない。
- 目安の数字は tools/estimates.py の出典つきの行（est: [工程コード, 行の文言]）だけを使う。期間は出典がないので出さない。
- カードの文言（t / d / lot）は (日本語, 英語, 中国語)。assemble.py が日本語だけを template.html の __IDEAS__ に入れ、
  i18n.py が T_IDEAS を辞書に足す。詳しいページ（/idea/）は日本語だけ（ガイドと同じ）。
- 許可・表示の説明は、出典つきで書いたガイド記事（tools/guides*.py）の内容に合わせ、そのガイドへリンクする。
- idea は「この内容で探す」で文章入力に入れる文。#match で工程が特定できる（フォールバックにならない）ことを確かめてから足す。
- 詳しいページは seo_pages.py が作る（python3 tools/seo_pages.py .）。
"""
import html, json, os

UPDATED = '2026-11-13'

IND = [
    ('pick', 'おすすめ', 'Recommended', '推荐'),
    ('pet', 'ペット用品・トリミング', 'Pet goods & grooming', '宠物用品・美容'),
    ('outdoor', 'アウトドア・キャンプ', 'Outdoor & camping', '户外・露营'),
    ('cafe', 'カフェ・飲食店', 'Cafés & restaurants', '咖啡馆・餐饮店'),
    ('salon', '美容室・サロン', 'Hair & beauty salons', '美发店・沙龙'),
    ('hotel', '宿泊・観光施設', 'Hotels & attractions', '住宿・观光设施'),
    ('shop', '小売・ネットショップ', 'Retail & online shops', '零售・网店'),
    ('farm', '農家・食品の店', 'Farms & food shops', '农户・食品店'),
    ('gym', 'ジム・スクール', 'Gyms & schools', '健身房・培训学校'),
    ('promo', '企業の販促・イベント', 'Company promotions & events', '企业促销・活动'),
    ('mfg', '町工場・製造業', 'Small factories & makers', '小工厂・制造业'),
    ('hw', 'ハードウェアのスタートアップ', 'Hardware startup', '硬件初创公司'),
]

# ---- 作り方の型（詳しいページの「作り方の流れ」「依頼前に決めること」「確かめる表示・許可」）
# check の中身は、リンク先のガイド記事（出典つき）に書いてあることだけ。
P = {
 'cosme': dict(
    ans='化粧品OEMの会社に、中身（処方）・容器・表示までまとめて相談するのが近道です。',
    steps=['化粧品OEMの会社に、作りたいもの・数量・売り方を伝えて相談する', 'すでにある処方から選ぶか、香りや使用感を変えるかを決め、サンプルで確かめる',
           '容器（既製か特注か）、ラベル、外箱を決める', '容器に書く表示（販売名・全成分・製造販売元など）を一緒に作る', '製造・充填して、納品を受ける'],
    decide=['種類と内容量（例：化粧水 150mL）', '最初に作る数と、その後の追加の見込み', '容器は既製品でよいか、特注にしたいか', '誰の名前で出すか（製造販売元をOEM先に頼むか）', '希望の発売時期'],
    check=['化粧品を市場に出すには「製造販売業」の許可が要ります。OEM先が製造販売元になれば、自社は発売元として売れます。',
           '容器には製造販売業者の名前と住所、販売名、製造番号、全成分などを日本語で書きます。',
           '化粧品で言える効能は決められた56項目の範囲です。「薬用」は医薬部外品で、化粧品の許可では扱えません。'],
    guides=['cosmetics-oem-license', 'cosmetics-oem-small-lot'], fig='bottle'),
 'household': dict(
    ans='雑貨・日用品のOEMを受ける会社に、中身と容器・ラベルをまとめて頼むのが近道です。',
    steps=['既製の中身や形から選ぶか、香り・色などを変えるかを決める', 'サンプルを作ってもらい、使い心地や香りを確かめる', '容器・ラベル・外箱を決める',
           '表示や注意書きを確かめる', '製造して納品を受ける'],
    decide=['中身・大きさ・香りや色', '最初に作る数', '容器や包装の形', '店頭で売るか、ネットで売るか', '希望の時期'],
    check=['人の体に使うもの（化粧品）か、雑貨か、動物に使うものかで、守る決まりが変わります。まずどれに当たるかをOEM先と確かめます。',
           '動物向けの品でも、病気の予防などをうたうと動物用医薬品等に当たり、許可や承認が要ります。',
           '店名やロゴを商品に使うなら、商標を確かめておきます。'],
    guides=['store-original-goods', 'small-lot-oem'], fig='bottle'),
 'food': dict(
    ans='作る品目の営業許可を持つ食品OEMの工場に、レシピや見本を渡して作ってもらうのが近道です。',
    steps=['作りたいもの・数量・売り方を伝え、品目に合う許可を持つ工場を探す', 'レシピや見本を渡し、工場で試作してもらう', '味・日持ち（賞味期限）・包装を決める',
           '原材料やアレルゲンなどの表示を一緒に作る', '製造して、納品を受ける'],
    decide=['中身と内容量（1袋・1個あたり）', '最初に作る数', '常温・冷蔵・冷凍のどれで売るか', '包装（袋・箱・瓶）とデザイン', '誰の名前で売るか（販売者として表示するか）'],
    check=['営業許可は製造する場所ごとに要ります。OEM先が、作る品目に合った許可（菓子製造業など）を持っているかを最初に確かめます。',
           '表示には「表示内容に責任を持つ者」の名前を書きます。製造者と合意すれば、販売者として自社の名前を書けます。',
           '常温で長期間保存できる包装食品を売るだけなら営業届出は不要です。冷蔵・冷凍品などは保健所に確認します。'],
    guides=['food-oem-license', 'food-oem-small-lot'], fig='pouch'),
 'supp': dict(
    ans='サプリメントのOEMを受ける工場に、形（粒・粉など）と原料から相談するのが近道です。',
    steps=['形（錠剤・カプセル・粉末など）と原料を工場と決める', '試作品で飲みやすさ・味を確かめる', '袋やボトルなど包材を決める', '表示と広告の言い方を確かめる', '製造して納品を受ける'],
    decide=['形と1日の量・1袋の量', '最初に作る数', '包材（袋・ボトル）', '機能を表示したいかどうか', '販売の時期'],
    check=['サプリは法律上は食品として扱われ、医薬品のような効能効果は書けません。',
           '機能を表示できるのは、特定保健用食品・栄養機能食品・機能性表示食品だけです。機能性表示食品は販売の60日前までに届出が要ります。',
           '最小ロットは、形、原料の最小購入量、包材の最小発注数で決まります。まとめて聞きます。'],
    guides=['supplement-oem-small-lot', 'food-oem-license'], fig='pouch'),
 'petfood': dict(
    ans='ペットフードを作れる工場に、原料・形・袋をまとめて相談するのが近道です。',
    steps=['原料・形（ジャーキー・クッキーなど）・1袋の量を工場と決める', '試作してもらい、食べつき・日持ちを確かめる', '袋とラベルを決める', '表示を一緒に作る', '製造して納品を受ける'],
    decide=['原料と形', '1袋の量と最初に作る数', '袋のデザイン', '販売者として名前を出すか', '販売の時期'],
    check=['犬・猫のペットフードは、名称・原材料名・賞味期限・製造業者等の名称と住所・原産国名の5つを日本語で表示する義務があります。',
           'ペットフードの製造業者・輸入業者は、事業を始める前に農政局などへの届出が必要です。',
           '病気の予防などをうたうと動物用医薬品等に当たり、許可や承認が要ります。'],
    guides=['pet-goods-oem', 'food-oem-small-lot'], fig='pouch'),
 'textile': dict(
    ans='既製品への名入れ（刺繍・プリント）なら小ロットで早く、形から作るなら縫製の工場に頼みます。',
    steps=['既製品に名入れするか、生地から作るかを決める', '生地・色・サイズ・ロゴの入れ方（刺繍・プリント）を決める', 'サンプルを1点作ってもらい確かめる', '数量を決めて製作する', '品質表示のタグを付けて納品を受ける'],
    decide=['形とサイズ（既製品の型番があれば伝える）', '色と生地', 'ロゴの入れ方・位置・色数', '最初に作る数', '売るか、使うか（配るか）'],
    check=['服やタオルなどの繊維製品を売るなら、組成・洗濯表示・表示者名の品質表示が必要です。',
           '店名やロゴをグッズに使うなら、商標を確かめておきます。',
           '買った人や来店者に配るなら、景品表示法の上限額に気をつけます。'],
    guides=['store-original-goods', 'apparel-oem-small-lot', 'goods-small-lot'], fig='bag'),
 'ceramic': dict(
    ans='既製のマグへの名入れ（転写・印刷）なら小ロットで始めやすく、形から作るなら陶磁器の工場に頼みます。',
    steps=['既製の形に名入れするか、形から作るかを決める', 'ロゴのデータと色・位置を決める', 'サンプルで色や仕上がりを確かめる', '製作して、検品・梱包してもらう', '納品を受ける'],
    decide=['形・大きさ（既製品の型番があれば伝える）', 'ロゴの色数と位置', '最初に作る数', '箱に入れるか', '売るか、配るか'],
    check=['食器など食品に触れる物は、食品衛生法の規格に合っているかを工場に確かめます（合成樹脂の物はポジティブリスト制度）。',
           '店名やロゴをグッズに使うなら、商標を確かめておきます。',
           '来店者などに配るなら、景品表示法の上限額に気をつけます。'],
    guides=['store-original-goods', 'goods-small-lot'], fig='mug'),
 'metal': dict(
    ans='既製品への刻印・名入れなら小ロットで早く、形から作るなら金属加工・金属雑貨の工場に頼みます。',
    steps=['既製品に刻印するか、形から作るかを決める', 'デザインのデータ（ロゴ・形）を用意する', 'サンプルで仕上がりを確かめる', '数量を決めて製作する', '検品・梱包して納品を受ける'],
    decide=['形・大きさ・素材（ステンレス・真鍮など）', 'ロゴの入れ方（刻印・印刷・色）', '最初に作る数', '包装', '売るか、配るか'],
    check=['食器など食品に触れる物は、食品衛生法の規格に合っているかを工場に確かめます。',
           '店名やロゴを使うなら商標を確かめておきます。配るノベルティは景品表示法の上限額に気をつけます。',
           'アウトドア用品は、品物によって安全の制度（PSCなど）の対象になります。対象かどうかを先に確かめます。'],
    guides=['goods-small-lot', 'outdoor-goods-oem', 'novelty-small-lot'], fig='cup'),
 'wood': dict(
    ans='木工の工場に、形・樹種・焼印のデータを渡して作ってもらうのが近道です。',
    steps=['形と大きさ、木の種類を決める', '焼印やレーザー刻印のロゴデータを用意する', 'サンプルで木目や仕上がりを確かめる', '数量を決めて製作する', '納品を受ける'],
    decide=['形・大きさ・厚み', '木の種類と仕上げ（オイルなど）', 'ロゴの入れ方', '最初に作る数', '売るか、配るか'],
    check=['食品に触れる物は、塗装や仕上げ材が食品に使えるものかを工場に確かめます。',
           '店名やロゴを使うなら商標を確かめておきます。'],
    guides=['outdoor-goods-oem', 'goods-small-lot'], fig='board'),
 'box': dict(
    ans='紙器・パッケージの会社に、形式・サイズ・印刷をまとめて頼むのが近道です。',
    steps=['箱の形式（キャラメル箱・貼り箱など）を決める', '中に入れる物に合わせてサイズを決める', 'デザインと印刷の色数を決める', '校正（色やレイアウトの確認）をする', '製造して納品を受ける'],
    decide=['箱の形式とサイズ', '印刷の有無と色数', '最初に作る数', '食品を直接入れるか', '納品の時期'],
    check=['食品を直接入れる箱か、袋に入れてから入れる箱かを伝えます。直接入れるなら、食品に触れて使える材料かを確かめます。',
           '店名やロゴを使うなら商標を確かめておきます。'],
    guides=['store-original-goods', 'sweets-oem-small-lot'], fig='box'),
 'sheet': dict(
    ans='手書きの絵や現物からでも、板金・切削の工場に図面化と試作をまとめて頼めます。',
    steps=['手書きの絵・現物・寸法のメモなど、手元にあるものを集める', '図面（CAD）にしてもらう、または自分で用意する', '試作して、使い心地や強さを確かめる', '形を直して、量産の数と方法を決める', '製作して納品を受ける'],
    decide=['大きさと材料（アルミ・ステンレス・鉄など）', '仕上げ（塗装・めっき・研磨など）', '試作の数と、量産の見込み', '図面や現物の有無', '希望の時期'],
    check=['アウトドア用品などは、品物によって安全の制度の対象になります。対象かどうかを先に確かめます。',
           '図面がなくても、寸法を書いた絵や現物で相談できます。'],
    guides=['sheet-metal-prototype', 'sheet-metal-quote', 'no-drawing'], fig='part'),
 'goods': dict(
    ans='グッズの制作会社に、データ（ロゴや絵）・大きさ・数をまとめて伝えるのが近道です。',
    steps=['作るグッズの種類と大きさを決める', 'ロゴや絵のデータを用意する（切り抜く線などの決まりを確かめる）', 'サンプルや校正で色と仕上がりを確かめる', '数量を決めて製作する', '包装・台紙を付けて納品を受ける'],
    decide=['種類・大きさ・素材', '色の数と入れ方', '最初に作る数', '包装（袋・台紙・箱）', '売るか、配るか'],
    check=['店名・社名・キャラクターを使うなら、商標や権利が自社にあるかを確かめておきます。',
           '買った人や来店者に配るノベルティは、景品表示法の上限額に気をつけます。'],
    guides=['goods-small-lot', 'novelty-small-lot'], fig='badge'),
 'iot': dict(
    ans='基板・ケース・組み込みソフト・アプリを、得意な会社に分けて頼むと進めやすくなります。',
    steps=['目的を確かめる小さな試作（PoC）の範囲を決める', '回路・基板の設計と実装を頼む', 'ケースを3Dプリントなどで試作する', '組み込みソフトとスマホアプリを作る', '組み立てて試し、量産向けの設計に進む'],
    decide=['測りたいもの・使う場所・電池の持ち', '試作の台数', '無線（Bluetoothなど）を使うか', 'アプリが要るか', '発売までの時期'],
    check=['無線を使うなら、技適を取ったモジュールを使うのが近道です。',
           'コンセントにつなぐ電源は電気用品安全法がかかわります。',
           'セキュリティには、2025年3月に始まったIoT製品のラベリング制度（JC-STAR）があります。'],
    guides=['iot-development', 'pcb-prototype'], fig='device'),
 'proto3d': dict(
    ans='1個からなら3Dプリントの出力サービスが早く、データがなければ設計から頼めます。',
    steps=['3Dデータがあるか確かめる（なければ絵と寸法で設計を頼む）', '方式と材料を選ぶ', '出力して、大きさやはまり具合を確かめる', '形を直して、もう一度試作する', '量産の方法（注型・金型）を考える'],
    decide=['大きさと、中に入れる物の寸法', '材料と色', '試作の数', '3Dデータの有無', '量産の見込み'],
    check=['3Dデータは STL などの形式で渡します。データがなくても、設計から頼める会社があります。'],
    guides=['3d-print-request', 'resin-prototype', '3d-print-cost'], fig='case'),
 'mold': dict(
    ans='数百個から先は、金型を作って射出成形にすると1個あたりが下がります。',
    steps=['試作の形をもとに、金型で作れる形に直す', '金型の種類（アルミ型・鉄の型）を数量で選ぶ', '金型を作り、最初の成形品（試し打ち）を確かめる', '必要なら金型を直す', '量産して納品を受ける'],
    decide=['作る数（最初と、その後の見込み）', '樹脂の種類と色', '3Dデータの有無', '金型をどこに置くか・持ち主は誰か', '希望の時期'],
    check=['金型代は数量で大きく変わります。金型の持ち主と保管の場所を契約で決めておきます。'],
    guides=['injection-molding-small-lot', 'resin-prototype'], fig='case'),
}

I_ = []
def I(k, ind, t, d, lot, q, code, idea, prof, why, tips, est=None, ex='', fig='', guides=(), pick=False):
    I_.append(dict(k=k, ind=ind, t=t, d=d, lot=lot, q=q, code=code, idea=idea, prof=prof, why=why, tips=tips,
                   est=est or [], ex=ex, fig=fig or P[prof]['fig'], guides=list(guides), pick=pick))

# ---------------- ペット
I('pet_shampoo', 'pet', ('自社ブランドの犬用シャンプー', 'Own-brand dog shampoo', '自有品牌狗狗香波'),
  ('サロンで使っている品を、自社のボトルとラベルで店頭・ネット販売', 'Sell the product you use in your salon, in your own bottle and label, in store and online', '把沙龙在用的产品换成自家瓶子和标签，在店里和网上销售'),
  ('300本', '300 bottles', '300瓶'), 'small', 'cosmetics.household',
  'トリミングサロンで使っている犬用シャンプーを、自社ブランドのボトルとラベルで300本作り、店頭とネットで販売したい',
  'household', 'トリミングサロンなら、ふだん使っているシャンプーを「お店と同じもの」として売れます。施術のあとに説明しやすく、リピートにつながります。',
  ['いま使っている品の成分や香りを伝えると、近い中身から始められます。', '業務用の大きいボトルと、販売用の小さいボトルを分けると売りやすくなります。', '「皮膚病に効く」などの言い方は使えません。'],
  fig='bottle', guides=['pet-goods-oem'], pick=True)
I('pet_treat', 'pet', ('国産素材の犬用おやつ', 'Dog treats from Japanese ingredients', '日本产原料的狗狗零食'),
  ('ジャーキーなどを自社ブランドの袋で', 'Jerky and more, in your own-brand bag', '肉干等，装进自有品牌包装袋'),
  ('500袋', '500 bags', '500袋'), 'small', 'food.pet_food',
  '国産の鶏肉を使った犬用ジャーキーを、自社ブランドの袋に入れて500袋作りたい',
  'petfood', 'おやつは試しに買いやすく、店頭やネットのついで買いにも向いています。原料の産地をそろえると、ほかの商品と違いを出せます。',
  ['袋の大きさは、内容量と店頭の置き場所の両方から決めます。', '賞味期限の長さで、作る数と売り切れる数を考えます。'],
  guides=['pet-goods-oem'])
I('pet_lead', 'pet', ('ロゴ入りのリードと首輪', 'Logo leashes and collars', '带logo的牵引绳和项圈'),
  ('色違いをそろえて、店のオリジナル商品に', "A range of colors as your shop's original product", '多种颜色，做成店铺原创商品'),
  ('各30本', '30 of each', '各30条'), 'small', 'apparel.leather',
  '店のロゴを入れた犬用のリードと首輪を、革で3色・各30本作りたい',
  'textile', 'リードと首輪は毎日使うもので、色違いをそろえると選ぶ楽しさが出ます。革や布の小物を作る工場なら、小ロットから相談できます。',
  ['金具（ナスカン・Dカン）の強さを、犬の大きさに合わせて確かめます。', 'サイズはS・M・Lなど少なめに絞ると、在庫が残りにくくなります。'],
  est=[['apparel.leather', '革小物・布小物のOEM']], fig='leash', guides=['pet-goods-oem', 'bag-oem'])
I('pet_collar', 'pet', ('健康を見守るスマート首輪', 'Smart collar that tracks health', '健康监测智能项圈'),
  ('センサー・基板・ケース・アプリを複数の会社で分担する作例', 'Example where several companies split the sensor, board, case and app', '由多家公司分工负责传感器、电路板、外壳和应用的示例'),
  ('試作5個', '5 prototypes', '试制5个'), 'proto', 'electronics.pcba', '',
  'iot', '1社ではそろわない技術を、得意な会社の組み合わせで形にする作例です。KATACHIでは工程ごとに会社を選んでチームを組めます。',
  ['首に着けたまま測れるか、防水と電池の持ちを最初の試作で確かめます。', '動物で試す工程を受ける会社も候補に入れます。'],
  ex='collar', fig='device', guides=['pet-goods-oem'])
# ---------------- アウトドア
I('out_cup', 'outdoor', ('刻印入りのシェラカップ', 'Engraved camping cups', '刻印露营杯'),
  ('キャンプ場の売店や自社ブランドのグッズに', 'For a campsite shop or your own brand', '用于露营地商店或自有品牌周边'),
  ('100個', '100 units', '100个'), 'small', 'crafts.metal_goods',
  'キャンプ場のロゴを刻印したステンレスのシェラカップを100個作り、売店で販売したい',
  'metal', 'シェラカップはキャンプの定番で、ロゴを刻印するだけでオリジナルの記念品になります。既製品への刻印なら小ロットで始めやすい品です。',
  ['刻印の位置（内側・外側・持ち手）で見え方が変わります。', '直火にかける使い方を想定するなら、素材と仕上げを工場に伝えます。'],
  fig='cup', guides=['outdoor-goods-oem'], pick=True)
I('out_case', 'outdoor', ('帆布のペグケース', 'Canvas tent-peg case', '帆布地钉收纳袋'),
  ('縫製の工場で小ロットから', 'Small batches from a sewing factory', '缝制工厂小批量起做'),
  ('100個', '100 units', '100个'), 'small', 'manufacturing.textile',
  '帆布を縫って作るテント用のペグ入れの袋を、自社ブランドで100個作りたい',
  'textile', 'ペグケースは形が単純で、縫製の工場に頼みやすい品です。帆布の色やロゴのタグで、ブランドらしさを出せます。',
  ['入れるペグの長さと本数から、袋の大きさを決めます。', '底や口の部分は傷みやすいので、補強の方法を相談します。'],
  fig='bag', guides=['outdoor-goods-oem', 'bag-oem'])
I('out_hanger', 'outdoor', ('アルミのランタンハンガー', 'Aluminum lantern hanger', '铝制营灯挂架'),
  ('まず数個試作して、使い心地を確かめてから', 'Prototype a few first and try them out', '先试制几个，确认使用感'),
  ('試作5個', '5 prototypes', '试制5个'), 'proto', 'manufacturing.sheet_metal',
  'アルミの板を曲げて作るキャンプ用のランタンハンガーを、まず5個試作したい。よければ300個作りたい',
  'sheet', '板を曲げて作る道具は、板金の工場なら1個から試作できます。使ってみて直してから数を増やせるので、小さく始められます。',
  ['吊るす重さ（ランタンの重さ）を伝えて、板の厚みを決めます。', '角の丸めや表面の仕上げ（アルマイトなど）で見た目と触り心地が変わります。'],
  est=[['manufacturing.sheet_metal', '1個の価格例（アルミ・鉄・ステンレスの曲げ品など）'], ['manufacturing.sheet_metal', '最低ロット']],
  fig='hook', guides=['outdoor-goods-oem'])
I('out_board', 'outdoor', ('焼印入りの木製カッティングボード', 'Branded wooden cutting board', '烙印木质砧板'),
  ('キャンプ用品やギフトに', 'As camping gear or a gift', '作为露营用品或礼品'),
  ('100枚', '100 pieces', '100件'), 'small', 'crafts.wood_furniture',
  'キャンプで使う木製のカッティングボードに、ロゴの焼印を入れて100枚作りたい',
  'wood', '木のカッティングボードは料理を盛る皿にもなり、焼印を入れるとギフトにも向きます。',
  ['持ち手の穴や形で、吊るして飾れるようにすると売り場で目立ちます。', '木の種類で重さと値段が変わります。'],
  fig='board', guides=['outdoor-goods-oem'])
# ---------------- カフェ
I('cafe_mug', 'cafe', ('店のロゴ入りマグカップ', 'Mugs with your shop logo', '印有店铺logo的马克杯'),
  ('店頭販売にも、常連さんへの記念品にも', 'To sell in store or give to regulars', '既可店内销售，也可送给常客做纪念'),
  ('100個', '100 units', '100个'), 'small', 'crafts.ceramics_glass',
  '自分のカフェのロゴを入れた陶器のマグカップを100個作り、店頭で販売したい',
  'ceramic', 'お店で実際に使っているマグをそのまま売ると、お客さんに説明しなくても伝わります。既製のマグへの名入れなら小ロットで始めやすい品です。',
  ['お店で使う分と販売する分をまとめて作ると、1個あたりが下がりやすくなります。', '電子レンジ・食洗機に使えるかを、売るときに書けるよう確かめます。'],
  fig='mug', pick=True)
I('cafe_sweets', 'cafe', ('人気の焼き菓子を通販・ギフトに', 'Your popular baked goods for mail order and gifts', '把人气烘焙点心做成网购和礼品'),
  ('店のレシピをもとに、食品の工場で作ってもらう', 'Have a food factory make them from your recipe', '按店铺配方，请食品工厂生产'),
  ('300個', '300 units', '300个'), 'small', 'food.processed_oem',
  '店で人気のクッキーを、食品の工場で作ってもらい、通販とギフト用に300個販売したい',
  'food', 'お店で焼ける数には限りがあります。人気の品を工場で作ってもらうと、通販やギフトに広げられます。',
  ['お店の味を工場の設備で再現するため、試作で何度か味を合わせます。', '日持ちを伸ばすと配送しやすくなりますが、レシピの見直しが要ることがあります。'],
  est=[['food.processed_oem', '菓子']], fig='sweets', guides=['sweets-oem-small-lot', 'restaurant-product-oem'])
I('cafe_box', 'cafe', ('焼き菓子のギフト箱', 'Gift boxes for baked goods', '烘焙点心礼盒'),
  ('ロゴを印刷した化粧箱を小ロットで', 'Printed logo boxes in small batches', '小批量印刷logo的包装盒'),
  ('200個', '200 units', '200个'), 'small', 'packaging.box',
  '焼き菓子の詰め合わせに使う、ロゴを印刷した化粧箱を200個作りたい',
  'box', 'ロゴ入りの箱があるだけで、同じ焼き菓子でも贈り物として選ばれやすくなります。',
  ['箱の中の仕切りや、個包装の数に合わせてサイズを決めます。', '季節ごとにシールや帯を変えると、箱は同じまま使い回せます。'],
  est=[['packaging.box', 'キャラメル箱 50個（印刷あり）']], fig='box')
I('cafe_apron', 'cafe', ('ロゴを刺繍したエプロン', 'Aprons with an embroidered logo', '刺绣logo的围裙'),
  ('スタッフの制服や、物販のグッズに', 'As staff uniforms or merchandise', '用作员工制服或周边商品'),
  ('30枚', '30 pieces', '30件'), 'small', 'manufacturing.textile',
  '店のロゴを刺繍したスタッフ用のエプロンを30枚作りたい',
  'textile', 'スタッフが着けているエプロンは、お店の印象を決めます。既製のエプロンへの刺繍なら少ない数から作れます。',
  ['汚れやすい色・洗濯の回数を考えて生地を選びます。', 'お客さん向けに売るなら、品質表示のタグが要ります。'],
  fig='cloth', guides=['uniform-custom'])
# ---------------- サロン
I('salon_lotion', 'salon', ('サロン専売の化粧水', 'Salon-exclusive lotion', '沙龙专售化妆水'),
  ('自社ブランドのスキンケアを店頭で', 'Your own skincare brand in store', '在店里销售自有品牌护肤品'),
  ('100本', '100 bottles', '100瓶'), 'small', 'cosmetics.oem',
  'サロン専売の自社ブランドの化粧水を100本作り、店頭で販売したい',
  'cosme', '施術で使った化粧水をそのまま持ち帰ってもらえると、ホームケアとして続けて買ってもらえます。',
  ['施術で使う業務用と、販売用の容量を分けて考えます。', '香りや使用感は、サンプルを何人かで試して決めます。'],
  est=[['cosmetics.oem', '化粧水・美容液・乳液'], ['cosmetics.oem', '化粧水・美容液など 100個〜']], guides=['salon-original-cosmetics', 'lotion-oem'], pick=True)
I('salon_shampoo', 'salon', ('自社ブランドのシャンプー', 'Own-brand shampoo', '自有品牌洗发水'),
  ('香りや容器を選んで、オリジナルのヘアケアに', 'Choose the scent and bottle for your original hair care', '选择香味和容器，做成原创护发产品'),
  ('300本', '300 bottles', '300瓶'), 'small', 'cosmetics.oem',
  '美容室の自社ブランドとして、シャンプーとトリートメントを各300本作りたい',
  'cosme', 'シャンプーは毎日使うので、気に入ってもらえれば続けて買ってもらえます。美容室なら、髪の状態に合わせて説明して売れます。',
  ['シャンプーとトリートメントを同じ香りでそろえると、セットで売りやすくなります。', '「薬用」とうたうなら医薬部外品になり、化粧品とは別の手続きです。'],
  guides=['salon-original-cosmetics', 'shampoo-oem'])
I('salon_candle', 'salon', ('店の香りのアロマキャンドル', "Candles with your shop's scent", '店铺香味的香薰蜡烛'),
  ('店内の香りをそのまま持ち帰れる物販に', "Let customers take your shop's scent home", '让顾客把店里的香味带回家'),
  ('100個', '100 units', '100个'), 'small', 'cosmetics.household',
  'サロンの香りに合わせたアロマキャンドルを100個作り、店頭で販売したい',
  'household', '「お店のいい香り」を持ち帰れる品は、説明しなくても体験が伝わります。',
  ['容器（ガラス・缶）と燃える時間で値段が変わります。', '火を使う品なので、使い方の注意書きを付けます。'],
  fig='candle')
I('salon_towel', 'salon', ('ロゴ入りのタオル', 'Logo towels', '带logo的毛巾'),
  ('施術用にも、物販にも', 'For treatments and for sale', '既可用于服务，也可销售'),
  ('100枚', '100 pieces', '100件'), 'small', 'manufacturing.textile',
  'サロンのロゴを刺繍したタオルを100枚作りたい',
  'textile', 'タオルは施術で毎日使い、ロゴが入っていると写真に写ったときにもお店が伝わります。',
  ['施術用は洗濯に強い厚み、販売用は手触りを優先するなど、用途で分けます。', 'ロゴは刺繍か、織りで入れるかで最低ロットが変わります。'],
  fig='cloth')
# ---------------- 宿泊・観光
I('hotel_soap', 'hotel', ('オリジナルの固形石けん', 'Original bar soap', '原创固体香皂'),
  ('客室のアメニティや、お土産に', 'As room amenities or souvenirs', '用作客房用品或伴手礼'),
  ('300個', '300 units', '300个'), 'small', 'cosmetics.oem',
  '旅館オリジナルの化粧石けん（固形）を化粧品の工場で300個作り、客室のアメニティと売店で使いたい',
  'cosme', '客室で使った石けんを売店でも買えるようにすると、旅の思い出として持ち帰ってもらえます。',
  ['地元の素材を入れる場合は、使えるかどうかと量を工場に相談します。', '客室用の小さいサイズと、お土産用の箱入りを分けて考えます。'],
  est=[['cosmetics.oem', '固形石けん']], fig='soap', guides=['soap-oem'], pick=True)
I('hotel_sweets', 'hotel', ('ご当地のお菓子のお土産', 'Local sweets as souvenirs', '当地特色点心伴手礼'),
  ('地元の素材を使って、売店のオリジナル品に', "Use local ingredients for your shop's own product", '使用当地食材，做成商店原创商品'),
  ('300個', '300 units', '300个'), 'small', 'food.processed_oem',
  '地元の果物を使ったオリジナルのお菓子を、旅館の売店のお土産として300個作りたい',
  'food', '宿や施設の名前が入ったお菓子は、ここでしか買えないお土産になります。',
  ['持ち帰りや配送を考えて、日持ちのするお菓子を選びます。', '地名や「◯◯産」を書くときの決まりを確かめます。'],
  est=[['food.processed_oem', '菓子']], fig='sweets', guides=['souvenir-oem', 'sweets-oem-small-lot'])
I('hotel_slipper', 'hotel', ('ロゴ入りの館内スリッパ', 'Logo slippers for guests', '带logo的馆内拖鞋'),
  ('客室用に、刺繍やプリントで', 'For guest rooms, embroidered or printed', '客房用，刺绣或印花'),
  ('200足', '200 pairs', '200双'), 'small', 'manufacturing.textile',
  'ホテルのロゴを刺繍した客室用のスリッパを200足作りたい',
  'textile', '客室で使うスリッパにロゴが入っていると、館内の統一感が出ます。',
  ['使い捨てか、洗って使うかで素材が変わります。', 'サイズは男女兼用の1サイズか、2サイズにするかを決めます。'],
  fig='slipper')
I('hotel_pin', 'hotel', ('施設のピンバッジ', 'Pin badges for your venue', '设施徽章'),
  ('記念品や、スタッフの名札に', 'As keepsakes or staff name badges', '用作纪念品或员工名牌'),
  ('300個', '300 units', '300个'), 'small', 'crafts.metal_goods',
  '観光施設のロゴを入れた金属のピンバッジを300個作り、売店で販売したい',
  'goods', 'ピンバッジは小さくて持ち帰りやすく、集める人も多い記念品です。',
  ['色の数と、色を入れる方法（七宝・印刷）で見た目と値段が変わります。', '台紙に付けて売ると、袋に入れるより目立ちます。'],
  fig='badge', guides=['goods-small-lot'])
# ---------------- 小売・ネットショップ
I('shop_tshirt', 'shop', ('オリジナルのTシャツ', 'Original T-shirts', '原创T恤'),
  ('無地にプリントするなら10枚から', 'From 10 if printed on blanks', '在素色T恤上印花10件起'),
  ('50枚', '50 pieces', '50件'), 'small', 'apparel.print_embroidery',
  '店のロゴを1色でプリントしたオリジナルのTシャツを50枚作り、ネットショップで販売したい',
  'textile', '無地のTシャツにプリントする方法なら、少ない枚数から作れて、売れたら追加もしやすい品です。',
  ['色数を増やすと版代と単価が上がります。最初は1色がおすすめです。', 'サイズごとの枚数は、売り先の客層から決めます。'],
  est=[['apparel.print_embroidery', 'Tシャツ片面1色シルク印刷 10枚'], ['apparel.print_embroidery', '同 100枚']], fig='shirt', guides=['apparel-oem-small-lot'], pick=True)
I('shop_tote', 'shop', ('ロゴ入りの帆布トートバッグ', 'Logo canvas tote bags', '带logo的帆布托特包'),
  ('ショップ袋代わりにも、商品にも', 'As a shopping bag or as a product', '既可当购物袋，也可作商品'),
  ('100枚', '100 pieces', '100件'), 'small', 'manufacturing.textile',
  '店のロゴを印刷した帆布のトートバッグを100枚作りたい',
  'textile', 'トートバッグは持ち歩くたびにお店の名前が人目に触れます。販売にも、まとめ買いの特典にも使えます。',
  ['既製のトートに印刷するか、形から作るかで最低ロットが大きく変わります。', 'マチの有無と持ち手の長さで使い勝手が変わります。'],
  fig='bag', guides=['bag-oem'])
I('shop_sweets', 'shop', ('自社ブランドのお菓子', 'Own-brand sweets', '自有品牌点心'),
  ('パッケージまでそろえてネットで販売', 'Complete with packaging, sold online', '连包装一起做好，在网上销售'),
  ('300個', '300 units', '300个'), 'small', 'food.processed_oem',
  '自社ブランドの焼き菓子を、パッケージも含めて300個作り、ネットショップで販売したい',
  'food', '工場が持っているレシピをもとに、パッケージを自社ブランドにして売る方法なら、少ない数から始めやすくなります。',
  ['工場の既存の品を使うか、オリジナルのレシピにするかで試作の回数が変わります。', '配送で割れないよう、個包装と箱を決めます。'],
  est=[['food.processed_oem', '菓子']], fig='sweets', guides=['sweets-oem-small-lot'])
I('shop_supp', 'shop', ('自社ブランドのサプリメント', 'Own-brand supplements', '自有品牌保健品'),
  ('粒・粉などの形と原料から相談', 'Start from the form (tablet, powder) and ingredients', '从片剂、粉末等形态和原料开始咨询'),
  ('1,000袋', '1,000 bags', '1,000袋'), 'mass', 'food.beverage_oem',
  '自社ブランドのサプリメント（粒タイプ）を1,000袋作り、ネットショップで販売したい',
  'supp', 'サプリメントは、形と原料を選べば工場の持っている処方から作れることが多い品です。売り方と表示の決まりを先に確かめます。',
  ['広告で言えることの範囲を、作る前に確かめておきます。', '原料の最小購入量で、最初の数が決まることがあります。'],
  fig='pouch')
# ---------------- 農家・食品
I('farm_juice', 'farm', ('自家栽培の果物でジュース', 'Juice from fruit you grow', '用自家种植的水果做果汁'),
  ('規格外の果物を、瓶詰めの商品に', 'Turn off-grade fruit into a bottled product', '把不合规格的水果做成瓶装商品'),
  ('500本', '500 bottles', '500瓶'), 'small', 'food.beverage_oem',
  '自分の農園で採れたりんごでジュースを作り、瓶詰めで500本販売したい',
  'food', '形が悪くて売れない果物も、ジュースにすれば商品になります。果物を持ち込んで加工してもらう工場もあります。',
  ['持ち込む果物の量から、できる本数を工場に計算してもらいます。', '瓶の大きさで、最小ロットが変わります。'],
  est=[['food.beverage_oem', '500mlびん'], ['food.beverage_oem', '200mlびん']], fig='bottle', guides=['food-oem-small-lot'], pick=True)
I('farm_jam', 'farm', ('果物のジャム', 'Fruit jam', '水果果酱'),
  ('加工を任せて、直売所やネットで', 'Outsource processing and sell at your stand or online', '委托加工，在直销点或网上销售'),
  ('300個', '300 units', '300个'), 'small', 'food.processed_oem',
  '自分の農園のいちごでジャムを作り、瓶詰めで300個販売したい',
  'food', 'ジャムは旬の果物を長く売れる形にでき、直売所やネットのギフトにも向いています。',
  ['糖度と日持ちの関係を工場に相談して、レシピを決めます。', '瓶とふたのデザインで、店頭での見え方が変わります。'],
  fig='jar', guides=['food-oem-small-lot'], pick=True)
I('farm_dry', 'farm', ('規格外野菜のドライ野菜', 'Dried vegetables from off-grade produce', '用不合规格蔬菜做的蔬菜干'),
  ('捨てていた野菜を、日持ちする商品に', 'Turn vegetables you threw away into a long-lasting product', '把原本丢弃的蔬菜做成耐储存的商品'),
  ('300袋', '300 bags', '300袋'), 'small', 'food.processed_oem',
  '規格外の野菜を加工食品の工場で乾燥させ、ドライ野菜として袋詰めで300袋作り販売したい',
  'food', '乾燥させると日持ちが伸び、軽くて送りやすくなります。捨てていた野菜を商品に変えられます。',
  ['乾燥すると重さが大きく減るので、必要な野菜の量を工場に計算してもらいます。', '袋の中の湿気を防ぐ包装を選びます。'],
  fig='pouch', guides=['food-oem-small-lot'])
I('farm_box', 'farm', ('贈答用のギフト箱', 'Gift boxes', '赠礼用礼盒'),
  ('果物や加工品の詰め合わせに', 'For fruit or processed-food assortments', '用于水果或加工品组合'),
  ('1,000個', '1,000 units', '1,000个'), 'mass', 'packaging.box',
  '果物の贈答用に、農園の名前を入れたギフト箱を1,000個作りたい',
  'box', '農園の名前が入った箱は、贈り物として選ばれる理由になります。',
  ['果物の大きさと数に合わせて、中の仕切りを決めます。', '無地の箱にシールや印刷を足す方法なら、費用を抑えられます。'],
  est=[['packaging.box', '無地のギフト箱 1,000個']], fig='box')
# ---------------- ジム・スクール
I('gym_wear', 'gym', ('ロゴ入りのトレーニングウェア', 'Logo training wear', '带logo的训练服'),
  ('会員向けの物販や、スタッフのウェアに', 'For member merchandise or staff wear', '用于会员周边或员工服装'),
  ('30枚', '30 pieces', '30件'), 'small', 'apparel.garment_oem',
  'ジムのロゴを入れたトレーニング用のTシャツを、吸汗速乾の生地で30枚作って会員に販売したい',
  'textile', '会員がジムのウェアを着ていると、仲間意識が生まれ、外でもジムの名前が伝わります。',
  ['汗を吸う生地か、伸びる生地かなど、運動の種類から生地を選びます。', '既製のスポーツウェアへのプリントなら、少ない数から作れます。'],
  est=[['apparel.garment_oem', 'スポーツウェア']], fig='shirt', guides=['sportswear-oem'], pick=True)
I('gym_towel', 'gym', ('ロゴ入りのスポーツタオル', 'Logo sports towels', '带logo的运动毛巾'),
  ('入会の記念品や、物販に', 'As a welcome gift or merchandise', '用作入会礼品或周边商品'),
  ('100枚', '100 pieces', '100件'), 'small', 'manufacturing.textile',
  'ジムのロゴを入れた細長いスポーツタオルを100枚作りたい',
  'textile', 'スポーツタオルは毎回の運動で使い、入会の記念品にも向いています。',
  ['ロゴを刺繍・プリント・織りのどれで入れるかで、最低ロットが変わります。', '色をジムのイメージカラーにそろえると目立ちます。'],
  fig='cloth')
I('gym_bottle', 'gym', ('名入れのステンレスボトル', 'Engraved stainless bottles', '刻名不锈钢水杯'),
  ('会員の記念品や、物販に', 'As member gifts or merchandise', '用作会员纪念品或周边商品'),
  ('100本', '100 bottles', '100瓶'), 'small', 'crafts.metal_goods',
  'ジムのロゴを刻印したステンレスのボトルを100本作り、会員に販売したい',
  'metal', 'ボトルはトレーニング中に必ず手に取るもので、ロゴが自然に目に入ります。既製品への名入れなら小ロットで作れます。',
  ['保冷・保温の有無と容量を決めます。', '飲み物を入れる物なので、食品に触れる部分の素材を確かめます。'],
  fig='cup')
I('gym_bag', 'gym', ('教室のレッスンバッグ', 'Lesson bags for your school', '培训班课程包'),
  ('習い事の生徒さん向けのオリジナル品に', 'An original item for your students', '为学员定制的原创商品'),
  ('50枚', '50 pieces', '50件'), 'small', 'manufacturing.textile',
  '習い事の教室のロゴを入れたレッスンバッグを、生徒向けに50枚作りたい',
  'textile', '同じバッグを持つと、教室の一員という気持ちが生まれ、送り迎えのときに名前も伝わります。',
  ['入れる物（楽譜・道着・シューズ）の大きさから、形とマチを決めます。', '子ども向けなら、名前を書けるタグを付けると喜ばれます。'],
  fig='bag', guides=['bag-oem'])
# ---------------- 企業の販促・イベント
I('promo_ecobag', 'promo', ('社名入りのエコバッグ', 'Eco bags with your company name', '印有公司名的环保袋'),
  ('展示会やキャンペーンで配るノベルティに', 'A giveaway for trade shows and campaigns', '展会和活动中派发的赠品'),
  ('300枚', '300 pieces', '300件'), 'small', 'manufacturing.textile',
  '展示会で配る、社名を印刷したエコバッグを300枚作りたい',
  'textile', 'エコバッグは受け取った人が普段使いしやすく、社名を長く見てもらえるノベルティです。',
  ['配る相手と場面から、大きさと生地を決めます。', '購入を条件に配るなら、景品表示法の上限額を確かめます。'],
  fig='bag', guides=['novelty-small-lot'], pick=True)
I('promo_sweets', 'promo', ('社名入りのお菓子', 'Sweets with your company name', '印有公司名的点心'),
  ('来場者へのお礼や、周年の記念品に', 'To thank visitors or mark an anniversary', '用于答谢来宾或周年纪念'),
  ('500個', '500 units', '500个'), 'small', 'food.processed_oem',
  '会社の周年記念で配る、社名を印刷した個包装の焼き菓子を500個作りたい',
  'food', '食べてなくなるお菓子は受け取る側の負担が少なく、パッケージに社名やメッセージを入れられます。',
  ['工場の既存の焼き菓子に、オリジナルの包装を付ける方法なら早く作れます。', '配る日から逆算して、賞味期限に余裕を持たせます。'],
  est=[['food.processed_oem', '菓子']], fig='sweets', guides=['novelty-small-lot', 'sweets-oem-small-lot'])
I('promo_plaque', 'promo', ('記念品の金属プレート', 'Commemorative metal plaques', '纪念金属牌'),
  ('表彰や周年の記念に', 'For awards or anniversaries', '用于表彰或周年纪念'),
  ('30個', '30 units', '30个'), 'small', 'crafts.metal_goods',
  '社内表彰の記念品として、名前を刻印した真鍮のプレートを30個作りたい',
  'goods', '名前を刻印したプレートは、表彰や周年の記念に長く残る品です。',
  ['一人ずつ名前を変える場合は、データの渡し方を工場と決めます。', '台座や箱を付けるかで見栄えと値段が変わります。'],
  fig='badge')
I('promo_acrylic', 'promo', ('キャラクターのアクリルスタンド', 'Character acrylic stands', '角色亚克力立牌'),
  ('イベントの物販や、ファン向けのグッズに', 'For event merchandise or fan goods', '用于活动周边或粉丝商品'),
  ('100個', '100 units', '100个'), 'small', 'cosmetics.household',
  '自社のキャラクターのアクリルスタンドを100個作り、イベントで販売したい',
  'goods', 'アクリルスタンドは絵のデータがあれば作れ、小ロットから頼めるグッズです。',
  ['絵のデータは、切り抜く線（カットライン）を付けて渡します。', 'キャラクターの権利が自社にあるかを確かめておきます。'],
  fig='badge', guides=['goods-small-lot'])
# ---------------- 町工場
I('mfg_fire', 'mfg', ('自社の加工技術で作る焚き火台', 'Fire pit made with your own machining skills', '用自家加工技术做的焚火台'),
  ('下請けの技術を、自社ブランドの商品に', 'Turn subcontracting skills into your own-brand product', '把代工技术变成自有品牌商品'),
  ('試作3個', '3 prototypes', '试制3个'), 'proto', 'manufacturing.cnc',
  '自社の板金と切削の技術を使って、キャンプ用の焚き火台を自社ブランドで作りたい。まず3個試作したい',
  'sheet', '下請けで磨いた加工の技術は、そのまま自社の商品の強みになります。足りない工程（塗装・梱包・販売）だけを外に頼めます。',
  ['自社でできる工程と、外に頼む工程を分けて考えます。', '火を使う品なので、熱による変形と安全の確かめ方を決めます。'],
  est=[['manufacturing.cnc', '1個の価格例（50mm角の樹脂〜200mmのステンレス）'], ['manufacturing.cnc', '最低ロット']],
  fig='fire', guides=['subcontractor-own-product', 'outdoor-goods-oem'], pick=True)
I('mfg_scrap', 'mfg', ('端材で作る金属の雑貨', 'Metal goods from offcuts', '用边角料做的金属杂货'),
  ('栓抜き・キーホルダーなど、捨てていた材料を商品に', 'Bottle openers, key rings: turn scrap material into products', '开瓶器、钥匙扣等，把废料做成商品'),
  ('100個', '100 units', '100个'), 'small', 'crafts.metal_goods',
  '工場で出る金属の端材を使って、栓抜きとキーホルダーを100個作り販売したい',
  'metal', '端材は材料費がかからず、「工場生まれ」の話も一緒に売れます。工場見学やふるさと納税の返礼品にも向いています。',
  ['端材の大きさから、作れる形と数を先に決めます。', '刻印や仕上げを外に頼む場合は、その工程だけ探せます。'],
  fig='part', guides=['subcontractor-own-product'])
I('mfg_jig', 'mfg', ('社内の治具を製品化', 'Turn an in-house jig into a product', '把内部治具产品化'),
  ('自社で使って便利だった道具を、他社にも売る', 'Sell a tool that works well for you to other companies', '把自己用着顺手的工具卖给其他公司'),
  ('50個', '50 units', '50个'), 'small', 'manufacturing.sheet_metal',
  '社内で使っている板金の治具を製品にして、他社にも販売したい。まず50個作りたい',
  'sheet', '社内で役に立っている道具は、同じ悩みを持つ会社にも売れる可能性があります。',
  ['社内用の寸法を、ほかの会社でも使える寸法に直します。', '取扱説明書と保証の範囲を決めます。'],
  est=[['manufacturing.sheet_metal', '1個の価格例（アルミ・鉄・ステンレスの曲げ品など）']], fig='part', guides=['subcontractor-own-product', 'own-product-development'])
I('mfg_part', 'mfg', ('廃番になった部品の作り直し', 'Remake a discontinued part', '重新制作停产零件'),
  ('現物から寸法を測って、少量だけ作る', 'Measure the original and make just a few', '按实物测量尺寸，只做少量'),
  ('10個', '10 units', '10个'), 'proto', 'manufacturing.cnc',
  '廃番になった金属の部品を、現物から寸法を測って切削加工で10個作り直したい',
  'sheet', '機械のメーカーが部品を作らなくなっても、現物があれば切削加工で作り直せることがあります。',
  ['現物を送るか、写真と寸法を送るかを工場と決めます。', '材料が分からないときは、硬さや色から近い材料を相談します。'],
  est=[['manufacturing.cnc', '丸物1個の価格例（φ50樹脂〜φ128鉄）']], fig='part', guides=['no-drawing'])
# ---------------- HW
I('hw_sensor', 'hw', ('スマホとつながる小型センサー', 'Small sensor that connects to a phone', '连接手机的小型传感器'),
  ('基板・ケース・アプリ・電波の認証まで', 'Board, case, app and radio certification', '电路板、外壳、应用及无线认证'),
  ('試作10台', '10 prototypes', '试制10台'), 'proto', 'electronics.pcba',
  '温度と湿度を測ってBluetoothでスマホに送る小型のセンサーを、10台試作したい',
  'iot', 'センサー機器は、基板・ケース・ソフト・アプリと必要な技術が多く、1社でそろわないことがよくあります。工程ごとに得意な会社を組み合わせます。',
  ['最初の試作は、測れるかどうかを確かめる最小の形にします。', '電池で動かすなら、どれくらい持つかを先に決めます。'],
  est=[['electronics.pcba', '基板10枚（10cm角まで）の製造'], ['testing.radio_cert', '技適（2.4GHz帯）申込の基本料']], fig='device', pick=True)
I('hw_case', 'hw', ('基板を入れるケースの試作', 'Prototype a case for your board', '试制电路板外壳'),
  ('3Dプリントなら1個から', 'From 1 unit with 3D printing', '3D打印1个起'),
  ('試作5個', '5 prototypes', '试制5个'), 'proto', 'manufacturing.rapid_proto',
  '手のひらくらいの大きさの樹脂のケースを、3Dプリントで5個試作したい',
  'proto3d', '3Dプリントなら金型なしで1個から作れ、形を直しながら何度も試せます。',
  ['中に入れる基板や電池の寸法を測って伝えます。', 'ねじ止めか、はめ込みかを決めます。'],
  est=[['manufacturing.rapid_proto', '手のひら大のボディ1個（ナイロン造形）']], fig='case')
I('hw_mold', 'hw', ('ケースを金型で量産', 'Mass-produce the case with a mold', '用模具量产外壳'),
  ('試作のあと、射出成形に切り替える', 'After prototyping, switch to injection molding', '试制后改用注塑成型'),
  ('1,000個', '1,000 units', '1,000个'), 'mass', 'manufacturing.injection_molding',
  '3Dプリントで試作した樹脂のケースを、金型を作って1,000個量産したい',
  'mold', '試作で形が決まったら、金型を作って射出成形にすると1個あたりの値段が下がります。',
  ['3Dプリントの形のままでは金型で抜けないことがあり、形の手直しが要ります。', 'アルミ型は少ない数向け、鉄の型は多い数向けです。'],
  est=[['manufacturing.injection_molding', '試作・少量向けの金型（プロトラブズの例）']], fig='case')
I('hw_light', 'hw', ('防水の自転車ライト', 'Waterproof bike light', '防水自行车灯'),
  ('回路・防水ケース・組立を組み合わせる作例', 'Example combining circuit, waterproof case and assembly', '组合电路、防水外壳和组装的示例'),
  ('試作', 'Prototype', '试制'), 'proto', 'manufacturing.assembly', '',
  'iot', '回路・防水のケース・組立を、それぞれ得意な会社に分けて頼む作例です。',
  ['雨の中で使えるか、防水の試験を試作で確かめます。', '充電式なら、電池と充電の安全を確かめます。'],
  ex='bike', fig='device')

IDEAS = I_

# ---- 図（カードと詳しいページの絵。線だけのアイコン。currentColor）
_S = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
FIG = {
 'bottle': f'<path d="M26 6h12v8l4 6v36a3 3 0 0 1-3 3H25a3 3 0 0 1-3-3V20l4-6z" {_S}/><path d="M22 30h20v14H22z" {_S}/>',
 'pouch': f'<path d="M16 10h32l-2 46H18z" {_S}/><path d="M16 18h32M26 30h12M24 38h16" {_S}/>',
 'jar': f'<path d="M20 12h24v8H20zM18 20h28v32a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4z" {_S}/><path d="M18 32h28" {_S}/>',
 'mug': f'<path d="M14 16h30v32a6 6 0 0 1-6 6H20a6 6 0 0 1-6-6z" {_S}/><path d="M44 24h4a6 6 0 0 1 0 12h-4" {_S}/><path d="M24 32h10" {_S}/>',
 'cup': f'<path d="M10 22h34l-3 22a6 6 0 0 1-6 5H19a6 6 0 0 1-6-5z" {_S}/><path d="M44 26h10M23 33h8" {_S}/>',
 'bag': f'<path d="M12 22h40l-3 34H15z" {_S}/><path d="M24 22v-6a8 8 0 0 1 16 0v6" {_S}/><path d="M26 36h12" {_S}/>',
 'shirt': f'<path d="M22 8l-12 8 5 10 5-3v33h24V23l5 3 5-10-12-8a10 6 0 0 1-20 0z" {_S}/><path d="M28 30h8" {_S}/>',
 'cloth': f'<path d="M14 10h36v44H14z" {_S}/><path d="M14 46h36M26 24h12" {_S}/>',
 'box': f'<path d="M10 22l22-10 22 10v26L32 58 10 48z" {_S}/><path d="M10 22l22 10 22-10M32 32v26" {_S}/>',
 'board': f'<path d="M14 18h30a6 6 0 0 1 6 6v24a6 6 0 0 1-6 6H14a6 6 0 0 1-6-6V24a6 6 0 0 1 6-6z" {_S}/><path d="M50 30h6v6h-6" {_S}/><circle cx="29" cy="36" r="5" {_S}/>',
 'badge': f'<circle cx="32" cy="32" r="18" {_S}/><circle cx="32" cy="32" r="10" {_S}/><path d="M32 50v8" {_S}/>',
 'candle': f'<path d="M18 26h28v26a4 4 0 0 1-4 4H22a4 4 0 0 1-4-4z" {_S}/><path d="M32 26v-6M32 8c4 4 4 8 0 10-4-2-4-6 0-10z" {_S}/>',
 'device': f'<rect x="16" y="14" width="32" height="36" rx="8" {_S}/><circle cx="32" cy="32" r="6" {_S}/><path d="M24 6c5-3 11-3 16 0M28 10c3-1 5-1 8 0" {_S}/>',
 'case': f'<path d="M10 22l22-8 22 8v20L32 50 10 42z" {_S}/><path d="M10 22l22 8 22-8M32 30v20" {_S}/><circle cx="20" cy="30" r="1.5" fill="currentColor"/>',
 'part': f'<circle cx="32" cy="32" r="18" {_S}/><circle cx="32" cy="32" r="6" {_S}/><path d="M32 8v6M32 50v6M8 32h6M50 32h6" {_S}/>',
 'hook': f'<path d="M14 54h36M32 54V14h14v8" {_S}/><path d="M46 22a6 6 0 1 1-6 6" {_S}/>',
 'fire': f'<path d="M12 40h40l-6 10H18z" {_S}/><path d="M18 50l-4 8M46 50l4 8M32 38c-8-6-4-14 0-20 0 6 8 8 6 16" {_S}/>',
 'leash': f'<circle cx="20" cy="40" r="12" {_S}/><path d="M30 34c8-4 12-12 16-22M46 12l6-2M46 12l2 6" {_S}/>',
 'slipper': f'<path d="M14 44c0-14 6-26 18-26s18 12 18 26v4a6 6 0 0 1-6 6H20a6 6 0 0 1-6-6z" {_S}/><path d="M16 36h32" {_S}/>',
 'soap': f'<rect x="10" y="24" width="44" height="22" rx="10" {_S}/><circle cx="22" cy="16" r="3" {_S}/><circle cx="32" cy="12" r="2" {_S}/>',
 'sweets': f'<circle cx="24" cy="32" r="12" {_S}/><circle cx="44" cy="36" r="10" {_S}/><circle cx="21" cy="29" r="1.5" fill="currentColor"/><circle cx="27" cy="35" r="1.5" fill="currentColor"/><circle cx="44" cy="35" r="1.5" fill="currentColor"/>',
}
def svg(kind, size=56):
    return f'<svg width="{size}" height="{size}" viewBox="0 0 64 64" aria-hidden="true">{FIG.get(kind, FIG["box"])}</svg>'


def js():
    """template.html の __IDEAS__ に入れる、日本語だけのデータ"""
    return json.dumps(dict(
        ind=[[k, ja] for k, ja, en, zh in IND],
        ideas=[dict(k=x['k'], ind=x['ind'], t=x['t'][0], d=x['d'][0], lot=x['lot'][0], q=x['q'], code=x['code'],
                    est=x['est'], ex=x['ex'], idea=x['idea'], fig=x['fig']) for x in IDEAS],
        picks=[x['k'] for x in IDEAS if x['pick']], fig=FIG), ensure_ascii=False, separators=(',', ':'))


T_IDEAS = {}
for k, ja, en, zh in IND:
    T_IDEAS[ja] = (en, zh)
for x in IDEAS:
    for f in ('t', 'd', 'lot'):
        T_IDEAS[x[f][0]] = x[f][1:]
T_IDEAS.update({
 '思いつかないときは、業種から選ぶ ↓': ('Not sure what to make? Pick your industry ↓', '想不出来？按行业挑选 ↓'),
 '何をつくるか、まだ決まっていなくても': ("Even if you haven't decided what to make", '即使还没想好要做什么'),
 '白紙からは思いつきにくいものです。業種を選ぶと、同じ立場の会社が作りやすいものを並べます。押すと、その内容で工程と候補の会社を探します。': ("It's hard to start from a blank page. Pick your industry and we'll show things businesses like yours can easily make. Tap one to see the steps and candidate companies.", '从零开始很难想到。选择行业后，会列出同类企业容易制作的产品。点击即可按该内容查找工序和候选公司。'),
 '業種': ('Industry', '行业'),
 'この内容で探す': ('Find makers for this', '按此内容查找'),
 '書き換えてから探す': ('Edit, then search', '修改后再查找'),
 '詳しく見る': ('Details', '查看详情'),
 '作例をすべて見る': ('See all examples', '查看全部示例'),
 '目安': ('Guide', '参考'),
 '対応する会社': ('Makers', '可对应的公司'),
 '最低ロット': ('Minimum lot', '最小批量'),
 '掲載ページ': ('Listing page', '收录页面'),
 '掲載企業の最小ロットの中央値': ('Median minimum lot of listed companies', '收录企业最小批量的中位数'),
 '作例（モデルケース）です。実在の会社の事例や見積ではありません。目安は公開されている料金表・記事と、掲載企業の最小ロットから出しています。期間は形・数量・工場の混み具合で変わるため、見積で確かめます。': ("These are model cases, not real companies' projects or quotes. The guide figures come from published price lists and articles and from listed companies' minimum lots. Lead time depends on shape, quantity and how busy the factory is, so it is confirmed in the quote.", '以下为示例（模型案例），并非真实公司的案例或报价。参考数字来自公开的价目表、文章以及收录企业的最小批量。周期因形状、数量和工厂繁忙程度而异，需通过报价确认。'),
})


# ================= 詳しいページ（/idea/<k>/ と /idea/）
SITE = 'https://katachi.shiokonbu.com'
QLAB = {'proto': '試作', 'small': '小ロット', 'mass': '量産'}
CSS = """<style>.crumb{font-size:12.5px;color:var(--mute);margin:0}.crumb a{color:var(--mute)}.upd{font-size:12.5px;color:var(--mute);margin:4px 0 14px}
.ihero{display:flex;gap:18px;align-items:center;margin:8px 0 6px}.ihero .fig{flex:none;width:88px;height:88px;border-radius:18px;background:#eef3fd;color:var(--ice);display:grid;place-items:center}
.chips{display:flex;gap:6px;flex-wrap:wrap}.chips span{font-size:12.5px;border:1px solid var(--line);border-radius:99px;padding:2px 10px;color:var(--mute)}
.points{background:#f3f6fd;border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:18px 0}.points b{display:block;margin-bottom:4px}.points ul{margin:0}
.tbl{overflow-x:auto;margin:12px 0}.tbl table{border-collapse:collapse;min-width:100%;font-size:14px;line-height:1.6}.tbl th,.tbl td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}.tbl th{background:#f3f6fd;white-space:nowrap}
.src{font-size:13px;color:var(--mute)}.cta{margin:30px 0 10px;padding:20px;border:1px solid var(--ice);border-radius:12px}.cta p{margin:4px 0 10px}
.cta a.btn{display:inline-block;margin:4px 8px 4px 0;background:var(--ice);color:#fff;text-decoration:none;padding:10px 18px;border-radius:8px;font-weight:600}.cta a.sub{background:#fff;color:var(--ice);border:1px solid var(--ice)}
.note{font-size:12.5px;color:var(--mute)}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:10px 0 6px}
.grid a{display:flex;gap:10px;align-items:center;border:1px solid var(--line);border-radius:10px;padding:10px 12px;text-decoration:none;color:var(--fg)}.grid a:hover{border-color:var(--ice)}
.grid a span.f{flex:none;color:var(--ice)}.grid a b{display:block;font-size:14.5px}.grid a small{display:block;color:var(--mute);font-size:12.5px;line-height:1.5}
@media(max-width:600px){.grid{grid-template-columns:1fr}.ihero .fig{width:68px;height:68px}}</style>"""


def _yen(v):
    if v >= 10000:
        m = v / 10000
        m = round(m) if m >= 100 else round(m, 1)
        return (f'{m:,.1f}'.rstrip('0').rstrip('.') if isinstance(m, float) else f'{m:,}') + '万円'
    return f'{round(v):,}円'


def fmt(v, u):
    if u == 'usd':
        return f'${v:,}'
    if u == 'pcs':
        return f'{v:,}個'
    if u == 'yen_cm3':
        return f'{v:,}円/cm³'
    return _yen(v)


def rng(lo, hi, u):
    if hi is None:
        return fmt(lo, u) + '〜'
    if lo == hi:
        return fmt(lo, u)
    return fmt(lo, u) + '〜' + fmt(hi, u)


def est_rows(x):
    from estimates import EST, SRC
    out = []
    for c, t in x['est']:
        r = next((r for r in EST.get(c, {}).get('rows', []) if r['t'] == t), None)
        if r and r.get('lo') is not None:
            out.append((r, SRC.get(r.get('s'), {})))
    return out


KIND = {'init': '初期費用', 'unit': '単価', 'moq': '最低ロット', 'min': '最低発注額', 'fee': '費用'}
LEVEL = {'official': '公式の料金表', 'article': '報道・記事', 'listing': '業者・まとめサイトの掲載', 'rough': '根拠の記載がない目安'}


def _stats(root):
    try:
        return json.load(open(os.path.join(root, 'data', 'stats.json'))).get('caps', {})
    except Exception:
        return {}


def meta(x):
    t = x['t'][0]
    ind = dict((k, ja) for k, ja, *_ in IND)[x['ind']]
    lot = x['lot'][0]
    title = f'{t}を作るには：{lot}からの進め方と目安'
    if x['ex']:
        title = f'{t}を作るには：工程の分け方と頼み先'
    desc = (f'{ind}が「{t}」を{lot}から作る作例です。作り方の流れ、依頼前に決めること、費用・最低ロットの目安（出典つき）、'
            f'確かめる表示や許可、頼める会社の数をまとめました。')
    return title, desc, ind


def page_html(x, root, guides_by):
    e = html.escape
    p = P[x['prof']]
    t, d, lot = x['t'][0], x['d'][0], x['lot'][0]
    title, desc, ind = meta(x)
    caps = _stats(root)
    n = caps.get(x['code'], 0)
    er = est_rows(x)
    est_txt = '、'.join(f'{KIND.get(r["k"], "")}{rng(r["lo"], r["hi"], r["u"])}（{r["t"]}）' for r, s in er)
    pts = [p['ans'], (f'公開されている目安：{est_txt}。' if er else '公開された相場は見つかっていないため、金額は見積で確かめます。'),
           p['check'][0]]
    if n:
        pts.insert(1, f'KATACHIに登録している会社のうち、この工程を受ける会社は{n:,}社あります。')
    steps = ''.join(f'<li>{e(s)}</li>' for s in p['steps'])
    tips = ''.join(f'<li>{e(s)}</li>' for s in x['tips'])
    dec = ''.join(f'<li>{e(s)}</li>' for s in p['decide'])
    chk = ''.join(f'<li>{e(s)}</li>' for s in p['check'])
    if er:
        tbl = ('<div class="tbl"><table><tr><th>項目</th><th>目安</th><th>中身</th><th>出典・確かさ</th></tr>'
               + ''.join(f'<tr><td>{KIND.get(r["k"], "")}</td><td>{rng(r["lo"], r["hi"], r["u"])}</td><td>{e(r["t"])}</td>'
                         f'<td><a href="{e(s.get("url", ""))}" target="_blank" rel="noopener">{e(s.get("t", ""))}</a>（{LEVEL.get(s.get("level"), "")}）</td></tr>' for r, s in er)
               + '</table></div><p class="src">公開されている料金表・記事に書かれた数字です（2026-11-12に確認）。形・材料・数量・納期で大きく変わり、正式な金額は工場の見積で決まります。'
               + ('ドルの金額は、画面では1ドル＝150円で換算しています。' if any(r['u'] == 'usd' for r, s in er) else '') + '</p>')
    else:
        tbl = '<p>この作例に当てはまる公開の相場は見つかっていません。金額は、見積の依頼で複数の会社に聞いて比べます。</p>'
    cnt = f'<p>KATACHIに登録している会社（公開情報）のうち、この工程を受ける会社は<b>{n:,}社</b>です。</p>' if n else ''
    gl = [g for g in x['guides'] + p['guides'] if g in guides_by]
    gl = list(dict.fromkeys(gl))
    rel = ''.join(f'<li><a href="/guide/{g}/">{e(guides_by[g]["h1"])}</a></li>' for g in gl)
    same = [y for y in IDEAS if y['ind'] == x['ind'] and y['k'] != x['k']]
    grid = ''.join(f'<a href="/idea/{y["k"]}/"><span class="f">{svg(y["fig"], 36)}</span><span><b>{e(y["t"][0])}</b><small>{e(y["d"][0])}</small></span></a>' for y in same)
    q = QLAB[x['q']]
    go = f'/?idea={x["k"]}'
    faq = [(f'{t}は、何個から作れますか', (f'この作例は{lot}を想定しています。' + (f'公開されている目安では、{est_txt}です。' if er else '')
                                       + '最低ロットは工場や作り方で変わるので、見積の依頼で確かめます。')),
           ('図面やデザインがなくても頼めますか', '頼めます。作りたいものを文章や写真で伝えると、KATACHIが工程に分けて、図面なしでも相談できる会社を探します。'),
           ('見積を頼むのにお金はかかりますか', '工程の整理・会社の検索・見積の依頼は無料です。試作・製造の代金は、依頼する会社に直接お支払いいただきます。')]
    faq_html = '<dl>' + ''.join(f'<dt>{e(a)}</dt><dd>{e(b)}</dd>' for a, b in faq) + '</dl>'
    body = (f'<p class="crumb"><a href="/">KATACHI</a> › <a href="/idea/">作例</a> › {e(ind)}</p>'
            f'<div class="ihero"><span class="fig">{svg(x["fig"], 56)}</span><div><h1>{e(title)}</h1>'
            f'<div class="chips"><span>{e(ind)}</span><span>{e(lot)}</span><span>{q}</span></div></div></div>'
            f'<p class="upd">更新日：{UPDATED.replace("-", "/")}</p>'
            f'<p>{e(t)}は、{e(p["ans"])}{e(x["why"])}</p>'
            f'<div class="points"><b>この作例の要点</b><ul>' + ''.join(f'<li>{e(s)}</li>' for s in pts) + '</ul></div>'
            f'<h2>作り方の流れ</h2><ol>{steps}</ol>'
            f'<h2>この作例で工夫すること</h2><ul>{tips}</ul>'
            f'<h2>依頼前に決めること</h2><p>見積は、次のことが決まっているほど早く、正確に出ます。決まっていないことは「未定」と書いて相談できます。</p><ul>{dec}</ul>'
            f'<h2>費用・最低ロットの目安</h2>{tbl}{cnt}<p class="note">期間は、形・数量・工場の混み具合で変わるため、見積で確かめます。</p>'
            f'<h2>確かめる表示・許可</h2><ul>{chk}</ul>'
            + (f'<p>くわしくは、次のガイドにまとめています。</p><ul>{rel}</ul>' if rel else '')
            + f'<h2>よくある質問</h2>{faq_html}'
            f'<div class="cta"><b>この作例の内容で、頼める会社をさがす</b><p>押すと、KATACHIがこの内容を工程に分け、工程ごとに候補の会社を出します。内容は書き換えてから探すこともできます。</p>'
            f'<a class="btn" href="{go}">この内容で探す</a><a class="btn sub" href="{go}&amp;edit=1">書き換えてから探す</a></div>'
            + (f'<h2>{e(ind)}のほかの作例</h2><div class="grid">{grid}</div>' if grid else '')
            + '<p><a href="/idea/">作例をすべて見る</a></p>'
            '<p class="note">作例（モデルケース）です。実在の会社の事例や見積ではありません。目安の数字は公開されている料金表・記事から、会社の数はKATACHIに登録している公開情報から出しています。</p>')
    url = f'{SITE}/idea/{x["k"]}/'
    graph = [{"@type": "Organization", "@id": SITE + "/#org", "name": "KATACHI", "url": SITE + "/", "logo": SITE + "/apple-touch-icon.png"},
             {"@type": "Article", "headline": title, "description": desc, "dateModified": UPDATED, "datePublished": UPDATED, "inLanguage": "ja",
              "mainEntityOfPage": url, "author": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"}, "image": SITE + "/og.png"},
             {"@type": "HowTo", "name": f'{t}の作り方の流れ', "step": [{"@type": "HowToStep", "position": i + 1, "text": s} for i, s in enumerate(p['steps'])]},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "KATACHI", "item": SITE + "/"},
                 {"@type": "ListItem", "position": 2, "name": "作例", "item": SITE + "/idea/"},
                 {"@type": "ListItem", "position": 3, "name": t, "item": url}]},
             {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": a, "acceptedAnswer": {"@type": "Answer", "text": b}} for a, b in faq]}]
    return title, desc, body, graph


def index_html():
    e = html.escape
    title = f'自社でつくれるものの作例集：業種別{len(IDEAS)}例'
    desc = ('カフェ・サロン・宿泊施設・農家・町工場など、設計部門のない中小企業が小ロットから作りやすいものの作例を業種別にまとめました。'
            '作り方の流れ・費用の目安・確かめる表示がわかります。')
    secs = ''
    for k, ja, *_ in IND:
        if k == 'pick':
            continue
        ys = [y for y in IDEAS if y['ind'] == k]
        if not ys:
            continue
        secs += f'<h2>{e(ja)}</h2><div class="grid">' + ''.join(
            f'<a href="/idea/{y["k"]}/"><span class="f">{svg(y["fig"], 36)}</span><span><b>{e(y["t"][0])}</b><small>{e(y["lot"][0])}・{e(y["d"][0])}</small></span></a>' for y in ys) + '</div>'
    body = (f'<p class="crumb"><a href="/">KATACHI</a></p><h1>{e(title)}</h1><p class="lead">{e(desc)}</p>'
            '<p>何をつくるか白紙から考えるのは難しいものです。同じ立場の会社が作りやすいものから選ぶと、「うちならこうしたい」が見つかります。'
            '気になる作例を開くと、作り方の流れ・依頼前に決めること・目安・確かめる表示がわかり、そのままKATACHIで頼める会社を探せます。</p>'
            f'{secs}<p class="note">作例（モデルケース）です。実在の会社の事例や見積ではありません。</p>')
    graph = [{"@type": "CollectionPage", "name": title, "url": SITE + "/idea/", "description": desc, "inLanguage": "ja",
              "hasPart": [{"@type": "Article", "headline": meta(y)[0], "url": f'{SITE}/idea/{y["k"]}/'} for y in IDEAS]}]
    return title, desc, body, graph


def by_guide():
    """ガイドの slug → そのガイドを参照する作例（ガイド記事の「このテーマの作例」に使う）"""
    m = {}
    for x in IDEAS:
        for g in dict.fromkeys(x['guides'] + P[x['prof']]['guides']):
            m.setdefault(g, []).append(x)
    return m


if __name__ == '__main__':
    import re
    ks = [x['k'] for x in IDEAS]
    assert len(ks) == len(set(ks))
    for x in IDEAS:
        assert x['prof'] in P and x['fig'] in FIG, x['k']
        assert x['ind'] in dict((k, 1) for k, *_ in IND), x['k']
        assert x['ex'] or x['idea'], x['k']
        assert not re.search('効く|治る|改善', x['why'] + ''.join(x['tips']) + x['idea']) or x['k'] == 'pet_shampoo', x['k']
    print(len(IDEAS), 'ideas,', len(T_IDEAS), 'strings, picks', sum(x['pick'] for x in IDEAS))
