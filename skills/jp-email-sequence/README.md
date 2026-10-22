# ステップメール設計（日本向け）（`jp-email-sequence`）

ウェルカム・育成・休眠顧客の掘り起こし・購入後などのステップメールを、流れの設計から件名・本文まで作ります。日本の受信者に送るときは、特定電子メール法（送ってよい相手、同意の記録、配信停止、フッターの表示義務）を各メールに反映します。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「無料体験に登録した人へのウェルカムメールを3通作って」
- 「休眠顧客の掘り起こしメールを3通書いて」
- 「展示会で名刺交換した相手に案内メールを送っていい？」
- 「メルマガの同意の記録はどれくらい保存すればいい？」

## 元との違い

marketingskills の `emails`（Corey Haines、MIT）を元に、次の点を変えました。元のリポジトリ: https://github.com/coreyhaines31/marketingskills（1efedbc 時点）。シーケンス設計の考え方と参照資料は元のままです。

| 変えたこと | 内容 |
|---|---|
| 日本の法令 | 特定電子メール法の送ってよい相手（法第3条）、同意記録の保存（最後の送信から1か月、施行規則第4条）、配信停止と取引通知の例外（施行規則第6条）、フッターの表示事項（法第4条・施行規則第9条）、罰則。景品表示法から、期限・順位・比較価格は事実のときだけ書く規則。条文は e-Gov で確認（2026-10-12） |
| 発火 | 日本語の発話例と、対象外（名簿を買っての一斉配信、SMS・LINE、アプリ内オンボーディング）を description に |
| 単体で使える形に | 元のリポジトリの別スキルへの参照と、エージェント固有のパスを外した |

評価（2026-10-12、Claude Code ／ claude-opus-5-5 で6問を各3回）: タスク達成 99%（元 77%）。元のスキルは、配信停止した人への注文確認メールに広告を載せる問題で「載せてはいけない」と条文と逆の答えをした回が3回中2回、同意記録の保存期間の起算点を取り違えた回が3回中2回ありました。
発火の模擬判定: 発火すべき依頼 20/20・すべきでない依頼 20/20（2回）

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code（VS Code 拡張）／ claude-opus-5-5 | 2026-10-12 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。法令の記述は確認日時点のもので、法的な結論は断定しません。

追加で必要なものはありません。

## インストール

```bash
npx skills add frametech971-png/skills --skill jp-email-sequence        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-email-sequence -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**: `/plugin marketplace add frametech971-png/skills` → `/plugin install jp-email-sequence@frametech-skills`

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-email-sequence/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-email-sequence/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う**: `prompts/jp-email-sequence.prompt.md` を知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。

## このスキルが実行すること

スクリプトはありません。メールを実際に送信することもありません（設計と文面の作成だけ）。本文中の配信ツールの表は、元のリポジトリの説明ページ（github.com）へのリンクです。

## ライセンス・クレジット

MIT。marketingskills © 2025 Corey Haines（MIT）を改変しています。元の著作権表示は LICENSE に残しています。

---

## English

Email sequence design (welcome, nurture, re-engagement, post-purchase) modified from coreyhaines31/marketingskills `emails`, with a Japan layer: Japan's Act on Specified Electronic Mail (who you may email, consent records, opt-out and the transactional exception, mandatory footer items, penalties) and truthful urgency/pricing claims under the Premiums and Representations Act. Verified with Claude Code (claude-opus-5-5). Install: `npx skills add frametech971-png/skills --skill jp-email-sequence`
