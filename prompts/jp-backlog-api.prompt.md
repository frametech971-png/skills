<!-- jp-backlog-api v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-backlog-api（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
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

=== FILE: references/api-spec.md ===
# Backlog API v2 の仕様（課題系）

確認日: 2026-10-23。**確認日から90日を過ぎたら、下の出典を読み直してから使う。** 数字・上限は変わりうる。
出典（すべてヌーラボ公式 developer.nulab.com）:
- 概要: https://developer.nulab.com/ja/docs/backlog/
- 認証と認可: https://developer.nulab.com/ja/docs/backlog/auth/
- レート制限: https://developer.nulab.com/ja/docs/backlog/rate-limit/
- エラーレスポンス: https://developer.nulab.com/ja/docs/backlog/error-response/
- 課題一覧: https://developer.nulab.com/ja/docs/backlog/api/2/get-issue-list/
- 課題数: https://developer.nulab.com/ja/docs/backlog/api/2/count-issue/
- 課題の追加: https://developer.nulab.com/ja/docs/backlog/api/2/add-issue/
- 課題の更新: https://developer.nulab.com/ja/docs/backlog/api/2/update-issue/
- コメント追加: https://developer.nulab.com/ja/docs/backlog/api/2/add-comment/
- 状態一覧: https://developer.nulab.com/ja/docs/backlog/api/2/get-status-list-of-project/
- 優先度一覧: https://developer.nulab.com/ja/docs/backlog/api/2/get-priority-list/
- 種別一覧: https://developer.nulab.com/ja/docs/backlog/api/2/get-issue-type-list/
- カスタム属性一覧: https://developer.nulab.com/ja/docs/backlog/api/2/get-custom-field-list/
- プロジェクト一覧: https://developer.nulab.com/ja/docs/backlog/api/2/get-project-list/

## 1. スペースURL（ホスト）

- ベースは `https://<スペースID>.backlog.com` / `.backlog.jp` / `.backlogtool.com`（各 API ページの記載。認証ページには `.backlog.jp` と `.backlog.com` の2つが載り、`backlogtool.com` は書かれていない）。どれかは**自分のスペースの URL のとおり**。別ドメインのスペースにキーは通らない。
- パスは `/api/v2/...`。

## 2. 認証

| 方式 | 送り方 | 注意 |
|---|---|---|
| APIキー | `Backlog-API-Key: <キー>` ヘッダー（公式推奨）。クエリ `apiKey=<キー>` も可 | URL に載せるとアクセスログ・履歴に残るため、ヘッダーを使う。キーは**ユーザーごと**に発行され、そのユーザーの権限で動く |
| OAuth 2.0（認可コード） | `Authorization: Bearer <access_token>` | アプリ登録で client_id / client_secret。認可 `GET /OAuth2AccessRequest.action`（response_type=code, client_id, redirect_uri, state）、トークン `POST /api/v2/oauth2/token`（form。grant_type=authorization_code または refresh_token）。アクセストークンは**3600秒（1時間）**で失効し、refresh_token で更新。失効・不正は 401 |

- **APIキーの発行手順は認証ページに書かれていなかった**（要確認）。一般には Backlog の個人設定にある「API」から発行する、とされるが、公式のこの確認では裏取りしていない。
- API ごとの権限: 各 API ページに「すべての権限」「課題の登録のみ（制限）」等が載る。キーやトークンに**スコープの指定は無く**、ユーザーの権限（管理者・プロジェクト管理者・一般・ゲスト）と制限（制限なし・課題の登録のみ・閲覧のみ）で決まる。→ 権限エラーはキーではなく**ユーザーの権限**を疑う。

## 3. 課題一覧 `GET /api/v2/issues`

- **`count`: 1〜100、既定20**。`offset`: 0以上（上限の記載は確認できず・要確認）。`sort`（`created` `updated` `status` `dueDate` `customField_<id>` など。既定の記載なし）、`order`: `asc`/`desc`（既定 `desc`）。
- 応答は**配列だけ**で、総件数は付かない → 総数は `GET /api/v2/issues/count`（`{"count": 43}`）。全件取得は「count=100、offset を100ずつ増やし、返りが100件未満で終了」。
- フィルタ: `projectId[]` `issueTypeId[]` `categoryId[]` `versionId[]` `milestoneId[]` `statusId[]` `priorityId[]` `assigneeId[]` `createdUserId[]` `resolutionId[]` `id[]` `parentIssueId[]`（配列は `statusId[]=1&statusId[]=2` の形）、`keyword`、`parentChild`、`attachment`、`sharedFile`、日付 `createdSince/Until` `updatedSince/Until` `startDateSince/Until` `dueDateSince/Until`（`yyyy-MM-dd`）、`hasDueDate`（**`false` のみ**。`true` はエラー）、`expand[]=childIssueSummary`。
- カスタム属性の絞り込み: テキスト `customField_<id>`、数値・日付 `customField_<id>_min` / `_max`、リスト `customField_<id>[]`（選択肢ID）。
- 応答の課題: `id` `issueKey` `summary` `description` `status{id,name}` `priority` `issueType` `assignee` `category[]` `versions[]` `milestone[]` `startDate` `dueDate` `created` `updated` `customFields[]` `attachments[]` `stars[]` ほか。
- 「完了」の課題が既定で含まれるか: 一覧ページに記載なし（要確認）。必要なら `statusId[]` で明示する。

## 4. 課題の登録 `POST /api/v2/issues`

- 本文は **`application/x-www-form-urlencoded`**（JSON ではない）。成功は **201 Created**。
- **必須4つ**: `projectId`（int。プロジェクト一覧 `GET /api/v2/projects` の `id`）、`summary`（string）、`issueTypeId`（int。`GET /api/v2/projects/:projectIdOrKey/issueTypes`）、`priorityId`（int。`GET /api/v2/priorities`。例: 2=高 3=中 4=低 — 例示のため自スペースで確認する）。
- 任意: `parentIssueId` `description` `startDate` `dueDate`（yyyy-MM-dd）`estimatedHours` `actualHours` `categoryId[]` `versionId[]` `milestoneId[]` `assigneeId` `notifiedUserId[]` `attachmentId[]`。
- カスタム属性: `customField_<id>`（テキスト＝文字列、数値＝数、日付＝yyyy-MM-dd、リスト＝選択肢ID）、`customField_<id>_otherValue`（リストの「その他」）。ID・選択肢IDは `GET /api/v2/projects/:projectIdOrKey/customFields`。`typeId` の意味の表と、`required: true` のときの挙動は公式ページに無かった（要確認）。
- 権限: 「すべての権限」。制限が「課題の登録のみ」でも可。

