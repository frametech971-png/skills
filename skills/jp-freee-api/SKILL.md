---
name: jp-freee-api
description: >-
  freee 会計の API（OAuth2 認証、事業所ID、取引・勘定科目・取引先の取得と登録）を使うコードを書く、取引を期間指定で取得して CSV にする、認証やエラーの原因を調べる。「freee の取引を月別に取得して CSV にして」「freee API のアクセストークンの取り方と更新」「company_id がわからない」「取引を API で登録したい」「401 や 403 が出る・リクエストが多すぎると言われる」と頼まれたときに使う。Keywords: freee accounting API, deals, OAuth2 access token, refresh token, company_id, rate limit。トークンの期限（アクセス6時間・リフレッシュ90日）や上限は公式で確認した値を使う。鍵は環境変数から読み、コードや会話に書かない。仕訳・税務の判断、freee 人事労務・請求書など他製品の API、会計ソフトの使い方の質問は対象外。
license: MIT
compatibility: "scripts/freee_deals.py は Python 3.9 以上（標準ライブラリのみ）。freee の API に通信できる環境が必要。通信できない環境では --dry-run で出る内容を手元で実行してもらう。"
metadata:
  version: "1.0.0"
  author: frametech
---

# freee 会計 API

目的: freee 会計の API を使うコードの作成、取引データの取得（CSV／JSON）、認証とエラーの原因調べ。
入力: やりたいこと（取得・登録・認証・エラー）。取得なら期間と絞り込み。エラーなら HTTP ステータスと `code`。
出力: 実行できるコードか、取得した CSV／JSON、または原因と次の手。鍵そのものは出力に含めない。

公式の値（トークンの期限・上限・エンドポイント）は変わる。[references/](references/) の確認日（2026-10-22）から90日を過ぎたら、各ファイルの出典 URL（developer.freee.co.jp）を読み直してから答える。

## 前提

- freee のアプリを作ってあること（Client ID/Secret）。無ければ [references/auth.md](references/auth.md) §4 の手順を案内する。試すだけなら公式の開発用テスト事業所が使える。
- 環境変数: `FREEE_ACCESS_TOKEN`（アクセストークン。**6時間**で切れる）、`FREEE_COMPANY_ID`（事業所ID）。
- **鍵（Client Secret・アクセストークン・リフレッシュトークン）をコード・引数・ファイル・会話に書かない。** ユーザーが貼ってきても、コードには `os.environ` で読む形だけを書き、値を書き写さない。貼られたら「そのトークンは無効化（revoke）して取り直すのが安全」と伝える。

## 手順

1. 依頼を分ける: (a) 取引を取得する (b) コードを書く（認証・取得・登録）(c) エラー・認証の原因を調べる (d) `company_id` を知りたい。
2. (a) は `scripts/freee_deals.py` を使う。まず `--dry-run` で送る内容と環境変数の有無を確かめ、そのあと本番。

   ```bash
   python3 scripts/freee_deals.py --start 2026-04-01 --end 2026-09-30 --dry-run
   python3 scripts/freee_deals.py --start 2026-04-01 --end 2026-09-30 --out deals.csv
   python3 scripts/freee_deals.py --start 2026-10-01 --end 2026-10-31 --type expense --format json
   ```

   全ページ（1ページ100件）を取得して、CSV は明細行ごとに1行（`month` 列つきなので月別に集計できる）。`--rows deal` で取引ごとの1行、`--bom` で Excel 向けの BOM。429・5xx・通信エラーは待って再試行する。読み取り専用で、取引は変更しない。実行できない環境では、[references/accounting.md](references/accounting.md) §3 のとおりに URL とヘッダーを組み立てて示し、手元で実行してもらう。
3. (b) は references を読んでから書く。必ず守る点:
   - 認証は [references/auth.md](references/auth.md)。API には `Authorization: Bearer …`。アクセストークンは6時間、リフレッシュトークンは90日で、**リフレッシュトークンは1回しか使えない**（更新のたびに新しいものを保存。リトライで二重に送らない）。
   - ベース URL は `https://api.freee.co.jp`。取引の取得は `limit` 最大100、`offset` で進め `meta.total_count` で終わる。
   - 呼び出しの間隔を空ける。通常の API の制限超過は **403（約10分で解除）**、**429 が出るのは `/reports` と証憑ダウンロードだけ**（[references/accounting.md](references/accounting.md) §6）。
4. **取引の登録（POST）は書き込み。** 実行する前に、送る内容（日付・金額・勘定科目・税区分）を示してユーザーの承認を取る。金額は税込。再送すると重複しうるので、実行済みかを確かめてから再実行する。試すのはテスト事業所で。仕訳や税区分が正しいかの判断はしない（会計の担当者に確認してもらう）。
5. (c)(d) は [references/errors.md](references/errors.md) の表に HTTP ステータスと `code` を当てて、原因と次の手を返す。`company_id` は `GET /api/1/companies` の `id`（`company_number` ではない）か、トークン取得時の応答の `company_id`。

## 出力の例

```text
month,deal_id,issue_date,due_date,type,status,partner_id,ref_number,deal_amount,due_amount,detail_id,account_item_id,tax_code,detail_amount,vat,item_id,section_id,description
2026-04,123456789,2026-04-03,,expense,settled,111,,1100,0,987654321,222,136,1100,100,,,文房具
```

（値は架空の例。実行結果は stderr に「N ページ目: 累計 M 件」と最終件数が出る。件数が `meta.total_count` と合わないときは注意が出る。）

## 実行環境が無いとき・確認できていないこと

- `scripts/freee_deals.py` を実行できない環境では、手順2のとおりリクエストを組み立てて示し、結果を貼ってもらえば集計する。
- 実アカウントでの動作は確認していない。スクリプトは公式のスキーマに沿った模擬サーバーで、ページ送りと429の再試行まで確かめてある。
- 認可コードの有効期限、1日の上限を超えたときの応答は、公式に数値・形式が見つからなかった（要確認）。推測で答えず、公式のページを示す。
