<!-- jp-kintone-api v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-kintone-api（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-kintone-api
description: >-
  kintone の REST API でレコードを取得・登録・更新するコードを書き、クエリ構文・件数制限・認証・エラーの原因を調べる。「kintone のレコードを全件取得するスクリプトを書いて」「クエリの書き方（条件・並び替え・limit/offset）を教えて」「500件の上限を超えて取りたい」「APIトークンで権限エラーになる」「CSV の内容を kintone に一括登録して」と頼まれたときに使う。公式ドキュメント（確認日つき）に沿い、カーソルAPIでの全件取得と CSV 出力のスクリプトを同梱。鍵は環境変数から読み、コードや会話に書かない。Keywords: kintone REST API, cursor API, records.json, X-Cybozu-API-Token, query, bulk import。アプリの設計、JavaScript カスタマイズ（kintone.api）、他社SaaSの API は対象外。
license: MIT
compatibility: "Python 3.9 以上（標準ライブラリだけ）。kintone への通信にはインターネット接続が必要。通信できない環境では --dry-run と手順の提示まで"
metadata:
  version: "1.0.0"
  author: frametech
---

# kintone REST API（レコードの取得・登録・更新）

目的: kintone のレコードを REST API で読み書きするコードと、クエリ・制限・エラーの答えを、公式仕様どおりに出す。
入力: やりたいこと（取得／登録／更新）、アプリの条件（フィールドコード、絞り込み）、エラーメッセージ。サブドメイン・アプリIDは聞くが、**APIトークンは聞かない・書き写さない**。
出力: 動くコード（またはスクリプトの実行手順）と、効いている制限・注意点の一言。エラー調べなら「原因の候補 → 確かめ方 → 直し方」。

事実は [references/](references/) にある（確認日 2026-10-21）。**確認日から90日を過ぎたら、各ファイル冒頭の公式URLを読み直してから答える。** 概要: https://cybozu.dev/ja/kintone/docs/rest-api/overview/kintone-rest-api-overview/

## 鍵の扱い（最初に守る）

- APIトークン・パスワードは**コード・コマンド引数・ファイル・会話に書かない**。ユーザーが鍵を貼ってきても、書き写さずに「環境変数 `KINTONE_API_TOKEN` から読む形」で書く。貼られた鍵は漏れた可能性があるので、アプリ設定で再生成するよう一言添える。
- 使う環境変数: `KINTONE_SUBDOMAIN`、`KINTONE_APP_ID`、`KINTONE_API_TOKEN`（パスワード認証は `KINTONE_LOGIN_NAME` / `KINTONE_PASSWORD`、ゲストスペースは `KINTONE_GUEST_SPACE_ID`）。

## 手順

1. 依頼を分ける: (a) 全件取得・エクスポート (b) 登録・更新 (c) クエリの書き方 (d) エラー・権限の調べ (e) 制限（件数・レート）の質問。
2. **件数で道具を選ぶ**（references/api-spec.md §3・§4）:
   - 500件以下 → `GET /k/v1/records.json`（`limit` 上限500）
   - 500件超、または offset が10,000を超える → **カーソルAPI**（作成→取得を `next:false` まで→途中でやめたら削除）
   - 登録・更新は**1回100件まで**。分割して送り、1回でも失敗するとその回は全件キャンセル
3. (a) はスクリプトを使う。まず `--dry-run` で送る内容を見せ、環境変数が揃っていれば本番を実行する。

   ```bash
   python3 scripts/kintone_records.py fetch --dry-run
   python3 scripts/kintone_records.py fetch --count-only --query '更新日時 > "2026-10-01T00:00:00+09:00"'
   python3 scripts/kintone_records.py fetch --query 'ステータス in ("対応中") order by $id asc' --fields 会社名,金額 -o out.csv
   ```

   `--format json` で元のレスポンスのまま、`--bom` で Excel 向け。途中で失敗・中断してもカーソルは削除される。
   スクリプトを実行できない・外部に通信できない環境では、api-spec.md §3・§4 のとおり URL・ヘッダー・本文を組み立てて示し、手元で実行してもらう（結果は貼ってもらう）。
4. (b) の登録は `add`。CSV の1行目をフィールドコードにし、**必ず先に `--dry-run`**、内容を見せてユーザーの確認を取ってから `--yes` で送る。Excel の CSV は `--encoding cp932`。**存在しないフィールドコードは黙って無視される**ので、見出しの綴りを確認させる。途中の回で失敗したら、登録済みの件数を伝え、同じ CSV の再実行は重複になると警告する。更新（PUT）はコードで書く（recipes.md）。**一括更新・登録は元に戻せない**ので、本番アプリでは先にテスト用アプリで試すよう勧める。
5. (c) クエリは query.md に沿って書く。`limit` / `offset` はカーソル作成の `query` に書けない。チェックボックス・ドロップダウンには `=` が使えず `in`。フィールドは「名前」ではなく**フィールドコード**。
6. (d) エラーは `code` / `message` / `id` と HTTP ステータスを聞き、errors.md の表から候補を出す。**公式で確認できたものとコミュニティ報告を区別して伝え、断定しない。**
7. (e) 制限は api-spec.md §3・§7。1日のリクエスト数は契約コースで違い、確認できた公式ページ間でも書き方が異なるので「自分の契約で要確認」と添える。

## コードを書くとき

- 認証ヘッダーは `X-Cybozu-API-Token`（パスワード認証は `X-Cybozu-Authorization`＝Base64(ログイン名:パスワード)）。URL は `https://<サブドメイン>.cybozu.com/k/v1/...`（ゲストスペースは `/k/guest/<ID>/v1/`）。
- GET に本文は付けない（パラメーターは URL エンコードしてクエリ文字列へ）。POST / PUT / DELETE は `Content-Type: application/json`。
- 429 は待って再試行。並列は絞る。カーソルは1ドメイン10個まで・10分で失効。
- 書き方の見本は recipes.md。

## 返す形

```
（コードまたは実行コマンド）

効いている制限: 取得500件／登録100件／offset 10,000 など、今回に関係するものだけ
確認が要ること: 契約の1日リクエスト数、フィールドコードの綴り、トークンの権限 など
```

## 同梱物

| ファイル | 内容 |
|---|---|
| scripts/kintone_records.py | `fetch`（カーソルで全件→CSV/JSON）、`add`（CSV→100件ずつ登録）。`--help` `--dry-run`。終了コード 0 正常／1 API・通信の失敗／2 引数・環境変数の誤り |
| scripts/selftest_mock.py | 手元にモックの kintone を立てて、ページング・カーソル削除・分割登録を確かめる自己検証（本物には接続しない） |
| references/api-spec.md | URL・認証・件数上限・カーソル・登録更新の本文・制限（出典URLと確認日つき） |
| references/query.md | クエリ文字列の書式・演算子・フィールド型ごとの可否・limit/offset |
| references/errors.md | エラー形式と症状別の対処（公式とコミュニティ報告を区別） |
| references/recipes.md | Python 標準ライブラリ・curl のコード例 |

