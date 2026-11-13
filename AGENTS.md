# KATACHI サイト（katachi.shiokonbu.com）

このリポジトリの共通ルール（Claude・Codex など、どのAIでも同じ）。

## 公開のしくみ
- GitHub Pages（main ブランチのルート）。`CNAME`・`.nojekyll` は消さない。DNS は `katachi CNAME nori-silver.github.io.`。
- `index.html` は生成物。直すときは `tools/template.html`（画面）と `tools/i18n.py`（日英中の訳）を直し、`tools/README.md` の手順で作り直す。
- 企業データとマッチング結果は、別の「企業DB・マッチングエンジン」（katachi-matching）から `tools/build.py` で取り込む。

## 守ること
- 実在企業の見積・口コミ・評価を作り上げない。架空のデータは「記入例（架空）」の画面だけ。
- 情報の確かさ（公式サイトで確認／報道／掲載ページ／AI推定／要確認）を分けて表示する。
- 新しい文言を足したら `tools/i18n.py` にも英語・中国語を足す。
- アクセス解析（GA4）は2つに送る：KATACHI専用 `G-3C2RRECKB8`（ストリーム katachi、2026-11-12〜）と、`G-ZYX17VBTWB`（shiokonbu.com 総合、プロパティ 292677591、全サブドメイン共通）。どちらも消さない。トップは `tools/prod.py` の `GA`、サブページは `tools/site_common.py` の `GA`。入力文・会社名・ファイル名など中身は送らない。イベント一覧は `tools/analytics.md`。
- 見積の依頼・相談の受付は Apps Script（`backend/forms.gs`）。**リポジトリにあっても本番には自動で反映されない**。直したら Apps Script に貼り直して「デプロイを管理」→ 同じデプロイの新しいバージョン、と Nori さんに伝える。受付URLは `tools/prod.py` の第3引数で入れる。
- 見積の依頼・相談で送られた写真・動画などは、受付（`backend/forms.gs`）が運営者の Google ドライブ「KATACHI 受付ファイル / 受付番号」の非公開フォルダに保存する（1件20ファイル・合計300MB・1本200MBまで、4MBずつ分けて送る）。サイトからAIのAPIには送らない（費用をかけない方針）。写真から仕様への整理は、画面の「見積に必要な4点」と利用者自身のAI、運営側の確認で行う。
- 工場・開発企業の提携申込みは `/partner/`（`tools/partner.py` で作る。画面は `tools/partner_template.html`、訳は `tools/partner_i18n.py`）。送信先は同じ受付（`backend/forms.gs` の type:`partner`）で、シートの「提携申込」タブに入り、写真・証明書は「KATACHI 受付ファイル / P〜」に入る。正式な規約と料金表は承認の連絡で送り、相手が同意したら状態を「提携成立」にして katachi-matching の `load-partners` で企業DBに取り込む。
- 秘密情報（トークン・APIキー・個人のメールアドレス・シートID）をコミットしない。リポジトリは公開。
- 利用規約・プライバシーポリシーは `tools/legal.py` から作る。外部送信先を増やしたら、プライバシーポリシーの「5. 外部送信」にも足す。

## SEO（Nori 2026-11-12「SEOもpetと同様にここから指示したらやってくれるように」）
- プロジェクトのチャットでSEOの指示が来たら、AIがこのリポジトリで記事・ページを作り、PRを出し、チェックが通ったらマージまで進める（`main` に入ると公開され、IndexNow で Bing などに更新が届く）。迷う内容（数字の出典がない、取り扱わない分野にかかる）は公開せず、Nori さんに聞く。
- 狙う語と優先順は `docs/seo-keywords.md`。作業したら `docs/seo-log.md` に1行残す。主な客は設計部門のない中小企業（10〜300人）。
- ガイド記事は `tools/guides.py` に書き、`python3 tools/seo_pages.py .` で `guide/`・`sitemap.xml`・`llms.txt` を作り直す（3つとも手で直さない）。規約などの共通の見た目は `tools/site_common.py`。新しい固定ページを作ったら `seo_pages.py` の `STATIC` に足す。
- 出す前に `python3 tools/seo_check.py .`（PRでも自動で動く）。title は32字前後でメインの語を前に、description は80〜120字、h1 は1つ、h2 にサブの語。
- 書き方：冒頭で一文で答える、「この記事の要点」、Q&A（FAQPage になる）、最後にトップへの誘導。料金・期間・制度の数字は公式の出典と確認日を書けるものだけ。実在企業の見積・口コミ・評価は作らない。競合は否定せず使い分けで書く。
- 取り扱わない分野（酒類・医薬品・医療機器）は記事にしない。サプリ・健康食品は効能を書かない。
- AI検索向け：`llms.txt` はガイドの要約つき一覧（自動）。AIのクローラーは止めない（`robots.txt`）。トップの本文は JS が動く前から読める静的な文（`tools/prod.py` の `static`）。
- IndexNow の鍵はルートの `<32桁>.txt`（公開してよい値。消さない）。全部送り直すときは Actions →「IndexNow」→ Run workflow。
- Search Console は shiokonbu.com のドメインプロパティで見られる（サブドメインの追加登録は不要）。

## 変更の出し方
- ブランチを作って PR で出す。`main` にマージすると本番にすぐ出る。
- PR のマージは AI がやってよい（Nori 2026-11-12「あなたがやって。今後も」）。チェックが通り、衝突がなく、画面を確かめてからマージする。
