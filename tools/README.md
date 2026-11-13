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
python3 public_records.py <katachi-matching>/data/gbiz <リポジトリ>   # 国の公開データ（gBizINFOの認定・表彰・補助金・特許）→ data/rec/（会社を開いたときだけ読み込む）
python3 seo_pages.py <リポジトリ>             # ガイド記事・sitemap.xml・llms.txt（本文は guides.py）
```

## 概算の目安（`estimates.py`）
「概算・最低ロット」タブ、選択式の候補画面（`#gEst`）、文章入力の結果画面（`#mEst`）に出す数字。公開されている料金表・記事に書かれた数字だけを、出典URL・確かさ（公式の料金表／報道・記事／業者・まとめサイト／根拠の記載がない目安）付きで持つ。`build.py` が `est` として data.js に入れ、企業DBの最小ロット（掲載情報）も工程ごとに集計する。画面からは `window.KATACHI_EST_CARD(工程コード, 数量の上限, 数量)` でカードのHTMLを得られる。数字を足したら出典を必ず付け、文言は `T_EST`/`T_ROWS` に英語・中国語も足す（`i18n.py` が読み込む）。確定見積ではないので、作った数字・推測の数字は入れない。

## 製品イメージ案（`concepts.py`）
文章入力の結果画面の最初に出す「製品イメージ案」（外観の図・サイズ・重さ・素材・動力・想定スペック・主な機能・方向性・試作で確かめること・作り方）。AIのAPIは使わず、製品の種類ごとの典型例をキーワードで選んで出す（法面の草刈機、草刈ロボット、電動台車、ドローン、首輪型、ウェアラブル、IoTセンサー、ライト、樹脂小物、バッグ、ウェア、化粧品、食品、グッズ、家具、汎用の機械・電子機器）。画面では「AI推定・たたき台」と明記し、最終判断は工場・専門家とする。当たらないときは、AI相談の質問文で「製品イメージ案を2〜3通り」と頼む。
- 文言は日英中の組で `concepts.py` に書く。`assemble.py` が日本語を `template.html` の `__CONCEPTS__` に入れ、`i18n.py` が英中を辞書に足す。
- 図は `template.html` の `CFIG`（種類ごとのSVG）。寸法は数字だけ（mm）。
- 種類を足すときは、上から順に当たるので、細かい種類（法面の草刈機）を広い種類（草刈機）より上に置く。
