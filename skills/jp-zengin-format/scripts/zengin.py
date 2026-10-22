#!/usr/bin/env python3
"""全銀フォーマット（全銀協規定形式・120バイト固定長）の生成と検証。

Python 3.9 の標準ライブラリだけで動く。銀行へは何も送らない（通信しない）。

サブコマンド:
  kana      文字列を全銀の名義向け（半角カナ・英大文字・数字・一部の記号）に変換して表示
  generate  CSV から 120 バイト固定長ファイルを作る（総合振込 21 / 給与振込 11 / 賞与振込 12）
  validate  既存ファイルの桁・文字・レコード順・トレーラの合計件数と合計金額を検証する

文字コードは Shift_JIS 系（cp932。半角カナ 1 バイト）だけ。EBCDIC は対象外。
仕様の根拠は references/zengin-spec.md（全銀協の公開資料）。銀行ごとの差は取引銀行の仕様書で確認すること。

終了コード: 0 正常 / 1 データに問題あり（検証エラー・変換できない文字など） / 2 引数・ファイルの誤り
"""
import argparse
import csv
import json
import os
import sys
import unicodedata
from datetime import date

RECORD_LEN = 120
TYPES = {"21": "総合振込", "11": "給与振込", "12": "賞与振込"}

# ───────── 文字集合（references/zengin-spec.md §4。全銀協 付録1 の JIS 表と注1〜注3） ─────────

KANA_BASE = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ"  # 小文字・ヲを除く
KANA_SMALL = "ｧｨｩｪｫｬｭｮｯ"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DIGITS = "0123456789"
NAME_CHARS = set(KANA_BASE + UPPER + DIGITS + " ()-.")  # 注1: 口座名・振込依頼人名・受取人名など
NAME_CHARS_WO = NAME_CHARS | {"ｦ"}  # 総合振込の名義ではヲを使える
BRANCH_CHARS = set(KANA_BASE + UPPER + DIGITS + "-")  # 注1: 店舗名（記号はハイフンのみ）
SALARY_OTHER_CHARS = set(KANA_BASE + DIGITS + " ")  # 注2（名義・店舗名以外の項目）
EDI_CHARS = set(KANA_BASE + "ｦ" + UPPER + DIGITS + " \\｢｣()-/.")  # 注3: EDI 情報（カンマは使わない）
CODE_CHARS = set(UPPER + DIGITS + " ")  # 顧客コードなど。仕様に明記なし → 英数字とスペースだけを許す
JIS_SYMBOLS_NOT_FOR_NAMES = ",+'?:/\\￥"  # JIS 表にはあるが名義では使えない（ヒント表示用）

# ───────── レコード定義（名前, 桁数, N 数字 / C 文字, 文字集合） ─────────

def _spec(*rows):
    return list(rows)


HEADER = _spec(
    ("data_kbn", 1, "N", None), ("type", 2, "N", None), ("code_kbn", 1, "N", None),
    ("client_code", 10, "N", None), ("client_name", 40, "C", "name"), ("date", 4, "N", None),
    ("bank_no", 4, "N", None), ("bank_name", 15, "C", "bank"), ("branch_no", 3, "N", None),
    ("branch_name", 15, "C", "branch"), ("acct_type", 1, "N", None), ("acct_no", 7, "N", None),
    ("dummy", 17, "C", "space"),
)
DATA_21 = _spec(
    ("data_kbn", 1, "N", None), ("bank_no", 4, "N", None), ("bank_name", 15, "C", "bank"),
    ("branch_no", 3, "N", None), ("branch_name", 15, "C", "branch"), ("clearing_no", 4, "N", None),
    ("acct_type", 1, "N", None), ("acct_no", 7, "N", None), ("name", 30, "C", "name"),
    ("amount", 10, "N", None), ("new_code", 1, "N", None), ("cust_or_edi", 20, "C", "custedi"),
    ("transfer_kbn", 1, "N", None), ("edi_flag", 1, "C", "flag"), ("dummy", 7, "C", "space"),
)
DATA_SAL = _spec(
    ("data_kbn", 1, "N", None), ("bank_no", 4, "N", None), ("bank_name", 15, "C", "bank"),
    ("branch_no", 3, "N", None), ("branch_name", 15, "C", "branch"), ("clearing_no", 4, "N", None),
    ("acct_type", 1, "N", None), ("acct_no", 7, "N", None), ("name", 30, "C", "name"),
    ("amount", 10, "N", None), ("new_code", 1, "N", None), ("emp_no", 10, "N", None),
    ("dept_code", 10, "N", None), ("dummy", 9, "C", "space"),
)
TRAILER = _spec(
    ("data_kbn", 1, "N", None), ("count", 6, "N", None), ("total", 12, "N", None),
    ("dummy", 101, "C", "space"),
)
END = _spec(("data_kbn", 1, "N", None), ("dummy", 119, "C", "space"))

