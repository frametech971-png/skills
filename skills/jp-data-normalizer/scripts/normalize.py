#!/usr/bin/env python3
"""日本語の業務データ（CSV）の表記ゆれを列ごとに直す。Python 3.9 の標準ライブラリだけで動く。

  python3 scripts/normalize.py 顧客.csv --map "電話=phone,郵便番号=zip,住所=address" --dry-run
  python3 scripts/normalize.py 顧客.csv --map "電話=phone,郵便番号=zip,住所=address,生年月日=date,氏名=name"
  python3 scripts/normalize.py --try date "昭和63年4月1日"
  python3 scripts/normalize.py --try phone "０９０ー１２３４ー５６７８"
  python3 scripts/normalize.py --to-wareki 1989-01-07

- 元のファイルは書き換えない。出力は別ファイル（既定: <元の名前>.normalized.csv）。
- 外部へ通信しない。読むのは入力CSVと references/area-codes.txt だけ。
- 確信が持てない値は直さず（または直して）「要確認」列に理由を書く。
- 終了コード: 0 正常（要確認があっても 0） / 2 引数の誤り / 3 入力を読めない / 4 出力を書けない
"""
import argparse
import codecs
import collections
import csv
import datetime
import io
import os
import re
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
AREA_FILE = os.path.join(HERE, "..", "references", "area-codes.txt")

# ───────── 定数 ─────────

# ハイフン・ダッシュ・長音の類（数字の区切りとして使われるもの）。NFKC は FF0D と FF70 しか寄せない
DASH_CHARS = "‐‑‒–—―−－ーｰ﹣⁃˗─━⁻₋"
DASH_RE = re.compile("[" + DASH_CHARS + "]")
ZERO_WIDTH_RE = re.compile("[\\u200b\\u200c\\u200d\\u2060\\ufeff]")

PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県",
    "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県",
    "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]
DESIGNATED = [
    "札幌市", "仙台市", "さいたま市", "千葉市", "横浜市", "川崎市", "相模原市", "新潟市", "静岡市", "浜松市",
    "名古屋市", "京都市", "大阪市", "堺市", "神戸市", "岡山市", "広島市", "北九州市", "福岡市", "熊本市",
]
TOKYO23 = [
    "千代田区", "中央区", "港区", "新宿区", "文京区", "台東区", "墨田区", "江東区", "品川区", "目黒区", "大田区",
    "世田谷区", "渋谷区", "中野区", "杉並区", "豊島区", "北区", "荒川区", "板橋区", "練馬区", "足立区", "葛飾区", "江戸川区",
]
# 名前の途中に 市区町村郡 の字を含む自治体。頭からこの語に一致したら確実とみなす
KNOWN_MUNI = [
    "武蔵村山市", "東村山市", "東村山郡", "西村山郡", "北村山郡", "町田市", "市川市", "市原市", "四日市市",
    "大町市", "郡山市", "郡上市", "小郡市", "田村市", "大村市", "村山市", "上市町", "市貝町", "余市町", "余市郡", "高市郡",
]
SUFFIX = "市区町村郡"

# 元号: (名前, 略号, 開始日, 終了日またはNone)。出典は references/wareki.md
ERAS = [
    ("明治", "M", datetime.date(1868, 1, 25), datetime.date(1912, 7, 29)),
    ("大正", "T", datetime.date(1912, 7, 30), datetime.date(1926, 12, 24)),
    ("昭和", "S", datetime.date(1926, 12, 25), datetime.date(1989, 1, 7)),
    ("平成", "H", datetime.date(1989, 1, 8), datetime.date(2019, 4, 30)),
    ("令和", "R", datetime.date(2019, 5, 1), None),
]
ERA_BY_NAME = {}
for _e in ERAS:
    ERA_BY_NAME[_e[0]] = _e
    ERA_BY_NAME[_e[1]] = _e

