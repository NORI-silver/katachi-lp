"""工場が打診に返事をするページ（/reply/?k=鍵）を作る。

  python3 tools/reply.py <リポジトリ> [受付URL]

受付URLを省くと、トップの index.html に入っている受付URLを使う。画面と日英中の文言は tools/reply_template.html。
送信先は backend/forms.gs の type:'offer'（依頼の要点を読む）と type:'offerreply'（受ける・質問・断る）。
検索には出さない（noindex、sitemap にも入れない）。
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from site_common import GA

REPO = sys.argv[1]
FORM = sys.argv[2] if len(sys.argv) > 2 else ''
if not FORM:
    m = re.search(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec', open(os.path.join(REPO, 'index.html')).read())
    FORM = m.group(0) if m else ''
body = open(os.path.join(HERE, 'reply_template.html')).read().replace('__FORM_URL__', FORM)
head = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>依頼へのお返事｜KATACHI</title><meta name="description" content="KATACHIから工場・開発企業へ届いた依頼のご相談に、受ける・質問する・断るで返事をするページです。">
<meta name="robots" content="noindex"><meta name="referrer" content="no-referrer">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA[0]}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());{''.join(f'gtag("config","{g}",{{page_location:location.origin+location.pathname}});' for g in GA)}</script>
</head><body>
'''
os.makedirs(os.path.join(REPO, 'reply'), exist_ok=True)
open(os.path.join(REPO, 'reply', 'index.html'), 'w').write(head + body + '\n</body></html>\n')
print('reply/index.html', 'form=' + ('set' if FORM else 'EMPTY'))
