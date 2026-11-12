# KATACHI サイトの GA4 計測

## 有効にする方法
`template.html`（= v2.html）の `GA_IDS` に測定IDを入れて再生成するだけ。
- ペットサイト（pet.shiokonbu.com）と同じく「サイト専用プロパティ」と「総合プロパティ」の両方に送れる（配列に2つ入れる）。総合側は hostName でサイトを絞る運用。
- claude.ai の試作版では外部スクリプトが読み込めないため、GA には届かない（`window.dataLayer` に積むだけ）。本番ドメインに置いたときに初めて送信される。
- ページビューは手動送信（`send_page_view:false`）。トップ `/` と結果 `/result` を仮想ページとして送る。
- デバッグ: ブラウザで `localStorage.setItem('katachi-ga-debug','1')` を実行すると、送ったイベントがコンソールに出る。

## イベント一覧（ペットサイトと同じ snake_case の命名）
共通パラメータ: `site_lang`（ja/en/zh）、`dataset`（real/demo）

| イベント | いつ | 主なパラメータ | キーイベント候補 |
|---|---|---|---|
| page_view | トップ・結果の表示 | page_path, page_title | |
| form_input_start | 入力欄に最初に文字を入れた | form | |
| form_cta | 「チームを組む」を押した | quantity, files, chars | ○ |
| form_error | 空のまま送信しようとした | reason | |
| example_click | 例のボタン | example | |
| filter_company | 絞り込み・並べ替えを変えた | filter, active_filters | |
| select_quantity | 試作/小ロット/量産 | quantity | |
| import_design | AI設計の取り込み | file_kind, file_ext / source | |
| view_team | 結果（チーム）を表示 | scenario, steps, companies, gaps | |
| select_plan | チーム案を切り替え | plan | |
| open_step | 工程を開いた | step_id | |
| swap_company | 担当会社を入れ替え | step_id, company_level, overseas | |
| select_tab | 表で比べる/作り方 | tab | |
| demo_toggle | 見積後の画面の切替 | on | |
| view_partners | 会社の詳細を開いた | company_level, overseas | |
| official_site | 出典・公式サイトのリンク | link_domain | |
| header_cta | 下部の相談/見積ボタン | cta, place | |
| open_inquiry | 見積依頼・相談の画面を開いた | type (rfq/consult), companies | |
| translate_preview | 依頼書の翻訳を確認 | | |
| generate_lead | 見積依頼・相談を送信 | type, companies, quantity, files, requester, optional_filled/optional_total, nda, overseas_ok | ◎（最重要） |
| lang_change | 言語切替 | from, to | |
| view_estimate | 概算の目安を表示（タブ・選択式・文章入力） | scenario | |
| estimate_qty | 概算の数量を変えた | qty_bucket (1-10/11-100/101-1000/1001+) | |

ペットサイトはキーイベントが0件のまま（2026-11-11時点のGA4レポート）。KATACHIでは最初から `generate_lead` をキーイベントに設定することを推奨。

## 送らないもの
入力文・会社名・ファイル名などの中身は送らない（個人情報や未公開アイデアを含みうるため）。種類・件数・文字数だけを送る。
