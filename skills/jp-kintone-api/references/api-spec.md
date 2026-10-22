# kintone REST API の仕様（レコード系）

確認日: 2026-10-21。**確認日から90日を過ぎたら、下の出典を読み直してから使う。** 数字（件数上限・制限値）は変わりうる。
出典（すべてサイボウズ公式）:
- 共通仕様: https://cybozu.dev/ja/kintone/docs/rest-api/overview/kintone-rest-api-overview/
- 認証: https://cybozu.dev/ja/kintone/docs/rest-api/overview/authentication/
- レコード取得（複数）: https://cybozu.dev/ja/kintone/docs/rest-api/records/get-records/
- レコード登録（複数）: https://cybozu.dev/ja/kintone/docs/rest-api/records/add-records/
- レコード更新（複数）: https://cybozu.dev/ja/kintone/docs/rest-api/records/update-records/
- カーソル作成: https://cybozu.dev/ja/kintone/docs/rest-api/records/create-cursor/
- カーソル取得: https://cybozu.dev/ja/kintone/docs/rest-api/records/get-cursor/
- カーソル削除: https://cybozu.dev/ja/kintone/docs/rest-api/records/delete-cursor/
- 同時接続数: https://cybozu.dev/ja/kintone/tips/development/customize/columns/concurrent-connection-limit-reason/
- 制限値一覧（ヘルプ）: https://jp.kintone.help/k/ja/admin/limitation/limit
- フィールド形式: https://cybozu.dev/ja/kintone/docs/overview/field-types/

## 1. URL とドメイン

| 場面 | URL |
|---|---|
| 通常のアプリ | `https://<サブドメイン>.cybozu.com/k/v1/<リソース>.json` |
| ゲストスペース内のアプリ | `https://<サブドメイン>.cybozu.com/k/guest/<スペースID>/v1/<リソース>.json` |

- サブドメインは契約ごとに決まる（ブラウザで kintone を開いたときの URL の先頭部分）。アプリIDはアプリを開いた URL の `/k/<数字>/`。
- 本文・レスポンスは UTF-8。`Content-Type` は本文を送るときだけ（JSON は `application/json`）。
- GET のパラメーターは URL エンコードしてクエリ文字列に入れるのが一般的。URL が長くなるとき（8KB 超）は `X-HTTP-Method-Override: GET` を付けた POST で JSON 本文に入れる方法がある（共通仕様ページ）。
- `*.cybozu.com` 以外のドメイン（kintone.com、cybozu-dev.com など）は**今回の確認では未確認**。契約のドメインを使う。基本認証・クライアント証明書を使う契約は共通仕様の別ページを読む（未確認）。

## 2. 認証

| 方式 | ヘッダー | 注意 |
|---|---|---|
| APIトークン | `X-Cybozu-API-Token: <トークン>` | アプリの設定で発行。**1アプリに20個まで**。1リクエストに指定できるのは**9個まで**（カンマ区切りまたは別ヘッダー。ルックアップ元アプリの値をコピーして登録するときなど） |
| パスワード認証 | `X-Cybozu-Authorization: <Base64("ログイン名:パスワード")>` | **2要素認証を有効にしたユーザーは使えない**。連携専用ユーザーを作る |

- APIトークンはアプリごと。トークンごとに許可する操作（閲覧・追加・編集・削除）を選ぶ。**権限の詳細は認証ページに記載が見当たらなかったため、アプリ設定画面で確認する**（要確認）。
- APIトークンで使えるのはレコード・ファイル・アプリ（フォーム・一覧・設定・グラフ等）のAPI。
- 鍵はコード・引数・ログ・会話に書かず、環境変数から読む。

## 3. 件数の上限（レコード）

| 操作 | メソッド・パス | 1回の上限 | 備考 |
|---|---|---|---|
| 取得（複数） | GET `/records.json` | **500件**（`query` 内の `limit`。既定100） | `offset` の上限は **10,000**。それ以上はカーソルAPI |
| 登録（複数） | POST `/records.json` | **100件** | 1件でも失敗するとその回の全件がキャンセル |
| 更新（複数） | PUT `/records.json` | **100件** | 同上。`upsert: true` で無ければ新規登録 |
| カーソル作成 | POST `/records/cursor.json` | `size` は1〜500（既定100） | `query` に **limit / offset は指定できない** |
| カーソル取得 | GET `/records/cursor.json?id=` | 作成時の `size` 件ずつ | `next: false` で終わり。全件取ればカーソルは自動で消える |
| カーソル削除 | DELETE `/records/cursor.json` | — | 途中でやめるときだけ必要 |

