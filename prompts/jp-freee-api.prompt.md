<!-- jp-freee-api v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-freee-api（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
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

=== FILE: references/accounting.md ===
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

=== FILE: references/auth.md ===
# freee API の認証（OAuth2）とトークン

確認日 2026-10-22。**確認日から90日を過ぎたら、下の公式ページを読み直してから使う。**

出典（すべて freee 公式の開発者サイト、2026-10-22 に取得）
- 認可の概要: https://developer.freee.co.jp/reference/%e8%aa%8d%e5%8f%af%e3%82%b3%e3%83%bc%e3%83%89
- アクセストークンを取得する: https://developer.freee.co.jp/startguide/getting-access-token
- トークンの有効期限について: https://developer.freee.co.jp/reference/faq/token_lifetime
- 【重要】リフレッシュトークンの有効期限の変更（2023-05-30 のお知らせ）: https://developer.freee.co.jp/news/6540
- 事業所の選択について: https://developer.freee.co.jp/reference/select-company
- アプリタイプ: https://developer.freee.co.jp/reference/application-types

## 1. 流れ（認可コードフロー。公式が推奨）

1. アプリを作る（freeeアプリストアの開発者向けアプリ管理）。**Client ID と Client Secret** が出る。コールバックURLを設定する。ローカルの試験だけ `urn:ietf:wg:oauth:2.0:oob`（画面に認可コードが表示される）。それ以外は自分の https URL にする（公式の注意）。
2. 認可URLをブラウザで開く（アプリ管理画面の「基本設定」に表示される）。ユーザーがログインして「許可する」を押すと認可コードが出る:
   `https://accounts.secure.freee.co.jp/public_api/authorize?response_type=code&client_id={client_id}&redirect_uri={エンコードしたコールバックURL}&state={ランダム文字列}&prompt=select_company`
   `state` は戻ってきた値と一致するか必ず確かめる（CSRF 対策）。
3. 認可コードをアクセストークンに換える:
   ```
   POST https://accounts.secure.freee.co.jp/public_api/token
   Content-Type: application/x-www-form-urlencoded
   grant_type=authorization_code&client_id=…&client_secret=…&code=…&redirect_uri=…
   ```
   応答: `access_token` / `token_type: bearer` / `expires_in: 21600` / `refresh_token` / `scope` / `created_at` / `company_id` / `external_cid`
4. API には `Authorization: Bearer {access_token}` を付けて呼ぶ。
5. 期限前に更新する:
   ```
   POST https://accounts.secure.freee.co.jp/public_api/token
   grant_type=refresh_token&client_id=…&client_secret=…&refresh_token=…
   ```
6. 失効させる: `POST https://accounts.secure.freee.co.jp/public_api/revoke`（`token=` にアクセストークンかリフレッシュトークン）。

## 2. 有効期限

| もの | 期限 | 出典 |
|---|---|---|
| アクセストークン | **6時間**（`expires_in: 21600`） | token_lifetime / getting-access-token |
| リフレッシュトークン | **発行後90日**（2023-12 頃に「期限なし」から変更） | token_lifetime / news/6540 |
| 認可コード | **要確認**（公式ページで数値を確認できなかった。短時間で、1回しか使えない前提で扱う） | — |

**リフレッシュトークンは1回しか使えない。** 更新するたびに新しいリフレッシュトークンが返るので、その都度保存し直す。同じものを2回使うと `invalid_grant`／401 になる（リトライで二重に送る・更新前のアクセストークンを revoke した、が典型）。90日以内に1回は更新しないと再認可になる。

注意: アクセストークン取得ページの本文に「リフレッシュトークンには有効期限はありません」という古い記述が残っている（同じページに「90日に変更される予定」とも書いてある）。**FAQ とお知らせの「90日」を正とする。** ネット上の古い記事（アクセストークン24時間・リフレッシュ無期限）も採らない。

## 3. 事業所ID（company_id）

