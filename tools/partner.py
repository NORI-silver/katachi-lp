"""提携の申込みページ（/partner/）を作る。

  python3 tools/partner.py <リポジトリ> [受付URL]

受付URLを省くと、トップの index.html に入っている受付URL（tools/prod.py の第3引数）を使う。
画面は tools/partner_template.html、訳はサイト共通の tools/i18n.py ＋ このページ専用の tools/partner_i18n.py。
送信先は backend/forms.gs の type:'partner'（スプレッドシート「KATACHI 受付」の「提携申込」タブ）。
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from i18n import T
from partner_i18n import P
from site_common import GA

REPO = sys.argv[1]
FORM = sys.argv[2] if len(sys.argv) > 2 else ''
if not FORM:
    m = re.search(r'https://script\.google\.com/macros/s/[A-Za-z0-9_-]+/exec', open(os.path.join(REPO, 'index.html')).read())
    FORM = m.group(0) if m else ''

TITLE = '工場・開発企業の提携申込み｜KATACHI'
DESC = 'KATACHIに工場・開発企業として掲載するための申込みフォームです。登録・掲載・案件への回答は無料で、成約したときだけ紹介手数料がかかります。得意な工程だけで参加でき、日英中で入力できます。'

body = open(os.path.join(HERE, 'partner_template.html')).read()
body = re.sub(r'^<title>.*?</title>\n<meta name="claude:viewport-fit-sides"[^>]*>\n', '', body)
body = body.replace('__I18N__', json.dumps({k: list(v) for k, v in T.items()}, ensure_ascii=False))
body = body.replace('__PARTNER_I18N__', json.dumps({k: list(v) for k, v in P.items()}, ensure_ascii=False))
body = body.replace('__FORM_URL__', FORM)
head = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title><meta name="description" content="{DESC}">
<link rel="canonical" href="https://katachi.shiokonbu.com/partner/">
<meta property="og:title" content="{TITLE}"><meta property="og:description" content="{DESC}"><meta property="og:image" content="https://katachi.shiokonbu.com/og.png"><meta property="og:url" content="https://katachi.shiokonbu.com/partner/">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA[0]}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());{''.join(f'gtag("config","{g}");' for g in GA)}</script>
</head><body>
'''
os.makedirs(os.path.join(REPO, 'partner'), exist_ok=True)
open(os.path.join(REPO, 'partner', 'index.html'), 'w').write(head + body + '\n</body></html>\n')
print('partner/index.html', 'form=' + ('set' if FORM else 'EMPTY'))
