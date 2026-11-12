"""概算の目安（初期費用・単価・最低ロット・最低発注額）。

- 数字はすべて下の出典に書かれていたものだけ。足し算・割り算・ドル換算は画面で行い、「計算」と明示する。
- 出典に数字がない工程は入れない（画面では「公開相場なし・見積が必要」と出す）。
- 確定見積ではない。工場の見積で必ず変わる。
- 調べた日: 2026-11-12（出典ごとの掲載年は src の date）。数字を更新したら RETRIEVED も直す。
- 新しい文言は T_EST に英語・中国語も足す（i18n.py が読み込む）。

build.py が data.js に `est` として入れる。
"""
RETRIEVED = '2026-11-12'
USDJPY = 150  # ドル→円の換算に使う仮定のレート（画面に明記）

# level: official=会社・公的機関の料金表 / article=報道・記事 / listing=業者の掲載ページ・まとめサイト / rough=根拠の書かれていない目安
SRC = {
    'meviy': dict(t='ミスミ meviy パンフレット（価格例）', url='https://jp.meviy.misumi-ec.com/info/ja/wp-content/uploads/2024/06/meviy_brochure20240601.pdf', date='2024-06', level='official'),
    'monoist15': dict(t='MONOist「コストは金型代だけじゃない!」', url='https://monoist.itmedia.co.jp/mn/articles/1504/24/news001.html', date='2015-04', level='article'),
    'mynavi15': dict(t='マイナビニュース TECH+（プロトラブズ）', url='https://news.mynavi.jp/techplus/article/protolabs-54/', date='2015-09', level='article'),
    'rapiddirect': dict(t='RapidDirect「少量の射出成形」', url='https://www.rapiddirect.com/ja/blog/low-volume-injection-molding/', date='', level='listing'),
    'monoist16': dict(t='MONOist「DMM.makeでミニ四駆ボディー」', url='https://monoist.itmedia.co.jp/mn/articles/1605/10/news011.html', date='2016-05', level='article'),
    'imitsu3d': dict(t='アイミツ「3Dプリント出力サービス比較」', url='https://imitsu.jp/list/printing/3d-printing-service-comparison', date='', level='listing'),
    'jlc3dp': dict(t='JLC3DP「3Dプリントのコスト」', url='https://jlc3dp.com/jp/blog/estimate-3d-printing-cost', date='', level='listing'),
    'xeffect': dict(t='イプロス「真空注型サービス」（クロスエフェクト）', url='https://mono.ipros.com/cg3/%E7%9C%9F%E7%A9%BA%E6%B3%A8%E5%9E%8B%E3%82%B5%E3%83%BC%E3%83%93%E3%82%B9/', date='', level='listing'),
    'jlcpcba': dict(t='JLCPCB「PCB assembly price」', url='https://jlcpcb.com/help/article/pcb-assembly-price', date='', level='official'),
    'jlcpcb2': dict(t='EasyEDA「JLCPCBで基板10枚2ドル」', url='https://easyeda.com/Amy14/Prototype_PCBs_for_Only_2_with_JLCPCB-ac671d662f06446f8930849caa25f641', date='', level='listing'),
    'atsoho': dict(t='@SOHO「基板設計の単価の相場」', url='https://atsoho.com/blog/kicad-pcb-design-side-hustle-2026', date='2026-08', level='rough'),
    'imitsuapp': dict(t='アイミツ「アプリ開発の費用相場」', url='https://imitsu.jp/matome/app-developer/5622501620282270', date='2025-01', level='listing'),
    'telec': dict(t='TELEC 技術基準適合証明 手数料表', url='https://telec.or.jp/services/tech/files/giteki_charge4.pdf', date='', level='official'),
    'ckbgoods': dict(t='THE CKB「小ロットのオリジナルグッズ」', url='https://www.theckb.com/archive/how-to-make-small-lot-original-goods/', date='', level='listing'),
    'ckbapparel': dict(t='THE CKB「小ロットのアパレルOEM」', url='https://www.theckb.com/archive/how-to-start-a-small-lot-apparel-oem-even-for-the-faint-of-heart/', date='', level='listing'),
    'ckb200': dict(t='THE CKB（アパレルOEM 1カラー200点）', url='https://www.theckb.com/?p=26984', date='', level='listing'),
    'ecnomikata': dict(t='ECのミカタ（アパレルOEM）', url='https://ecnomikata.com/column/6971/', date='', level='article'),
    'jpcosme': dict(t='日本郵便「化粧品OEMの費用と最小ロット」', url='https://www.post.japanpost.jp/bizpost/column/sales_promotion22/cosmetics-oem/', date='', level='article'),
    'miyagi': dict(t='宮城県「みやぎOEM」事業者一覧', url='https://www.pref.miyagi.jp/site/miyagi_oem/jigyosha/index.html', date='', level='official'),
    'imitsubox': dict(t='アイミツ「小ロットの化粧箱」', url='https://imitsu.jp/list/printing/cosmetic-box-small-lot', date='', level='listing'),
    'nikoniko': dict(t='楽天 にこにこ雑貨「OEM」', url='https://www.rakuten.co.jp/nikonikozakka/contents/oem/', date='', level='listing'),
}

