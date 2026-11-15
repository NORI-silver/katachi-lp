"""ガイド記事・作例ページを「見てわかる」ようにする部品。seo_pages.py から使う。

- 図はすべて自作のSVG（線のイラスト）。写真や他社サイトの画像は使わない。ページに直接書くので読み込みは増えない。
- hero(): 記事の冒頭の図（アイデア → 工場 → 商品 の流れ。分野ごとに色と品物の絵を変える）。
- enhance(): 本文のHTMLを見やすい形にする（見出しに番号とアイコン、手順を流れ図とカードに、表をスマホでカード表示に、
  太字で始まる箇条書きをカードに）。文章は変えない。
- og_svg(): 記事ごとのOGP画像（1200×630）の元。PNGへの書き出しは tools/og_images.py（ローカルで実行してコミット）。
"""
import html, re
from ideas import FIG as IFIG

_S = 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
FIG = dict(IFIG)
FIG.update({
    'printer': f'<path d="M10 12h44v8H10zM14 20v34M50 20v34M10 54h44" {_S}/><path d="M28 20v8l4 4 4-4v-8" {_S}/><path d="M22 50h20l-3-10H25z" {_S}/>',
    'pcb': f'<rect x="10" y="12" width="44" height="40" rx="3" {_S}/><rect x="24" y="24" width="16" height="16" {_S}/><path d="M28 24v-6M36 24v-6M28 40v6M36 40v6M24 28h-8M24 36h-8M40 28h8M40 36h8" {_S}/>',
    'factory': f'<path d="M8 54V30l12 8v-8l12 8v-8l12 8V12h8v42z" {_S}/><path d="M16 46h6M28 46h6M40 46h6" {_S}/>',
    'doc': f'<path d="M16 8h22l10 10v38H16z" {_S}/><path d="M38 8v10h10M23 30h18M23 38h18M23 46h11" {_S}/>',
    'yen': f'<circle cx="32" cy="32" r="22" {_S}/><path d="M23 20l9 12 9-12M32 32v14M24 34h16M24 41h16" {_S}/>',
    'search': f'<circle cx="28" cy="28" r="16" {_S}/><path d="M40 40l14 14" {_S}/>',
    'gear': f'<circle cx="32" cy="32" r="8" {_S}/><path d="M32 8v8M32 48v8M8 32h8M48 32h8M15 15l6 6M43 43l6 6M15 49l6-6M43 21l6-6" {_S}/><circle cx="32" cy="32" r="16" {_S}/>',
    'shield': f'<path d="M32 8l20 8v14c0 13-9 22-20 26-11-4-20-13-20-26V16z" {_S}/><path d="M23 32l6 6 12-12" {_S}/>',
    'scale': f'<path d="M32 10v44M20 54h24M12 20h40" {_S}/><path d="M12 20l-6 16a8 6 0 0 0 12 0zM52 20l-6 16a8 6 0 0 0 12 0z" {_S}/>',
    'steps': f'<path d="M8 50h14V38h14V26h14V14h6" {_S}/><circle cx="15" cy="44" r="2" fill="currentColor"/>',
    'idea': f'<path d="M32 8a16 16 0 0 1 9 29v7H23v-7A16 16 0 0 1 32 8z" {_S}/><path d="M25 50h14M27 56h10" {_S}/>',
    'person': f'<circle cx="32" cy="20" r="10" {_S}/><path d="M12 56c2-12 10-18 20-18s18 6 20 18" {_S}/>',
    'flask': f'<path d="M26 8h12M28 8v16L14 50a4 4 0 0 0 4 6h28a4 4 0 0 0 4-6L36 24V8" {_S}/><path d="M20 42h24" {_S}/>',
    'tube': f'<path d="M20 10h24l-4 40H24z" {_S}/><path d="M26 50h12v6H26zM24 22h16" {_S}/>',
    'sheet': f'<path d="M8 40l24-12 24 12-24 12z" {_S}/><path d="M8 40v6l24 12 24-12v-6" {_S}/><path d="M32 28V14l12-6" {_S}/>',
    'q': f'<circle cx="32" cy="32" r="22" {_S}/><path d="M25 26a7 7 0 1 1 10 6c-2 1-3 3-3 5v2" {_S}/><circle cx="32" cy="46" r="1.8" fill="currentColor"/>',
})

# 分野：色・名前・品物の絵（3つ）
CAT = {
    'cosmetics': ('#c4527a', '#fbeef3', '化粧品', ['bottle', 'tube', 'jar']),
    'food': ('#d0701f', '#fdf1e6', '食品・お菓子', ['pouch', 'sweets', 'jar']),
    'supplement': ('#2b8f63', '#e9f6ef', 'サプリ・健康食品', ['pouch', 'jar', 'bottle']),
    'apparel': ('#5257c9', '#eeeffc', 'アパレル・布製品', ['shirt', 'bag', 'cloth']),
    'goods': ('#0f8f9c', '#e6f6f7', 'グッズ・雑貨', ['mug', 'badge', 'box']),
    'parts': ('#2350c8', '#eaf0fd', '部品・試作', ['part', 'case', 'printer']),
    'business': ('#3f5576', '#eef1f6', '進め方・制度', ['doc', 'yen', 'search']),
}
# 記事ごとの分野と主役の絵（無ければ分野の先頭の絵）
RULES = [
    (r'cosmetic|lotion|shampoo|salon', 'cosmetics', 'bottle'), (r'soap', 'cosmetics', 'soap'), (r'bath-salt', 'cosmetics', 'jar'),
    (r'hair-oil', 'cosmetics', 'bottle'), (r'hand-cream', 'cosmetics', 'tube'),
    (r'supplement', 'supplement', 'jar'),
    (r'sweets|souvenir', 'food', 'sweets'), (r'retort|food', 'food', 'pouch'), (r'canned', 'food', 'jar'), (r'frozen', 'food', 'box'),
    (r'jelly', 'food', 'cup'), (r'restaurant', 'food', 'pouch'),
    (r'bag-oem', 'apparel', 'bag'), (r'apparel|uniform|sportswear', 'apparel', 'shirt'),
    (r'novelty', 'goods', 'badge'), (r'store-original', 'goods', 'mug'), (r'pet-goods', 'goods', 'leash'), (r'outdoor', 'goods', 'fire'),
    (r'goods-small-lot', 'goods', 'mug'),
    (r'small-lot-oem', 'goods', 'box'),
    (r'prototype-cost|cnc-machining', 'parts', 'part'), (r'oem-minimum-lot', 'goods', 'box'),
    (r'metal-3d|3d-print|dmm-make', 'parts', 'printer'), (r'pcb', 'parts', 'pcb'), (r'iot', 'parts', 'device'),
    (r'sheet-metal', 'parts', 'sheet'), (r'injection|resin', 'parts', 'case'), (r'no-drawing|meviy', 'parts', 'doc'),
    (r'what-gets-ordered|prototype-outsourcing|individual-prototype|prototype-service', 'parts', 'part'),
    (r'subsidy', 'business', 'yen'), (r'design-outsourcing', 'business', 'doc'), (r'emidas|find-manufacturer', 'business', 'search'),
    (r'own-product|subcontractor', 'business', 'factory'), (r'individual-product', 'business', 'idea'),
]
FIG_CAT = {'bottle': 'cosmetics', 'soap': 'cosmetics', 'tube': 'cosmetics', 'pouch': 'food', 'jar': 'food', 'sweets': 'food',
           'shirt': 'apparel', 'bag': 'apparel', 'cloth': 'apparel', 'slipper': 'apparel', 'device': 'parts', 'case': 'parts', 'part': 'parts',
           'mug': 'goods', 'cup': 'goods', 'badge': 'goods', 'candle': 'goods', 'leash': 'goods', 'fire': 'goods', 'board': 'goods', 'hook': 'goods', 'box': 'goods'}
