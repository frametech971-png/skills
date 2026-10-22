# freee 会計 API：取引・事業所・マスタ

確認日 2026-10-22。**確認日から90日を過ぎたら、下の公式を読み直してから使う。**

出典
- freee会計 API の OpenAPI スキーマ（freee 公式 GitHub）: https://github.com/freee/freee-api-schema （`v2020_06_15/open-api-3/api-schema.json`、コミット ac1acd4、2026-10-21 更新分を 2026-10-22 に取得）。公式のリファレンスページ https://developer.freee.co.jp/reference/accounting/reference はこのスキーマを描画したもの。
- 最初の GET/POST: https://developer.freee.co.jp/startguide/first-call

## 1. 基本

| 項目 | 内容 |
|---|---|
| ベースURL | `https://api.freee.co.jp`（https のみ）。パスは `/api/1/…` |
| 認証 | `Authorization: Bearer {access_token}`（認証は auth.md） |
| 形式 | リクエスト・応答とも JSON。POST は `Content-Type: application/json` |
| 応答ヘッダー | `X-Freee-Request-ID`（リクエストごとのID。問い合わせのとき控える） |
| 互換性 | 新しい項目やエンドポイントの追加、エラーメッセージの変更は予告なく入る。**未知の項目を無視し、エラーは `code` で分岐してメッセージ文には依存しない** |

## 2. 事業所 `GET /api/1/companies`

アクセストークンのユーザーが所属する事業所の一覧。`companies[]` に `id`（これが `company_id`）・`name`・`display_name`・`company_number`・`role`。会計年度などの詳細は `GET /api/1/companies/{id}`。

## 3. 取引の取得 `GET /api/1/deals`

| パラメータ | 内容 |
|---|---|
| `company_id` | **必須**。事業所ID |
| `start_issue_date` / `end_issue_date` | 発生日の範囲（`yyyy-mm-dd`） |
| `start_due_date` / `end_due_date` | 支払期日の範囲 |
| `start_renew_date` / `end_renew_date` | +更新日の範囲 |
| `type` | `income`（収入）／`expense`（支出） |
| `status` | `unsettled`（未決済）／`settled`（完了） |
| `partner_id` / `partner_code` | 取引先で絞る（同時指定は不可。`partner_code` は事業所設定で取引先コードを有効にしたときだけ） |
| `account_item_id` | 勘定科目IDで絞る |
| `min_due_amount` | 支払残額の下限（円） |
| `accruals` | `with` で債権債務行も返す（既定 `without`） |
| `offset` | 取得開始位置（既定 0） |
| `limit` | 件数（**既定 20、最大 100**） |

応答: `{"deals": […], "meta": {"total_count": 合計件数}}`。各取引に `id`・`issue_date`・`due_date`・`amount`・`due_amount`・`type`・`partner_id`・`ref_number`・`status`・`details[]`（明細行: `id`・`account_item_id`・`tax_code`・`amount`・`vat`・`description` ほか）・`payments[]` など。

**ページング**: `offset` を取得済み件数ずつ進め、`offset >= meta.total_count` か空のページで終わる。月別に集計したいときは期間を `start_issue_date`〜`end_issue_date` で月ごとに切るか、`issue_date` の先頭7文字で束ねる。`scripts/freee_deals.py` がこれを行う。

セグメントタグ（`segment_*`）は法人アドバンス以上のプランだけ（§6）。

## 4. 取引の登録 `POST /api/1/deals`（書き込み。実行前に必ず確認を取る）

必須: ボディの `company_id`・`issue_date`・`type`・`details`。`details[]` の必須は `tax_code` と `amount`（**最大100行**）。実用上は `account_item_id` も入れる。主な任意: `due_date`・`partner_id`・`ref_number`・`payments[]`（支払済みにするとき）・`receipt_ids`。

```json
{"company_id": 12345, "issue_date": "2026-10-01", "type": "expense",
 "details": [{"tax_code": 136, "account_item_id": 1001, "amount": 1100, "description": "文房具"}]}
```
（数値はすべて例。実際の `tax_code` は `GET /api/1/taxes/codes` 、`account_item_id` は `GET /api/1/account_items?company_id=…` で調べる。）

- `amount` は**税込金額**（公式のスタートガイドの例: 1,000円の文具を税込1,100円で登録）。
- `account_item_code` `item_code` `section_code` `partner_code` は、事業所の設定でコードの利用を有効にしたときだけ使え、対応する `*_id` との同時指定はできない。
- 応答は 201。**同じリクエストを再送すると取引が重複しうる**（公式の仕様に重複防止の仕組みは書かれていない）。送る前に `ref_number` などで既存を確認する。
- `+更新行`（renews）はこの API では操作できない（別の「+更新」API）。

## 5. マスタ

| 目的 | エンドポイント | 備考 |
|---|---|---|
| 勘定科目 | `GET /api/1/account_items?company_id=` | `keyword`・`base_date` で絞る。`id` が `account_item_id` |
| 取引先 | `GET /api/1/partners?company_id=` | `offset`・`limit`（**既定 50、最大 3000**）・`keyword` |
| 税区分 | `GET /api/1/taxes/codes` | `code` が `tax_code` |

エンドポイントごとに `limit` の上限が違う（取引は100、取引先は3000）。1つの値を使い回さない。

## 6. 使用制限・プラン

出典は §冒頭のスキーマの説明文（公式の API 仕様）。

- **一定期間に過度のアクセスを検知すると、HTTP 403 が返り、約10分で再び使える。**
- **`/reports` と `/receipts/{id}/download` だけ**は HTTP 429（too many requests）で、`/reports` は1秒10回まで、`/receipts/{id}/download` は1秒3回まで。429 のとき応答ヘッダーに `x-ratelimit-limit`（上限）・`x-ratelimit-remaining`（残り）・`x-ratelimit-reset`（リセット時刻）が付く。
- **1日のAPIコール数の上限**（事業所とアプリケーションごと）: 法人エンタープライズプラン 10,000／法人アドバンスプラン（旧法人プロフェッショナルを含む）5,000／上記以外 3,000。超えたときの応答は公式に書かれていない（要確認）。
- 取引・事業所・マスタの API は、freee 会計の Web 版で使える機能と同じ範囲で使える。**例外**: 総勘定元帳 API は旧法人プロフェッショナル・旧法人エンタープライズ・法人アドバンス・新法人エンタープライズ、固定資産台帳 API は旧法人エンタープライズ・新法人エンタープライズのみ。プラン不足は 401 `freee_plan_limit`。

**つまり「リクエストが多すぎる」と言われたとき**: 通常の API では 429 ではなく **403**（10分待つ）か、1日の上限超え。429 が出るのは `/reports` と証憑ダウンロードだけ。ループで連続して呼んでいるなら、ページ間に待ちを入れ、`limit` を最大にして回数を減らす。
