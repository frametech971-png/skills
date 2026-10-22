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