- 認可URLに `prompt=select_company` を付けた（既定の）場合、**トークン応答に `company_id` が入る**。トークンと一緒に保存する。
- 後から調べる: `GET https://api.freee.co.jp/api/1/companies`（`Authorization: Bearer …`）。応答の `companies[].id` が、他の API の `company_id` に渡す値。`company_number`（10桁の英数字）は別物で、API の `company_id` には使えない。
- `prompt=select_company` を外した認可だと、そのユーザーが所属する**全事業所**にアクセスできるが、アプリ側で事業所を選ばせる実装が必須（アプリストア公開時の審査項目）。既定のままが公式推奨。

## 4. アプリ登録・利用の前提

- freee のアカウントがあり、**従業員として所属する事業所**でアプリを作る（顧問先として招待されただけの事業所では作れない）。アプリ名と概要を入れると Client ID/Secret が出る。
- アプリタイプは**作成後に変えられない**: プライベートアプリ（特定事業所用。利用事業所は5以下。ストア掲載不可）／パブリックアプリ（配布用。既定で20事業所以下、ストア公開か申請で無制限）。自社の事業所だけで使うならプライベート。
- 開発用テスト事業所と無料の開発者アカウントがある（freee 公式のスタートガイド https://developer.freee.co.jp/startguide ）。本番データに触れずに試せる。
- アプリの「権限設定」で、使うデータ（取引の参照・更新など）にチェックを入れる。権限を変えたら**トークンを取り直す**（古いトークンは古い権限のまま）。
- **鍵（Client Secret・アクセストークン・リフレッシュトークン）をコード・Git・チャットに書かない。** 環境変数か秘密情報の保管庫から読む。保存したリフレッシュトークンの読み書きは、書き込みが失敗しても古い値が消えない順序（新しい値を書いてから古い値を捨てる）にする。

=== FILE: references/errors.md ===
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

=== FILE: scripts/freee_deals.py ===
#!/usr/bin/env python3
"""freee 会計 API の取引（GET /api/1/deals）を期間指定で全ページ取得し、CSV / JSON に出す。

Python 3.9 以上・標準ライブラリだけ。通信先は api.freee.co.jp だけ（--base-url で変えられるのは試験用）。
読み取り専用（GET だけ）。取引の登録・更新・削除はしない。

使い方:
  python3 scripts/freee_deals.py --start 2026-04-01 --end 2026-09-30 --dry-run   # 送らずに、送る内容だけ出す
  python3 scripts/freee_deals.py --start 2026-04-01 --end 2026-09-30 --out deals.csv
  python3 scripts/freee_deals.py --start 2026-10-01 --end 2026-10-31 --type expense --format json

環境変数（引数やファイルに鍵を書かない）:
  FREEE_ACCESS_TOKEN  必須。アクセストークン（有効期限は6時間。切れたらリフレッシュトークンで取り直す）
  FREEE_COMPANY_ID    必須。事業所ID（GET /api/1/companies の id、またはトークン取得時の company_id）

CSV は明細行（details）ごとに1行。取引だけで足りるときは --rows deal。
終了コード: 0 成功 / 1 API・通信のエラー / 2 使い方・設定の誤り
"""

import argparse
import csv
import datetime
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.freee.co.jp"
PATH = "/api/1/deals"
MAX_LIMIT = 100  # GET /api/1/deals の limit の最大（公式スキーマ）

DEAL_COLS = ["month", "deal_id", "issue_date", "due_date", "type", "status", "partner_id",
             "ref_number", "deal_amount", "due_amount"]
DETAIL_COLS = ["detail_id", "account_item_id", "tax_code", "detail_amount", "vat",
               "item_id", "section_id", "description"]


def die(msg, code=2):
    print("エラー: " + msg, file=sys.stderr)
    sys.exit(code)


def parse_date(s, name):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        die("%s は YYYY-MM-DD の形で指定してください（受け取った値: %s）" % (name, s))


