# 国税庁 法人番号・適格請求書の Web-API（`jp-nta-corporate-api`）

国税庁の法人番号公表サイトの Web-API（法人名・番号での検索、差分取得）と、適格請求書発行事業者公表システムの Web-API（登録番号での照会）を使うコードを書き、エラーの原因を調べます。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「法人番号から会社名を取得するコードを書いて」
- 「適格請求書の登録番号が有効か API で調べたい」
- 「アプリケーションIDの取り方を教えて」
- 「差分データの取り方は？」
- 「法人名で検索したら件数が多すぎる（分割取得）」

## 何が違うか

アプリケーションIDの届出・取得の手続、エンドポイントとバージョン、応答の形式（XML/CSV と文字コード）、1回に取れる件数と分割取得、差分取得、利用規約と出典表示、エラーコードを、国税庁の公式資料（PDF 仕様書）で確認した日付つきで `references/` に持っています。法人番号の検査桁の検証は `jp-invoice-check` の領域なので含めず、API の照会に絞っています。

評価（2026-10-23、Claude Code のサブエージェント／sonnet で各3回。比較対象はスキルなし・Web 検索あり）: タスク達成 98%（スキルなし 74%）／ 発火の模擬判定 発火すべき依頼 12/12・すべきでない依頼 13/13（2回）

スキルなしで外れやすかったのは、2つの API（法人番号とインボイス）でアプリケーションIDが別であること、応答の形式と件数上限、エラーコード、利用規約の細部でした。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: 国税庁に届け出て取得するアプリケーションID（法人番号用は `NTA_HOUJIN_APP_ID`、インボイス用は `NTA_INVOICE_APP_ID`。環境変数）。スクリプトは Python 3.9 以上（標準ライブラリだけ）です。

既知の制限:
- 有効なアプリケーションIDでの実通信は未検証です。実サーバーでは、無効なIDで両ホストが HTTP 404 を返すことだけ確認しました。モックでの確認と、公式仕様書との突き合わせまでです
- エラー応答の CSV 本文の列の並びは仕様書に図が無く未確認です（スクリプトは本文から該当コードの数字を拾います）
- インボイス Web-API の利用規約はページの要約での確認で、原文の逐語確認は未了です
- 名称検索のエラー112のメッセージは、公式の表と条件表で食い違っています（条件表に従いました）
- 参照資料の確認日は 2026-10-23。90日を過ぎたら公式を読み直してください

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-nta-corporate-api        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-nta-corporate-api -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-nta-corporate-api@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-nta-corporate-api/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-nta-corporate-api/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-nta-corporate-api.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-nta-corporate-api` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/nta_lookup.py`: `houjin-num`・`houjin-name`・`houjin-diff`・`invoice-num`・`invoice-valid`・`invoice-diff` の6つ。`--all` で分割取得し、`--dry-run` ではアプリケーションIDを伏せて送る内容を表示します。通信先は国税庁の2つのホストだけです。
- `scripts/selftest_mock.py`: 上のスクリプトを標準ライブラリのモックサーバーで検査します。外部には通信しません。

## ライセンス・クレジット

MIT。
