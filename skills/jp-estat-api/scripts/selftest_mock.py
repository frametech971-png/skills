#!/usr/bin/env python3
"""estat_fetch.py の自己検査。ローカルのモックサーバーで NEXT_KEY のページングと欠損記号の扱いなどを確かめる。
実際の e-Stat には接続しない（appId も要らない）。Python 3.9 標準ライブラリだけ。

  python3 scripts/selftest_mock.py        # 全部通れば "ALL PASSED" で終了コード 0
"""
import contextlib
import csv
import gzip
import io
import json
import os
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estat_fetch  # noqa: E402

estat_fetch.time.sleep = lambda s: None  # 再試行・ページ間の待ちを省く

SECRET = "TESTAPPID1234567890"
LOG = []
MODE = {"name": "normal"}

ROWS = [
    {"@tab": "001", "@cat01": "000", "@area": "13000", "@time": "2020000000", "@unit": "人", "$": "13960000"},
    {"@tab": "001", "@cat01": "000", "@area": "27000", "@time": "2020000000", "@unit": "人", "$": "-"},
    {"@tab": "001", "@cat01": "000", "@area": "01000", "@time": "2020000000", "@unit": "人", "$": "…"},
    {"@tab": "001", "@cat01": "000", "@area": "02000", "@time": "2020000000", "@unit": "人", "$": "X", "@annotation": "J1"},
    {"@tab": "001", "@cat01": "000", "@area": "03000", "@time": "2020000000", "@unit": "人", "$": "***"},
]
CLASS_INF = {"CLASS_OBJ": [
    {"@id": "tab", "@name": "表章項目", "CLASS": {"@code": "001", "@name": "人口"}},
    {"@id": "cat01", "@name": "男女", "CLASS": [{"@code": "000", "@name": "総数"}]},
    {"@id": "area", "@name": "地域", "CLASS": [{"@code": "13000", "@name": "東京都"}, {"@code": "27000", "@name": "大阪府"},
                                               {"@code": "01000", "@name": "北海道"}, {"@code": "02000", "@name": "青森県"},
                                               {"@code": "03000", "@name": "岩手県"}]},
    {"@id": "time", "@name": "時間軸", "CLASS": [{"@code": "2020000000", "@name": "2020年"}]},
]}


def ok(status=0, msg="正常に終了しました。"):
    return {"STATUS": status, "ERROR_MSG": msg, "DATE": "2026-10-21T00:00:00.000+09:00"}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, obj, gz=False):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        if gz:
            raw = gzip.compress(raw)
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if gz:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        func = u.path.rsplit("/", 1)[-1]
        LOG.append((func, q))
        if q.get("appId") != SECRET:
            return self.send(403, {"GET_STATS_DATA": {"RESULT": ok(100, "認証に失敗しました。")}})
        m = MODE["name"]
        if func == "getStatsList":
            return self.send(200, {"GET_STATS_LIST": {"RESULT": ok(), "DATALIST_INF": {
                "NUMBER": 1, "RESULT_INF": {"FROM_NUMBER": 1, "TO_NUMBER": 1},
                "TABLE_INF": {"@id": "0000000000", "STAT_NAME": {"@code": "00200521", "$": "国勢調査"},
                              "TITLE": {"@no": "1", "$": "男女別人口"}, "SURVEY_DATE": "202010", "UPDATED_DATE": "2022-01-01"}}}})
        if func == "getMetaInfo":
            return self.send(200, {"GET_META_INFO": {"RESULT": ok(), "METADATA_INF": {
                "TABLE_INF": {"@id": q["statsDataId"], "TITLE": "男女別人口"}, "CLASS_INF": CLASS_INF}}})
        if m == "status1":
            return self.send(200, {"GET_STATS_DATA": {"RESULT": ok(1, "該当データはありませんでした。")}})
        if m == "status300":
            return self.send(400, {"GET_STATS_DATA": {"RESULT": ok(300, "statsDataId=[x]のデータは存在しません。")}})
        start, limit = int(q.get("startPosition", 1)), int(q.get("limit", 100000))
        chunk = ROWS[start - 1:start - 1 + limit]
        end = start - 1 + len(chunk)
        inf = {"TOTAL_NUMBER": len(ROWS), "FROM_NUMBER": start, "TO_NUMBER": end}
        if end < len(ROWS):
            inf["NEXT_KEY"] = start if m == "stuck" else end + 1
        sd = {"RESULT_INF": inf, "DATA_INF": {
            "NOTE": [{"@char": "-", "$": "事実のないもの"}, {"@char": "…", "$": "事実不詳又は調査を欠くもの"},
                     {"@char": "X", "$": "数字が秘匿されているもの"}],
            "ANNOTATION": {"@annotation": "J1", "$": "注記テスト"},
            "VALUE": chunk[0] if (m == "single" and len(chunk) == 1) else chunk}}
        if q.get("metaGetFlg") == "Y":
            sd["CLASS_INF"] = CLASS_INF
        self.send(200, {"GET_STATS_DATA": {"RESULT": ok(), "STATISTICAL_DATA": sd}}, gz=(m == "gzip"))


