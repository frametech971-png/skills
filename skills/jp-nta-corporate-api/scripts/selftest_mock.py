#!/usr/bin/env python3
"""nta_lookup.py の自己検証。手元にモックの国税庁 Web-API を立てて、分割取得・エラー・伏せ字を確かめる。

本物には接続しない（127.0.0.1 だけ）。Python 3.9 以上・標準ライブラリだけ。
モックの形式は公式仕様書（references/api-spec.md の出典）の説明に合わせたもの。実サーバーの応答との一致は未検証。

  python3 scripts/selftest_mock.py     # 終了コード 0 で全部合格
"""
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "nta_lookup.py")
GOOD_ID = "1234567890123"
FAILS = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        FAILS.append(name)
        print("     " + str(detail)[:400])


class State:
    def __init__(self):
        self.log = []          # (path, params)
        self.fail500 = 0       # 次の n 回は 500 を返す


def houjin_xml(count, divide, size, rows):
    items = "".join(
        "<corporation><sequenceNumber>%d</sequenceNumber><corporateNumber>%s</corporateNumber><process>01</process>"
        "<name>%s</name><kind>301</kind><prefectureName>東京都</prefectureName><latest>1</latest></corporation>" % r
        for r in rows)
    return ('<?xml version="1.0" encoding="UTF-8"?><corporations><lastUpdateDate>2026-10-22</lastUpdateDate><count>%d</count>'
            "<divideNumber>%d</divideNumber><divideSize>%d</divideSize>%s</corporations>" % (count, divide, size, items)).encode("utf-8")


def make_handler(st):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype="text/plain; charset=UTF-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            st.log.append((u.path, q))
            if st.fail500 > 0:
                st.fail500 -= 1
                return self.send(500, "システムエラー".encode("utf-8"))
            if q.get("id") == "0000000000000":
                return self.send(404, b"")
            if q.get("id") == "9999999999999":
                return self.send(403, b"")
            if q.get("id") != GOOD_ID:
                return self.send(404, b"")
            parts = u.path.strip("/").split("/")
            ver, fn = parts[0], parts[1]
            if ver == "4":      # 法人番号
                if fn == "num":
                    nums = q.get("number", "").split(",")
                    if len(nums) > 10:
                        return self.send(400, '"400","041","法人番号は10件以内で指定してください。"'.encode("utf-8"))
                    rows = [(i + 1, n, "株式会社テスト%d" % (i + 1)) for i, n in enumerate(nums) if n != "9999999999990"]
                    return self.send(200, houjin_xml(len(rows), 1, 1, rows), "application/xml")
                if fn == "name":
                    if q.get("mode") == "9":
                        return self.send(400, '400,112,"商号又は名称検索方式の項目値が正しくありません。"'.encode("utf-8"))
                    div = int(q.get("divide", "1"))
                    # 4500 件を 2000 件ずつ 3 分割
                    total, size = 4500, 3
                    if div > size:
                        return self.send(400, '400,091,"分割番号はZZZZ9以下で指定してください。"'.encode("utf-8"))
                    start = (div - 1) * 2000
                    n = min(2000, total - start)
                    rows = [(start + i + 1, "%013d" % (start + i + 1), "名前" + urllib.parse.unquote(q.get("name", ""))) for i in range(n)]
                    return self.send(200, houjin_xml(total, div, size, rows), "application/xml")
                if fn == "diff":
                    if q.get("address") == "99999":
                        return self.send(400, '400,052,"所在地の項目値が正しくありません。"'.encode("utf-8"))
                    if q.get("from", "") < "2015-12-01":
                        return self.send(400, '400,013,"取得期間開始日は2015-12-01以降を指定してください。"'.encode("utf-8"))
                    return self.send(200, houjin_xml(1, 1, 1, [(1, "1000000000001", "差分株式会社")]), "application/xml")
            if ver == "1":      # インボイス
                def doc(div, size, total, nums):
                    return json.dumps({"lastUpdateDate": "2026-10-22", "count": str(total), "divideNumber": str(div), "divideSize": str(size),
                                       "announcement": [{"sequenceNumber": str(i + 1), "registratedNumber": n, "process": "01", "latest": "1",
                                                         "registrationDate": "2023-10-01", "name": "株式会社インボイス公表", "expireDate": "", "disposalDate": ""}
                                                        for i, n in enumerate(nums)]}, ensure_ascii=False).encode("utf-8")
                if fn in ("num", "valid"):
                    nums = [n for n in q.get("number", "").split(",") if n != "T0000000000000"]
                    if fn == "valid" and not q.get("day"):
                        return self.send(400, '400,0301,"判定基準日が指定されていません。"'.encode("utf-8"))
                    return self.send(200, doc(1, 1, len(nums), nums), "application/json")
                if fn == "diff":
                    div = int(q.get("divide", "1"))
                    total, size = 1200, 3
                    start = (div - 1) * 500
                    n = min(500, total - start)
                    return self.send(200, doc(div, size, total, ["T%013d" % (start + i + 1) for i in range(n)]), "application/json")
            return self.send(404, b"")
    return H