- `fields` は本文では1,000件まで、クエリ文字列では添字0〜99まで。サブテーブル内のフィールドは直接指定できず、テーブルのフィールドコードを指定する。
- `totalCount=true` を付けると、条件に一致する件数が**文字列**で返る（付けないと `null`）。

## 4. カーソルAPI（500件超・offset 10,000超の全件取得）

1. 作成: `POST /k/v1/records/cursor.json` 本文 `{"app": 1, "fields": [...], "query": "...", "size": 500}` → `{"id": "...", "totalCount": "1234"}`
2. 取得: `GET /k/v1/records/cursor.json?id=<id>` → `{"records": [...], "next": true|false}`。`next` が `true` の間、同じ `id` で繰り返す
3. 削除: 途中でやめるときだけ `DELETE /k/v1/records/cursor.json` 本文 `{"id": "..."}`（レスポンスは `{}`）

制限・注意（カーソル作成・取得ページ）:
- 有効なカーソルは**1ドメインあたり最大10個**。超えると新規作成できない（全件取得済み・削除・期限切れのいずれかで空く）。作成の並行実行もできない。
- 有効期限は、作成または取得を**最後に実行してから10分**。
- カーソルから取れるのは**作成時点で対象だったレコード**。値は取得した時点のもの。
- `next` が `true` でも次の `records` が空のことがある。`next: false` まで続ける。
- 絞り込みに `like` / `not like` を含むと、一致が100,000件に達した時点で検索を打ち切る（警告がヘッダーに付く）。作成は5分でタイムアウトする。
- 認証は パスワード認証・APIトークン認証・セッション認証（OAuth は記載なし）。

## 5. 登録・更新の本文

登録（POST）:
```json
{"app": 1, "records": [ {"会社名": {"value": "A社"}, "金額": {"value": "1000"}} ]}
```
- 存在しないフィールドコードは**無視される**（綴りミスでもエラーにならない）。必須項目は値が要る。空配列 `{}` だと初期値で登録。
- 登録できない: ルックアップ元からコピーされる項目、ステータス、カテゴリー、計算、作業者、自動計算の文字列1行。作成者・更新者・作成日時・更新日時はアプリ管理権限が要る。
- レスポンス: `{"ids": [...], "revisions": [...]}`（リクエストの順）。

更新（PUT）:
```json
{"app": 1, "records": [
  {"id": 3, "record": {"金額": {"value": "2000"}}, "revision": 5},
  {"updateKey": {"field": "社員番号", "value": "E001"}, "record": {"金額": {"value": "1"}}}
], "upsert": false}
```
- `id` と `updateKey` はどちらか一方。`updateKey` は「重複禁止」の文字列1行か数値のフィールドだけ。
- `revision` を付けると、一致しないとエラーで更新されない（`-1` か省略で検証しない）。
- **テーブルは更新したい行だけでなく既存の全行を送る**。送らなかった行は削除される。行の `id` を付けると更新、無いと新規行。
- 更新できない項目は登録と同様（作成者・更新者・日時を含む）。

## 6. 取得結果の形

`records` は配列。各レコードは `{"フィールドコード": {"type": "...", "value": ...}}`。値の形（フィールド形式ページ）:
- 数値・文字列・日付などは `value` が文字列（数値も文字列で返る）。空は `""` か `null`。
- チェックボックス・複数選択・カテゴリーは文字列の配列。
- ユーザー選択は `[{"code": "sato", "name": "佐藤"}]`。登録・更新するときは `name` ではなく `code` を使う。
- サブテーブル（`SUBTABLE`）は `[{"id": "147", "value": {"<内側のコード>": {"type": ..., "value": ...}}}]`。
- 添付ファイルはファイルのメタ情報の配列（中身は別のファイル取得API）。
- システム項目: `$id`（レコードID）、`$revision`。

## 7. 制限・レート

- **同時接続数: 1ドメインにつき100まで**。超えるとHTTP **429**。レスポンスヘッダー `X-ConcurrencyLimit-Limit`（常に100）と `X-ConcurrencyLimit-Running`（現在の同時接続数）で確認できる。100に達した状態が続くと、APIを使っていない画面にも遅延が出ることがある。
- **1日のAPIリクエスト数（アプリごと）**: 契約コースで異なる。共通仕様ページには「スタンダード10,000件・ワイド100,000件」とある。ヘルプの制限値一覧は「契約コースによって異なる」とだけ書く。**自分の契約の値は要確認**。日本時間で毎日午前9時にリセット。超えても止まらず、管理者に警告メールが届く。バルクリクエストは中の API それぞれが1回と数える。
- 単位時間あたりのレート制限（秒間何件など）は、確認した公式ページに**記載なし**。並列を絞り、429 のときは待って再試行する。
