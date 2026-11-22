# どのAIでも同じ作業をするための手順（Claude・ChatGPT・Gemini・Muse）

KATACHI（katachi.shiokonbu.com） の作業を、どのAIが受けても同じ決まりで進めるための入口です。全サービス共通の指示書は pet-lp の `docs/ai/` と同じ考え方です。

## 1. 作業の前に読む（この順）

1. `AGENTS.md`（このリポジトリの全部の決まり）。
2. 非公開のリポジトリ `NORI-silver/katachi-data` の `docs/ai-memory/MEMORY.md`（Nori さんの方針と進行中のこと。まだなければ飛ばす）
3. `docs/ai/handoff.md`（ほかのAIの直近の引き継ぎ）。
4. GitHub の開いているPRと最近のコミット（同じところを二重に直さないため）。

ほかのAIの会話は自動では伝わりません。共有されるのは GitHub に残したもの（PR・この引き継ぎメモ・非公開のリポジトリ）だけです。

## 2. 作業のしかた

- 変更はブランチを作ってPR。ブランチ名はAIごとに分ける：`claude/…`・`chatgpt/…`・`codex/…`・`gemini/…`・`muse/…`。`main` に直接書かない。マージは `AGENTS.md` の決まりどおり。
- ページを生成・点検する手順は `AGENTS.md` のとおり。コードを動かせないAI（チャットだけの ChatGPT・Gemini・Muse）は、生成したファイルを手で直さず「生成と点検はまだです」とPRに書き、Codex・Jules・Claude に回す。
- 報告は Nori さんがやることを先に、短く、日本語でやさしく。

## 3. してはいけないこと

- 秘密（トークン・APIキー・パスワード・シートID・個人のメールアドレス・電話番号）をリポジトリ・PR・チャットに書かない。
- お金のかかる設定・購入をしない。外部への送信と、元に戻せないことは Nori さんの「やって」のあと。

## 4. 終わるとき

- `docs/ai/handoff.md` のいちばん上に1行足す。
- Nori さんに新しい決まりを言われたら `AGENTS.md` に足す。