def run(argv, env=SECRET):
    out, errb = io.StringIO(), io.StringIO()
    if env is None:
        os.environ.pop("ESTAT_APP_ID", None)
    else:
        os.environ["ESTAT_APP_ID"] = env
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(errb):
        try:
            code = estat_fetch.main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), errb.getvalue()


FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILS.append(name)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/rest/3.0/app" % srv.server_port
    tmp = tempfile.mkdtemp(prefix="estat_selftest_")
    out = os.path.join(tmp, "o.csv")
    data = ["data", "--stats-data-id", "0000000000", "--base-url", base, "--out", out]

    # 1. ページング: limit=2 で 5 行 → 3 ページ
    MODE["name"] = "normal"
    del LOG[:]
    code, so, se = run(data + ["--limit", "2", "--cd-area", "13000,27000"])
    reqs = [q for f, q in LOG if f == "getStatsData"]
    check("paging: exit 0", code == 0, se)
    check("paging: startPosition が NEXT_KEY をたどる 1,3,5", [q["startPosition"] for q in reqs] == ["1", "3", "5"], reqs)
    check("paging: metaGetFlg は初回だけ Y", [q["metaGetFlg"] for q in reqs] == ["Y", "N", "N"])
    check("paging: replaceSpChar=0 で記号をそのまま受ける", all(q["replaceSpChar"] == "0" for q in reqs))
    check("paging: cdArea が渡る", all(q["cdArea"] == "13000,27000" for q in reqs))
    rows = read_csv(out)
    check("paging: CSV は 5 行", len(rows) == 5, len(rows))
    check("paging: コードと名称の列", rows[0]["area_code"] == "13000" and rows[0]["area_name"] == "東京都" and rows[0]["time_name"] == "2020年")
    check("paging: 次のページの行にも名称が付く", rows[4]["area_name"] == "岩手県")
    check("secret: appId が stdout/stderr に出ない", SECRET not in so + se)

    # 2. 欠損記号
    check("symbol: 数値は value_num に入る", rows[0]["value_num"] == "13960000" and rows[0]["symbol"] == "")
    check("symbol: '-' は空欄にせず symbol 列に残す", rows[1]["value"] == "-" and rows[1]["symbol"] == "-" and rows[1]["value_num"] == "")
    check("symbol: '…' の意味が NOTE から付く", rows[2]["symbol"] == "…" and "不詳" in rows[2]["symbol_note"])
    check("symbol: 'X' の意味と注記", rows[3]["symbol"] == "X" and "秘匿" in rows[3]["symbol_note"]
          and rows[3]["annotation_code"] == "J1" and rows[3]["annotation_text"] == "注記テスト")
    check("symbol: NOTE に無い '***' は説明なしと明記", rows[4]["symbol"] == "***" and "NOTE に説明なし" in rows[4]["symbol_note"])

    # 3. 1 ページで終わる / 単一 VALUE が dict / gzip
    for m in ("normal", "single", "gzip"):
        MODE["name"] = m
        code, so, se = run(data + ["--limit", "1" if m == "single" else "100000"])
        check("mode %s: exit 0 で行が取れる" % m, code == 0 and len(read_csv(out)) == 5, se)

    # 4. エラー
    MODE["name"] = "normal"
    p = os.path.join(tmp, "n.csv")
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p], env="WRONG")
    check("STATUS 100: exit 1 で原因と次の手", code == 1 and "原因" in se and "次の手" in se, (code, se))
    check("STATUS 100: 渡した appId を表示しない", "WRONG" not in se)
    check("STATUS 100: ファイルを作らない", not os.path.exists(p))
    MODE["name"] = "status1"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p])
    check("STATUS 1: exit 4 でファイルなし", code == 4 and not os.path.exists(p), (code, se))
    MODE["name"] = "status300"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p])
    check("STATUS 300 (HTTP 400): exit 1 で STATUS を読む", code == 1 and "STATUS 300" in se, (code, se))
    MODE["name"] = "stuck"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p, "--limit", "2"])
    check("NEXT_KEY が進まない: 止めて exit 1、CSV を書かない", code == 1 and "進んでいない" in se and not os.path.exists(p), (code, se))
    MODE["name"] = "normal"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p, "--max-pages", "2", "--limit", "2"])
    check("max-pages 超過: exit 1、途中の CSV を書かない", code == 1 and not os.path.exists(p), (code, se))
    pre = os.path.join(tmp, "pre.csv")
    with open(pre, "w") as f:
        f.write("old")
    run(["data", "--stats-data-id", "x", "--base-url", base, "--out", pre, "--max-pages", "2", "--limit", "2"])
    with open(pre) as f:
        check("失敗しても既存ファイルを壊さない", f.read() == "old")

    # 5. 引数・環境
    code, so, se = run(data, env=None)
    check("ESTAT_APP_ID なし: exit 2 と取り方の案内", code == 2 and "ESTAT_APP_ID" in se and "マイページ" in se, (code, se))
    code, so, se = run(data + ["--cd-area", ",".join(str(i) for i in range(101))])
    check("コード 101 個: exit 2（STATUS 105 を先回り）", code == 2 and "100" in se, (code, se))
    code, so, se = run(data + ["--param", "appId=evil"])
    check("--param で appId は上書き不可", code == 2, (code, se))
    code, so, se = run(data + ["--limit", "100001"])
    check("limit 超過: exit 2", code == 2)

    # 6. dry-run
    del LOG[:]
    code, so, se = run(data + ["--cd-area", "13000", "--dry-run"])
    check("dry-run: 通信しない", code == 0 and not LOG, so)
    check("dry-run: appId を伏せる", SECRET not in so and "appId=***" in so, so)
    code, so, se = run(data + ["--dry-run"], env=None)
    check("dry-run: appId 未設定でも動く", code == 0 and "未設定" in so)

    # 7. list / meta
    MODE["name"] = "normal"
    code, so, se = run(["list", "--search-word", "人口", "--base-url", base])
    check("list: statsDataId と表題を出す", code == 0 and "0000000000" in so and "男女別人口" in so, so + se)
    code, so, se = run(["meta", "--stats-data-id", "0000000000", "--base-url", base])
    check("meta: 地域コードと名称を出す", code == 0 and "13000" in so and "東京都" in so, so + se)

    # 8. 通信不可
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", "http://127.0.0.1:1/rest/3.0/app", "--out", p])
    check("通信不可: exit 3", code == 3 and "次の手" in se, (code, se))

    srv.shutdown()
    print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
