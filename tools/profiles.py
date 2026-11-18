"""会社ごとの「作れる物・扱う材料・受ける条件」（公式サイトに書いてあることだけ）を、会社一覧（data/companies.json の列14 `pf`）に入れる。
Nori 2026-11-15「マッチングの精度が低い。各社がどんな情報が必要なのかをもっと具体的に持ってないといけない」「そのDBが生命線」。

元データ: 企業DB（katachi-matching）の data/real/profiles.jsonl。1行1社で、公式サイトの文から取った値と、その出典URL・確認日。
  items 作れる品目・製品例 / procs 工程・加工 / mats 材料 / size 大きさ（原文） / minlot 最小ロット（原文） / proto 試作1個から
  design 設計・図面なしから（原文） / elec 電子回路・基板を扱うか / lead 納期（原文） / certs 認証 / install 設置工事 / individual 個人の依頼 / quote_needs 見積に要る物（原文）
書いていない項目は null（推測で埋めない）。

列14 `pf` の形（画面と並べ方が使う）:
  t   作れる品目・製品例をつないだ文（工程・材料は1語で上がりすぎるので入れない）（依頼との近さを見る言葉。画面には出さない）
  m   材料の種類（MAT_FAM のキー）。公式サイトに材料が書いてあるときだけ
  el  電子回路・基板を扱う 1 / 扱わないと書いてある 0
  ind 個人の依頼を受ける 1
  q   見積に要る物（原文、80字まで）
  src 出典URL  d 確認日
依頼の側も同じ材料の種類で読み（tools/template.html の MAT_FAM）、合わない会社を下げる。
"""
import json, os, re

# 材料の種類（依頼と会社の両方を、この同じ物差しで読む。tools/template.html の MAT_FAM と同じ中身）
MAT_FAM = {
    'leather': r'革|レザー|皮革|合皮|ヌメ|スエード|ヌバック',
    'fabric': r'布|生地|帆布|キャンバス|コットン|綿|麻|リネン|ナイロン(?!樹脂)|ポリエステル|不織布|フェルト|デニム|ウール|ニット|メッシュ|ガーゼ|タオル地',
    'wood': r'木材|木製|木工|木の|ウッド|合板|無垢|天然木|ひのき|檜|杉|竹',
    'metal': r'金属|ステンレス|SUS|アルミ|鉄|スチール|鋼|真鍮|銅|チタン|シルバー|銀|ゴールド|亜鉛|ダイカスト|板金',
    'resin': r'樹脂|プラスチック|アクリル|ABS|ポリカ|PVC|塩ビ|ポリプロピレン|ポリエチレン|ウレタン|PET(?!ボトル)|熱可塑|(?<![A-Za-z])(PP|PBT|POM|PMMA|TPU|TPE)(?![A-Za-z])',
    'rubber': r'ゴム|シリコン|シリコーン|エラストマー|ラバー',
    'paper': r'紙|段ボール|ダンボール|板紙',
    'glass': r'ガラス|陶器|磁器|陶磁器|セラミック|焼き物',
    'food': r'食品|原料|菓子|茶葉|コーヒー豆|果実|野菜|肉|魚',
    'cosme': r'化粧品|精油|植物エキス|界面活性|美容成分|(?<![ァ-ヶ])オイル(?![ァ-ヶ])',
}
_RX = {k: re.compile(v, re.I) for k, v in MAT_FAM.items()}
NODRAW = re.compile(r'図面(が|は)?(無|な)|図面なし|アイデア|イメージ|ラフ|ポンチ絵|手書き|イラスト|構想|あやふや|決まっていない|コンセプト|写真')
LOT = re.compile(r'(\d[\d,]*)\s*(個|枚|点|台|着|本|セット|pcs)\s*(から|〜|~|以上)')


def fams(words):
    s = ' '.join(words or [])
    return [k for k, rx in _RX.items() if rx.search(s)]


def load(root):
    """社名 → プロフィール（後から書いた行が勝つ）"""
    p = os.path.join(root, 'data', 'real', 'profiles.jsonl')
    out = {}
    if os.path.exists(p):
        for l in open(p, encoding='utf-8'):
            l = l.strip()
            if l:
                o = json.loads(l)
                out[o['name']] = o
    return out


def apply(row, o):
    """row: companies.json の1行（列14まで）。公式サイトの値で、空いている列（試作・図面なし・最小ロット）を埋め、列14に pf を足す"""
    if not o:
        return row
    if o.get('proto') is True and row[6] is None:
        row[6] = 1
    if row[7] is None and isinstance(o.get('design'), str) and NODRAW.search(o['design']):
        row[7] = 1
    m = LOT.search(o.get('minlot') or '')
    if row[8] is None and m:
        row[8] = int(m.group(1).replace(',', ''))
    # 品目が2つ以下のページは一部しか読めていないことが多いので、品目で上げ下げしない
    t = '／'.join(o.get('items') or []) if len(o.get('items') or []) >= 3 else ''
    pf = {'t': t[:240], 'src': o.get('url'), 'd': o.get('checked')}
    f = fams(o.get('mats'))
    if f:
        pf['m'] = f
    if o.get('elec') is True:
        pf['el'] = 1
    elif o.get('elec') is False:
        pf['el'] = 0
    if o.get('individual') is True:
        pf['ind'] = 1
    if o.get('quote_needs'):
        pf['q'] = o['quote_needs'][:80]
    x = row[14] if isinstance(row[14], dict) else {}
    x['pf'] = pf
    row[14] = x
    return row