## 限界

実際の kintone 環境での成功は、このスキルの作成時点では未検証（モックと公式仕様との突き合わせまで）。初めて本番に向けるときは `--count-only` と少数件の取得から始める。

=== FILE: references/api-spec.md ===
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

=== FILE: references/errors.md ===
# エラーの読み方と対処

確認日: 2026-10-21。**公式が一覧として公開している範囲は狭い。** 下の表は「公式で確認」と「コミュニティの報告」を分けてある。コミュニティ報告は目安として使い、断定しない。**90日を過ぎたら公式を読み直す。**

## 形式（公式で確認）

出典: https://cybozu.dev/ja/kintone/docs/rest-api/overview/kintone-rest-api-overview/#response-error

- 成功は 200 番台。失敗は 200 番台以外のステータスと、次の JSON:
  `{"id": "<エラーID>", "code": "CB_IJ01", "message": "不正なJSON文字列です。"}`
- `id` はサポートへの問い合わせに使う。`message` の言語は実行ユーザーの表示言語による。
- `errors`（入力値エラーの詳細）が付くことがあるが、共通仕様ページには説明が無い。付いていれば**どのフィールドが悪いかが書いてある**ので必ず読む。

## 症状から探す

| 症状・code | 区分 | 原因の候補 | 次の手 |
|---|---|---|---|
| HTTP **429** | 公式 | 同時接続数が1ドメイン100を超えた | 並列を減らし、待って再試行。`X-ConcurrencyLimit-Running` を見る（api-spec.md §7） |
| `CB_IJ01` 不正な JSON | 公式 | 本文が JSON として壊れている | 引用符・カンマ・文字コード（UTF-8）、`Content-Type: application/json` を確認 |
| `CB_VA01` 入力値エラー | コミュニティ | クエリの書式ミス、フィールドコードの綴り、必須項目の欠け、本文の階層違い（`app` / `records` / `record`）、チェックボックスに `=` など | `errors` を読む。クエリは query.md と照らす。PUT の本文が「配列か1件か」を確認 |
| `CB_NO02` 権限がありません | コミュニティ | アプリ・レコード・フィールドの権限不足。APIトークンの許可操作が足りない | トークンの権限（閲覧・追加・編集）を確認。パスワード認証なら別ユーザー／トークンで切り分け |
| `GAIA_IA02` トークンがアプリのものと異なる | コミュニティ | 別アプリのトークン、コピー漏れ、アプリ設定で「アプリを更新」していない | トークンを発行したアプリのIDと `app` を一致させる。設定画面で保存→更新を済ませる |
| `GAIA_NO01` このトークンでは実行できない | コミュニティ | トークンにそのAPI（登録・更新など）の許可が無い | アプリ設定のAPIトークンで、必要な操作にチェックを入れて保存・更新 |
| `GAIA_TM12` カーソル上限 | コミュニティ | 有効なカーソルが1ドメイン10個に達した（途中で止めたスクリプトが残した等） | 10分待つ（最後の操作から10分で失効）。プログラムは終了時に DELETE する |
| `GAIA_RE01` レコードが見つからない | コミュニティ | レコードIDの誤り・削除済み | IDを取得し直す。`updateKey` なら値の一致を確認 |
| `GAIA_AP01` アプリが見つからない | コミュニティ（検索で確認できず・要確認） | アプリIDまたはサブドメインの誤り | URL の `/k/<数字>/` を確認 |
| 401 / 403 | 一般的な意味 | 認証ヘッダーの名前・値の誤り。パスワード認証で2要素認証のユーザー | ヘッダー名は `X-Cybozu-API-Token` / `X-Cybozu-Authorization`。2要素認証のユーザーは使えない（api-spec.md §2） |
| 404 | 一般的な意味 | サブドメイン・パス・ゲストスペースIDの違い | URL を組み立て直す。ゲストスペースは `/k/guest/<ID>/v1/` |
| 「500件までしか取れない」 | 仕様 | `limit` の上限は500 | カーソルAPIで全件取得（SKILL.md） |
| 「10,000件目から先が取れない」 | 仕様 | `offset` の上限は10,000 | カーソルAPI。または `$id` の範囲で条件を区切る |
| 登録したのに値が空 | 仕様 | 存在しないフィールドコードは**黙って無視**される | 見出し／キーの綴り、フィールドコードと表示名の取り違えを確認 |
| 一括更新後、テーブルの行が消えた | 仕様 | テーブルは既存の全行を送らないと、送らなかった行が削除される | いったん取得して全行を含めて送る |

## 切り分けの順序

1. HTTP ステータスと `code` / `message` / `id` を控える（トークンは控えない）
2. 認証（ヘッダー名・トークンの対象アプリ・権限）
3. URL（サブドメイン・アプリID・ゲストスペース）
4. 本文／クエリ（フィールドコード・演算子・階層）
5. 件数・同時接続の上限
6. それでも分からなければ `id` を添えて公式のサポート／コミュニティ（https://community.cybozu.dev/）へ

=== FILE: references/query.md ===
# kintone のクエリ文字列

確認日: 2026-10-21。出典: https://cybozu.dev/ja/kintone/docs/overview/query/ （サイボウズ公式）。**90日を過ぎたら読み直す。**

## 書式