for _s in (HEADER, DATA_21, DATA_SAL, TRAILER, END):
    assert sum(r[1] for r in _s) == RECORD_LEN


def split_fields(text, spec):
    """120 文字の文字列をフィールドに分ける。{name: (開始位置1始まり, 値)}"""
    out, pos = {}, 0
    for name, width, _k, _c in spec:
        out[name] = (pos + 1, text[pos:pos + width])
        pos += width
    return out


# ───────── かな変換 ─────────

_HALF = {}
for _cp in range(0xFF66, 0xFF9E):  # ｦ..ﾝ
    _h = chr(_cp)
    _HALF[unicodedata.normalize("NFKC", _h)] = _h
_SMALL_TO_LARGE = {"ァ": "ア", "ィ": "イ", "ゥ": "ウ", "ェ": "エ", "ォ": "オ", "ャ": "ヤ", "ュ": "ユ",
                   "ョ": "ヨ", "ッ": "ツ", "ヮ": "ワ", "ヵ": "カ", "ヶ": "ケ"}
_DASHES = set("ー－‐‑‒–—―−ｰ-")
_MIDDOT = set("・･·")

ABBREV = [  # 法人略語（全銀協 付録2 のうち主な 6 種）。長い表記を先に
    ("株式会社", "ｶ"), ("カブシキガイシャ", "ｶ"), ("有限会社", "ﾕ"), ("ユウゲンガイシャ", "ﾕ"),
    ("合同会社", "ﾄﾞ"), ("ゴウドウガイシャ", "ﾄﾞ"), ("合名会社", "ﾒ"), ("ゴウメイガイシャ", "ﾒ"),
    ("合資会社", "ｼ"), ("ゴウシガイシャ", "ｼ"), ("相互会社", "ｿ"), ("ソウゴガイシャ", "ｿ"),
]


def apply_abbrev(s):
    """法人格を略語にする（先頭: ｶ)名前 / 末尾: 名前(ｶ / 中間: 前(ｶ)後）。1 法人名につき 1 個だけ"""
    for long_name, short in ABBREV:
        idx = s.find(long_name)
        if idx < 0:
            continue
        before, after = s[:idx].strip(" 　"), s[idx + len(long_name):].strip(" 　")
        if not before and not after:
            return s
        if not before:
            return short + ")" + after
        if not after:
            return before + "(" + short
        return before + "(" + short + ")" + after
    return s


def to_zengin(text, middot="error", abbrev=False):
    """名義などを全銀向けに変換する。戻り値 (変換後, 注意の一覧, 変換できない文字の一覧)"""
    notes, bad = [], []
    if abbrev:
        text = apply_abbrev(text)
    s = unicodedata.normalize("NFKC", text.replace("\u309b", "\u3099").replace("\u309c", "\u309a"))
    out = []
    for i, ch in enumerate(s):
        if ch in _MIDDOT:
            if middot == "space":
                out.append(" ")
                notes.append("中黒をスペースにした")
            elif middot == "period":
                out.append(".")
                notes.append("中黒をピリオドにした")
            elif middot == "drop":
                notes.append("中黒を削除した")
            else:
                bad.append((i, ch, "中黒は銀行・届出名義で扱いが違うため自動変換しない（--middot space|period|drop で指定）"))
            continue
        if ch in _DASHES:
            out.append("-")
            if ch != "-":
                notes.append("長音・ダッシュ「%s」をハイフンにした（長音は全銀の文字表にない。届出名義で確認）" % ch)
            continue
        if "ぁ" <= ch <= "ゖ":
            ch = chr(ord(ch) + 0x60)
        if ch in "゛゜":  # 単独の濁点・半濁点（NFKC 後は U+3099/309A に化けないよう直接扱う）
            out.append("ﾞ" if ch == "゛" else "ﾟ")
            continue
        if "ァ" <= ch <= "ヶ" or ch == "ヮ":
            base = unicodedata.normalize("NFD", ch)
            mark = ""
            if len(base) == 2 and base[1] in "\u3099\u309a":
                mark = "ﾞ" if base[1] == "\u3099" else "ﾟ"
                base = base[0]
            else:
                base = ch
            if base in _SMALL_TO_LARGE:
                notes.append("小文字「%s」を大文字にした（全銀では小文字不可。例: ｷﾔﾂｼﾕ）" % base)
                base = _SMALL_TO_LARGE[base]
            half = _HALF.get(base)
            if half is None:
                bad.append((i, ch, "対応する半角カナがない"))
                continue
            out.append(half + mark)
            continue
        if "a" <= ch <= "z":
            out.append(ch.upper())
            notes.append("英小文字を大文字にした")
            continue
        if ch in UPPER or ch in DIGITS or ch in " ()-.":
            out.append(ch)
            continue
        if ch in "｡｢｣､" or ch in "ﾞﾟ" or "ｦ" <= ch <= "ﾝ":  # すでに半角カナ（NFKC で全角になるので通常は来ない）
            out.append(ch)
            continue
        if ch in JIS_SYMBOLS_NOT_FOR_NAMES:
            bad.append((i, ch, "名義に使えない記号（使える記号は ( ) - . とスペースだけ）"))
        elif unicodedata.category(ch).startswith("Lo"):
            bad.append((i, ch, "漢字などは自動変換できない（読みを使い手が決めてカナで渡す）"))
        else:
            bad.append((i, ch, "全銀の文字表にない文字"))
    result = "".join(out)
    return result, sorted(set(notes)), bad


