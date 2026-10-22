# freee 会計 API（取引の取得・登録と認証）（`jp-freee-api`）

freee 会計の API（OAuth2 認証、事業所ID、取引・勘定科目・取引先）を使うコードを、公式仕様どおりに書きます。取引を期間指定で取得して CSV にする、トークンの更新、認証やエラーの原因調べにも使えます。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「freee の取引を月別に取得して CSV にして」
- 「freee API のアクセストークンの取り方と更新のしかた」
- 「company_id がわからない」
- 「取引を API で登録したい」
- 「401 や 403 が出る。リクエストが多すぎると言われる」

## 何が違うか

アクセストークンは6時間、リフレッシュトークンは90日で、**リフレッシュトークンは1回しか使えません**（更新のたびに新しいものを保存します）。取引の取得は `limit` の最大が100で、`offset` と `meta.total_count` で進めます。通常の制限超過は 403（約10分で解除）で、429 が出るのは `/reports` と証憑ダウンロードだけです。1日の上限はプランで違います。このスキルはこれらを freee の公式ドキュメントで確認した日付つきで `references/` に持っています。貼られたトークンはコードに書き写さず、環境変数から読む形にして、無効化（revoke）して取り直すよう伝えます。勘定科目や税区分の判断はせず、会計担当者・税理士の確認を勧めます。

評価（2026-10-22、Claude Code のサブエージェント／sonnet で各3回。比較対象はスキルなし・Web 検索あり）: タスク達成 98%（スキルなし 72%）／ 発火の模擬判定 発火すべき依頼 12/12・すべきでない依頼 13/13（2回）
スキルなしで外れやすかったのは、`limit` の最大100とページング、勘定科目・税区分を勝手に決めないこと、リフレッシュトークンが1回限りであること、制限超過の応答（403 と 429 の違い）です。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: Python 3.9 以上（標準ライブラリだけ）。実際に通信するには freee のアプリ登録と、環境変数 `FREEE_ACCESS_TOKEN`・`FREEE_COMPANY_ID` が要ります。

既知の制限:
- freee の実アカウントでの通信は、作者の手元に環境が無く未検証です。標準ライブラリのモックサーバーに対して、3ページのページ送り、500行のCSV、429 の再試行、401/403、上書き拒否などを25項目確認しています
- 認可コードの有効期限は公式で数値を確認できず「要確認」としています。1日の上限を超えたときの応答形式も同様です
- スクリプトはトークンの更新（リフレッシュ）をしません。Client Secret を扱うため、更新の手順は `references/auth.md` に置いています
- 参照資料の確認日は 2026-10-22。90日を過ぎたら公式を読み直してください

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-freee-api        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-freee-api -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-freee-api@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-freee-api/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-freee-api/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-freee-api.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-freee-api` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/freee_deals.py`: 環境変数のアクセストークンと事業所IDで、freee の取引を期間指定で全ページ取得し、CSV か JSON に出力します。`--dry-run` では通信せず、トークンを伏せ字にして送る内容を表示します。既存のファイルは上書きせず、通信先は api.freee.co.jp だけです（外部の http URL は拒否します）。429 のときは待って再試行します。

## ライセンス・クレジット

MIT。
