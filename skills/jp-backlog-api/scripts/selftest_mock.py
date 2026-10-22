#!/usr/bin/env python3
"""backlog_issues.py をモックの Backlog で確かめる自己検証（本物には接続しない）。Python 3.9 以上・標準ライブラリだけ。

  python3 scripts/selftest_mock.py     # 全部通れば終了コード 0
"""
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "backlog_issues.py")
KEY = "MOCKKEY-should-never-appear-in-output"
TOTAL = 250
STATE = {"log": [], "rate_limited": False, "fail_post_at": None, "posts": 0}
ISSUES = [{"id": i, "issueKey": "PRJ-%d" % i, "projectId": 1, "summary": "課題,%d \"引用\"" % i,
           "status": {"id": 1, "name": "未対応"}, "priority": {"id": 3, "name": "中"},
           "issueType": {"id": 7, "name": "タスク"}, "assignee": None, "created": "2026-10-01T00:00:00Z",
           "customFields": [{"id": 5, "name": "顧客", "value": {"id": 9, "name": "株式会社テスト"}}],
           "description": "行1\n行2"} for i in range(1, TOTAL + 1)]


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj, extra=None):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json;charset=utf-8")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        if self.headers.get("Backlog-API-Key") != KEY or "apiKey" in self.path:
            self._send(401, {"errors": [{"message": "Authenticate error", "code": 11, "moreInfo": ""}]})
            return False
        return True

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        STATE["log"].append(("GET", u.path, q))
        if not self._auth():
            return
        if u.path == "/api/v2/issues/count":
            return self._send(200, {"count": TOTAL})
        if u.path == "/api/v2/issues":
            if not STATE["rate_limited"]:
                STATE["rate_limited"] = True
                return self._send(429, {"errors": [{"message": "Too many requests.", "code": 13, "moreInfo": ""}]},
                                  {"X-RateLimit-Reset": "0"})
            off, cnt = int(q.get("offset", ["0"])[0]), int(q.get("count", ["20"])[0])
            if cnt > 100:
                return self._send(400, {"errors": [{"message": "count", "code": 7, "moreInfo": ""}]})
            return self._send(200, ISSUES[off:off + cnt])
        if u.path == "/api/v2/priorities":
            return self._send(200, [{"id": 2, "name": "高"}, {"id": 3, "name": "中"}, {"id": 4, "name": "低"}])
        if u.path == "/api/v2/projects/1/statuses":
            return self._send(200, [{"id": 1, "name": "未対応"}, {"id": 4, "name": "完了"}])
        if u.path == "/api/v2/projects/1/issueTypes":
            return self._send(200, [{"id": 7, "name": "タスク"}])
        if u.path == "/api/v2/projects/1/customFields":
            return self._send(200, [{"id": 5, "name": "顧客", "typeId": 6, "required": False, "items": [{"id": 9, "name": "A社"}]}])
        return self._send(404, {"errors": [{"message": "No resource.", "code": 6, "moreInfo": ""}]})

    def _form(self):
        n = int(self.headers.get("Content-Length", "0"))
        return urllib.parse.parse_qs(self.rfile.read(n).decode("utf-8"))

    def do_POST(self):
        STATE["log"].append(("POST", self.path, None))
        if not self._auth():
            return
        f = self._form()
        STATE["log"][-1] = ("POST", self.path, f)
        STATE["posts"] += 1
        if STATE["fail_post_at"] and STATE["posts"] == STATE["fail_post_at"]:
            return self._send(403, {"errors": [{"message": "no permission", "code": 5, "moreInfo": ""}]})
        if self.headers.get("Content-Type") != "application/x-www-form-urlencoded":
            return self._send(400, {"errors": [{"message": "ct", "code": 7, "moreInfo": ""}]})
        for r in ("projectId", "summary", "issueTypeId", "priorityId"):
            if r not in f:
                return self._send(400, {"errors": [{"message": "required " + r, "code": 7, "moreInfo": ""}]})
        self._send(201, {"id": 1000 + STATE["posts"], "issueKey": "PRJ-%d" % (1000 + STATE["posts"])})

    def do_PATCH(self):
        f = self._form()
        STATE["log"].append(("PATCH", self.path, f))
        if not self._auth():
            return
        self._send(200, {"id": 1, "issueKey": self.path.rsplit("/", 1)[-1]})