def build_parser():
    p = argparse.ArgumentParser(
        description="freee 会計の取引（deals）を期間指定で全ページ取得して CSV / JSON に出す（読み取り専用）。",
        epilog="環境変数 FREEE_ACCESS_TOKEN と FREEE_COMPANY_ID が必要。鍵は引数に渡さない。")
    p.add_argument("--start", required=True, help="発生日の開始 YYYY-MM-DD（start_issue_date）")
    p.add_argument("--end", required=True, help="発生日の終了 YYYY-MM-DD（end_issue_date）")
    p.add_argument("--type", choices=["income", "expense"], help="収支区分で絞る")
    p.add_argument("--status", choices=["settled", "unsettled"], help="決済状況で絞る")
    p.add_argument("--partner-id", type=int, help="取引先IDで絞る")
    p.add_argument("--account-item-id", type=int, help="勘定科目IDで絞る")
    p.add_argument("--format", choices=["csv", "json"], default="csv", help="出力形式（既定 csv）")
    p.add_argument("--rows", choices=["detail", "deal"], default="detail",
                   help="CSV の1行の単位。detail=明細行ごと（既定）、deal=取引ごと")
    p.add_argument("--out", help="出力ファイル。省略すると標準出力。既存ファイルは上書きしない（--force で上書き）")
    p.add_argument("--force", action="store_true", help="--out の既存ファイルを上書きする")
    p.add_argument("--bom", action="store_true", help="CSV の先頭に BOM を付ける（Excel で文字化けするとき）")
    p.add_argument("--limit", type=int, default=MAX_LIMIT, help="1ページの件数 1〜100（既定 100）")
    p.add_argument("--max-pages", type=int, default=500, help="安全のためのページ数の上限（既定 500）")
    p.add_argument("--interval", type=float, default=0.3, help="ページ間の待ち秒（既定 0.3）")
    p.add_argument("--retries", type=int, default=5, help="429・5xx・通信エラーの再試行回数（既定 5）")
    p.add_argument("--backoff", type=float, default=1.0, help="再試行の待ち秒の基準（1,2,4…倍。既定 1.0）")
    p.add_argument("--base-url", default=DEFAULT_BASE, help="試験用。https 以外は localhost / 127.0.0.1 のみ可")
    p.add_argument("--dry-run", action="store_true", help="送らずに、送る URL と環境変数の有無だけ出す")
    return p


def check_base(base):
    u = urllib.parse.urlparse(base)
    if u.scheme == "https":
        return
    if u.scheme == "http" and u.hostname in ("localhost", "127.0.0.1"):
        return
    die("--base-url は https:// で指定してください（http は localhost / 127.0.0.1 のみ）")


def explain_http(status, body):
    """HTTP エラーの原因と次の手を1〜3行で返す。本文は秘密を含まない前提で一部だけ載せる。"""
    codes, msgs = [], []
    try:
        j = json.loads(body)
        if isinstance(j, dict):
            if j.get("code"):
                codes.append(str(j["code"]))
            if j.get("message"):
                msgs.append(str(j["message"]))
            for e in j.get("errors") or []:
                codes.extend(str(c) for c in e.get("codes") or [])
                msgs.extend(str(m) for m in e.get("messages") or [])
    except ValueError:
        pass
    code_s = ",".join(codes) if codes else "-"
    hint = {
        400: "パラメータが不正です。日付は YYYY-MM-DD、limit は 1〜100、company_id は数値か確認してください。",
        401: "認証に失敗しました。",
        403: "権限がありません、または短時間にアクセスしすぎです。",
        404: "事業所IDかパスが違います。company_id を GET /api/1/companies で確認してください。",
        500: "freee 側のエラーです。時間をおいて再実行してください。",
    }.get(status, "想定外のエラーです。")
    if "expired_access_token" in codes:
        hint = ("アクセストークンの有効期限切れ（6時間）です。リフレッシュトークンで取り直し、"
                "FREEE_ACCESS_TOKEN を更新して再実行してください。")
    elif "invalid_access_token" in codes or status == 401:
        hint += " トークンが誤り・失効、または company_id のアプリに認可されていない可能性があります。"
    elif "freee_plan_limit" in codes:
        hint = "この事業所のプランでは使えない API です。契約プランを確認してください。"
    elif "company_not_found" in codes:
        hint = "事業所IDが存在しないか削除済みです。FREEE_COMPANY_ID を確認してください。"
    elif "user_do_not_have_permission" in codes:
        hint = "ログインしたユーザーの権限が足りません。事業所の管理者に権限割り当てを確認してください。"
    elif status == 403:
        hint = ("403 は①アプリの権限設定（取引の参照）が足りない ②過度のアクセスによる制限（約10分で解除）"
                "のどちらかです。①はアプリ管理の権限設定を直してトークンを取り直し、②は10分待ってください。")
    msg = (" / ".join(msgs))[:200]
    return "HTTP %d（code: %s）%s\n  → %s" % (status, code_s, (" " + msg) if msg else "", hint)


