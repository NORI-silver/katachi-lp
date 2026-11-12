"""選択式（選んで探す）用の会社一覧を作る。
使い方: python3 guided_data.py <companies.csv> <taxonomy.pyのあるkatachiフォルダの親> <出力json>
出力: {"caps":[code...], "lv":[...], "c":[[name,country,pref,city,web,[capIdx...],proto,nodraw,minlot,mat,lvIdx,summary,src],...]}
"""
import csv, json, sys
src, root, out = sys.argv[1:4]
sys.path.insert(0, root)
from katachi.taxonomy import CAPABILITIES
name2code = {n: c for c, p, n, *_ in CAPABILITIES}
codes = [c for c, *_ in CAPABILITIES]
LV = ['公式サイトで確認', '報道・記事で確認', '企業掲載ページで確認', '集約サイト掲載のみ(未確認)']
LVK = ['pub', 'pub', 'pub', 'unk']
rows = []
for x in csv.DictReader(open(src, encoding='utf-8-sig')):
    caps = []
    for t in x['技術(★=課題解決実績あり)'].split('／'):
        t = t.rstrip('★')
        if t in name2code: caps.append(codes.index(name2code[t]))
    if not caps: continue
    lv = LV.index(x['確認レベル']) if x['確認レベル'] in LV else 3
    ml = x['最小ロット']
    rows.append([x['社名'], x['国'] or 'JP', x['都道府県'], x['市区町村'], x['公式サイト'], caps,
                 1 if x['試作対応'] == '可' else None, 1 if x['図面なし相談'] == '可' else None,
                 int(ml) if ml.isdigit() else None,
                 {'工場が手配': 'factory', 'どちらも可': 'both', '自分で用意': 'customer'}.get(x['材料調達']),
                 LVK[lv], x['概要'][:70], x['出典URL'], x['確認日']])
from katachi.taxonomy import REGULATION_HINTS, DEFERRED, DEFERRED_KEYWORDS
# 文章入力の読み取り用に、taxonomy のキーワードを補う（サイト側だけで使う。本来は taxonomy.py に足す）
EXTRA_KW = {
 'food.processed_oem': ['クッキー','ケーキ','パン','チョコ','ジャム','ソース','ドレッシング','菓子','焼き菓子','和菓子','ラーメン','カレー','惣菜','ドライフルーツ','ナッツ','グラノーラ','食べ物','ギフト食品'],
 'food.beverage_oem': ['コーヒー','お茶','紅茶','スムージー','青汁','炭酸','ドリンク'],
 'food.pet_food': ['犬のおやつ','猫のおやつ','ジャーキー'],
 'manufacturing.textile': ['トート','ポーチ','エプロン','タオル','巾着','布製','クッション','カバン','リュック','ハーネス','リード'],
 'apparel.garment_oem': ['Tシャツ','パーカー','ユニフォーム','制服','作業着','ワンピース','シャツ','ジャケット'],
 'apparel.print_embroidery': ['ロゴ入り','名入れ','シルクスクリーン'],
 'cosmetics.household': ['ノベルティ','グッズ','キーホルダー','アクリル','ステッカー','マグカップ','タンブラー','石鹸','入浴剤','芳香剤'],
 'manufacturing.cnc': ['金具','ブラケット','削り出し','削って','シャフト','ギア','補修部品','治具','金属部品'],
 'manufacturing.sheet_metal': ['曲げ','溶接','ステンレス板','筐体板金'],
 'manufacturing.injection_molding': ['樹脂部品','プラ部品','成形','ケース','カバー','フタ','キャップ'],
 'manufacturing.rapid_proto': ['モック','試作品','プロトタイプ'],
 'packaging.box': ['化粧箱','ギフトボックス','段ボール','パッケージデザイン'],
 'packaging.label_print': ['チラシ','パンフレット','名刺','カード'],
 'crafts.wood_furniture': ['木製','什器','棚','ベンチ','デスク'],
 'crafts.ceramics_glass': ['マグ','皿','茶碗','グラス','花瓶'],
 'crafts.metal_goods': ['真鍮','アクセサリー','ピアス','ネックレス','指輪','金属雑貨','ネームプレート'],
 'cosmetics.oem': ['化粧水','美容液','クリーム','リップ','ハンドクリーム','ヘアオイル','トリートメント'],
 'electronics.pcb_design': ['IoT','電子工作','ガジェット','デバイス','機器'],
 'sensing.environment': ['湿度','空気','におい','匂い'],
 'software.mobile_app': ['通知'],
}
kws = [list(k) + [x for x in EXTRA_KW.get(c, []) if x not in k] for c, p, n, st, k in CAPABILITIES]
json.dump({'caps': codes, 'names': [n for c, p, n, *_ in CAPABILITIES], 'kw': kws, 'regs': REGULATION_HINTS, 'deferred': DEFERRED, 'deferred_kw': DEFERRED_KEYWORDS, 'c': rows}, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(rows))
