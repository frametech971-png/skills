#!/usr/bin/env python3
"""国税庁の法人番号システム Web-API と、適格請求書発行事業者公表システム Web-API を呼ぶ。

Python 3.9 以上・標準ライブラリだけ。法人番号の検査桁の検証はしない（形式＝桁数と T の有無だけ確かめる）。

  環境変数（アプリケーションID は引数に取らない）
    NTA_HOUJIN_APP_ID    法人番号 Web-API 用（13桁）。無ければ NTA_INVOICE_APP_ID を使う（インボイス用IDは両方に使える）
    NTA_INVOICE_APP_ID   適格請求書 Web-API 用（13桁）。インボイス用ID だけが使える
    NTA_HOUJIN_BASE / NTA_INVOICE_BASE   接続先の差し替え（テスト用。https か localhost/127.0.0.1 だけ）

  使い方
    python3 nta_lookup.py houjin-num   --number 5111101000006 --dry-run
    python3 nta_lookup.py houjin-num   --number 5111101000006,4111101000007 --history
    python3 nta_lookup.py houjin-name  --name 国税 --mode 2 --address 13 --all --format csv -o out.csv
    python3 nta_lookup.py houjin-diff  --from 2026-10-01 --to 2026-10-03 --all
    python3 nta_lookup.py invoice-num  --number T8040001999011
    python3 nta_lookup.py invoice-valid --number T8040001999011 --day 2026-10-23
    python3 nta_lookup.py invoice-diff --from 2026-10-01 --to 2026-10-03 --all

  終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り

通信できない環境（外部通信が禁止のチャット等）では実行できない。--dry-run は通信しないので、
組み立てた URL を確かめて、手元の環境で実行してもらう。
法的判断（登録の有無が何を意味するか）はしない。返すのは公表されている項目の値だけ。
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 1, 2
HOUJIN_BASE = "https://api.houjin-bangou.nta.go.jp"
INVOICE_BASE = "https://web-api.invoice-kohyo.nta.go.jp"
HOUJIN_VER = "4"
INVOICE_VER = "1"
MASK = "＊＊＊＊（環境変数から読み込み済み・表示しない）"
MAX_NUMBERS = 10          # 番号指定は1回10件まで（両API）
MAX_DIFF_DAYS = 50        # 期間指定は50日まで（両API）
HOUJIN_DIFF_MIN = datetime.date(2015, 12, 1)
HOUJIN_ASSIGN_MIN = datetime.date(2015, 10, 5)
INVOICE_DIFF_MIN = datetime.date(2021, 10, 1)
RETRY_WAITS = (2, 5)      # 500 系・通信エラーのときだけ。400/403/404 は再試行しない

# 公式の別紙2から。法人番号 API は3桁、インボイス API は4桁
HOUJIN_ERRORS = {
    "010": "取得期間開始日が指定されていません", "011": "取得期間開始日は YYYY-MM-DD 形式", "012": "取得期間開始日が存在しない日付",
    "013": "取得期間開始日は 2015-12-01 以降", "020": "取得期間終了日が指定されていません", "021": "取得期間終了日は YYYY-MM-DD 形式",
    "022": "取得期間終了日が存在しない日付", "030": "開始日が終了日より後", "031": "取得期間が最大50日を超えている",
    "040": "法人番号が指定されていません", "041": "法人番号は10件以内", "042": "法人番号は半角数字", "043": "法人番号は13桁",
    "050": "所在地は半角数字", "051": "所在地は2桁又は5桁（市区町村コードだけは不可）", "052": "所在地コードが存在しない",
    "060": "法人種別は4件以内", "061": "法人種別は半角数字", "062": "法人種別は2桁", "063": "法人種別の値が 01〜04 以外",
    "070": "応答形式(type)が指定されていません", "071": "応答形式は半角数字", "072": "応答形式は2桁", "073": "応答形式は 01/02/12 以外",
    "080": "変更履歴要否(history)は半角数字", "081": "history は1桁", "082": "history は 0/1 以外",
    "090": "分割番号(divide)は半角数字", "091": "分割番号が範囲外（分割数を超えた等）",
    "100": "商号又は名称(name)が指定されていません", "101": "name は UTF-8 で URL エンコード（全角/半角の別あり）",
    "102": "name は日本語150文字・英語300文字以内", "103": "name が組織名称（株式会社等）だけ",
    "110": "検索方式(mode)は半角数字", "111": "mode は1桁", "112": "mode の値が正しくない（1 前方一致 / 2 部分一致）",
    "120": "検索対象(target)は半角数字", "121": "target は1桁", "122": "target の値が正しくない（1/2/3）",
    "130": "変更履歴(change)は半角数字", "131": "change は1桁", "132": "change は 0/1 以外",
    "140": "登記記録の閉鎖等(close)は半角数字", "141": "close は1桁", "142": "close は 0/1 以外",
    "150": "法人番号指定年月日開始日(from)は YYYY-MM-DD 形式", "151": "from が存在しない日付", "152": "from は 2015-10-05 以降",
    "160": "法人番号指定年月日終了日(to)は YYYY-MM-DD 形式", "161": "to が存在しない日付", "170": "from が to より後",
    "180": "検索結果件数が多く返せない。条件を足す",
}
INVOICE_ERRORS = {
    "0001": "登録番号が指定されていません", "0002": "登録番号は10件以内", "0003": "登録番号n に値が指定されていません",
    "0004": "登録番号は14桁（T＋13桁）", "0005": "登録番号は T＋数字13桁",
    "0101": "取得期間開始日が指定されていません", "0102": "from は YYYY-MM-DD 形式", "0103": "from が存在しない日付",
    "0104": "from は 2021-10-01 以降", "0201": "取得期間終了日が指定されていません", "0202": "to は YYYY-MM-DD 形式",
    "0203": "to が存在しない日付", "0204": "to が from より前", "0205": "取得期間が最大50日を超えている",
    "0301": "判定基準日(day)が指定されていません", "0302": "day は YYYY-MM-DD 形式", "0303": "day が存在しない日付",
    "0401": "人格区分(division)は半角数字", "0402": "division は1桁", "0403": "division の値が正しくない（1 個人 / 2 法人）",
    "0501": "応答形式(type)が指定されていません", "0502": "type は半角数字", "0503": "type は2桁", "0504": "type は 01/11/21 以外",
    "0601": "履歴情報要否(history)は半角数字", "0602": "history は1桁", "0603": "history は 0/1 以外",
    "0701": "分割番号(divide)は半角数字", "0702": "分割番号が範囲外",
}
HTTP_HINTS = {
    403: "同一アプリケーションIDでの短時間の大量アクセスによるアクセス制限中（公式）。間隔を空け、件数を減らし、時間をおいて再開する。解除の方法は公式に記載なし（問い合わせ先: 各Web-APIの問合せフォーム）",
    404: "アプリケーションIDが未登録・無効（公式）。または URL（バージョン・機能名）の誤り。法人番号用IDでインボイスAPIを呼んでいないかも確かめる",
    500: "国税庁側の障害（公式）。時間をおいて再試行。メンテナンス告知は法人番号公表サイトに載る",
}

HOUJIN_CSV_COLUMNS = [
    "sequenceNumber", "corporateNumber", "process", "correct", "updateDate", "changeDate", "name", "nameImageId", "kind",
    "prefectureName", "cityName", "streetNumber", "addressImageId", "prefectureCode", "cityCode", "postCode",
    "addressOutside", "addressOutsideImageId", "closeDate", "closeCause", "successorCorporateNumber", "changeCause",
    "assignmentDate", "latest", "enName", "enPrefectureName", "enCityName", "enAddressOutside", "furigana", "hihyoji",
]


class UsageError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status, body, hint):
        super().__init__(hint)
        self.status, self.body, self.hint = status, body, hint


# ───────── 入力の検査（形式だけ。検査桁は見ない） ─────────

def parse_date(s, label):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s or ""):
        raise UsageError("%s は YYYY-MM-DD の形式で指定してください（入力: %r）" % (label, s))
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:]))
    except ValueError:
        raise UsageError("%s は存在しない日付です（入力: %s）" % (label, s))


def split_numbers(raw, kind):
    nums = [x.strip() for x in (raw or "").replace("，", ",").split(",") if x.strip()]
    if not nums:
        raise UsageError("--number が空です")
    if len(nums) > MAX_NUMBERS:
        raise UsageError("番号は1回 %d 件までです（%d 件）。分けて呼んでください" % (MAX_NUMBERS, len(nums)))
    pat = r"\d{13}" if kind == "houjin" else r"T\d{13}"
    for n in nums:
        if not re.fullmatch(pat, n):
            if kind == "houjin":
                raise UsageError("法人番号は半角数字13桁です（入力: %r）。先頭の T や - は付けない" % n)
            raise UsageError("登録番号は T＋半角数字13桁です（入力: %r）。法人番号13桁の前に大文字の T を付ける" % n)
    return nums


def check_range(frm, to, minimum, label):
    f, t = parse_date(frm, "--from"), parse_date(to, "--to")
    if f < minimum:
        raise UsageError("--from は %s 以降です（%s の下限）" % (minimum.isoformat(), label))
    if t < f:
        raise UsageError("--to は --from 以降にしてください")
    if (t - f).days > MAX_DIFF_DAYS:
        raise UsageError("期間は --from から %d 日以内です（%d 日）。区切って呼んでください" % (MAX_DIFF_DAYS, (t - f).days))


def check_csv_list(val, allowed, label, maxn):
    items = [x.strip() for x in val.split(",") if x.strip()]
    if len(items) > maxn or any(i not in allowed for i in items):
        raise UsageError("%s は %s のうち最大 %d 個をカンマ区切りで指定します（入力: %r）" % (label, "/".join(allowed), maxn, val))


def check_address(val):
    if not re.fullmatch(r"(\d{2}|\d{5})", val):
        raise UsageError("--address は都道府県コード2桁（国外は 99）か、都道府県＋市区町村の5桁です。市区町村だけは不可（エラー 051）")


# ───────── 接続先 ─────────

def pick_base(env_name, default):
    base = os.environ.get(env_name, "").strip().rstrip("/") or default
    host = urllib.parse.urlparse(base)
    local = host.hostname in ("localhost", "127.0.0.1")
    if host.scheme != "https" and not (host.scheme == "http" and local):
        raise UsageError("%s は https か localhost だけ使えます（アプリケーションIDを平文で送らないため）: %s" % (env_name, base))
    return base


def get_app_id(api, dry):
    if api == "houjin":
        names = ["NTA_HOUJIN_APP_ID", "NTA_INVOICE_APP_ID"]   # インボイス用IDは法人番号APIにも使える（公式）
    else:
        names = ["NTA_INVOICE_APP_ID"]
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            if not re.fullmatch(r"\d{13}", v) and not dry:
                sys.stderr.write("注意: アプリケーションIDは13桁の数字のはずです（公式）。値が違う可能性があります\n")
            return v
    if dry:
        return None
    raise UsageError("環境変数 %s が未設定です。取得方法は references/app-id-and-terms.md（届出から発行まで2週間〜1か月ほど）。値をコードや会話に書かない" % names[0])


# ───────── 通信 ─────────

def build_url(api, path, params, app_id):
    base = pick_base("NTA_HOUJIN_BASE", HOUJIN_BASE) if api == "houjin" else pick_base("NTA_INVOICE_BASE", INVOICE_BASE)
    ver = HOUJIN_VER if api == "houjin" else INVOICE_VER
    q = [("id", app_id or "")] + [(k, v) for k, v in params if v not in (None, "")]
    return "%s/%s/%s?%s" % (base, ver, path, urllib.parse.urlencode(q, quote_via=urllib.parse.quote, safe=","))


def explain_error(api, status, body):
    table = HOUJIN_ERRORS if api == "houjin" else INVOICE_ERRORS
    hint = HTTP_HINTS.get(status, "")
    code_re = r"\b\d{3}\b" if api == "houjin" else r"\b\d{4}\b"
    found = []
    for m in re.finditer(code_re, body or ""):
        c = m.group(0)
        if c in table and c not in found:
            found.append(c)
    if status == 400 and found:
        hint = "; ".join("エラーコード %s: %s" % (c, table[c]) for c in found)
    elif status == 400:
        hint = "リクエスト条件の誤り。応答本文のエラーコードを references/errors.md の表と照らす"
    return hint or "想定外の HTTP ステータス。応答本文を確認"


def fetch(api, url, timeout):
    last = None
    for wait in (0,) + RETRY_WAITS:
        if wait:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": "nta-lookup/1.0 (+python-urllib)"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            raw = e.read() or b""
            body = decode_text(raw)
            if e.code >= 500:
                last = ApiError(e.code, body, explain_error(api, e.code, body))
                continue
            raise ApiError(e.code, body, explain_error(api, e.code, body))
        except (urllib.error.URLError, OSError) as e:
            last = ApiError(0, "", "通信できません: %s。ネットワーク・プロキシ・DNS を確認（外部通信が禁止された環境では実行できない）" % e)
    raise last


def decode_text(raw):
    for enc in ("utf-8", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


# ───────── 応答の解釈 ─────────

def parse_houjin_xml(raw):
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise ApiError(200, decode_text(raw)[:300], "XML として読めません（%s）。エラー応答は CSV 形式で返る。本文を確認" % e)
    header = {k: (root.findtext(k) or "") for k in ("lastUpdateDate", "count", "divideNumber", "divideSize")}
    recs = []
    for c in root.findall("corporation"):
        recs.append({ch.tag: (ch.text or "").strip() for ch in c})
    return header, recs


def parse_invoice_json(raw):
    try:
        doc = json.loads(decode_text(raw))
    except ValueError as e:
        raise ApiError(200, decode_text(raw)[:300], "JSON として読めません（%s）。エラー応答は CSV 形式で返る。本文を確認" % e)
    header = {k: str(doc.get(k, "")) for k in ("lastUpdateDate", "count", "divideNumber", "divideSize")}
    recs = doc.get("announcement") or []
    if isinstance(recs, dict):
        recs = [recs]
    return header, recs


def run_query(api, path, params, args, app_id):
    """分割（divide）を順に取って (ヘッダー, 全レコード) を返す。--all が無ければ1回だけ。"""
    typ = "12" if api == "houjin" else "21"
    base_params = list(params) + [("type", typ)]
    divide, pages, records, header = max(1, getattr(args, "divide", 1)), 0, [], None
    while True:
        p = list(base_params)
        if divide > 1:
            p.append(("divide", str(divide)))
        url = build_url(api, path, p, app_id)
        raw = fetch(api, url, args.timeout)
        h, recs = parse_houjin_xml(raw) if api == "houjin" else parse_invoice_json(raw)
        header = header or h
        records.extend(recs)
        pages += 1
        size = int(h.get("divideSize") or 1)
        if not getattr(args, "all", False) or divide >= size:
            break
        if pages >= getattr(args, "max_pages", 100):
            sys.stderr.write("注意: --max-pages %d で打ち切りました（分割数 %d）。続きは --divide を使うか上限を上げる\n" % (getattr(args, "max_pages", 100), size))
            break
        divide += 1
        time.sleep(getattr(args, "sleep", 1.0))
    header["fetchedPages"] = str(pages)
    header["fetchedRecords"] = str(len(records))
    if not getattr(args, "all", False) and int(header.get("divideSize") or 1) > 1:
        sys.stderr.write("注意: 応答は %s 分割中の1つ目だけです（総件数 %s）。全部取るには --all\n" % (header["divideSize"], header["count"]))
    return header, records


# ───────── 出力 ─────────

def emit(header, records, args, api):
    if args.format == "csv":
        cols = HOUJIN_CSV_COLUMNS if api == "houjin" else None
        if cols is None:
            cols = []
            for r in records:
                for k in r:
                    if k not in cols:
                        cols.append(k)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(cols)
        for r in records:
            w.writerow([r.get(c, "") for c in cols])
        text = buf.getvalue()
    else:
        text = json.dumps({"header": header, "records": records}, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8-sig" if args.bom else "utf-8", newline="") as f:
            f.write(text)
        sys.stderr.write("%d 件を %s に書きました（総件数 %s）\n" % (len(records), args.output, header.get("count")))
    else:
        sys.stdout.write(text)


def note_missing(api, numbers, records):
    key = "corporateNumber" if api == "houjin" else "registratedNumber"
    got = {r.get(key) for r in records}
    missing = [n for n in numbers if n not in got]
    if missing:
        sys.stderr.write("応答に出てこなかった番号: %s（該当なしの可能性。意味づけは法的判断になるため、このスクリプトは断定しない）\n" % ", ".join(missing))


# ───────── サブコマンド ─────────

def build_request(args):
    cmd = args.cmd
    if cmd == "houjin-num":
        nums = split_numbers(args.number, "houjin")
        return "houjin", "num", [("number", ",".join(nums)), ("history", "1" if args.history else "0")], nums
    if cmd == "houjin-diff":
        check_range(args.frm, args.to, HOUJIN_DIFF_MIN, "法人番号 API の差分")
        p = [("from", args.frm), ("to", args.to)]
        if args.address:
            check_address(args.address); p.append(("address", args.address))
        if args.kind:
            check_csv_list(args.kind, ["01", "02", "03", "04"], "--kind", 4); p.append(("kind", args.kind))
        return "houjin", "diff", p, []
    if cmd == "houjin-name":
        if not args.name.strip():
            raise UsageError("--name が空です")
        if len(args.name) > 150:
            raise UsageError("--name は日本語150文字（英語表記検索は300文字）以内です")
        if args.target == "3" and re.search(r"[^\x20-\x7e]", args.name):
            raise UsageError("--target 3（英語表記）は半角英数記号で指定します。全角文字が含まれています")
        p = [("name", args.name), ("mode", args.mode), ("target", args.target), ("change", args.change), ("close", args.close)]
        if args.address:
            check_address(args.address); p.append(("address", args.address))
        if args.kind:
            check_csv_list(args.kind, ["01", "02", "03", "04"], "--kind", 4); p.append(("kind", args.kind))
        if args.assigned_from:
            if parse_date(args.assigned_from, "--assigned-from") < HOUJIN_ASSIGN_MIN:
                raise UsageError("--assigned-from は 2015-10-05 以降です（エラー 152）")
            p.append(("from", args.assigned_from))
        if args.assigned_to:
            parse_date(args.assigned_to, "--assigned-to"); p.append(("to", args.assigned_to))
        return "houjin", "name", p, []
    if cmd == "invoice-num":
        nums = split_numbers(args.number, "invoice")
        return "invoice", "num", [("number", ",".join(nums)), ("history", "1" if args.history else "0")], nums
    if cmd == "invoice-valid":
        nums = split_numbers(args.number, "invoice")
        parse_date(args.day, "--day")
        return "invoice", "valid", [("number", ",".join(nums)), ("day", args.day)], nums
    if cmd == "invoice-diff":
        check_range(args.frm, args.to, INVOICE_DIFF_MIN, "インボイス API の差分")
        p = [("from", args.frm), ("to", args.to)]
        if args.division:
            p.append(("division", args.division))
        return "invoice", "diff", p, []
    raise UsageError("不明なサブコマンド: " + cmd)


def main(argv=None):
    ap = argparse.ArgumentParser(description="国税庁 法人番号 Web-API / 適格請求書発行事業者公表 Web-API の照会（標準ライブラリだけ）。アプリケーションIDは環境変数から読む。",
                                 epilog="終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, divide=True):
        p.add_argument("--dry-run", action="store_true", help="通信せず、組み立てた URL を表示する（IDは伏せ字）")
        p.add_argument("--format", choices=["json", "csv"], default="json", help="出力形式（既定 json）")
        p.add_argument("-o", "--output", help="出力ファイル（UTF-8）。省略時は標準出力")
        p.add_argument("--bom", action="store_true", help="CSV/JSON を BOM つきで書く（Excel で開く用）")
        p.add_argument("--timeout", type=float, default=30.0, help="1回の通信の待ち秒数（既定 30）")
        if divide:
            p.add_argument("--all", action="store_true", help="分割された応答を divideSize まで全部取る")
            p.add_argument("--divide", type=int, default=1, help="取り始める分割番号（既定 1。中断した続きから取る用）")
            p.add_argument("--max-pages", type=int, default=100, help="--all の最大リクエスト数（既定 100）")
            p.add_argument("--sleep", type=float, default=1.0, help="--all のリクエスト間隔の秒（既定 1.0。短時間の大量アクセスは禁止・403 の原因）")

    p = sub.add_parser("houjin-num", help="法人番号から法人情報（最大10件）"); common(p, False)
    p.add_argument("--number", required=True, help="13桁の法人番号。カンマ区切りで最大10件")
    p.add_argument("--history", action="store_true", help="変更履歴も取る（history=1）")

    p = sub.add_parser("houjin-name", help="法人名から検索（Ver.2.0 以降）"); common(p)
    p.add_argument("--name", required=True, help="商号又は名称（URLエンコードはこちらでする）")
    p.add_argument("--mode", choices=["1", "2"], default="1", help="1 前方一致（既定。株式会社等を除いた名前の先頭）/ 2 部分一致")
    p.add_argument("--target", choices=["1", "2", "3"], default="1", help="1 JIS第一第二水準のあいまい検索（既定）/ 2 JIS第一〜第四水準の完全一致 / 3 英語表記")
    p.add_argument("--address", help="都道府県コード2桁（国外99）か 5桁（都道府県＋市区町村）")
    p.add_argument("--kind", help="法人種別 01 国の機関 02 地方公共団体 03 設立登記法人 04 外国会社等・その他（カンマ区切り最大4）")
    p.add_argument("--change", choices=["0", "1"], default="0", help="1 で旧名称も検索対象（既定 0）。旧名称で当たると最新情報は返らない")
    p.add_argument("--close", choices=["0", "1"], default="1", help="0 で登記記録の閉鎖等を除く（既定 1＝含める）")
    p.add_argument("--assigned-from", help="法人番号指定年月日の開始日 YYYY-MM-DD（2015-10-05 以降）")
    p.add_argument("--assigned-to", help="法人番号指定年月日の終了日")

    p = sub.add_parser("houjin-diff", help="期間（更新年月日）を指定して差分を取る。最大50日"); common(p)
    p.add_argument("--from", dest="frm", required=True, help="開始日 YYYY-MM-DD（2015-12-01 以降）")
    p.add_argument("--to", required=True, help="終了日 YYYY-MM-DD（開始日から50日以内）")
    p.add_argument("--address", help="都道府県コード2桁か5桁")
    p.add_argument("--kind", help="法人種別（カンマ区切り最大4）")

    p = sub.add_parser("invoice-num", help="登録番号（T＋13桁）で照会（最大10件）"); common(p, False)
    p.add_argument("--number", required=True, help="T＋13桁。カンマ区切りで最大10件")
    p.add_argument("--history", action="store_true", help="登録・取消・失効の履歴も取る")

    p = sub.add_parser("invoice-valid", help="登録番号と判定基準日で、その日付に基づく直近の情報を取る"); common(p, False)
    p.add_argument("--number", required=True, help="T＋13桁。カンマ区切りで最大10件")
    p.add_argument("--day", required=True, help="判定基準日 YYYY-MM-DD")

    p = sub.add_parser("invoice-diff", help="期間（更新年月日）を指定して差分を取る。最大50日"); common(p)
    p.add_argument("--from", dest="frm", required=True, help="開始日 YYYY-MM-DD（2021-10-01 以降）")
    p.add_argument("--to", required=True, help="終了日 YYYY-MM-DD（開始日から50日以内）")
    p.add_argument("--division", choices=["1", "2"], help="1 個人 / 2 法人（省略で両方）")

    args = ap.parse_args(argv)
    try:
        api, path, params, numbers = build_request(args)
        app_id = get_app_id(api, args.dry_run)
        if args.dry_run:
            typ = "12" if api == "houjin" else "21"
            url = build_url(api, path, list(params) + [("type", typ)], "IDPLACEHOLDER").replace("IDPLACEHOLDER", MASK)
            print("GET " + url)
            print("（--dry-run: 通信していません。環境変数 %s は%s）" % ("NTA_HOUJIN_APP_ID" if api == "houjin" else "NTA_INVOICE_APP_ID", "設定済み" if app_id else "未設定"))
            return EXIT_OK
        header, records = run_query(api, path, params, args, app_id)
        emit(header, records, args, api)
        if numbers:
            note_missing(api, numbers, records)
        return EXIT_OK
    except UsageError as e:
        sys.stderr.write("入力エラー: %s\n" % e)
        return EXIT_USAGE
    except ApiError as e:
        sys.stderr.write("失敗: HTTP %s\n原因の候補: %s\n" % (e.status or "-", e.hint))
        if e.body:
            sys.stderr.write("応答本文（先頭300字）: %s\n" % e.body[:300].replace(os.environ.get("NTA_HOUJIN_APP_ID", "\0"), "＊＊＊＊").replace(os.environ.get("NTA_INVOICE_APP_ID", "\0"), "＊＊＊＊"))
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
