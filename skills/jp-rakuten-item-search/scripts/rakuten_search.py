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
