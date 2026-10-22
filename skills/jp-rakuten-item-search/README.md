# 楽天市場の商品検索（2026年版API）（`jp-rakuten-item-search`）

楽天市場の商品を、2026年版の楽天ウェブサービス商品検索APIで探し、商品名・価格・ショップ・レビュー・リンクの一覧にします。楽天APIを使うコードの作成、旧APIからの移行、`Invalid Access Key` などのエラーの原因調べにも使えます。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「楽天でモバイルバッテリーを探して、レビューの多い順に10件並べて」
- 「この商品リストの楽天アフィリエイトリンクをまとめて取って」
- 「楽天APIが403で Invalid Access Key と出る。直して」
- 「旧楽天APIのコードを新しいAPIに移行して」

## 何が違うか

楽天の商品検索APIは2026年に仕様が変わり、エンドポイント（`openapi.rakuten.co.jp/.../20260701`）、アクセスキー（`accessKey`）、Referer が必要になりました。ネット上の記事や既存のコードの多くは旧APIのままです。このスキルは新しい仕様（公式ドキュメント、2026-10-10 確認）を持っていて、鍵は環境変数から読み、貼られた鍵をコードに書き写しません。

評価（2026-10-10、Claude Code ／ claude-opus-5-5 で各3回。比較対象はスキルなし・Web 検索あり）: タスク達成 100%（スキルなし 88%）／ 発火の模擬判定 発火すべき依頼 20/20・すべきでない依頼 20/20（2回）
スキルなしでは、貼られたアクセスキーをそのまま書き写した回が3回中2回、旧APIのコードを新エンドポイントへ直せなかった回が3回中2回ありました。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code（VS Code 拡張）／ claude-opus-5-5 | 2026-10-10 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: 楽天ウェブサービスのアプリ登録（無料）と、環境変数 `RAKUTEN_APP_ID`・`RAKUTEN_ACCESS_KEY`・`RAKUTEN_REFERER`（アプリ登録の「アプリケーションURL」と同じ値）。任意で `RAKUTEN_AFFILIATE_ID`。検索スクリプトは Python 3.9 以上（標準ライブラリだけ）。

既知の制限:
- 正しい鍵で商品が返る経路は、作者の手元では鍵が無く未確認です（鍵が違うときの 403 は実際のAPIで確認済み）
- Referer の要件は公式ドキュメントの本文には書かれていません。実際に動いている実装と開発者の報告に基づいています

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-rakuten-item-search        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-rakuten-item-search -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-rakuten-item-search@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-rakuten-item-search/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-rakuten-item-search/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-rakuten-item-search.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-rakuten-item-search` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/rakuten_search.py`: 環境変数からアプリID・アクセスキー・Referer を読み、`https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701` へ GET を送ります（1件ごとに1.1秒空ける）。結果を標準出力に表・JSON・CSV で出すだけで、ファイルは書きません。`--dry-run` では送らずに、送る URL（鍵は伏せ字）を出します。通信先は openapi.rakuten.co.jp だけです。

## ライセンス・クレジット

MIT。

---

## English

Searches Rakuten Ichiba products with the 2026 Rakuten Web Service Item Search API (`openapi.rakuten.co.jp`, `applicationId` + `accessKey` + `Referer`) and returns a table/JSON/CSV; also writes, migrates, and debugs code for the new API. Verified with Claude Code (claude-opus-5-5); works in any Agent Skills–compatible agent, and a single-file prompt version is included for chat apps and APIs. Install: `npx skills add frametech971-png/skills --skill jp-rakuten-item-search`
