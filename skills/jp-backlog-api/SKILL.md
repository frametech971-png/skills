---
name: jp-backlog-api
description: >-
  Backlog（ヌーラボ）API v2 で課題の取得・登録・更新・コメント・ステータス変更をするコードを書き、認証・件数制限・エラーの原因を調べる。「Backlog の課題を全件 CSV にして」「課題を API で登録したい」「APIキーの取り方と権限エラーを調べて」「ステータスを一括で変えたい」「課題一覧が20件しか返らない」と頼まれたときに使う。公式（確認日つき）に沿い、count 上限100と offset での全件取得、登録の必須4項目と ID の調べ方、レート制限、エラーコード表を備え、CSV 出力・登録・一括ステータス変更のスクリプトを同梱。鍵は環境変数から読み、コードや会話に書かない。Keywords: Backlog API v2, Nulab, issues, Backlog-API-Key, OAuth 2.0, rate limit。Backlog の Git/Wiki 操作全般、Jira・Redmine など他の課題管理サービスは対象外。
license: MIT
compatibility: "Python 3.9 以上（標準ライブラリだけ）。Backlog への通信にはインターネット接続が必要。通信できない環境では --dry-run と手順の提示まで"
metadata:
  version: "1.0.0"
  author: frametech
---

# Backlog API v2（課題の取得・登録・更新）

目的: Backlog の課題を API で読み書きするコードと、認証・制限・エラーの答えを、公式仕様どおりに出す。
入力: やりたいこと（取得／登録／ステータス変更）、スペースのホスト（`xxx.backlog.com` か `.backlog.jp`）、プロジェクト、絞り込み、エラーメッセージ。**APIキーは聞かない・書き写さない。**
出力: 動くコード（またはスクリプトの実行手順）と、効いている制限の一言。エラー調べなら「原因の候補 → 確かめ方 → 直し方」。

事実は [references/](references/) にある（確認日 2026-10-23）。**確認日から90日を過ぎたら、各ファイル冒頭の公式URLを読み直してから答える。**

## 鍵の扱い（最初に守る）

- APIキー・トークンは**コード・コマンド引数・ファイル・会話に書かない**。貼られても書き写さず、環境変数 `BACKLOG_API_KEY` から読む形で書く。貼られた鍵は漏れた可能性があるので、再発行（古い鍵の無効化）を一言勧める。
- 環境変数: `BACKLOG_SPACE`（例 `example.backlog.jp`。URL のホスト部分）、`BACKLOG_API_KEY`、OAuth なら `BACKLOG_ACCESS_TOKEN`（1時間で失効）。
- 鍵はヘッダー `Backlog-API-Key` で送る。URL の `apiKey=` はログに残るので使わない。

## 手順

1. 依頼を分ける: (a) 全件取得・CSV (b) 課題の登録 (c) ステータス等の更新・一括変更 (d) 認証・権限・エラー調べ (e) 制限の質問。
2. ホストを確認する。`.backlog.com` と `.backlog.jp` は別物で、自分のスペースの URL のとおりに。
3. (a) 全件取得は**一覧が1回最大100件（既定20）**。`count=100` で offset を100ずつ増やし、返りが100件未満で終了。総数は `/issues/count`。スクリプト:

   ```bash
   python3 scripts/backlog_issues.py fetch --dry-run
   python3 scripts/backlog_issues.py fetch --count-only --project-id 123
   python3 scripts/backlog_issues.py fetch --project-id 123 --status-id 1,2 -o issues.csv --bom
   ```

   既定は 1 秒間隔（公式の一括処理の目安）。2万件なら 200 回強で数分かかると先に伝える。`--max-issues 50` で試し取り。実行できない・通信できない環境では、references/api-spec.md §3 のとおり URL とヘッダーを組み立てて示し、手元で実行してもらう。
4. (b) 登録は**必須4つ** `projectId` `summary` `issueTypeId` `priorityId`、本文は **JSON ではなく form**（api-spec.md §4）。ID は名前ではなく数字なので、先に `meta` で調べる（`meta` → プロジェクト・優先度、`meta --project-id 123` → 状態・種別・カスタム属性）。CSV 登録は**必ず先に `--dry-run`**、内容をユーザーに見せて確認を取ってから `--yes`。途中で失敗したら登録済みの課題キーを伝え、同じ CSV の再実行は重複になると警告する。
5. (c) 一括ステータス変更: `set-status --keys PRJ-1,PRJ-2 --status-id 4`（`--dry-run` → 確認 → `--yes`）。状態 ID は**プロジェクトごとに違う**。変更は履歴に残り通知も飛ぶので、対象件数と変更後の状態を先に見せる。完了にするなら `resolutionId` も要るか確認。同じ指定の再実行は安全（冪等）。
6. (d) エラーは `errors[].code` と HTTP ステータスを聞き、references/errors.md の表から出す。**権限エラー（code 5）はキーではなくユーザーの権限・制限が原因**で、キーを作り直しても直らない。APIキーの発行画面の手順は公式で確認できていないため、「個人設定の API から。画面は要確認」と添える。
7. (e) 制限: 分あたりの固定値は公式ページに無く、プランと種別で変わる。**ユーザー単位**で、応答ヘッダー `X-RateLimit-*` と「レート制限情報の取得」API で確認。超過は 429 → 1分待つ。

## 返す形

```
（コードまたは実行コマンド）

効いている制限: count 100／1秒間隔／429 は1分待つ など今回に関係するものだけ
確認が要ること: ホスト（.com/.jp）、projectId などの ID、ユーザーの権限
```

## 同梱物

| ファイル | 内容 |
|---|---|
| scripts/backlog_issues.py | `fetch`（全件→CSV/JSON）、`meta`（ID の一覧）、`add`（CSV→登録）、`set-status`（一括変更）。`--help` `--dry-run`。書き込みは `--yes` 必須。終了コード 0 正常／1 API・通信の失敗／2 引数・環境変数の誤り（`--yes` なしもここ） |
| scripts/selftest_mock.py | モックの Backlog で、ページング・429・分割・失敗時の挙動を確かめる自己検証（本物には接続しない） |
| references/api-spec.md | ホスト・認証・件数・登録の必須項目・更新・レート制限（出典URLと確認日つき） |
| references/errors.md | エラーコード表（公式）と症状別の対処 |
| references/recipes.md | curl・Python のコード例 |

## 限界

実際の Backlog スペースでの成功は未検証（モックと公式仕様の突き合わせまで）。初めて本番に向けるときは `--count-only` と `--max-issues` から。offset の上限・完了課題が既定で含まれるか・カスタム属性の typeId の意味は公式で確認できていない（要確認）。