def pad_c(value, width):
    return value.ljust(width)


def pad_n(value, width):
    return str(value).rjust(width, "0")


# ───────── 検証 ─────────

class Report:
    def __init__(self, max_errors=50):
        self.errors, self.warnings, self.max_errors = [], [], max_errors

    def err(self, rec, col, field, msg):
        self.errors.append({"record": rec, "column": col, "field": field, "message": msg})

    def warn(self, rec, col, field, msg):
        self.warnings.append({"record": rec, "column": col, "field": field, "message": msg})


def valid_mmdd(s):
    if len(s) != 4 or not s.isdigit():
        return False
    m, d = int(s[:2]), int(s[2:])
    try:
        date(2024, m, d)  # 2024 は閏年。2/29 は年によって不可なので警告側で扱う
    except ValueError:
        return False
    return True


def check_chars(rep, rec, col, field, value, allowed, label):
    for off, ch in enumerate(value):
        if ch not in allowed:
            hint = ""
            if ch in KANA_SMALL:
                hint = "（小文字カナは不可。大文字に直す: ｯ→ﾂ ｬ→ﾔ など）"
            elif ch == "ｦ":
                hint = "（ヲはこの業務の名義では使えない）"
            elif ch in "abcdefghijklmnopqrstuvwxyz":
                hint = "（英小文字は不可。大文字に直す）"
            elif ch == "ｰ":
                hint = "（長音は文字表にない。ハイフン - にするかは銀行・届出名義で確認）"
            elif ch in JIS_SYMBOLS_NOT_FOR_NAMES:
                hint = "（この項目で使える記号は %s）" % label
            rep.err(rec, col + off, field, "使えない文字 %r (U+%04X)%s" % (ch, ord(ch), hint))
            return


