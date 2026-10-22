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
