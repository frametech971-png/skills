#!/usr/bin/env python3
"""zengin.py の自己検証。実際に生成・検証を走らせる（モックなし。銀行には接続しない）。

使い方: python3 scripts/selftest_zengin.py   （全部合格なら終了コード 0）
テストデータは架空の値だけ（銀行番号 9999・口座 0000001 など。実在の口座は使わない）。
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ZG = os.path.join(HERE, "zengin.py")
ASSETS = os.path.join(HERE, "..", "assets")
fails, total = [], 0


def run(*args):
    r = subprocess.run([sys.executable, ZG] + list(args), capture_output=True, timeout=60)
    return r.returncode, r.stdout.decode("utf-8"), r.stderr.decode("utf-8")


def check(name, cond, detail=""):
    global total
    total += 1
    if not cond:
        fails.append(name)
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else "  " + str(detail)[:300]))


def gen(tmp, out, csv_path, typ="21", extra=()):
    return run("generate", "--input", csv_path, "--output", out, "--type", typ, "--client-code", "1234",
               "--client-name", "テストショウジ株式会社", "--abbrev", "--date", "1125", "--bank-no", "9999",
               "--branch-no", "1", *extra)


def val(path, *extra):
    return run("validate", path, *extra)


def tamper(src, dst, fn):
    data = open(src, "rb").read()
    open(dst, "wb").write(fn(data))


def main():
    sample = os.path.join(ASSETS, "sample_transfers.csv")
    sal = os.path.join(ASSETS, "sample_salary.csv")
    with tempfile.TemporaryDirectory() as tmp:
        P = lambda n: os.path.join(tmp, n)

        # 1. 総合振込 CRLF あり
        rc, out, err = gen(tmp, P("a.txt"), sample, extra=["--crlf"])
        check("generate 21 --crlf が成功", rc == 0, err)
        raw = open(P("a.txt"), "rb").read()
        lines = raw.split(b"\r\n")[:-1]
        check("7 レコード・各 120 バイト", len(lines) == 7 and all(len(l) == 120 for l in lines), [len(l) for l in lines])
        exp_total = 150000 + 32000 + 1000 + 500
        tr = lines[5].decode("cp932")
        check("トレーラ: 8 + 件数000004 + 合計(別計算) 183500", tr[:19] == "8" + "000004" + str(exp_total).rjust(12, "0"), tr[:19])
        check("エンド: 9 + スペース", lines[6].decode("cp932") == "9" + " " * 119)
        h = lines[0].decode("cp932")
        check("ヘッダー: 種別21・JIS(0)・依頼人コード・名義の法人略語・日付", h[:14] == "12100000001234" and h[14:54].rstrip() == "ﾃｽﾄｼﾖｳｼﾞ(ｶ" and h[54:58] == "1125", h[:60])
        d1 = lines[3].decode("cp932")
        check("データ(小文字・長音・EDI): 名義 ｱｲｳ ｷﾔﾂｼﾕ(ｶ / EDI=INV-0001 / 区分7 / 識別Y",
              d1[0] == "2" and d1[50:80].rstrip() == "ｱｲｳ ｷﾔﾂｼﾕ(ｶ" and d1[91:111].rstrip() == "INV-0001" and d1[111] == "7" and d1[112] == "Y", (d1[50:80], d1[91:113]))
        d2 = lines[4].decode("cp932")
        check("ヴァイオリン ワークス → ｳﾞｱｲｵﾘﾝ ﾜ-ｸｽ", d2[50:80].rstrip() == "ｳﾞｱｲｵﾘﾝ ﾜ-ｸｽ", d2[50:80])
        rc, out, err = val(P("a.txt"))
        check("validate が合格(終了コード0)", rc == 0 and "エラー 0 件" in out, out)
        check("validate の集計が別計算と一致(4件・183,500円)", "データ・レコード 4 件" in out and "183,500" in out, out)

        # 2. 改行なし
        rc, _, err = gen(tmp, P("b.txt"), sample)
        check("generate 改行なしが成功", rc == 0, err)
        check("改行なしは 7*120=840 バイト", os.path.getsize(P("b.txt")) == 840)
        rc, out, _ = val(P("b.txt"))
        check("改行なしも validate 合格", rc == 0, out)

        # 3. 給与振込
        rc, _, err = gen(tmp, P("s.txt"), sal, typ="11", extra=["--crlf"])
        check("generate 11(給与) 成功", rc == 0, err)
        sl = open(P("s.txt"), "rb").read().split(b"\r\n")[:-1]
        check("給与: 種別11・5 レコード・社員番号/所属コード位置", len(sl) == 5 and sl[0][1:3] == b"11" and sl[1][91:101] == b"0000000001" and sl[1][101:111] == b"0000000010", sl[1][85:115])
        rc, out, _ = val(P("s.txt"), "--type", "11")
        check("給与 validate 合格", rc == 0, out)
        rc, out, _ = val(P("s.txt"), "--type", "21")
        check("--type 不一致を検出", rc == 1 and "--type" in out, out)

        # 4. 改ざん
        base = P("a.txt")
        def fix_total(d):
            return d.replace(b"000004000000183500", b"000004000000183000", 1)
        tamper(base, P("t1.txt"), fix_total)
        rc, out, _ = val(P("t1.txt"))
        check("トレーラ合計金額の不一致を検出（差も出す）", rc == 1 and "合計金額が合いません" in out and "183500" not in out.split("差")[0] or ("183,500" in out), out)
        check("差額 -500 円 を表示", "差 -500 円" in out, out)
        tamper(base, P("t2.txt"), lambda d: d.replace(b"000004000000183500", b"000005000000183500", 1))
        rc, out, _ = val(P("t2.txt"))
        check("合計件数の不一致を検出", rc == 1 and "合計件数が合いません: トレーラ 5 件 / データ・レコード実数 4 件" in out, out)

        def drop_line(d):
            ls = d.split(b"\r\n")
            del ls[2]
            return b"\r\n".join(ls)
        tamper(base, P("t3.txt"), drop_line)
        rc, out, _ = val(P("t3.txt"))
        check("データ行が欠けると件数・金額の両方を検出", rc == 1 and "合計件数が合いません" in out and "合計金額が合いません" in out, out)

        def short(d):
            ls = d.split(b"\r\n")
            ls[1] = ls[1][:-1]
            return b"\r\n".join(ls)
        tamper(base, P("t4.txt"), short)
        rc, out, _ = val(P("t4.txt"))
        check("119 バイトのレコードを検出", rc == 1 and "レコード長が 119 バイト" in out, out)

        def zen(d):
            ls = d.split(b"\r\n")
            ls[1] = ls[1].replace("ﾃｽﾄ".encode("cp932"), "テスト".encode("cp932"), 1)
            return b"\r\n".join(ls)
        tamper(base, P("t5.txt"), zen)
        rc, out, _ = val(P("t5.txt"))
        check("全角文字による桁ずれを検出", rc == 1 and "全角文字" in out, out)

        def small(d):
            ls = d.split(b"\r\n")
            ls[2] = ls[2].replace("ﾔﾏﾀﾞ".encode("cp932"), "ﾔﾏﾀﾞ".encode("cp932"), 1).replace("ﾊﾅｺ".encode("cp932"), "ｯﾅｺ".encode("cp932"), 1)
            return b"\r\n".join(ls)
        tamper(base, P("t6.txt"), small)
        rc, out, _ = val(P("t6.txt"))
        check("小文字カナを検出（直し方つき）", rc == 1 and "使えない文字 'ｯ'" in out and "大文字" in out, out)

        tamper(base, P("t7.txt"), lambda d: d.replace(b"11259999", b"13329999", 1))
        rc, out, _ = val(P("t7.txt"))
        check("振込指定日 1332 を検出", rc == 1 and "MMDD" in out, out)

        tamper(base, P("t8.txt"), lambda d: d.replace(b"\r\n9" + b" " * 119 + b"\r\n", b"\r\n"))
        rc, out, _ = val(P("t8.txt"))
        check("エンド・レコード欠落を検出", rc == 1 and "エンド" in out, out)

        tamper(base, P("t9.txt"), lambda d: bytes([0xF1]) + d[1:])
        rc, out, _ = val(P("t9.txt"))
        check("EBCDIC らしいファイルは対象外と案内", rc == 1 and "EBCDIC" in out, out)

        tamper(base, P("t10.txt"), lambda d: d.replace(b"0000001", b"000-001", 1))
        rc, out, _ = val(P("t10.txt"))
        check("口座番号のハイフンを検出", rc == 1 and "acct_no" in out, out)

        tamper(base, P("t11.txt"), lambda d: d.replace(b"12100000001234", b"12100000001234", 1).replace(b"\r\n2", b"\r\n3", 1))
        rc, out, _ = val(P("t11.txt"))
        check("データ区分の誤りを検出", rc == 1 and "データ区分" in out, out)

        tamper(base, P("t12.txt"), lambda d: d.replace(b"\r\n", b"")[:-30])
        rc, out, _ = val(P("t12.txt"))
        check("改行なし・途中で切れたファイルを検出", rc == 1 and "120 の倍数" in out, out)

        rc, out, _ = val(P("t12.txt"), "--json")
        check("--json が出力できる", '"ok": false' in out)

        # 5. generate の失敗系
        bad = P("bad.csv")
        open(bad, "w", encoding="utf-8").write("bank_no,branch_no,account_type,account_no,name,amount\n9999,001,1,0000001,山田花子,1000\n9999,001,1,00-1,ヤマダ,0\n")
        rc, out, err = gen(tmp, P("c.txt"), bad)
        check("漢字・不正な口座・0円は作成中止(終了1)でファイルを作らない", rc == 1 and not os.path.exists(P("c.txt")) and "漢字" in err and "account_no" in err and "amount" in err, err)
        rc, out, err = gen(tmp, P("a.txt"), sample)
        check("既存の出力先は --force なしで上書きしない(終了2)", rc == 2 and "--force" in err, err)
        rc, out, err = gen(tmp, P("a.txt"), sample, extra=["--force", "--dry-run"])
        check("--dry-run は書かない", rc == 0 and "dry-run" in out)

        # Excel(cp932)・先頭ゼロ落ち・カンマ区切り金額
        xl = P("xl.csv")
        with open(xl, "w", encoding="cp932", newline="") as fh:
            fh.write("bank_no,branch_no,account_type,account_no,name,amount\r\n999,1,1,123,ヤマダ　タロウ,\"1,250\"\r\n")
        rc, out, err = gen(tmp, P("x.txt"), xl, extra=["--input-encoding", "cp932"])
        check("cp932 CSV・先頭ゼロ落ち・カンマ金額を処理", rc == 0 and "左ゼロ埋め" in err, err)
        xr = open(P("x.txt"), "rb").read()
        check("0999/001/0000123/1250 に補正", xr[121:125] == b"0999" and xr[163:170] == b"0000123" and b"0000001250" in xr, xr[120:240])
        rc, out, err = gen(tmp, P("y.txt"), xl)
        check("文字コード違いは原因と次の手を出す(終了2)", rc == 2 and "cp932" in err, err)

        # kana 変換
        rc, out, _ = run("kana", "キャッシュ", "ガ゛ギ", "ﾊﾟﾋﾟﾌﾟ", "ａｂｃ１２３", "ｰ")
        lines2 = out.splitlines()
        check("kana: キャッシュ→ｷﾔﾂｼﾕ", lines2[0] == "ｷﾔﾂｼﾕ", lines2)
        check("kana: 半角のパ行はそのまま", lines2[2] == "ﾊﾟﾋﾟﾌﾟ", lines2)
        check("kana: 全角英数→半角英大文字数字", lines2[3] == "ABC123", lines2)
        rc, out, err = run("kana", "山田")
        check("kana: 漢字は終了コード1", rc == 1)
        rc, out, err = run("kana", "--middot", "space", "ﾔﾏﾀﾞ・ﾀﾛｳ")
        check("kana: 中黒→スペース指定", out.strip() == "ﾔﾏﾀﾞ ﾀﾛｳ", out)
        rc, out, _ = run("kana", "--abbrev", "株式会社ヤマモト", "ヤマモト株式会社", "ヤマモト株式会社トウキョウ")
        check("kana: 法人略語 先頭/末尾/中間", out.splitlines() == ["ｶ)ﾔﾏﾓﾄ", "ﾔﾏﾓﾄ(ｶ", "ﾔﾏﾓﾄ(ｶ)ﾄｳｷﾖｳ"], out)
        rc, out, err = run()
        check("引数なしは使い方を出して終了2", rc == 2)

    print("\n%d/%d 合格" % (total - len(fails), total))
    if fails:
        print("不合格: " + ", ".join(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
