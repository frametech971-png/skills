# 日本の営業日の計算（`jp-business-days`）

日本の祝日（振替休日・国民の休日を含む）を踏まえて、N営業日後、期間内の営業日数、月末・支払期限の休日繰り延べ、祝日の一覧を、日付を間違えずに出します。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「2026年の祝日を一覧にして」
- 「10月30日から3営業日後は？」
- 「今月の営業日数は？」
- 「支払期限が土日祝なら翌営業日に直して」
- 「この日は祝日？」
- 「年末年始（12/29〜1/3）を休みにした営業日計算」

## 何が違うか

祝日は国民の祝日に関する法律のルール（ハッピーマンデー、春分・秋分の日、振替休日、国民の休日）から計算します。実装の出力は内閣府の祝日CSV（1955〜2027年）と全年一致することを確認しています。年末年始は法定の祝日ではなく会社ごとの休みなので、`--extra-closed` で別に足す形にしています。起点の日付が無い依頼には日付を作らずに聞き返し、数えるときに起点の日を含めるかなどの前提を明記します。

評価（2026-10-22、Claude Code のサブエージェント／sonnet で各3回。比較対象はスキルなし・Web 検索とコード実行あり）: タスク達成 100%（スキルなし 95%）／ 発火の模擬判定 発火すべき依頼 12/12・すべきでない依頼 14/14（2回）

**差は小さいスキルです。** スキルなしでもコードを実行して祝日・営業日を正しく計算できるため、結果の正しさはほぼ同じでした。差が出たのは、「起点の日は数えない」という前提を書くこと、年末年始が法定の祝日ではなく会社の休みだと区別すること、起点日が無いときに聞き返すことです。このスキルの利点は、祝日を法令のルールで計算する実装と、内閣府CSVとの突き合わせ（`verify-csv`）が手元に揃っていることです。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: Python 3.9 以上（標準ライブラリだけ）。実行できない環境でも手順は書けますが、数え上げは誤りやすいので結果に「未検算」と付ける作りです。

既知の制限:
- 対応は 1955〜2099 年です
- 2028 年以降の春分・秋分の日は官報公表前の推定です（確定は前年2月）。確定後は `OFFICIAL_EQUINOX_THROUGH` を更新して `verify-csv` で突き合わせてください
- 銀行の休日、行政機関の休日、民法の期間の規定は判定しません
- e-Gov 法令検索が確認時（2026-10-22）にメンテナンス中で、法務省の日本法令外国語訳DBの現行条文で確認しています。改正法の逐条は読んでいません（施行日と内閣府CSVの年ごとの変化で裏付け）

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-business-days        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-business-days -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-business-days@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-business-days/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-business-days/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-business-days.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-business-days` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/jbd.py`: `holidays`（年の祝日）・`is-holiday`・`add`（N営業日後）・`count`・`next-business-day`・`month-end`・`verify-csv`（内閣府CSVとの突き合わせ）。引数や、渡された内閣府CSVのファイルを読むだけで、ファイルは書かず、外部への通信もありません。

## ライセンス・クレジット

MIT。