def main():
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    env = dict(os.environ, BACKLOG_SPACE="127.0.0.1:%d" % srv.server_port, BACKLOG_TEST_HTTP="1", BACKLOG_API_KEY=KEY)
    tmp = tempfile.mkdtemp()
    results = []

    def run(args, env_=None, **kw):
        p = subprocess.run([sys.executable, "-I", SCRIPT, "--interval", "0", "--retry-wait", "0"] + args,
                           env=env_ or env, capture_output=True, **kw)
        return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")

    def check(name, cond):
        results.append(cond)
        print(("OK   " if cond else "NG   ") + name)

    # 1. dry-run: 通信ゼロ・鍵なし
    STATE["log"].clear()
    rc, out, err = run(["fetch", "--dry-run"])
    check("fetch --dry-run は通信しない・終了0", rc == 0 and not STATE["log"])
    check("dry-run に鍵が出ない", KEY not in out + err and "＊＊＊＊" in out)
    env_nokey = {k: v for k, v in env.items() if k != "BACKLOG_API_KEY"}
    rc, out, err = run(["fetch", "--dry-run"], env_nokey)
    check("鍵が無くても dry-run は通る", rc == 0)
    rc, out, err = run(["fetch"], env_nokey)
    check("鍵が無い本番実行は終了2", rc == 2 and "BACKLOG_API_KEY" in err)

    # 2. 全件取得 250 件を 100/100/50 で、429 を 1 回再試行
    out_csv = os.path.join(tmp, "o.csv")
    STATE["log"].clear()
    rc, out, err = run(["fetch", "-o", out_csv, "--bom"])
    gets = [l for l in STATE["log"] if l[1] == "/api/v2/issues"]
    check("終了0", rc == 0)
    check("429 を再試行して 100/100/50 の計4回（429 1回＋3ページ）", len(gets) == 4)
    check("offset が 0,0(再試行),100,200", [l[2]["offset"][0] for l in gets] == ["0", "0", "100", "200"])
    check("count=100 を送る", all(l[2]["count"][0] == "100" for l in gets))
    check("鍵は URL ではなくヘッダー（apiKey がパスに無い）", all("apiKey" not in l[2] for l in gets))
    raw = open(out_csv, "rb").read()
    check("BOM つき UTF-8", raw.startswith(b"\xef\xbb\xbf"))
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    check("250 行・重複なし", len(rows) == TOTAL and len({r["id"] for r in rows}) == TOTAL)
    check("カンマ・引用符・改行が壊れない", rows[0]["summary"] == '課題,1 "引用"' and rows[0]["description"] == "行1\n行2")
    check("カスタム属性が列になる", rows[0].get("カスタム:顧客") == "株式会社テスト")
    check("出力に鍵が出ない", KEY not in out + err)

    # 3. count-only・max-issues
    rc, out, err = run(["fetch", "--count-only"])
    check("--count-only は件数だけ", rc == 0 and out.strip() == str(TOTAL))
    STATE["log"].clear()
    rc, out, err = run(["fetch", "--max-issues", "120", "--format", "json", "-o", os.path.join(tmp, "o.json")])
    check("--max-issues 120 で打ち切り", rc == 0 and len(json.load(open(os.path.join(tmp, "o.json")))) == 120)

    # 4. 認証エラーの説明
    rc, out, err = run(["fetch", "--count-only"], dict(env, BACKLOG_API_KEY="wrong"))
    check("401 は終了1・原因の案内・鍵を出さない", rc == 1 and "認証" in err and "wrong" not in err)

    # 5. スペース形式
    rc, out, err = run(["fetch", "--dry-run"], dict(env, BACKLOG_SPACE="example.invalid.com", BACKLOG_TEST_HTTP=""))
    check("不正なホストは終了2", rc == 2 and "backlog.com" in err)
    rc, out, err = run(["fetch", "--dry-run"], dict(env, BACKLOG_SPACE="https://example.backlog.jp/", BACKLOG_TEST_HTTP=""))
    check(".backlog.jp も受け付ける", rc == 0 and "example.backlog.jp" in out)

    # 6. meta
    rc, out, err = run(["meta", "--project-id", "1"])
    check("meta は優先度と状態を出す", rc == 0 and "高" in out and "完了" in out and "customField" in out and "A社" in out)

    # 7. add
    good = os.path.join(tmp, "good.csv")
    with open(good, "w", encoding="utf-8", newline="") as f:
        f.write("summary,description,categoryId,dueDate\nA,説明,1;2,2026-11-01\nB,,,\nC,,,\n")
    STATE["log"].clear()
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3"])
    check("--yes なしは送らず終了2", rc == 2 and not [l for l in STATE["log"] if l[0] == "POST"])
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--dry-run"])
    check("add --dry-run は送らない", rc == 0 and not STATE["log"])
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--yes"])
    posts = [l for l in STATE["log"] if l[0] == "POST"]
    check("3 件登録", rc == 0 and len(posts) == 3)
    check("categoryId[] を複数で送る", posts[0][2]["categoryId[]"] == ["1", "2"])
    check("必須4つが全部付く", all(k in posts[1][2] for k in ("projectId", "summary", "issueTypeId", "priorityId")))
    bad = os.path.join(tmp, "bad.csv")
    with open(bad, "w", encoding="utf-8") as f:
        f.write("summary,priority\nA,高\nB,中\n")
    STATE["log"].clear()
    rc, out, err = run(["add", "--csv", bad, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--yes"])
    check("未対応の列は1件も送らず終了2", rc == 2 and "priority" in err and not STATE["log"])
    rc, out, err = run(["add", "--csv", bad.replace("bad", "x"), "--yes"])
    check("存在しない CSV は終了2", rc == 2)
    nores = os.path.join(tmp, "nores.csv")
    with open(nores, "w", encoding="utf-8") as f:
        f.write("summary\nA\n")
    rc, out, err = run(["add", "--csv", nores, "--yes"])
    check("必須 ID 不足は送らず終了2", rc == 2 and "projectId" in err)
    STATE["posts"], STATE["fail_post_at"] = 0, 2
    rc, out, err = run(["add", "--csv", good, "--project-id", "1", "--issue-type-id", "7", "--priority-id", "3", "--yes"])
    check("途中失敗は終了1・登録済みと重複を案内", rc == 1 and "登録済み 1 件" in err and "重複" in err and "権限" in err)
    STATE["fail_post_at"] = None

    # 8. set-status
    STATE["log"].clear()
    rc, out, err = run(["set-status", "--keys", "PRJ-1,PRJ-2", "--status-id", "4"])
    check("set-status は --yes なしで送らない", rc == 2 and not STATE["log"])
    rc, out, err = run(["set-status", "--keys", "PRJ-1,PRJ-2", "--status-id", "4", "--comment", "一括完了", "--yes"])
    pt = [l for l in STATE["log"] if l[0] == "PATCH"]
    check("2 件を PATCH・statusId とコメント", rc == 0 and len(pt) == 2 and pt[0][2]["statusId"] == ["4"] and pt[0][2]["comment"] == ["一括完了"])
    rc, out, err = run(["set-status", "--keys", "bad key!", "--status-id", "4", "--yes"])
    check("不正なキーは終了2", rc == 2)

    srv.shutdown()
    print("\n%d/%d 合格" % (sum(results), len(results)))
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
