<!-- jp-rakuten-item-search v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-rakuten-item-search（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
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

=== FILE: references/api-2026.md ===
# 楽天市場 商品検索API 2026年版の仕様と移行

確認日 2026-10-10。**確認日から90日を過ぎたら、下の公式ドキュメントを読み直してから使う**（2026年は2月・4月・7月と版が変わった）。

出典: 楽天ウェブサービス「Rakuten Ichiba Item Search API (version:2026-07-01)」 https://webservice.rakuten.co.jp/documentation/ichiba-item-search

## 1. 旧版との違い（ここで間違えやすい）

| 項目 | 旧版（2025年まで多くの記事・コードが使っている形） | 2026年版 |
|---|---|---|
| エンドポイント | `https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601` | `https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701` |
| 認証 | `applicationId` だけ | `applicationId` ＋ **`accessKey`**（クエリかヘッダー `accessKey` のどちらか） |
| Referer | 不要 | **アプリ登録の「アプリケーションURL」と同じ Referer を付ける**（※） |
| 一つ前の版 | — | `20260401`（公式の Old Versions に記載） |

※ Referer の要件は公式ドキュメントの本文には書かれていない。アプリ登録時のURLと一致する Referer を送って動いている実装（2026-05 以降）と、付けないと `HTTP_REFERRER_MISSING` で拒否されたという開発者の報告（Qiita・note、2026年）に基づく。サーバーから呼ぶときもヘッダーで付ける。

アクセスキーとアプリIDは https://webservice.rakuten.co.jp/app/list （ログインが要る）で確認・発行する。新規登録は https://webservice.rakuten.co.jp/app/create 。

## 2. 主なパラメータ

| 名前 | 内容 |
|---|---|
| `keyword` | UTF-8 で URL エンコード。半角128字まで。空白区切りは AND（`orFlag=1` で OR）。各語は半角2文字以上か全角1文字以上 |
| `shopCode` / `itemCode` / `genreId` | `keyword` を含め、この4つのどれか1つは必須 |
| `hits` | 1〜30（既定30） |
| `page` | 1〜100 |
| `sort` | `standard` `±affiliateRate` `±reviewCount` `±reviewAverage` `±itemPrice` `±updateTimestamp`。`+` は URL エンコード（`%2B`）が必要 |
| `minPrice` / `maxPrice` | 1〜999,999,999。`maxPrice` は `minPrice` より大きく |
| `NGKeyword` | 除外語 |
| `availability` | 1＝在庫ありだけ（既定）、0＝すべて |
| `affiliateId` | 付けると各商品に `affiliateUrl` が付く |
| `elements` | 返す項目をカンマ区切りで絞る（例 `itemName,itemPrice,itemUrl`） |
| `formatVersion` | `2` にすると `items[0].itemName` の平らな形。既定 `1` は `Items[0].Item.itemName` |

同じ URL に短時間に何度も送ると、一定時間応答しなくなる（公式の注意書き）。1秒に1回を超えない間隔で送る。

## 3. エラー

公式の例は `{"error": "...", "error_description": "..."}` の形だが、2026年版のエンドポイントは**認証エラーを別の形で返す**（2026-10-10、実際に送って確認）:

```json
{"errors": {"errorCode": 403, "errorMessage": "Invalid Access Key"}}
```

両方の形を読むこと。

| HTTP | 中身 | 次の手 |
|---|---|---|
| 400 `wrong_parameter` | `specify valid applicationId`、`keyword parameter is not valid` など | アプリID、キーワードの条件（§2）を確かめる |
| 403 `Invalid Access Key` | アクセスキーが違う・無い・失効 | app/list でアクセスキーを確かめ、環境変数を入れ直す |
| 403 Referer 関連 | Referer が無い・登録URLと違う | アプリ登録の「アプリケーションURL」と同じ値を Referer に |
| 404 `not_found` | 該当なし | キーワードを広げる、`availability=0` |
| 429 `too_many_requests` | 回数の上限 | 間隔を空けて再試行 |
| 500 / 503 | 内部エラー・メンテナンス | 時間をおいて再試行 |

## 4. アフィリエイトリンクを公開ページに載せるとき

`affiliateUrl` を記事・SNS に載せるのは広告にあたる。ステルスマーケティング告示（2023年10月1日施行）により、**広告であることが分かる表示**（「PR」「広告」「本ページはアフィリエイト広告を利用しています」など）を、読者が見て分かる位置に置く。
出典: 消費者庁「ステルスマーケティングに関する景品表示法の考え方」 https://www.caa.go.jp/policies/policy/representation/fair_labeling/stealth_marketing/ （確認日 2026-10-10）

価格・在庫は取得した時点のもの。ページに載せるなら「◯年◯月◯日時点」を添える。