# 作例ページの業種 → 分野
IND_CAT = {'cafe': 'food', 'farm': 'food', 'salon': 'cosmetics', 'hotel': 'goods', 'gym': 'goods', 'shop': 'goods',
           'pet': 'goods', 'outdoor': 'goods', 'maker': 'parts', 'startup': 'parts', 'clinic': 'goods', 'school': 'goods'}


def topic(slug):
    for pat, cat, fig in RULES:
        if re.search(pat, slug):
            return cat, fig
    return 'business', 'doc'


def icon(kind, size=24, color='currentColor', x=None, y=None):
    pos = f' x="{x}" y="{y}"' if x is not None else ''
    return (f'<svg{pos} width="{size}" height="{size}" viewBox="0 0 64 64" style="color:{color}" aria-hidden="true">'
            f'{FIG.get(kind, FIG["box"])}</svg>')


def hero(cat, fig, label, name=None):
    """冒頭の図：アイデア → 工場 → 商品（720×220）。文字は分野名だけ"""
    c, bg, cname, figs = CAT[cat]
    name = name or cname
    others = [f for f in figs if f != fig][:2]
    e = html.escape
    return (f'<figure class="hero"><svg viewBox="0 0 720 226" role="img" aria-label="{e(label)}：つくりたいものを、工程ごとに頼める会社に頼んで形にする流れのイラスト">'
            f'<rect width="720" height="226" rx="18" fill="{bg}"/>'
            f'<circle cx="640" cy="34" r="60" fill="{c}" opacity=".07"/><circle cx="70" cy="200" r="70" fill="{c}" opacity=".06"/>'
            f'<g fill="{c}" opacity=".18">' + ''.join(f'<circle cx="{30 + i * 16}" cy="24" r="2"/>' for i in range(6)) + '</g>'
            # 1. アイデア
            f'<rect x="52" y="62" width="112" height="112" rx="22" fill="#fff" stroke="{c}" stroke-opacity=".25"/>'
            + icon('idea', 64, c, 76, 78) +
            f'<text x="108" y="204" text-anchor="middle" font-size="21" fill="#3d4a63" font-weight="700">つくりたいもの</text>'
            # 矢印
            f'<path d="M180 118h70" stroke="{c}" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/><path d="M246 110l10 8-10 8" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            # 2. 工場（チーム）
            f'<rect x="272" y="62" width="176" height="112" rx="22" fill="#fff" stroke="{c}" stroke-opacity=".25"/>'
            + icon('factory', 58, c, 290, 84) + icon(others[0] if others else 'gear', 40, c, 356, 74) + icon(others[1] if len(others) > 1 else 'gear', 40, c, 396, 116) +
            f'<text x="360" y="204" text-anchor="middle" font-size="21" fill="#3d4a63" font-weight="700">工程ごとに頼める会社</text>'
            f'<path d="M464 118h70" stroke="{c}" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/><path d="M530 110l10 8-10 8" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
            # 3. 商品
            f'<circle cx="612" cy="118" r="62" fill="#fff" stroke="{c}" stroke-opacity=".35"/><circle cx="612" cy="118" r="50" fill="{c}" opacity=".08"/>'
            + icon(fig, 74, c, 575, 81) +
            f'<text x="612" y="210" text-anchor="middle" font-size="21" fill="#3d4a63" font-weight="700">{e(name)}</text>'
            '</svg></figure>')


SEC_ICON = [(r'許可|表示|法|規制|届出|規程|商標|権|守る|安全|技適', 'shield'), (r'費用|見積|価格|単価|補助|お金|料金|安く', 'yen'),
            (r'流れ|進め方|手順|ステップ|始め|使い方|頼み方|作り方|つくり方|進む', 'steps'), (r'探し|選び|頼み先|依頼先|委託先|どこ', 'search'),
            (r'違い|比較|使い分け|ちがい|分かれ目|どれ', 'scale'), (r'方式|素材|処方|容器|加工|工程|設計|殺菌|形', 'gear'),
            (r'質問', 'q'), (r'データ|調査|現状|多い', 'doc')]


def sec_icon(h):
    for pat, k in SEC_ICON:
        if re.search(pat, h):
            return k
    return 'idea'


def _flow(ol):
    """<ol> の各項目の太字を、横に並ぶ流れ図にする（太字が無い項目は頭の文）"""
    items = re.findall(r'<li>(.*?)</li>', ol, re.S)
    if not 3 <= len(items) <= 8:
        return ''
    labels = []
    for it in items:
        m = re.match(r'\s*<strong>(.*?)</strong>', it)
        t = re.sub(r'<[^>]+>', '', m.group(1) if m else it).strip()
        t = re.split(r'[：。、（(]', t)[0]
        if len(t) > 12:
            return ''
        labels.append(t)
    return ('<div class="flow" aria-hidden="true">' + '<b>→</b>'.join(
        f'<span><i>{i + 1}</i>{html.escape(t)}</span>' for i, t in enumerate(labels)) + '</div>')


def _cards_table(tb):
    """表の各セルに見出しを持たせ、スマホではカードとして表示できるようにする"""
    rows = re.findall(r'<tr>(.*?)</tr>', tb, re.S)
    if len(rows) < 2:
        return tb
    heads = [re.sub(r'<[^>]+>', '', h).strip() for h in re.findall(r'<th[^>]*>(.*?)</th>', rows[0], re.S)]
    if not heads:
        return tb
    out = []
    for i, r in enumerate(rows):
        if i == 0:
            out.append(f'<tr>{r}</tr>')
            continue
        cells = re.findall(r'<(td|th)([^>]*)>(.*?)</\1>', r, re.S)
        cs = []
        for j, (tag, attr, inner) in enumerate(cells):
            lab = heads[j] if j < len(heads) else ''
            cs.append(f'<{tag}{attr} data-l="{html.escape(lab)}">{inner}</{tag}>')
        out.append('<tr>' + ''.join(cs) + '</tr>')
    return re.sub(r'<table>.*</table>', lambda m: '<table class="ct">' + ''.join(out) + '</table>', tb, flags=re.S)


