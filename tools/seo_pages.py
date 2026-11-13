"""ガイド記事・sitemap.xml・llms.txt を作る。python3 tools/seo_pages.py <リポジトリ>

- 記事の本文は tools/guides.py、llms.txt の前半は tools/llms_head.md。
- トップ（index.html）・規約・プライバシーは別の手順（tools/README.md）で作る。ここでは sitemap に載せるだけ。
- 新しい固定ページを作ったら STATIC に足す（lastmod はそのページの本文を変えた日）。
"""
import html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from site_common import page
from guides import ARTICLES

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://katachi.shiokonbu.com"
STATIC = [("/", "2026-11-12"), ("/terms/", "2026-11-12"), ("/privacy/", "2026-11-13"), ("/partner/", "2026-11-13")]
ORG = {"@type": "Organization", "@id": SITE + "/#org", "name": "KATACHI", "url": SITE + "/", "logo": SITE + "/apple-touch-icon.png"}

CSS = """<style>.crumb{font-size:12.5px;color:var(--mute);margin:0}.crumb a{color:var(--mute)}.upd{font-size:12.5px;color:var(--mute);margin:4px 0 18px}
.points{background:#f3f6fd;border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:18px 0}.points b{display:block;margin-bottom:4px}
.points ul{margin:0}h3{font-size:16px;margin:22px 0 4px}.cta{margin:36px 0 10px;padding:20px;border:1px solid var(--ice);border-radius:12px}
.cta a.btn{display:inline-block;margin-top:8px;background:var(--ice);color:#fff;text-decoration:none;padding:10px 18px;border-radius:8px;font-weight:600}
.tbl{overflow-x:auto;margin:12px 0}.tbl table{border-collapse:collapse;min-width:100%;font-size:14px;line-height:1.6}.tbl th,.tbl td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}.tbl th{background:#f3f6fd;white-space:nowrap}.src{font-size:13px;color:var(--mute)}.src li{color:var(--mute)}
.list a{font-weight:600}.list p{margin:2px 0 18px;color:var(--mute)}</style>"""
CTA = """<div class="cta"><b>つくりたいものを書くだけで、工程ごとに頼める会社をさがせます</b>
<p>KATACHIでは、AIが作り方を工程に分け、図面なし・試作・小ロットで相談できる会社を組み合わせて提案します。工程の整理・会社の検索・見積の依頼は無料です。</p>
<a class="btn" href="/">工場チームを組んでみる</a></div>"""


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


def article(a):
    url = f"{SITE}/guide/{a['slug']}/"
    pts = "".join(f"<li>{p}</li>" for p in a["points"])
    secs = "".join(f"<h2>{h}</h2>{b.strip()}" for h, b in a["sections"])
    faq = ""
    if a.get("faq"):
        faq = "<h2>よくある質問</h2><dl>" + "".join(f"<dt>{q}</dt><dd>{ans}</dd>" for q, ans in a["faq"]) + "</dl>"
    src = ""
    if a.get("sources"):
        src = (f'<h2>出典</h2><p class="src">数字はいずれも次の公開資料から（{a["checked"]}に確認）。</p><ol class="src">'
               + "".join(f'<li><a href="{u}" target="_blank" rel="noopener">{t}</a></li>' for t, u in a["sources"]) + "</ol>")
    rel = ""
    if a.get("related"):
        by = {x["slug"]: x for x in ARTICLES}
        rel = "<h2>関連するガイド</h2><ul>" + "".join(f'<li><a href="/guide/{s}/">{by[s]["h1"]}</a></li>' for s in a["related"] if s in by) + "</ul>"
    body = (f'<p class="crumb"><a href="/">KATACHI</a> › <a href="/guide/">ガイド</a></p><h1>{a["h1"]}</h1>'
            f'<p class="upd">更新日：{a["updated"].replace("-", "/")}</p>{a["lead"]}'
            f'<div class="points"><b>この記事の要点</b><ul>{pts}</ul></div>{secs}{faq}{CTA}{src}{rel}')
    graph = [ORG,
             {"@type": "Article", "headline": a["h1"], "description": a["desc"], "dateModified": a["updated"],
              "datePublished": a.get("published", a["updated"]), "inLanguage": "ja", "mainEntityOfPage": url,
              "author": {"@id": SITE + "/#org"}, "publisher": {"@id": SITE + "/#org"}, "image": SITE + "/og.png"},
             {"@type": "BreadcrumbList", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "KATACHI", "item": SITE + "/"},
                 {"@type": "ListItem", "position": 2, "name": "ガイド", "item": SITE + "/guide/"},
                 {"@type": "ListItem", "position": 3, "name": a["h1"], "item": url}]}]
    if a.get("faq"):
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": ans}} for q, ans in a["faq"]]})
    head = CSS + og(a["title"], a["desc"], url, "article") + ld({"@context": "https://schema.org", "@graph": graph})
    page(OUT, f"/guide/{a['slug']}/", a["title"], a["desc"], body, head=head, full_title=True)


def og(title, desc, url, typ):
    e = html.escape
    return (f'<meta property="og:type" content="{typ}"><meta property="og:site_name" content="KATACHI">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/og.png">'
            f'<meta property="og:locale" content="ja_JP"><meta name="twitter:card" content="summary_large_image">')


def index():
    url = SITE + "/guide/"
    title = "自社製品の試作・製造を外注するためのガイド"
    desc = "設計部門や図面がない中小企業が、自社製品の試作・小ロット製造・OEMを外注するときの進め方、頼む先の選び方、見積の比べ方をまとめたガイドです。"
    items = "".join(f'<div class="list"><a href="/guide/{a["slug"]}/">{a["h1"]}</a><p>{a["summary"]}</p></div>' for a in ARTICLES)
    body = f'<p class="crumb"><a href="/">KATACHI</a></p><h1>{title}</h1><p class="lead">{desc}</p>{items}{CTA}'
    graph = [ORG, {"@type": "CollectionPage", "name": title, "url": url, "description": desc, "inLanguage": "ja",
                   "hasPart": [{"@type": "Article", "headline": a["h1"], "url": f"{SITE}/guide/{a['slug']}/"} for a in ARTICLES]}]
    page(OUT, "/guide/", title, desc, body, head=CSS + og(title + "｜KATACHI", desc, url, "website") + ld({"@context": "https://schema.org", "@graph": graph}))


def sitemap():
    rows = list(STATIC) + [("/guide/", max(a["updated"] for a in ARTICLES))] + [(f"/guide/{a['slug']}/", a["updated"]) for a in ARTICLES]
    x = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    x += "".join(f"  <url><loc>{SITE}{p}</loc><lastmod>{d}</lastmod></url>\n" for p, d in rows)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(x + "</urlset>\n")


def llms():
    head = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "llms_head.md")).read()
    s = head + "## ページ\n"
    s += f"- [トップ（入力と工場チームの提案）]({SITE}/)\n- [ガイド一覧]({SITE}/guide/)\n"
    s += f"- [利用規約]({SITE}/terms/)\n- [プライバシーポリシー・運営者情報]({SITE}/privacy/)\n"
    s += "\n## ガイド\n" + "".join(f"- [{a['h1']}]({SITE}/guide/{a['slug']}/): {a['summary']}\n" for a in ARTICLES)
    open(os.path.join(OUT, "llms.txt"), "w").write(s)


if __name__ == "__main__":
    for a in ARTICLES:
        article(a)
    index()
    sitemap()
    llms()
    print("ok", len(ARTICLES), "記事")
