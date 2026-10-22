#!/usr/bin/env python3
"""インボイス制度の計算と形式確認（登録番号の形式・検査桁／税率ごとの消費税額）。

Python 3.9 の標準ライブラリだけ。通信もファイル書き込みもしない。

使い方:
  python3 scripts/invoice.py regno T7000012050002
  python3 scripts/invoice.py tax --basis excl --round floor 8:13861 8:13199 10:4389 10:23769 --stated 8=2164 --stated 10=2815

終了コード: 0 問題なし / 1 指摘あり（検査桁の不一致・形式の不備・記載税額の不一致）/ 2 引数エラー
実行できない環境では、references/calculation.md の式を手で計算し、「概算」と明記する。
"""
import argparse
import sys
import unicodedata

# 検査用数字の式（国税庁・法人番号公表サイト「チェックデジットの計算」）:
#   基礎番号12桁を最下位から数え、奇数桁の和 + 偶数桁の和 x 2 を 9 で割った余りを r として、検査用数字 = 9 - r
# 出典: https://www.houjin-bangou.nta.go.jp/documents/checkdigit.pdf


def corporate_check_digit(base12):
    """12桁の基礎番号から検査用数字(0-9)を返す。"""
    digits = [int(c) for c in reversed(base12)]  # digits[0] が最下位(1桁目)
    odd = sum(digits[0::2])    # 最下位から奇数桁
    even = sum(digits[1::2])   # 最下位から偶数桁
    return 9 - ((odd + even * 2) % 9)


def normalize_regno(raw):
    """全角・ハイフン・空白を取り除いた文字列と、見つけた表記ゆれの一覧を返す。"""
    notes = []
    s = raw.strip()
    n = unicodedata.normalize("NFKC", s)
    if n != s:
        notes.append("全角文字が含まれる（半角にそろえて判定した）")
    for ch in ("-", "ー", "−", " ", "　"):
        if ch in n:
            notes.append("ハイフン・空白が含まれる（取り除いて判定した）")
            break
    n = n.replace("-", "").replace("ー", "").replace("−", "").replace(" ", "").replace("　", "")
    if n[:1] == "t":
        notes.append("先頭の T が小文字（大文字 T に直して判定した）")
        n = "T" + n[1:]
    return n, notes


def cmd_regno(args):
    findings = []
    for raw in args.numbers:
        n, notes = normalize_regno(raw)
        print("入力: %s" % raw)
        for t in notes:
            print("  注意: %s" % t)
        ok = True
        if not n.startswith("T"):
            print("  不備: 先頭が T ではない。登録番号は T + 13桁の数字")
            ok = False
        body = n[1:] if n.startswith("T") else n
        if not body.isdigit() or not body.isascii():
            print("  不備: T の後ろが数字だけではない")
            ok = False
        elif len(body) != 13:
            print("  不備: T の後ろが %d 桁（13桁である必要がある）" % len(body))
            ok = False
        if ok:
            expect = corporate_check_digit(body[1:])
            if int(body[0]) == expect:
                print("  形式: OK（T + 13桁）。法人番号として検査桁も一致（検査用数字 %d）" % expect)
                print("  ※ 個人事業者の登録番号は法人番号ではなく、検査桁の公開仕様は確認できていない。")
                print("    検査桁が合っていても登録されている証明にはならない。公表サイトで照会すること。")
            else:
                print("  形式: OK（T + 13桁）。ただし法人番号の検査桁は不一致（先頭の数字 %s、計算値 %d）" % (body[0], expect))
                print("    法人なら入力ミスの可能性が高い。個人事業者の番号なら検査桁は判定できない（形式のみ確認）。")
                findings.append(raw)
        else:
            findings.append(raw)
        print("  照会: https://www.invoice-kohyo.nta.go.jp/ （登録の有無・登録日・失効は公表サイトで確認）")
    return 1 if findings else 0


def parse_line(tok):
    try:
        rate_s, amt_s = tok.split(":", 1)
        rate = int(unicodedata.normalize("NFKC", rate_s).replace("%", ""))
        amt = int(unicodedata.normalize("NFKC", amt_s).replace(",", ""))
    except ValueError:
        raise SystemExit_("明細の形式が違う: %r（税率:金額 の形。例 10:12345）" % tok)
    if rate <= 0 or rate > 100:
        raise SystemExit_("税率が範囲外: %r" % tok)
    return rate, amt


class SystemExit_(Exception):
    pass


def tax_of(amount, rate, basis, mode):
    """1円未満を mode(floor/ceil/round)で処理した消費税額。整数だけで計算する。"""
    if basis == "excl":
        num, den = amount * rate, 100
    else:
        num, den = amount * rate, 100 + rate
    if num < 0:
        sign, num = -1, -num
    else:
        sign = 1
    q, r = divmod(num, den)
    if mode == "floor":
        v = q
    elif mode == "ceil":
        v = q + (1 if r else 0)
    else:  # 四捨五入（半分は切り上げ）
        v = q + (1 if r * 2 >= den else 0)
    return sign * v


