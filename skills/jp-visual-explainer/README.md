# 日本語の図解ページ（`jp-visual-explainer`）

仕組み・業務フロー・設計・数字を、日本語の図解ページ（1ファイルの HTML。手描きの SVG 図・比較・KPI・スライド）にします。和文の組版（`lang="ja"`、和文フォント、行長、禁則、見出しの字間）を守ります。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「経費精算の承認フローを1枚の図解ページにして」
- 「ログインの仕組みを新人向けに図解して」
- 「今月のKPIをダッシュボード風のページにまとめて」
- 「情報セキュリティのルールを日本語のスライド3枚にして（HTMLで）」

## 元との違い

visual-explainer（Nico Bailon、MIT）を元に、次の点を変えました。元のリポジトリ: https://github.com/nicobailon/visual-explainer（0cc6f15 時点）

| 変えたこと | 内容 |
|---|---|
| 日本語化 | 和文組版の規則を追加（行長30〜40字、行送り1.7〜1.9、見出しの字間0、斜体を使わない、`line-break: strict`、`word-break: auto-phrase`、「図1」表記、SVG ラベルは1行9〜10字）。出典つき |
| テンプレート | `lang="ja"`、Noto Sans JP の読み込み、和文フォントを含むフォントの並び、`:lang(ja)` の上書きを追加 |
| 発火 | 日本語の発話例と、対象外（PowerPoint ファイル・画像生成・印刷用 DTP）を description に |
| 範囲を絞った | npm が要る動画（MP4）・PPTX 書き出し・MCP・プランのツールを外し、1ファイルの HTML 作成に絞った |

評価（2026-10-10、Claude Code ／ claude-opus-5-5 で5問を各3回）: タスク達成 100%（元 88%）。日本語の慣習として入れた「図1」表記の項目を除くと 100%（元 91%）。元のスキルは、日本語の見出しに負の字間を付けた回が3回中3回、和文の改行規則が無い回が3回中1回ありました。
発火の模擬判定: 発火すべき依頼 20/20・すべきでない依頼 20/20（2回）

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code（VS Code 拡張）／ claude-opus-5-5 | 2026-10-10 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: 生成した HTML を開くブラウザ。フォントは Google Fonts から読みます（オフラインでは OS の和文フォントで表示）。評価ではページをブラウザで描画しての見た目の確認はしていません（HTML・CSS の指定を機械的に確認）。

## インストール

```bash
npx skills add frametech971-png/skills --skill jp-visual-explainer        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-visual-explainer -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**: `/plugin marketplace add frametech971-png/skills` → `/plugin install jp-visual-explainer@frametech-skills`

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-visual-explainer/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-visual-explainer/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う**: `prompts/jp-visual-explainer.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。`npx skills use frametech971-png/skills@jp-visual-explainer` でも同じプロンプトが出ます。

## このスキルが実行すること

スクリプトはありません。エージェントが HTML ファイルを書くだけです。生成したページは開いたときに Google Fonts（fonts.googleapis.com / fonts.gstatic.com）からフォントを読み、必要なときだけ CDN（Chart.js・three.js）を読みます。スライドのテンプレートは、表示中のスライド番号をブラウザの localStorage に保存します。

## ライセンス・クレジット

MIT。visual-explainer © 2025 Nico Bailon（MIT）を改変しています。元の著作権表示は LICENSE に残しています。

---

## English

Japanese-typeset visual explainer pages (single-file HTML with hand-drawn SVG, KPIs, comparisons, slides), modified from nicobailon/visual-explainer: adds Japanese typography rules (lang="ja", Japanese web fonts, measure in em, no negative tracking, strict line breaking, 図N labels) and Japanese-ready templates; video/PPTX/MCP tooling removed. Verified with Claude Code (claude-opus-5-5). Install: `npx skills add frametech971-png/skills --skill jp-visual-explainer`
