---
name: jp-rakuten-item-search
description: >-
  楽天市場の商品を、2026年版の楽天ウェブサービス商品検索API（openapi.rakuten.co.jp、applicationId＋accessKey＋Referer）で検索し、商品名・価格・ショップ・レビュー・商品URL／アフィリエイトURLを表・JSON・CSVで返す。「楽天で◯◯を探して価格順に並べて」「商品リストの楽天リンクをまとめて取って」「楽天APIのコードを書いて」「楽天APIが403になる・Invalid Access Key と出る」「旧APIから新APIへ移行して」と頼まれたときに使う。Keywords: Rakuten Ichiba API, IchibaItem Search, affiliate link, 楽天アフィリエイト, 商品検索。APIキーは環境変数から読む。Amazon・Yahoo!ショッピングなど楽天以外の商品検索は対象外。
license: MIT
metadata:
  version: "1.0.0"
  author: frametech
---

# 楽天市場の商品検索（2026年版API）

目的: 楽天市場の商品を2026年版の商品検索APIで探し、比較・リンク集・記事の下書きに使える一覧にする。API を使うコードの作成・移行・エラーの原因調べもここで扱う。
入力: 検索キーワード（1つ、または「識別名<TAB>キーワード」のリスト）。必要なら件数・並び順・価格帯・除外語。
出力: 既定は Markdown の表（識別名・順位・商品名・価格・ショップ・レビュー数・評価・URL）。頼まれれば JSON か CSV。コードを頼まれたらコード。

**多くの記事・既存コードは旧API（`app.rakuten.co.jp/services/api/...`、`applicationId` だけ）のまま。2026年版はエンドポイント・認証・Referer が違う。** コードを書く・直す前に [references/api-2026.md](references/api-2026.md) を読む。

## 前提

- 楽天ウェブサービスのアプリ登録（無料）。環境変数に入れる:
  - `RAKUTEN_APP_ID`（アプリID）、`RAKUTEN_ACCESS_KEY`（アクセスキー）: https://webservice.rakuten.co.jp/app/list で確認
  - `RAKUTEN_REFERER`: アプリ登録の「アプリケーションURL」と同じ値
  - `RAKUTEN_AFFILIATE_ID`（任意）: あると `affiliateUrl` が返る
- **鍵をコード・引数・ファイル・会話に書かない。** ユーザーが鍵を貼ってきても、コードには `os.environ` / `process.env` で読む形だけを書き、鍵そのものは書き写さない

## 手順

1. 依頼を分ける: (a) 今すぐ商品を探す (b) API を使うコードを書く・直す (c) エラーの原因を調べる
2. (a) はスクリプトで検索する。まず `--dry-run` で送る内容を確かめ、環境変数が揃っていれば本番を実行する。

   ```bash
   python3 scripts/rakuten_search.py "ワイヤレスイヤホン" --hits 5 --sort +itemPrice --dry-run
   python3 scripts/rakuten_search.py "ワイヤレスイヤホン" --hits 5 --sort +itemPrice
   python3 scripts/rakuten_search.py --file 商品リスト.tsv --format csv > 結果.csv
   ```

   並び順は `-reviewCount`（レビュー数の多い順、既定）`+itemPrice`（安い順）`-itemPrice` `-reviewAverage` `standard` など。`--min-price` `--max-price` `--ng`（除外語）も使える。Python 3.9 以上・標準ライブラリだけで、通信先は openapi.rakuten.co.jp だけ。1件ごとに1.1秒空けて送る。
   シェルを実行できない・外部に通信できない環境では、api-2026.md §1・§2 のとおりに URL とヘッダーを組み立てて示し、ユーザーに手元で実行してもらう（結果を貼ってもらえば表にまとめる）。
3. (b) はコードを書く。必ず api-2026.md §1 の3点（新エンドポイント、`accessKey`、Referer ヘッダー）を入れ、鍵は環境変数から読み、1秒1回を超えない間隔にし、§3 の2つのエラー形式を両方読む。`formatVersion=2` を使うと `items[i].itemName` で読める。
4. (c) はエラーの本文を api-2026.md §3 の表に当てて、原因と次の手を返す。旧エンドポイントを使っていたら新エンドポイントへの書き換えを示す。
5. 結果を記事・SNS に載せる用途なら、api-2026.md §4 の広告表示と取得時点の注記を添える。

## 出力の例

```text
| 識別名 | 順位 | 商品名 | 価格（円） | ショップ | レビュー数 | 評価 | URL | エラー |
|---|---|---|---|---|---|---|---|---|
| ワイヤレスイヤホン | 1 | （商品名） | 1980 | （ショップ名） | 1520 | 4.3 | https://hb.afl.rakuten.co.jp/... | |

2026年10月10日時点の価格です。記事に載せる場合は「本ページはアフィリエイト広告を利用しています」等の表示を添えてください。
```

商品名・価格・URL はスクリプトか API の結果だけから書く。結果に無い商品・価格を推測で埋めない。エラーの行は消さずに残す。