def validate_bytes(data, rec_type=None, max_errors=50):
    """バイト列を検証する。戻り値 (Report, 集計 dict)"""
    rep = Report(max_errors)
    stats = {"groups": 0, "data_records": 0, "records": 0, "total_amount": 0, "types": []}
    if not data:
        rep.err(0, 0, "file", "ファイルが空です")
        return rep, stats
    if data[:1] == b"\xf1" or data[:3] == b"\xef\xbb\xbf":
        rep.err(1, 1, "file", "EBCDIC または UTF-8(BOM) のようです。このスキルは Shift_JIS 系（cp932）の 120 バイト固定長だけを扱います")
        return rep, stats

    # レコードに分ける
    records = []
    if b"\n" in data:
        lines = data.split(b"\n")
        if lines and lines[-1] in (b"", b"\x1a"):
            lines = lines[:-1]
        for ln in lines:
            if ln.endswith(b"\r"):
                ln = ln[:-1]
            if ln.endswith(b"\x1a"):
                ln = ln[:-1]
            records.append(ln)
        if b"\r\n" not in data:
            rep.warn(0, 0, "file", "改行が LF のみです。CRLF を求める銀行が多いので仕様書で確認してください")
    else:
        body = data[:-1] if data.endswith(b"\x1a") else data
        if len(body) % RECORD_LEN:
            rep.err(0, 0, "file", "改行なしのファイルですが全体のバイト数 %d が 120 の倍数ではありません（余り %d）。"
                    "途中のレコードの桁がずれているか、改行コードが欠けています" % (len(body), len(body) % RECORD_LEN))
        records = [body[i:i + RECORD_LEN] for i in range(0, len(body) - len(body) % RECORD_LEN, RECORD_LEN)]
        if len(body) % RECORD_LEN:
            tail = body[len(body) - len(body) % RECORD_LEN:]
            records.append(tail)

    stats["records"] = len(records)
    texts = []
    for n, raw in enumerate(records, 1):
        if len(raw) != RECORD_LEN:
            extra = ""
            try:
                t = raw.decode("cp932")
                wide = [c for c in t if ord(c) > 0xFF and not (0xFF61 <= ord(c) <= 0xFF9F)]
                if wide:
                    extra = "。全角文字 %r が含まれています（全角は 2 バイトになり桁がずれます）" % wide[0]
            except UnicodeDecodeError:
                extra = "。Shift_JIS として読めないバイトがあります"
            rep.err(n, 0, "record", "レコード長が %d バイトです（120 バイトであること）%s" % (len(raw), extra))
            texts.append(None)
            continue
        try:
            t = raw.decode("cp932")
        except UnicodeDecodeError:
            rep.err(n, 0, "record", "Shift_JIS として読めないバイトがあります（EBCDIC・UTF-8 の疑い）")
            texts.append(None)
            continue
        if len(t) != RECORD_LEN:
            rep.err(n, 0, "record", "2 バイト文字（全角）が含まれ、桁がずれています")
            texts.append(None)
            continue
        texts.append(t)

    # レコードの順序と中身
    state = "need_header"  # need_header / in_group / after_trailer / done
    group_type, group_count, group_sum, last_n = None, 0, 0, 0
    first_type = None
    for n, t in enumerate(texts, 1):
        last_n = n
        if t is None:
            continue
        kbn = t[0]
        if state == "done":
            rep.err(n, 1, "data_kbn", "エンド・レコードの後ろにレコードがあります")
            continue
        if kbn == "1":
            if state == "in_group":
                rep.err(n, 1, "data_kbn", "トレーラ・レコード(8) が無いまま次のヘッダー(1) が来ました")
            f = split_fields(t, HEADER)
            group_type = f["type"][1]
            stats["groups"] += 1
            stats["types"].append(group_type)
            group_count, group_sum = 0, 0
            if group_type not in TYPES:
                rep.err(n, 2, "type", "種別コード %r は未対応です（対応: 21 総合振込 / 11 給与振込 / 12 賞与振込）" % group_type)
            elif rec_type and group_type != rec_type:
                rep.err(n, 2, "type", "種別コード %s ですが --type %s が指定されています" % (group_type, rec_type))
            if first_type and group_type != first_type:
                rep.err(n, 2, "type", "1 ファイル内の複数ヘッダーは同じ種別コードに限られます（先頭は %s）" % first_type)
            first_type = first_type or group_type
            _check_record(rep, n, t, HEADER, group_type)
            state = "in_group"
        elif kbn == "2":
            if state != "in_group":
                rep.err(n, 1, "data_kbn", "ヘッダー・レコード(1) の前（またはトレーラの後）にデータ・レコード(2) があります")
            spec = DATA_21 if group_type == "21" else DATA_SAL
            _check_record(rep, n, t, spec, group_type)
            f = split_fields(t, spec)
            group_count += 1
            stats["data_records"] += 1
            if f["amount"][1].isdigit():
                group_sum += int(f["amount"][1])
                stats["total_amount"] += int(f["amount"][1])
        elif kbn == "8":
            if state != "in_group":
                rep.err(n, 1, "data_kbn", "ヘッダー・レコード(1) が無いのにトレーラ・レコード(8) があります")
            f = split_fields(t, TRAILER)
            _check_record(rep, n, t, TRAILER, group_type)
            c, s = f["count"][1], f["total"][1]
            if c.isdigit() and int(c) != group_count:
                rep.err(n, f["count"][0], "count", "合計件数が合いません: トレーラ %d 件 / データ・レコード実数 %d 件" % (int(c), group_count))
            if s.isdigit() and int(s) != group_sum:
                rep.err(n, f["total"][0], "total", "合計金額が合いません: トレーラ %d 円 / データ・レコードの振込金額の合計 %d 円（差 %d 円）"
                        % (int(s), group_sum, int(s) - group_sum))
            state = "after_trailer"
        elif kbn == "9":
            if state == "in_group":
                rep.err(n, 1, "data_kbn", "トレーラ・レコード(8) が無いままエンド・レコード(9) が来ました")
            elif state == "need_header":
                rep.err(n, 1, "data_kbn", "ヘッダーが無いファイルです")
            _check_record(rep, n, t, END, group_type)
            state = "done"
        else:
            rep.err(n, 1, "data_kbn", "データ区分 %r は 1/2/8/9 のどれでもありません" % kbn)
    if state != "done" and last_n:
        rep.err(last_n, 0, "file", "エンド・レコード(9) で終わっていません（ファイルが途中で切れている可能性）")
    return rep, stats


