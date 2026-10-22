# LINE Messaging API（Bot・通知）（`jp-line-messaging-api`）

LINE公式アカウントの Messaging API で、Webhook を受けて返信・通知する実装を公式仕様どおりに書き、署名検証が合わないなどの原因を絞ります。LINE Notify の代わりの通知、送れる通数と料金プランの質問にも使えます。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「LINE Bot の Webhook を受けて返信するコードを書いて」
- 「x-line-signature の検証が合わない。直して」
- 「reply と push の違い、replyToken の期限は？」
- 「LINE Notify の代わりに通知を送りたい」
- 「LINE公式アカウントで無料で送れる通数は？」

## 何が違うか

署名はチャネルシークレットで HMAC-SHA256 を Base64 にし、**パース前の生のボディ**で検証します。フレームワークがボディを JSON にしてから検証して失敗する例が多いので、手元で原因を切り分ける `--diagnose` つきの検証スクリプトを同梱しています。仕様の数値（1回の送信は最大5件、テキスト5,000文字、replyToken は1回限りで約1分以内など）は LINE Developers の公式ドキュメントで確認した日付つきで `references/` にあります。LINE Notify は 2025-03-31 に終了しており、代わりは Messaging API です。料金プランは変わるので、公式で再確認するよう案内します。

評価（2026-10-22、Claude Code のサブエージェント／sonnet で各3回。比較対象はスキルなし・Web 検索あり）: タスク達成 93%（スキルなし 79%）／ 発火の模擬判定 発火すべき依頼 12/12・すべきでない依頼 12/12（2回）
差が大きかったのは、貼られたチャネルシークレット・アクセストークンをコードに書き写さないこと、署名検証の落とし穴（生のボディ）、LINE Notify 終了後の代替の案内です。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: Python 3.9 以上（標準ライブラリだけ）。実際に送るには自分の LINE チャネルのアクセストークン（環境変数 `LINE_CHANNEL_ACCESS_TOKEN`）が要ります。署名検証は外部通信なしで動きます。

既知の制限:
- LINE 本番との実通信（Webhook の受信、reply/push の成功）は、作者の手元に実アカウントが無く未検証です。署名検証は公式ドキュメントのテストベクトルと一致することを確認済みです
- 追加メッセージの単価表は公式ページが画像のため、金額を断定せず公式を見るよう案内します
- 参照資料の確認日は 2026-10-21。90日を過ぎたら公式を読み直してください

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-line-messaging-api        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-line-messaging-api -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-line-messaging-api@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-line-messaging-api/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-line-messaging-api/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-line-messaging-api.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-line-messaging-api` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/line_verify_signature.py`: 受け取ったボディとヘッダーの署名を、チャネルシークレットで検証します（`--self-test`、原因を切り分ける `--diagnose` つき）。外部への通信はなく、ファイルも書きません。
- `scripts/line_send.py`: 環境変数のアクセストークンで reply/push を送ります。`--dry-run` ではトークンを伏せ字にして送る内容だけを表示し、実際に送るには `--yes` が必要です。通信先は api.line.me だけです。

## ライセンス・クレジット

MIT。
