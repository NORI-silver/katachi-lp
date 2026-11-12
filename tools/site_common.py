"""サブページ（規約・ガイドなど）の共通の見た目。legal.py と seo_pages.py から使う。"""
import os
GA = "G-ZYX17VBTWB"
CSS = """:root{--bg:#fff;--fg:#0d1424;--mute:#566176;--line:rgba(16,28,58,.12);--ice:#2350c8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:"IBM Plex Sans JP","Hiragino Sans","Noto Sans JP",system-ui,sans-serif;line-height:1.85;font-size:15.5px}
header,main,footer{max-width:760px;margin:0 auto;padding:0 20px}header{display:flex;align-items:center;gap:10px;height:64px;border-bottom:1px solid var(--line);max-width:none}
header a{color:var(--fg);text-decoration:none;font-weight:700;letter-spacing:.18em;font-size:14px;display:flex;gap:10px;align-items:center}
main{padding-top:28px;padding-bottom:40px}h1{font-size:26px;line-height:1.4;margin:10px 0 6px}h2{font-size:18px;margin:34px 0 8px;padding-top:12px;border-top:1px solid var(--line)}
p,li,dd{color:#1f2a40}ol,ul{padding-left:1.4em}a{color:var(--ice)}.lead{color:var(--mute)}dt{font-weight:600;margin-top:12px}dd{margin:2px 0 0}
footer{border-top:1px solid var(--line);padding:22px 20px 40px;font-size:12.5px;color:var(--mute);display:flex;gap:18px;flex-wrap:wrap}footer a{color:var(--mute)}"""
LOGO = '<svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><path d="M3 3h7v7H3z" fill="#2350c8"/><path d="M12 3h7v7h-7z" fill="none" stroke="#2350c8" stroke-width="1.5"/><path d="M3 12h7v7H3z" fill="none" stroke="#2350c8" stroke-width="1.5" stroke-dasharray="2 2"/><path d="M12 12h7v7h-7z" fill="#2350c8" opacity=".45"/></svg>'
def page(OUT, path, title, desc, body, noindex=False, head='', full_title=False):
    html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title if full_title else title + '｜KATACHI'}</title><meta name="description" content="{desc}">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="https://katachi.shiokonbu.com{path}">'}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{GA}");</script>
<style>{CSS}</style>{head}</head><body>
<header><a href="/">{LOGO}KATACHI</a></header>
<main>{body}</main>
<footer><a href="/">トップ</a><a href="/guide/">ガイド</a><a href="/terms/">利用規約</a><a href="/privacy/">プライバシーポリシー</a><a href="/privacy/#operator">運営者情報</a><span>© 2026 KATACHI</span></footer>
</body></html>
'''
    d = OUT + path
    os.makedirs(d, exist_ok=True) if path.endswith('/') else None
    open((d + 'index.html') if path.endswith('/') else d, 'w').write(html)

