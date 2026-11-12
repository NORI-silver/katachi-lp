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
- アクセス解析（GA4）は `G-ZYX17VBTWB`（shiokonbu.com 総合、プロパティ 292677591、全サブドメイン共通。消さない）。KATACHI単体のIDができたら `tools/prod.py` の `GA` に足す。入力文・会社名・ファイル名など中身は送らない。イベント一覧は `tools/analytics.md`。
- 見積の依頼・相談の受付は Apps Script（`backend/forms.gs`）。**リポジトリにあっても本番には自動で反映されない**。直したら Apps Script に貼り直して「デプロイを管理」→ 同じデプロイの新しいバージョン、と Nori さんに伝える。受付URLは `tools/prod.py` の第3引数で入れる。
- 秘密情報（トークン・APIキー・個人のメールアドレス・シートID）をコミットしない。リポジトリは公開。
- 利用規約・プライバシーポリシーは `tools/legal.py` から作る。外部送信先を増やしたら、プライバシーポリシーの「5. 外部送信」にも足す。

## 変更の出し方
- ブランチを作って PR で出す。`main` にマージすると本番にすぐ出る。