def enhance_block(b):
    # 手順：<ol>（出典の ol.src は除く）→ 流れ図＋番号カード
    def ol(m):
        o = m.group(0)
        return _flow(o) + o.replace('<ol>', '<ol class="steps">', 1)
    b = re.sub(r'<ol>.*?</ol>', ol, b, flags=re.S)
    # 太字で始まる箇条書き → カード
    def ul(m):
        u = m.group(0)
        lis = re.findall(r'<li>(.*?)</li>', u, re.S)
        if len(lis) >= 3 and all(re.match(r'\s*<strong>', x) for x in lis):
            return re.sub(r'</strong>\s*[：:]\s*', '</strong>', u.replace('<ul>', '<ul class="cards">', 1))
        return u.replace('<ul>', '<ul class="chk">', 1)
    b = re.sub(r'<ul>.*?</ul>', ul, b, flags=re.S)
    b = re.sub(r'<div class="tbl">.*?</div>', lambda m: _cards_table(m.group(0)), b, flags=re.S)
    return b


def section(i, h, b):
    return (f'<section class="sec"><h2><span class="no">{i:02d}</span>{icon(sec_icon(h), 22)}<span class="ht">{h}</span></h2>'
            f'{enhance_block(b.strip())}</section>')


def faq(items):
    return ('<section class="sec"><h2><span class="no">Q&amp;A</span>' + icon('q', 22) + '<span class="ht">よくある質問</span></h2><dl class="faq">'
            + ''.join(f'<div><dt><b>Q</b>{q}</dt><dd><b>A</b><span>{a}</span></dd></div>' for q, a in items) + '</dl></section>')


def points(title, items):
    return (f'<div class="points"><b>{icon("idea", 20)}{title}</b><ul>'
            + ''.join(f'<li>{p}</li>' for p in items) + '</ul></div>')


CSS = """<style>
.hero{margin:6px 0 18px}.glist{display:grid;gap:10px;margin:10px 0 24px}.glist a{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--line);border-radius:12px;padding:12px 14px;text-decoration:none;color:var(--fg);background:#fff}.glist a:hover{border-color:#2350c8}.glist .ic{flex:none;width:44px;height:44px;border-radius:12px;display:grid;place-items:center}.glist b{display:block;font-size:15px;line-height:1.5}.glist small{display:block;color:var(--mute);font-size:13px;line-height:1.6;margin-top:2px}.hero svg{display:block;width:100%;height:auto;font-family:inherit}
.lead p,.leadp{font-size:16.5px}
.points{background:#f5f8ff;border:1px solid #d9e3fb;border-radius:14px;padding:16px 18px 10px;margin:20px 0}.points>b{display:flex;gap:8px;align-items:center;margin-bottom:6px;color:#1b3a8f}
.points ul{list-style:none;padding:0;margin:0}.points li{position:relative;padding-left:28px;margin:0 0 8px}
.points li:before{content:"";position:absolute;left:2px;top:.45em;width:18px;height:18px;border-radius:50%;background:#2350c8}
.points li:after{content:"";position:absolute;left:8px;top:calc(.45em + 4px);width:5px;height:8px;border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg)}
.sec{margin-top:38px}.sec h2{display:flex;align-items:center;gap:10px;border-top:none;padding-top:0;margin:0 0 12px;font-size:19px;line-height:1.45}
.sec h2 .no{flex:none;font-size:12px;font-weight:700;letter-spacing:.06em;color:#fff;background:#2350c8;border-radius:8px;padding:3px 7px}
.sec h2 svg{flex:none;color:#2350c8}.sec h2 .ht{flex:1}
.flow{display:flex;flex-wrap:wrap;gap:8px 0;align-items:stretch;margin:6px 0 14px}
.flow span{display:flex;align-items:center;gap:6px;background:#fff;border:1px solid #d9e3fb;border-radius:999px;padding:5px 12px 5px 6px;font-size:13.5px;font-weight:600;color:#1f2a40}
.flow span i{font-style:normal;display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#2350c8;color:#fff;font-size:12px}
.flow b{color:#9fb4ea;margin:0 6px;align-self:center;font-weight:700}
ol.steps{list-style:none;counter-reset:s;padding:0;margin:8px 0 14px;position:relative}
ol.steps li{counter-increment:s;position:relative;padding:12px 14px 12px 54px;margin:0 0 10px;background:#fafbfe;border:1px solid var(--line);border-radius:12px}
ol.steps li:before{content:counter(s);position:absolute;left:14px;top:12px;width:28px;height:28px;border-radius:50%;background:#2350c8;color:#fff;font-weight:700;font-size:14px;display:grid;place-items:center}
ol.steps li:not(:last-child):after{content:"";position:absolute;left:27px;top:44px;bottom:-12px;width:2px;background:#c9d6f6}
ul.cards{list-style:none;padding:0;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:10px 0 14px}
ul.cards li{background:#fff;border:1px solid var(--line);border-left:4px solid #2350c8;border-radius:10px;padding:10px 12px;font-size:14.5px;line-height:1.7}
ul.cards li strong{display:block;color:#13265c}
ul.chk{list-style:none;padding:0}ul.chk li{position:relative;padding-left:22px;margin:4px 0}ul.chk li:before{content:"";position:absolute;left:4px;top:.75em;width:8px;height:8px;border-radius:2px;background:#2350c8;opacity:.7}
.tbl{border:1px solid var(--line);border-radius:12px;overflow-x:auto}.tbl table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.65}
.tbl th,.tbl td{border:none;border-bottom:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}.tbl tr:last-child td{border-bottom:none}
.tbl tr:first-child th{background:#2350c8;color:#fff;font-weight:600;white-space:nowrap}.tbl tr:nth-child(even) td{background:#f7f9fe}.tbl td:first-child{font-weight:600;color:#13265c}
.faq{margin:0}.faq>div{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:0 0 10px;background:#fff}
.faq dt{display:flex;gap:10px;margin:0;font-weight:700}.faq dd{display:flex;gap:10px;margin:8px 0 0;color:#2a3550}
.faq b{flex:none;display:grid;place-items:center;width:24px;height:24px;border-radius:7px;font-size:13px;color:#fff;background:#2350c8}.faq dd b{background:#e08a1e}
.cta{background:linear-gradient(135deg,#eef3ff,#fff);border:1px solid #c9d6f6!important}
@media(max-width:600px){ul.cards{grid-template-columns:1fr}.sec h2{font-size:17.5px}
 .tbl{border:none;overflow:visible}.tbl table.ct,.tbl table.ct tbody,.tbl table.ct tr,.tbl table.ct td,.tbl table.ct th{display:block;width:auto}
 .tbl table.ct tr:first-child{display:none}.tbl table.ct tr{border:1px solid var(--line);border-radius:12px;margin:0 0 10px;overflow:hidden;background:#fff}
 .tbl table.ct td,.tbl table.ct th{background:#fff!important;border-bottom:1px dashed var(--line);padding:8px 12px;white-space:normal;color:inherit}
 .tbl table.ct td:first-child,.tbl table.ct th:first-child{background:#eef3ff!important;font-weight:700;color:#13265c}
 .tbl table.ct td[data-l]:not(:first-child):before{content:attr(data-l);display:block;font-size:11.5px;font-weight:700;color:#5c6b8a;margin-bottom:1px}
 .flow span{font-size:12.5px}}
</style>"""


