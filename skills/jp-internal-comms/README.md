# 日本の社内文書（`jp-internal-comms`）

日報・週報（3P）・議事録・稟議書・社内通達・社内報・社内FAQ・障害報告を、日本の職場でそのまま出せる型で書きます。メモや箇条書きを渡すと本文と「要確認」の一覧を返します。

> 無料（Apache-2.0） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「今日の日報を書いて。午前は見積作成、午後は2社訪問」
- 「会議のメモから議事録を作って。決定事項とToDoを分けて」
- 「ノートPCを買うための稟議書の文面を作りたい」
- 「昨日の夕方にサイトが落ちた件の障害報告を上長向けに書いて」
- 「全社向けに、パスワード変更のお知らせを作って」

## 元との違い

anthropics/skills の `internal-comms`（Anthropic、Apache-2.0）を元に、次の点を変えました。元のリポジトリ: https://github.com/anthropics/skills （dbd4588 時点）

| 変えたこと | 内容 |
|---|---|
| 日本の文書の型 | 日報・週報・議事録・稟議書・社内通達・障害報告を追加。元は英語の3P・社内報・FAQ だけ |
| 日付 | 「来週水曜」「再来週の月曜」を曜日つきの日付に直す。曜日・営業日後・継続時間を計算する `scripts/jpdate.mjs` つき |
| 作り話の防止 | 素材に無い数値・担当者・原因・予算科目を作らず、本文に `【要確認】` と置いて末尾に一覧を付ける |
| 日本の書き方 | 税込・税抜の併記と検算、決裁欄は社内様式に従う、お詫びの順序、敬語の目安 |
| 本文の構成 | 本文57行（約1,200トークン）、型ごとの手順は `references/` に分割（読むのは1本） |

評価（2026-10-21、Claude Code のサブエージェント／sonnet で各3回。比較対象は元の `internal-comms`）: タスク達成 95%（元 69%）／ 発火の模擬判定 発火すべき依頼 10/10・すべきでない依頼 10/10（2回）／ 平均トークン 元の約1.1倍
元との差が大きかったのは議事録（48%→95%）と稟議書（48%→100%）で、来週・今週の日付の変換、金額の税込税抜と検算、担当者未定の扱いが主な違いです。日報は 86%→86%、社内通達は 93%→100% で差は小さいです。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-21 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: 追加で必要なものはありません。`scripts/jpdate.mjs`（日付の計算）は Node 18 以上があれば使えます。無くても、スキルは基準日から曜日を数える手順で動きます。

既知の制限:
- 祝日は、内閣府の祝日CSVを渡したときだけ営業日の計算に入ります（渡さなければ土日だけを休みとして計算し、出力にそう表示します）
- 社外向けの文書、法令上の報告義務（個人情報の漏えい等）の判断、会社ごとの決裁ルートは対象外です

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-internal-comms        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-internal-comms -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-internal-comms@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-internal-comms/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-internal-comms/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-internal-comms.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-internal-comms` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/jpdate.mjs`: 日付の曜日・「来週の水曜」・N営業日後・期間・継続時間を日本語の書式で出します。ファイルは読みません（`--holidays-file` で渡した祝日CSVだけ読みます）。何も書かず、外部への通信はありません。

## ライセンス・クレジット

Apache-2.0。anthropics/skills の `internal-comms`（Apache-2.0）を改変しています。元のライセンス全文を `LICENSE`、出典と改変の表示を `NOTICE` に残しています。

---

## English

Writes Japanese workplace documents — daily/weekly (3P) reports, meeting minutes, ringi approval requests, internal announcements, incident reports — from your notes. Adapted from `internal-comms` in anthropics/skills (dbd4588, Apache-2.0): added Japanese document formats, a date helper (`scripts/jpdate.mjs`) that turns "next Wednesday" into a weekday-correct date, and a rule to flag missing facts instead of inventing them. Verified in Claude Code (sonnet subagents, 2026-10-21); chat/API use via the single-file prompt is untested. Install: `npx skills add frametech971-png/skills --skill jp-internal-comms`