=== FILE: scripts/rakuten_search.py ===
#!/usr/bin/env python3
"""楽天市場の商品検索API（2026年版 openapi.rakuten.co.jp）で商品を探し、JSON / CSV / Markdown の表で出す。

Python 3.9 以上・標準ライブラリだけ。ネットワークへ出るのは openapi.rakuten.co.jp だけ。

使い方:
  python3 scripts/rakuten_search.py "ワイヤレスイヤホン" --hits 5 --sort +itemPrice
  python3 scripts/rakuten_search.py --file 商品リスト.tsv --format md
  python3 scripts/rakuten_search.py "炊飯器" --dry-run          # 送らずに、送る URL（鍵は伏せ字）だけ出す

環境変数（引数やファイルに鍵を書かない）:
  RAKUTEN_APP_ID        必須。アプリID（applicationId）
  RAKUTEN_ACCESS_KEY    必須。アクセスキー（2026年版で必須になった）
  RAKUTEN_REFERER       必須。アプリ登録の「アプリケーションURL」と同じURL（例 https://example.com/）
  RAKUTEN_AFFILIATE_ID  任意。あれば affiliateUrl が返る

終了コード: 0 成功 / 1 API エラーが1件以上 / 2 使い方・設定の誤り
"""

import argparse
import csv
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ENDPOINT = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"
SORTS = [
    "standard", "+affiliateRate", "-affiliateRate", "+reviewCount", "-reviewCount",
    "+reviewAverage", "-reviewAverage", "+itemPrice", "-itemPrice",
    "+updateTimestamp", "-updateTimestamp",
]
ELEMENTS = "itemName,itemPrice,itemUrl,affiliateUrl,shopName,reviewCount,reviewAverage,itemCode"
INTERVAL = 1.1  # 同じアプリIDで1秒1回を超えない


def die(msg, code=2):
    print("✗ " + msg, file=sys.stderr)
    sys.exit(code)