# 行の種類 k: init=初期費用 / unit=単価 / moq=最低ロット / min=最低発注額 / fee=費用 / note=補足
# u: yen=円 / usd=ドル / pcs=個 / yen_cm3=円/cm3 / none=数字なし
# calc（概算の足し算に使う。出典の数字そのもの）:
#   init=[lo,hi] 円（初期費用）, unit=[lo,hi] 円/個, fixed=[lo,hi] 円（数量によらない費用）, usd_fixed=[lo,hi] ドル,
#   tiers=[[数量,lo,hi],...] 円/個（その数量以上の単価）, qmax/qmin=この数量の範囲でだけ合計に入れる（出典の「向く数量」）, assume=前提（画面に出す）
EST = {
 'manufacturing.injection_molding': dict(rows=[
    dict(k='init', t='試作・少量向けの金型（プロトラブズの例）', lo=300000, hi=400000, u='yen', s='monoist15'),
    dict(k='init', t='アルミ金型（CNC加工）', lo=2000, hi=5000, u='usd', s='rapiddirect'),
    dict(k='init', t='国内で量産金型を見積もった例', lo=3000000, hi=3000000, u='yen', s='monoist15'),
    dict(k='init', t='大量生産用の鉄製金型', lo=5000000, hi=6000000, u='yen', s='mynavi15'),
    dict(k='init', t='金型の修正1回', lo=100000, hi=200000, u='yen', s='monoist15'),
    dict(k='moq', t='アルミ金型が向く数量', lo=100, hi=10000, u='pcs', s='rapiddirect'),
    dict(k='note', t='成形1個あたりの単価は形・樹脂で大きく変わり、公開された相場は見つかっていません。', u='none'),
  ], calc=dict(init=[300000, 3000000], qmin=100, assume='金型代のみ（試作向け30万円〜国内量産300万円）。成形単価・材料費は別')),
 'manufacturing.cnc': dict(rows=[
    dict(k='unit', t='1個の価格例（50mm角の樹脂〜200mmのステンレス）', lo=3900, hi=52220, u='yen', s='meviy'),
    dict(k='unit', t='丸物1個の価格例（φ50樹脂〜φ128鉄）', lo=8016, hi=27510, u='yen', s='meviy'),
    dict(k='moq', t='最低ロット', lo=1, hi=1, u='pcs', s='meviy'),
    dict(k='note', t='丸物は101個以上で最大70%引き。数量割引は概算に入れていません。', u='none', s='meviy'),
  ], calc=dict(unit=[3900, 52220], assume='1個の価格例×数量（数量割引なし）')),
 'manufacturing.sheet_metal': dict(rows=[
    dict(k='unit', t='1個の価格例（アルミ・鉄・ステンレスの曲げ品など）', lo=3110, hi=5830, u='yen', s='meviy'),
    dict(k='moq', t='最低ロット', lo=1, hi=1, u='pcs', s='meviy'),
    dict(k='note', t='101個以上で最大60%引き。数量割引は概算に入れていません。', u='none', s='meviy'),
  ], calc=dict(unit=[3110, 5830], assume='1個の価格例×数量（数量割引なし）')),
 'manufacturing.rapid_proto': dict(rows=[
    dict(k='unit', t='ナイロン造形の体積単価（DMM.make）', lo=112, hi=112, u='yen_cm3', s='imitsu3d'),
    dict(k='unit', t='手のひら大のボディ1個（ナイロン造形）', lo=3000, hi=4000, u='yen', s='monoist16'),
    dict(k='moq', t='最低ロット', lo=1, hi=1, u='pcs', s='monoist16'),
    dict(k='moq', t='3Dプリントが向く数量（100個未満）', lo=1, hi=99, u='pcs', s='rapiddirect'),
    dict(k='min', t='金属3Dプリントの最低注文額（よくある条件）', lo=500, hi=500, u='usd', s='jlc3dp'),
  ], calc=dict(unit=[3000, 4000], qmax=99, assume='手のひら大のナイロン造形1個×数量。大きさで大きく変わる')),
 'manufacturing.silicone_molding': dict(rows=[
    dict(k='moq', t='真空注型（シリコン型）で受ける数量', lo=1, hi=1000, u='pcs', s='xeffect'),
    dict(k='note', t='型代・単価は各社とも「応相談」で、公開された金額は見つかっていません。', u='none'),
  ]),
 'electronics.pcba': dict(rows=[
    dict(k='fee', t='基板10枚（10cm角まで）の製造', lo=2, hi=2, u='usd', s='jlcpcb2'),
    dict(k='init', t='実装の段取り費', lo=8.18, hi=51.12, u='usd', s='jlcpcba'),
    dict(k='init', t='メタルマスク', lo=1.53, hi=16.42, u='usd', s='jlcpcba'),
    dict(k='unit', t='はんだ付け1点あたり', lo=0.0016, hi=0.0164, u='usd', s='jlcpcba'),
    dict(k='note', t='中国の格安サービスの例です。部品代・送料・関税は別。国内の実装会社の公開相場は見つかっていません。', u='none'),
  ], calc=dict(usd_fixed=[11.71, 69.54], qmax=10, assume='中国の格安サービスで基板10枚まで（基板＋段取り＋マスク）。部品代・送料は別')),
 'electronics.pcb_design': dict(rows=[
    dict(k='fee', t='シンプルな2層基板の設計（1件）', lo=30000, hi=30000, u='yen', s='atsoho'),
    dict(k='fee', t='一般的な4層基板の設計（1件）', lo=50000, hi=150000, u='yen', s='atsoho'),
    dict(k='note', t='根拠の調査データが示されていない目安です。高速信号・電源を含むと20万円を超えることもあるとされています。', u='none', s='atsoho'),
  ], calc=dict(fixed=[30000, 150000], assume='基板1枚の設計（2層〜4層）')),
 'software.mobile_app': dict(rows=[
    dict(k='fee', t='ツール系アプリの開発費', lo=500000, hi=3000000, u='yen', s='imitsuapp'),
    dict(k='fee', t='アプリ開発の平均', lo=2500000, hi=None, u='yen', s='imitsuapp'),
    dict(k='note', t='機器とBluetoothでつなぐアプリの公開相場は見つかっていません。', u='none'),
  ], calc=dict(fixed=[500000, 3000000], assume='ツール系アプリの相場')),
 'testing.radio_cert': dict(rows=[
    dict(k='fee', t='技適（2.4GHz帯）申込の基本料', lo=36000, hi=36000, u='yen', s='telec'),
    dict(k='fee', t='1台目の試験手数料', lo=38000, hi=38000, u='yen', s='telec'),
    dict(k='note', t='TELECで技術基準適合証明を受ける場合の手数料です。技適を取った無線モジュールを使うと、製品としての取得が不要になる場合があります。', u='none', s='telec'),
  ], calc=dict(fixed=[74000, 74000], assume='TELECの手数料（申込＋1台目の試験）')),
 'apparel.garment_oem': dict(rows=[
    dict(k='moq', t='簡易OEM（無地＋プリント）', lo=10, hi=10, u='pcs', s='ckbapparel'),
    dict(k='moq', t='スポーツウェア', lo=30, hi=30, u='pcs', s='ckbapparel'),
    dict(k='moq', t='1カラーあたり', lo=50, hi=50, u='pcs', s='ecnomikata'),
    dict(k='moq', t='一般的なアパレル（1カラーあたり）', lo=200, hi=200, u='pcs', s='ckb200'),
    dict(k='note', t='生地は1反（約200〜300枚分）単位で買うことが多く、少ない数量では割高になります。', u='none', s='ckbapparel'),
  ]),
 'apparel.print_embroidery': dict(rows=[
    dict(k='unit', t='Tシャツ片面1色シルク印刷 10枚', lo=2500, hi=2500, u='yen', s='ckbgoods'),
    dict(k='unit', t='同 30枚', lo=1800, hi=1800, u='yen', s='ckbgoods'),
    dict(k='unit', t='同 50枚', lo=1500, hi=1500, u='yen', s='ckbgoods'),
    dict(k='unit', t='同 100枚', lo=1200, hi=1200, u='yen', s='ckbgoods'),
    dict(k='min', t='10枚の合計', lo=25000, hi=25000, u='yen', s='ckbgoods'),
  ], calc=dict(tiers=[[10, 2500, 2500], [30, 1800, 1800], [50, 1500, 1500], [100, 1200, 1200]], assume='Tシャツ片面1色シルク印刷の相場')),
 'cosmetics.oem': dict(rows=[
    dict(k='unit', t='化粧水・美容液など 100個〜', lo=900, hi=2000, u='yen', s='jpcosme'),
    dict(k='unit', t='同 500個〜', lo=800, hi=1000, u='yen', s='jpcosme'),
    dict(k='unit', t='同 1,000個〜', lo=600, hi=800, u='yen', s='jpcosme'),
    dict(k='moq', t='化粧水・美容液・乳液', lo=100, hi=1000, u='pcs', s='jpcosme'),
    dict(k='moq', t='リップ', lo=500, hi=3000, u='pcs', s='jpcosme'),
    dict(k='moq', t='ファンデーション（パウダー）', lo=1000, hi=5000, u='pcs', s='jpcosme'),
    dict(k='moq', t='固形石けん', lo=100, hi=300, u='pcs', s='jpcosme'),
  ], calc=dict(tiers=[[100, 900, 2000], [500, 800, 1000], [1000, 600, 800]], assume='化粧水・美容液などの相場')),
 'food.processed_oem': dict(rows=[
    dict(k='moq', t='菓子', lo=100, hi=100, u='pcs', s='miyagi'),
    dict(k='moq', t='レトルト', lo=250, hi=500, u='pcs', s='miyagi'),
    dict(k='moq', t='冷凍惣菜', lo=2000, hi=2000, u='pcs', s='miyagi'),
    dict(k='moq', t='缶詰', lo=2000, hi=5000, u='pcs', s='miyagi'),
    dict(k='note', t='宮城県の食品OEM事業者の掲載条件です。価格は掲載されていません。', u='none', s='miyagi'),
  ]),
 'food.beverage_oem': dict(rows=[
    dict(k='moq', t='200mlびん', lo=500, hi=500, u='pcs', s='miyagi'),
    dict(k='moq', t='500mlびん', lo=200, hi=200, u='pcs', s='miyagi'),
    dict(k='note', t='宮城県の食品OEM事業者の掲載条件です。価格は掲載されていません。', u='none', s='miyagi'),
  ]),
 'packaging.box': dict(rows=[
    dict(k='min', t='キャラメル箱 50個（印刷あり）', lo=51502, hi=51502, u='yen', s='imitsubox'),
    dict(k='min', t='無地のギフト箱 1,000個', lo=69000, hi=None, u='yen', s='imitsubox'),
    dict(k='moq', t='最低ロット', lo=1, hi=1, u='pcs', s='imitsubox'),
  ]),
 'apparel.leather': dict(rows=[
    dict(k='moq', t='革小物・布小物のOEM', lo=30, hi=30, u='pcs', s='nikoniko'),
    dict(k='note', t='ロゴを入れる場合は版代がかかることがあります（金額は非公開）。', u='none', s='nikoniko'),
  ]),
}

