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
