#!/usr/bin/env python3
"""Backlog（ヌーラボ）API v2 で、課題の全件取得（CSV/JSON）・登録・ステータス一括変更をする。

Python 3.9 以上・標準ライブラリだけ。通信先は BACKLOG_SPACE で指定したスペースのホストだけ。

  環境変数（鍵は引数に取らない・出力に出さない）
    BACKLOG_SPACE         必須。スペースのホスト名。例: example.backlog.com / example.backlog.jp
    BACKLOG_API_KEY       APIキー（Backlog-API-Key ヘッダーで送る。URL には付けない）
    BACKLOG_ACCESS_TOKEN  OAuth 2.0 のアクセストークン（あれば APIキーより優先。Authorization: Bearer）

  使い方
    python3 backlog_issues.py fetch --dry-run
    python3 backlog_issues.py fetch --project-id 123 --status-id 1,2 -o issues.csv --bom
    python3 backlog_issues.py meta --project-id 123            # 登録に要る ID の一覧（読み取りのみ）
    python3 backlog_issues.py add --csv new.csv --dry-run
    python3 backlog_issues.py add --csv new.csv --yes
    python3 backlog_issues.py set-status --keys PRJ-1,PRJ-2 --status-id 4 --yes

  終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り（--yes が無い書き込みもここ）

通信できない環境（外部通信が禁止のチャット等）では実行できない。--dry-run は通信しないので、
組み立てた URL・ヘッダー・本文を確かめて、手元の環境で実行してもらう。
"""
import argparse
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
PAGE_MAX = 100          # 課題一覧 count の上限（公式）
MASK = "＊＊＊＊（環境変数から読み込み済み・表示しない）"
HOST_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*\.backlog(?:tool)?\.(?:com|jp)")


class UsageError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status, errors, raw=""):
        super().__init__("HTTP %s" % status)
        self.status, self.errors, self.raw = status, errors, raw


class Client:
    def __init__(self, scheme, host, auth, interval, retry_wait, retries=3):
        self.base = "%s://%s" % (scheme, host)
        self.auth, self.interval, self.retry_wait, self.retries = auth, interval, retry_wait, retries
        self._last = 0.0
        self.calls = 0

    def headers(self, masked=False):
        name, val = self.auth
        return {name: MASK if masked else (("Bearer " + val) if name == "Authorization" else val)}

    def url(self, path, params=None):
        q = urllib.parse.urlencode(params or [], doseq=True)
        return self.base + path + ("?" + q if q else "")

    def request(self, method, path, params=None, form=None):
        """params は URL、form は application/x-www-form-urlencoded 本文。(status, json, headers) を返す。"""
        url = self.url(path, params if method == "GET" else None)
        data = urllib.parse.urlencode(form, doseq=True).encode("utf-8") if form is not None else None
        for attempt in range(self.retries + 1):
            wait = self.interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            req = urllib.request.Request(url, data=data, method=method)
            for k, v in self.headers().items():
                req.add_header(k, v)
            if data is not None:
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
            self._last = time.time()
            self.calls += 1
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = r.read().decode("utf-8")
                    return r.status, (json.loads(body) if body.strip() else None), r.headers
            except urllib.error.HTTPError as e:
                raw = e.read().decode("utf-8", "replace")
                if e.code == 429 and attempt < self.retries:
                    time.sleep(self._reset_wait(e.headers))
                    continue
                try:
                    errs = json.loads(raw).get("errors", [])
                except Exception:
                    errs = []
                raise ApiError(e.code, errs, raw[:300])
            except urllib.error.URLError as e:
                raise ApiError(0, [{"message": "通信できません: %s" % e.reason, "code": None}])
        raise ApiError(429, [{"message": "レート制限が続きました", "code": 13}])

    def _reset_wait(self, headers):
        # X-RateLimit-Reset は UNIX 時刻。無ければ公式の目安どおり 1 分待つ（--retry-wait で変更）
        try:
            reset = int(headers.get("X-RateLimit-Reset"))
            return max(0.0, min(reset - time.time() + 1, 120.0)) if self.retry_wait else 0.0
        except (TypeError, ValueError):
            return self.retry_wait