```
<フィールドコード> <演算子> <値> [and|or <条件>] [order by <フィールドコード> asc|desc[, ...]] [limit <件数>] [offset <件数>]
```
- 条件は `フィールドコード 演算子 値`。`and` / `or` でつなぎ、丸括弧でまとめられる。
- **指定するのはフィールド名ではなく「フィールドコード」**（アプリ設定のフォームで確認する）。
- 文字列の値は二重引用符で囲む。`in` / `not in` は括弧で列挙: `ステータス in ("対応中", "完了")`。
- 値に `"` や `\` を含む場合はエスケープが必要（JSON に入れるときはさらに二重に）。
- オプションの記述順は **`order by` → `limit` → `offset`**。

## 演算子

| 種類 | 書き方 |
|---|---|
| 比較 | `=` `!=` `>` `<` `>=` `<=` |
| 一致 | `in` `not in` |
| 部分一致 | `like` `not like`（文字列検索は単語単位） |
| 論理 | `and` `or`（公式の演算子一覧に `not` は無い） |
| 空欄 | `is empty` `is not empty` |

- テーブル内のフィールド・関連レコードのフィールドは `=` `!=` の代わりに `in` `not in` を使う。

## フィールドタイプごとに使えるもの（レコード取得時）

| フィールドタイプ | 使える演算子 |
|---|---|
| 文字列（1行）、リンク | `=` `!=` `in` `not in` `like` `not like` |
| 数値、計算 | 比較6種、`in` `not in` |
| 文字列（複数行）、添付ファイル | `like` `not like` `is` `is not` |
| リッチエディター | `like` `not like` |
| チェックボックス、ラジオボタン、ドロップダウン、複数選択 | `in` `not in` |
| 日付、日時、作成日時、更新日時 | 比較6種＋日付関数 |
| 時刻 | 比較6種 |
| 作成者、更新者、ユーザー選択 | `in` `not in`＋`LOGINUSER()` |
| 組織選択 / グループ選択・作業者 | `in` `not in` |
| ステータス | `=` `!=` `in` `not in` |
| レコード番号、`$id` | 比較6種、`in` `not in` |

→ **チェックボックスやドロップダウンに `=` を使うとエラー**。`in ("値")` にする。

## 関数

- ユーザー・組織: `LOGINUSER()` `PRIMARY_ORGANIZATION()`
- 日時: `NOW()` `TODAY()` `YESTERDAY()` `TOMORROW()` `FROM_TODAY(数字, 単位)`（単位は DAYS / WEEKS / MONTHS / YEARS の4種類。綴りは公式で確認）
- 週・月・年: `THIS_WEEK()` `LAST_WEEK()` `NEXT_WEEK()` `THIS_MONTH()` `LAST_MONTH()` `NEXT_MONTH()`（引数に末日 `LAST` または1〜31）`THIS_YEAR()` `LAST_YEAR()` `NEXT_YEAR()`

## limit / offset

| | 既定 | 上限 |
|---|---|---|
| `limit` | 100 | 複数レコード取得系のAPIは **500**、それ以外は100 |
| `offset` | 0 | **10,000** |
| `order by` を省略 | レコードIDの降順 | — |

- offset を進めるページングは、10,000件までしか使えない。それ以上は**カーソルAPI**（カーソル作成の `query` には limit / offset を書けない）。
- offset ページングで更新が走ると、ずれて重複・取りこぼしが出る。確実に全件取るならカーソル。

## 例

```
更新日時 >= "2026-10-01T00:00:00+09:00" and ステータス in ("対応中") order by 更新日時 desc limit 100
金額 >= 10000 and 担当者 in (LOGINUSER()) order by $id asc
会社名 like "株式会社" and 登録日 = TODAY()
```
- 日時の値の書き方（`"2026-10-01T00:00:00+09:00"` のような ISO 8601）は、実行する環境で一度試して確かめる（今回の確認では例の全文を取得できていない）。

=== FILE: references/recipes.md ===
# コードの書き方（Python 標準ライブラリ版と curl）

確認日: 2026-10-21。仕様の数字は api-spec.md を正とする。**鍵はコードに書かず、環境変数から読む。**

## 全件取得（同梱スクリプト）

```bash
export KINTONE_SUBDOMAIN=example KINTONE_APP_ID=12     # 鍵は export KINTONE_API_TOKEN=... を手元のシェルで（会話・コードには書かない）
python3 scripts/kintone_records.py fetch --dry-run
python3 scripts/kintone_records.py fetch --count-only --query 'ステータス in ("対応中")'
python3 scripts/kintone_records.py fetch --query 'ステータス in ("対応中") order by $id asc' --fields 会社名,金額 --format csv -o out.csv
```
`--bom` で Excel 向けの BOM つき UTF-8。CSV のチェックボックスは `;` 区切り、ユーザー選択は code、サブテーブルは JSON 文字列。JSON 出力は元のレスポンス（type つき）のまま。

## コードを書くとき（カーソルで全件）

```python
import json, os, urllib.request

BASE = "https://%s.cybozu.com/k/v1" % os.environ["KINTONE_SUBDOMAIN"]
HEAD = {"X-Cybozu-API-Token": os.environ["KINTONE_API_TOKEN"], "Content-Type": "application/json"}

def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, headers=HEAD,
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")

cur = call("POST", "/records/cursor.json", {"app": os.environ["KINTONE_APP_ID"], "size": 500, "query": 'ステータス in ("対応中")'})
records, done = [], False
try:
    while True:
        page = call("GET", "/records/cursor.json?id=" + cur["id"])   # GET に本文は付けない
        records += page["records"]
        if not page["next"]:
            done = True          # 取り切るとカーソルは自動で消える
            break
finally:
    if not done:
        call("DELETE", "/records/cursor.json", {"id": cur["id"]})
```
- 429 のときは待って再試行する。`query` に limit / offset は書かない。
- offset ページング（10,000件まで）で済む件数でも、取りこぼしを避けたいならカーソルを使う。

## 登録（100件ずつ）

```python
for i in range(0, len(rows), 100):
    call("POST", "/records.json", {"app": APP, "records": [
        {"会社名": {"value": r["name"]}, "金額": {"value": str(r["amount"])}} for r in rows[i:i+100]]})
```
- 失敗した回は全件キャンセルされる。**それまでの回は登録済み**なので、再実行の前に件数を確かめる（重複を避ける）。
- 同梱スクリプト: `python3 scripts/kintone_records.py add --csv 登録.csv --dry-run` で内容を確かめ、`--yes` で送る。CSV の1行目はフィールドコード。Excel の CSV は `--encoding cp932`。空欄のセルは送らない（アプリの初期値になる）。値は文字列で送る（数値フィールドも文字列でよい）。複数選択・ユーザー選択・テーブルは CSV では扱えない（コードで書く）。

## 更新

```python
call("PUT", "/records.json", {"app": APP, "records": [
    {"id": 3, "record": {"金額": {"value": "2000"}}}]})          # 100件まで。updateKey でも指定できる
```
テーブルは全行を送る（api-spec.md §5）。楽観ロックが要るときは `revision` を付ける。

## curl

```bash
curl -s -X POST "https://${KINTONE_SUBDOMAIN}.cybozu.com/k/v1/records/cursor.json" \
  -H "X-Cybozu-API-Token: ${KINTONE_API_TOKEN}" -H "Content-Type: application/json" \
  -d '{"app": 12, "size": 500}'
