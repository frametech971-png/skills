# frametech skills

日本語で使えるエージェントスキル集です。[Agent Skills](https://agentskills.io) 形式（`SKILL.md`）なので、対応するエージェントにそのまま入れられます。読み込みの仕組みが無いチャットや API では、`prompts/` の貼り付け版（1ファイル）を使います。

## スキル一覧

| スキル | できること | ライセンス | 版 |
|---|---|---|---|
| [`jp-internal-comms`](skills/jp-internal-comms) | 日本の職場で使う社内文書（日報・週報・3P報告・議事録・稟議書・社内通達・社内報・障害報告とお詫び・社内FAQ）を、型に沿って書く。 | Apache-2.0 | v1.0.0 |
| [`jp-rakuten-item-search`](skills/jp-rakuten-item-search) | 楽天市場の商品を、2026年版の楽天ウェブサービス商品検索API（openapi.rakuten.co.jp、applicationId＋accessKey＋Referer）で検索し、商品名・価格・ショップ・レビュー・商品URL／アフィリエイトURLを表・JSON・CSVで返す。 | MIT | v1.0.0 |
| [`jp-visual-explainer`](skills/jp-visual-explainer) | 仕組み・業務フロー・設計・コードの変更・計画・数字を、日本語の図解ページ（1ファイルの HTML。 | MIT | v1.0.0 |
| [`jp-web-security-audit`](skills/jp-web-security-audit) | コード・API・サービスのセキュリティを、防御側の立場でソースから監査する。 | MIT | v1.0.0 |
| [`jp-email-sequence`](skills/jp-email-sequence) | ウェルカム・育成・再エンゲージメント・購入後などのステップメール（メールシーケンス、ドリップ、ライフサイクルメール）を設計して文面まで作る。 | MIT | v1.0.0 |
| [`jp-line-messaging-api`](skills/jp-line-messaging-api) | LINE公式アカウントの Messaging API を使う Bot・通知のコードを書き、Webhook の署名検証・reply/push・メッセージ上限・エラー・料金プランの原因を調べる。 | MIT | v1.0.0 |

各スキルのフォルダに、使い方・元との違い・評価の数字・動作確認の範囲を書いた README があります。評価セットは `evals/<name>/` にあり、誰でも再現できます。

## インストール

```bash
npx skills add frametech971-png/skills --skill <name>        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill <name> -g     # すべてのプロジェクトで
```

Claude Code のプラグインとして:

```
/plugin marketplace add frametech971-png/skills
/plugin install <name>@frametech-skills
```

手で置く場合は、`skills/<name>/` のフォルダごと、Claude Code はプロジェクトの `.claude/skills/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode などは `.agents/skills/` に置きます。

## 動作確認について

実機で確かめたのは Claude Code（サブエージェント）だけです。それ以外の環境と、`prompts/` の貼り付け版でのチャット・API 利用は未確認です（Agent Skills 形式に準拠しています）。各スキルの README の「動作確認」の表が正です。

## ライセンス

このリポジトリの既定は MIT です。各スキルのフォルダにある `LICENSE` が優先します（`jp-internal-comms` は Apache-2.0）。他者の OSS を元にしたスキルは、元の著作権表示とライセンスを同梱しています。
