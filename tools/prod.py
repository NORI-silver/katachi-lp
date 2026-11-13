"""katachi.html（Artifact用）から katachi.shiokonbu.com 用の index.html を作る。
使い方: python3 prod.py <scratchpad> <出力フォルダ> [FORM_URL]
"""
import sys, json, re
S, OUT = sys.argv[1], sys.argv[2]
FORM = sys.argv[3] if len(sys.argv) > 3 else ''
SITE = 'https://katachi.shiokonbu.com/'
GA = ['G-3C2RRECKB8', 'G-ZYX17VBTWB']  # KATACHI専用（2026-11-12）, shiokonbu.com 総合（全サブドメイン共通）
s = open(S + '/katachi.html').read()
d = json.loads(re.search(r'window\.KATACHI_DATA=(\{.*?\});\n', s, re.S).group(1))
N = d['realCount']; NA = d['realAbroad']
TITLE = 'KATACHI｜設計部門がなくても、自社製品をつくる工場チームが見つかる'
DESC = (f'つくりたいものを書くだけで、AIが作り方を工程に分け、国内外{N:,}社の中から工程ごとに得意な会社を組み合わせて提案します。'
        '図面なし・試作・小ロットから。料金・ロット・確かめられる品質を比べて選べます。見積の依頼は無料。')
# 本文の「よくある質問」と構造化データ（FAQPage）の両方に使う
FAQ = [("費用はかかりますか", "工程の整理、会社の検索、見積の依頼は無料です。試作・製造の代金は、依頼する会社に直接お支払いいただきます。"),
       ("図面がなくても頼めますか", "はい。文章や写真、AIで作った仕様書から始められます。図面なしの相談を受ける会社を絞り込めます。"),
       ("海外の工場も選べますか", "はい。中国・台湾・ベトナムなどの会社も候補に出ます。依頼書は相手の言語に合わせて届けます。")]
def rep(a, b, cnt=1):
    global s
    assert s.count(a) == cnt, (s.count(a), a[:80]); s = s.replace(a, b)

ld = {"@context": "https://schema.org", "@graph": [
  {"@type": "WebSite", "@id": SITE + "#site", "url": SITE, "name": "KATACHI", "inLanguage": ["ja", "en", "zh-Hans"], "description": DESC},
  {"@type": "Service", "name": "KATACHI 工場チームのマッチング", "url": SITE, "serviceType": "製造委託先・試作先のマッチング", "areaServed": ["JP", "CN", "TW", "VN"],
   "provider": {"@id": SITE + "#org"}, "description": DESC,
   "offers": {"@type": "Offer", "price": "0", "priceCurrency": "JPY", "description": "工程の整理・会社の検索・見積の依頼は無料"}},
  {"@type": "Organization", "@id": SITE + "#org", "name": "KATACHI", "url": SITE, "logo": SITE + "apple-touch-icon.png"},
  {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}]}
head = f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="{SITE}">
<meta name="google-site-verification" content="MmM3OGz9LIPxBOmE4jR8GdP4vACP_FrchZwBLT3W0sM" />  <!-- Search Console（URLプレフィックス）の確認。消さない -->
<link rel="alternate" hreflang="ja" href="{SITE}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="KATACHI">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="{SITE}">
<meta property="og:image" content="{SITE}og.png">
<meta property="og:locale" content="ja_JP">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
'''
rep('<title>KATACHI 試作版</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n', head)
rep('const GA_IDS=[/* \'G-XXXXXXXXXX\' (KATACHI専用), \'G-YYYYYYYYYY\' (総合) */];', 'const GA_IDS=' + json.dumps(GA) + ';')
rep("const FORM_URL='';const TERMS_URL='';const PRIVACY_URL='';", f"const FORM_URL={json.dumps(FORM)};const TERMS_URL='/terms/';const PRIVACY_URL='/privacy/';")
rep('<span class="tag">PROTOTYPE</span>', '<span class="tag">BETA</span>')
FAQ_HTML = '\n'.join(f'<dt>{q}</dt><dd>{a}</dd>' for q, a in FAQ)
# 検索エンジン・AI向けに、JSが動く前から読める本文（描画で置き換わる）
static = f'''<main id="app"><section style="max-width:760px;margin:40px auto;padding:0 20px;line-height:1.8">
<h1>アイデアを、製品のかたちに。</h1>
<p>KATACHI（カタチ）は、設計部門や図面がない中小企業でも、自社製品の試作・製造を頼める会社を見つけられるサービスです。つくりたいものを文章で書くと、AIが作り方を工程（センサー、回路、筐体、成形、縫製、アプリ、試験など）に分け、国内外{N:,}社（うち海外{NA:,}社）の中から工程ごとに得意な会社を選んで「チーム」を組みます。</p>
<h2>できること</h2>
<ul><li>図面なし・試作1個から・小ロットで相談できる会社を探す</li><li>工程ごとに会社を入れ替えて、料金・最小ロット・材料の手配・相談の可否・品質の裏付けを表で比べる</li><li>見積の依頼と、試作後の改良の相談（無料）</li><li>ChatGPT・Gemini・Claude などで作った仕様書・画像・3Dデータの取り込み</li></ul>
<h2>情報の確かさ</h2>
<p>会社の情報は、公式サイト・報道・掲載ページで確認したものと、AIの推定、要確認のものを分けて表示します。見積や口コミを作り上げることはありません。</p>
<h2>よくある質問</h2>
<dl>{FAQ_HTML}</dl>
<p><a href="/guide/">試作・製造の外注ガイドを読む</a></p>
</section></main>'''
rep('<main id="app"></main>', static)
foot = '''<footer class="sfoot" id="sfoot"><div><a href="/guide/">ガイド</a><a href="/terms/">利用規約</a><a href="/privacy/">プライバシーポリシー</a><a href="/privacy/#operator">運営者情報</a><a href="/partner/">工場・開発企業の方へ</a></div><small>© 2026 KATACHI</small></footer>
<style>.sfoot{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;max-width:1240px;margin:40px auto 0;padding:24px 20px 120px;border-top:1px solid var(--line);font-size:12.5px;color:var(--mute)}.sfoot div{display:flex;gap:18px;flex-wrap:wrap}.sfoot a{color:var(--mute)}</style>'''
rep('<div id="ov"></div>', '<div id="ov"></div>\n' + foot)
s = s.rstrip() + '\n</body>\n</html>\n' if '</html>' not in s else s
# head ends before first non-head element: insert </head><body> before <nav
i = s.find('<nav')
assert i > 0
s = s[:i] + '</head>\n<body>\n' + s[i:]
open(OUT + '/index.html', 'w').write(s)
print('ok', len(s), N, NA)
