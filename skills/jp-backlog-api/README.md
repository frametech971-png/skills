# Backlog API（課題の取得・登録・更新）（`jp-backlog-api`）

Backlog（ヌーラボ）の API v2 で、課題の取得・登録・更新・コメント・ステータス変更を行うコードを、公式仕様どおりに書きます。認証・件数制限・エラーの原因調べにも使えます。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「Backlog の課題を全件 CSV にして」
- 「課題を API で登録したい」
- 「APIキーの取り方と、権限エラーが出る」
- 「ステータスを一括で変えたい」
- 「スペースURLの形式（backlog.com と backlog.jp）はどっち？」

## 何が違うか

課題の登録に必要な `projectId`・`summary`・`issueTypeId`・`priorityId` と、それらの ID を調べる API（`meta` サブコマンドで一覧）、課題一覧は `count` の上限100で `offset` を進めること、スペース URL の形式、APIキー認証（OAuth 2.0 は手順のみ）を、Backlog の公式ドキュメントで確認した日付つきで `references/` に持っています。書き込み（登録・ステータス変更）は `--yes` を付けない限り送りません。貼られた API キーはコードに書き写さず、環境変数から読む形にします。

評価（2026-10-23、Claude Code のサブエージェント／sonnet で各3回。比較対象はスキルなし・Web 検索あり）: タスク達成 100%（スキルなし 94%）／ 発火の模擬判定 発火すべき依頼 12/12・すべきでない依頼 13/13（2回）

**差は小さいスキルです。** Backlog API は公開ドキュメントが整っており、スキルなしでも大きくは外れませんでした（退行なし）。スキルなしで外れやすかったのは、課題登録の必須パラメータと ID の調べ方、レート制限の数値を断定しないこと、貼られた鍵の扱いです。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: Python 3.9 以上（標準ライブラリだけ）。実際に通信するには、環境変数 `BACKLOG_SPACE`（スペース名）と `BACKLOG_API_KEY` が要ります。

既知の制限:
- 実際の Backlog スペースでの通信は未検証です。標準ライブラリのモックサーバーで、全件取得（count=100）、429 の再試行、CSV、書き込みの `--yes` 必須、途中失敗時の案内を32項目確認しています
- API キーの発行画面の手順、`offset` の上限、完了課題が既定で一覧に含まれるか、カスタム属性 `typeId` の意味、分あたりのレート制限値は、公式ページで確認できず「要確認」としています
- OAuth の認可フローはスクリプト化していません（アクセストークンを環境変数で渡す方式のみ）。`add` は文字列値の列のみで、添付は非対応です
- 参照資料の確認日は 2026-10-23。90日を過ぎたら公式を読み直してください

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-backlog-api        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-backlog-api -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-backlog-api@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-backlog-api/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-backlog-api/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-backlog-api.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-backlog-api` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/backlog_issues.py`: `fetch`（課題を全件取得して CSV/JSON）、`meta`（priorityId・statusId・issueTypeId・カスタム属性の ID を一覧）、`add`（課題を登録）、`set-status`（ステータス変更）。鍵はヘッダー `Backlog-API-Key` で送り、`--dry-run` では伏せ字で表示します。書き込みは `--yes` が無いと終了コード2で止まります。通信先は自分のスペースの `*.backlog.com` / `*.backlog.jp` だけです。
- `scripts/selftest_mock.py`: 上のスクリプトを標準ライブラリのモックサーバーで検査します。外部には通信しません。

## ライセンス・クレジット

MIT。
