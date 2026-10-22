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
