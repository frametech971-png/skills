# kintone REST API（レコードの取得・登録・更新）（`jp-kintone-api`）

kintone のレコードを REST API で読み書きするコードを、公式仕様どおりに書きます。クエリ構文、件数の上限、認証、エラーの原因調べにも使えます。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「kintone のレコードを全件取得するスクリプトを書いて」
- 「クエリ文字列の書き方（条件・並び替え・limit/offset）を教えて」
- 「500件の上限を超えて取りたい」
- 「APIトークンの権限エラーが出る」
- 「CSV の内容を kintone に一括登録して」

## 何が違うか

取得は1回500件まで、登録は1回100件まで、`offset` には上限があるので、全件取得はカーソルAPIで行います。このスキルはその使い分け、サブドメイン形式の URL、`X-Cybozu-API-Token` による認証、クエリの書き方を、cybozu.dev の公式ドキュメントで確認した日付つきで `references/` に持っています。公式で確認できなかったこと（エラーコードの一覧、秒間のリクエスト数）は断定せず、「公式で確認できない」と答えます。貼られた API トークンはコードに書き写さず、環境変数から読む形にします。

評価（2026-10-22、Claude Code のサブエージェント／sonnet で各3回。比較対象はスキルなし・Web 検索あり）: タスク達成 97%（スキルなし 85%）／ 発火の模擬判定 発火すべき依頼 11/11・すべきでない依頼 12/12（2回）
スキルなしで外れやすかったのは、URL のサブドメイン形式、公式で未確認の情報を断定しないこと、秒間の制限は記載が無いと正直に言うことです。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: Python 3.9 以上（標準ライブラリだけ）。実際に通信するには、環境変数 `KINTONE_SUBDOMAIN`・`KINTONE_APP_ID`・`KINTONE_API_TOKEN`（アプリの API トークン）が要ります。

既知の制限:
- 実際の kintone 環境での通信は、作者の手元に環境が無く未検証です。標準ライブラリで作ったモックサーバーに対して、ページング・カーソルの削除・429 の再試行・CSV の一括登録などを34項目確認しています
- エラーコードの公式一覧は見つからず、`CB_IJ01` 以外はコミュニティの報告として区別しています
- 1日のリクエスト数は公式ページ間で書き方が違うため「契約で要確認」としています
- cybozu.com 以外のドメイン、基本認証、クライアント証明書、OAuth は対象外です
- 参照資料の確認日は 2026-10-21。90日を過ぎたら公式を読み直してください

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-kintone-api        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-kintone-api -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-kintone-api@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-kintone-api/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-kintone-api/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-kintone-api.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-kintone-api` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/kintone_records.py`: 環境変数のサブドメイン・アプリID・API トークンで kintone に接続します。`fetch` はカーソルAPIで全件を取得して CSV か JSON に出力します（取り切れなかったときや途中で失敗したときはカーソルを削除します）。`add` は CSV を100件ずつ登録しますが、`--yes` を付けない限り送りません。`--dry-run` では通信せず、トークンを伏せ字にして送る内容を表示します。通信先は自分の `<サブドメイン>.cybozu.com` だけです。
- `scripts/selftest_mock.py`: 上のスクリプトを標準ライブラリのモックサーバーで検査します。外部には通信しません。

## ライセンス・クレジット

MIT。
