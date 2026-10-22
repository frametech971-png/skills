# セキュリティ監査（日本向け）（`jp-web-security-audit`）

コード・API・サービスのセキュリティを、防御側の立場でソースから監査します。日本語の報告書（IPA「安全なウェブサイトの作り方」の項番つき）、個人情報が漏れたときの個人情報保護委員会への報告の要否と期限、他社製品の脆弱性の IPA への届出まで扱います。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「このコードの脆弱性を見て、取引先に出す報告書にして」
- 「会員のメールアドレスが不正アクセスで漏れたかも。委員会への報告は要る？期限は？」
- 「令和8年の個人情報保護法改正で、漏えい報告はどう変わる？」
- 「他社のルーターに脆弱性を見つけた。どうすればいい？」

## 元との違い

security-audit（Cloudflare, Inc.、MIT）を元に、次の点を変えました。元のリポジトリ: https://github.com/cloudflare/security-audit-skill（c1c8a8c 時点）。監査の手順・安全規則・検証スクリプトは元のままです。

| 変えたこと | 内容 |
|---|---|
| 日本語の報告書 | IPA「安全なウェブサイトの作り方」（改訂第7版）の項番 1.1〜1.11 を併記し、修正案を「根本的解決」と「保険的対策」に分ける。重大度の日本語訳 |
| 個人情報の漏えい | 施行規則第7条の報告対象4類型、速報（概ね3〜5日）・確報（30日、不正目的は60日）、本人通知、サイバー攻撃の共通様式。令和8年改正（2026-07-17 公布・未施行）の漏えい関係の改正点 |
| 他社製品の脆弱性 | 公表せず IPA の届出制度へ（JPCERT/CC の調整） |
| 発火 | 日本語の発話例と、対象外（他者のシステムへの攻撃・侵入）を description に |

法令の結論は断定せず、根拠の条文・公式ページと確認事項を示します。出典の確認日は 2026-10-10 です。90日を過ぎたら公式ページを読み直すよう、スキル自身に書いてあります。

評価（2026-10-12、Claude Code ／ claude-opus-5-5 で6問を各3回）: タスク達成 99%（元 70%）。報告書の形式に関わる項目（IPA の項番、根本的解決・保険的対策）を除いても 99%（元 79%）。元のスキルは Web 検索で調べても、令和8年改正の漏えい関係の改正点やサイバー攻撃の共通様式に触れられない回がありました。
発火の模擬判定: 発火すべき依頼 20/20・すべきでない依頼 20/20（2回）

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。読み込みの仕組みが無いチャットや API では、貼り付け版（1ファイル）を使います。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code（VS Code 拡張）／ claude-opus-5-5 | 2026-10-12 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。評価は相談（ガイダンス）型の6問で行いました。完全監査モード（6段階の手順と成果物の作成）は評価していません。

必要なもの: 完全監査モードで検証スクリプトを使うときは Node.js。

## インストール

```bash
npx skills add frametech971-png/skills --skill jp-web-security-audit        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-web-security-audit -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**: `/plugin marketplace add frametech971-png/skills` → `/plugin install jp-web-security-audit@frametech-skills`

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-web-security-audit/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-web-security-audit/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う**: `prompts/jp-web-security-audit.prompt.md` を知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。

## このスキルが実行すること

- `validate-findings.cjs`・`validate-coverage-ledger.cjs`（完全監査モードのときだけ）: 引数で渡した JSON ファイルを読み取り専用で開いて検査し、結果を画面に出すだけです。ファイルを書かず、通信しません。
- 完全監査モードの成果物は、既定でホームの `~/security-audit-skill/<リポジトリ名>/run-<N>` に書かれます（元のスキルの仕様）。
- 監査対象のコードを動かすのは、外部通信の無い隔離した環境（サンドボックス）を用意できるときだけです。用意できなければ動かしません。本番環境・他者のシステムには通信しません。

## ライセンス・クレジット

MIT。security-audit © 2025-2026 Cloudflare, Inc.（MIT）を改変しています。元の著作権表示は LICENSE に残しています。

---

## English

Defensive, source-first security audit skill modified from cloudflare/security-audit-skill, with a Japan layer: Japanese reports mapped to IPA's "How to Secure Your Web Site" items, APPI breach-reporting duties and deadlines (incl. the 2026 amendment, not yet in force), and IPA vulnerability disclosure. Verified with Claude Code (claude-opus-5-5). Install: `npx skills add frametech971-png/skills --skill jp-web-security-audit`