# 画面の固定文言と、上の t / assume の訳（i18n.py が T に足す）
T_EST = {
 '概算・最低ロット': ('Rough cost & MOQ', '概算与起订量'),
 '概算の目安': ('Rough cost guide', '概算参考'),
 '確定の見積ではありません': ('Not a quote', '并非正式报价'),
 '公開されている料金表・記事に書かれた数字だけを集め、工程ごとに並べたAIの目安です。形・材料・数量・納期で大きく変わります。正式な金額は工場の見積で決まります。': (
   'An AI guide built only from figures published in price lists and articles, arranged by step. Shape, material, quantity and lead time change it a lot. The real price comes from the factory quote.',
   '仅汇总公开价目表和文章中的数字，按工序整理的AI参考。形状、材料、数量和交期都会大幅影响价格。正式金额以工厂报价为准。'),
 '数量': ('Quantity', '数量'),
 'この数量での概算': ('Rough total for this quantity', '该数量的概算'),
 '相場がわかる工程だけの合計': ('Total of steps with known prices only', '仅合计有行情的工序'),
 '見積が必要な工程': ('Steps that need a quote', '需要报价的工序'),
 '公開された相場が見つかっていないため、金額に入れていません。': ('No published price found, so not included in the total.', '未找到公开行情，未计入金额。'),
 '工程ごとの目安': ('Guide by step', '各工序参考'),
 '初期費用': ('Setup cost', '初期费用'),
 '単価': ('Unit price', '单价'),
 '最低ロット': ('Minimum lot', '最小批量'),
 '最低発注額': ('Minimum order', '最低订购额'),
 '費用': ('Cost', '费用'),
 '補足': ('Note', '备注'),
 '計算の前提': ('Assumption', '计算前提'),
 '出典': ('Source', '来源'),
 '概算に入れた金額': ('Amount in the total', '计入概算的金额'),
 '公開相場なし・見積が必要': ('No public price; needs a quote', '无公开行情，需要报价'),
 '掲載企業の最小ロット': ('Minimum lot of listed companies', '收录企业的最小批量'),
 '最小ロットの記載がある会社': ('Companies stating a minimum lot', '注明最小批量的公司'),
 '1個から受ける会社': ('Accept from 1 unit', '1个起接单的公司'),
 '中央値': ('Median', '中位数'),
 'この数量では合計に入れていない工程': ('Steps left out at this quantity', '该数量下未计入的工序'),
 '試作と量産で作り方が変わるため、出典が示す向く数量の外では合計に入れていません。': ('Prototype and production use different methods, so steps outside the quantity their source recommends are left out.', '试制和量产的做法不同，超出来源所示适用数量的工序未计入合计。'),
 'この数量では当てはまりません': ('Does not apply at this quantity', '不适用于该数量'),
 '最低ロットに届いていません': ('Below the minimum lot', '未达到最小批量'),
 '1ドル＝150円で換算（仮定）': ('Converted at ¥150 per USD (assumed)', '按1美元＝150日元换算（假定）'),
 '部品代・材料費・送料・税は、出典に含まれない限り入っていません。': ('Parts, materials, shipping and tax are not included unless the source includes them.', '除非来源已包含，否则不含零件、材料、运费和税。'),
 '公式の料金表': ('Official price list', '官方价目表'),
 '報道・記事': ('News / article', '报道・文章'),
 '業者・まとめサイトの掲載': ('Vendor or directory page', '厂商・汇总网站'),
 '根拠の記載がない目安': ('Rough guide without stated basis', '未注明依据的参考'),
 '調べた日': ('Checked', '调查日期'),
 'この目安で見積を依頼': ('Request a quote with this guide', '按此参考申请报价'),
 'AIの目安': ('AI guide', 'AI参考'),
 '〜': ('–', '～'),
}
T_ROWS = {
 '試作・少量向けの金型（プロトラブズの例）': ('Prototype / low-volume mold (Protolabs example)', '试制・小批量模具（Protolabs示例）'),
 'アルミ金型（CNC加工）': ('Aluminum mold (CNC)', '铝模（CNC加工）'),
 '国内で量産金型を見積もった例': ('Example quote for a production mold in Japan', '日本国内量产模具报价示例'),
 '大量生産用の鉄製金型': ('Steel mold for high volume', '大批量钢模'),
 '金型の修正1回': ('One mold modification', '模具修改一次'),
 'アルミ金型が向く数量': ('Quantity suited to aluminum molds', '适合铝模的数量'),
 '成形1個あたりの単価は形・樹脂で大きく変わり、公開された相場は見つかっていません。': ('Per-part molding price varies widely by shape and resin; no published rate was found.', '每件成型单价因形状和树脂差异很大，未找到公开行情。'),
 '金型代のみ（試作向け30万円〜国内量産300万円）。成形単価・材料費は別': ('Mold cost only (¥300k prototype to ¥3M production in Japan). Molding and material extra.', '仅模具费（试制30万日元～国内量产300万日元）。成型单价和材料另计'),
 '1個の価格例（50mm角の樹脂〜200mmのステンレス）': ('Price per part (50 mm plastic to 200 mm stainless)', '单件价格示例（50mm树脂～200mm不锈钢）'),
 '丸物1個の価格例（φ50樹脂〜φ128鉄）': ('Turned part price (ø50 plastic to ø128 steel)', '车削件价格示例（φ50树脂～φ128钢）'),
 '丸物は101個以上で最大70%引き。数量割引は概算に入れていません。': ('Turned parts: up to 70% off at 101+. Volume discounts not included.', '车削件101个以上最多优惠70%。概算未计入数量折扣。'),
 '1個の価格例×数量（数量割引なし）': ('Per-part example × quantity (no volume discount)', '单件价格示例×数量（无数量折扣）'),
 '1個の価格例（アルミ・鉄・ステンレスの曲げ品など）': ('Price per part (bent aluminum, steel, stainless etc.)', '单件价格示例（铝・铁・不锈钢折弯件等）'),
 '101個以上で最大60%引き。数量割引は概算に入れていません。': ('Up to 60% off at 101+. Volume discounts not included.', '101个以上最多优惠60%。概算未计入数量折扣。'),
 'ナイロン造形の体積単価（DMM.make）': ('Nylon printing price per volume (DMM.make)', '尼龙打印体积单价（DMM.make）'),
 '手のひら大のボディ1個（ナイロン造形）': ('One palm-sized body (nylon print)', '一个手掌大小的外壳（尼龙打印）'),
 '金属3Dプリントの最低注文額（よくある条件）': ('Typical minimum order for metal 3D printing', '金属3D打印的常见最低订购额'),
 '3Dプリントが向く数量（100個未満）': ('Quantity suited to 3D printing (under 100)', '适合3D打印的数量（100个以下）'),
 '手のひら大のナイロン造形1個×数量。大きさで大きく変わる': ('One palm-sized nylon print × quantity. Varies greatly with size.', '手掌大小尼龙打印单价×数量。尺寸不同差异很大'),
 '真空注型（シリコン型）で受ける数量': ('Quantities accepted for vacuum casting (silicone mold)', '真空注型（硅胶模）接单数量'),
 '型代・単価は各社とも「応相談」で、公開された金額は見つかっていません。': ('Mold and unit prices are "on request" everywhere; no published amount found.', '模具费和单价各家均为"面议"，未找到公开金额。'),
 '基板10枚（10cm角まで）の製造': ('10 PCBs (up to 10 cm square)', '10片电路板（10cm见方以内）'),
 '実装の段取り費': ('Assembly setup fee', '贴片准备费'),
 'メタルマスク': ('Stencil', '钢网'),
 'はんだ付け1点あたり': ('Per solder joint', '每个焊点'),
 '中国の格安サービスの例です。部品代・送料・関税は別。国内の実装会社の公開相場は見つかっていません。': ('A low-cost Chinese service. Parts, shipping and duties extra. No published rates found for Japanese assemblers.', '这是中国低价服务的示例。零件、运费、关税另计。未找到日本贴片厂的公开行情。'),
 '中国の格安サービスで基板10枚まで（基板＋段取り＋マスク）。部品代・送料は別': ('Up to 10 boards at a low-cost Chinese service (board + setup + stencil). Parts and shipping extra.', '中国低价服务10片以内（电路板＋准备费＋钢网）。零件和运费另计'),
 'シンプルな2層基板の設計（1件）': ('Simple 2-layer board design (per job)', '简单双层板设计（每件）'),
 '一般的な4層基板の設計（1件）': ('Typical 4-layer board design (per job)', '常规四层板设计（每件）'),
 '根拠の調査データが示されていない目安です。高速信号・電源を含むと20万円を超えることもあるとされています。': ('A guide with no survey data behind it. With high-speed signals or power design it can exceed ¥200k.', '该参考未提供调查数据。包含高速信号或电源设计时可能超过20万日元。'),
 '基板1枚の設計（2層〜4層）': ('Design of one board (2 to 4 layers)', '一块电路板的设计（2～4层）'),
 'ツール系アプリの開発費': ('Development cost of a utility app', '工具类应用开发费'),
 'アプリ開発の平均': ('Average app development', '应用开发平均'),
 '機器とBluetoothでつなぐアプリの公開相場は見つかっていません。': ('No published rates found for apps that connect to devices over Bluetooth.', '未找到通过蓝牙连接设备的应用的公开行情。'),
 'ツール系アプリの相場': ('Utility app market rate', '工具类应用行情'),
 '技適（2.4GHz帯）申込の基本料': ('Japan radio certification (2.4 GHz) application fee', '日本无线认证（2.4GHz）申请基本费'),
 '1台目の試験手数料': ('Test fee for the first unit', '第一台测试费'),
 'TELECで技術基準適合証明を受ける場合の手数料です。技適を取った無線モジュールを使うと、製品としての取得が不要になる場合があります。': ('Fees for certification at TELEC. Using a pre-certified radio module can make product certification unnecessary.', '这是在TELEC取得技术基准适合证明的手续费。使用已认证的无线模块，产品可能无需另行认证。'),
 'TELECの手数料（申込＋1台目の試験）': ('TELEC fees (application + first unit test)', 'TELEC手续费（申请＋第一台测试）'),
 '簡易OEM（無地＋プリント）': ('Simple OEM (blank + print)', '简易OEM（素色＋印花）'),
 'スポーツウェア': ('Sportswear', '运动服'),
 '1カラーあたり': ('Per color', '每个颜色'),
 '一般的なアパレル（1カラーあたり）': ('General apparel (per color)', '一般服装（每个颜色）'),
 '生地は1反（約200〜300枚分）単位で買うことが多く、少ない数量では割高になります。': ('Fabric is often bought by the bolt (about 200–300 garments), so small runs cost more per piece.', '面料常按整匹（约200～300件）购买，数量少时单价偏高。'),
 'Tシャツ片面1色シルク印刷 10枚': ('T-shirt, 1-color screen print one side, 10 pcs', 'T恤单面单色丝印 10件'),
 '同 30枚': ('Same, 30 pcs', '同上 30件'),
 '同 50枚': ('Same, 50 pcs', '同上 50件'),
 '同 100枚': ('Same, 100 pcs', '同上 100件'),
 '10枚の合計': ('Total for 10 pcs', '10件合计'),
 'Tシャツ片面1色シルク印刷の相場': ('Market rate for 1-color screen-printed T-shirts', 'T恤单面单色丝印行情'),
 '化粧水・美容液など 100個〜': ('Lotion, serum etc. 100+', '化妆水・精华等 100个起'),
 '同 500個〜': ('Same, 500+', '同上 500个起'),
 '同 1,000個〜': ('Same, 1,000+', '同上 1,000个起'),
 '化粧水・美容液・乳液': ('Lotion, serum, emulsion', '化妆水・精华・乳液'),
 'リップ': ('Lipstick', '唇膏'),
 'ファンデーション（パウダー）': ('Powder foundation', '粉底（粉状）'),
 '固形石けん': ('Bar soap', '固体香皂'),
 '化粧水・美容液などの相場': ('Market rate for lotion, serum etc.', '化妆水・精华等行情'),
 '菓子': ('Confectionery', '点心'),
 'レトルト': ('Retort pouch food', '蒸煮袋食品'),
 '冷凍惣菜': ('Frozen side dishes', '冷冻熟食'),
 '缶詰': ('Canned food', '罐头'),
 '宮城県の食品OEM事業者の掲載条件です。価格は掲載されていません。': ('Conditions listed by food OEM makers in Miyagi Prefecture. Prices are not listed.', '宫城县食品OEM企业公布的条件。未公布价格。'),
 '200mlびん': ('200 ml bottle', '200ml瓶'),
 '500mlびん': ('500 ml bottle', '500ml瓶'),
 'キャラメル箱 50個（印刷あり）': ('Tuck-end box, 50 pcs (printed)', '插口盒 50个（含印刷）'),
 '無地のギフト箱 1,000個': ('Plain gift box, 1,000 pcs', '素色礼盒 1,000个'),
 '革小物・布小物のOEM': ('Leather / fabric small goods OEM', '皮革・布艺小物OEM'),
 'ロゴを入れる場合は版代がかかることがあります（金額は非公開）。': ('Adding a logo may need a plate fee (amount not published).', '加logo可能产生制版费（金额未公开）。'),
}
T_EST.update(T_ROWS)
T_EST.update({v['t']: (v['t'], v['t']) for v in SRC.values()})  # 出典名は訳さない（そのまま出す）