## 5. 更新・ステータス変更・コメント

- 更新 `PATCH /api/v2/issues/:issueIdOrKey`（課題IDまたは `PRJ-12` のキー）、form 本文、成功 200。`statusId`（`GET /api/v2/projects/:projectIdOrKey/statuses` の `id`）、`resolutionId`、`comment`（同時にコメント）ほか登録と同じ項目。送った項目だけ変わる（冪等に再実行できる）。
- コメント追加 `POST /api/v2/issues/:issueIdOrKey/comments`、form、`content` 必須、成功 **201**。
- 状態・種別・カスタム属性の ID は**プロジェクトごとに違う**。別プロジェクトの ID を使い回さない。

## 6. レート制限

- 制限は**ユーザー単位（APIキー単位ではない）**。区分: 読み込み（GET）・更新（POST/PATCH/DELETE。PUT の記載なし）・検索（課題一覧・課題数・Wiki 一覧・Wiki 数の GET）・アイコン。
- **分あたりの固定値はページに無い**（種別とプランで異なり、混雑時は下がることがある）。現在値は「レート制限情報の取得」API で見る。ページ内の 150回/分は例示。
- 全応答のヘッダー: `X-RateLimit-Limit`（毎分の上限）`X-RateLimit-Remaining` `X-RateLimit-Reset`（UNIX 時刻）。超過は **429**。
- 公式の指針: 1アプリから同時に複数送らない。一括の更新・検索は**1秒以上あける**。429 は1分後に再試行（短くするなら Reset から計算）。

## 7. 未確認

- 実スペースでの成功は未検証（モックとの突き合わせまで）。
- offset の上限、APIキーの発行画面の手順、完了課題が既定で含まれるか、`typeId` の意味、429 以外の HTTP ステータスとエラーコードの対応。

=== FILE: references/errors.md ===
# エラーの読み方と対処

確認日: 2026-10-23。出典: https://developer.nulab.com/ja/docs/backlog/error-response/ ・ https://developer.nulab.com/ja/docs/backlog/auth/ ・ https://developer.nulab.com/ja/docs/backlog/rate-limit/ 。**90日を過ぎたら公式を読み直す。**

## 形式（公式）

```
HTTP/1.1 404 Not Found
{"errors":[{"message":"No project.","code":6,"moreInfo":""}]}
```
`errors[]` の各要素は `message` `code` `moreInfo`。公式ページが HTTP ステータスとの対応を書いているのは「code 6 = 404」の例だけ。

## code 一覧（公式）

| code | 名前 | 意味 | 次の手 |
|---|---|---|---|
| 1 | InternalError | 内部の問題 | 少し待って再試行。続くなら Backlog のサポートへ |
| 2 | LicenceError | 現プランで使えない機能 | プランを確認 |
| 3 | LicenceExpiredError | ライセンス期限切れ | 契約を確認 |
| 4 | AccessDeniedError | アクセス拒否（IPアドレス制限など） | スペースの IP 制限を確認 |
| 5 | UnauthorizedOperationError | そのユーザーに操作の権限が無い | ユーザーの権限（管理者/一般/ゲスト）と制限（課題の登録のみ・閲覧のみ）、プロジェクト参加の有無を確認。**キーを作り直しても直らない** |
| 6 | NoResourceError | 対象が存在しない | projectId・課題キー・スペースのホスト。参加していないプロジェクトも見えない |
| 7 | InvalidRequestError | パラメーター不正 | 必須4つ、ID の取り違え（名前を渡している）、日付 yyyy-MM-dd、`hasDueDate=true`、`count` が1〜100の外、form でなく JSON を送っている |
| 8 | SpaceOverCapacityError | スペース容量超過 | 容量を確認 |
| 9 | ResourceOverflowError | 上限超過 | 追加できる数の上限 |
| 10 | TooLargeFileError | ファイルが大きすぎる | 添付のサイズ |
| 11 | AuthenticationError | 認証失敗 | キーの誤り・別スペースのキー・失効したユーザー。ヘッダー名 `Backlog-API-Key` を確認 |
| 12 | RequiredMFAError | スペースが2要素認証を必須にしているが未設定 | ユーザー側で設定 |
| 13 | TooManyRequestsError | レート制限（HTTP 429） | 1分待つ。`X-RateLimit-Reset` を見る。間隔を1秒以上に |

## 症状から探す

| 症状 | 原因の候補 | 次の手 |
|---|---|---|
| 401 + `WWW-Authenticate: invalid_token` | OAuth のアクセストークンが不正または**1時間で期限切れ** | refresh_token で更新 |
| 401 / code 11 | キーが違う・ホストが違う（`.backlog.com` と `.backlog.jp` を取り違え） | `BACKLOG_SPACE` と発行元スペースを一致させる |
| code 5 で登録だけ通る | ユーザーの制限が「課題の登録のみ」 | 取得・更新には使えない。権限の見直しを管理者へ |
| 一覧が20件しか来ない | `count` 既定20 | `count=100` と offset で繰り返す（上限100） |
| 登録で code 7 | 必須4つの欠け、`priorityId` に「高」などの文字を渡した | `meta` で ID を調べる |
| 429 が頻発 | 並列・連続送信。制限はユーザー単位なので同じユーザーの他アプリの分も数える | 逐次・1秒以上あける |

=== FILE: references/recipes.md ===
# コード例（Python 標準ライブラリ・curl）

出典の仕様は api-spec.md（確認日 2026-10-23）。鍵は環境変数から読み、コードに書かない。