def _check_record(rep, n, t, spec, rtype):
    f = split_fields(t, spec)
    kbn_expected = {id(HEADER): "1", id(DATA_21): "2", id(DATA_SAL): "2", id(TRAILER): "8", id(END): "9"}[id(spec)]
    is_header = spec is HEADER
    for name, width, kind, cset in spec:
        col, val = f[name]
        if kind == "N":
            if is_header and name in ("acct_type", "acct_no") and val.strip(" ") == "":
                rep.warn(n, col, name, "依頼人の預金種目・口座番号が空です（全銀協の仕様では任意。銀行によっては必須）")
            elif not val.isdigit() or not val.isascii():
                rep.err(n, col, name, "数字項目（%d 桁）に数字以外があります: %r（数字は右詰め・左をゼロ埋め）" % (width, val))
        if cset == "space" and val.strip(" "):
            rep.err(n, col, name, "ダミー（予備）領域はスペースのみです: %r" % val[:20])
        elif cset in ("name", "bank", "branch", "flag", "custedi") and kind == "C":
            if cset == "name":
                allowed = NAME_CHARS_WO if rtype == "21" else NAME_CHARS
                label = "( ) - . とスペース"
                check_chars(rep, n, col, name, val, allowed, label)
                if val.strip(" ") == "" and name in ("name", "client_name"):
                    rep.err(n, col, name, "名義が空です")
                elif val.startswith(" "):
                    rep.warn(n, col, name, "文字項目は左詰めです（先頭がスペース）")
            elif cset == "bank":
                if val.strip(" "):
                    check_chars(rep, n, col, name, val, NAME_CHARS_WO, "( ) - . とスペース")
            elif cset == "branch":
                if val.strip(" "):
                    bad = [c for c in val.strip(" ") if c not in BRANCH_CHARS]
                    if bad:
                        rep.warn(n, col, name, "店舗名で使える文字はカナ・英大文字・数字・ハイフンだけです（%r）。任意項目なので銀行が見ない場合もあります" % bad[0])
            elif cset == "flag":
                if val not in ("Y", " "):
                    rep.err(n, col, name, "識別表示は Y またはスペースです: %r" % val)
            elif cset == "custedi":
                flag = f["edi_flag"][1] if "edi_flag" in f else " "
                allowed = EDI_CHARS if flag == "Y" else CODE_CHARS
                if flag == "Y" and "," in val:
                    rep.err(n, col, name, "EDI 情報にカンマは使えません（銀行システムの区切り文字と衝突）")
                else:
                    check_chars(rep, n, col, name, val, allowed, "EDI 情報の記号")
    if f["data_kbn"][1] != kbn_expected:
        rep.err(n, 1, "data_kbn", "データ区分が %r（期待 %s）" % (f["data_kbn"][1], kbn_expected))
    if is_header:
        if f["code_kbn"][1] != "0":
            rep.err(n, f["code_kbn"][0], "code_kbn", "コード区分 %r: 0（JIS）のみ対応。1（EBCDIC）は対象外" % f["code_kbn"][1])
        if f["date"][1].isdigit() and not valid_mmdd(f["date"][1]):
            rep.err(n, f["date"][0], "date", "振込指定日 %s は MMDD の月日として不正です" % f["date"][1])
        elif f["date"][1] == "0229":
            rep.warn(n, f["date"][0], "date", "2/29 は閏年のみ有効です。営業日かどうかは検証できません")
        if f["acct_type"][1] not in ("1", "2", "9", " ") and f["acct_type"][1].isdigit():
            rep.err(n, f["acct_type"][0], "acct_type", "依頼人の預金種目は 1/2/9（給与・賞与は 1/2）")
        if f["client_code"][1].isdigit() and int(f["client_code"][1]) == 0:
            rep.warn(n, f["client_code"][0], "client_code", "依頼人（委託者・会社）コードが全部ゼロです。銀行が採番したコードを入れます")
    elif spec in (DATA_21, DATA_SAL):
        allowed_acct = ("1", "2", "4", "9") if rtype == "21" else ("1", "2")
        if f["acct_type"][1].isdigit() and f["acct_type"][1] not in allowed_acct:
            rep.err(n, f["acct_type"][0], "acct_type", "預金種目 %s は使えません（%s）" % (f["acct_type"][1], "/".join(allowed_acct)))
        if f["new_code"][1].isdigit() and f["new_code"][1] not in ("0", "1", "2"):
            rep.err(n, f["new_code"][0], "new_code", "新規コードは 0/1/2 です: %s" % f["new_code"][1])
        if f["amount"][1].isdigit() and int(f["amount"][1]) == 0:
            rep.warn(n, f["amount"][0], "amount", "振込金額が 0 円です")
        if rtype == "21" and f["transfer_kbn"][1].isdigit() and f["transfer_kbn"][1] not in ("7", "8"):
            rep.err(n, f["transfer_kbn"][0], "transfer_kbn", "振込指定区分は 7（テレ振込）または 8（文書振込）。銀行の仕様書では 7 のみのことが多い")
        if f["clearing_no"][1].isdigit() and int(f["clearing_no"][1]) != 0:
            rep.warn(n, f["clearing_no"][0], "clearing_no", "手形交換所番号は 0000 とする銀行が多いです")