def _check():
    for code, e in EST.items():
        for r in e['rows']:
            assert r['t'] in T_EST, r['t']
            assert r.get('s') is None or r['s'] in SRC, r
        a = (e.get('calc') or {}).get('assume')
        assert a is None or a in T_EST, a


def db_stats(companies, codes):
    """企業DBの最小ロット（掲載情報）を工程ごとに集計する。"""
    out = {}
    # 設計・ソフト・試験は会社単位の最小ロットが意味をなさないので、つくる工程だけ。3社未満は出さない
    make = ('manufacturing.', 'apparel.', 'food.', 'cosmetics.', 'packaging.', 'crafts.', 'electronics.pcba', 'electronics.flexible')
    for code in codes:
        if not code.startswith(make):
            continue
        lots = sorted(c['terms']['min_lot'] for c in companies
                      if (c.get('terms') or {}).get('min_lot') is not None
                      and any(x['code'] == code for x in c.get('capabilities', [])))
        if len(lots) >= 3:
            out[code] = dict(n=len(lots), n1=sum(1 for x in lots if x <= 1), med=lots[len(lots) // 2], max=lots[-1])
    return out


def build(companies, cap_codes):
    _check()
    codes = sorted(set(cap_codes) | set(EST) | {x['code'] for c in companies for x in c.get('capabilities', [])})
    return dict(rows=EST, src=SRC, usdjpy=USDJPY, retrieved=RETRIEVED, db=db_stats(companies, codes))


if __name__ == '__main__':
    _check()
    print(len(EST), 'processes', sum(len(e['rows']) for e in EST.values()), 'rows ok')
