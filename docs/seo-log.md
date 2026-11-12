# SEO の作業メモ（新しい順）

効果の判定は変更から14日以上たってから（28日が理想）。Search Console は shiokonbu.com のドメインプロパティ（sc-domain:shiokonbu.com）で katachi.shiokonbu.com も見られる。

## 2026-11-12
- 記事：/guide/3d-print-request/（狙う語「3Dプリンター 依頼」月1,000〜1万、副「3Dプリント 外注／代行」「3Dプリンター 試作」「3Dプリンター 依頼 個人」各月100〜1,000、競合「高」）。根拠はキーワードプランナー（DMM.make 3Dプリント起点）。
- キーワードプランナー3回目（DMM.make 3Dプリント・Protolabs Network・Fictiv起点）：DMMは日本語で3Dプリント依頼の語がまとまって多い。後の2つは英語のみ。CSVはプロジェクトファイル katachi-seo/keyword-planner/。
- 記事：/guide/no-drawing/（狙う語「図面 加工」月100〜1,000、副「板金 図面」月100〜1,000、「板金 曲げ 図面 書き方」月100〜1,000）。根拠はキーワードプランナー（Kabuku Connect 起点、2025/11〜2026/10）。
- キーワードプランナー2回目（プラッとものづくり・Kabuku Connect・Xometry起点）：依頼系は小さい（板金 見積・工場 おすすめ・ものづくり 会社 が月100〜1,000、ものづくり 依頼・工場 依頼・試作 制作 は月10〜100）。Xometry は英語のみ。
- 記事：/guide/find-manufacturer/（狙う語「製造委託先 探し方」、副「OEM 委託先 探し方」「工場 探し方」）。数字なし。
- キーワードプランナー（Nori共有、エミダス・ミスミ起点、2025/11〜2026/10）：技術用語と部品名がほとんどで、試作・OEM・外注・小ロットを含む語はゼロ。KATACHIの語は seed-keywords（プロジェクトファイル katachi-seo/keyword-planner/）で取り直しを依頼中。
- 記事：/guide/what-gets-ordered/（狙う語「試作 依頼 事例」、副「部品加工 依頼 多い」「製造委託 事例」）。Nori「どんなものが実際にオーダーされているのかの濃い記事」。数字は Protolabs 2025年決算・Xometry 2025年決算・Xometry 2027 Outlook・九都県市合同商談会2025 発注案件一覧（2026-11-12 確認）。
- 土台を追加：ガイド記事のしくみ（tools/guides.py → tools/seo_pages.py）、sitemap・llms.txt の自動生成、構造化データ（Organization・FAQPage・Article・BreadcrumbList）、IndexNow、PRごとのSEOチェック。robots.txt で tools/backend/docs を除外。
- 1本目の記事：/guide/prototype-outsourcing/（狙う語「試作 外注」、副「図面なし 試作」「自社製品 開発 外注」）。
- 公開時点で katachi.shiokonbu.com/ は Google に未認識（URL検査「URL が Google に認識されていません」）。
- 2026-11-12 /guide/3d-print-request/ に「どんな企業が何に使っているか」を追記（Protolabs 3DP Trend Report 2024・MONOist 2024年7月調査）。Nori依頼。
- 2026-11-12 seed語でキーワードプランナー（3シート）。実需は「◯◯ OEM 小ロット」に集中 → 計画を並べ替え。記事6本目 /guide/small-lot-oem/（狙う語「OEM 小ロット」）。
