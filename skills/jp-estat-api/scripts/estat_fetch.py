#!/usr/bin/env python3
"""e-Stat API 3.0 から統計表の検索・メタ情報・統計データを取得する。Python 3.9 の標準ライブラリだけで動く。

  python3 scripts/estat_fetch.py list --search-word 人口 --survey-years 2020
  python3 scripts/estat_fetch.py meta --stats-data-id 0000000000
  python3 scripts/estat_fetch.py data --stats-data-id 0000000000 --cd-area 13000,27000 --cd-time 2020000000 --out out.csv
  python3 scripts/estat_fetch.py data --stats-data-id 0000000000 --cd-area 13000 --out out.csv --dry-run

appId は環境変数 ESTAT_APP_ID から読む（コマンドラインには渡さない。履歴に残るため）。
data は NEXT_KEY をたどって全ページを取得し、CSV に書く。欠損・秘匿の記号（- … X * など）は
空欄にせず、value 列に原文、value_num 列に数値（記号なら空）、symbol 列に記号、symbol_note 列にその意味を残す。

終了コード: 0 正常 / 1 API エラー・HTTP エラー / 2 引数・環境の誤り / 3 通信できない / 4 該当データなし
実行できない環境（外部通信不可のコード実行環境など）では、references/api-spec.md のとおり URL を組み立てて
ユーザーのブラウザかシェルで実行してもらう。--dry-run は通信せず URL（appId は伏せる）だけ出す。
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.e-stat.go.jp/rest/3.0/app"
ENV_NAME = "ESTAT_APP_ID"
MAX_LIMIT = 100000  # 仕様の既定値。1 回の取得は最大 10 万件（FAQ Q5-7）
NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")
RESERVED = {"appid", "statsdataid", "startposition", "limit", "replacespchar", "lang", "metagetflg", "cntgetflg"}

# STATUS → (原因, 次の手)。出典: API 仕様 3.0 のエラーコード一覧（references/api-spec.md）
STATUS_HELP = {
    100: ("appId が認証されなかった（未指定・誤り・削除済み）", "マイページで appId を確かめ、ESTAT_APP_ID を設定し直す。前後の空白と、再発行で無効になった古い ID に注意"),
    101: ("必須パラメータが足りない", "メッセージの {0} に出ているパラメータを足す（statsDataId と appId は必須）"),
    102: ("パラメータの値が正しくない・範囲外", "コードは meta で調べ直す。limit は 1 以上、startPosition は 1 以上"),
    103: ("パラメータの値が長すぎる", "メッセージの上限バイト数以内に短くする"),
    104: ("パラメータに使えない文字が入っている", "URL エンコード（UTF-8）と文字種を確かめる。コードの # は %23"),
    105: ("1 つのパラメータに指定したコードが 100 個を超えた", "コードを 100 個以下に分けて、別々に実行する。lvArea などの階層指定で絞る手もある"),
    200: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する。続くなら e-Stat のお問い合わせへ"),
    201: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する"),
    202: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する"),
    203: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する"),
    299: ("e-Stat 側の予期しないエラー", "しばらく待ってから再実行する。続くなら e-Stat のお問い合わせへ"),
    300: ("指定した ID のデータが存在しない", "statsDataId を list で調べ直す（桁のコピー漏れが多い）"),
}


class Fatal(Exception):
    def __init__(self, msg, code=1):
        Exception.__init__(self, msg)
        self.msg = msg
        self.code = code


def err(msg):
    sys.stderr.write(msg + "\n")


def mask(text, app_id):
    if app_id:
        text = text.replace(app_id, "***")
        text = text.replace(urllib.parse.quote(app_id, safe=""), "***")
    return text


# ───────── 通信 ─────────

def build_url(base, func, params, fmt="json"):
    path = base.rstrip("/") + "/" + (fmt + "/" if fmt else "") + func
    return path + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def http_get_json(url, app_id, retries=3, timeout=60):
    """JSON を取得する。5xx と通信エラーだけ再試行する（2 秒, 4 秒, 8 秒）。"""
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "jp-estat-api-skill/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                raw = res.read()
                if res.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
                if e.headers.get("Content-Encoding", "").lower() == "gzip":
                    body = gzip.decompress(body)
            except Exception:
                pass
            if e.code >= 500 and attempt < retries:
                last = "HTTP %d" % e.code
                time.sleep(2 ** (attempt + 1))
                continue
            # 本文に JSON の RESULT があれば、その STATUS を優先して読む
            try:
                return json.loads(body.decode("utf-8"))
            except Exception:
                raise Fatal("HTTP %d が返った。原因: appId の誤り・パラメータの誤り・e-Stat 側の障害のどれか。"
                            "次の手: --dry-run で URL を確かめ、数分おいて再実行する。" % e.code, 1)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            last = mask(str(getattr(e, "reason", e)), app_id)
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
    raise Fatal("api.e-stat.go.jp に通信できない（%s）。原因: ネットワーク遮断・プロキシ・外部通信できない実行環境。"
                "次の手: 通信できる環境で実行するか、--dry-run の URL をユーザーのブラウザで開いてもらう。" % last, 3)
    # unreachable


def find_result(doc):
    """応答のどこにあっても RESULT を探す（エラー時は包みのキーが違う可能性があるため）。"""
    if isinstance(doc, dict):
        if "RESULT" in doc and isinstance(doc["RESULT"], dict):
            return doc["RESULT"], doc
        for v in doc.values():
            if isinstance(v, dict):
                r = find_result(v)
                if r:
                    return r
    return None


def check_status(doc, app_id):
    """STATUS を確かめ、(status, body) を返す。100 以上は Fatal。"""
    found = find_result(doc)
    if not found:
        raise Fatal("応答に RESULT が無い。原因: e-Stat 側の仕様変更または想定外の応答。次の手: --dry-run の URL をブラウザで開いて確かめる。", 1)
    result, body = found
    try:
        status = int(result.get("STATUS"))
    except (TypeError, ValueError):
        raise Fatal("STATUS を読めなかった: %r" % (result.get("STATUS"),), 1)
    msg = result.get("ERROR_MSG", "")
    if status >= 100:
        cause, nxt = STATUS_HELP.get(status, ("未知のエラーコード", "references/api-spec.md のエラーコード表と公式仕様を確かめる"))
        raise Fatal(mask("STATUS %d: %s\n  原因: %s\n  次の手: %s" % (status, msg, cause, nxt), app_id), 1)
    return status, body


# ───────── JSON の正規化 ─────────

def aslist(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def text_of(x):
    """{"@no": "..", "$": "text"} または文字列 から文字列を取る。"""
    if isinstance(x, dict):
        return str(x.get("$", ""))
    return "" if x is None else str(x)


def class_map(class_inf):
    """CLASS_INF → ({dim: {code: name}}, {dim: 見出し}, {(dim, code): unit})。"""
    names, labels, units = {}, {}, {}
    for obj in aslist((class_inf or {}).get("CLASS_OBJ")):
        dim = obj.get("@id")
        labels[dim] = obj.get("@name", "")
        names[dim] = {}
        for c in aslist(obj.get("CLASS")):
            names[dim][c.get("@code")] = c.get("@name", "")
            if c.get("@unit"):
                units[(dim, c.get("@code"))] = c.get("@unit")
    return names, labels, units


def dim_order(keys):
    order = ["tab"] + ["cat%02d" % i for i in range(1, 16)] + ["area", "time"]
    return [d for d in order if d in keys]


def classify(value):
    """値の原文を (value_num, symbol) に分ける。数値なら symbol は空、記号なら value_num は空。"""
    v = value.strip()
    if NUMERIC.match(v):
        return v, ""
    return "", v if v else "(空)"


# ───────── 引数 ─────────

def parse_extra(pairs):
    out = []
    for p in pairs or []:
        if "=" not in p:
            raise Fatal("--param は KEY=VALUE の形で指定する: %s" % p, 2)
        k, v = p.split("=", 1)
        if k.lower() in RESERVED:
            raise Fatal("--param で %s は上書きできない（専用の引数を使う）" % k, 2)
        out.append((k, v))
    return out


def check_codes(name, value):
    n = len([c for c in value.split(",") if c])
    if n > 100:
        raise Fatal("%s のコードが %d 個ある。1 つのパラメータに指定できるのは 100 個まで（STATUS 105）。"
                    "次の手: 100 個以下に分けて複数回実行する。" % (name, n), 2)


def common_filters(args):
    params = []
    for flag, key in (("cd_tab", "cdTab"), ("cd_cat01", "cdCat01"), ("cd_area", "cdArea"), ("cd_time", "cdTime")):
        v = getattr(args, flag, None)
        if v:
            check_codes(key, v)
            params.append((key, v))
    for k, v in parse_extra(getattr(args, "param", None)):
        if k.startswith("cd"):
            check_codes(k, v)
        params.append((k, v))
    return params


def get_app_id(required):
    app_id = os.environ.get(ENV_NAME, "").strip()
    if not app_id and required:
        raise Fatal("環境変数 %s が未設定。原因: appId をまだ取っていない、または設定していない。\n"
                    "  次の手: e-Stat のユーザ登録 → マイページ「API機能（アプリケーションID発行）」で appId を取り、\n"
                    "  `export %s=（appId）` を実行してから再実行する。確認だけなら --dry-run。" % (ENV_NAME, ENV_NAME), 2)
    return app_id


# ───────── list / meta ─────────

def cmd_list(args):
    params = [("appId", "{APP_ID}"), ("lang", "J"), ("limit", str(args.limit))]
    for flag, key in (("search_word", "searchWord"), ("survey_years", "surveyYears"), ("stats_code", "statsCode"),
                      ("stats_field", "statsField"), ("collect_area", "collectArea"), ("open_years", "openYears")):
        v = getattr(args, flag)
        if v:
            params.append((key, v))
    params += parse_extra(args.param)
    return run_simple(args, "getStatsList", params, "GET_STATS_LIST")


def cmd_meta(args):
    params = [("appId", "{APP_ID}"), ("lang", "J"), ("statsDataId", args.stats_data_id), ("explanationGetFlg", "N")]
    return run_simple(args, "getMetaInfo", params, "GET_META_INFO")


def run_simple(args, func, params, root_key):
    app_id = get_app_id(required=not args.dry_run)
    shown = [(k, "***" if k == "appId" else v) for k, v in params]
    if args.dry_run:
        print("[dry-run] GET " + build_url(args.base_url, func, shown).replace("appId=%2A%2A%2A", "appId=***"))
        print("[dry-run] appId は環境変数 %s から読む（%s）" % (ENV_NAME, "設定済み" if app_id else "未設定"))
        return 0
    real = [(k, app_id if k == "appId" else v) for k, v in params]
    doc = http_get_json(build_url(args.base_url, func, real), app_id)
    status, body = check_status(doc, app_id)
    if status == 1:
        err("該当データはありませんでした（STATUS 1）。検索語・調査年・statsCode を変えて再実行する。")
        return 4
    if func == "getStatsList":
        inf = body.get("DATALIST_INF", {})
        rng = inf.get("RESULT_INF", {})
        print("# 該当 %s 件中 %s〜%s 件目。続きは --param startPosition=%s" % (
            inf.get("NUMBER", "?"), rng.get("FROM_NUMBER", "?"), rng.get("TO_NUMBER", "?"), rng.get("NEXT_KEY", "（なし）")))
        print("statsDataId\t政府統計名\t表題\t調査年月\t更新日")
        for t in aslist(inf.get("TABLE_INF")):
            print("\t".join([str(t.get("@id", "")), text_of(t.get("STAT_NAME")), text_of(t.get("TITLE")).replace("\t", " "),
                            text_of(t.get("SURVEY_DATE")), text_of(t.get("UPDATED_DATE"))]))
    else:
        inf = body.get("METADATA_INF", {})
        tinf = inf.get("TABLE_INF", {})
        print("# 統計表 %s: %s" % (tinf.get("@id", args.stats_data_id), text_of(tinf.get("TITLE"))))
        names, labels, _ = class_map(inf.get("CLASS_INF"))
        for dim in dim_order(names):
            print("\n[%s] %s（%d 件）" % (dim, labels.get(dim, ""), len(names[dim])))
            for i, (code, name) in enumerate(names[dim].items()):
                if i >= args.max_rows:
                    print("  …（残り %d 件。--max-rows で増やす）" % (len(names[dim]) - i))
                    break
                print("  %s\t%s" % (code, name))
    return 0


# ───────── data ─────────

def cmd_data(args):
    if args.limit < 1 or args.limit > MAX_LIMIT:
        raise Fatal("--limit は 1〜%d の範囲で指定する（1 回の取得は最大 10 万件）" % MAX_LIMIT, 2)
    filters = common_filters(args)
    app_id = get_app_id(required=not args.dry_run)

    def params_for(start, first):
        p = [("appId", app_id or "{APP_ID}"), ("lang", "J"), ("statsDataId", args.stats_data_id)] + filters
        p += [("startPosition", str(start)), ("limit", str(args.limit)),
              ("metaGetFlg", "Y" if first else "N"), ("cntGetFlg", "N"),
              ("annotationGetFlg", "Y"), ("replaceSpChar", "0")]  # 記号をそのまま受け取る
        return p

    if args.dry_run:
        p = [(k, "***" if k == "appId" else v) for k, v in params_for(1, True)]
        print("[dry-run] GET " + build_url(args.base_url, "getStatsData", p).replace("appId=%2A%2A%2A", "appId=***"))
        print("[dry-run] 続きは応答の NEXT_KEY を startPosition に入れて繰り返す（最大 %d ページ、間隔 %.1f 秒）" % (args.max_pages, args.sleep))
        print("[dry-run] 出力先: %s（既存ならページ取得が全部成功した後で置き換える）" % args.out)
        print("[dry-run] appId は環境変数 %s から読む（%s）" % (ENV_NAME, "設定済み" if app_id else "未設定"))
        return 0

    rows, notes, annots = [], {}, {}
    names, labels, units = {}, {}, {}
    start, page, total = 1, 0, None
    while True:
        page += 1
        if page > args.max_pages:
            raise Fatal("--max-pages(%d) に達したので止めた。取得途中のため CSV は書いていない。"
                        "次の手: cd* で絞り込むか、--max-pages を増やす。" % args.max_pages, 1)
        doc = http_get_json(build_url(args.base_url, "getStatsData", params_for(start, page == 1)), app_id)
        status, body = check_status(doc, app_id)
        if status == 1:
            err("該当データはありませんでした（STATUS 1）。cdArea・cdTime などの絞り込みコードを meta で確かめて直す。")
            return 4
        sd = body.get("STATISTICAL_DATA", {})
        inf = sd.get("RESULT_INF", {})
        if total is None:
            total = inf.get("TOTAL_NUMBER")
        if page == 1:
            names, labels, units = class_map(sd.get("CLASS_INF"))
        di = sd.get("DATA_INF") or {}
        for n in aslist(di.get("NOTE")):
            notes[n.get("@char", "")] = text_of(n)
        for a in aslist(di.get("ANNOTATION")):
            annots[a.get("@annotation", "")] = text_of(a)
        rows.extend(aslist(di.get("VALUE")))
        nxt = inf.get("NEXT_KEY")
        err("ページ %d: %s〜%s 件目 / 全 %s 件" % (page, inf.get("FROM_NUMBER", "?"), inf.get("TO_NUMBER", "?"), total))
        if nxt in (None, ""):
            break
        try:
            nxt = int(nxt)
        except ValueError:
            raise Fatal("NEXT_KEY が数値でない: %r" % (nxt,), 1)
        if nxt <= start:
            raise Fatal("NEXT_KEY(%d) が進んでいない（startPosition=%d）。無限ループを避けて止めた。" % (nxt, start), 1)
        start = nxt
        time.sleep(args.sleep)  # 短時間の大量アクセスは規約で禁止

    if total is not None and str(total).isdigit() and int(total) != len(rows):
        err("警告: TOTAL_NUMBER=%s だが取得できたのは %d 行。" % (total, len(rows)))
    write_csv(args, rows, names, notes, annots, units)
    sym = sum(1 for r in rows if not NUMERIC.match(text_of(r).strip()))
    err("書き出し完了: %s（%d 行、うち数値でない値 %d 行）" % (args.out, len(rows), sym))
    err("次元: " + " / ".join("%s=%s" % (d, labels.get(d, "")) for d in dim_order(names)))
    err("出典の書き方は references/terms-and-credit.md。加工したなら『加工して作成』を併記する。")
    return 0


def write_csv(args, rows, names, notes, annots, units):
    keys = set()
    for r in rows:
        keys.update(k[1:] for k in r if k.startswith("@"))
    dims = dim_order(keys | set(names))
    header = []
    for d in dims:
        header += [d + "_code", d + "_name"]
    header += ["unit", "value", "value_num", "symbol", "symbol_note", "annotation_code", "annotation_text"]
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".estat_", suffix=".csv", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding=args.encoding, newline="") as f:
            w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            w.writerow(header)
            for r in rows:
                raw = text_of(r)
                num, sym = classify(raw)
                line = []
                for d in dims:
                    code = r.get("@" + d, "")
                    line += [code, names.get(d, {}).get(code, "")]
                unit = r.get("@unit") or next((units[(d, r.get("@" + d))] for d in dims if (d, r.get("@" + d)) in units), "")
                note = ""
                if sym:
                    note = notes.get(sym, "（この表の NOTE に説明なし。統計表の注記を確かめる）" if sym != "(空)" else "値が空")
                ac = r.get("@annotation", "")
                line += [unit, raw, num, sym, note, ac, annots.get(ac, "") if ac else ""]
                w.writerow(line)
        os.replace(tmp, args.out)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ───────── main ─────────

def build_parser():
    p = argparse.ArgumentParser(
        description="e-Stat API 3.0 で統計表の検索(list)・メタ情報(meta)・統計データ(data)を取得する。appId は環境変数 %s。" % ENV_NAME,
        epilog="終了コード: 0 正常 / 1 API・HTTP エラー / 2 引数・環境 / 3 通信不可 / 4 該当なし。例は SKILL.md を参照。")
    sub = p.add_subparsers(dest="cmd")

    def common(sp):
        sp.add_argument("--base-url", default=DEFAULT_BASE, help="既定 %s（テスト用に差し替え可）" % DEFAULT_BASE)
        sp.add_argument("--dry-run", action="store_true", help="通信せず、組み立てた URL（appId は伏せる）を出す")
        sp.add_argument("--param", action="append", metavar="KEY=VALUE", help="追加パラメータ（例 lvArea=2, cdCat02=001）。繰り返し可")

    sl = sub.add_parser("list", help="統計表を検索して statsDataId を調べる（getStatsList）")
    common(sl)
    sl.add_argument("--search-word", help="キーワード（AND/OR/NOT 可）")
    sl.add_argument("--survey-years", help="調査年 yyyy / yyyymm / yyyymm-yyyymm")
    sl.add_argument("--open-years", help="公開年")
    sl.add_argument("--stats-code", help="政府統計コード（5 桁=府省、8 桁=統計）。国勢調査は 00200521")
    sl.add_argument("--stats-field", help="統計分野（2 桁 / 4 桁）")
    sl.add_argument("--collect-area", choices=["1", "2", "3"], help="1 全国 / 2 都道府県 / 3 市区町村")
    sl.add_argument("--limit", type=int, default=20, help="表示する表の数（既定 20）")
    sl.set_defaults(func=cmd_list)

    sm = sub.add_parser("meta", help="統計表の次元（表章・分類・地域・時間）とコードを見る（getMetaInfo）")
    common(sm)
    sm.add_argument("--stats-data-id", required=True)
    sm.add_argument("--max-rows", type=int, default=50, help="次元ごとの表示件数（既定 50）")
    sm.set_defaults(func=cmd_meta)

    sd = sub.add_parser("data", help="統計データを全ページ取得して CSV に書く（getStatsData）")
    common(sd)
    sd.add_argument("--stats-data-id", required=True)
    sd.add_argument("--cd-tab", help="表章項目コード（カンマ区切り、100 個まで）")
    sd.add_argument("--cd-cat01", help="分類事項 01 のコード")
    sd.add_argument("--cd-area", help="地域コード（例 13000 は東京都）")
    sd.add_argument("--cd-time", help="時間軸コード（例 2020000000）")
    sd.add_argument("--limit", type=int, default=MAX_LIMIT, help="1 ページの件数（既定・上限 100000）")
    sd.add_argument("--max-pages", type=int, default=1000, help="安全弁のページ数上限（既定 1000）")
    sd.add_argument("--sleep", type=float, default=1.0, help="ページ間の待ち秒（既定 1.0。規約で短時間の大量アクセスは禁止）")
    sd.add_argument("--out", default="estat_data.csv", help="出力 CSV（既定 estat_data.csv）。同名は成功時に置き換える")
    sd.add_argument("--encoding", default="utf-8-sig", help="文字コード（既定 utf-8-sig=Excel 向け BOM つき。cp932 / utf-8 も可）")
    sd.set_defaults(func=cmd_data)
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except Fatal as e:
        err("エラー: " + e.msg)
        return e.code
    except LookupError as e:
        err("エラー: 文字コードが不正: %s" % e)
        return 2
    except OSError as e:
        err("エラー: ファイルを書けない（%s）。次の手: --out の場所と権限を確かめる。" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