def wait_seconds(headers, attempt, base):
    ra = headers.get("Retry-After")
    if ra:
        try:
            return max(0.0, min(float(ra), 120.0))
        except ValueError:
            pass
    reset = headers.get("x-ratelimit-reset")
    if reset:
        try:
            t = datetime.datetime.fromisoformat(reset)
            now = datetime.datetime.now(t.tzinfo)
            return max(0.0, min((t - now).total_seconds(), 120.0))
        except ValueError:
            pass
    return min(base * (2 ** attempt), 60.0)


def get_json(url, token, retries, backoff):
    """GET して JSON を返す。429・5xx・通信エラーは再試行。それ以外の HTTP エラーは即座に打ち切る。"""
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token, "Accept": "application/json",
        "User-Agent": "jp-freee-api-skill/1.0"})
    attempt = 0
    while True:
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                w = wait_seconds(e.headers, attempt, backoff)
                print("  HTTP %d。%.1f 秒待って再試行します（%d/%d）" % (e.code, w, attempt + 1, retries),
                      file=sys.stderr)
                time.sleep(w)
                attempt += 1
                continue
            if e.code == 429:
                die("HTTP 429（短時間にアクセスしすぎ）が %d 回の再試行でも解消しません。\n"
                    "  → --interval を大きく（例 1.0）、--limit を 100 にして、数分あけて再実行してください。" % retries, 1)
            die(explain_http(e.code, body), 1)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < retries:
                w = min(backoff * (2 ** attempt), 60.0)
                print("  通信エラー（%s）。%.1f 秒待って再試行します（%d/%d）" % (e, w, attempt + 1, retries),
                      file=sys.stderr)
                time.sleep(w)
                attempt += 1
                continue
            die("通信できません（%s）。ネットワーク、または api.freee.co.jp への通信が許可されているか確認してください。"
                "外部通信できない環境では、--dry-run で出る URL を手元で実行してください。" % e, 1)
        except ValueError:
            die("応答が JSON ではありません。--base-url や経路上のプロキシを確認してください。", 1)


def fetch_all(args, token, company_id):
    base = args.base_url.rstrip("/")
    q = {"company_id": company_id, "start_issue_date": args.start, "end_issue_date": args.end,
         "limit": args.limit}
    for k, name in (("type", "type"), ("status", "status"), ("partner_id", "partner_id"),
                    ("account_item_id", "account_item_id")):
        v = getattr(args, k)
        if v is not None:
            q[name] = v
    deals, offset, total, pages, seen = [], 0, None, 0, set()
    while True:
        q["offset"] = offset
        url = base + PATH + "?" + urllib.parse.urlencode(q)
        j = get_json(url, token, args.retries, args.backoff)
        page = j.get("deals")
        if not isinstance(page, list):
            die("応答に deals がありません（想定外の形式）。API の版が変わった可能性があります。"
                "references/accounting.md の確認日を見て公式を読み直してください。", 1)
        if total is None:
            total = (j.get("meta") or {}).get("total_count")
        for d in page:
            if d.get("id") not in seen:
                seen.add(d.get("id"))
                deals.append(d)
        pages += 1
        offset += len(page)
        print("  %d ページ目: 累計 %d 件%s" % (pages, len(deals), (" / 全 %s 件" % total) if total is not None else ""),
              file=sys.stderr)
        if not page or (total is not None and offset >= total):
            break
        if pages >= args.max_pages:
            die("--max-pages（%d）に達しました。期間を分けるか --max-pages を増やしてください。"
                "ここまでの %d 件は出力していません。" % (args.max_pages, len(deals)), 1)
        time.sleep(args.interval)
    if total is not None and len(deals) != total:
        print("注意: meta.total_count=%s と取得件数 %d が一致しません。取得中に取引が増減した可能性があります。"
              % (total, len(deals)), file=sys.stderr)
    return deals


