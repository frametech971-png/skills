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
