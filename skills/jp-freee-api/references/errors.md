# freee API のエラーと次の手

確認日 2026-10-22。**確認日から90日を過ぎたら、公式を読み直してから使う。**

出典: https://developer.freee.co.jp/reference/40x-checkpoint （HTTP 40x系エラー）、https://developer.freee.co.jp/reference/faq/token_lifetime 、OpenAPI スキーマ（accounting.md 冒頭）

公式の注意: 新しいエラーコードやメッセージの変更は予告なく入る。**特定の code だけでなく、未知の code でも動き続ける作りにする**（4xx として一括処理するなど）。

## 形式

```json
{"status_code": 401, "errors": [{"type": "status", "messages": ["…"], "codes": ["expired_access_token"]}]}
```
`type` は `status`（HTTP ステータスの説明）か `validation`（入力の不備の詳細。開発者向け）。トークン不正のときは `{"message": "ログインをして下さい", "code": "invalid_access_token"}` の形になる。ステータスコードは本文にもヘッダーにも入る。

## 401 と 403

| 症状・code | 原因 | 次の手 |
|---|---|---|
| 401 `expired_access_token` | アクセストークンが6時間を過ぎた | リフレッシュトークンで取り直す（auth.md §1 手順5）。保存した新しいトークンで再実行 |
| 401 `invalid_access_token` | トークンが誤り・失効・書式違い | `Authorization: Bearer ` の綴り、前後の空白・改行、revoke 済みでないかを確認。分からなければ再認可 |
| 401 `user_do_not_have_permission` | トークンのユーザーに、その機能の権限が無い | freee の管理画面で、メンバーの権限割り当てを事業所の管理者に確認してもらう |
| 401 `company_not_found` | `company_id` が存在しない・削除済み | `GET /api/1/companies` で id を引き直す（`company_number` と取り違えていないか） |
| 401 `freee_plan_limit` | 有料プラン限定の API を、対象外のプランの事業所で呼んだ | 契約プランを確認（accounting.md §6） |
| 401 `source_ip_address_limit` | 事業所のIP制限（エンタープライズ）に接続元が入っていない | 事業所のシステム管理者にIP制限の解除・許可を依頼 |
| 401 `re_authorization_required` | アプリの権限を広げたので再認可が必要（ストア公開アプリ） | 利用者にもう一度認可してもらう |
| `invalid_grant`（公式の表では 401 の欄。トークン取得・更新で出る） | 認可コード・リフレッシュトークンが不正・期限切れ・使用済み、`redirect_uri` 不一致、別アプリのもの | `client_id/secret` を確認。リフレッシュを**二重に送っていない**か（リトライで2回送るのが典型）、更新前のトークンを revoke していないかを確認。直らなければ再認可 |
| 403（本文にアプリの権限不足） | アプリの権限設定でそのデータ種別（参照／更新）にチェックが無い | アプリ管理の権限設定を直し、**トークンを取り直す** |
| 403（権限は足りている） | 過度のアクセスによる制限 | 約10分待つ。連続呼び出しの間に待ちを入れる |

## その他

| 症状 | 原因 | 次の手 |
|---|---|---|
| 400 | パラメータ不正。日付は `yyyy-mm-dd`、`limit` はエンドポイントの上限内、必須の `company_id` | `validation` の `messages` を読む |
| 404 | リソースやパスが違う、事業所に存在しない ID | ID とパスを確認 |
| 429 | `/reports` か `/receipts/{id}/download` を短時間に呼びすぎ | `x-ratelimit-reset` の時刻まで待つ。ほかの API では通常出ない（403 を疑う） |
| 500 | freee 側の障害 | 時間をおいて再実行。直らなければ `X-Freee-Request-ID` を添えて問い合わせ（https://developer.freee.co.jp/reference の障害・インシデント報告フォーム） |

エラーを報告するときは、`X-Freee-Request-ID`、エンドポイント、HTTP ステータス、`code` を添える。**トークン・Client Secret・事業所のデータは貼らない。**