def explain(e):
    """原因と次の手。公式のエラーコード表（references/api-spec.md）に沿う。"""
    hints = {
        2: "このプランでは使えない機能です。プランを確認してください。",
        4: "アクセスが拒否されました。IP アドレス制限の可能性があります。",
        5: "このユーザーにその操作の権限がありません。権限（管理者/一般/ゲスト）と制限（課題の登録のみ・閲覧のみ）を確認してください。",
        6: "リソースが見つかりません。projectId・課題キー・スペースのホストを確認してください。",
        7: "パラメーターが不正です。必須項目・ID の取り違え・日付形式（yyyy-MM-dd）を確認してください。",
        11: "認証に失敗しました。APIキー（またはトークン）が正しいか、別スペースのものでないか確認してください。",
        12: "このスペースは2要素認証が必須です。ユーザー側で設定してください。",
        13: "レート制限です。しばらく待って、間隔（--interval）を広げて再実行してください。",
    }
    lines = ["HTTP %s" % e.status]
    for er in e.errors:
        lines.append("  code=%s message=%s" % (er.get("code"), er.get("message")))
        if er.get("code") in hints:
            lines.append("  -> " + hints[er.get("code")])
    if e.status == 401 and not e.errors:
        lines.append("  -> 認証エラー。キーが無効か、OAuth のアクセストークンが期限切れ（1時間）かもしれません。")
    if e.status == 429:
        lines.append("  -> レート制限。1分ほど待つか --interval を広げてください。")
    if e.status == 0:
        lines.append("  -> " + e.errors[0]["message"] + "（BACKLOG_SPACE のホスト名・ネットワークを確認）")
    if not e.errors and e.raw and e.status not in (0, 401, 429):
        lines.append("  本文: " + e.raw)
    return "\n".join(lines)


# ───────── 設定 ─────────

def load_client(args):
    env = os.environ
    space = env.get("BACKLOG_SPACE", "").strip()
    scheme = "https"
    if not space:
        raise UsageError("環境変数 BACKLOG_SPACE が空です。例: export BACKLOG_SPACE=example.backlog.com（.backlog.jp のスペースもある。URL のホスト部分）")
    space = re.sub(r"^https?://", "", space).rstrip("/")
    if env.get("BACKLOG_TEST_HTTP") == "1" and re.fullmatch(r"(127\.0\.0\.1|localhost):\d+", space):
        scheme = "http"  # 自己検証のモックサーバー専用（ローカルホストだけ）
    elif not HOST_RE.fullmatch(space):
        raise UsageError("BACKLOG_SPACE の形式が違います: '%s'。<スペースID>.backlog.com か .backlog.jp（.backlogtool.com も可）の形で指定してください。" % space)
    token = env.get("BACKLOG_ACCESS_TOKEN", "").strip()
    key = env.get("BACKLOG_API_KEY", "").strip()
    if token:
        auth = ("Authorization", token)
    elif key:
        auth = ("Backlog-API-Key", key)
    elif getattr(args, "dry_run", False):
        auth = ("Backlog-API-Key", "")
    else:
        raise UsageError("環境変数 BACKLOG_API_KEY（または BACKLOG_ACCESS_TOKEN）が空です。鍵は引数や会話に書かず、環境変数に入れてください。")
    return Client(scheme, space, auth, args.interval, args.retry_wait)


def csv_ints(s):
    out = []
    for p in (s or "").split(","):
        p = p.strip()
        if p:
            if not re.fullmatch(r"[0-9]+", p):
                raise UsageError("数字のカンマ区切りで指定してください: '%s'" % p)
            out.append(p)
    return out


# ───────── fetch ─────────