def run(port, args, env_extra=None, base_env=True):
    env = {"PATH": os.environ.get("PATH", ""), "NTA_HOUJIN_BASE": "http://127.0.0.1:%d" % port,
           "NTA_INVOICE_BASE": "http://127.0.0.1:%d" % port}
    if base_env:
        env["NTA_HOUJIN_APP_ID"] = GOOD_ID
        env["NTA_INVOICE_APP_ID"] = GOOD_ID
    env.update(env_extra or {})
    return subprocess.run([sys.executable, "-I", SCRIPT] + args, capture_output=True, text=True, env=env, timeout=60)


def main():
    st = State()
    srv = http.server.HTTPServer(("127.0.0.1", 0), make_handler(st))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    tmp = tempfile.mkdtemp()

    # 1. --dry-run: 通信ゼロ・IDが出ない
    n0 = len(st.log)
    r = run(port, ["houjin-num", "--number", "5111101000006", "--dry-run"])
    check("dry-run は通信せず ID を出さない", r.returncode == 0 and len(st.log) == n0 and GOOD_ID not in r.stdout + r.stderr and "＊＊＊＊" in r.stdout, (r.stdout, r.stderr))
    r = run(port, ["invoice-num", "--number", "T8040001999011", "--dry-run"], base_env=False)
    check("dry-run は ID 未設定でも動き、未設定と表示する", r.returncode == 0 and "未設定" in r.stdout, (r.stdout, r.stderr))

    # 2. 環境変数が無い → 終了コード2
    r = run(port, ["houjin-num", "--number", "5111101000006"], base_env=False)
    check("ID 未設定は終了コード2で取得先を案内", r.returncode == 2 and "NTA_HOUJIN_APP_ID" in r.stderr, r.stderr)

    # 3. 法人番号の取得（XML を解釈して JSON に）
    r = run(port, ["houjin-num", "--number", "5111101000006,4111101000007"])
    doc = json.loads(r.stdout) if r.returncode == 0 else {}
    check("houjin-num が2件を JSON で返す", r.returncode == 0 and len(doc.get("records", [])) == 2 and doc["header"]["count"] == "2", (r.stdout, r.stderr))
    check("type=12 と history=0 を付けて送る", st.log[-1][1].get("type") == "12" and st.log[-1][1].get("history") == "0", st.log[-1])
    r = run(port, ["houjin-num", "--number", "5111101000006,9999999999990"])
    check("応答に無い番号を知らせる（断定しない）", "9999999999990" in r.stderr and "断定しない" in r.stderr, r.stderr)

    # 4. 入力検査（通信前に弾く）
    n0 = len(st.log)
    r = run(port, ["houjin-num", "--number", ",".join(["5111101000006"] * 11)])
    check("11件は通信前に弾く", r.returncode == 2 and "10" in r.stderr and len(st.log) == n0, r.stderr)
    r = run(port, ["invoice-num", "--number", "8040001999011"])
    check("T 無しの登録番号は弾く", r.returncode == 2 and "T" in r.stderr and len(st.log) == n0, r.stderr)
    r = run(port, ["houjin-diff", "--from", "2026-01-01", "--to", "2026-03-01"])
    check("51日以上の期間は弾く", r.returncode == 2 and "50" in r.stderr and len(st.log) == n0, r.stderr)
    r = run(port, ["houjin-diff", "--from", "2015-11-30", "--to", "2015-12-02"])
    check("法人番号 diff の下限(2015-12-01)未満は弾く", r.returncode == 2 and "2015-12-01" in r.stderr, r.stderr)
    r = run(port, ["invoice-diff", "--from", "2021-09-30", "--to", "2021-10-02"])
    check("インボイス diff の下限(2021-10-01)未満は弾く", r.returncode == 2 and "2021-10-01" in r.stderr, r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--address", "131"])
    check("市区町村だけ/3桁の address は弾く", r.returncode == 2 and "address" in r.stderr, r.stderr)

    # 5. 名称検索: URL エンコードと分割取得
    r = run(port, ["houjin-name", "--name", "国税", "--mode", "2", "--all", "--sleep", "0", "-o", os.path.join(tmp, "n.json")])
    got = json.load(open(os.path.join(tmp, "n.json"), encoding="utf-8")) if r.returncode == 0 else {}
    divs = [q.get("divide", "1") for p, q in st.log[-3:]]
    check("4500件を3分割で全部取る", r.returncode == 0 and len(got.get("records", [])) == 4500 and divs == ["1", "2", "3"], (r.stderr, divs))
    check("name は UTF-8 で URL エンコードされて届く", st.log[-1][1].get("name") == "国税" and st.log[-1][1].get("mode") == "2", st.log[-1])
    check("2回目以降だけ divide を付ける（1回目は付けない）", "divide" not in st.log[-3][1], st.log[-3])
    r = run(port, ["houjin-name", "--name", "国税", "--sleep", "0"])
    check("--all 無しは1回だけ取り、分割を注意する", r.returncode == 0 and "--all" in r.stderr and json.loads(r.stdout)["header"]["fetchedPages"] == "1", r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--all", "--max-pages", "2", "--sleep", "0"])
    check("--max-pages で打ち切り、注意する", r.returncode == 0 and "打ち切り" in r.stderr and json.loads(r.stdout)["header"]["fetchedPages"] == "2", r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--all", "--sleep", "0", "--format", "csv", "--bom", "-o", os.path.join(tmp, "n.csv")])
    raw = open(os.path.join(tmp, "n.csv"), "rb").read()
    check("CSV は BOM つき UTF-8 で列名が1行目", raw.startswith(b"\xef\xbb\xbf") and raw.decode("utf-8-sig").splitlines()[0].startswith("sequenceNumber,corporateNumber"), raw[:80])

    # 6. インボイス
    r = run(port, ["invoice-valid", "--number", "T8040001999011,T0000000000000", "--day", "2026-10-23"])
    doc = json.loads(r.stdout) if r.returncode == 0 else {}
    check("invoice-valid が JSON を返し、無い番号を知らせる", r.returncode == 0 and len(doc["records"]) == 1 and "T0000000000000" in r.stderr, (r.stdout, r.stderr))
    check("valid に type=21 と day を付ける", st.log[-1][0] == "/1/valid" and st.log[-1][1].get("type") == "21" and st.log[-1][1].get("day") == "2026-10-23", st.log[-1])
    r = run(port, ["invoice-diff", "--from", "2026-10-01", "--to", "2026-10-03", "--all", "--sleep", "0"])
    check("invoice-diff を 500件ずつ3分割で1200件取る", r.returncode == 0 and len(json.loads(r.stdout)["records"]) == 1200, r.stderr)

    # 7. エラー
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": "0000000000000"})
    check("404 は ID 無効の可能性を案内（再試行しない）", r.returncode == 1 and "404" in r.stderr and "無効" in r.stderr, r.stderr)
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": "9999999999999"})
    check("403 はアクセス制限と案内", r.returncode == 1 and "アクセス制限" in r.stderr, r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--no-such-option"])
    check("未知のオプションは argparse が終了コード2", r.returncode == 2, r.stderr)
    r = run(port, ["houjin-diff", "--from", "2026-10-01", "--to", "2026-10-02", "--address", "99999"])
    check("400 の本文からエラーコードを引いて原因を出す", r.returncode == 1 and "エラーコード 052" in r.stderr and "400" in r.stderr, r.stderr)
    st.fail500 = 1
    n0 = len(st.log)
    r = run(port, ["houjin-num", "--number", "5111101000006"])
    check("500 は1回再試行して成功する", r.returncode == 0 and len(st.log) - n0 == 2, (r.returncode, r.stderr))
    st.fail500 = 10
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": GOOD_ID})
    st.fail500 = 0
    check("500 が続けば終了コード1で国税庁側の障害と案内", r.returncode == 1 and "障害" in r.stderr, r.stderr)

    # 8. ID が出力に出ない
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": "0000000000000"})
    check("失敗時の出力にも ID が出ない", "0000000000000" not in r.stdout + r.stderr, r.stderr)

    # 9. https 以外の接続先は拒否（ID の平文送信防止）
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_BASE": "http://example.com"})
    check("http の外部ホストは拒否", r.returncode == 2 and "https" in r.stderr, r.stderr)

    # 10. --help
    r = subprocess.run([sys.executable, "-I", SCRIPT, "--help"], capture_output=True, text=True)
    check("--help が終了コード0", r.returncode == 0 and "houjin-num" in r.stdout and "invoice-valid" in r.stdout)

    srv.shutdown()
    print("\n" + ("OK 全部通りました" if not FAILS else "失敗 %d 件: %s" % (len(FAILS), FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