# ───────── generate ─────────

def read_csv(path, enc):
    try:
        with open(path, newline="", encoding=enc) as fh:
            return list(csv.DictReader(fh))
    except UnicodeDecodeError:
        die("CSV を %s として読めません。Excel の CSV なら --input-encoding cp932 を付けてください" % enc)
    except OSError as e:
        die("CSV を開けません: %s" % e)


def die(msg, code=2):
    print("エラー: " + msg, file=sys.stderr)
    sys.exit(code)


def num_field(value, width, label, problems, row, pad_note=None):
    v = (value or "").strip()
    if not v.isdigit() or not v.isascii():
        problems.append("行%d: %s は数字だけで指定してください（ハイフン・スペース・全角は不可）: %r" % (row, label, value))
        return "0" * width
    if len(v) > width:
        problems.append("行%d: %s が %d 桁を超えています: %s" % (row, label, width, v))
        return v[:width]
    if len(v) < width and pad_note is not None:
        pad_note.add("%s を左ゼロ埋めした（Excel で先頭の 0 が落ちた可能性。元の桁を確認）" % label)
    return v.rjust(width, "0")


def convert_name(value, width, label, row, args, problems, notes, rtype):
    conv, nts, bad = to_zengin((value or "").strip(), args.middot, args.abbrev) if not args.no_convert else ((value or "").strip(), [], [])
    for b in bad:
        problems.append("行%d: %s の %d 文字目 %r: %s" % (row, label, b[0] + 1, b[1], b[2]))
    for nt in nts:
        notes.add("%s: %s" % (label, nt))
    if len(conv) > width:
        problems.append("行%d: %s が %d 文字を超えています（変換後 %d 文字: %s）。法人略語（--abbrev）や短縮を検討" % (row, label, width, len(conv), conv))
        conv = conv[:width]
    return conv.ljust(width)


def build_records(args, rows):
    rtype = args.type
    problems, notes = [], set()
    if not rows:
        die("CSV にデータ行がありません")
    first = rows[0].keys()
    need = ["bank_no", "branch_no", "account_type", "account_no", "name", "amount"]
    missing = [c for c in need if c not in first]
    if missing:
        die("CSV に必須の列がありません: %s（1 行目は列名。references/zengin-spec.md §6 参照）" % ", ".join(missing))

    # ヘッダー
    h = []
    cc = num_field(args.client_code, 10, "--client-code", problems, 0)
    if not valid_mmdd(args.date or ""):
        problems.append("--date は MMDD の月日で指定してください: %r" % args.date)
    acct_type = (args.acct_type or "").strip()
    if acct_type and acct_type not in ("1", "2", "9"):
        problems.append("--acct-type は 1(普通) 2(当座) 9(その他) のどれか")
    cname = convert_name(args.client_name, 40, "--client-name", 0, args, problems, notes, rtype)
    hdr = ("1" + rtype + "0" + cc + cname + (args.date or "0000") +
           num_field(args.bank_no, 4, "--bank-no", problems, 0) +
           convert_name(args.bank_name or "", 15, "--bank-name", 0, args, problems, notes, rtype) +
           num_field(args.branch_no, 3, "--branch-no", problems, 0) +
           convert_name(args.branch_name or "", 15, "--branch-name", 0, args, problems, notes, rtype) +
           (acct_type or " ") + (num_field(args.acct_no, 7, "--acct-no", problems, 0) if args.acct_no else " " * 7) +
           " " * 17)
    h.append(hdr)

    body, total = [], 0
    for i, r in enumerate(rows, 2):  # CSV の行番号（1 行目は列名）
        g = lambda k: (r.get(k) or "").strip()
        bank_no = num_field(g("bank_no"), 4, "bank_no", problems, i, notes)
        branch_no = num_field(g("branch_no"), 3, "branch_no", problems, i, notes)
        acct_type_r = g("account_type")
        allowed = ("1", "2", "4", "9") if rtype == "21" else ("1", "2")
        if acct_type_r not in allowed:
            problems.append("行%d: account_type %r は使えません（%s）" % (i, acct_type_r, "/".join(allowed)))
        acct_no = num_field(g("account_no"), 7, "account_no", problems, i, notes)
        name = convert_name(g("name"), 30, "name", i, args, problems, notes, rtype)
        if not name.strip():
            problems.append("行%d: name が空です" % i)
        amt = g("amount").replace(",", "")
        if not amt.isdigit() or not amt.isascii() or int(amt) < 1:
            problems.append("行%d: amount は 1 以上の整数（円）です: %r" % (i, g("amount")))
            amt_i = 0
        else:
            amt_i = int(amt)
            if amt_i > 9999999999:
                problems.append("行%d: amount が 10 桁(9,999,999,999 円)を超えています" % i)
        total += amt_i
        new_code = g("new_code") or "0"
        if new_code not in ("0", "1", "2"):
            problems.append("行%d: new_code は 0/1/2 です: %r" % (i, new_code))
        bank_name = convert_name(g("bank_name"), 15, "bank_name", i, args, problems, notes, rtype)
        branch_name = convert_name(g("branch_name"), 15, "branch_name", i, args, problems, notes, rtype)
        common = "2" + bank_no + bank_name + branch_no + branch_name + "0000" + acct_type_r[:1].ljust(1) + acct_no + name + \
            str(amt_i).rjust(10, "0") + new_code
        if rtype == "21":
            edi = g("edi")
            if edi:
                ediv = edi.upper()
                bad = [c for c in ediv if c not in EDI_CHARS]
                if bad:
                    problems.append("行%d: edi に使えない文字 %r" % (i, bad[0]))
                if len(ediv) > 20:
                    problems.append("行%d: edi は 20 文字までです" % i)
                mid, flag = ediv[:20].ljust(20), "Y"
            else:
                mid = g("customer1").ljust(10)[:10] + g("customer2").ljust(10)[:10]
                flag = " "
                if len(g("customer1")) > 10 or len(g("customer2")) > 10:
                    problems.append("行%d: customer1/customer2 は 10 文字までです" % i)
            tk = g("transfer_kbn") or "7"
            if tk not in ("7", "8"):
                problems.append("行%d: transfer_kbn は 7 または 8 です: %r" % (i, tk))
            rec = common + mid + tk + flag + " " * 7
        else:
            rec = common + num_field(g("employee_no") or "0", 10, "employee_no", problems, i) + \
                num_field(g("dept_code") or "0", 10, "dept_code", problems, i) + " " * 9
        body.append(rec)

    if total > 999999999999:
        problems.append("合計金額が 12 桁を超えます")
    if len(body) > 999999:
        problems.append("件数が 6 桁を超えます")
    trailer = "8" + str(len(body)).rjust(6, "0") + str(total).rjust(12, "0") + " " * 101
    end = "9" + " " * 119
    return h + body + [trailer, end], problems, sorted(notes), total


