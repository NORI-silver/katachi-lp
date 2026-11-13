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
            f'<g transform="translate(80,520)"><svg width="44" height="44" viewBox="0 0 22 22"><path d="M3 3h7v7H3z" fill="#2350c8"/><path d="M12 3h7v7h-7z" fill="none" stroke="#2350c8" stroke-width="1.5"/><path d="M3 12h7v7H3z" fill="none" stroke="#2350c8" stroke-width="1.5" stroke-dasharray="2 2"/><path d="M12 12h7v7h-7z" fill="#2350c8" opacity=".45"/></svg>'
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