```
パスワード認証は `-H "X-Cybozu-Authorization: $(printf '%s' "$LOGIN:$PASS" | base64)"`。

## JavaScript カスタマイズから呼ぶ場合

`kintone.api()`（ブラウザ内。ログイン中のユーザー権限で動き、鍵は不要）は対象外。このスキルは外部のスクリプトから REST API を呼ぶ場合を扱う。

=== FILE: scripts/kintone_records.py ===
#!/usr/bin/env python3
"""kintone のレコードを、カーソルAPIで全件取得して CSV / JSON に出す。CSV から一括登録もできる。

Python 3.9 以上・標準ライブラリだけ。接続先は <サブドメイン>.cybozu.com（KINTONE_BASE_DOMAIN で変更可）だけ。

  環境変数（鍵は引数に取らない）
    KINTONE_SUBDOMAIN     必須。https://<ここ>.cybozu.com の部分
    KINTONE_APP_ID        必須（--app でも指定可。アプリIDは秘密ではない）
    KINTONE_API_TOKEN     APIトークン（複数はカンマ区切り）。無ければ下の2つでパスワード認証
    KINTONE_LOGIN_NAME / KINTONE_PASSWORD   パスワード認証（2要素認証のユーザーは使えない）
    KINTONE_GUEST_SPACE_ID  ゲストスペース内のアプリのときだけ
    KINTONE_BASE_DOMAIN     既定 cybozu.com

  使い方
    python3 kintone_records.py fetch --dry-run
    python3 kintone_records.py fetch --query 'ステータス in ("対応中") order by 更新日時 desc' --fields 会社名,金額 --format csv -o out.csv
    python3 kintone_records.py fetch --count-only
    python3 kintone_records.py add --csv 登録.csv --dry-run
    python3 kintone_records.py add --csv 登録.csv --yes

  終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り

通信できない環境（外部通信が禁止のチャット等）では実行できない。--dry-run だけは通信しないので、
組み立てた URL・ヘッダー・本文を確かめて、手元の環境で実行してもらう。
"""
import argparse
import base64
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
CURSOR_SIZE_MAX = 500   # カーソル作成 size の上限（公式）
ADD_CHUNK_MAX = 100     # 1回の登録の上限（公式）
MASK = "＊＊＊＊（環境変数から読み込み済み・表示しない）"
RETRY_WAITS = (2, 4, 8, 16)  # 429 のときの待ち秒数


class UsageError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status, code, message, err_id=None, body=None):
        super().__init__(message)
        self.status, self.code, self.message, self.err_id, self.body = status, code, message, err_id, body


# ───────── 設定 ─────────

def load_config(args):
    env = os.environ
    sub = env.get("KINTONE_SUBDOMAIN", "").strip()
    if not sub:
        raise UsageError("環境変数 KINTONE_SUBDOMAIN が空です。https://<ここ>.cybozu.com のサブドメイン部分を入れてください。")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", sub):
        raise UsageError("KINTONE_SUBDOMAIN は英数字とハイフンだけです（'.cybozu.com' や 'https://' は付けない）。")
    base = env.get("KINTONE_BASE_DOMAIN", "cybozu.com").strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*\.[a-z]{2,}", base):
        raise UsageError("KINTONE_BASE_DOMAIN の形式が違います（例: cybozu.com）。")
    app = (getattr(args, "app", None) or env.get("KINTONE_APP_ID", "")).strip()
    if not re.fullmatch(r"[0-9]+", app):
        raise UsageError("アプリIDが数字ではありません。環境変数 KINTONE_APP_ID か --app に、アプリの URL の /k/<数字>/ の数字を指定してください。")
    guest = env.get("KINTONE_GUEST_SPACE_ID", "").strip()
    if guest and not re.fullmatch(r"[0-9]+", guest):
        raise UsageError("KINTONE_GUEST_SPACE_ID は数字です。")

    token = env.get("KINTONE_API_TOKEN", "").strip()
    login, pw = env.get("KINTONE_LOGIN_NAME", ""), env.get("KINTONE_PASSWORD", "")
    if token:
        auth_header = ("X-Cybozu-API-Token", token)
    elif login and pw:
        auth_header = ("X-Cybozu-Authorization", base64.b64encode(("%s:%s" % (login, pw)).encode("utf-8")).decode("ascii"))
    else:
        raise UsageError("認証情報がありません。環境変数 KINTONE_API_TOKEN（アプリの設定で発行したAPIトークン）を設定してください。"
                         "（鍵は引数やコードに書かない。シェルで export するか .env を読み込む）")

    origin = "https://%s.%s" % (sub, base)
    test_origin = env.get("KINTONE_TEST_ORIGIN", "")  # 手元のモックサーバー検証用。ローカル以外は受け付けない
    if test_origin:
        if not re.fullmatch(r"http://(127\.0\.0\.1|localhost)(:[0-9]+)?", test_origin):
            raise UsageError("KINTONE_TEST_ORIGIN は http://127.0.0.1:<ポート> の形だけ使えます。")
        origin = test_origin
    prefix = "/k/guest/%s/v1" % guest if guest else "/k/v1"
    return {"origin": origin, "prefix": prefix, "app": app, "auth": auth_header}


# ───────── リクエストの組み立てと送信 ─────────

def build(cfg, method, path, params=None, body=None):
    """(method, url, headers, data) を返す。GET はパラメーターを URL エンコードしてクエリ文字列に、他は JSON 本文に。"""
    url = cfg["origin"] + cfg["prefix"] + path
    headers = {cfg["auth"][0]: cfg["auth"][1], "User-Agent": "jp-kintone-api-skill/1.0"}
    data = None
    if method == "GET" and params:
        url += "?" + urllib.parse.urlencode(params)
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    return method, url, headers, data


def show_request(label, method, url, headers, data, max_chars=1200):
    """--dry-run 用。認証ヘッダーの値は伏せる。"""
    print("# " + label)
    print("%s %s" % (method, url))
    for k, v in headers.items():
        print("%s: %s" % (k, MASK if k in ("X-Cybozu-API-Token", "X-Cybozu-Authorization") else v))
    if data is not None:
        text = data.decode("utf-8")
        print(text if len(text) <= max_chars else text[:max_chars] + " …（以下省略）")
    print()


def send(cfg, method, path, params=None, body=None, retry=False):
    method, url, headers, data = build(cfg, method, path, params, body)
    waits = list(RETRY_WAITS) if retry else []
    while True:
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode("utf-8")
                return json.loads(text) if text.strip() else {}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                j = json.loads(raw)
            except ValueError:
                j = {}
            if e.code == 429 and waits:
                w = waits.pop(0)
                print("429（同時接続数の上限）。%d 秒待って再試行します" % w, file=sys.stderr)
                time.sleep(w)
                continue
            raise ApiError(e.code, j.get("code"), j.get("message") or raw[:200], j.get("id"), raw)
        except urllib.error.URLError as e:
            raise ApiError(None, None, "通信できません: %s" % e.reason)
        except ValueError:
            raise ApiError(None, None, "レスポンスが JSON ではありません（サブドメインやプロキシを確認）")


HINTS = {
    "CB_IJ01": "リクエスト本文が不正な JSON です。引用符や括弧、文字コード（UTF-8）を確認する。",
    "CB_VA01": "入力値エラー（公式の一覧は未確認）。クエリ文字列の書式、フィールドコードの綴り、必須項目の漏れ、本文の階層（app / records）を確認し、レスポンスの errors があれば見る。",
    "CB_NO02": "権限がありません（コミュニティ報告）。APIトークンの権限（閲覧・追加・編集）と、パスワード認証ならユーザーのアプリ・レコード・フィールド権限を確認する。",
    "GAIA_IA02": "APIトークンがこのアプリのものと一致しません（コミュニティ報告）。トークンのアプリ違い・コピー漏れと、アプリ設定で「アプリを更新」したかを確認する。",
    "GAIA_NO01": "このAPIトークンでは指定したAPIを実行できません（コミュニティ報告）。トークンの権限（閲覧・追加・編集・削除）のチェックを確認する。",
    "GAIA_TM12": "カーソルの数が上限（1ドメイン10個）です。10分待つか、不要なカーソルを削除してからやり直す。",
    "GAIA_RE01": "指定したレコードが見つかりません。レコードIDと、削除済みでないかを確認する。",
    "GAIA_AP01": "指定したアプリが見つかりません（コミュニティ報告）。アプリIDとサブドメイン、ゲストスペースのアプリかどうかを確認する。",
}


def explain(e):
    lines = ["失敗: %s" % e.message]
    if e.status:
        lines.append("  HTTP %s / code=%s / id=%s" % (e.status, e.code, e.err_id))
    if e.code in HINTS:
        lines.append("  原因と次の手: " + HINTS[e.code])
    elif e.status == 429:
        lines.append("  原因と次の手: 同時接続数の上限（1ドメイン100）に当たっています。並列数を減らし、少し待ってからやり直す。")
    elif e.status in (401, 403):
        lines.append("  原因と次の手: 認証に失敗しています。APIトークンの値・有効なアプリか・権限を確認する（パスワード認証は2要素認証のユーザーでは使えない）。")
    elif e.status == 404:
        lines.append("  原因と次の手: サブドメイン・アプリID・ゲストスペースIDのどれかが違う可能性があります。")
    elif e.status is None:
        lines.append("  原因と次の手: ネットワーク・プロキシ・サブドメインの綴りを確認する。外部通信できない環境では --dry-run だけ使う。")
    else:
        lines.append("  原因と次の手: references/errors.md を見て code を引く。載っていなければ id を添えて公式（cybozu.dev）か管理者に問い合わせる。")
    return "\n".join(lines)


# ───────── 値の平坦化（CSV 用） ─────────

def flat(field):
    t, v = field.get("type"), field.get("value")
    if v is None:
        return ""
    if t == "SUBTABLE":
        return json.dumps([{k: flat(x) for k, x in row.get("value", {}).items()} for row in v], ensure_ascii=False)
    if isinstance(v, list):
        out = []
        for x in v:
            if isinstance(x, dict):
                out.append(str(x.get("code") or x.get("name") or json.dumps(x, ensure_ascii=False)))
            else:
                out.append(str(x))
        return ";".join(out)
    if isinstance(v, dict):
        return str(v.get("code") or json.dumps(v, ensure_ascii=False))
    return str(v)


def to_csv(records):
    cols = []
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for r in records:
        w.writerow([flat(r[c]) if c in r else "" for c in cols])
    return buf.getvalue()


# ───────── fetch ─────────

LIMIT_RE = re.compile(r"\b(limit|offset)\s+\d+", re.I)


def split_fields(s):
    return [x.strip() for x in s.split(",") if x.strip()] if s else None


def cmd_fetch(args):
    cfg = load_config(args)
    query = args.query or ""
    if LIMIT_RE.search(query):
        raise UsageError("query に limit / offset は指定できません（カーソルAPIの制約）。件数を絞るなら --max-records を使う。")
    size = args.size
    if not 1 <= size <= CURSOR_SIZE_MAX:
        raise UsageError("--size は 1〜%d です。" % CURSOR_SIZE_MAX)
    fields = split_fields(args.fields)

    if args.count_only:
        params = {"app": cfg["app"], "query": (query + " limit 1").strip(), "totalCount": "true"}
        req = build(cfg, "GET", "/records.json", params=params)
        if args.dry_run:
            show_request("件数の確認", *req)
            return EXIT_OK
        print(send(cfg, "GET", "/records.json", params=params, retry=True).get("totalCount"))
        return EXIT_OK

    create_body = {"app": cfg["app"], "size": size}
    if query:
        create_body["query"] = query
    if fields:
        create_body["fields"] = fields
    out_path = args.output
    if out_path and os.path.exists(out_path) and not args.force and not args.dry_run:
        raise UsageError("%s は既にあります。上書きするなら --force を付ける。" % out_path)

    if args.dry_run:
        show_request("1. カーソルを作成", *build(cfg, "POST", "/records/cursor.json", body=create_body))
        show_request("2. 続きが無くなる（next=false）まで繰り返し取得", *build(cfg, "GET", "/records/cursor.json", params={"id": "CURSOR_ID"}))
        show_request("3. 途中で止めたときだけ削除（最後まで取り切れば自動で消える）", *build(cfg, "DELETE", "/records/cursor.json", body={"id": "CURSOR_ID"}))
        print("# --dry-run のため通信していません。")
        return EXIT_OK

    created = send(cfg, "POST", "/records/cursor.json", body=create_body, retry=True)
    cid, total = created["id"], int(created.get("totalCount") or 0)
    print("カーソル作成: 対象 %d 件" % total, file=sys.stderr)
    records, finished, empty_streak = [], False, 0
    try:
        while True:
            page = send(cfg, "GET", "/records/cursor.json", params={"id": cid}, retry=True)
            got = page.get("records", [])
            records.extend(got)
            print("  取得 %d / %d 件" % (len(records), total), file=sys.stderr)
            if not page.get("next"):
                finished = True
                break
            if args.max_records and len(records) >= args.max_records:
                records = records[:args.max_records]
                break
            empty_streak = empty_streak + 1 if not got else 0
            if empty_streak >= 20:  # next=true で空が返ることがある（公式）が、延々続くなら止める
                raise ApiError(None, None, "next=true なのに20回続けて空でした。中断します")
    finally:
        if not finished:  # 途中終了（件数指定・エラー・Ctrl-C）。取り切ったカーソルは自動で消えるので削除しない
            try:
                send(cfg, "DELETE", "/records/cursor.json", body={"id": cid})
                print("カーソルを削除しました", file=sys.stderr)
            except ApiError as e:
                print("カーソルの削除に失敗（10分で自動失効します）: %s" % e.message, file=sys.stderr)

    text = json.dumps(records, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else to_csv(records)
    if out_path:
        with open(out_path, "w", encoding="utf-8-sig" if args.bom else "utf-8", newline="") as f:
            f.write(text)
        print("%d 件を %s に書きました" % (len(records), out_path), file=sys.stderr)
    else:
        sys.stdout.write(text)
    return EXIT_OK


# ───────── add（CSV から一括登録） ─────────

def read_csv_records(path, encoding):
    try:
        with open(path, "r", encoding=encoding, newline="") as f:
            rows = list(csv.reader(f))
    except UnicodeDecodeError:
        raise UsageError("%s を %s として読めません。Excel の CSV なら --encoding cp932 を試す。" % (path, encoding))
    except OSError as e:
        raise UsageError("CSV を開けません: %s" % e)
    if len(rows) < 2:
        raise UsageError("CSV にデータ行がありません（1行目はフィールドコードの見出し）。")
    head = [h.strip() for h in rows[0]]
    if not all(head) or len(set(head)) != len(head):
        raise UsageError("1行目の見出し（フィールドコード）に空欄または重複があります: %s" % head)
    records = []
    for n, row in enumerate(rows[1:], start=2):
        if len(row) != len(head):
            raise UsageError("%d 行目の列数が見出し（%d列）と違います（%d列）。" % (n, len(head), len(row)))
        rec = {h: {"value": v} for h, v in zip(head, row) if v != ""}  # 空欄は送らず、アプリの初期値に任せる
        records.append(rec)
    return head, records


def cmd_add(args):
    cfg = load_config(args)
    chunk = args.chunk
    if not 1 <= chunk <= ADD_CHUNK_MAX:
        raise UsageError("--chunk は 1〜%d です（1回の登録の上限）。" % ADD_CHUNK_MAX)
    head, records = read_csv_records(args.csv, args.encoding)
    chunks = [records[i:i + chunk] for i in range(0, len(records), chunk)]
    print("CSV: %d 件 → %d 回に分けて登録します。フィールドコード: %s" % (len(records), len(chunks), ", ".join(head)), file=sys.stderr)
    print("注意: 存在しないフィールドコードは黙って無視されます（公式）。見出しの綴りをアプリの設定と照らしてください。", file=sys.stderr)

    if args.dry_run or not args.yes:
        show_request("1回目の登録（先頭2件だけ表示）", *build(cfg, "POST", "/records.json", body={"app": cfg["app"], "records": chunks[0][:2]}))
        if not args.dry_run:
            print("# --yes が無いので送っていません。内容に問題がなければ --yes を付けて再実行してください。")
        return EXIT_OK

    done = 0
    for i, part in enumerate(chunks, start=1):
        try:
            res = send(cfg, "POST", "/records.json", body={"app": cfg["app"], "records": part})
        except ApiError as e:
            print(explain(e), file=sys.stderr)
            print("  %d 回目（データ行 %d〜%d）で失敗。この回は全件キャンセルされています。"
                  "それ以前の %d 件は登録済みなので、同じ CSV をそのまま再実行すると重複します。"
                  % (i, done + 1, done + len(part), done), file=sys.stderr)
            return EXIT_FAIL
        done += len(part)
        print("  登録 %d / %d 件（ID %s 〜 %s）" % (done, len(records), res["ids"][0], res["ids"][-1]), file=sys.stderr)
    return EXIT_OK


# ───────── CLI ─────────

EPILOG = """環境変数（鍵は引数に取らない。シェルで export する）
  KINTONE_SUBDOMAIN       必須。https://<ここ>.cybozu.com の部分
  KINTONE_APP_ID          必須（--app でも可）
  KINTONE_API_TOKEN       APIトークン（複数はカンマ区切り）
  KINTONE_LOGIN_NAME / KINTONE_PASSWORD   トークンが無いときのパスワード認証
  KINTONE_GUEST_SPACE_ID  ゲストスペースのアプリのときだけ
  KINTONE_BASE_DOMAIN     既定 cybozu.com

例
  python3 kintone_records.py fetch --dry-run
  python3 kintone_records.py fetch --query 'ステータス in ("対応中") order by 更新日時 desc' -o out.csv
  python3 kintone_records.py add --csv 登録.csv --dry-run

終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り"""

def main(argv=None):
    p = argparse.ArgumentParser(
        prog="kintone_records.py",
        description=__doc__.split("\n")[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="カーソルAPIで全件取得して CSV / JSON に出す")
    f.add_argument("--app", help="アプリID（省略時は環境変数 KINTONE_APP_ID）")
    f.add_argument("--query", help="クエリ文字列（条件と order by。limit / offset は不可）")
    f.add_argument("--fields", help="取得するフィールドコード（カンマ区切り）。省略で全部")
    f.add_argument("--size", type=int, default=CURSOR_SIZE_MAX, help="1回に取る件数 1〜500（既定500）")
    f.add_argument("--max-records", type=int, default=0, help="この件数で打ち切る（0=全件）")
    f.add_argument("--format", choices=["csv", "json"], default="csv")
    f.add_argument("-o", "--output", help="出力先ファイル（省略で標準出力）")
    f.add_argument("--bom", action="store_true", help="UTF-8 BOM 付きで書く（Excel で文字化けするとき）")
    f.add_argument("--force", action="store_true", help="既存の出力ファイルを上書きする")
    f.add_argument("--count-only", action="store_true", help="件数だけ表示して終了")
    f.add_argument("--dry-run", action="store_true", help="送る内容を（鍵は伏せて）表示するだけで通信しない")
    f.set_defaults(func=cmd_fetch)

    a = sub.add_parser("add", help="CSV の内容を一括登録する（1行目=フィールドコード、100件ずつ）")
    a.add_argument("--app", help="アプリID（省略時は環境変数 KINTONE_APP_ID）")
    a.add_argument("--csv", required=True, help="登録する CSV")
    a.add_argument("--encoding", default="utf-8-sig", help="CSV の文字コード（既定 utf-8-sig。Excel 出力は cp932）")
    a.add_argument("--chunk", type=int, default=ADD_CHUNK_MAX, help="1回に送る件数 1〜100")
    a.add_argument("--yes", action="store_true", help="確認済み。これが無いと送らず内容を表示するだけ")
    a.add_argument("--dry-run", action="store_true", help="送る内容を（鍵は伏せて）表示するだけで通信しない")
    a.set_defaults(func=cmd_add)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except UsageError as e:
        print("入力の誤り: %s" % e, file=sys.stderr)
        return EXIT_USAGE
    except ApiError as e:
        print(explain(e), file=sys.stderr)
        return EXIT_FAIL
    except KeyboardInterrupt:
        print("中断しました", file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())

=== FILE: scripts/selftest_mock.py ===
#!/usr/bin/env python3
"""kintone_records.py の自己検証。手元にモックの kintone（標準ライブラリの HTTP サーバー）を立てて、
ページング・カーソル削除・100件ずつの登録・エラー時の挙動を確かめる。本物の kintone には接続しない。

  python3 scripts/selftest_mock.py        # すべて通れば最後に「OK」と出て終了コード 0

モックは公式ドキュメントの仕様（カーソル作成 size 1〜500、limit/offset 不可、next=false で自動削除、
登録 100件まで、同時カーソル10個まで）を写したもの。実機での成功を保証するものではない。
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "kintone_records.py")
TOKEN = "dummy-token-for-selftest"


class State:
    def __init__(self, total=1234):
        self.total, self.cursors, self.log = total, {}, []
        self.fail_page = None      # この回数目のカーソル取得で 500 を返す
        self.empty_once = False    # 1回だけ next=true で空配列を返す
        self.rate_limit_first = 0  # 最初の N リクエストに 429
        self.fail_add_on = None    # この回数目の登録で 400 を返す
        self.add_batches, self.gets, self.seq = [], 0, 0
        self.last_count_query = None


def make_handler(st):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, obj):
            b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}

        def _auth(self):
            st.log.append((self.command, self.path, self.headers.get("X-Cybozu-API-Token")))
            if st.rate_limit_first > 0:
                st.rate_limit_first -= 1
                self._send(429, {"code": "GAIA_TM01", "id": "x", "message": "too many"})
                return False
            if self.headers.get("X-Cybozu-API-Token") != TOKEN:
                self._send(401, {"code": "CB_AU01", "id": "x", "message": "auth"})
                return False
            return True

        def do_POST(self):
            if not self._auth():
                return
            b = self._body()
            if self.path == "/k/v1/records/cursor.json":
                q = b.get("query", "")
                if "limit" in q or "offset" in q:
                    return self._send(400, {"code": "CB_VA01", "id": "x", "message": "limit/offset 不可"})
                if not 1 <= int(b.get("size", 100)) <= 500:
                    return self._send(400, {"code": "CB_VA01", "id": "x", "message": "size"})
                if len(st.cursors) >= 10:
                    return self._send(400, {"code": "GAIA_TM12", "id": "x", "message": "cursor limit"})
                st.seq += 1
                cid = "cur-%d" % st.seq
                st.cursors[cid] = {"pos": 0, "size": int(b.get("size", 100)), "fields": b.get("fields")}
                return self._send(200, {"id": cid, "totalCount": str(st.total)})
            if self.path == "/k/v1/records.json":
                recs = b.get("records", [])
                if len(recs) > 100:
                    return self._send(400, {"code": "CB_VA01", "id": "x", "message": "100件まで"})
                st.add_batches.append(len(recs))
                if st.fail_add_on and len(st.add_batches) == st.fail_add_on:
                    st.add_batches.pop()
                    return self._send(400, {"code": "CB_VA01", "id": "x", "message": "入力値エラー"})
                base = sum(st.add_batches[:-1])
                ids = [str(base + i + 1) for i in range(len(recs))]
                return self._send(200, {"ids": ids, "revisions": ["1"] * len(recs)})
            self._send(404, {"code": "CB_NF01", "id": "x", "message": "nf"})

        def do_GET(self):
            if not self._auth():
                return
            u = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(u.query)
            if u.path == "/k/v1/records/cursor.json":
                cid = qs.get("id", [""])[0]
                c = st.cursors.get(cid)
                if not c:
                    return self._send(400, {"code": "GAIA_CU01", "id": "x", "message": "cursor not found"})
                st.gets += 1
                if st.fail_page and st.gets == st.fail_page:
                    return self._send(500, {"code": "GAIA_UN00", "id": "x", "message": "server error"})
                if st.empty_once and st.gets == 2:
                    return self._send(200, {"records": [], "next": True})
                start = c["pos"]
                end = min(start + c["size"], st.total)
                c["pos"] = end
                recs = []
                for i in range(start, end):
                    recs.append({"$id": {"type": "__ID__", "value": str(i + 1)},
                                 "name": {"type": "SINGLE_LINE_TEXT", "value": "会社,%d \"A\"" % (i + 1)},
                                 "tags": {"type": "CHECK_BOX", "value": ["a", "b"]},
                                 "owner": {"type": "USER_SELECT", "value": [{"code": "sato", "name": "佐藤"}]},
                                 "rows": {"type": "SUBTABLE", "value": [{"id": "1", "value": {"x": {"type": "NUMBER", "value": "5"}}}]}})
                nxt = end < st.total
                if not nxt:
                    del st.cursors[cid]
                return self._send(200, {"records": recs, "next": nxt})
            if u.path == "/k/v1/records.json":
                st.last_count_query = qs
                return self._send(200, {"records": [], "totalCount": str(st.total) if qs.get("totalCount") == ["true"] else None})
            self._send(404, {"code": "CB_NF01", "id": "x", "message": "nf"})

        def do_DELETE(self):
            if not self._auth():
                return
            b = self._body()
            st.cursors.pop(b.get("id"), None)
            self._send(200, {})
    return H


class Mock:
    def __init__(self, **kw):
        self.st = State(**kw)
        self.srv = HTTPServer(("127.0.0.1", 0), make_handler(self.st))
        self.origin = "http://127.0.0.1:%d" % self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown()


def run(mock, args, env_extra=None, drop=()):
    env = {k: v for k, v in os.environ.items() if not k.startswith("KINTONE_")}
    env.update({"KINTONE_SUBDOMAIN": "example", "KINTONE_APP_ID": "7", "KINTONE_API_TOKEN": TOKEN,
                "KINTONE_TEST_ORIGIN": mock.origin if mock else "http://127.0.0.1:9"})
    env.update(env_extra or {})
    for k in drop:
        env.pop(k, None)
    return subprocess.run([sys.executable, "-I", SCRIPT] + args, env=env, capture_output=True, text=True, timeout=120)


FAILS = []


def check(name, cond, detail=""):
    print(("  ok  " if cond else "  NG  ") + name + ("" if cond else "  <- " + str(detail)[:300]))
    if not cond:
        FAILS.append(name)


def main():
    tmp = tempfile.mkdtemp()

    # 1. 全件取得（500+500+234）、CSV、カーソルは自動で消える（DELETE を送らない）
    m = Mock()
    out = os.path.join(tmp, "all.csv")
    r = run(m, ["fetch", "-o", out])
    rows = open(out, encoding="utf-8").read().splitlines()
    check("全件取得が終了コード0", r.returncode == 0, r.stderr)
    check("1234件ぶんの CSV 行（見出し+1234）", len(rows) == 1235, len(rows))
    check("カンマと引用符を含む値が CSV として壊れない", '"会社,1 ""A"""' in rows[1], rows[1])
    check("チェックボックスは ; 区切り、ユーザー選択は code", ",a;b,sato," in rows[1], rows[1])
    check("カーソル取得は3回", sum(1 for x in m.st.log if x[0] == "GET") == 3, m.st.log)
    check("取り切ったら DELETE を送らない", not any(x[0] == "DELETE" for x in m.st.log))
    check("全リクエストにトークンヘッダー", all(x[2] == TOKEN for x in m.st.log))
    r2 = run(m, ["fetch", "-o", out])
    check("既存ファイルは --force 無しで上書きしない（終了コード2）", r2.returncode == 2, r2.stderr)
    m.close()

    # 2. --max-records で打ち切り → カーソルを DELETE する
    m = Mock()
    r = run(m, ["fetch", "--max-records", "600", "--format", "json", "-o", os.path.join(tmp, "p.json")])
    data = json.load(open(os.path.join(tmp, "p.json"), encoding="utf-8"))
    check("--max-records 600 で600件", r.returncode == 0 and len(data) == 600, r.stderr)
    check("打ち切ったカーソルは DELETE される", any(x[0] == "DELETE" for x in m.st.log) and not m.st.cursors, m.st.log)
    m.close()

    # 3. 途中のサーバーエラー → 終了コード1、原因表示、カーソル削除
    m = Mock()
    m.st.fail_page = 2
    r = run(m, ["fetch"])
    check("途中失敗は終了コード1", r.returncode == 1, r.returncode)
    check("失敗時に「原因と次の手」を出す", "原因と次の手" in r.stderr, r.stderr)
    check("失敗時もカーソルを DELETE する", any(x[0] == "DELETE" for x in m.st.log) and not m.st.cursors, m.st.log)
    m.close()

    # 4. next=true で空配列が返っても続行
    m = Mock()
    m.st.empty_once = True
    r = run(m, ["fetch", "--format", "json", "-o", os.path.join(tmp, "e.json")])
    check("next=true の空ページを挟んでも全件取る", r.returncode == 0 and len(json.load(open(os.path.join(tmp, "e.json"), encoding="utf-8"))) == 1234, r.stderr)
    m.close()

    # 5. query の limit/offset は通信前に弾く
    m = Mock()
    r = run(m, ["fetch", "--query", "金額 > 100 limit 10"])
    check("query に limit → 終了コード2・通信しない", r.returncode == 2 and not m.st.log, (r.returncode, m.st.log))
    m.close()

    # 6. --dry-run は通信せず、トークンを表示しない
    m = Mock()
    r = run(m, ["fetch", "--query", 'ステータス in ("対応中") order by 更新日時 desc', "--fields", "a,b", "--dry-run"])
    check("dry-run は終了コード0・通信ゼロ", r.returncode == 0 and not m.st.log, (r.returncode, m.st.log))
    check("dry-run にトークンの値が出ない", TOKEN not in r.stdout + r.stderr)
    check("dry-run に 3つのエンドポイントが出る", all(s in r.stdout for s in ("POST ", "GET ", "DELETE ")) and "cursor.json" in r.stdout, r.stdout)
    check("dry-run の本文に app と size と query", '"app": "7"' in r.stdout and '"size": 500' in r.stdout and "order by" in r.stdout, r.stdout)
    r = run(m, ["add", "--csv", os.path.join(tmp, "none.csv"), "--dry-run"])
    check("存在しない CSV は終了コード2", r.returncode == 2, r.stderr)
    m.close()

    # 7. --count-only
    m = Mock()
    r = run(m, ["fetch", "--count-only", "--query", "金額 > 100"])
    qs = m.st.last_count_query or {}
    check("--count-only は件数だけ出す", r.stdout.strip() == "1234", r.stdout + r.stderr)
    check("count は totalCount=true と limit 1 で問い合わせる", qs.get("totalCount") == ["true"] and "limit 1" in qs.get("query", [""])[0], qs)
    m.close()

    # 8. 429 は待って再試行する（2秒）
    m = Mock(total=3)
    m.st.rate_limit_first = 1
    r = run(m, ["fetch", "--format", "json", "-o", os.path.join(tmp, "r.json")])
    check("429 のあと再試行して成功", r.returncode == 0 and "429" in r.stderr, r.stderr)
    m.close()

    # 9. 認証エラー・環境変数の不足
    m = Mock()
    r = run(m, ["fetch"], {"KINTONE_API_TOKEN": "wrong-token"})
    check("トークン違いは終了コード1・認証の案内", r.returncode == 1 and "認証" in r.stderr, r.stderr)
    r = run(m, ["fetch"], drop=("KINTONE_API_TOKEN",))
    check("鍵が無いと終了コード2で環境変数名を案内", r.returncode == 2 and "KINTONE_API_TOKEN" in r.stderr, r.stderr)
    r = run(m, ["fetch"], {"KINTONE_SUBDOMAIN": "evil.example.com/x"})
    check("サブドメインに . や / を許さない", r.returncode == 2, r.stderr)
    r = run(m, ["fetch"], {"KINTONE_TEST_ORIGIN": "http://example.com"})
    check("テスト用オリジンはローカル以外を拒否", r.returncode == 2, r.stderr)
    m.close()

    # 10. add: 250行 → 100+100+50。--yes が無ければ送らない
    csvp = os.path.join(tmp, "in.csv")
    with open(csvp, "w", encoding="utf-8") as f:
        f.write("name,amount\n")
        for i in range(250):
            f.write("会社%d,%d\n" % (i, i * 10))
        f.write("空欄の行,\n")
    m = Mock()
    r = run(m, ["add", "--csv", csvp])
    check("--yes 無しは送らない", r.returncode == 0 and not m.st.add_batches and "--yes" in r.stdout, (r.stdout, r.stderr))
    r = run(m, ["add", "--csv", csvp, "--yes"])
    check("251行が 100/100/51 で登録される", r.returncode == 0 and m.st.add_batches == [100, 100, 51], (m.st.add_batches, r.stderr))
    m.close()

    # 11. add: 2回目が失敗 → 1回目は登録済みと案内
    m = Mock()
    m.st.fail_add_on = 2
    r = run(m, ["add", "--csv", csvp, "--yes"])
    check("2回目失敗で終了コード1", r.returncode == 1, r.returncode)
    check("登録済み件数と重複注意を案内", "100 件は登録済み" in r.stderr and "重複" in r.stderr, r.stderr)
    m.close()

    # 12. add: Shift_JIS の CSV
    sj = os.path.join(tmp, "sj.csv")
    open(sj, "wb").write("name,amount\n日本語会社,5\n".encode("cp932"))
    m = Mock()
    r = run(m, ["add", "--csv", sj, "--yes"])
    check("cp932 の CSV は文字コード指定の案内つきで弾く", r.returncode == 2 and "cp932" in r.stderr, r.stderr)
    r = run(m, ["add", "--csv", sj, "--encoding", "cp932", "--yes"])
    check("--encoding cp932 なら登録できる", r.returncode == 0 and m.st.add_batches == [1], r.stderr)
    m.close()

    # 13. --help
    r = subprocess.run([sys.executable, "-I", SCRIPT, "--help"], capture_output=True, text=True)
    check("--help が終了コード0", r.returncode == 0 and "fetch" in r.stdout and "add" in r.stdout)

    print("\n" + ("OK 全部通りました" if not FAILS else "失敗 %d 件: %s" % (len(FAILS), FAILS)))
    return 1 if FAILS else 0


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