MODE_JA = {"floor": "切捨て", "ceil": "切上げ", "round": "四捨五入"}


def cmd_tax(args):
    lines = [parse_line(t) for t in args.lines]
    stated = {}
    for s in args.stated or []:
        try:
            k, v = s.split("=", 1)
            stated[int(k)] = int(v.replace(",", ""))
        except ValueError:
            raise SystemExit_("--stated の形式が違う: %r（税率=税額。例 8=2164）" % s)
    rates = sorted({r for r, _ in lines})
    basis_ja = "税抜" if args.basis == "excl" else "税込"
    print("基準: 各明細は%s金額。端数処理: %s（税率ごとに合計してから1回）" % (basis_ja, MODE_JA[args.round]))
    findings = 0
    grand_excl = 0
    grand_tax = 0
    for rate in rates:
        amts = [a for r, a in lines if r == rate]
        total = sum(amts)
        tax = tax_of(total, rate, args.basis, args.round)
        per_line = sum(tax_of(a, rate, args.basis, args.round) for a in amts)
        formula = "x %d/100" % rate if args.basis == "excl" else "x %d/%d" % (rate, 100 + rate)
        print("\n[%d%%] 明細 %d 件 / %s合計 %s円" % (rate, len(amts), basis_ja, format(total, ",")))
        print("  消費税額等 = %s %s = %s円（%s）" % (format(total, ","), formula, format(tax, ","), MODE_JA[args.round]))
        if len(amts) > 1 and per_line != tax:
            print("  参考: 明細ごとに端数処理して合計すると %s円。これは請求書の記載税額としては認められない（差 %d円）" % (format(per_line, ","), per_line - tax))
        if args.basis == "excl":
            grand_excl += total
            grand_tax += tax
            print("  税込合計 = %s円" % format(total + tax, ","))
        else:
            grand_excl += total - tax
            grand_tax += tax
            print("  税抜合計 = %s円" % format(total - tax, ","))
        if rate in stated:
            if stated[rate] == tax:
                print("  記載税額 %s円: 一致" % format(stated[rate], ","))
            else:
                findings += 1
                hits = [MODE_JA[m] for m in ("floor", "ceil", "round")
                        if tax_of(total, rate, args.basis, m) == stated[rate]]
                msg = "  記載税額 %s円: 不一致（計算値との差 %d円）" % (format(stated[rate], ","), stated[rate] - tax)
                print(msg)
                if hits:
                    print("    別の端数処理（%s）なら一致。端数処理は事業者の任意なので、方法が違うだけの可能性がある。" % "・".join(hits))
                elif stated[rate] == per_line:
                    print("    明細ごとに端数処理した合計と一致。税率ごとに1回の端数処理になっていない可能性がある。")
                else:
                    print("    どの端数処理でも一致しない。税額か対象額の転記ミスの可能性。")
    for rate in stated:
        if rate not in rates:
            findings += 1
            print("\n[%d%%] 記載税額 %s円があるが、この税率の明細が渡されていない" % (rate, format(stated[rate], ",")))
    print("\n合計: 税抜 %s円 + 消費税額等 %s円 = 税込 %s円" % (format(grand_excl, ","), format(grand_tax, ","), format(grand_excl + grand_tax, ",")))
    return 1 if findings else 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="invoice.py",
        description="インボイス制度の計算と形式確認。登録番号の形式・検査桁と、税率ごとの消費税額（税率ごとに1回の端数処理）。",
        epilog="終了コード: 0 問題なし / 1 指摘あり / 2 引数エラー",
    )
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("regno", help="登録番号（T + 13桁）の形式と、法人番号としての検査桁を確認する")
    r.add_argument("numbers", nargs="+", help="例: T7000012050002")
    t = sub.add_parser("tax", help="税率ごとに合計して消費税額等を1回だけ端数処理する")
    t.add_argument("lines", nargs="+", help="明細。税率:金額 の形（例 10:12345 8:2000）。金額は円の整数")
    t.add_argument("--basis", choices=["excl", "incl"], default="excl", help="明細金額が税抜(excl)か税込(incl)か。既定 excl")
    t.add_argument("--round", choices=["floor", "ceil", "round"], default="floor", help="端数処理: 切捨て/切上げ/四捨五入。既定 floor")
    t.add_argument("--stated", action="append", help="請求書に記載された税額と照合する。税率=税額（例 8=2164）。複数可")
    return p


def main(argv=None):
    p = build_parser()
    args = p.parse_args(argv)
    if not args.cmd:
        p.print_help()
        return 2
    try:
        return cmd_regno(args) if args.cmd == "regno" else cmd_tax(args)
    except SystemExit_ as e:
        sys.stderr.write("エラー: %s\n次の手: --help で使い方を確認し、入力を直して再実行する。\n" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