KANJI_DIGITS = {"〇": 0, "零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

TYPE_ALIASES = {
    "text": "text", "テキスト": "text", "文字": "text",
    "name": "name", "氏名": "name", "名前": "name",
    "phone": "phone", "tel": "phone", "電話": "phone", "電話番号": "phone",
    "zip": "zip", "postal": "zip", "郵便番号": "zip", "郵便": "zip",
    "address": "address", "住所": "address",
    "date": "date", "日付": "date",
    "number": "number", "num": "number", "数値": "number", "金額": "number",
}


class Fail(Exception):
    def __init__(self, code, msg):
        Exception.__init__(self, msg)
        self.code = code
        self.msg = msg


# ───────── 共通の文字処理 ─────────

def nfkc(s):
    return unicodedata.normalize("NFKC", s)


def clean_text(s, protect_compat=False):
    """NFKC＋空白の整理。～(FF5E) は ASCII の ~ にせず 〜(301C) に寄せる。"""
    s = s.replace("～", "〜")
    if protect_compat:
        out = []
        buf = []
        for ch in s:
            if "豈" <= ch <= "﫿":
                out.append(nfkc("".join(buf)))
                buf = []
                out.append(ch)
            else:
                buf.append(ch)
        out.append(nfkc("".join(buf)))
        s = "".join(out)
    else:
        s = nfkc(s)
    s = ZERO_WIDTH_RE.sub("", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in s.split("\n")]
    return "\n".join(lines).strip()


def expansion_chars(s):
    """NFKC で複数文字や別の字に展開される合字・丸数字・単位記号を拾う（報告用）。"""
    found = []
    for ch in s:
        if ch.isascii() or "｡" <= ch <= "ﾟ":
            continue
        r = unicodedata.normalize("NFKC", ch)
        cat = unicodedata.category(ch)
        if r != ch and (len(r) > 1 or cat in ("No", "So", "Nl")) and not ("！" <= ch <= "～"):
            found.append((ch, r))
    return found


# ───────── 型ごとの処理。戻り値は (新しい値, 要確認の理由のリスト) ─────────

def conv_text(v, ctx):
    return clean_text(v), []


def conv_name(v, ctx):
    return clean_text(v, protect_compat=True), []


def conv_number(v, ctx):
    s = clean_text(v)
    flags = []
    if re.match(r"^[" + DASH_CHARS + r"]\s*\d", s):
        s = "-" + s[1:].strip()
    t = re.sub(r"[,¥￥円\s]", "", s)
    if t == "":
        return s, flags
    if not re.match(r"^-?\d+(\.\d+)?$", t):
        flags.append("数値として読めない: " + v)
        return s, flags
    return t, flags


# --- 電話番号 ---

_AREA = {"codes": None, "short": None}


def load_area():
    if _AREA["codes"] is not None:
        return _AREA["codes"], _AREA["short"]
    codes = set()
    short = {}
    try:
        with io.open(AREA_FILE, encoding="utf-8") as f:
            section = ""
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("["):
                    section = line
                    continue
                if section == "[codes]":
                    codes.add(line)
                elif section == "[short]":
                    head, _, rest = line.partition(" ")
                    ln, _, p3 = head.partition(":")
                    for tail in rest.split():
                        short[p3 + tail] = int(ln)
    except (IOError, OSError, ValueError):
        codes = set()
        short = {}
    _AREA["codes"] = codes
    _AREA["short"] = short
    return codes, short


def fixed_line(d):
    """0 で始まる10桁。戻り値 (ハイフン付き, 理由)。確定できなければ (None, 理由)。"""
    codes, short = load_area()
    if not codes:
        # 市外局番の一覧が読めないときは 03・06 だけ確実に扱う
        if d[:2] in ("03", "06"):
            return "%s-%s-%s" % (d[:2], d[2:6], d[6:]), None
        return None, "市外局番の一覧（references/area-codes.txt）を読めないため桁を決められない"
    body = d[1:]
    cands = [c for c in codes if body.startswith(c)]
    if not cands:
        return None, "市外局番が総務省の一覧に無い（先頭 %s）" % d[:4]
    p5 = body[:5]
    length = short.get(p5)
    if length is None or length not in [len(c) for c in cands]:
        length = max(len(c) for c in cands)
    area = "0" + body[:length]
    local = body[length:5]
    return "%s-%s-%s" % (area, local, d[6:]), None


def conv_phone(v, ctx):
    flags = []
    s = clean_text(v)
    if s == "":
        return s, flags
    s = re.sub(r"^(?i:tel|fax|phone|電話番号|電話|携帯|直通)\s*[:：]?\s*", "", s)
    plus81 = False
    m = re.match(r"^\+\s*81[\s-]*(.*)$", s)
    if m:
        plus81 = True
        rest = re.sub(r"^\(0\)\s*", "", m.group(1))
        rest = re.sub(r"^0(?=\d)", "", rest)
        s = "0" + rest
    s = DASH_RE.sub("-", s)
    if not re.match(r"^[\d\-\s()]+$", s):
        flags.append("電話番号以外の文字を含む（内線・複数番号・文字列）: " + v)
        return clean_text(v), flags
    d = re.sub(r"\D", "", s)
    if d == "":
        flags.append("数字が無い: " + v)
        return s, flags
    note_zero = False
    if not d.startswith("0"):
        if len(d) in (9, 10):
            d = "0" + d
            note_zero = True
        else:
            flags.append("先頭が0でなく桁数も合わない（%d桁）: %s" % (len(d), v))
            return s, flags
    out = None
    n = len(d)
    if n == 11:
        if d[:4] == "0800":
            out = "%s-%s-%s" % (d[:4], d[4:7], d[7:])
        elif d[:3] in ("050", "060", "070", "080", "090"):
            out = "%s-%s-%s" % (d[:3], d[3:7], d[7:])
        else:
            flags.append("11桁だが種別を判定できない: " + v)
    elif n == 10:
        if d[:4] in ("0120", "0570"):
            out = "%s-%s-%s" % (d[:4], d[4:7], d[7:])
        elif d[:4] in ("0990", "0180", "0170"):
            flags.append("特殊番号（%s）は区切りを決めない: %s" % (d[:4], v))
        elif d[:3] in ("050", "060", "070", "080", "090"):
            flags.append("携帯・IP電話は11桁。10桁しかない（1桁欠けた可能性）: " + v)
        else:
            out, why = fixed_line(d)
            if out is None:
                flags.append(why + ": " + v)
    else:
        flags.append("桁数が合わない（%d桁）: %s" % (n, v))
    if out is None:
        return d if not flags else clean_text(v), flags
    if note_zero:
        flags.append("先頭の0を補った（Excel が消した可能性）: %s -> %s" % (v, out))
    return out, flags


# --- 郵便番号 ---

def conv_zip(v, ctx):
    flags = []
    s = clean_text(v)
    if s == "":
        return s, flags
    s2 = DASH_RE.sub("-", s.replace("〒", "")).strip()
    if not re.match(r"^[\d\-\s]+$", s2):
        flags.append("郵便番号以外の文字を含む: " + v)
        return s, flags
    d = re.sub(r"\D", "", s2)
    if len(d) == 6 and "-" not in s2:
        d = "0" + d
        flags.append("6桁だった。先頭の0を補った（Excel が消した可能性）: " + v)
    if len(d) != 7:
        flags.append("7桁でない（%d桁）。旧5桁か欠けた可能性: %s" % (len(d), v))
        return s2, flags
    if ctx.get("zip_style") == "plain":
        return d, flags
    return d[:3] + "-" + d[3:], flags


# --- 住所 ---

def split_address(a):
    """戻り値 (都道府県, 市区町村, 以降, 理由のリスト)。分けられなければ空文字。"""
    flags = []
    pref = ""
    rest = a
    for p in PREFECTURES:
        if a.startswith(p):
            pref = p
            rest = a[len(p):]
            break
    if not pref:
        flags.append("都道府県が先頭に無い（推測しない）")
    rest = rest.lstrip()
    muni = ""
    # 1 東京23区
    if pref == "東京都":
        for w in sorted(TOKYO23, key=len, reverse=True):
            if rest.startswith(w):
                muni = w
                break
    # 2 政令指定都市＋区
    if not muni:
        for c in DESIGNATED:
            if rest.startswith(c):
                m = re.match(r"^([^\s\d市区町村郡]{1,5}?区)", rest[len(c):])
                if m:
                    muni = c + m.group(1)
                else:
                    muni = c
                    flags.append("政令指定都市の区を読み取れない")
                break
    # 3 名前に 市区町村郡 を含む自治体（既知）
    known = False
    if not muni:
        for k in sorted(KNOWN_MUNI, key=len, reverse=True):
            if rest.startswith(k):
                known = True
                if k.endswith("郡"):
                    m = re.search(r"[町村]", rest[len(k) + 1:])
                    if m:
                        muni = rest[:len(k) + 1 + m.start() + 1]
                    else:
                        flags.append("郡の下の町村を読み取れない")
                        muni = k
                else:
                    muni = k
                break
    # 4 一般: 先頭から最初の 市区町村郡
    if not muni:
        embedded = False
        i = 1
        limit = min(len(rest), 10)
        found = -1
        while i < limit:
            ch = rest[i]
            if ch in SUFFIX:
                nxt = rest[i + 1] if i + 1 < len(rest) else ""
                if nxt and nxt in SUFFIX and ch != "郡":
                    embedded = True
                    i += 1
                    continue
                if ch == "郡" and nxt and nxt in "市":
                    embedded = True
                    i += 1
                    continue
                found = i
                break
            i += 1
        if found < 0:
            flags.append("市区町村を見つけられない")
        else:
            if rest[found] == "郡":
                m = re.search(r"[町村]", rest[found + 1:])
                if m:
                    muni = rest[:found + 1 + m.start() + 1]
                else:
                    muni = rest[:found + 1]
                    flags.append("郡の下の町村を読み取れない")
            else:
                muni = rest[:found + 1]
            if embedded or rest[0] in SUFFIX:
                flags.append("市区町村名に市区町村郡の字を含む。切れ目を目で確かめる: " + muni)
    tail = rest[len(muni):].lstrip() if muni else rest
    if muni and len(muni) > 9:
        flags.append("市区町村が長すぎる。切れ目を目で確かめる: " + muni)
    if muni and tail == "":
        flags.append("市区町村より後ろが無い")
    elif muni and not re.search(r"[0-9]|丁目|番地|番|号", tail):
        flags.append("番地の数字が無い")
    return pref, muni, tail, flags


def conv_address(v, ctx):
    s = clean_text(v)
    # 数字に挟まれたダッシュ・長音は半角ハイフンへ（1ー2ー3 -> 1-2-3）
    s = re.sub(r"(?<=\d)[" + DASH_CHARS + r"](?=\d)", "-", s)
    s = s.replace("\n", " ")
    if s == "":
        return s, [], ("", "", "")
    pref, muni, tail, flags = split_address(s)
    return s, flags, (pref, muni, tail)


# --- 日付・和暦 ---

def kanji_to_int(s):
    """算用数字・漢数字（六十三・二〇二六）を整数に。読めなければ None。"""
    if re.match(r"^[0-9]+$", s):
        return int(s)
    if s and all(ch in KANJI_DIGITS for ch in s):
        return int("".join(str(KANJI_DIGITS[ch]) for ch in s))
    total = 0
    cur = 0
    for ch in s:
        if ch in KANJI_DIGITS:
            cur = KANJI_DIGITS[ch]
        elif ch == "十":
            total += (cur or 1) * 10
            cur = 0
        elif ch == "百":
            total += (cur or 1) * 100
            cur = 0
        else:
            return None
    return total + cur


_NUM = r"(?:[0-9]+|[〇零一二三四五六七八九十百]+)"
ERA_RE = re.compile(
    r"^(明治|大正|昭和|平成|令和|[MTSHRmtshr])\s*(元|" + _NUM + r")\s*(?:年|[./\-])?\s*"
    r"(?:(" + _NUM + r")\s*(?:月|[./\-])?\s*(?:(" + _NUM + r")\s*日?)?)?$"
)
AD_RE = re.compile(r"^(\d{4})\s*(?:年|[./\-])\s*(\d{1,2})\s*(?:月|[./\-])?\s*(?:(\d{1,2})\s*日?)?$")
AD_YEAR_RE = re.compile(r"^(\d{4})\s*年?$")
AD_8_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})$")