def cmd_generate(args):
    if args.type not in TYPES:
        die("--type は 21（総合振込）/ 11（給与振込）/ 12（賞与振込）")
    rows = read_csv(args.input, args.input_encoding)
    recs, problems, notes, total = build_records(args, rows)
    for nt in notes:
        print("注意: " + nt, file=sys.stderr)
    if problems:
        print("作成を中止しました。次の %d 件を直してやり直してください（ファイルは作っていません）:" % len(problems), file=sys.stderr)
        for p in problems[:args.max_errors]:
            print("  - " + p, file=sys.stderr)
        return 1
    eol = "\r\n" if args.crlf else ""
    data = "".join(r + eol for r in recs).encode("cp932")
    rep, stats = validate_bytes(data, args.type)
    if rep.errors:  # 作ったものが自分の検証に通らないのは不具合。書き出さない
        print("内部検証に失敗したため書き出しません:", file=sys.stderr)
        for e in rep.errors[:10]:
            print("  - レコード%d 桁%d %s: %s" % (e["record"], e["column"], e["field"], e["message"]), file=sys.stderr)
        return 1
    summary = "%s(%s) データ%d件 合計%s円 → %d バイト/%d レコード%s" % (
        TYPES[args.type], args.type, len(rows), format(total, ","), len(data), len(recs), "（CRLF 付き）" if args.crlf else "（改行なし）")
    if args.dry_run:
        print("[dry-run] " + summary + "。ファイルは作っていません")
        for r in recs[:min(len(recs), 4)]:
            print("  " + r.replace(" ", "_"))
        return 0
    if os.path.exists(args.output) and not args.force:
        die("出力先が既にあります: %s（上書きするなら --force）" % args.output)
    with open(args.output, "wb") as fh:
        fh.write(data)
    print(summary + " → " + args.output)
    print("取引銀行の仕様書（改行・振込指定区分・新規コード・営業日）に合うか確認してから、銀行のサービスで取り込んでください。")
    return 0


# ───────── validate / kana ─────────