## curl

```bash
# 件数
curl -s -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues/count?projectId%5B%5D=123"
# 1ページ（100件）
curl -s -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues?projectId%5B%5D=123&count=100&offset=0&sort=created&order=asc"
# 登録（form 本文。-d は application/x-www-form-urlencoded になる）
curl -s -X POST -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues" \
  -d projectId=123 --data-urlencode "summary=テスト課題" -d issueTypeId=7 -d priorityId=3
# ステータス変更
curl -s -X PATCH -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues/PRJ-1" -d statusId=4
# コメント
curl -s -X POST -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues/PRJ-1/comments" --data-urlencode "content=確認しました"
```

## Python（全件取得の骨格）

```python
import json, os, time, urllib.parse, urllib.request
BASE = "https://" + os.environ["BACKLOG_SPACE"]          # 例 example.backlog.jp
KEY = os.environ["BACKLOG_API_KEY"]

def get(path, params):
    url = BASE + path + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Backlog-API-Key": KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

issues, offset = [], 0
while True:
    page = get("/api/v2/issues", [("projectId[]", 123), ("count", 100), ("offset", offset), ("sort", "created"), ("order", "asc")])
    issues += page
    if len(page) < 100:
        break
    offset += 100
    time.sleep(1)            # 公式: 一括処理は1秒以上あける
```

登録・更新は `urllib.request.Request(url, data=urllib.parse.urlencode(form, doseq=True).encode(), method="POST"|"PATCH")`（Content-Type は `application/x-www-form-urlencoded`）。配列は `[("categoryId[]", 1), ("categoryId[]", 2)]`。

## ID の調べ方

`python3 scripts/backlog_issues.py meta`（プロジェクト一覧と優先度）→ `meta --project-id 123`（状態・種別・カスタム属性）。

=== FILE: scripts/backlog_issues.py ===
#!/usr/bin/env python3
"""Backlog（ヌーラボ）API v2 で、課題の全件取得（CSV/JSON）・登録・ステータス一括変更をする。

Python 3.9 以上・標準ライブラリだけ。通信先は BACKLOG_SPACE で指定したスペースのホストだけ。

  環境変数（鍵は引数に取らない・出力に出さない）
    BACKLOG_SPACE         必須。スペースのホスト名。例: example.backlog.com / example.backlog.jp
    BACKLOG_API_KEY       APIキー（Backlog-API-Key ヘッダーで送る。URL には付けない）
    BACKLOG_ACCESS_TOKEN  OAuth 2.0 のアクセストークン（あれば APIキーより優先。Authorization: Bearer）

  使い方
    python3 backlog_issues.py fetch --dry-run
    python3 backlog_issues.py fetch --project-id 123 --status-id 1,2 -o issues.csv --bom
    python3 backlog_issues.py meta --project-id 123            # 登録に要る ID の一覧（読み取りのみ）
    python3 backlog_issues.py add --csv new.csv --dry-run
    python3 backlog_issues.py add --csv new.csv --yes
    python3 backlog_issues.py set-status --keys PRJ-1,PRJ-2 --status-id 4 --yes

  終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り（--yes が無い書き込みもここ）

通信できない環境（外部通信が禁止のチャット等）では実行できない。--dry-run は通信しないので、
組み立てた URL・ヘッダー・本文を確かめて、手元の環境で実行してもらう。
"""
import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 1, 2
PAGE_MAX = 100          # 課題一覧 count の上限（公式）
MASK = "＊＊＊＊（環境変数から読み込み済み・表示しない）"
HOST_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*\.backlog(?:tool)?\.(?:com|jp)")


class UsageError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status, errors, raw=""):
        super().__init__("HTTP %s" % status)
        self.status, self.errors, self.raw = status, errors, raw


class Client:
    def __init__(self, scheme, host, auth, interval, retry_wait, retries=3):
        self.base = "%s://%s" % (scheme, host)
        self.auth, self.interval, self.retry_wait, self.retries = auth, interval, retry_wait, retries
        self._last = 0.0
        self.calls = 0

    def headers(self, masked=False):
        name, val = self.auth
        return {name: MASK if masked else (("Bearer " + val) if name == "Authorization" else val)}

    def url(self, path, params=None):
        q = urllib.parse.urlencode(params or [], doseq=True)
        return self.base + path + ("?" + q if q else "")

    def request(self, method, path, params=None, form=None):
        """params は URL、form は application/x-www-form-urlencoded 本文。(status, json, headers) を返す。"""
        url = self.url(path, params if method == "GET" else None)
        data = urllib.parse.urlencode(form, doseq=True).encode("utf-8") if form is not None else None
        for attempt in range(self.retries + 1):
            wait = self.interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(url, data=data, method=method)
            for k, v in self.headers().items():
                req.add_header(k, v)
            if data is not None:
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
            self._last = time.time()
            self.calls += 1
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read().decode("utf-8")
                    return r.status, (json.loads(body) if body.strip() else None), r.headers
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", "replace")
                if e.code == 429 and attempt < self.retries:
                    time.sleep(self._reset_wait(e.headers))
                    continue
                try:
                    errs = json.loads(raw).get("errors", [])
                except Exception:
                    errs = []
                raise ApiError(e.code, errs, raw[:300])
            except urllib.error.URLError as e:
                raise ApiError(0, [{"message": "通信できません: %s" % e.reason, "code": None}])
        raise ApiError(429, [{"message": "レート制限が続きました", "code": 13}])

    def _reset_wait(self, headers):
        # X-RateLimit-Reset は UNIX 時刻。無ければ公式の目安どおり 1 分待つ（--retry-wait で変更）
        try:
            reset = int(headers.get("X-RateLimit-Reset"))
            return max(0.0, min(reset - time.time() + 1, 120.0)) if self.retry_wait else 0.0
        except (TypeError, ValueError):
            return self.retry_wait