FILTERS = [("project_id", "projectId[]"), ("issue_type_id", "issueTypeId[]"), ("status_id", "statusId[]"),
           ("priority_id", "priorityId[]"), ("assignee_id", "assigneeId[]"), ("category_id", "categoryId[]"),
           ("milestone_id", "milestoneId[]")]
DATES = [("created_since", "createdSince"), ("created_until", "createdUntil"),
         ("updated_since", "updatedSince"), ("updated_until", "updatedUntil"),
         ("due_since", "dueDateSince"), ("due_until", "dueDateUntil")]


def filter_params(args):
    p = []
    for attr, name in FILTERS:
        for v in csv_ints(getattr(args, attr, None)):
            p.append((name, v))
    for attr, name in DATES:
        v = getattr(args, attr, None)
        if v:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                raise UsageError("日付は yyyy-MM-dd 形式です: '%s'" % v)
            p.append((name, v))
    if args.keyword:
        p.append(("keyword", args.keyword))
    return p


def flat(v):
    if v is None:
        return ""
    if isinstance(v, dict):
        return str(v.get("name", v.get("value", v.get("id", ""))))
    if isinstance(v, list):
        return ";".join(flat(x) for x in v)
    return str(v)


BASE_COLS = ["issueKey", "id", "projectId", "summary", "status", "priority", "issueType", "assignee",
             "createdUser", "created", "updatedUser", "updated", "startDate", "dueDate",
             "estimatedHours", "actualHours", "category", "versions", "milestone", "parentIssueId", "description"]


def issue_row(it):
    row = {}
    for c in BASE_COLS:
        row[c] = flat(it.get(c))
    for cf in it.get("customFields") or []:
        row["カスタム:" + str(cf.get("name"))] = flat(cf.get("value"))
        if cf.get("otherValue"):
            row["カスタム:" + str(cf.get("name"))] += "（その他: %s）" % cf["otherValue"]
    return row


def write_csv(issues, path, bom):
    rows = [issue_row(i) for i in issues]
    cols = list(BASE_COLS)
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\r\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in cols})
    data = buf.getvalue().encode("utf-8-sig" if bom else "utf-8")
    if path in (None, "-"):
        sys.stdout.buffer.write(data)
    else:
        with open(path, "wb") as f:
            f.write(data)