def og_svg(title, cat, fig, kind='ガイド', label=None):
    """OGP画像（1200×630）の元。タイトルは最大3行"""
    c, bg, name, figs = CAT[cat]
    name = label or name
    e = html.escape
    t = re.split(r'[：｜]', title)[0] if len(title) > 34 else title
    if len(t) > 36:
        t = t[:35] + '…'
    n = -(-len(t) // 12)
    w = -(-len(t) // n)
    lines = [t[i:i + w] for i in range(0, len(t), w)]
    ty = 300 - (len(lines) - 1) * 40
    txt = ''.join(f'<text x="80" y="{ty + i * 80}" font-size="58" font-weight="700" fill="#0d1424">{e(l)}</text>' for i, l in enumerate(lines))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">'
            f'<rect width="1200" height="630" fill="#fff"/><rect x="0" y="0" width="1200" height="630" fill="{bg}"/>'
            f'<circle cx="1080" cy="90" r="160" fill="{c}" opacity=".08"/><circle cx="1010" cy="560" r="120" fill="{c}" opacity=".06"/>'
            f'<rect x="80" y="70" rx="22" width="{60 + len(name) * 30 + len(kind) * 30}" height="46" fill="{c}"/>'
            f'<text x="102" y="102" font-size="26" font-weight="700" fill="#fff">{e(kind)}｜{e(name)}</text>'
            f'{txt}'
            f'<circle cx="960" cy="330" r="170" fill="#fff"/><circle cx="960" cy="330" r="140" fill="{c}" opacity=".09"/>'
            + icon(fig, 190, c, 865, 235) +
            f'<g transform="translate(80,520)"><image width="44" height="44" href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGAAAABgCAYAAADimHc4AAAoKklEQVR42t2debxlRXXvv6v2Pufcue/Qt1sRp/gcko+SOBAkkxMoGhBRIJLEPBVtBCGCYoRojBoVp0aIgNDQDIKCTDYNiI2JgFMzaUCJwyOoiQ1E6PE2TQ/37Frvj6q9d1XtfW5/3hMy3c/n9O17pl21atUafutXa8vvv+wgQFEFAFWt/lZrsWrLF/BvQVXdw/rXyuf8O9xX+PdUT+C+17r3qSqoGlVrUKyCRfy7rAK6RJXnorq3whJV3RfVjqJ7qOoeqCii4saLooiiD4A8gOq8omtRHlK4A9V7FB6iHi2AcQ+xqBuVH2w9Bz8jP9Zq/lLOJXhP/bWBHKV+vnqXKiD0+7uY2/Qr8lA+pfArgfuHu6jUAlSLHxOqigjRe+vvAqFeBCd4K6oYULWqFqVc4T3VyosQDgR+C+WZoIvLxSqvVQkIK/VQ1U9V9kB1DydM3Vdria0X5V5V/RFwHXCnwjoBiyjqFkMA69bfT06kFqqbpJuHhIIOVkUIFrFcUIlk6n5Z8rzLouknuAUQEdRruviL2mhl1f2t7ks11GgveEl2QrVg9UKKqhpUC3UPFPYEjkD1AFX9XdAxVPy8tVQ6668nAlh3KRERrNVoLEK0TqXOGpTFqiwG3Rc4EngE5XYVviYql4KuC5Qn85dx+7KSoQaaGisZLTvA/SH1DtF6x5SLkGUd5PdeemCgWVIL0VpUFav+t7WNrRRqff3/UCUUBVFrjVotvFgztfpyVT0WeCkwEUykcJdQATXerFRmK93O3nBUE6qVKVgY/4WqakVE/abMAoMyB3ozyhmKfgMo/NJlqmoF0WjOwe/SFNU7JTS5WolUE6WtPyzk6gVcbxU3Yas2ELKNbLpa69RRa1tYv6/8cgUlU7WFKoWiXVT/XFXfBewVLFrfy81oKRjVWstiw1rbZAh8Sf2W2mcFn3e7JgveqwrWX2gCeK2qvhb4AXC6ql4C7PKfz9yiUM29EnrltBK/EchTbeALYncIKNmeT/1fteaq1g6nsvX1IlgbvqcyE5Fzqc0NBtRaazuKvlngAuDtwFKtV0v8ljfOjofBgE21ON5pgc/UZPdGOzAyG9XfgngnrH62qiLwBOBglENAdwL3AH3AaMPgEwmWwByJBC9IbLIksVnZHk9+RiX02utTaZr1kY4qyUqGJknDyCfDa5eq7g9cLHCMqi4RKPzHjXN84gw+ieaE5i2IrqKhB8/X/oZE++NdX1lmb6a8fARV432MVcWCPkHRg4FXovwrcJ//ZIagibEnFE3sF+LICprrZtRre2Et1lq3ZVQjDdTAuUd2P7DF1lqxanNFC1Xdw6peCtyoyj6qFKpq3eKooWFWalGiig1NkMbbNnK8GuyAcOISK4ZGUQlJtBaEmapG0UxddFag7KPojYpeqrCHqhao5okMEx8YhOka7xqJNwQoZE96yjNavyj6EgJtLDW/1EBVrFXjp2GBw1G9CtjXRzCqajNAlNQhxc5btfk3VTwd+Kgo/h6wOxIh1xpZGiyJPEzyLQJq/G5Q4HkKRwDrgB/6oMiIDBxC0wSJJBbEfSjbM1oArTWwdnN1/BuYBVtPMnOhs+aqulxVlwPjItJX1UytSmhCauE2H03haWXfa7PqZmR9iCjSptWpE5dA+Er8lK1j/Ng/4iN+EaUvwiKUw0AngX/EmdMsUuhW85OkEsEzit8B5TRLJ0uQxamGiZeNBeaEXgDPVNVVVvVw3N/eFwRZb5JlD9q68cCbfqAR0rVMXq3G1jnQQmnR0NqkaR3zV8GcgogRsCJY4PeAVwDfAtYDuaI2TYdVJTY3aOq1QSEviqIO72yQadpa0NZqkgUrXuP7qrq3iHxNVadxIWVeLhiEYaptpPmhQEWIHa62hJmRT9Om1jV2ThARa5gWJRBJ8h3Rd0rl4I1/pg/8Psqtih4A3AHkqPY1iIAkvFKZz4lGlxMpnbAz1lVYGZmGKgoKhW9L4R8OrLFqp621fb8o3lHaxo5Z6GGtjcLJ2u5LYhrqcaLlO6T2yVWylAYNfkw+wXS5jjelQaARBh5tCSeQu0XQaWCNwuFAHyEvk64aN4qDgzqgqJUsD4VbLZa1tY33Ew5ygFyhr6pvV2WFt+dWXXRQZaRxXF6HmCF2FG7H8vVSS2qtkWgy2jBRRAmkokEcnpo720QNWvCr0idoi3MPFsECU8CXFRaBnCuQI/RDC+lC3jbP7H7lqj571GT1w7wgFL5qX9G3q+oKb/8dxuOFJRjESCAY47ROfPIkjTgca5VCi0RgEmfCkSXShhkjBRIJnGxgTUyWR3MLbbc2nUP1igQK5XMjU4J3wAr/oXODHRJdV7XhAaqVBJUo7relTbZ1uKlqc5zmH6qqK3y8X6KIWGvZunVr5eptmbJ7a1j7l0QrUXrdHsPDQ7G9lzAEDnCX6mtsZbDcUDWAI9T7UluF0lkm9PsFWzdtxobwcgAjiFSpWQRsihEEwdoCYzImJsbLNTKCqFfEFSqySeBKJ1fp13MIk8B40fM6YdEgIyZwINbh9tBHdW9ghaJWrYp6V6/WLdhrXr0/Y2PjzO/aiSqYzFC6JPGaL8YtkDEuHzOZYd0DD/LdtbfRybIoIYsgCJLIKMqAtXawMeTgss1M2LFjJ6Ojoxx7zDJGhoejndUv+s679gvm5+cB2DU/T39+HnCo686d2zF+Z1+96jrm5+cRMSUU7nVAVwD/KnCHumzfNqM1iXxCrt75eS2PskX/MNapzG+o6hpFpzyGb8rvnp+fZ+nSWc4753N0u13+X3+uve4GbrzxH5mZnqIobKT97dGbRrh7rMlaweeokmUZu+bnyTLDFy44h/32ezm/zs9fvus9bN26lZGRkXCRjdNUphRZA7wI+DlamakmcOE/m6f5flQBUiulaVflSwpTDlYmCx2siDM5mzdvYWbxjEdLpTXFDOtKRb9P3sl55JFHfNAjlc8pzYE2IISW3DWBTZztBGOEnTt3kmWGL196Mfu94mXs2rnL7cJqb8bJkTiwpx6Pj5qyPONty47hwvMvZHrJUgprfWGiitaMT86mQL+E8vtSBWpSoYda1y7cAtRwg8SoaAk+oX2Qz4Lug2pfINdgh4gfxa6dO91AjcEGhZ0qeqZRKoA8I8syZ44kQTO1BC+IHHaIDUm4U4MJqhf+/HyBtQWXffEC9nvFy5ifn6fT7TAQSUtyN2sVzQxZlnH0O9/FhRd8gcVPeCL9+T5JGl7+PwP6DkPiM6AnCJKryx1aEQtjtVnVcgOQDKEPHKro8Qp9RPIAEwiBzAC+CIJqaYm+pAUu8WFC7bjDWF/j58KQtCVxwytBf36eouhz2Zcu4oADXsn8/Dx5ng8wLEpYWynno96EHf/uv+Lss89jdulSin6/8mUVguHn5aJAF4oCxwOH+sQto3XqilGPglpfgPchp/H7eomqnqXWqlo1LQFtA6JoxVy1+TuKBoLKW6jFdQQWBgk2QFBjjEpVMUbo9/v0+30uvuhcXvPqVzE/36+EL62qKHXk5ZfaWmd2TnzvyZx+2hnMLpmlKAoPqkmFbYoIIsZv1iq0NX6WZyks8SGbaSy5+kw4BdtUVazLrs5Q1VmnENZUGas2IYUQxNMWbDFGBltkoPVCYK0PKmxkFqkz8Wq8NigYGVyouWPHdi46fwUHv/ZA5nf1ybMsRitkMHRZzjHPM97/gb9l+Wc/x+zSJRRFEZm+GLqos2uvNMZPYFZVzygj6VYTlDpeX7or1OpLUD1MVQuBLEyeQrtbDqqwMU1lIEwrbY65WWteGM4gXggUEUNhLdse3cbKFWfx+tcf7DU/a/qftr9LJbKWPM/5mw9+mI9/Yjmzs7OV8CWsA6MR7KHRtATKUiYcpvASXN6U1Q7YfaHR2JaKQxW0B7q8coUhw6IB+fq4wxYVRLxbMyTp67FN14RxUdr3Cq8qd4fXOOOV45Ft2zjvnDM54ojDvc3PaqnJYMdbmqXCC//vPnoKHz3lM8zOLo40P1o8bY8tJNY8EUFFWA7SC/hL1W40UeVL1ajL3d+oygv9/w1tNYGEr2NtUjrU3QhdExggLUNGptESEJEijEt8Ijg3N8fnz/gsb/rzI5zws7x9N7YIXxUKW5DnOR/92Cl88EMfY/HiGZeTENZxxYfG7TFGC9pc5gEvBN7o6C7e6gTOotQAH6zSAzm5DIfbt35cKauR0yBDbRCVEsvTYArYiDNTQeSE1yNyymUUtnnLZj53+nKOfOv/dmYny8MCWlCA0UbB2KpSFE74H//Ep/nghz7O7OLF2MIGiGBcaJd2SxpHZSmeDSc72aIapMOmBuG840DeCPpsR1xT0xayNRYEp0E29QGJ3Rdt9wsSRj1RXB86ttgXlPWDjRs38dnln+QdRx3phZ8Fzl4T8yN17Ox/WWvJOzmf/PSpfOBv/o7FixcnhSEZEECSrLC2hNcQlDafDbzR2c7a95qqUCJiXYXLvs8XckVb2F5R3bbMhBW0sDWDgjQclXZbHGTHVXQVUlECJl60ywTEGDZs2MinTvkIxx17NPPzfbJS+NWqymAT4bGfPM9ZfurpnPz+DzEzM+3DcW31UVFlp67+B+OMiQKBnMqU/n24PMGGNsplcG7ZXwI8R61VTyOsvqhkTGiaGGlYdtQFYu0FIqNBO6va0nGyaMSwYf0GPv6xD3HiiSfQ95ovklxIwmQlfqnoF3Q6OZ897XO896S/YWZ6ulICCaWvMd1FkwJalRNIHNElLsv4jz4H4SVlObjk54Qr9W7Pu9SowmTbi/8xBB9wiFgg1pb2RYmJtwELL8mIsyxjw/r1fPADJ3PySe+ln2q+tgxAJFKMflGQd3LOOPPzvPd9H2B6ajLJwtv1RQdplBAVhpqRiJekIqr67vBtxuOjBfBEhT8gRHA01fBmaS3MRhthaJv2tS6KJGbHxlGQ96JZlvHwQw9x0vtO5MMfer8Xvom3nAwIf33yVxRO88/6/Dmc8O6TmJqaCqplErPaGrFqi93XNmSgib+oYrwQ/0CdrAuH4ImU8dqbPFG20IoQoHGqpLEJQmkyGNqEK7uHeUM2XnWGIKha5VnG+oce5rjjjuaUj3+Yol/UIN6CWy60+Q59XXHuSo5/90ksmpysKJcN9HYQt0gqgdaJWCBsaaHGVAMUClUmQN/k35Obumanr65qUaEt1GYFq0GCFgn8w2Cgqxmh0Sj4V7sqoMh0OjkP/+pXLFt2JH9/+nKKfuHAMJNwNNt2m3/N2fwO56w4j3ce9x5f1XK7VqISaLu5kVY7lPBPgyRSQhJBzaMtL/LqMvY2Wpof5QVlASYkdkQUvyD7jcEwW9P/GkVsaQTPkixIGmxoEEXkec7Dv3qIN/3Fn3H25/+eorAeiWxmPdVuS3ZEqfnnrbyA4951IhMTEzVZVuI6YVxxa7P/qY2RgJQcF6/Db/URcRl+vkDRJ4IWxm+1vVV1QtUWtkwSqkikSSekEbeXOEqT0dDQSmkPryvuUBkWq9LJc9Y/9DBvOPR1nL/ybEoVahZ7EjMXkKv6XvPPW3kBxxx7AuPjEwFTQZpIoS7kdHVAxK8Ds4NkfOLPH0yg7F2FoWrtQZ5MpQygDEpAeNIkuxWf0BS2aK18NcyztoSqJf3FXzPvdFi/fj2vPmB/vnjxBWQmcyG4kd1GVGXq0feh5srzL+Lodx7P+Ni4x/BtC3bTZkLTk0AtQGJy8qUNZmw86S56kCvIWJtb1d8OzU9rOCUpMSouiFS1hMgdaRN9bA3vYg5qJ8/ZsH4DL33pH3H55V+k1+1h1dbC1wVyizLa8cI//4KLeMc738X4+DgIQbYeELIqqyItZjSNajThMmm7pUidcMAR8P//bSA3wAzwjIAMEmEv0SCCozkhTUQTBsNuk69WzXUZaN7psHHjRvZ98d585arLGBsbo7AFRkzzKwZAzEXfxfkXXPgFjjr6XYyPjlGeKWtlqLUz/SuKYeygmskZCwAVjbMK9QWeAcwYlN8EJr35kVj42shQ4+OndYJUnS2IPiokK7ZALdZp/uZNm3j+7+zFNauuZHJysg43m64wBtwCs1MKf9lRxzI6OooYp/mSnGLUxoHDkJAQKnEcLaSBkLTVXSU8IRqFNeUoJhF+06jqPr7aZVOlqPiXIo1DDs0iRFIXTuGAlt0QHo81JmPz5s385nOexeprrnJYfL+PyUzkbCXdQRIDa51OzkVfuIRl7ziWkdExjBFsoU1fGdqeROkiV6oaZ9dJ9DU4zxRPlAhoNLWiWG+K9jEuHJIBGh8eVI7Dw/RoQ3mwuzXDbTMXwVw6nS622MkznvF0rlt9NU960h70+wUmy0hKUQOT6qIoyLKMFeeuZNlRxzFaCt/akmRAW3m/JRaI2HKa7LvQxqsulFU2oe/44DYo+kQD7JOQMRtFl+gAX2J6aoDKUrTB0TqA+hH8ntuyhSVLl3D9tV/haU9/WgWu1Vy+hQGZsoz4zW+t5fS/PwtFKQqLEeP2TADqJeIMdrZGCZRqiz2v+K8t42p10omdqixQCaOyj/EHqIOMrcKxG2w0bTs9WR1TstiiaHpJGUBPCeL5PZ+0B6u+cjW/8RtPd/hOnvkTxruHMKy1ZFnGTTd/i6tXXcdf/MWbWfb2tzEzPc2WubkKug6TPFoeKkm0E7UniE9apuNvRI4SHBuHuBwvUdFKcuDJWjOzkp4QCR+/DYL2pCRt4wYtUId1nE2HT73qgFfVwsyzRlg5qKhv1Qn/5pu/xarV1zM9NY0x8MIXvIC99tqLNWvWsObGr1P0C0ZHRyls4ZnabUUJaZxBqHxOOfeoxrCQCWorR0i4QOXFnmxUdY8oBI2ANm2eshzEdEBbCjK7SZpKUpe1FEVRs+lkAVSTWPj/8I+3sGr1V5mdWczIyDAjIyNYa1m0aIKjj34HnzjlozznOc9m06ZNFIXzK6qJc1USLKoVgIijwCRSrM5AtmL2jQCgbDKyh/HneQmPFTXYCSVxNxpMemBCsUEmPLA4TzN0FJGKLR3lQgN2Qin8W775ba659gampqcZHhlmbGyU0dERxsfHGB7qsWPHdvZ63vM47dTPcMIJf0m322Fubs4Xb4QEc4193sBaTnqciei8dKmMzepwE2tCXb1SoqOfmna80OpsrracpdKWgsxuqxlCe4ZcYjhJMT8tojuz822uWf1Vli5ZzOjICKOjo4yPjTE+Nsbo6ChDQ0MMDw0zP99HjPDWt76Fiy5cyX6veDmbt2xh166AqhiFpE3GRlTpC5+TljJBmI5rDDFpemLcBapJLx9NegDZtE5bAmbxVVWJF0BocUBJiNHKHw3NkDQdrjGsXXs7V6+6lsnJKUZHR1k0Mc74+Bhj4+OMjY8xPDLM0NAQ3W6H4ZEher0eW+fmePpTn8aZZ5zOaad+isWzM2zcsBEj4nn/IS8phEZS3W+JKpK2Ebowohe9ZHwrkaS40ALI6QBAP+le0pruNopMMoBYowP9RRntrF17O1devZolS2YZGRmpTM7Y2Bgjw8MMDw0x1OvR7Xbodbv0Ol263Q5DQz36/T7bH32Uww49lNWrruJtb3sL27dv55FHHiHP8xq9pVnfbbWdjcRLIodeg7YNQKn6QqNUXacitrWqtiJ/rQtbYjCFHVhqbCXSDMiMW5OsPOOOO77P5Vdew8TEBGNjoyxaNM7Y6CjDI8OMDA8xNNSj1+3S6XTodDp0e106nZw8d49ur0O322XLli1MT02y/NOf4MuXXcLzf2cvNm3YQGEtWZ7H7Axi00x6Hi1JzSWsAOqA37WHEKOqD9QmXRsOIzVpYRuyeuHERzL9dg88iKae2HlpCQ/LJOt737uLa69fw/T0FBPjY4yMjLBoYoLx8XGGh5zJGRrqkXc6dDo53W7XCd4vRievF6I31MNay6ZNm3jZS1/C9ddfw0c/9hF6vS6bN24kyzKfO2hrNBFVBVNIPaDsaSLDMBnwkegDBvild7iu2YPVZj1TkyymZWCqWmfC2mYcG7Ti2s630EbKSlaWZXzjplvY/5X788Mf/oCnPfXJTE5OMj42ytjYqA89h2uB5xl5npMZUwk8zzO3EzJ3ICTLMvJOh16vx7Zt20Dh5JP+im98/QYOPvhAtmzezI4dO8g7naC+qwmqHNasdQDde2AkVz77S6P+pHLFNo4a8TQL8alPcBhQwN9cCIIexE2Upp8oK1nf+c53OeT1h7Lt0V1cf/31nHPOCoaGejzlKU+h0+lUmt/tdMgzL/DML0KWVf83WUaW5WS5f86ffOl2u2SZYeOGDTz72c/iK1dfzqVfuoinP+2pbFq/3gOFJirPNmrCoVFJF6Ql2guJGtn4opnnAS9Wq9bz2oOjP+0RbbohRdwpxMMPez3PefazsNa6LBdFVKr2Mc3UXRq+WqgrWbfdfjsHvfYQtm17lKGhYfK8w7/87D7+6Z/u4lnPeibPfe5zq4N4nW6HzAs180efSo03WUZmTCX8LDMYk5Hn7niUEaHTzSmKgvldu3jhC5/PEW88nB07tnP77Xeya75Pt9tF1UYkrJY66GDcJY6lrDio9CoDPJjSK2qLYwNOZzNJCa1RxAsSYpKut3ptEVQ6xlL43/ve9znooNexZW4rQ8MjFfd00aJF3H///Rz3l8ezcuVKFk1OMD42hgCdTsdrfk7H74CsFH6WkXuhZ5kzS5kxGP+aMYY8y+h0Omzbto3xsTFOP/1Uvvvdm/ndFz2fHdsfJTMZEcQTmFlJqoAR+BciwIRMOn3QqOptXtImRj0TqoWm+EccmqoqRb+/G7iC3XM1Ozl3/+AHHHjQIWzevJWRkTFsUWB8c62iX9Dr9ej1hjh1+WksO+poNm7ayJIlSxCBPDN0O1744SLk/mGM3wEGMaZaBCPubwTy3EVQO3bsYHZ2CS9/xcvp9/tBW5vYH0jKzlCtBZ22N5OKEGcVbjPAj4HNoFInttqgZKe9zxr4dtJnaHdJSPqGwtMF//lHP+LAAw9h/YaNjIyO1RhRGWeLVAc1Jqenuemmb/K6172Br61Zw9KlS+l2u24h8ryy86VfyDJTm6NS+NViSLWLer0u//Zv61h97Q1ce/0a5rZuo9PpYW0Rq2VyXk1bEuLWArh7ZTPKjw3KBoX7fMar5Qm6ga0WVRvFah1U9B0EpiVHTkp+/r33/gt/fODrePDfH2J0bIx+Ivyo24+6KGnR5CI2bZ7jzW9+Gyf/9fvp9bpMTCzyfTnLqKc0M7XZMYHmI5BnOUPDQ8zNbeWrN3ydVau/ysMPb2B8dJQ8yxrdGBvwgsboe0pYjpymE+Z9CBuMon1U764IkhE/0zZaRGpLnlXZtLZKtSb1AQ3JslIJ/+c//wWv+eODWbfuAcbHx+n3vfAlLgNKknUW/YJOt8vo+DhnnnEWB732EO677z6esHSpd9BS2XhjJBC+VMdNh4aGKKzl1tvu4IqrruFnP/8FvV6XLM8RI87/VLWOBp6TVAfjdjmpItZdM/RulH5JzLq2rAnUR0GbJKxmkhsWoAfA0NFI4+f7hTs+uu7++/njAw/mZz//BeMTi+iXZ3Hb3EX4vF8cta4P0OT0Ym697U722/8Azr/gImYWz9DpdKvjq6XdLxe2N9Sj2+3yk5/ey6WXXcnaW++kKJRut+eOnpIQjtsgCW3hUOiC1KCyFnCto6c74d4BzKnr/6aa9ukMBCtRr9IWvLzVxEtKGMAWLsN9+OGHOeigQ/jxT+5lYtEk/f58JXyN0vvwdEsYedRf3+/3mZgY59HtOzjyyKN4+7Jj2LVrFxMT49jCugUQyDs5vV6PB//9V3xl1XXc8LV/YG7rI4yMDFfVQGOoFsuIqfyhptak0ZpS2lHf+k0ZMIfrtIXxTzwIfL/M/huEWdWWeDeGsNPePBUS2uIHCl/52rRpE689+A3cddcPmZyacprv24mmlFIhxVzqdL+ilYvn/ucdJqYmOe/cc/nDP3opa9feytj4GHnmBL9zx05uvuXbXHHVav7tl/czMjJMr9cDahMlXujOiWdxR61Wsx4gydK+UbSGkb+P8CCQGUSNX90byi7LC4Uv2gobuAEU3k4ONkU1qjk3N8fBrzuUW9feztTMTNUCIExyKs0vnbCUniMGv8L3iSfKFkXBoqnF/OjHP2W//V/DGWeczY6dO7jr7nv48pWruOvue+h2OowMD1fXyjJDnmeImOo8QqeTI2J872xttStx+cA2FkgjDj+g3OAV1OSoayQhwsWqvB8Yd/i0szfN9mKx4IM2GtUCDKo/lpWsRx99lDcc9ka+9c1vM7V4trL50Q7zkViKz0nY46BBNxNft3Xshvn+PGNj4/SLguOOeyc/+T/38tu/83z687sYHx+roPQMU5knJ/g6lsnzPAkwwkReg0Qs7NCoUe+VQFSZwpzAxR4M7fuSpM3U6oOofrvk2qYH66MbNDRoGUk3wDb/a50N3rlzJ39yxJ/zDzd+g+nZJfTn530UVWq51LbXyOBiskql/dJIduo+DkVhybMMk3V55JGtTC6aoNvpIuJygNLEhEBdFmBJgF8c8bVfTU7Ep/9K1MUk6iuOiqDfBh5EXM9Ro/HuOFUjUn8NvLmmQbtJZaNKWYA4eFUuioI/e9NbuG71V5mena26TlWdRkKTg9Ck3yQ+QAfzvsq0H3FnPawqQ0NDzsZnNVKaZbnHixw+VGbJ1W+fO4T9QKNG3UkhqUqlmpFgOeJTw1DW+FUq/HfdAvzEDz/qdqcNjkwTF2ojZoU1g7e8dRlXXXEVM0uW0J9Pbf7gzE1az25JS8uDcMWkwY4si/9VQiamBvCyUPguaTPGwRfxeQKNKle6UJZfY2jWj+wnCrd4tKjwJ+WDQ9toX0Q+6fMB1Rb8U9taRvoLpRWxuoWMYdlRx3DJxZcwPbvU9WWLohyhebS9CWVIq20rm/qlJz5a5OGa4Dpt94/Ma7kJgLk4ezathSKkBRWtXIJGJa2yaaLCJ1Hto3WPDhPQSzxhVC8D/am/g4UNDyHE9wpoSXqtjWvFHio+9rjjOe/clUzPLqXfn28KXmpYu5VLJG2LIDFhNzKZQV07gNMrAYdQhDc/WctrZQBiogPg0pJTDS7CCBUR96eqehl1f7naBAVjF4WdwCmSWNlQC1QGQTwBMmodWfZ9J72fM884m5klT3ChZgXHSqONwKBoKw19m9NOE6LBlDUxEkMS3tlLsCCZcYy9TqfD5NQkmzdvSmoWKSF9YPuO+my96CkCO1PvZWJ7rtbdWorLFL6XrlaTl66RAKzWp2XyPOdvP/QRPvXJ5czMLqnhXAlw8bLblJjBFDihlQYiUXomETA2iLtQg3EZRkzlkN3/PVThE8WJRRMgcNaZZ3H+ygsYKvuatm5SaSuQlEmtwcky0v66cWvA/fS2ygA7Qd8DcrOWt5kacMQoNCVlz4der8cpn/g0H/nwKUzPzjaK9XVBoq4iue2eVpV0cK1JWLAE6riZEkUkxme2pdZXoKAfiy0Kur0eIyMj3HrrWs49dyW/+NnPGRkbc6ipEmFfbay3pA+jP/Su70HZqf4OTSHXNK9ZpFWDxcK9UW5R1SuAw4DC38ymnV/ibfj8rnmMMXxm+Wn89Qc+zNTimSg5E98EOGIRBAKQYFHa0I/GWa2BcHj7cxX2L6YG9YTqYPjk1CTrN2zg7LPP5oYb1mBMxvjkpEdCpeHjGzGbRpBkAWQCV6hyi4d8irSZdx7b9/BeBCpAeaupxVI2G0pOaYdliJmZGS778uW898S/Ymrx0oApF2h6GjSEdMQB/czaOlXU3XIHaL+mhJwgcTOCKbGjfsHIyAidTodv3HQTF5x/IQ+su5+xiYmqtYG0nVGQweS+yvSoPozIsZSNQ1t4VXltqsIu32p92vwQ6DECVyAUqL+bUGIWisIyPDbGxZd8kbvuvoexiamg+UViJ4PFFol9p0SNL9qMnbYSjge9r/aaEuFL5b1HMjFMTy/il+t+yYXnX8hNN99Cr9djfHKy2rlpo6bwDLg2UPbKCFmv3Meo6kNaan8LpJnXRUibUPCkvGHNlQinqXK8a+JK3tBKhV63xy3f/A5DQ0PkndwfipMqiRl0oCSNZUL+fX0dYcC2CD4bHIvVdKElOlShKGOjo6gqV199NRdffAlbtswxPjGBeqp85as0dPpEPaqjuzjV4+krmqOcBlyp/uYOMXJWzyePsfyUB+nsmConAvui7OMyOLISGSG4K8ToyGjdcydp8Kq+UN1625ywwC268BFSjfsAKO11aIn2n1S3a7SqTE5N8S/33suZZ53F3d+/m+HRUcbHxwN/RXRWQQbwKsN+ECUY4BX0NoUTcX2YikYAHcwhb+sIIs3Cmqryp8CduJsWWHVBhWt97zXPqk1CFgkaTKX3CxtgU1ub62lrAqgtxRBtKz95eGtqehojcO6KFVxzzbXs3LmLiclJf8rfBlGvJHY+1VyNwgnvYSxohuom4E9dtKORmxKazOlseHRRg3ib1M1VXI+zjbh7LR6KMBSoZBN4KnPvhv1cqJ7aLLo0Y1BNWAk6kBEYYTaA2oLFM9NcfsVV3HjDDXS6Q/SGhtyhEg3wJhFa2yuEULg2Rlze52Uz6KsU/tmfUbW7I4fI9OyTm3cl0raiivo7Q3AoyhUuNMXEebGwYLdWjdER3Q1vJda4loVrHBUaxD1y19++fTvGZIyMjETmZtB1a1p5+z3AAlW1ztxwmKJXouVdNJqZQjrMbGhkolIxbbmhcR2bY719u0fhAeBg91zV4b4dmGpgI9Kap1b9iWQhal96TzBaENXB69/tOAJvUQYICactzK13T2kq8TNRcVHOMkUvQavm3Y1xS2pdBbLhkQnC+zdKeB+t5KC1ghXn4e9EqkWQKo4NL9N2N+kBxyajjizhIYmwlRm7/xl4uLIyLfWipYtd3yyojeAc+oAKaHSxvrsp6DKQ5P4xAyBric1xNjw8HvXSDNvYh+lT0NvZKuSC3KnwY9D9BBnxq26a0WJN4ZYW0kB9OJkgL9B2kxbdx7cmETcSyfKmbQ3EQ6odKIGtl9bWcNrw+8F1+qqaibAJ5M2gFyP+vjEMahCurb7F8P/30/erfTnwKuegm3bvf+hPOfeNfu6X/zpzN4/BQO4AXgx8x/9d0Lhvyv+IH0sZ57u5vpjyLnq/huKZx0AbMuBejxmd5v82/8N2Qz/gUJ3m53ov5S1Lfo0f8xgMrggEfgLwJ7goqbzbnP1vrvXWz+UBP7cTggUpft0LmMdwoBL4hb3rAkQ1UPvf0NyU47/Mz6m09/JYzcc8hoPWwCQ9gLsB8iuB2wKz9F99IULBZ37sr/RzeSAwOfpYXdA8DpMoKS4G+Drwh8CRwD3BQqh/n/4XEHo4llLw9/gx/6GfQ3nLxuKxvrh5HCdl/WTmgfNxd5E4EviBn0zmf/f/ExajFHo/GcsP/Bhf6Mc8T1lGfJzGZx7niRbBBHf5Sb3Ab+vVOJp2HgigeJwWRJPvLseU+zGs9mN6gR/jrmRMj9tP/h+obRL4ga/7x57evh4A/C4wNmAnkSTAC/ULSwsOJhB4+fMIcDvwNeBSYF2IjwW+4HH/kamZJwU3MNao1joAigie84DdAPi2CUVU1Y2ylbutWt4Ie4rwIpQDFf0t4JlgFi8ERUB5611p3A69giJcO7L1KPci8iPgOtA7RWRdzApE1N08U7UBRcTYWNmaJyQRVDB2ecpUWuDxoHdciQXl/Mf/aKBdZZhnvRauA1b515YAz/Xh3xJgX6AD7OEfKd4qPlJ5wNvutcBDPlu9x/8/Nb/mPztX+b/h2fdIWMdXowAAAABJRU5ErkJggg=="/>'
            f'<text x="60" y="33" font-size="30" font-weight="700" letter-spacing="6" fill="#0d1424">KATACHI</text>'
            f'<text x="250" y="33" font-size="24" fill="#566176">図面がなくても、つくりたいものを工場に頼める</text></g>'
            '</svg>')


def restructure(body):
    """h2 ごとに区切り、見出しに番号とアイコンを付け、本文を見やすくする。よくある質問はQ&Aカードに"""
    i = body.find('<h2>')
    if i < 0:
        return body
    pre, rest = body[:i], body[i:]
    parts = re.split(r'<h2>(.*?)</h2>', rest, flags=re.S)[1:]
    out, n = [], 0
    for h, b in zip(parts[0::2], parts[1::2]):
        if h == 'よくある質問':
            m = re.match(r'\s*<dl>(.*?)</dl>(.*)', b, re.S)
            if m:
                items = re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', m.group(1), re.S)
                out.append(faq(items) + m.group(2))
                continue
        if h in ('出典', '関連するガイド', 'このテーマの作例') or h.endswith('のほかの作例'):
            out.append(f'<h2 class="sub">{h}</h2>{b}')
            continue
        n += 1
        out.append(section(n, h, b))
    return pre + ''.join(out)


def guide_index(arts):
    """ガイド一覧：分野ごとにアイコンつきのカードで並べる"""
    groups = {}
    for a in arts:
        cat, fig = topic(a['slug'])
        groups.setdefault(cat, []).append((a, fig))
    out = ''
    for cat in ['business', 'parts', 'cosmetics', 'food', 'supplement', 'apparel', 'goods']:
        if cat not in groups:
            continue
        c, bg, name, _ = CAT[cat]
        out += f'<h2 class="sub">{icon(CAT[cat][3][0], 22, c)} {name}</h2><div class="glist">' + ''.join(
            f'<a href="/guide/{a["slug"]}/"><span class="ic" style="background:{bg}">{icon(fig, 28, c)}</span>'
            f'<span><b>{a["h1"]}</b><small>{a["summary"]}</small></span></a>' for a, fig in groups[cat]) + '</div>'
    return out
