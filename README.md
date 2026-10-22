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
| [`jp-kintone-api`](skills/jp-kintone-api) | kintone の REST API でレコードを取得・登録・更新するコードを書き、クエリ構文・件数制限・認証・エラーの原因を調べる。 | MIT | v1.0.0 |
| [`jp-freee-api`](skills/jp-freee-api) | freee 会計の API（OAuth2 認証、事業所ID、取引・勘定科目・取引先の取得と登録）を使うコードを書く、取引を期間指定で取得して CSV にする、認証やエラーの原因を調べる。 | MIT | v1.0.0 |
| [`jp-privacy-policy-check`](skills/jp-privacy-policy-check) | Webサービス・アプリのプライバシーポリシー（個人情報の取扱い）を、個人情報保護法と電気通信事業法の外部送信規律に照らして点検し、足りない項目を根拠条文つきの表で指摘する。 | MIT | v1.0.0 |
| [`jp-invoice-check`](skills/jp-invoice-check) | 日本のインボイス制度（適格請求書・適格簡易請求書）の記載事項の不足を指摘し、税率ごとの消費税額を検算し、登録番号（T+13桁）の形式と検査桁を確認する。 | MIT | v1.0.0 |

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