def era_year_to_ad(era, n):
    return era[2].year + n - 1


def fmt_date(y, m, d, style):
    if m is None:
        return "%04d" % y if style != "jp" else "%d年" % y
    if d is None:
        if style == "slash":
            return "%04d/%02d" % (y, m)
        if style == "jp":
            return "%d年%d月" % (y, m)
        return "%04d-%02d" % (y, m)
    if style == "slash":
        return "%04d/%02d/%02d" % (y, m, d)
    if style == "jp":
        return "%d年%d月%d日" % (y, m, d)
    return "%04d-%02d-%02d" % (y, m, d)


def parse_date(text):
    """和暦・西暦の文字列を (西暦年, 月, 日, 理由のリスト) にする。読めなければ (None,...,理由)。"""
    s = nfkc(text).strip()
    s = ZERO_WIDTH_RE.sub("", s)
    s = DASH_RE.sub("-", s) if not re.search(r"[年月日]", s) else s
    flags = []
    m = ERA_RE.match(s)
    if m:
        era = ERA_BY_NAME[m.group(1).upper() if m.group(1).isascii() else m.group(1)]
        n = 1 if m.group(2) == "元" else kanji_to_int(m.group(2))
        mo = kanji_to_int(m.group(3)) if m.group(3) else None
        dd = kanji_to_int(m.group(4)) if m.group(4) else None
        if n is None or n < 1:
            return None, None, None, ["元号の年を読めない: " + text]
        y = era_year_to_ad(era, n)
        end_y = era[3].year if era[3] else None
        if y < era[2].year or (end_y is not None and y > end_y):
            return None, None, None, ["%s%s年は存在しない（%s は %d〜%s 年）: %s" % (
                era[0], n, era[0], era[2].year, end_y if end_y else "", text)]
        if mo is not None:
            if not 1 <= mo <= 12:
                return None, None, None, ["月が範囲外: " + text]
            first = datetime.date(y, mo, 1)
            last = (datetime.date(y + (mo == 12), mo % 12 + 1, 1) - datetime.timedelta(days=1))
            if last < era[2] or (era[3] is not None and first > era[3]):
                return None, None, None, ["%s%s年%d月は存在しない（元号の切り替わりの前後）: %s" % (era[0], n, mo, text)]
        if dd is not None:
            try:
                dt = datetime.date(y, mo, dd)
            except ValueError:
                return None, None, None, ["存在しない日付: " + text]
            if dt < era[2] or (era[3] is not None and dt > era[3]):
                return None, None, None, ["%s%s年%d月%d日は存在しない（元号の切り替わりの前後）。西暦 %04d-%02d-%02d は %s: %s" % (
                    era[0], n, mo, dd, y, mo, dd, "、".join(to_wareki(y, mo, dd)), text)]
        if era[0] == "明治" and n <= 5 and mo is not None:
            return None, None, None, ["明治5年12月2日までは旧暦（太陰太陽暦）の日付。月日は西暦に直せない（年だけなら %d 年）: %s" % (y, text)]
        return y, mo, dd, flags
    m = AD_RE.match(s)
    if m:
        y, mo = int(m.group(1)), int(m.group(2))
        dd = int(m.group(3)) if m.group(3) else None
        try:
            datetime.date(y, mo, dd or 1)
        except ValueError:
            return None, None, None, ["存在しない日付: " + text]
        return y, mo, dd, flags
    m = AD_8_RE.match(s)
    if m:
        y, mo, dd = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            datetime.date(y, mo, dd)
        except ValueError:
            return None, None, None, ["存在しない日付: " + text]
        return y, mo, dd, flags
    m = AD_YEAR_RE.match(s)
    if m:
        return int(m.group(1)), None, None, flags
    return None, None, None, ["日付として読めない（時刻つき・2桁の年・Excelのシリアル値などは対象外）: " + text]


