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