def cmd_fetch(args):
    cl = load_client(args)
    filt = filter_params(args)
    page_params = filt + [("sort", args.sort), ("order", args.order), ("count", PAGE_MAX), ("offset", 0)]
    if args.dry_run:
        print("[dry-run] 通信しません。")
        print("GET " + cl.url("/api/v2/issues/count", filt))
        print("GET " + cl.url("/api/v2/issues", page_params) + "   （offset を %d ずつ増やして、返りが %d 件未満になるまで繰り返す）" % (PAGE_MAX, PAGE_MAX))
        print("ヘッダー: %s" % cl.headers(masked=True))
        print("間隔: %.1f 秒（公式の目安は一括処理で1秒以上）" % cl.interval)
        return EXIT_OK
    _, c, _ = cl.request("GET", "/api/v2/issues/count", filt)
    total = (c or {}).get("count")
    print("条件に合う課題: %s 件（約 %s 回のリクエスト）" % (total, (total or 0) // PAGE_MAX + 1), file=sys.stderr)
    if args.count_only:
        print(total)
        return EXIT_OK
    issues, seen, offset = [], set(), 0
    while True:
        params = [(k, v) if k != "offset" else (k, offset) for k, v in page_params]
        _, page, _ = cl.request("GET", "/api/v2/issues", params)
        page = page or []
        for it in page:
            if it.get("id") not in seen:
                seen.add(it.get("id"))
                issues.append(it)
        if args.max_issues and len(issues) >= args.max_issues:
            issues = issues[:args.max_issues]
            break
        if len(page) < PAGE_MAX:
            break
        offset += PAGE_MAX
        print("  取得済み %d 件" % len(issues), file=sys.stderr)
    if total is not None and len(issues) != total and not args.max_issues:
        print("注意: 件数 API は %s 件、取得できたのは %d 件。取得中に課題が増減した可能性があります（重複は除いてあります）。" % (total, len(issues)), file=sys.stderr)
    if args.format == "json":
        data = json.dumps(issues, ensure_ascii=False, indent=1)
        if args.output in (None, "-"):
            print(data)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(data)
    else:
        write_csv(issues, args.output, args.bom)
    print("%d 件を書き出しました。" % len(issues), file=sys.stderr)
    return EXIT_OK


# ───────── meta ─────────

def cmd_meta(args):
    cl = load_client(args)
    proj = args.project_id
    plan = [("優先度 priorityId", "/api/v2/priorities")]
    if proj:
        plan += [("状態 statusId", "/api/v2/projects/%s/statuses" % proj),
                 ("種別 issueTypeId", "/api/v2/projects/%s/issueTypes" % proj),
                 ("カスタム属性 customField_<id>", "/api/v2/projects/%s/customFields" % proj)]
    else:
        plan.insert(0, ("プロジェクト projectId", "/api/v2/projects"))
    if args.dry_run:
        print("[dry-run] 通信しません。")
        for label, path in plan:
            print("GET " + cl.url(path))
        print("ヘッダー: %s" % cl.headers(masked=True))
        return EXIT_OK
    for label, path in plan:
        _, items, _ = cl.request("GET", path)
        print("## " + label)
        for it in items or []:
            extra = ""
            if "projectKey" in it:
                extra = "  key=" + it["projectKey"]
            if path.endswith("customFields"):
                extra = "  required=%s typeId=%s 選択肢=%s" % (it.get("required"), it.get("typeId"),
                                                            [(i["id"], i["name"]) for i in it.get("items", [])])
            print("  %s\t%s%s" % (it.get("id"), it.get("name"), extra))
    return EXIT_OK


# ───────── add ─────────

REQUIRED = ["projectId", "summary", "issueTypeId", "priorityId"]
MULTI = {"categoryId", "versionId", "milestoneId", "notifiedUserId", "attachmentId"}
OPTIONAL = {"parentIssueId", "description", "startDate", "dueDate", "estimatedHours", "actualHours", "assigneeId"} | MULTI


def read_csv(path, encoding):
    try:
        with open(path, "r", encoding=encoding, newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, UnicodeDecodeError) as e:
        raise UsageError("CSV を読めません（%s）。Excel の CSV なら --encoding cp932 を試してください。" % e)


def build_forms(rows, args):
    forms, problems = [], []
    defaults = {"projectId": args.project_id, "issueTypeId": args.issue_type_id, "priorityId": args.priority_id}
    for n, row in enumerate(rows, start=2):  # 1行目は見出し
        row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        form = []
        for k, v in row.items():
            if not v:
                continue
            base = k[:-2] if k.endswith("[]") else k
            if base in MULTI:
                for x in v.replace("；", ";").split(";"):
                    if x.strip():
                        form.append((base + "[]", x.strip()))
            elif base in OPTIONAL or base in REQUIRED or re.fullmatch(r"customField_\d+(_otherValue)?", base):
                form.append((base, v))
            else:
                problems.append("%d行目: 未対応の列 '%s'（無視せず止めます。綴りを確認）" % (n, k))
        have = {k for k, _ in form}
        for r in REQUIRED:
            if r not in have and defaults.get(r):
                form.append((r, defaults[r]))
                have.add(r)
            if r not in have:
                problems.append("%d行目: 必須の %s がありません（列で与えるか --%s で既定値を指定）" % (
                    n, r, {"projectId": "project-id", "issueTypeId": "issue-type-id", "priorityId": "priority-id", "summary": "csv の summary 列"}[r]))
        for k, v in form:
            if k in ("projectId", "issueTypeId", "priorityId") and not v.isdigit():
                problems.append("%d行目: %s は数字の ID です（名前ではなく ID。`meta` で調べる）: '%s'" % (n, k, v))
            if k in ("startDate", "dueDate") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                problems.append("%d行目: %s は yyyy-MM-dd 形式です: '%s'" % (n, k, v))
        forms.append(form)
    return forms, sorted(set(problems), key=problems.index)


def cmd_add(args):
    cl = load_client(args)
    rows = read_csv(args.csv, args.encoding)
    if not rows:
        raise UsageError("CSV にデータ行がありません。")
    forms, problems = build_forms(rows, args)
    if problems:
        for p in problems[:30]:
            print("エラー: " + p, file=sys.stderr)
        print("1件も送っていません。直してから再実行してください。", file=sys.stderr)
        return EXIT_USAGE
    print("登録予定: %d 件（POST %s）" % (len(forms), cl.url("/api/v2/issues")))
    for i, f in enumerate(forms[:5], start=1):
        print("  例%d: %s" % (i, urllib.parse.urlencode(f)[:200]))
    if args.dry_run:
        print("[dry-run] 通信しません。ヘッダー: %s" % cl.headers(masked=True))
        return EXIT_OK
    if not args.yes:
        print("送っていません。内容を確認して --yes を付けて再実行してください（登録した課題は API では取り消せません）。", file=sys.stderr)
        return EXIT_USAGE
    created = []
    for i, f in enumerate(forms, start=1):
        try:
            _, issue, _ = cl.request("POST", "/api/v2/issues", form=f)
        except ApiError as e:
            print("%d 行目（CSV 上は %d 行目）で失敗。登録済み %d 件: %s" % (i, i + 1, len(created), ",".join(created) or "なし"), file=sys.stderr)
            print(explain(e), file=sys.stderr)
            print("同じ CSV をそのまま再実行すると登録済みの分が重複します。失敗した行以降だけの CSV にしてください。", file=sys.stderr)
            return EXIT_FAIL
        created.append(issue.get("issueKey", str(issue.get("id"))))
    print("%d 件登録: %s" % (len(created), ",".join(created)))
    return EXIT_OK


# ───────── set-status ─────────

def cmd_set_status(args):
    cl = load_client(args)
    keys = [k.strip() for k in (args.keys or "").split(",") if k.strip()]
    if args.keys_file:
        try:
            with open(args.keys_file, encoding="utf-8") as f:
                keys += [l.strip() for l in f if l.strip()]
        except OSError as e:
            raise UsageError("キー一覧を読めません: %s" % e)
    if not keys:
        raise UsageError("--keys（例: PRJ-1,PRJ-2）か --keys-file（1行1キー）で課題キーを指定してください。")
    bad = [k for k in keys if not re.fullmatch(r"[A-Za-z0-9_]+-\d+|\d+", k)]
    if bad:
        raise UsageError("課題キーの形式が違います（例 PRJ-12 または課題ID）: %s" % bad[:5])
    if not args.status_id or not args.status_id.isdigit():
        raise UsageError("--status-id は数字の ID です。`meta --project-id <ID>` で状態の ID を調べてください。")
    form = [("statusId", args.status_id)]
    if args.resolution_id:
        form.append(("resolutionId", args.resolution_id))
    if args.comment:
        form.append(("comment", args.comment))
    print("変更予定: %d 件 -> %s（PATCH %s/api/v2/issues/<キー>）" % (len(keys), urllib.parse.urlencode(form), cl.base))
    print("  先頭: %s" % ",".join(keys[:5]))
    if args.dry_run:
        print("[dry-run] 通信しません。ヘッダー: %s" % cl.headers(masked=True))
        return EXIT_OK
    if not args.yes:
        print("送っていません。確認して --yes を付けて再実行してください（状態の変更は課題の履歴に残り、通知も飛びます）。", file=sys.stderr)
        return EXIT_USAGE
    done = []
    for k in keys:
        try:
            cl.request("PATCH", "/api/v2/issues/%s" % k, form=form)
        except ApiError as e:
            print("%s で失敗。変更済み %d 件: %s" % (k, len(done), ",".join(done) or "なし"), file=sys.stderr)
            print(explain(e), file=sys.stderr)
            print("変更済みの分は再実行しても同じ状態になるだけです（冪等）。", file=sys.stderr)
            return EXIT_FAIL
        done.append(k)
    print("%d 件を変更しました。" % len(done))
    return EXIT_OK


def build_parser():
    ap = argparse.ArgumentParser(description="Backlog API v2: 課題の取得・登録・ステータス変更（鍵は環境変数 BACKLOG_API_KEY）")
    ap.add_argument("--interval", type=float, default=1.0, help="リクエスト間隔の秒数（既定1.0。公式は一括処理で1秒以上を推奨）")
    ap.add_argument("--retry-wait", type=float, default=60.0, help="429 のとき待つ秒数（既定60。X-RateLimit-Reset があればそれを使う）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="課題を全件取得して CSV/JSON に出す")
    for attr, _ in FILTERS:
        f.add_argument("--" + attr.replace("_", "-"), help="ID（カンマ区切りで複数）")
    for attr, name in DATES:
        f.add_argument("--" + attr.replace("_", "-"), help=name + "（yyyy-MM-dd）")
    f.add_argument("--keyword")
    f.add_argument("--sort", default="created", help="既定 created（取得中の順序が安定する）")
    f.add_argument("--order", default="asc", choices=["asc", "desc"])
    f.add_argument("--max-issues", type=int, default=0, help="この件数で打ち切る（試し取り用）")
    f.add_argument("--count-only", action="store_true", help="件数だけ表示")
    f.add_argument("--format", choices=["csv", "json"], default="csv")
    f.add_argument("-o", "--output", help="出力先（省略か - で標準出力）")
    f.add_argument("--bom", action="store_true", help="CSV を BOM つき UTF-8 に（Excel で開く用）")
    f.add_argument("--dry-run", action="store_true")
    f.set_defaults(fn=cmd_fetch)

    m = sub.add_parser("meta", help="登録・更新に要る ID（優先度・状態・種別・カスタム属性）を一覧する（読み取りのみ）")
    m.add_argument("--project-id", help="プロジェクトID/キー。省略するとプロジェクト一覧")
    m.add_argument("--dry-run", action="store_true")
    m.set_defaults(fn=cmd_meta)

    a = sub.add_parser("add", help="CSV から課題を登録する（--yes 必須）")
    a.add_argument("--csv", required=True, help="列: projectId,summary,issueTypeId,priorityId（必須）＋ description,dueDate,assigneeId,categoryId(;区切り),customField_<id> など")
    a.add_argument("--encoding", default="utf-8-sig", help="Excel の CSV は cp932")
    a.add_argument("--project-id", help="CSV に列が無いときの既定値")
    a.add_argument("--issue-type-id")
    a.add_argument("--priority-id")
    a.add_argument("--dry-run", action="store_true")
    a.add_argument("--yes", action="store_true", help="確認済み。これが無いと送らない")
    a.set_defaults(fn=cmd_add)

    s = sub.add_parser("set-status", help="課題のステータスを一括で変える（--yes 必須）")
    s.add_argument("--keys", help="課題キーをカンマ区切り（PRJ-1,PRJ-2）")
    s.add_argument("--keys-file", help="1行1キーのファイル")
    s.add_argument("--status-id", help="新しい状態のID（meta で調べる）")
    s.add_argument("--resolution-id", help="完了にするときの完了理由ID")
    s.add_argument("--comment", help="同時に付けるコメント")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_set_status)
    return ap


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except UsageError as e:
        print("引数・設定のエラー: %s" % e, file=sys.stderr)
        return EXIT_USAGE
    except ApiError as e:
        print(explain(e), file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