def conv_date(v, ctx):
    s = clean_text(v)
    if s == "":
        return s, []
    y, mo, dd, flags = parse_date(s)
    if y is None:
        return s, flags
    return fmt_date(y, mo, dd, ctx.get("date_format", "iso")), flags


def to_wareki(y, mo=None, dd=None):
    """西暦から和暦。年だけで元号の境目にかかる年は両方返す。"""
    res = []
    for name, _, start, end in ERAS:
        if mo is not None and dd is not None:
            dt = datetime.date(y, mo, dd)
            if dt >= start and (end is None or dt <= end):
                n = y - start.year + 1
                res.append("%s%s年%d月%d日" % (name, "元" if n == 1 else n, mo, dd))
        else:
            if y >= start.year and (end is None or y <= end.year):
                n = y - start.year + 1
                res.append("%s%s年" % (name, "元" if n == 1 else n))
    return res


CONVERTERS = {
    "text": conv_text, "name": conv_name, "phone": conv_phone, "zip": conv_zip,
    "date": conv_date, "number": conv_number,
}


# ───────── 入出力 ─────────

def detect_encoding(raw, forced):
    if forced and forced != "auto":
        enc = forced.lower().replace("_", "-")
        if enc in ("shift-jis", "sjis", "shiftjis", "ms932", "windows-31j"):
            enc = "cp932"
        try:
            codecs.lookup(enc)
        except LookupError:
            raise Fail(2, "知らない文字コード: %s（utf-8 / utf-8-sig / cp932 / euc-jp など）" % forced)
        return enc
    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        return "utf-16"
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        raw.decode("cp932")
        return "cp932"
    except UnicodeDecodeError:
        pass
    raise Fail(3, "UTF-8 でも CP932（Shift_JIS）でも読めない。次の手: --encoding euc-jp や --encoding utf-16 を試す。"
                  "それでも読めなければ元のアプリで UTF-8 か CP932 の CSV として保存し直す")


