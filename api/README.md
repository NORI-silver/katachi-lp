# KATACHI API（AIエージェント向けの入口・Gateway、HTTP ＋ MCP）

**Gateway の方針**（Nori 2026-11-14「ウォルマートみたいにGatewayつくるか」「一緒にすすめて」）：AIに渡すのは「KATACHIに来たくなる材料」まで。製品は工程と法規制、会社は候補の社数と上位3社の名前・理由、仕様書は点数・足りない項目・質問まで。会社の連絡先・条件・出典、工場向け仕様書の本文、工場への質問、概算、組み合わせ案、提携の状況は渡さず、どの答えも入力を引き継いだKATACHIのページ（`katachi_url`、`?q=&qty=&from=<AI名>`）で締める。どのAIが何を聞いたかは受付の「入力ログ」（入口=api、補足に AI名とツール）に残す（メール・電話は伏せる）。

作りたいものを工場に頼める形に整え、注文できる会社を探すAPI。Cloudflare Workers（無料プラン）で動く。
同じ機能を HTTP（`/v1/...`）と MCP（`/mcp`、Streamable HTTP・状態なし）で出す。有料AIは使わない。

| 機能 | HTTP | MCPツール |
|---|---|---|
| 製品を調べる（製品仕様DB 約2.6万品目→工程・部品・素材・最小ロット・法規制、出典つき） | `GET /v1/products?q=` / `GET /v1/products/{id}` | `lookup_product` |
| 工程の一覧 | `GET /v1/processes` | `list_processes` |
| 会社を探す（注文できる会社だけ。1回10社・上位30社まで） | `GET /v1/companies?product=&process=&q=&area=` | `search_companies` |
| 仕様書の形（`data/fspec.json`） | `GET /v1/spec/schema` | `get_spec_schema` |
| 仕様書を検査する（抜け・矛盾・根拠なし・工場に出せる度） | `POST /v1/spec/check` | `check_spec` |
| 依頼を送る（受付 Apps Script へ。1IP1日3件・全体1日50件まで） | `POST /v1/requests` | `send_request` |

OpenAPI: `/openapi.json`（ChatGPT の GPTs Actions などに読み込める）。

## サイトと同じ結果にする
- 製品の当て方は `tools/template.html` の `pdbRx〜pdbMatch` を `node api/build.mjs` で取り出して使う（写さない）。
- 会社はサイトの `canOrder` と同じ条件（日本の会社と、日本へ発送できると確かめた海外の会社。1688等は出さない）。
- 仕様書の形・工場に出せる度は `data/fspec.json` とサイトの `fsBuild`・`sxCheck` と同じ決まり（引用が原文に無い・値の数字が引用に無い→要確認、必須項目の確かさの平均×100、75以上で見積に出せる、設計からの依頼や形のある品目で図面・3D・現物が無ければ「設計から頼む」）。
- 提携しやすさの段階など社内の情報は出さない（`data/companies.json` に入っていない）。

## 守り
- 一覧の取得はできない（工程・製品名・キーワードのどれかが必須）。1回10件、上位30件まで。製品の似た候補も10件まで。
- IPごとに 1分30回（検査・送信は1分10回）。Workers Rate Limiting と isolate 内の数え上げ。違反が5分で20回続いたIPは10分遮断。`DENY_IPS`（カンマ区切り）で固定の遮断も可。
- 本文64KBまで、JSON-RPCはバッチ不可、扱わない分野（酒類・医薬品・医療機器・武器など）は 422。
- 依頼送信は利用者の同意（`agree_privacy: true`）が必須、CORSを付けない（他サイトのブラウザから送らせない）。受付シートには「受付の経路: KATACHI API」と入る。工場への自動送信はしない。
- ログ（Workers Logs）は IP をハッシュにし、入力本文は残さない。
- エッジの守り（DDoS・ボット）は Cloudflare 側の標準のもの。独自ドメインにするときは `../` の katachi-mcp の deploy/cloudflare-waf.md の WAF 設定も足す。
- 注意：サイト自体が `data/companies.json`・`data/products.json` をブラウザで読み込む作りなので、APIの件数制限だけではDBの丸ごと取得は防げない（リポジトリも公開）。守るならサイトを API 経由の検索に切り替え、DBを非公開の置き場所に移す必要がある。

## 開発
```bash
node api/build.mjs && node api/test/test.mjs    # テスト（受付とキャッシュは差し替え）
cd api && npx wrangler dev                        # 手元で動かす
```
main に入ると GitHub Actions（`.github/workflows/api.yml`）がテストして公開する（Secrets に CLOUDFLARE_API_TOKEN と CLOUDFLARE_ACCOUNT_ID が要る）。
