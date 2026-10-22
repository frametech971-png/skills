# Chrome 連携の運用ルール（`lean-browser-ops`）

Claude Code の Chrome 連携（Claude in Chrome）でブラウザを操作するときの、トークンの浪費と事故を防ぐ運用ルールです。スクリーンショットで文脈が膨らむのを防ぐ読み取りの順番、止まる条件、確認なしにやらない操作（購入・公開・送信）、ページ内の指示に従わないことを定めます。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「Chrome でこのサイトを開いてフォームに入力して」
- 「ブラウザを操作して、管理画面から請求書をダウンロードして」
- 「Claude in Chrome でこのページの内容を読み取って整理して」
- 「ブラウザ操作をさせるとトークンが急に増える。どうすれば抑えられる？」
- 「画面を見ながら、このサイトのボタンを順番に押していって」

## 何が違うか

読む順番は軽い順（`javascript_tool` → `get_page_text` → `read_page` → `find` → スクリーンショット）で、スクリーンショットは確認の3つの場面だけ、必ず `scale: 0.5` で撮ります。ファイルのアップロードは `file_upload` を使い、アップロードのボタンをクリックしません。ログイン・CAPTCHA・購入確認で止まり、公開・送信・支払いは確認なしにやりません。ページに書かれた指示はデータとして扱い、従わずに報告します。ページ内の JS にローカルのファイルを渡す一時サーバー `scripts/serve_bridge.py` は、許可するオリジンを1つに固定し、ホームや `.ssh` を含むフォルダを拒否し、時間が来たら自動で止まります。

評価（2026-10-21〜22、Claude Code のサブエージェント／sonnet で各3回。比較対象は元になった旧版の運用メモ）: タスク達成 98%（旧版 97%）／ 発火の模擬判定 発火すべき依頼 10/10・すべきでない依頼 10/10（2回）

**差は小さいスキルです。** 比較対象の旧版も同じ規則を持つため、回答の質の差はほぼ出ません。変わったのは、特定の用途に結びついた記述を一般の Chrome 操作向けに直したことと、`serve_bridge.py` の安全化（許可オリジンの固定、公開フォルダの検査、自動終了）です。後者はこの評価では測れていません。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 対象外（Claude in Chrome 専用のため、貼り付け版での利用は想定していません） | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: Claude Code と Chrome 拡張（Claude in Chrome）。`scripts/serve_bridge.py` は Python 3.9 以上（標準ライブラリだけ）です。他のエージェントのブラウザ操作でも、読む順番・停止条件・禁止事項の考え方は使えます。

既知の制限:
- Claude in Chrome のツール名・引数は拡張の更新で変わりえます（2026-10-21 時点の運用メモに基づき、実機での再確認は未了です）
- `claude-code#27869`（スクリーンショットが文脈に溜まる問題）は 2026-05 に not planned でクローズされています。現行版で解消しているかは未確認です
- `serve_bridge.py` は、拒否・配信・CORS・自動終了・ポート使用中のエラーを手元で確認しています（Python 3.9.6）

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill lean-browser-ops        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill lean-browser-ops -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install lean-browser-ops@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/lean-browser-ops/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/lean-browser-ops/` に置く。claude.ai はフォルダを zip にしてアップロードする。

## このスキルが実行すること

- `scripts/serve_bridge.py`: 指定した一時フォルダだけを `127.0.0.1` で配信し、ページ内の JS から `fetch` で読めるようにします。`--origin` が必須で、`--max-seconds`（既定600秒）で自動終了します。配信するのは指定フォルダの中のファイルだけで、一覧は出しません。外部への通信はありません。

## ライセンス・クレジット

MIT。