def parse_maps(values):
    maps = []
    for v in values or []:
        for part in re.split(r"[,、]", v):
            part = part.strip()
            if not part:
                continue
            if "=" not in part:
                raise Fail(2, "--map は 列名=型 の形で書く（例: 電話=phone）。受け取った値: %s" % part)
            col, _, typ = part.rpartition("=")
            t = TYPE_ALIASES.get(typ.strip().lower()) or TYPE_ALIASES.get(typ.strip())
            if not t:
                raise Fail(2, "知らない型: %s（%s）" % (typ, " / ".join(sorted(set(TYPE_ALIASES.values())))))
            maps.append((col.strip(), t))
    return maps


def run_one(typ, value, ctx):
    """1つの値を型に従って直す。戻り値 (新しい値, 理由, 住所の分割 or None)。"""
    if typ == "address":
        s, flags, parts = conv_address(value, ctx)
        return s, flags, parts
    new, flags = CONVERTERS[typ](value, ctx)
    return new, flags, None


def process(args):
    ctx = {"zip_style": args.zip_style, "date_format": args.date_format}
    maps = parse_maps(args.map)
    if not maps:
        raise Fail(2, "--map で直す列を1つ以上指定する（例: --map \"電話=phone,住所=address\"）")
    if not os.path.isfile(args.input):
        raise Fail(3, "入力ファイルが見つからない: %s。次の手: パスを確かめる（ls で名前を見る）" % args.input)
    try:
        with open(args.input, "rb") as f:
            raw = f.read()
    except (IOError, OSError) as e:
        raise Fail(3, "入力ファイルを開けない: %s（%s）。次の手: 権限と、他のアプリで開いたままでないかを確かめる" % (args.input, e))
    enc = detect_encoding(raw, args.encoding)
    try:
        text = raw.decode(enc)
    except (UnicodeDecodeError, LookupError) as e:
        raise Fail(3, "%s として読めない（%s）。次の手: --encoding cp932 または utf-8 を指定し直す" % (enc, e))
    delim = {"tab": "\t", "\\t": "\t", "comma": ",", "semicolon": ";"}.get(args.delimiter, args.delimiter)
    if len(delim) != 1:
        raise Fail(2, "--delimiter は1文字（, ; tab）")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delim)
    rows = []
    lines = []
    try:
        for r in reader:
            rows.append(r)
            lines.append(reader.line_num)
    except csv.Error as e:
        raise Fail(3, "CSV として読めない（%s）。次の手: 区切り文字を --delimiter で指定する、または引用符の閉じ忘れを直す" % e)
    if not rows:
        raise Fail(3, "空のファイル: %s" % args.input)
    header = rows[0]
    hnorm = [nfkc(h).strip() for h in header]
    colidx = []
    for col, typ in maps:
        key = nfkc(col).strip()
        if key not in hnorm:
            raise Fail(3, "列が見つからない: %s。次の手: 列名を確かめる。ある列: %s" % (col, " / ".join(header)))
        colidx.append((hnorm.index(key), col, typ))
    # 出力の列を決める（新しい列は末尾に足す。既にあればそれを使う）
    out_header = list(header)

    def ensure(name):
        if name in out_header:
            return out_header.index(name)
        out_header.append(name)
        return len(out_header) - 1

    split_idx = {}
    for i, col, typ in colidx:
        if typ == "address":
            split_idx[i] = (ensure(header[i] + "_都道府県"), ensure(header[i] + "_市区町村"), ensure(header[i] + "_番地以降"))
    flag_idx = ensure("要確認")
    width = len(out_header)

    out_rows = [out_header]
    changed_rows = 0
    flagged_rows = []
    col_changed = collections.Counter()
    col_flagged = collections.Counter()
    samples = []
    expansions = collections.Counter()
    ragged = 0
    for ri, r in enumerate(rows[1:], start=1):
        line = lines[ri]
        if len(r) < len(header):
            ragged += 1
        row = list(r) + [""] * (width - len(r))
        row_flags = []
        row_changed = False
        for i, col, typ in colidx:
            old = row[i] if i < len(r) else ""
            if old == "":
                if typ == "address":
                    for k in split_idx[i]:
                        row[k] = ""
                continue
            for ch, rep in expansion_chars(old):
                expansions[(ch, rep)] += 1
            new, flags, parts = run_one(typ, old, ctx)
            if parts is not None:
                for k, p in zip(split_idx[i], parts):
                    row[k] = p
            if new != old:
                row_changed = True
                col_changed[col] += 1
                if len(samples) < args.show:
                    samples.append((line, col, old, new))
            row[i] = new
            if flags:
                col_flagged[col] += 1
                for fl in flags:
                    row_flags.append("%s: %s" % (col, fl))
        row[flag_idx] = " / ".join(row_flags)
        if row_changed:
            changed_rows += 1
        if row_flags:
            flagged_rows.append((line, row_flags))
        out_rows.append(row)

    # 出力の文字コード
    oe = args.out_encoding
    if oe == "same":
        oe = enc
    if oe == "shift_jis" or oe == "sjis":
        oe = "cp932"
    buf = io.StringIO(newline="")
    w = csv.writer(buf, delimiter=delim, lineterminator="\r\n")
    for r in out_rows:
        w.writerow(r)
    body = buf.getvalue()
    try:
        data = body.encode(oe)
    except UnicodeEncodeError as e:
        bad = body[e.start:e.start + 1]
        raise Fail(4, "出力の文字コード %s で書けない文字がある: %r（U+%04X）。次の手: --out-encoding utf-8-sig で出力する"
                   % (oe, bad, ord(bad) if bad else 0))
    except LookupError:
        raise Fail(2, "知らない出力の文字コード: %s" % args.out_encoding)

    out_path = args.output
    if not out_path:
        stem, ext = os.path.splitext(args.input)
        out_path = stem + ".normalized" + (ext or ".csv")
    if os.path.realpath(out_path) == os.path.realpath(args.input):
        raise Fail(4, "出力先が入力と同じ。元のファイルは上書きしない。次の手: -o で別の名前を指定する")
    if not args.dry_run:
        if os.path.exists(out_path) and not args.force:
            raise Fail(4, "出力先が既にある: %s。次の手: 別の名前を -o で指定する、消してよければ --force を付ける" % out_path)
        try:
            d = os.path.dirname(os.path.abspath(out_path))
            fd, tmp = tempfile.mkstemp(prefix=".normalize-", suffix=".tmp", dir=d)
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp, out_path)
        except (IOError, OSError) as e:
            raise Fail(4, "出力を書けない: %s（%s）。次の手: 書き込める場所を -o で指定する" % (out_path, e))

    # 要約
    total = len(rows) - 1
    p = []
    p.append("入力: %s（文字コード %s / %d 行 / %d 列）" % (args.input, enc, total, len(header)))
    if args.dry_run:
        p.append("出力: 書き込まない（--dry-run）。書くなら %s" % out_path)
    else:
        p.append("出力: %s（文字コード %s）" % (out_path, oe))
    p.append("変更した行: %d / %d 行" % (changed_rows, total))
    for i, col, typ in colidx:
        p.append("  %s [%s]: 変更 %d 件・要確認 %d 件" % (col, typ, col_changed[col], col_flagged[col]))
    p.append("要確認の行: %d" % len(flagged_rows))
    for line, fl in flagged_rows[:args.show]:
        p.append("  行%d: %s" % (line, " / ".join(fl)))
    if len(flagged_rows) > args.show:
        p.append("  …ほか %d 行（--show %d で増やす。出力の「要確認」列に全部ある）" % (len(flagged_rows) - args.show, len(flagged_rows)))
    if samples:
        p.append("変更の例（行: 列 前 -> 後）")
        for line, col, old, new in samples:
            p.append("  行%d: %s %r -> %r" % (line, col, old, new))
    if expansions:
        p.append("NFKC で展開された合字・丸数字・単位記号: " + "、".join("%s→%s %d件" % (a, b, n) for (a, b), n in expansions.most_common(8)))
    if ragged:
        p.append("列数が足りない行が %d 行あった（空欄で補った）" % ragged)
    if enc == "utf-8" and any(ord(c) > 127 for c in body) and oe == "utf-8":
        p.append("注意: BOM なしの UTF-8。Excel で直接開くなら --out-encoding utf-8-sig（BOM つき）か cp932 で出す")
    if enc == "cp932":
        p.append("注意: CP932（Windows の Shift_JIS）として読んだ。CP932 に無い文字（絵文字など）は出力で失敗する")
    print("\n".join(p))
    return 0


