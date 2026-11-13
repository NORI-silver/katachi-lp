"""記事ごとのOGP画像（/og/guide-<slug>.png・/og/idea-<k>.png、1200×630）を書き出す。

ローカルで実行してPNGをコミットする（CIでは作らない）：
  python3 tools/og_images.py .          # 無いものだけ作る
  python3 tools/og_images.py . --all    # 全部作り直す
Playwright（Chromium）と、日本語フォント（Google Fonts の Noto Sans JP を読み込む）を使う。
"""
import os, sys, json, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import visuals as V
from guides import ARTICLES
import ideas as I
import factory_pages as F

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else '.'
ALL = '--all' in sys.argv
FONT = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap">'


def jobs():
    for a in ARTICLES:
        cat, fig = V.topic(a['slug'])
        yield f'og/guide-{a["slug"]}.png', V.og_svg(a['h1'], cat, fig, 'ガイド')
    for x in I.IDEAS:
        cat = V.FIG_CAT.get(x['fig'], V.IND_CAT.get(x['ind'], 'goods'))
        yield f'og/idea-{x["k"]}.png', V.og_svg(I.meta(x)[0], cat, x['fig'], '作例', I.meta(x)[2])
    for p in F.PROC:  # 工場をさがす：工程ごとに1枚（都道府県のページも同じ画像）
        yield f'og/factory-{p[1]}.png', V.og_svg(f'{p[2]}の会社を都道府県から探す', p[3], p[4], '工場をさがす')


def main():
    os.makedirs(os.path.join(OUT, 'og'), exist_ok=True)
    todo = [(p, s) for p, s in jobs() if ALL or not os.path.exists(os.path.join(OUT, p))]
    if not todo:
        print('ok 0')
        return
    tmp = tempfile.mkdtemp()
    items = []
    for n, (p, s) in enumerate(todo):
        f = os.path.join(tmp, f'{n}.html')
        open(f, 'w').write(f'<!doctype html><meta charset="utf-8">{FONT}<style>html,body{{margin:0}}svg{{font-family:"Noto Sans JP",sans-serif;display:block}}</style>{s}')
        items.append([f, os.path.abspath(os.path.join(OUT, p))])
    js = os.path.join(tmp, 'r.js')
    open(js, 'w').write('''const {chromium}=require('playwright');const items=%s;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});
for(const [f,o] of items){await p.goto('file://'+f,{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:o});}
await b.close();})();''' % json.dumps(items))
    subprocess.run(['node', js], check=True)
    from PIL import Image  # 色数を減らして軽くする（1枚20〜30KB）
    for f, o in items:
        Image.open(o).convert('RGB').quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(o, optimize=True)
    print('ok', len(items))


if __name__ == '__main__':
    main()
