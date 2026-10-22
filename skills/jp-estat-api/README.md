# e-Stat API で日本の公的統計を取る（`jp-estat-api`）

政府統計の総合窓口 e-Stat の API で統計表を探し、条件で絞って全件取得し、欠損記号を残した CSV にして、出典つきで集計します。

> 無料（MIT） ・ v1.0.0 ・ 作者: frametech

## こう頼むと動きます

- 「e-Stat API で都道府県別の人口を取得して」
- 「統計表IDの探し方を教えて」
- 「国勢調査のデータを CSV にして」
- 「appId の取り方は？」
- 「値が '-' や '…' になっているのは何？」
- 「取得件数の上限を超えるときは？」

## 何が違うか

取得は `NEXT_KEY` で続きを取り、欠損・秘匿を表す記号（`-` `…` `X` など）は 0 や空欄にせず、別の列に残します。記号の意味は統計表ごとに違うので、`***` のような公式で確認できない記号は断定せず、表の注記で確かめるよう案内します。出典の書き方（「政府統計の総合窓口（e-Stat）」を書く、加工したら「加工して作成」と明記、国が作成したかのように見せない）と、API を使った公開サービスのクレジット文も `references/` にあります。appId の規約（利用できる数、譲渡の禁止）と、取得時に特殊文字を置換すると記号の区別が消える点にも触れます。

評価（2026-10-22、Claude Code のサブエージェント／sonnet で各3回。比較対象はスキルなし・Web 検索あり）: タスク達成 95%（スキルなし 85%）／ 発火の模擬判定 発火すべき依頼 12/12・すべきでない依頼 14/14（2回）

**退行が少しあります。** 評価8問のうち2問で、スキルなしでは3回とも満たした項目を、こちらは1回ずつ落としました（続きを `NEXT_KEY` で繰り返し取る手順の記載、合計が一部の行だけの合計であることの明示）。スキルなしで外れやすかったのは、appId の規約、取得時の記号の置換、取得していない人口の数値を作ってしまうことでした。

## 動作確認

Agent Skills 形式（`SKILL.md`）のスキルです。対応しているエージェント（Claude Code・Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code ほか79種、2026-10-07 時点）ではフォルダのまま使えます。

| 使い方 | 実機で確認した環境・モデル | 確認日 |
|---|---|---|
| エージェントに入れる | Claude Code ／ sonnet（サブエージェント） | 2026-10-22 |
| チャット・API に貼る | 未確認 | — |

上の表にない環境は、Agent Skills 形式に準拠していますが未検証です。

必要なもの: e-Stat の利用登録（無料）で得る appId を環境変数 `ESTAT_APP_ID` に入れます。スクリプトは Python 3.9 以上（標準ライブラリだけ）です。

既知の制限:
- e-Stat への実通信は、appId が無く未検証です。モックサーバー（`scripts/selftest_mock.py`）で、`NEXT_KEY` のページング、欠損記号の扱い、STATUS 100/1/300、gzip、通信不可を確認しています
- 応答の形は仕様ページの記述に基づきます。実際の応答との差は未確認です
- JSON 形式のみ対応です。XML・CSV 形式、一括取得、データカタログは対象外です
- 取得した行はメモリに集めてから書き出します（数百万行規模は分割してください）
- 国勢調査の統計コード `00200521` は例として載せています。公式の統計コード一覧での再確認は未了です
- 参照資料の確認日は 2026-10-21。90日を過ぎたら公式を読み直してください

## インストール

**エージェントにまとめて入れる**（入っているエージェントを自動で見つけます）

```bash
npx skills add frametech971-png/skills --skill jp-estat-api        # このプロジェクトだけ
npx skills add frametech971-png/skills --skill jp-estat-api -g     # すべてのプロジェクトで
```

**Claude Code のプラグインとして**

```
/plugin marketplace add frametech971-png/skills
/plugin install jp-estat-api@frametech-skills
```

**手で置く**: このフォルダごと、Claude Code はプロジェクトの `.claude/skills/jp-estat-api/`、Codex・Cursor・Gemini CLI・GitHub Copilot・OpenCode・Kimi Code などはプロジェクトの `.agents/skills/jp-estat-api/` に置く。claude.ai はフォルダを zip にしてアップロードする。

**チャット・API で使う（ChatGPT・Gemini・Grok・DeepSeek など）**: `prompts/jp-estat-api.prompt.md` を、プロジェクト・Gem・GPT の知識ファイルとして入れるか、会話の最初に貼ってから「このスキルで〜して」と頼む。API ではシステムプロンプトに入れる。`npx skills use frametech971-png/skills@jp-estat-api` でも同じプロンプトが出ます。

## このスキルが実行すること

- `scripts/estat_fetch.py`: 環境変数の appId で api.e-stat.go.jp に接続し、統計表ID と絞り込み条件で全ページを取得して CSV に出力します。`--dry-run` では通信せず、appId を伏せて送る内容を表示します。通信先は api.e-stat.go.jp だけです。
- `scripts/selftest_mock.py`: 上のスクリプトを標準ライブラリのモックサーバーで検査します。外部には通信しません。

## ライセンス・クレジット

MIT。