def try_one(args):
    typ = TYPE_ALIASES.get(args.try_[0].lower()) or TYPE_ALIASES.get(args.try_[0])
    if not typ:
        raise Fail(2, "知らない型: %s（%s）" % (args.try_[0], " / ".join(sorted(set(TYPE_ALIASES.values())))))
    ctx = {"zip_style": args.zip_style, "date_format": args.date_format}
    new, flags, parts = run_one(typ, args.try_[1], ctx)
    print("入力: %r" % args.try_[1])
    print("結果: %r" % new)
    if parts is not None:
        print("分割: 都道府県=%r 市区町村=%r 以降=%r" % parts)
    print("要確認: " + (" / ".join(flags) if flags else "なし"))
    return 0


def do_wareki(args):
    m = re.match(r"^(\d{4})(?:-(\d{1,2})-(\d{1,2}))?$", args.to_wareki.strip())
    if not m:
        raise Fail(2, "--to-wareki は YYYY または YYYY-MM-DD（例: 1989-01-07）")
    y = int(m.group(1))
    mo = int(m.group(2)) if m.group(2) else None
    dd = int(m.group(3)) if m.group(3) else None
    if mo is not None:
        try:
            datetime.date(y, mo, dd)
        except ValueError:
            raise Fail(2, "存在しない日付: %s" % args.to_wareki)
    old_cal = y <= 1872
    if old_cal and mo is not None:
        print("注意: 1872年（明治5年）までの月日は旧暦（太陰太陽暦）で、西暦の月日とは対応しない。年だけを示す")
        mo = dd = None
    res = to_wareki(y, mo, dd)
    if not res:
        print("元号の範囲外（明治元年=1868 年より前）: %s" % args.to_wareki)
        return 0
    print("、".join(res) + ("（元号の切り替わりの年。年だけでは決まらない。日付まで指定すると1つに絞れる）" if len(res) > 1 else ""))
    return 0


class JpParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("引数の誤り: %s\n次の手: python3 scripts/normalize.py --help\n" % message)
        sys.exit(2)


def build_parser():
    p = JpParser(add_help=False, description="日本語の業務データ（CSV）の表記ゆれを列ごとに直す。元のファイルは書き換えない。")
    p.add_argument("input", nargs="?", help="入力のCSV")
    p.add_argument("-h", "--help", action="help", help="この説明を出す")
    p.add_argument("--map", action="append", metavar="列名=型", help="直す列と型。型: text name phone zip address date number（日本語名も可: 電話 郵便番号 住所 日付 氏名 数値）。カンマ区切りで複数、または繰り返し")
    p.add_argument("-o", "--output", help="出力先（既定: 元の名前.normalized.csv）。入力と同じ場所は不可")
    p.add_argument("--dry-run", action="store_true", help="何も書かず、変更の要約と例だけを出す")
    p.add_argument("--force", action="store_true", help="出力先が既にあっても上書きする（入力は常に上書きしない）")
    p.add_argument("--encoding", default="auto", help="入力の文字コード（既定 auto: BOM→UTF-8→CP932 の順に試す）")
    p.add_argument("--out-encoding", default="same", help="出力の文字コード: same（入力と同じ）/ utf-8 / utf-8-sig（Excel向けBOMつき）/ cp932")
    p.add_argument("--delimiter", default=",", help="区切り文字（既定 ,）。tab も可")
    p.add_argument("--date-format", choices=["iso", "slash", "jp"], default="iso", help="日付の出力: iso=2026-03-01 / slash=2026/03/01 / jp=2026年3月1日")
    p.add_argument("--zip-style", choices=["hyphen", "plain"], default="hyphen", help="郵便番号: hyphen=123-4567 / plain=1234567")
    p.add_argument("--show", type=int, default=10, help="要約に載せる要確認・変更例の行数（既定 10）")
    p.add_argument("--try", dest="try_", nargs=2, metavar=("型", "値"), help="1つの値だけ試す（CSV不要）")
    p.add_argument("--to-wareki", metavar="YYYY[-MM-DD]", help="西暦から和暦を出す（CSV不要）")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.to_wareki:
            return do_wareki(args)
        if args.try_:
            return try_one(args)
        if not args.input:
            raise Fail(2, "入力のCSVを指定する。例: python3 scripts/normalize.py 顧客.csv --map \"電話=phone\" --dry-run")
        return process(args)
    except Fail as e:
        sys.stderr.write("エラー: %s\n" % e.msg)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