def explain(e):
    """原因と次の手。公式のエラーコード表（references/api-spec.md）に沿う。"""
    hints = {
        2: "このプランでは使えない機能です。プランを確認してください。",
        4: "アクセスが拒否されました。IP アドレス制限の可能性があります。",
        5: "このユーザーにその操作の権限がありません。権限（管理者/一般/ゲスト）と制限（課題の登録のみ・閲覧のみ）を確認してください。",
        6: "リソースが見つかりません。projectId・課題キー・スペースのホストを確認してください。",
        7: "パラメーターが不正です。必須項目・ID の取り違え・日付形式（yyyy-MM-dd）を確認してください。",
        11: "認証に失敗しました。APIキー（またはトークン）が正しいか、別スペースのものでないか確認してください。",
        12: "このスペースは2要素認証が必須です。ユーザー側で設定してください。",
        13: "レート制限です。しばらく待って、間隔（--interval）を広げて再実行してください。",
    }
    lines = ["HTTP %s" % e.status]
    for er in e.errors:
        lines.append("  code=%s message=%s" % (er.get("code"), er.get("message")))
        if er.get("code") in hints:
            lines.append("  -> " + hints[er.get("code")])
    if e.status == 401 and not e.errors:
        lines.append("  -> 認証エラー。キーが無効か、OAuth のアクセストークンが期限切れ（1時間）かもしれません。")
    if e.status == 429:
        lines.append("  -> レート制限。1分ほど待つか --interval を広げてください。")
    if e.status == 0:
        lines.append("  -> " + e.errors[0]["message"] + "（BACKLOG_SPACE のホスト名・ネットワークを確認）")
    if not e.errors and e.raw and e.status not in (0, 401, 429):
        lines.append("  本文: " + e.raw)
    return "\n".join(lines)


# ───────── 設定 ─────────

def load_client(args):
    env = os.environ
    space = env.get("BACKLOG_SPACE", "").strip()
    scheme = "https"
    if not space:
        raise UsageError("環境変数 BACKLOG_SPACE が空です。例: export BACKLOG_SPACE=example.backlog.com（.backlog.jp のスペースもある。URL のホスト部分）")
    space = re.sub(r"^https?://", "", space).rstrip("/")
    if env.get("BACKLOG_TEST_HTTP") == "1" and re.fullmatch(r"(127\.0\.0\.1|localhost):\d+", space):
        scheme = "http"  # 自己検証のモックサーバー専用（ローカルホストだけ）
    elif not HOST_RE.fullmatch(space):
        raise UsageError("BACKLOG_SPACE の形式が違います: '%s'。<スペースID>.backlog.com か .backlog.jp（.backlogtool.com も可）の形で指定してください。" % space)
    token = env.get("BACKLOG_ACCESS_TOKEN", "").strip()
    key = env.get("BACKLOG_API_KEY", "").strip()
    if token:
        auth = ("Authorization", token)
    elif key:
        auth = ("Backlog-API-Key", key)
    elif getattr(args, "dry_run", False):
        auth = ("Backlog-API-Key", "")
    else:
        raise UsageError("環境変数 BACKLOG_API_KEY（または BACKLOG_ACCESS_TOKEN）が空です。鍵は引数や会話に書かず、環境変数に入れてください。")
    return Client(scheme, space, auth, args.interval, args.retry_wait)


def csv_ints(s):
    out = []
    for p in (s or "").split(","):
        p = p.strip()
        if p:
            if not re.fullmatch(r"[0-9]+", p):
                raise UsageError("数字のカンマ区切りで指定してください: '%s'" % p)
            out.append(p)
    return out


# ───────── fetch ─────────

FILTERS = [("project_id", "projectId[]"), ("issue_type_id", "issueTypeId[]"), ("status_id", "statusId[]"),
           ("priority_id", "priorityId[]"), ("assignee_id", "assigneeId[]"), ("category_id", "categoryId[]"),
           ("milestone_id", "milestoneId[]")]
DATES = [("created_since", "createdSince"), ("created_until", "createdUntil"),
         ("updated_since", "updatedSince"), ("updated_until", "updatedUntil"),
         ("due_since", "dueDateSince"), ("due_until", "dueDateUntil")]


def filter_params(args):
    p = []
    for attr, name in FILTERS:
        for v in csv_ints(getattr(args, attr, None)):
            p.append((name, v))
    for attr, name in DATES:
        v = getattr(args, attr, None)
        if v:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                raise UsageError("日付は yyyy-MM-dd 形式です: '%s'" % v)
            p.append((name, v))
    if args.keyword:
        p.append(("keyword", args.keyword))
    return p


def flat(v):
    if v is None:
        return ""
    if isinstance(v, dict):
        return str(v.get("name", v.get("value", v.get("id", ""))))
    if isinstance(v, list):
        return ";".join(flat(x) for x in v)
    return str(v)


BASE_COLS = ["issueKey", "id", "projectId", "summary", "status", "priority", "issueType", "assignee",
             "createdUser", "created", "updatedUser", "updated", "startDate", "dueDate",
             "estimatedHours", "actualHours", "category", "versions", "milestone", "parentIssueId", "description"]


def issue_row(it):
    row = {}
    for c in BASE_COLS:
        row[c] = flat(it.get(c))
    for cf in it.get("customFields") or []:
        row["カスタム:" + str(cf.get("name"))] = flat(cf.get("value"))
        if cf.get("otherValue"):
            row["カスタム:" + str(cf.get("name"))] += "（その他: %s）" % cf["otherValue"]
    return row


def write_csv(issues, path, bom):
    rows = [issue_row(i) for i in issues]
    cols = list(BASE_COLS)
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\r\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in cols})
    data = buf.getvalue().encode("utf-8-sig" if bom else "utf-8")
    if path in (None, "-"):
        sys.stdout.buffer.write(data)
    else:
        with open(path, "wb") as f:
            f.write(data)


