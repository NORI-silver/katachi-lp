# 作り直し方

前提: 企業DB・マッチングエンジン（katachi-matching）が `km/` にあり、`real.db`・`fx.db` にデータを入れてマッチ結果を作ってある（`collar_real.json` `mimamori.json` `bike.json` `collar_fx.json`）。

```
S=作業フォルダ（km/ とマッチ結果と、このフォルダのファイルを置く）
cp template.html $S/v2.html
python3 build.py $S        # マッチ結果と企業データ → data.js
python3 assemble.py $S     # v2.html + data.js + i18n.py → katachi.html（claude.ai の試作版にも使う）
python3 guided_data.py <katachi-matching>/data/real/companies.csv <katachi-matching> <リポジトリ>/data/companies.json   # 文章の読み取り・選択式で使う会社一覧（8千社、使うときだけ読み込む）
python3 prod.py $S <リポジトリ> <受付URL>   # → index.html（GA・受付先・OGP・本文つき）
python3 legal.py <リポジトリ>               # 利用規約・プライバシーポリシー・404
python3 seo_pages.py <リポジトリ>             # ガイド記事・sitemap.xml・llms.txt（本文は guides.py）
```