def cmd_validate(args):
    try:
        with open(args.file, "rb") as fh:
            data = fh.read()
    except OSError as e:
        die("ファイルを開けません: %s" % e)
    rep, stats = validate_bytes(data, args.type, args.max_errors)
    if args.json:
        print(json.dumps({"ok": not rep.errors, "stats": stats, "errors": rep.errors, "warnings": rep.warnings}, ensure_ascii=False, indent=1))
        return 1 if rep.errors else 0
    print("レコード %d 件 / ヘッダー群 %d / データ・レコード %d 件 / 振込金額の合計 %s 円 / 種別 %s" % (
        stats["records"], stats["groups"], stats["data_records"], format(stats["total_amount"], ","), ",".join(stats["types"]) or "-"))
    for e in rep.errors[:args.max_errors]:
        print("ERROR レコード%d 桁%d [%s] %s" % (e["record"], e["column"], e["field"], e["message"]))
    if len(rep.errors) > args.max_errors:
        print("... ほか %d 件のエラー" % (len(rep.errors) - args.max_errors))
    for w in rep.warnings[:args.max_errors]:
        print("WARN  レコード%d 桁%d [%s] %s" % (w["record"], w["column"], w["field"], w["message"]))
    print("結果: エラー %d 件 / 警告 %d 件" % (len(rep.errors), len(rep.warnings)))
    if not rep.errors:
        print("形式は仕様どおりです。ただし銀行ごとの差・口座の実在・営業日は検証していません。")
    return 1 if rep.errors else 0


def cmd_kana(args):
    code = 0
    for t in args.text:
        conv, notes, bad = to_zengin(t, args.middot, args.abbrev)
        print(conv if not bad else "%s\t# 変換できない文字あり" % conv)
        for n in notes:
            print("  注意: " + n, file=sys.stderr)
        for pos, ch, why in bad:
            print("  エラー: %d 文字目 %r: %s" % (pos + 1, ch, why), file=sys.stderr)
            code = 1
    return code


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0] + "（詳細は references/zengin-spec.md）", formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd")
    k = sub.add_parser("kana", help="名義を全銀向けに変換する")
    k.add_argument("text", nargs="+")
    k.add_argument("--middot", choices=["error", "space", "period", "drop"], default="error", help="中黒の扱い（既定 error）")
    k.add_argument("--abbrev", action="store_true", help="株式会社などを法人略語にする")
    g = sub.add_parser("generate", help="CSV から 120 バイト固定長ファイルを作る")
    g.add_argument("--input", required=True, help="データ CSV（1 行目は列名。assets/sample_transfers.csv 参照）")
    g.add_argument("--output", help="出力ファイル（--dry-run なら不要）")
    g.add_argument("--type", default="21", help="21 総合振込 / 11 給与振込 / 12 賞与振込（既定 21）")
    g.add_argument("--client-code", required=True, help="依頼人（委託者・会社）コード 10 桁。銀行が採番")
    g.add_argument("--client-name", required=True, help="依頼人名（全角でもよい。全銀向けに変換する）")
    g.add_argument("--date", required=True, help="振込指定日 MMDD（金融機関の営業日）")
    g.add_argument("--bank-no", required=True, help="仕向銀行番号 4 桁")
    g.add_argument("--bank-name", default="")
    g.add_argument("--branch-no", required=True, help="仕向支店番号 3 桁")
    g.add_argument("--branch-name", default="")
    g.add_argument("--acct-type", default="", help="依頼人の預金種目 1/2/9（任意）")
    g.add_argument("--acct-no", default="", help="依頼人の口座番号 7 桁（任意）")
    g.add_argument("--input-encoding", default="utf-8-sig", help="CSV の文字コード（Excel の CSV は cp932）")
    g.add_argument("--crlf", action="store_true", help="各レコードの後ろに CRLF を付ける（銀行の指定に従う。既定は付けない）")
    g.add_argument("--no-convert", action="store_true", help="名義の自動変換をしない（すでに半角カナの場合）")
    g.add_argument("--middot", choices=["error", "space", "period", "drop"], default="error")
    g.add_argument("--abbrev", action="store_true", help="株式会社などを法人略語にする")
    g.add_argument("--dry-run", action="store_true", help="作らずに内容と合計だけ表示")
    g.add_argument("--force", action="store_true", help="出力先があっても上書き")
    g.add_argument("--max-errors", type=int, default=50)
    v = sub.add_parser("validate", help="既存ファイルを検証する")
    v.add_argument("file")
    v.add_argument("--type", choices=sorted(TYPES), help="期待する種別コード（任意）")
    v.add_argument("--json", action="store_true")
    v.add_argument("--max-errors", type=int, default=50)
    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        return 2
    if args.cmd == "generate" and not args.dry_run and not args.output:
        die("--output を指定してください（確認だけなら --dry-run）")
    return {"kana": cmd_kana, "generate": cmd_generate, "validate": cmd_validate}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