def to_rows(deals, mode):
    rows = []
    for d in deals:
        base = [(d.get("issue_date") or "")[:7], d.get("id"), d.get("issue_date"), d.get("due_date"),
                d.get("type"), d.get("status"), d.get("partner_id"), d.get("ref_number"),
                d.get("amount"), d.get("due_amount")]
        if mode == "deal":
            rows.append(base)
            continue
        details = d.get("details") or [{}]
        for x in details:
            rows.append(base + [x.get("id"), x.get("account_item_id"), x.get("tax_code"), x.get("amount"),
                                x.get("vat"), x.get("item_id"), x.get("section_id"), x.get("description")])
    return rows


def render(args, deals):
    if args.format == "json":
        return json.dumps({"deals": deals, "count": len(deals)}, ensure_ascii=False, indent=1) + "\n"
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(DEAL_COLS + (DETAIL_COLS if args.rows == "detail" else []))
    w.writerows(to_rows(deals, args.rows))
    return (chr(0xFEFF) if args.bom else "") + buf.getvalue()


def main(argv=None):
    args = build_parser().parse_args(argv)
    s, e = parse_date(args.start, "--start"), parse_date(args.end, "--end")
    if s > e:
        die("--start が --end より後です（%s > %s）" % (args.start, args.end))
    if not 1 <= args.limit <= MAX_LIMIT:
        die("--limit は 1〜%d で指定してください" % MAX_LIMIT)
    if args.retries < 0 or args.max_pages < 1:
        die("--retries は 0 以上、--max-pages は 1 以上で指定してください")
    check_base(args.base_url)
    token = os.environ.get("FREEE_ACCESS_TOKEN", "").strip()
    cid = os.environ.get("FREEE_COMPANY_ID", "").strip()
    if args.dry_run:
        print("[dry-run] 送りません。", file=sys.stderr)
        print("FREEE_ACCESS_TOKEN: %s" % ("設定済み" if token else "未設定"), file=sys.stderr)
        print("FREEE_COMPANY_ID  : %s" % (cid if cid.isdigit() else ("数値ではない" if cid else "未設定")), file=sys.stderr)
        q = {"company_id": cid or "<FREEE_COMPANY_ID>", "start_issue_date": args.start,
             "end_issue_date": args.end, "limit": args.limit, "offset": 0}
        for k in ("type", "status", "partner_id", "account_item_id"):
            if getattr(args, k) is not None:
                q[k] = getattr(args, k)
        print("GET " + args.base_url.rstrip("/") + PATH + "?" + urllib.parse.urlencode(q))
        print("Authorization: Bearer ****（環境変数から読む）")
        return 0
    if not token or not cid:
        die("環境変数 FREEE_ACCESS_TOKEN と FREEE_COMPANY_ID を設定してください。\n"
            "  トークンは developer.freee.co.jp の手順で取得（references/auth.md）、"
            "事業所IDは GET /api/1/companies の id。--dry-run で設定状況だけ確認できます。")
    if not cid.isdigit():
        die("FREEE_COMPANY_ID は数値です（受け取った値の長さ: %d）。" % len(cid))
    if args.out and os.path.exists(args.out) and not args.force:
        die("%s は既にあります。上書きするなら --force、別名にするなら --out を変えてください。" % args.out)
    print("取得開始: %s 〜 %s" % (args.start, args.end), file=sys.stderr)
    deals = fetch_all(args, token, int(cid))
    text = render(args, deals)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as f:
            f.write(text)
        print("%d 件の取引を %s に書きました。" % (len(deals), args.out), file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


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