def cmd_fetch(args):
    cl = load_client(args)
    filt = filter_params(args)
    page_params = filt + [("sort", args.sort), ("order", args.order), ("count", PAGE_MAX), ("offset", 0)]
    if args.dry_run:
        print("[dry-run] 通信しません。")
        print("GET " + cl.url("/api/v2/issues/count", filt))
        print("GET " + cl.url("/api/v2/issues", page_params) + "   （offset を %d ずつ増やして、返りが %d 件未満になるまで繰り返す）" % (PAGE_MAX, PAGE_MAX))
        print("ヘッダー: %s" % cl.headers(masked=True))
        print("間隔: %.1f 秒（公式の目安は一括処理で1秒以上）" % cl.interval)
        return EXIT_OK
    _, c, _ = cl.request("GET", "/api/v2/issues/count", filt)
    total = (c or {}).get("count")
    print("条件に合う課題: %s 件（約 %s 回のリクエスト）" % (total, (total or 0) // PAGE_MAX + 1), file=sys.stderr)
    if args.count_only:
        print(total)
        return EXIT_OK
    issues, seen, offset = [], set(), 0
    while True:
        params = [(k, v) if k != "offset" else (k, offset) for k, v in page_params]
        _, page, _ = cl.request("GET", "/api/v2/issues", params)
        page = page or []
        for it in page:
            if it.get("id") not in seen:
                seen.add(it.get("id"))
                issues.append(it)
        if args.max_issues and len(issues) >= args.max_issues:
            issues = issues[:args.max_issues]
            break
        if len(page) < PAGE_MAX:
            break
        offset += PAGE_MAX
        print("  取得済み %d 件" % len(issues), file=sys.stderr)
    if total is not None and len(issues) != total and not args.max_issues:
        print("注意: 件数 API は %s 件、取得できたのは %d 件。取得中に課題が増減した可能性があります（重複は除いてあります）。" % (total, len(issues)), file=sys.stderr)
    if args.format == "json":
        data = json.dumps(issues, ensure_ascii=False, indent=1)
        if args.output in (None, "-"):
            print(data)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(data)
    else:
        write_csv(issues, args.output, args.bom)
    print("%d 件を書き出しました。" % len(issues), file=sys.stderr)
    return EXIT_OK


# ───────── meta ─────────

def cmd_meta(args):
    cl = load_client(args)
    proj = args.project_id
    plan = [("優先度 priorityId", "/api/v2/priorities")]
    if proj:
        plan += [("状態 statusId", "/api/v2/projects/%s/statuses" % proj),
                 ("種別 issueTypeId", "/api/v2/projects/%s/issueTypes" % proj),
                 ("カスタム属性 customField_<id>", "/api/v2/projects/%s/customFields" % proj)]
    else:
        plan.insert(0, ("プロジェクト projectId", "/api/v2/projects"))
    if args.dry_run:
        print("[dry-run] 通信しません。")
        for label, path in plan:
            print("GET " + cl.url(path))
        print("ヘッダー: %s" % cl.headers(masked=True))
        return EXIT_OK
    for label, path in plan:
        _, items, _ = cl.request("GET", path)
        print("## " + label)
        for it in items or []:
            extra = ""
            if "projectKey" in it:
                extra = "  key=" + it["projectKey"]
            if path.endswith("customFields"):
                extra = "  required=%s typeId=%s 選択肢=%s" % (it.get("required"), it.get("typeId"),
                                                            [(i["id"], i["name"]) for i in it.get("items", [])])
            print("  %s\t%s%s" % (it.get("id"), it.get("name"), extra))
    return EXIT_OK


# ───────── add ─────────

REQUIRED = ["projectId", "summary", "issueTypeId", "priorityId"]
MULTI = {"categoryId", "versionId", "milestoneId", "notifiedUserId", "attachmentId"}
OPTIONAL = {"parentIssueId", "description", "startDate", "dueDate", "estimatedHours", "actualHours", "assigneeId"} | MULTI


def read_csv(path, encoding):
    try:
        with open(path, "r", encoding=encoding, newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, UnicodeDecodeError) as e:
        raise UsageError("CSV を読めません（%s）。Excel の CSV なら --encoding cp932 を試してください。" % e)


def build_forms(rows, args):
    forms, problems = [], []
    defaults = {"projectId": args.project_id, "issueTypeId": args.issue_type_id, "priorityId": args.priority_id}
    for n, row in enumerate(rows, start=2):  # 1行目は見出し
        row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        form = []
        for k, v in row.items():
            if not v:
                continue
            base = k[:-2] if k.endswith("[]") else k
            if base in MULTI:
                for x in v.replace("；", ";").split(";"):
                    if x.strip():
                        form.append((base + "[]", x.strip()))
            elif base in OPTIONAL or base in REQUIRED or re.fullmatch(r"customField_\d+(_otherValue)?", base):
                form.append((base, v))
            else:
                problems.append("%d行目: 未対応の列 '%s'（無視せず止めます。綴りを確認）" % (n, k))
        have = {k for k, _ in form}
        for r in REQUIRED:
            if r not in have and defaults.get(r):
                form.append((r, defaults[r]))
                have.add(r)
            if r not in have:
                problems.append("%d行目: 必須の %s がありません（列で与えるか --%s で既定値を指定）" % (
                    n, r, {"projectId": "project-id", "issueTypeId": "issue-type-id", "priorityId": "priority-id", "summary": "csv の summary 列"}[r]))
        for k, v in form:
            if k in ("projectId", "issueTypeId", "priorityId") and not v.isdigit():
                problems.append("%d行目: %s は数字の ID です（名前ではなく ID。`meta` で調べる）: '%s'" % (n, k, v))
            if k in ("startDate", "dueDate") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                problems.append("%d行目: %s は yyyy-MM-dd 形式です: '%s'" % (n, k, v))
        forms.append(form)
    return forms, sorted(set(problems), key=problems.index)


def cmd_add(args):
    cl = load_client(args)
    rows = read_csv(args.csv, args.encoding)
    if not rows:
        raise UsageError("CSV にデータ行がありません。")
    forms, problems = build_forms(rows, args)
    if problems:
        for p in problems[:30]:
            print("エラー: " + p, file=sys.stderr)
        print("1件も送っていません。直してから再実行してください。", file=sys.stderr)
        return EXIT_USAGE
    print("登録予定: %d 件（POST %s）" % (len(forms), cl.url("/api/v2/issues")))
    for i, f in enumerate(forms[:5], start=1):
        print("  例%d: %s" % (i, urllib.parse.urlencode(f)[:200]))
    if args.dry_run:
        print("[dry-run] 通信しません。ヘッダー: %s" % cl.headers(masked=True))
        return EXIT_OK
    if not args.yes:
        print("送っていません。内容を確認して --yes を付けて再実行してください（登録した課題は API では取り消せません）。", file=sys.stderr)
        return EXIT_USAGE
    created = []
    for i, f in enumerate(forms, start=1):
        try:
            _, issue, _ = cl.request("POST", "/api/v2/issues", form=f)
        except ApiError as e:
            print("%d 行目（CSV 上は %d 行目）で失敗。登録済み %d 件: %s" % (i, i + 1, len(created), ",".join(created) or "なし"), file=sys.stderr)
            print(explain(e), file=sys.stderr)
            print("同じ CSV をそのまま再実行すると登録済みの分が重複します。失敗した行以降だけの CSV にしてください。", file=sys.stderr)
            return EXIT_FAIL
        created.append(issue.get("issueKey", str(issue.get("id"))))
    print("%d 件登録: %s" % (len(created), ",".join(created)))
    return EXIT_OK


# ───────── set-status ─────────

def cmd_set_status(args):
    cl = load_client(args)
    keys = [k.strip() for k in (args.keys or "").split(",") if k.strip()]
    if args.keys_file:
        try:
            with open(args.keys_file, encoding="utf-8") as f:
                keys += [l.strip() for l in f if l.strip()]
        except OSError as e:
            raise UsageError("キー一覧を読めません: %s" % e)
    if not keys:
        raise UsageError("--keys（例: PRJ-1,PRJ-2）か --keys-file（1行1キー）で課題キーを指定してください。")
    bad = [k for k in keys if not re.fullmatch(r"[A-Za-z0-9_]+-\d+|\d+", k)]
    if bad:
        raise UsageError("課題キーの形式が違います（例 PRJ-12 または課題ID）: %s" % bad[:5])
    if not args.status_id or not args.status_id.isdigit():
        raise UsageError("--status-id は数字の ID です。`meta --project-id <ID>` で状態の ID を調べてください。")
    form = [("statusId", args.status_id)]
    if args.resolution_id:
        form.append(("resolutionId", args.resolution_id))
    if args.comment:
        form.append(("comment", args.comment))
    print("変更予定: %d 件 -> %s（PATCH %s/api/v2/issues/<キー>）" % (len(keys), urllib.parse.urlencode(form), cl.base))
    print("  先頭: %s" % ",".join(keys[:5]))
    if args.dry_run:
        print("[dry-run] 通信しません。ヘッダー: %s" % cl.headers(masked=True))
        return EXIT_OK
    if not args.yes:
        print("送っていません。確認して --yes を付けて再実行してください（状態の変更は課題の履歴に残り、通知も飛びます）。", file=sys.stderr)
        return EXIT_USAGE
    done = []
    for k in keys:
        try:
            cl.request("PATCH", "/api/v2/issues/%s" % k, form=form)
        except ApiError as e:
            print("%s で失敗。変更済み %d 件: %s" % (k, len(done), ",".join(done) or "なし"), file=sys.stderr)
            print(explain(e), file=sys.stderr)
            print("変更済みの分は再実行しても同じ状態になるだけです（冪等）。", file=sys.stderr)
            return EXIT_FAIL
        done.append(k)
    print("%d 件を変更しました。" % len(done))
    return EXIT_OK


def build_parser():
    ap = argparse.ArgumentParser(description="Backlog API v2: 課題の取得・登録・ステータス変更（鍵は環境変数 BACKLOG_API_KEY）")
    ap.add_argument("--interval", type=float, default=1.0, help="リクエスト間隔の秒数（既定1.0。公式は一括処理で1秒以上を推奨）")
    ap.add_argument("--retry-wait", type=float, default=60.0, help="429 のとき待つ秒数（既定60。X-RateLimit-Reset があればそれを使う）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="課題を全件取得して CSV/JSON に出す")
    for attr, _ in FILTERS:
        f.add_argument("--" + attr.replace("_", "-"), help="ID（カンマ区切りで複数）")
    for attr, name in DATES:
        f.add_argument("--" + attr.replace("_", "-"), help=name + "（yyyy-MM-dd）")
    f.add_argument("--keyword")
    f.add_argument("--sort", default="created", help="既定 created（取得中の順序が安定する）")
    f.add_argument("--order", default="asc", choices=["asc", "desc"])
    f.add_argument("--max-issues", type=int, default=0, help="この件数で打ち切る（試し取り用）")
    f.add_argument("--count-only", action="store_true", help="件数だけ表示")
    f.add_argument("--format", choices=["csv", "json"], default="csv")
    f.add_argument("-o", "--output", help="出力先（省略か - で標準出力）")
    f.add_argument("--bom", action="store_true", help="CSV を BOM つき UTF-8 に（Excel で開く用）")
    f.add_argument("--dry-run", action="store_true")
    f.set_defaults(fn=cmd_fetch)

    m = sub.add_parser("meta", help="登録・更新に要る ID（優先度・状態・種別・カスタム属性）を一覧する（読み取りのみ）")
    m.add_argument("--project-id", help="プロジェクトID/キー。省略するとプロジェクト一覧")
    m.add_argument("--dry-run", action="store_true")
    m.set_defaults(fn=cmd_meta)

    a = sub.add_parser("add", help="CSV から課題を登録する（--yes 必須）")
    a.add_argument("--csv", required=True, help="列: projectId,summary,issueTypeId,priorityId（必須）＋ description,dueDate,assigneeId,categoryId(;区切り),customField_<id> など")
    a.add_argument("--encoding", default="utf-8-sig", help="Excel の CSV は cp932")
    a.add_argument("--project-id", help="CSV に列が無いときの既定値")
    a.add_argument("--issue-type-id")
    a.add_argument("--priority-id")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--yes", action="store_true", help="確認済み。これが無いと送らない")
    a.set_defaults(fn=cmd_add)

    s = sub.add_parser("set-status", help="課題のステータスを一括で変える（--yes 必須）")
    s.add_argument("--keys", help="課題キーをカンマ区切り（PRJ-1,PRJ-2）")
    s.add_argument("--keys-file", help="1行1キーのファイル")
    s.add_argument("--status-id", help="新しい状態のID（meta で調べる）")
    s.add_argument("--resolution-id", help="完了にするときの完了理由ID")
    s.add_argument("--comment", help="同時に付けるコメント")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_set_status)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except UsageError as e:
        print("引数・設定のエラー: %s" % e, file=sys.stderr)
        return EXIT_USAGE
    except ApiError as e:
        print(explain(e), file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())

=== FILE: scripts/selftest_mock.py ===
#!/usr/bin/env python3
"""backlog_issues.py をモックの Backlog で確かめる自己検証（本物には接続しない）。Python 3.9 以上・標準ライブラリだけ。

  python3 scripts/selftest_mock.py     # 全部通れば終了コード 0
"""
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "backlog_issues.py")
KEY = "MOCKKEY-should-never-appear-in-output"
TOTAL = 250
STATE = {"log": [], "rate_limited": False, "fail_post_at": None, "posts": 0}
ISSUES = [{"id": i, "issueKey": "PRJ-%d" % i, "projectId": 1, "summary": "課題,%d \"引用\"" % i,
           "status": {"id": 1, "name": "未対応"}, "priority": {"id": 3, "name": "中"},
           "issueType": {"id": 7, "name": "タスク"}, "assignee": None, "created": "2026-10-01T00:00:00Z",
           "customFields": [{"id": 5, "name": "顧客", "value": {"id": 9, "name": "株式会社テスト"}}],
           "description": "行1\n行2"} for i in range(1, TOTAL + 1)]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj, extra=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json;charset=utf-8")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        if self.headers.get("Backlog-API-Key") != KEY or "apiKey" in self.path:
            self._send(401, {"errors": [{"message": "Authenticate error", "code": 11, "moreInfo": ""}]})
            return False
        return True

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        STATE["log"].append(("GET", u.path, q))
        if not self._auth():
            return
        if u.path == "/api/v2/issues/count":
            return self._send(200, {"count": TOTAL})
        if u.path == "/api/v2/issues":
            if not STATE["rate_limited"]:
                STATE["rate_limited"] = True
                return self._send(429, {"errors": [{"message": "Too many requests.", "code": 13, "moreInfo": ""}]},
                                  {"X-RateLimit-Reset": "0"})
            off, cnt = int(q.get("offset", ["0"])[0]), int(q.get("count", ["20"])[0])
            if cnt > 100:
                return self._send(400, {"errors": [{"message": "count", "code": 7, "moreInfo": ""}]})
            return self._send(200, ISSUES[off:off + cnt])
        if u.path == "/api/v2/priorities":
            return self._send(200, [{"id": 2, "name": "高"}, {"id": 3, "name": "中"}, {"id": 4, "name": "低"}])
        if u.path == "/api/v2/projects/1/statuses":
            return self._send(200, [{"id": 1, "name": "未対応"}, {"id": 4, "name": "完了"}])
        if u.path == "/api/v2/projects/1/issueTypes":
            return self._send(200, [{"id": 7, "name": "タスク"}])
        if u.path == "/api/v2/projects/1/customFields":
            return self._send(200, [{"id": 5, "name": "顧客", "typeId": 6, "required": False, "items": [{"id": 9, "name": "A社"}]}])
        return self._send(404, {"errors": [{"message": "No resource.", "code": 6, "moreInfo": ""}]})

    def _form(self):
        n = int(self.headers.get("Content-Length", "0"))
        return urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"))

    def do_POST(self):
        STATE["log"].append(("POST", self.path, None))
        if not self._auth():
            return
        f = self._form()
        STATE["log"][-1] = ("POST", self.path, f)
        STATE["posts"] += 1
        if STATE["fail_post_at"] and STATE["posts"] == STATE["fail_post_at"]:
            return self._send(403, {"errors": [{"message": "no permission", "code": 5, "moreInfo": ""}]})
        if self.headers.get("Content-Type") != "application/x-www-form-urlencoded":
            return self._send(400, {"errors": [{"message": "ct", "code": 7, "moreInfo": ""}]})
        for r in ("projectId", "summary", "issueTypeId", "priorityId"):
            if r not in f:
                return self._send(400, {"errors": [{"message": "required " + r, "code": 7, "moreInfo": ""}]})
        self._send(201, {"id": 1000 + STATE["posts"], "issueKey": "PRJ-%d" % (1000 + STATE["posts"])})

    def do_PATCH(self):
        f = self._form()
        STATE["log"].append(("PATCH", self.path, f))
        if not self._auth():
            return
        self._send(200, {"id": 1, "issueKey": self.path.rsplit("/", 1)[-1]})


def main():
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    env = dict(os.environ, BACKLOG_SPACE="127.0.0.1:%d" % srv.server_port, BACKLOG_TEST_HTTP="1", BACKLOG_API_KEY=KEY)
    tmp = tempfile.mkdtemp()
    results = []

    def run(args, env_=None, **kw):
        p = subprocess.run([sys.executable, "-I", SCRIPT, "--interval", "0", "--retry-wait", "0"] + args,
                           env=env_ or env, capture_output=True, **kw)
        return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")

    def check(name, cond):
        results.append(cond)
        print(("OK   " if cond else "NG   ") + name)

    # 1. dry-run: 通信ゼロ・鍵なし
    STATE["log"].clear()
    rc, out, err = run(["fetch", "--dry-run"])
    check("fetch --dry-run は通信しない・終了0", rc == 0 and not STATE["log"])
    check("dry-run に鍵が出ない", KEY not in out + err and "＊＊＊＊" in out)
    env_nokey = {k: v for k, v in env.items() if k != "BACKLOG_API_KEY"}
    rc, out, err = run(["fetch", "--dry-run"], env_nokey)
    check("鍵が無くても dry-run は通る", rc == 0)
    rc, out, err = run(["fetch"], env_nokey)
    check("鍵が無い本番実行は終了2", rc == 2 and "BACKLOG_API_KEY" in err)

    # 2. 全件取得 250 件を 100/100/50 で、429 を 1 回再試行
    out_csv = os.path.join(tmp, "o.csv")
    STATE["log"].clear()
    rc, out, err = run(["fetch", "-o", out_csv, "--bom"])
    gets = [l for l in STATE["log"] if l[1] == "/api/v2/issues"]
    check("終了0", rc == 0)
    check("429 を再試行して 100/100/50 の計4回（429 1回＋3ページ）", len(gets) == 4)
    check("offset が 0,0(再試行),100,200", [l[2]["offset"][0] for l in gets] == ["0", "0", "100", "200"])
    check("count=100 を送る", all(l[2]["count"][0] == "100" for l in gets))
    check("鍵は URL ではなくヘッダー（apiKey がパスに無い）", all("apiKey" not in l[2] for l in gets))
    raw = open(out_csv, "rb").read()
    check("BOM つき UTF-8", raw.startswith(b"\xef\xbb\xbf"))
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    check("250 行・重複なし", len(rows) == TOTAL and len({r["id"] for r in rows}) == TOTAL)
    check("カンマ・引用符・改行が壊れない", rows[0]["summary"] == '課題,1 "引用"' and rows[0]["description"] == "行1\n行2")
    check("カスタム属性が列になる", rows[0].get("カスタム:顧客") == "株式会社テスト")
    check("出力に鍵が出ない", KEY not in out + err)

    # 3. count-only・max-issues
    rc, out, err = run(["fetch", "--count-only"])
    check("--count-only は件数だけ", rc == 0 and out.strip() == str(TOTAL))
    STATE["log"].clear()
    rc, out, err = run(["fetch", "--max-issues", "120", "--format", "json", "-o", os.path.join(tmp, "o.json")])
    check("--max-issues 120 で打ち切り", rc == 0 and len(json.load(open(os.path.join(tmp, "o.json")))) == 120)

    # 4. 認証エラーの説明
    rc, out, err = run(["fetch", "--count-only"], dict(env, BACKLOG_API_KEY="wrong"))
    check("401 は終了1・原因の案内・鍵を出さない", rc == 1 and "認証" in err and "wrong" not in err)

    # 5. スペース形式
    rc, out, err = run(["fetch", "--dry-run"], dict(env, BACKLOG_SPACE="example.invalid.com", BACKLOG_TEST_HTTP=""))
    check("不正なホストは終了2", rc == 2 and "backlog.com" in err)
    rc, out, err = run(["fetch", "--dry-run"], dict(env, BACKLOG_SPACE="https://example.backlog.jp/", BACKLOG_TEST_HTTP=""))
    check(".backlog.jp も受け付ける", rc == 0 and "example.backlog.jp" in out)

    # 6. meta
    rc, out, err = run(["meta", "--project-id", "1"])
    check("meta は優先度と状態を出す", rc == 0 and "高" in out and "完了" in out and "customField" in out and "A社" in out)

    # 7. add
    good = os.path.join(tmp, "good.csv")
    with open(good, "w", encoding="utf-8", newline="") as f:
        f.write("summary,description,categoryId,dueDate\nA,説明,1;2,2026-11-01\nB,,,\nC,,,\n")
    STATE["log"].clear()
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3"])
    check("--yes なしは送らず終了2", rc == 2 and not [l for l in STATE["log"] if l[0] == "POST"])
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--dry-run"])
    check("add --dry-run は送らない", rc == 0 and not STATE["log"])
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--yes"])
    posts = [l for l in STATE["log"] if l[0] == "POST"]
    check("3 件登録", rc == 0 and len(posts) == 3)
    check("categoryId[] を複数で送る", posts[0][2]["categoryId[]"] == ["1", "2"])
    check("必須4つが全部付く", all(k in posts[1][2] for k in ("projectId", "summary", "issueTypeId", "priorityId")))
    bad = os.path.join(tmp, "bad.csv")
    with open(bad, "w", encoding="utf-8") as f:
        f.write("summary,priority\nA,高\nB,中\n")
    STATE["log"].clear()
    rc, out, err = run(["add", "--csv", bad, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--yes"])
    check("未対応の列は1件も送らず終了2", rc == 2 and "priority" in err and not STATE["log"])
    rc, out, err = run(["add", "--csv", bad.replace("bad", "x"), "--yes"])
    check("存在しない CSV は終了2", rc == 2)
    nores = os.path.join(tmp, "nores.csv")
    with open(nores, "w", encoding="utf-8") as f:
        f.write("summary\nA\n")
    rc, out, err = run(["add", "--csv", nores, "--yes"])
    check("必須 ID 不足は送らず終了2", rc == 2 and "projectId" in err)
    STATE["posts"], STATE["fail_post_at"] = 0, 2
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--yes"])
    check("途中失敗は終了1・登録済みと重複を案内", rc == 1 and "登録済み 1 件" in err and "重複" in err and "権限" in err)
    STATE["fail_post_at"] = None

    # 8. set-status
    STATE["log"].clear()
    rc, out, err = run(["set-status", "--keys", "PRJ-1,PRJ-2", "--status-id", "4"])
    check("set-status は --yes なしで送らない", rc == 2 and not STATE["log"])
    rc, out, err = run(["set-status", "--keys", "PRJ-1,PRJ-2", "--status-id", "4", "--comment", "一括完了", "--yes"])
    pt = [l for l in STATE["log"] if l[0] == "PATCH"]
    check("2 件を PATCH・statusId とコメント", rc == 0 and len(pt) == 2 and pt[0][2]["statusId"] == ["4"] and pt[0][2]["comment"] == ["一括完了"])
    rc, out, err = run(["set-status", "--keys", "bad key!", "--status-id", "4", "--yes"])
    check("不正なキーは終了2", rc == 2)

    srv.shutdown()
    print("\n%d/%d 合格" % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

=== FILE: LICENSE ===
MIT License

Copyright (c) 2026 frametech

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
