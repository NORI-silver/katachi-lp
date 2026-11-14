"""製品仕様DB（KATACHIが先に入れておく「よくある製品」の一覧）→ data/products.json

- 入力文の読み取りで、まずこのDBの近い製品を当て、足りない項目だけを AI の読み取り（受付 type:'spec'）で埋める。
- 新しい製品は受付のシート「仕様読み取り」に溜まる（「DBの一致」が空の行）。見直して、よいものをここに足して育てる。
- 値ごとに確かさを分ける（サイトの区分と同じ）：
    official = 公的機関・会社の公式ページ（URLつき） / article = 報道・記事 / listing = 業者の掲載ページ・まとめ
    site = KATACHIのページ（作例・ガイド。中に出典がある） / ai = AI推定（よくある構成の例） / 空 = 要確認
- 数字（最小ロット・費用）は tools/estimates.py の出典つきの行だけ。寸法・重さは製品ごとに違うので入れない（要確認）。
- 法規制は、ガイド記事で出典を確かめた公的機関のページ（REG）だけ。医療機器・医薬品・酒類は扱わない（AGENTS.md）。
- 作例（tools/ideas.py）44本と、製品イメージ案の種類（concepts.py・concepts_generic.py）も取り込む。

使い方: python3 tools/product_db.py .   （seo_pages.py からも呼ばれる）
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concepts, concepts_generic, estimates, ideas  # noqa: E402

SITE = 'https://katachi.shiokonbu.com'
UPDATED = '2026-11-14'

# ---- 法規制・表示（出典はガイド記事で使っている公的機関のページ）
REG = {
    'cosme': ('化粧品の製造販売業の許可・容器の表示（OEM先が製造販売元になれば、自社は発売元として売れる）', '茨城県「初めて化粧品を製造・製造販売・輸入される方へ」', 'https://www.pref.ibaraki.jp/hokenfukushi/yakumu/yakuji/seizougyoutou/kesyouhin/hazimete.html'),
    'soap': ('合成洗剤・台所用石けん・住宅用洗浄剤の品質表示（家庭用品品質表示法）', '消費者庁「雑貨工業品品質表示規程 二十七」', 'https://www.caa.go.jp/policies/policy/representation/household_goods/law/law_07/item_027.html'),
    'food_lic': ('食品の製造・加工の営業許可・届出（製造する会社が持つ）', '厚生労働省「営業許可制度の見直し及び営業届出制度の創設の施行について」', 'https://www.mhlw.go.jp/content/000786682.pdf'),
    'food_label': ('食品表示（名称・原材料・アレルゲン・期限・製造者など）', '消費者庁「食品表示ガイド 早わかり」', 'https://www.caa.go.jp/policies/policy/food_labeling/information/pamphlets/assets/food_labeling_cms201_261030_02.pdf'),
    'haccp': ('HACCPに沿った衛生管理（製造する会社が行う）', '厚生労働省 菓子製造業の衛生管理計画作成の手引書', 'https://www.mhlw.go.jp/content/11130500/000478404.pdf'),
    'food_pack': ('食品に触れる器具・容器包装のポジティブリスト制度', '消費者庁「食品用器具・容器包装のポジティブリスト制度について」', 'https://www.caa.go.jp/policies/policy/standards_evaluation/appliance/positive_list_new'),
    'health': ('健康食品は効能を書けない（医薬品と誤認される表示は不可）', '厚生労働省「いわゆる『健康食品』のホームページ」', 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/shokuhin/hokenkinou/index.html'),
    'nutri': ('栄養機能食品として表示するときの決まり', '消費者庁「栄養機能食品について」', 'https://www.caa.go.jp/policies/policy/food_labeling/foods_with_nutrient_function_claims'),
    'petfood': ('ペットフード安全法（犬・猫のフードの基準と表示、製造業者の届出）', '環境省「ペットフード安全法の概要」', 'https://www.env.go.jp/nature/dobutsu/aigo/petfood/outline.html'),
    'petdrug': ('「病気に効く」などは動物用医薬品にあたるおそれ', '農林水産省「動物用医薬品等に該当するか否かの考え方」', 'https://www.maff.go.jp/j/syouan/tikusui/yakuzi/y_import/'),
    'pse': ('電気用品安全法（コンセントにつなぐ機器・ACアダプター・リチウムイオン電池など、PSEマーク）', '経済産業省「電気用品安全法の概要」', 'https://www.meti.go.jp/policy/consumer/seian/denan/act_outline.html'),
    'battery': ('モバイルバッテリー・リチウムイオン電池の扱い（電気用品安全法）', '経済産業省「モバイルバッテリーに関するFAQ」', 'https://www.meti.go.jp/policy/consumer/seian/denan/mlb_faq.html'),
    'giteki': ('無線（Bluetooth・Wi-Fi・LTEなど）を使う機器の技適（電波法）', '総務省 電波利用ポータル「基準認証制度についてよくある質問」', 'https://www.tele.soumu.go.jp/j/sys/equ/tech/faq/index.htm'),
    'terminal': ('通信回線につなぐ端末機器の基準認証（電気通信事業法）', '総務省「端末機器の基準認証に関するガイドライン」', 'https://www.soumu.go.jp/main_content/001034595.pdf'),
    'psc': ('消費生活用製品安全法（PSCマークの対象製品か確かめる）', '経済産業省「消費生活用製品安全法」', 'https://www.meti.go.jp/product_safety/consumer/system/01.html'),
    'lpg': ('ガスを使う器具（カセットこんろ・ガスバーナー等）のPSLPGマーク', '経済産業省「液化石油ガス法（PSLPGマークの対象製品）」', 'https://www.meti.go.jp/product_safety/consumer/system/04.html'),
    'toy': ('乳幼児用玩具の新しい規制（子ども用の製品）', '経済産業省「乳幼児用玩具に対して新しい規制が導入されました」', 'https://www.meti.go.jp/product_safety/kodomo/gangu_kisei.html'),
    'fiber': ('繊維製品の表示（組成・洗濯表示・表示者名）', '消費者庁「繊維製品の表示事項」', 'https://www.caa.go.jp/policies/policy/representation/household_goods/guide/fiber/fiber_show.html'),
    'bag': ('かばんの品質表示（雑貨工業品品質表示規程）', '消費者庁「かばん」（雑貨工業品品質表示規程の手引き）', 'https://www.caa.go.jp/policies/policy/representation/household_goods/guide/zakka/zakka_02.html'),
    'zakka': ('家庭用品品質表示法の対象か確かめる（雑貨・家具・台所用品など）', '消費者庁「家庭用品品質表示法 手引き」', 'https://www.caa.go.jp/policies/policy/representation/household_goods/guide/index.html'),
    'origin': ('原産国の表示（海外で作ったものの見せ方）', '消費者庁「商品の原産国に関する不当な表示」', 'https://www.caa.go.jp/policies/policy/representation/fair_labeling/representation_regulation/case_005/'),
    'premium': ('景品・ノベルティとして配るときの上限（景品表示法）', '消費者庁「景品規制の概要」', 'https://www.caa.go.jp/policies/policy/representation/fair_labeling/premium_regulation/'),
    'pl': ('製造物責任（PL法）：欠陥で事故が起きたときの責任', '消費者庁「製造物責任（PL）法の概要Q&A」', 'https://www.caa.go.jp/policies/policy/consumer_safety/other/pl_qa.html'),
}

IND = {
    'cosme': '化粧品・美容', 'daily': '日用品・雑貨', 'pet': 'ペット用品', 'food': '食品・お菓子', 'drink': '飲料・健康食品',
    'apparel': 'アパレル・繊維', 'bag': 'バッグ・革小物', 'goods': 'グッズ・ノベルティ', 'pack': 'パッケージ・印刷',
    'wood': '木工・家具・インテリア', 'kitchen': 'キッチン・食器', 'outdoor': 'アウトドア・スポーツ', 'iot': 'IoT・電子機器',
    'wear': 'ウェアラブル・健康管理（医療機器を除く）', 'mech': '機械・装置・治具', 'parts': '金属・樹脂の部品',
    'care': '福祉・介護・暮らしの補助（医療機器を除く）', 'kids': 'ベビー・キッズ・玩具', 'car': '車・バイク・自転車用品',
    'garden': '園芸・農業資材', 'store': '店舗・施設の什器・サイン',
    'material': '素材・中間材（布・紙・木材・金属材料など）', 'chem': '化学品・塗料・接着剤', 'build': '建築部材・住宅設備',
    'vehicle': '輸送機器（自動車・鉄道・船舶・航空機）', 'measure': '計測・試験・光学機器', 'instrument': '楽器', 'office': '文具・事務用品',
}

# ---- よくある製品（ind, id, 名前, 探す語, 種類, 工程, 法規制, よくある構成, よくある素材）
# 構成・素材は「よくある例」（AI推定）。依頼ごとに違うので、画面では「例」として出す。
CAT = []


def C(ind, i, name, kw, kind, proc, reg, parts='', mat=''):
    CAT.append(dict(ind=ind, id=i, name=name, kw=kw, kind=kind, proc=proc.split(), reg=reg.split(), parts=[x for x in parts.split('・') if x], mat=[x for x in mat.split('・') if x]))


# 化粧品・美容
C('cosme', 'lotion', '化粧水', r'化粧水|ローション|トナー', 'cosme', 'cosmetics.oem packaging.container packaging.label_print packaging.box', 'cosme', '中身（処方）・ボトル・キャップ・ラベル・外箱', 'PETボトル・PP樹脂のキャップ')
C('cosme', 'serum', '美容液', r'美容液|セラム|serum', 'cosme', 'cosmetics.oem packaging.container packaging.label_print', 'cosme', '中身（処方）・スポイト付きボトル・ラベル・外箱', 'ガラス瓶・PP樹脂')
C('cosme', 'cream', 'クリーム・バーム', r'クリーム|バーム|保湿剤', 'cosme', 'cosmetics.oem packaging.container packaging.label_print', 'cosme', '中身（処方）・ジャー容器・中蓋・ラベル', 'PP・アクリル樹脂の容器')
C('cosme', 'shampoo', 'シャンプー・トリートメント', r'シャンプー|トリートメント|コンディショナー', 'cosme', 'cosmetics.oem packaging.container packaging.label_print', 'cosme', '中身（処方）・ポンプボトル・ラベル', 'PET・PEボトル')
C('cosme', 'bodysoap', 'ボディソープ・ハンドソープ', r'ボディソープ|ハンドソープ|ボディウォッシュ', 'cosme', 'cosmetics.oem packaging.container packaging.label_print', 'cosme', '中身（処方）・ポンプボトル・ラベル', 'PET・PEボトル')
C('cosme', 'barsoap', '固形石けん', r'石けん|石鹸|せっけん|ソープバー', 'cosme', 'cosmetics.oem packaging.box', 'cosme', '石けん本体・個包装・外箱', '紙箱・フィルム')
C('cosme', 'cleansing', 'クレンジング・洗顔料', r'クレンジング|洗顔', 'cosme', 'cosmetics.oem packaging.container packaging.label_print', 'cosme', '中身（処方）・チューブかボトル・ラベル', 'ラミネートチューブ・PET')
C('cosme', 'sunscreen', '日焼け止め', r'日焼け止め|サンスクリーン|uv(ケア|クリーム)', 'cosme', 'cosmetics.oem packaging.container', 'cosme', '中身（処方）・チューブ・ラベル', 'ラミネートチューブ')
C('cosme', 'lip', 'リップクリーム・リップグロス', r'リップ', 'cosme', 'cosmetics.oem packaging.container', 'cosme', '中身・スティック容器かチューブ', 'PP・AS樹脂')
C('cosme', 'makeup', 'ファンデーション・アイシャドウなどメイク用品', r'ファンデ|アイシャドウ|チーク|マスカラ|アイライナー|メイク(用品|品)', 'cosme', 'cosmetics.oem packaging.container', 'cosme', '中身・コンパクトやパレット・パフ', '樹脂のケース・ミラー')
C('cosme', 'perfume', 'フレグランス・香水', r'香水|フレグランス|オードトワレ|パルファム', 'cosme', 'cosmetics.oem packaging.container packaging.box', 'cosme', '香料を含む中身・アトマイザー瓶・外箱', 'ガラス瓶・金属のポンプ')
C('cosme', 'hairoil', 'ヘアオイル・スタイリング剤', r'ヘアオイル|ヘアワックス|スタイリング|ヘアミスト|ヘアバーム', 'cosme', 'cosmetics.oem packaging.container', 'cosme', '中身（処方）・ボトルやジャー・ラベル', 'ガラス・PET・PP')
C('cosme', 'bathsalt', '入浴剤・バスソルト', r'入浴剤|バスソルト|バスボム', 'cosme', 'cosmetics.oem packaging.box', 'cosme', '中身・袋や容器・ラベル', 'アルミ袋・PET容器')
C('cosme', 'nail', 'ネイル用品', r'ネイル|マニキュア|ジェルネイル', 'cosme', 'cosmetics.oem packaging.container', 'cosme', '中身・小瓶・ブラシ付きキャップ', 'ガラス瓶・樹脂キャップ')
C('cosme', 'mask', 'フェイスパック・シートマスク', r'フェイスパック|シートマスク|フェイスマスク', 'cosme', 'cosmetics.oem packaging.label_print', 'cosme', '美容液・シート・アルミ袋', '不織布・アルミ袋')
C('cosme', 'tool', '美容雑貨（ブラシ・パフ・スポンジ）', r'メイクブラシ|パフ|スポンジ|美容雑貨', 'goods', 'cosmetics.household', 'zakka origin', '毛やスポンジ・持ち手・袋', '合成繊維・樹脂・木')
# 日用品・雑貨
C('daily', 'detergent', '洗剤（台所用・洗濯用・住宅用）', r'洗剤|クリーナー|洗浄剤|柔軟剤', 'cosme', 'cosmetics.household packaging.container packaging.label_print', 'soap', '中身・ボトルやスプレー・ラベル', 'PE・PETボトル')
C('daily', 'diffuser', 'ルームフレグランス・ディフューザー', r'ディフューザー|ルームフレグランス|ルームスプレー|芳香剤', 'cosme', 'cosmetics.household packaging.container', 'zakka', '香りの液・瓶・リードスティック', 'ガラス瓶・ラタン')
C('daily', 'candle', 'キャンドル', r'キャンドル|ろうそく|蝋燭', 'goods', 'cosmetics.household', 'zakka', 'ろう・芯・容器', 'ソイワックス・パラフィン・ガラス')
C('daily', 'towel', 'タオル・ハンカチ', r'タオル|ハンカチ|手ぬぐい|てぬぐい', 'apparel', 'manufacturing.textile apparel.print_embroidery', 'fiber', '生地・縫製・刺繍やプリント・下げ札', '綿・ガーゼ')
C('daily', 'umbrella', '傘', r'傘|日傘|雨傘', 'shape:cover', 'manufacturing.textile', 'zakka origin pl', '生地・骨・手元', 'ポリエステル・グラスファイバー・アルミ')
C('daily', 'stationery', '文房具（ペン・ノート・ふせん）', r'文房具|文具|ボールペン|ノート|ふせん|付箋|メモ帳', 'goods', 'packaging.label_print cosmetics.household', 'zakka premium', '本体・印刷・包装', '紙・樹脂')
C('daily', 'mobile', 'スマホケース・スマホスタンド', r'スマホケース|スマホスタンド|スマホリング|iphoneケース', 'case', 'manufacturing.injection_molding manufacturing.rapid_proto', 'origin', 'ケース本体・印刷', 'TPU・ポリカーボネート')
C('daily', 'storage', '収納用品（ボックス・ケース）', r'収納ボックス|収納ケース|小物入れ|整理', 'shape:box', 'manufacturing.injection_molding crafts.wood_furniture', 'zakka', '本体・ふた・仕切り', 'PP樹脂・木・紙')
C('daily', 'mask', 'マスク（布・不織布）', r'(布|不織布|立体)マスク', 'apparel', 'manufacturing.textile', 'fiber', '本体の布・耳ひも', '綿・ポリエステル・不織布')
C('daily', 'slipper', 'スリッパ・ルームシューズ', r'スリッパ|ルームシューズ', 'apparel', 'manufacturing.textile', 'zakka origin', 'アッパー・中敷き・底', 'パイル・EVA')
C('daily', 'cushion', 'クッション・枕', r'クッション|枕|まくら|ピロー', 'shape:bed', 'manufacturing.textile', 'fiber', 'カバー・中材', '綿・ポリエステルわた・ウレタン')
C('daily', 'blanket', 'ブランケット・寝具', r'ブランケット|毛布|寝具|シーツ|布団カバー', 'shape:mat', 'manufacturing.textile apparel.knit', 'fiber', '生地・縫製・ラベル', 'フリース・綿')
# ペット用品
C('pet', 'petfood', 'ドッグフード・キャットフード', r'(ドッグ|キャット|ペット)フード', 'food', 'food.pet_food packaging.label_print', 'petfood', '中身・袋・ラベル', 'アルミ袋・クラフト袋')
C('pet', 'pettreat', '犬・猫のおやつ', r'(犬|猫|ペット).{0,6}(おやつ|ジャーキー|トリーツ)', 'food', 'food.pet_food packaging.label_print', 'petfood', '中身・袋・ラベル', 'アルミ袋')
C('pet', 'petshampoo', 'ペット用シャンプー', r'(犬|猫|ペット).{0,6}シャンプー', 'cosme', 'cosmetics.household packaging.container', 'petdrug', '中身・ボトル・ラベル', 'PETボトル')
C('pet', 'leash', 'リード・首輪・ハーネス', r'リード|首輪|ハーネス', 'collar', 'apparel.leather manufacturing.textile', 'zakka', 'ベルト・金具・持ち手', 'ナイロン・革・金属の金具')
C('pet', 'petbed', 'ペットベッド・マット', r'(犬|猫|ペット).{0,6}(ベッド|マット|クッション)', 'shape:bed', 'manufacturing.textile', 'zakka', 'カバー・中材・底の滑り止め', 'ポリエステル・ウレタン')
C('pet', 'petwear', '犬の服', r'(犬|ドッグ).{0,4}(服|ウェア|レインコート)', 'apparel', 'apparel.garment_oem', '', '生地・縫製・留め具', 'ポリエステル・綿')
C('pet', 'petbowl', 'ペット用の食器・給水器', r'(犬|猫|ペット).{0,6}(食器|ボウル|給水)', 'shape:bowl', 'crafts.ceramics_glass manufacturing.injection_molding', 'food_pack', '器・台', '陶器・ステンレス・樹脂')
C('pet', 'pettoy', 'ペット用のおもちゃ', r'(犬|猫|ペット).{0,6}(おもちゃ|玩具|トイ)', 'shape:toy', 'manufacturing.silicone_molding manufacturing.textile', 'pl', '本体・中のわたや鈴', 'ゴム・布・ロープ')
C('pet', 'pethouse', 'ペットハウス・ケージ・キャリー', r'(犬|猫|ペット).{0,6}(ハウス|ケージ|キャリー|サークル|小屋)', 'shape:house', 'crafts.wood_furniture manufacturing.sheet_metal manufacturing.textile', 'pl', '枠・扉・床・持ち手', '木・金属・布')
C('pet', 'petslope', 'ペット用スロープ・ステップ', r'(犬|猫|ペット).{0,8}(スロープ|ステップ|階段)', 'shape:slope', 'crafts.wood_furniture manufacturing.textile', 'pl', '本体・踏み面・滑り止め', '木・樹脂・カーペット生地')
C('pet', 'petcart', 'ペットカート', r'(ペット|犬|猫).{0,4}カート', 'cart', 'manufacturing.sheet_metal manufacturing.textile', 'pl', 'フレーム・車輪・布のかご', 'アルミ・ポリエステル')
C('pet', 'petwheel', '犬・猫用の車椅子', r'(犬|猫|ペット).{0,15}(車椅子|車いす|歩行器)', 'pet_wheelchair', 'manufacturing.cnc manufacturing.textile mechanical.wearable_fit', 'pl petdrug', 'フレーム・車輪・ハーネス', 'アルミのパイプ・ウレタンタイヤ・ナイロン')
C('pet', 'petlift', 'ペット用リフト・移乗の補助具', r'(犬|猫|ペット).{0,20}(リフト|移乗|担架|ストレッチャー)', '', 'mechanical.enclosure_design manufacturing.sheet_metal manufacturing.assembly testing.battery_safety', 'pl pse petdrug', '担架・昇降機構・脚・電源と操作部', 'アルミ合金・鋼材・パッド')
C('pet', 'smartcollar', 'スマート首輪（見守り・健康管理）', r'(スマート|gps|見守り).{0,6}首輪|首輪.{0,10}(センサ|gps|見守)', 'collar', 'electronics.pcba electronics.wireless sensing.motion mechanical.waterproof testing.radio_cert', 'giteki battery petdrug', '基板・電池・センサー・防水ケース・ベルト', '樹脂ケース・シリコーン')
C('pet', 'petfeeder', '自動給餌器', r'自動給餌|自動えさ|オートフィーダー', 'device', 'electronics.pcba manufacturing.injection_molding manufacturing.assembly', 'pse giteki food_pack', 'タンク・送り出し機構・モーター・基板', '樹脂（食品に触れる部分）')
C('pet', 'pettoilet', 'ペット用トイレ', r'(犬|猫|ペット).{0,6}トイレ', 'shape:box', 'manufacturing.injection_molding', 'zakka', '本体・すのこ・トレー', 'PP樹脂')
# 食品・お菓子
C('food', 'bakedsweets', '焼き菓子（クッキー・フィナンシェなど）', r'焼き菓子|クッキー|フィナンシェ|マドレーヌ|サブレ|パウンドケーキ', 'food', 'food.processed_oem packaging.box packaging.label_print', 'food_lic food_label haccp', '中身・個包装・化粧箱', '個包装フィルム・紙箱')
C('food', 'chocolate', 'チョコレート', r'チョコ', 'food', 'food.processed_oem packaging.box', 'food_lic food_label haccp', '中身・型・個包装・箱', 'フィルム・紙箱')
C('food', 'wagashi', '和菓子', r'和菓子|まんじゅう|饅頭|どら焼き|羊羹|ようかん|せんべい|煎餅', 'food', 'food.processed_oem packaging.box', 'food_lic food_label haccp', '中身・個包装・箱', 'フィルム・紙箱')
C('food', 'jam', 'ジャム・はちみつ・スプレッド', r'ジャム|はちみつ|蜂蜜|スプレッド|コンフィチュール', 'food', 'food.processed_oem packaging.container packaging.label_print', 'food_lic food_label food_pack', '中身・瓶・ふた・ラベル', 'ガラス瓶・金属のふた')
C('food', 'sauce', 'ソース・ドレッシング・調味料', r'ソース|ドレッシング|調味料|たれ|タレ|醤油|ポン酢|スパイス', 'food', 'food.processed_oem packaging.container packaging.label_print', 'food_lic food_label food_pack', '中身・瓶やボトル・ラベル', 'ガラス瓶・PETボトル')
C('food', 'retort', 'レトルト食品・カレー', r'レトルト|カレー|スープ|パウチ食品', 'food', 'food.processed_oem packaging.label_print', 'food_lic food_label haccp', '中身・レトルトパウチ・化粧箱', 'アルミのレトルトパウチ')
C('food', 'frozen', '冷凍食品', r'冷凍食品|冷凍(の|で)', 'food', 'food.processed_oem packaging.label_print', 'food_lic food_label haccp', '中身・袋・箱', 'フィルム袋')
C('food', 'dried', 'ドライフルーツ・乾燥野菜', r'ドライフルーツ|乾燥野菜|干し|ドライ(マンゴー|いちじく)', 'food', 'food.processed_oem packaging.label_print', 'food_lic food_label', '中身・チャック袋・ラベル', 'チャック付き袋')
C('food', 'noodle', '麺類', r'麺|うどん|そば|ラーメン|パスタ', 'food', 'food.processed_oem packaging.label_print', 'food_lic food_label haccp', '中身・袋・スープ', 'フィルム袋')
C('food', 'bread', 'パン', r'パン(?!フレット|ツ)', 'food', 'food.processed_oem', 'food_lic food_label haccp', '中身・袋', 'フィルム袋')
C('food', 'snack', 'スナック菓子・ナッツ', r'スナック|ナッツ|ポテトチップ|おつまみ', 'food', 'food.processed_oem packaging.label_print', 'food_lic food_label', '中身・袋', 'アルミ蒸着袋')
C('food', 'gift', 'ギフトセット・詰め合わせ', r'ギフトセット|詰め合わせ|ギフトボックス', 'shape:box', 'packaging.box food.processed_oem', 'food_label premium', '中身・仕切り・化粧箱・のし', '紙箱・トレー')
# 飲料・健康食品
C('drink', 'juice', 'ジュース・清涼飲料', r'ジュース|清涼飲料|ソーダ|サイダー|ドリンク', 'cosme', 'food.beverage_oem packaging.container packaging.label_print', 'food_lic food_label', '中身・瓶や缶・ラベル', 'ガラス瓶・アルミ缶・PET')
C('drink', 'tea', 'お茶・ティーバッグ', r'お茶|ティーバッグ|紅茶|ハーブティー|緑茶', 'food', 'food.beverage_oem packaging.label_print', 'food_lic food_label', 'ティーバッグ・袋・箱', '不織布・アルミ袋')
C('drink', 'coffee', 'コーヒー（豆・ドリップバッグ）', r'コーヒー|珈琲|ドリップバッグ', 'food', 'food.beverage_oem packaging.label_print', 'food_lic food_label', '中身・袋（バルブ付き）・ラベル', 'アルミ袋')
C('drink', 'supplement', 'サプリメント', r'サプリ|錠剤|カプセル|健康食品', 'food', 'food.beverage_oem packaging.label_print', 'health nutri food_label', '中身（錠剤・カプセル）・袋や瓶', 'アルミ袋・PET瓶')
C('drink', 'protein', 'プロテイン・粉末飲料', r'プロテイン|粉末(飲料|ドリンク)|青汁', 'food', 'food.beverage_oem packaging.label_print', 'health nutri food_label', '中身・袋・スプーン', 'アルミ袋')
C('drink', 'water', 'ミネラルウォーター・オリジナルラベル水', r'ミネラルウォーター|ラベル水|名入れ水', 'cosme', 'food.beverage_oem packaging.label_print', 'food_label premium', '中身・ボトル・ラベル', 'PETボトル')
# アパレル・繊維
C('apparel', 'tshirt', 'Tシャツ', r'tシャツ|ティーシャツ|t-shirt', 'apparel', 'apparel.print_embroidery apparel.garment_oem', 'fiber origin', '生地・プリント・タグ', '綿・ポリエステル')
C('apparel', 'hoodie', 'パーカー・スウェット', r'パーカー|スウェット|トレーナー', 'apparel', 'apparel.garment_oem apparel.print_embroidery', 'fiber origin', '生地・リブ・プリントや刺繍', '綿・裏毛')
C('apparel', 'uniform', '制服・作業着・ユニフォーム', r'制服|作業着|ユニフォーム|ワークウェア', 'apparel', 'apparel.garment_oem apparel.print_embroidery', 'fiber', '生地・縫製・刺繍', 'ポリエステル・綿')
C('apparel', 'apron', 'エプロン', r'エプロン', 'apparel', 'manufacturing.textile apparel.print_embroidery', 'fiber', '生地・ひも・刺繍', '綿・帆布')
C('apparel', 'cap', '帽子・キャップ', r'帽子|キャップ|ハット|ビーニー', 'apparel', 'apparel.garment_oem apparel.print_embroidery apparel.knit', 'fiber', '本体・つば・刺繍', '綿・ポリエステル・ニット')
C('apparel', 'socks', '靴下', r'靴下|ソックス', 'apparel', 'apparel.knit', 'fiber', '編み地・ゴム', '綿・ナイロン')
C('apparel', 'knit', 'ニット・セーター・マフラー', r'ニット|セーター|マフラー|カーディガン', 'apparel', 'apparel.knit', 'fiber', '編み地', 'ウール・アクリル・綿')
C('apparel', 'sportswear', 'スポーツウェア・ヨガウェア', r'スポーツウェア|ヨガウェア|トレーニングウェア|ジャージ|ラッシュガード', 'apparel', 'apparel.garment_oem apparel.print_embroidery', 'fiber', '伸縮生地・縫製・プリント', 'ポリエステル・ポリウレタン')
C('apparel', 'jacket', 'ジャケット・アウター', r'ジャケット|アウター|コート|ブルゾン', 'apparel', 'apparel.garment_oem', 'fiber origin', '表地・裏地・ファスナー', 'ナイロン・ポリエステル')
C('apparel', 'underwear', 'インナー・肌着', r'インナー|肌着|下着|ブラ', 'apparel', 'apparel.garment_oem apparel.knit', 'fiber', '生地・ゴム', '綿・ナイロン')
C('apparel', 'shoes', '靴・サンダル', r'靴|シューズ|スニーカー|サンダル|ブーツ', 'apparel', 'apparel.leather', 'zakka origin', 'アッパー・中底・本底', '革・合成皮革・ゴム')
C('apparel', 'smartwear', 'センサー入りの衣類（スマートウェア）', r'スマートウェア|スマートテキスタイル|導電糸|センサー入り(の)?(服|ウェア|シャツ)', 'apparel', 'apparel.smart_textile electronics.flexible electronics.pcba testing.radio_cert', 'fiber giteki battery', '生地・導電糸や電極・取り外せる電子部品', 'ポリエステル・導電糸')
# バッグ・革小物
C('bag', 'tote', 'トートバッグ・エコバッグ', r'トート|エコバッグ|エコバック|手提げ', 'bag', 'manufacturing.textile apparel.print_embroidery', 'bag premium', '本体・持ち手・プリント', '綿キャンバス・ポリエステル')
C('bag', 'backpack', 'リュック・バックパック', r'リュック|バックパック|デイパック', 'bag', 'apparel.leather manufacturing.textile', 'bag origin', '本体・背あて・肩ベルト・ファスナー', 'ナイロン・ポリエステル')
C('bag', 'pouch', 'ポーチ・ペンケース', r'ポーチ|ペンケース|小物入れ', 'bag', 'manufacturing.textile', 'bag', '本体・ファスナー・裏地', 'ポリエステル・合成皮革')
C('bag', 'wallet', '財布・名刺入れ・キーケース', r'財布|名刺入れ|キーケース|カードケース|コインケース', 'case', 'apparel.leather', 'zakka origin', '本体・内装・金具', '牛革・合成皮革')
C('bag', 'leatherbag', '革のバッグ', r'革(の)?(バッグ|鞄|かばん)|レザーバッグ', 'bag', 'apparel.leather', 'bag origin', '本体・持ち手・金具・内装', '牛革・金属の金具')
C('bag', 'belt', 'ベルト・ストラップ', r'ベルト|ストラップ', 'collar', 'apparel.leather', 'zakka', 'ベルト・バックル', '革・ナイロン・金属')
# グッズ・ノベルティ
C('goods', 'acrylic', 'アクリルキーホルダー・アクリルスタンド', r'アクスタ|アクリル(スタンド|キーホルダー|ブロック)', 'goods', 'cosmetics.household packaging.label_print', 'premium origin', 'アクリル板・印刷・金具', 'アクリル')
C('goods', 'badge', '缶バッジ・ピンバッジ', r'缶バッジ|ピンバッジ|ピンズ|バッジ', 'goods', 'crafts.metal_goods', 'premium', '本体・留め具', '金属・エナメル')
C('goods', 'sticker', 'ステッカー・シール', r'ステッカー|シール', 'goods', 'packaging.label_print', 'premium', '印刷・台紙', '塩ビ・紙')
C('goods', 'mug', 'マグカップ・タンブラー（名入れ）', r'マグカップ|マグ|タンブラー', 'shape:bowl', 'crafts.ceramics_glass crafts.metal_goods', 'food_pack premium', '本体・印刷やレーザー刻印', '陶器・ステンレス')
C('goods', 'keychain', 'キーホルダー・チャーム', r'キーホルダー|チャーム|キーリング', 'goods', 'crafts.metal_goods manufacturing.silicone_molding', 'premium', '本体・金具', '金属・ラバー・アクリル')
C('goods', 'plush', 'ぬいぐるみ・マスコット', r'ぬいぐるみ|マスコット', 'shape:toy', 'manufacturing.textile', 'toy pl premium', '生地・わた・刺繍', 'ポリエステル')
C('goods', 'figure', 'フィギュア・模型', r'フィギュア|模型|ジオラマ', 'shape:toy', 'manufacturing.rapid_proto manufacturing.injection_molding', 'premium', '原型・成形品・塗装', 'PVC・レジン')
C('goods', 'calendar', 'カレンダー・ノベルティの印刷物', r'カレンダー|うちわ|クリアファイル|ポストカード', 'goods', 'packaging.label_print', 'premium', '印刷物', '紙・PP')
C('goods', 'medal', 'メダル・トロフィー・記念品', r'メダル|トロフィー|記念品|盾', 'goods', 'crafts.metal_goods crafts.wood_furniture', 'premium', '本体・台座・刻印', '金属・木・アクリル')
C('goods', 'smartaccessory', 'スマホアクセサリー（モバイルバッテリー・ケーブル）', r'モバイルバッテリー|充電ケーブル|ワイヤレス充電', 'device', 'electronics.pcba manufacturing.assembly testing.battery_safety', 'pse battery premium', '電池・基板・ケース・ケーブル', '樹脂・リチウムイオン電池')
# パッケージ・印刷
C('pack', 'giftbox', '化粧箱・ギフトボックス', r'化粧箱|ギフトボックス|貼り箱|パッケージ(箱)?', 'shape:box', 'packaging.box', '', '箱・中仕切り・印刷', '紙・板紙')
C('pack', 'label', 'ラベル・シール', r'ラベル', 'goods', 'packaging.label_print', '', '印刷・のり', '紙・フィルム')
C('pack', 'paperbag', '紙袋・ショッパー', r'紙袋|ショッパー|ショップバッグ', 'bag', 'packaging.box packaging.label_print', '', '袋・持ち手・印刷', 'クラフト紙・コート紙')
C('pack', 'bottle', 'ボトル・容器（特注）', r'ボトル|容器|ジャー|瓶', 'cosme', 'packaging.container manufacturing.injection_molding', 'food_pack', '本体・キャップ', 'PET・PP・ガラス')
C('pack', 'pouchbag', 'スタンドパウチ・袋', r'パウチ|スタンド袋|チャック袋', 'food', 'packaging.label_print', 'food_pack', '袋・チャック・印刷', 'PET・アルミ・PE')
C('pack', 'shippingbox', '配送用の段ボール箱', r'段ボール|ダンボール|配送箱', 'shape:box', 'packaging.box', '', '箱・印刷', '段ボール')
# 木工・家具・インテリア
C('wood', 'table', 'テーブル・机', r'テーブル|机|デスク', 'furniture', 'crafts.wood_furniture manufacturing.sheet_metal', 'zakka pl', '天板・脚・金具', '木・スチール')
C('wood', 'chair', '椅子・スツール', r'椅子|いす|チェア|スツール', 'furniture', 'crafts.wood_furniture', 'zakka pl', '座面・脚・背もたれ', '木・スチール・布')
C('wood', 'shelf', '棚・ラック', r'棚|ラック|シェルフ', 'furniture', 'crafts.wood_furniture manufacturing.sheet_metal', 'zakka pl', '側板・棚板・金具', '木・スチール')
C('wood', 'interior', 'インテリア雑貨（時計・フレーム・小物）', r'時計|フォトフレーム|写真立て|インテリア雑貨|置物', 'goods', 'crafts.wood_furniture crafts.metal_goods', 'zakka', '本体・金具', '木・金属')
C('wood', 'lamp', '照明器具・ランプ', r'照明|ランプ|ペンダントライト|スタンドライト', 'light', 'crafts.wood_furniture electronics.pcba manufacturing.assembly', 'pse', '笠・本体・光源・配線', '木・金属・LED')
C('wood', 'woodtoy', '木のおもちゃ・積み木', r'木のおもちゃ|積み木|木製玩具', 'shape:toy', 'crafts.wood_furniture', 'toy pl', '木の部品・塗装', '木・自然塗料')
C('wood', 'cuttingboard', 'カッティングボード・木のトレー', r'カッティングボード|まな板|木(の|製)トレー', 'goods', 'crafts.wood_furniture', 'food_pack', '板・焼印', '木')
# キッチン・食器
C('kitchen', 'tableware', '食器（皿・茶碗）', r'食器|皿|茶碗|小鉢|器', 'shape:bowl', 'crafts.ceramics_glass', 'food_pack zakka', '本体・釉薬・絵付け', '陶器・磁器')
C('kitchen', 'glass', 'グラス・タンブラー', r'グラス|コップ', 'shape:bowl', 'crafts.ceramics_glass', 'food_pack', '本体・印刷', 'ガラス')
C('kitchen', 'cutlery', 'カトラリー・調理器具', r'カトラリー|スプーン|フォーク|調理器具|フライパン|鍋|包丁', 'shape:tool', 'crafts.metal_goods', 'food_pack zakka', '本体・持ち手', 'ステンレス・木')
C('kitchen', 'bento', '弁当箱・保存容器', r'弁当箱|保存容器|ランチボックス', 'shape:box', 'manufacturing.injection_molding', 'food_pack zakka', '本体・ふた・パッキン', 'PP樹脂・シリコーン')
C('kitchen', 'bottle', '水筒・ボトル', r'水筒|ボトル|ステンレスボトル', 'cosme', 'crafts.metal_goods', 'food_pack', '本体・ふた・パッキン', 'ステンレス・PP')
C('kitchen', 'kitchengadget', 'キッチン家電（小型）', r'キッチン家電|ミキサー|ブレンダー|ホットプレート|電気ケトル|トースター', 'device', 'electronics.pcba manufacturing.injection_molding manufacturing.assembly testing.battery_safety', 'pse food_pack pl', '本体ケース・ヒーターやモーター・基板・電源', '樹脂・金属')
# アウトドア・スポーツ
C('outdoor', 'camptable', 'キャンプ用テーブル・チェア', r'キャンプ.{0,6}(テーブル|チェア|椅子)|アウトドア(テーブル|チェア)', 'furniture', 'manufacturing.sheet_metal crafts.wood_furniture', 'pl', '天板・脚・折りたたみ金具', 'アルミ・木')
C('outdoor', 'tent', 'テント・タープ', r'テント|タープ|シェルター', 'shape:cover', 'manufacturing.textile', 'pl', '幕体・ポール・ペグ', 'ポリエステル・アルミ')
C('outdoor', 'stove', 'ガスバーナー・焚き火台', r'焚き火台|焚火台|バーナー|コンロ|こんろ|ストーブ', 'machine', 'manufacturing.sheet_metal manufacturing.cnc', 'lpg pl', '本体・五徳・脚', 'ステンレス・鉄')
C('outdoor', 'lantern', 'ランタン・ライト', r'ランタン|ヘッドライト|懐中電灯', 'light', 'electronics.pcba manufacturing.assembly mechanical.waterproof', 'battery pse', 'ケース・LED・電池・スイッチ', 'アルミ・樹脂')
C('outdoor', 'cooler', 'クーラーボックス', r'クーラーボックス|保冷バッグ', 'shape:box', 'manufacturing.injection_molding manufacturing.textile', 'zakka', '外装・断熱材・ふた', 'PP・発泡ウレタン')
C('outdoor', 'sportsgear', 'スポーツ用品（ボール・ラケット・トレーニング器具）', r'ボール|ラケット|トレーニング(器具|用品)|ダンベル|ヨガマット', 'shape:tool', 'manufacturing.silicone_molding manufacturing.cnc', 'pl', '本体・グリップ', 'ゴム・樹脂・金属')
C('outdoor', 'fishing', '釣り用品', r'釣り|ルアー|ロッド', 'shape:tool', 'manufacturing.cnc manufacturing.rapid_proto', 'pl', '本体・金具', '樹脂・金属')
C('outdoor', 'bike', '自転車用品', r'自転車|サイクル', 'shape:holder', 'manufacturing.cnc manufacturing.sheet_metal', 'pl', '本体・取付金具', 'アルミ・樹脂')
# IoT・電子機器
C('iot', 'iotsensor', 'IoTセンサー（温湿度・開閉・人感）', r'温湿度センサ|開閉センサ|人感センサ|iotセンサ|環境センサ', 'sensor', 'electronics.pcba electronics.wireless sensing.environment electronics.low_power testing.radio_cert', 'giteki battery', '基板・センサー・電池・無線・ケース', '樹脂ケース')
C('iot', 'tracker', 'GPSトラッカー・見守り端末', r'gps|トラッカー|見守り端末|紛失防止', 'device', 'electronics.pcba electronics.wireless sensing.position electronics.low_power testing.radio_cert', 'giteki battery terminal', '基板・GPS・通信モジュール・電池・ケース', '樹脂ケース')
C('iot', 'remote', 'リモコン・スイッチ（スマート家電）', r'リモコン|スマートスイッチ|スマートプラグ|スマートホーム', 'device', 'electronics.pcba electronics.wireless electronics.firmware testing.radio_cert', 'giteki pse', '基板・ボタン・無線・ケース', '樹脂ケース')
C('iot', 'speaker', 'スピーカー・オーディオ機器', r'スピーカー|イヤホン|ヘッドホン|オーディオ', 'device', 'electronics.pcba electronics.wireless manufacturing.injection_molding testing.radio_cert', 'giteki battery pse', 'スピーカーユニット・基板・電池・ケース', '樹脂・金属')
C('iot', 'camera', 'カメラ付きの機器', r'カメラ|監視カメラ|防犯カメラ|ドラレコ', 'device', 'electronics.pcba electronics.wireless electronics.firmware mechanical.waterproof testing.radio_cert', 'giteki pse', 'カメラモジュール・基板・電源・ケース', '樹脂・アルミ')
C('iot', 'display', '表示器・サイネージ', r'サイネージ|表示器|ディスプレイ|電子看板', 'device', 'electronics.pcba manufacturing.sheet_metal manufacturing.assembly', 'pse', '液晶やLED・基板・筐体', '金属・樹脂')
C('iot', 'charger', '充電器・電源アダプター', r'充電器|acアダプター|電源アダプター|チャージャー', 'device', 'electronics.pcba electronics.low_power testing.battery_safety', 'pse', '基板・ケース・ケーブル', '難燃樹脂')
C('iot', 'drone', 'ドローン', r'ドローン|drone', 'drone', 'electronics.pcba electronics.wireless electronics.firmware manufacturing.rapid_proto testing.radio_cert', 'giteki battery', 'フレーム・モーター・制御基板・電池', '樹脂・カーボン')
C('iot', 'robot', 'ロボット・自動で動く機器', r'ロボット|自走|自動運転', 'machine', 'electronics.pcba electronics.firmware mechanical.enclosure_design manufacturing.cnc manufacturing.assembly', 'pse giteki battery pl', '駆動部・センサー・制御基板・電池・外装', 'アルミ・樹脂')
C('iot', 'devkit', '試作基板・評価ボード', r'評価ボード|試作基板|プロトタイプ基板|pcb', 'device', 'electronics.pcb_design electronics.pcba', '', '基板・部品', 'ガラスエポキシ（FR-4）')
# ウェアラブル・健康管理（医療機器を除く）
C('wear', 'band', 'スマートバンド・活動量計', r'スマートバンド|活動量計|リストバンド|スマートウォッチ', 'wearable', 'electronics.pcba sensing.motion electronics.low_power electronics.wireless mechanical.wearable_fit testing.radio_cert', 'giteki battery', '基板・センサー・電池・ベルト', '樹脂・シリコーン')
C('wear', 'ring', 'スマートリング', r'スマートリング|指輪型', 'wearable', 'electronics.pcba electronics.flexible sensing.biosignal.ppg mechanical.wearable_fit testing.radio_cert', 'giteki battery', '基板・センサー・電池・外装', 'チタン・樹脂')
C('wear', 'heartrate', '心拍・体温を測る機器（健康管理用）', r'心拍|体温計測|バイタル', 'wearable', 'sensing.biosignal sensing.temperature electronics.pcba testing.human_trial', 'giteki battery', 'センサー・基板・電池・装着部', '樹脂・シリコーン')
C('wear', 'posture', '姿勢・動きを記録するセンサー', r'姿勢|歩数|モーションセンサ|動きを記録', 'wearable', 'sensing.motion electronics.pcba electronics.wireless', 'giteki battery', '加速度センサー・基板・電池・クリップ', '樹脂')
# 機械・装置・治具
C('mech', 'jig', '治具・作業台', r'治具|ジグ|作業台|固定具', 'shape:tool', 'manufacturing.cnc manufacturing.sheet_metal', '', '本体・位置決めピン・クランプ', 'アルミ・鉄・樹脂')
C('mech', 'conveyor', '搬送装置・コンベア', r'コンベア|搬送装置|搬送機', 'machine', 'mechanical.enclosure_design manufacturing.sheet_metal manufacturing.assembly electronics.pcba', 'pse pl', 'フレーム・ベルト・モーター・制御盤', 'アルミフレーム・鋼材')
C('mech', 'cart', '台車・運搬カート', r'台車|運搬カート|搬送カート|ワゴン', 'cart', 'manufacturing.sheet_metal manufacturing.assembly', 'pl', 'フレーム・天板・キャスター・ハンドル', 'スチール・アルミ')
C('mech', 'lift', 'リフト・昇降装置', r'リフト|昇降(装置|機|台)|リフター', '', 'mechanical.enclosure_design manufacturing.sheet_metal manufacturing.cnc manufacturing.assembly testing.battery_safety', 'pl pse', '昇降機構・フレーム・駆動部・操作部', '鋼材・アルミ')
C('mech', 'mower', '草刈り機・芝刈り機', r'草刈|芝刈', 'lawn_mower', 'mechanical.enclosure_design manufacturing.sheet_metal manufacturing.assembly electronics.pcba', 'pl pse battery', '刃・モーター・車輪・電池・外装', '鋼材・樹脂')
C('mech', 'machine', '自動化装置・専用機', r'自動化|専用機|装置|省力化', 'machine', 'mechanical.enclosure_design manufacturing.cnc manufacturing.sheet_metal manufacturing.assembly electronics.firmware', 'pl pse', 'フレーム・駆動部・センサー・制御盤', 'アルミフレーム・鋼材')
C('mech', 'enclosure', '筐体・ケース（機器用）', r'筐体|ケース|ハウジング|カバー', 'case', 'mechanical.enclosure_design manufacturing.sheet_metal manufacturing.injection_molding', '', '本体・ふた・ねじ', '鋼板・アルミ・樹脂')
# 金属・樹脂の部品
C('parts', 'cncpart', '切削加工の部品', r'切削|旋盤|フライス|削り出し', 'shape:tool', 'manufacturing.cnc', '', '部品', 'アルミ・ステンレス・樹脂')
C('parts', 'sheetpart', '板金の部品・ブラケット', r'板金|ブラケット|曲げ加工|レーザー加工', 'shape:holder', 'manufacturing.sheet_metal', '', '部品', '鋼板・ステンレス・アルミ')
C('parts', 'moldpart', '樹脂の成形部品', r'射出成形|成形品|樹脂部品|プラスチック部品', 'case', 'manufacturing.injection_molding', '', '成形品・金型', 'ABS・PP・PC')
C('parts', 'rubberpart', 'ゴム・シリコーンの部品', r'シリコーン|シリコン|ゴム部品|パッキン', 'case', 'manufacturing.silicone_molding', '', '成形品・型', 'シリコーンゴム')
C('parts', 'print3d', '3Dプリントの試作品', r'3dプリント|3dプリンタ|積層造形', 'shape:product', 'manufacturing.rapid_proto', '', '造形品', 'PLA・ナイロン・レジン')
C('parts', 'casting', '鋳物・ダイカスト部品', r'鋳物|鋳造|ダイカスト', 'shape:tool', 'crafts.metal_goods manufacturing.cnc', '', '鋳造品・仕上げ加工', 'アルミ・鉄・真鍮')
# 福祉・介護・暮らしの補助（医療機器を除く）
C('care', 'handrail', '手すり・つかまり台', r'手すり|手摺|つかまり', 'shape:holder', 'manufacturing.sheet_metal crafts.wood_furniture', 'pl', '手すり・取付金具', 'ステンレス・木')
C('care', 'rampcare', '段差スロープ（家・車いす用）', r'段差(スロープ|解消)|車(椅子|いす)用?スロープ', 'shape:slope', 'manufacturing.sheet_metal manufacturing.injection_molding', 'pl', '本体・滑り止め', 'アルミ・樹脂・ゴム')
C('care', 'cane', '杖・歩行補助具', r'杖|ステッキ|歩行補助|シルバーカー', 'shape:tool', 'manufacturing.cnc manufacturing.sheet_metal', 'pl psc', '本体・グリップ・先ゴム', 'アルミ・ゴム')
C('care', 'caretools', '介護用品（食事・入浴・移乗の補助具）', r'介護用品|介助|移乗|入浴補助|食事補助|自助具', 'shape:tool', 'manufacturing.injection_molding manufacturing.sheet_metal manufacturing.textile', 'pl', '本体・持ち手', '樹脂・金属・布')
C('care', 'monitor', '見守りセンサー（高齢者向け）', r'見守り(センサ|機器)|高齢者.{0,8}(センサ|見守)', 'sensor', 'electronics.pcba electronics.wireless sensing.biosignal.radar testing.radio_cert', 'giteki pse', 'センサー・基板・通信・ケース', '樹脂ケース')
C('care', 'carebed', '介護用のクッション・体位を支える用品', r'体位|床ずれ|ポジショニング|介護.{0,4}(クッション|マット)', 'shape:bed', 'manufacturing.textile', 'fiber', 'カバー・中材', 'ウレタン・ポリエステル')
# ベビー・キッズ・玩具
C('kids', 'babygoods', 'ベビー用品（スタイ・ブランケット）', r'ベビー|赤ちゃん|スタイ|よだれかけ|おくるみ', 'apparel', 'manufacturing.textile apparel.knit', 'fiber toy', '生地・縫製', '綿・ガーゼ')
C('kids', 'toy', 'おもちゃ・知育玩具', r'おもちゃ|玩具|知育|パズル', 'shape:toy', 'manufacturing.injection_molding crafts.wood_furniture manufacturing.rapid_proto', 'toy pl psc', '本体・部品・塗装', '樹脂・木')
C('kids', 'kidsfurniture', '子ども用の家具', r'子ども(用)?(の)?(家具|椅子|机)|キッズチェア|ベビーチェア', 'furniture', 'crafts.wood_furniture', 'pl psc', '座面・脚・ベルト', '木・樹脂')
C('kids', 'schoolbag', '通園・通学のバッグ・グッズ', r'通園|通学|上履き入れ|レッスンバッグ|ランドセル', 'bag', 'manufacturing.textile apparel.leather', 'bag', '本体・持ち手・名札', 'キャンバス・ナイロン・人工皮革')
# 車・バイク・自転車用品
C('car', 'carholder', '車内用ホルダー・収納', r'車内|車載|カーホルダー|ドリンクホルダー', 'shape:holder', 'manufacturing.injection_molding manufacturing.rapid_proto', 'pl', '本体・取付部', '樹脂')
C('car', 'carcover', 'シートカバー・カバー類', r'シートカバー|カーカバー|ボディカバー', 'shape:cover', 'manufacturing.textile', 'fiber', '生地・ゴム・ひも', 'ポリエステル')
C('car', 'roofbox', 'ルーフボックス・キャリア', r'ルーフ(ボックス|キャリア)|ヒッチ|キャリア', 'shape:box', 'manufacturing.sheet_metal manufacturing.injection_molding', 'pl', '本体・取付金具・鍵', 'ABS・アルミ')
C('car', 'motorbike', 'バイク用品', r'バイク|オートバイ|ツーリング', 'shape:holder', 'manufacturing.cnc manufacturing.textile', 'pl', '本体・取付部', 'アルミ・ナイロン')
# 園芸・農業資材
C('garden', 'planter', 'プランター・植木鉢', r'プランター|植木鉢|鉢', 'shape:box', 'crafts.ceramics_glass manufacturing.injection_molding', 'zakka', '本体・受け皿', '陶器・樹脂')
C('garden', 'gardentool', '園芸用品・農具', r'園芸|農具|ガーデニング|スコップ|じょうろ', 'shape:tool', 'crafts.metal_goods manufacturing.injection_molding', 'pl', '本体・持ち手', '鉄・ステンレス・樹脂')
C('garden', 'agrisensor', '農業用センサー・水やりの自動化', r'農業.{0,6}センサ|圃場|自動水やり|灌水|ハウス栽培', 'sensor', 'electronics.pcba electronics.wireless sensing.environment mechanical.waterproof testing.radio_cert', 'giteki', 'センサー・基板・電池や太陽電池・防水ケース', '樹脂ケース')
C('garden', 'fence', '柵・フェンス・ゲート', r'柵|フェンス|ゲート', 'shape:fence', 'manufacturing.sheet_metal crafts.wood_furniture', 'pl', '柱・枠・金具', 'アルミ・木・スチール')
# 店舗・施設の什器・サイン
C('store', 'display', '陳列什器・ディスプレイ台', r'什器|陳列|ディスプレイ(台|棚)|ポップ', 'furniture', 'crafts.wood_furniture manufacturing.sheet_metal', '', '棚・台・パネル', '木・スチール・アクリル')
C('store', 'sign', '看板・サイン', r'看板|サイン|表札|案内板', 'shape:platform', 'manufacturing.sheet_metal packaging.label_print', 'pse', '板・文字・取付金具・照明', 'アルミ複合板・アクリル・LED')
C('store', 'menu', 'メニュー表・卓上POP', r'メニュー(表|ブック)|卓上pop|ポップ', 'goods', 'packaging.label_print', '', '印刷物・スタンド', '紙・アクリル')
C('store', 'partition', '仕切り・パーテーション', r'パーテーション|パーティション|仕切り|衝立', 'shape:fence', 'crafts.wood_furniture manufacturing.sheet_metal', '', 'パネル・脚', 'アクリル・木・アルミ')
C('store', 'hanger', 'ハンガー・フック・ブラケット', r'ハンガー|フック|ブラケット', 'shape:holder', 'manufacturing.sheet_metal crafts.metal_goods', '', '本体・取付部', 'スチール・真鍮')
C('store', 'amenity', 'ホテルのアメニティ', r'アメニティ', 'cosme', 'cosmetics.oem cosmetics.household packaging.label_print', 'cosme', '中身・小分け容器・個包装', 'PET・フィルム')

# 作例の型（ideas.P）→ 法規制のキー
PROF_REG = {'cosme': 'cosme', 'household': 'zakka', 'petfood': 'petfood food_label', 'food': 'food_lic food_label haccp', 'supp': 'health nutri food_label',
            'textile': 'fiber', 'box': '', 'ceramic': 'food_pack', 'metal': 'zakka', 'wood': 'zakka', 'goods': 'premium', 'sheet': 'pl', 'iot': 'giteki battery',
            'mold': '', 'proto3d': ''}
IDEA_IND = {'pet': 'pet', 'outdoor': 'outdoor', 'cafe': 'food', 'salon': 'cosme', 'hotel': 'daily', 'shop': 'goods', 'farm': 'food', 'gym': 'apparel',
            'promo': 'goods', 'mfg': 'parts', 'hw': 'iot'}


def _lot(proc):
    """工程ごとの最低ロット・費用の目安（estimates.py の出典つきの行だけ）"""
    out = []
    for p in proc:
        for r in estimates.EST.get(p, {}).get('rows', []):
            if r.get('k') in ('moq', 'init', 'unit') and r.get('s'):
                s = estimates.SRC[r['s']]
                out.append(dict(proc=p, k=r['k'], t=r['t'], lo=r['lo'], hi=r['hi'], u=r['u'], src=dict(t=s['t'], url=s['url'], date=s.get('date', ''), level=s['level'])))
    return out[:6]


def _reg(keys):
    return [dict(t=REG[k][0], src=dict(t=REG[k][1], url=REG[k][2], level='official')) for k in keys if k]


def _kind(name):
    """製品名から、製品イメージ案の種類（concepts.py → concepts_generic.py の順）を決める"""
    t = name.lower()
    for c in concepts.C:
        if c.get('kw') and re.search(c['kw'], t, re.I):
            return c['id']
    for s in concepts_generic.SHAPES:
        if s['id'] != 'product' and s.get('kw') and re.search(s['kw'], t, re.I):
            return 'shape:' + s['id']
    return ''


# ---- 日本標準商品分類（総務省、平成2年6月改定）をすべて取り込む（e-Stat の分類検索から。tools/data/jscc_1990.tsv）
# 工程・法規制・業界は、上位の分類ごとの決まり（JRULES、tools/jscc_rules.py）から引く。構成・素材は入れない（要確認）。
# 扱わない分野（原料・エネルギー、スクラップ、酒類・医薬品・医療機器・たばこ・武器）は JRULES で None にして取り込まない。
import unicodedata  # noqa: E402
import jscc_rules  # noqa: E402

JSCC_SRC = dict(t='総務省「日本標準商品分類（平成2年6月改定）」（e-Stat 統計分類）', url='https://www.e-stat.go.jp/classifications/terms/30', level='official')
_GENERIC = re.compile(r'^(その他|他に分類されない|.{0,2}(登録|無登録)$|.*(のもの|以外のもの)$|.*部分品・取付具・附属品$)')


def _norm(x):
    return unicodedata.normalize('NFKC', x).lower()


_ATTR = re.compile(r'^.{1,8}(式|型|形|製|用|系|級|品種)$')


def _kws(name, parent):
    """名前から探す語をつくる（かっこ書きを外し、「、」で分ける。短すぎる語・あいまいな語は使わない）"""
    base = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
    if not base or _GENERIC.match(base) or _ATTR.match(base):
        return ''
    out = []
    for w in re.split(r'[、，,]|及び|並びに', base):
        w = _norm(w.strip(' 　・'))
        w = re.sub(r'^(その他の|各種)', '', w)
        if len(w) >= 2 and w != _norm(parent) and not re.fullmatch(r'[\d.]+.*', w):
            out.append(w)
    return '|'.join(dict.fromkeys(out))


def jscc():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'jscc_1990.tsv')
    if not os.path.exists(path):
        return None
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            if '\t' in line and not line.startswith('#'):
                c, n = line.rstrip('\n').split('\t', 1)
                rows.append((c.strip(), n.strip()))
    rows.sort(key=lambda r: r[0])
    names = dict(rows)

    def rule(code):
        for k in range(len(code), 1, -1):
            if code[:k] in jscc_rules.R:
                return jscc_rules.R[code[:k]]
        return None
    items, used = [], {}
    for c, n in rows:
        r = rule(c)
        if r is None:
            continue
        parent = ''
        for k in range(len(c) - 1, 1, -1):
            if c[:k] in names:
                parent = names[c[:k]]
                break
        k = _kws(n, parent)
        items.append([c, n, 1 if k == _norm(n) else k])
    codes = [i[0] for i in items]
    anc = {c[:k] for c in codes for k in range(2, len(c))}
    items = [i for i in items if i[2] or i[0] in anc]
    rules = {}
    for k, r in jscc_rules.R.items():
        if r is not None:
            rules[k] = {x: v for x, v in dict(ind=r.get('ind', ''), proc=r.get('proc', '').split(), reg=r.get('reg', '').split(), kind=r.get('kind', '')).items() if v}
    return dict(src=JSCC_SRC, rules=rules, items=items)


def build():
    rows = []
    for c in CAT:
        rows.append(dict(id='c_' + c['ind'] + '_' + c['id'], name=c['name'], ind=c['ind'], kw=c['kw'], kind=c['kind'] or '', proc=c['proc'],
                         parts=c['parts'], mat=c['mat'], pl='ai', lot=_lot(c['proc']), reg=_reg(c['reg']), src=[], from_='catalog'))
    for i in ideas.I_:
        name = i['t'][0]
        prof = ideas.P[i['prof']]
        reg = _reg(PROF_REG.get(i['prof'], '').split())
        refs = [dict(t='KATACHIの作例「' + name + '」', url=SITE + '/idea/' + i['k'] + '/', level='site')]
        refs += [dict(t='KATACHIのガイド', url=SITE + '/guide/' + g + '/', level='site') for g in i['guides']]
        rows.append(dict(id='i_' + i['k'], name=name, ind=IDEA_IND.get(i['ind'], 'goods'), kw='', kind=_kind(name + ' ' + i['idea']), proc=[i['code']],
                         parts=[], mat=[], pl='', lot=_lot([i['code']]), reg=reg, src=refs, from_='idea',
                         example=dict(qty=i['lot'][0], text=i['idea'], src=refs[0]),
                         note=[dict(t=x, src=refs[-1] if len(refs) > 1 else refs[0]) for x in prof.get('check', [])][:3]))
    for c in concepts.C:
        rows.append(dict(id='k_' + c['id'], name=c['name'][0], ind='', kw=c.get('kw') or '', kind=c['id'], proc=[], parts=[x[0] for x in c['feats']][:6],
                         mat=[c['mat'][0]], pl='ai', lot=[], reg=[], src=[], from_='concept', size=c['size'][0]))
    for s in concepts_generic.SHAPES:
        if s['id'] == 'product':
            continue
        rows.append(dict(id='s_' + s['id'], name=s['name'][0], ind='', kw=s.get('kw') or '', kind='shape:' + s['id'], proc=[], parts=[x[0] if isinstance(x, (list, tuple)) else x for x in s.get('feats', [])][:6],
                         mat=[s['mat'][0] if isinstance(s['mat'], (list, tuple)) else s['mat']], pl='ai', lot=[], reg=[], src=[], from_='concept'))
    for r in rows:
        r['from'] = r.pop('from_')
    ids = [r['id'] for r in rows]
    assert len(ids) == len(set(ids)), 'id が重複しています'
    for r in rows:
        if r['kw']:
            re.compile(r['kw'])
    J = jscc()
    out = dict(updated=UPDATED, levels={'official': '公的機関・会社の公式ページ', 'article': '報道・記事', 'listing': '業者の掲載ページ・まとめ', 'site': 'KATACHIの作例・ガイド（中に出典）', 'ai': 'AI推定（よくある例）'},
                ind=IND, products=rows)
    if J:
        procs = sorted({p for r in J['rules'].values() for p in r.get('proc', [])})
        out['lots'] = {p: [{k: v for k, v in x.items() if k != 'proc'} for x in _lot([p])] for p in procs}
        out['lots'] = {p: v for p, v in out['lots'].items() if v}
        out['regs'] = {k: _reg([k])[0] for k in REG}
        out['jscc'] = J
    return out


def stats(db):
    from collections import Counter
    rows = db['products']
    by_from = Counter(r['from'] for r in rows)
    by_ind = Counter(db['ind'].get(r['ind'], '種類の型') for r in rows)
    sourced = sum(1 for r in rows if r['lot'] or r['reg'] or r['src'])
    if db.get('jscc'):
        by_from['jscc'] = len(db['jscc']['items'])
    return by_from, by_ind, sourced


def main(root='.'):
    db = build()
    os.makedirs(os.path.join(root, 'data'), exist_ok=True)
    with open(os.path.join(root, 'data', 'products.json'), 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, separators=(',', ':'))
    return db


if __name__ == '__main__':
    db = main(sys.argv[1] if len(sys.argv) > 1 else '.')
    f, i, s = stats(db)
    print(len(db['products']), '件', dict(f))
    print(dict(i))
    print('出典つきの項目（ロット・法規制・ページ）がある製品:', s)