def load_queries(args):
    """[(識別名, キーワード)] を返す。ファイルは1行1件、タブ区切りなら「識別名<TAB>キーワード」。"""
    queries = [(k, k) for k in args.keywords]
    if args.file:
        if not os.path.exists(args.file):
            die("ファイルが見つかりません: %s" % args.file)
        with open(args.file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                label, _, kw = line.partition("\t")
                queries.append((label.strip(), (kw or label).strip()))
    if not queries:
        die("キーワードがありません。引数か --file で渡してください（--help）")
    for label, kw in queries:
        if len(kw.encode("utf-8")) > 128 * 3 or len(kw) > 128:
            die("キーワードが長すぎます（128字まで）: %s" % label)
        if len(kw) < 2 and not any(ord(c) > 0x7F for c in kw):
            die("キーワードは半角2文字以上（全角なら1文字以上）: %s" % label)
    return queries


def build_params(kw, args, app_id, access_key, affiliate_id):
    p = {
        "format": "json",
        "formatVersion": "2",
        "keyword": kw,
        "applicationId": app_id,
        "accessKey": access_key,
        "hits": str(args.hits),
        "sort": args.sort,
        "elements": ELEMENTS,
    }
    if affiliate_id:
        p["affiliateId"] = affiliate_id
    if args.min_price:
        p["minPrice"] = str(args.min_price)
    if args.max_price:
        p["maxPrice"] = str(args.max_price)
    if args.ng:
        p["NGKeyword"] = args.ng
    return p


def masked_url(params):
    shown = dict(params)
    for k in ("applicationId", "accessKey", "affiliateId"):
        if shown.get(k):
            shown[k] = "***"
    return ENDPOINT + "?" + urllib.parse.urlencode(shown)


def error_text(body):
    """新APIは {"errors":{"errorCode","errorMessage"}}、文書の例は {"error","error_description"}。両方を読む。"""
    try:
        d = json.loads(body)
    except ValueError:
        return body[:200]
    if isinstance(d.get("errors"), dict):
        e = d["errors"]
        return "%s %s" % (e.get("errorCode", ""), e.get("errorMessage", ""))
    if "error" in d:
        return "%s %s" % (d.get("error"), d.get("error_description", ""))
    return body[:200]


HINTS = {
    "Invalid Access Key": "RAKUTEN_ACCESS_KEY が違うか失効しています。https://webservice.rakuten.co.jp/app/list でアクセスキーを確かめてください",
    "REFERRER": "RAKUTEN_REFERER をアプリ登録の「アプリケーションURL」と同じにしてください",
    "applicationId": "RAKUTEN_APP_ID が違います。アプリ一覧でアプリIDを確かめてください",
    "too_many_requests": "回数の上限です。間隔を空けて再実行してください（このスクリプトは1.1秒間隔）",
    "keyword": "キーワードの条件（半角2文字以上・128字まで）を確かめてください",
}


def fetch(params, referer, retries=3):
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Referer": referer, "User-Agent": "jp-rakuten-item-search/1.0"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code in (429, 503) and attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            msg = "HTTP %d %s" % (e.code, error_text(body))
            hint = next((h for k, h in HINTS.items() if k.lower() in msg.lower()), "")
            return None, msg + ("（" + hint + "）" if hint else "")
        except urllib.error.URLError as e:
            return None, "接続できません: %s（ネットワークに出られない環境では使えません）" % e.reason
    return None, "再試行しても失敗しました"


def to_rows(label, kw, data, err):
    if err:
        return [{"label": label, "keyword": kw, "rank": "", "itemName": "", "itemPrice": "",
                 "url": "", "shopName": "", "reviewCount": "", "reviewAverage": "", "error": err}]
    items = data.get("Items") or data.get("items") or []
    rows = []
    for i, it in enumerate(items, 1):
        it = it.get("Item", it) if isinstance(it, dict) else it  # formatVersion=1 の形にも対応
        rows.append({
            "label": label, "keyword": kw, "rank": i,
            "itemName": it.get("itemName", ""), "itemPrice": it.get("itemPrice", ""),
            "url": it.get("affiliateUrl") or it.get("itemUrl", ""),
            "shopName": it.get("shopName", ""), "reviewCount": it.get("reviewCount", ""),
            "reviewAverage": it.get("reviewAverage", ""), "error": "",
        })
    if not rows:
        rows.append({"label": label, "keyword": kw, "rank": "", "itemName": "", "itemPrice": "",
                     "url": "", "shopName": "", "reviewCount": "", "reviewAverage": "", "error": "該当なし"})
    return rows


def render(rows, fmt):
    if fmt == "json":
        return json.dumps(rows, ensure_ascii=False, indent=2)
    cols = ["label", "rank", "itemName", "itemPrice", "shopName", "reviewCount", "reviewAverage", "url", "error"]
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
        return buf.getvalue()
    head = "| 識別名 | 順位 | 商品名 | 価格（円） | ショップ | レビュー数 | 評価 | URL | エラー |"
    lines = [head, "|" + "---|" * len(cols)]
    for r in rows:
        name = str(r["itemName"]).replace("|", "｜")[:60]
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["label"], r["rank"], name, r["itemPrice"], r["shopName"], r["reviewCount"],
            r["reviewAverage"], r["url"], r["error"]))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="楽天市場の商品検索API（2026年版）で商品を探す", epilog=__doc__.split("使い方:")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keywords", nargs="*", help="検索キーワード（複数可。空白で AND）")
    ap.add_argument("--file", help="1行1件のリスト。「識別名<TAB>キーワード」も可。# で始まる行は無視")
    ap.add_argument("--hits", type=int, default=3, help="1キーワードあたりの件数 1〜30（既定 3）")
    ap.add_argument("--sort", default="-reviewCount", choices=SORTS, help="並び順（既定 -reviewCount）")
    ap.add_argument("--min-price", type=int)
    ap.add_argument("--max-price", type=int)
    ap.add_argument("--ng", help="除外キーワード")
    ap.add_argument("--format", default="md", choices=["md", "json", "csv"], help="出力形式（既定 md）")
    ap.add_argument("--dry-run", action="store_true", help="送らずに、送る URL（鍵は伏せ字）を出す")
    args = ap.parse_args()

    if not 1 <= args.hits <= 30:
        die("--hits は 1〜30")
    if args.min_price and args.max_price and args.max_price <= args.min_price:
        die("--max-price は --min-price より大きくしてください")
    queries = load_queries(args)

    app_id = os.environ.get("RAKUTEN_APP_ID", "")
    access_key = os.environ.get("RAKUTEN_ACCESS_KEY", "")
    referer = os.environ.get("RAKUTEN_REFERER", "")
    affiliate_id = os.environ.get("RAKUTEN_AFFILIATE_ID", "")

    if args.dry_run:
        for label, kw in queries:
            p = build_params(kw, args, app_id or "<RAKUTEN_APP_ID>", access_key or "<RAKUTEN_ACCESS_KEY>", affiliate_id)
            print("%s\tGET %s\tReferer: %s" % (label, masked_url(p), referer or "<RAKUTEN_REFERER>"))
        missing = [n for n, v in (("RAKUTEN_APP_ID", app_id), ("RAKUTEN_ACCESS_KEY", access_key), ("RAKUTEN_REFERER", referer)) if not v]
        if missing:
            print("（未設定: %s。実行前に環境変数へ入れてください）" % ", ".join(missing), file=sys.stderr)
        return 0

    missing = [n for n, v in (("RAKUTEN_APP_ID", app_id), ("RAKUTEN_ACCESS_KEY", access_key), ("RAKUTEN_REFERER", referer)) if not v]
    if missing:
        die("環境変数が未設定です: %s\n  アプリID・アクセスキーは https://webservice.rakuten.co.jp/app/list で確認し、"
            "RAKUTEN_REFERER にはアプリ登録の「アプリケーションURL」を入れてください。" % ", ".join(missing))

    rows, failed = [], 0
    for n, (label, kw) in enumerate(queries):
        if n:
            time.sleep(INTERVAL)
        data, err = fetch(build_params(kw, args, app_id, access_key, affiliate_id), referer)
        failed += 1 if err else 0
        rows.extend(to_rows(label, kw, data, err))
    print(render(rows, args.format))
    return 1 if failed else 0


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
