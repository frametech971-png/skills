#!/usr/bin/env python3
"""プライバシーポリシー本文を読み、点検項目のキーワードが有るかを一覧にする（一次スクリーニング）。

使い方:
  python3 scripts/pp_scan.py policy.txt            # 表で出力
  python3 scripts/pp_scan.py policy.txt --json     # JSON で出力
  cat policy.txt | python3 scripts/pp_scan.py -    # 標準入力
  python3 scripts/pp_scan.py policy.txt --strict   # 未検出や未入力が残っていれば終了コード 1

できること: キーワードの有無、未入力の穴埋め記号の取り残し（【要入力】、＜＞、山括弧、○○、XXX）の検出。
できないこと: 記載内容が法に適合しているかの判断。「検出」は言葉があるという意味だけで、
中身が足りているかは人が references/checklist.md で確かめる。外部へ通信せず、ファイルも書かない。

終了コード: 0 正常 / 1 --strict で指摘あり / 2 引数エラー / 3 読み込み失敗
実行できない環境では: references/checklist.md の項目 C01〜C20 を、本文を読みながら手で確かめる。
Python 3.9 の標準ライブラリだけで動く。
"""
import argparse
import json
import re
import sys

# (ID, 項目, 条文, 検出パターン, 該当する場合のみ必要か)
ITEMS = [
    ("C01", "事業者の名称・住所・代表者", "法32条1項1号", [r"(住所|所在地)", r"代表"], False),
    ("C02", "取得する情報の項目・取得方法", "法20条1項・21条", [r"(取得|収集)する(個人)?情報|取得方法|取得する項目|収集方法"], False),
    ("C03", "利用目的", "法17条1項", [r"利用目的|以下の目的|次の目的|目的で(利用|使用)"], False),
    ("C04", "利用目的の変更", "法17条2項・21条3項", [r"利用目的.{0,12}(変更|追加)"], False),
    ("C05", "要配慮個人情報", "法20条2項", [r"要配慮"], True),
    ("C06", "安全管理措置", "法23条・32条1項4号", [r"安全管理"], False),
    ("C07", "委託", "法25条・27条5項1号", [r"委託"], True),
    ("C08", "第三者提供", "法27条", [r"第三者(へ|に)?(の)?提供|第三者提供"], False),
    ("C09", "共同利用", "法27条5項3号", [r"共同(して)?利用"], True),
    ("C10", "外国にある第三者・外国保管", "法28条", [r"外国|海外|国外"], True),
    ("C11", "Cookie・アクセス解析・広告タグ・外部送信", "法31条・電気通信事業法27条の12", [r"Cookie|クッキー|アクセス解析|Google\s*Analytics|広告配信|タグ|外部送信|SDK|ピクセル"], True),
    ("C12", "保有個人データの公表事項（手続）", "法32条1項3号", [r"開示"], False),
    ("C13a", "訂正・利用停止等の請求", "法34条・35条", [r"訂正", r"利用停止|消去"], False),
    ("C13b", "手数料", "法32条1項3号・38条", [r"手数料|無料"], False),
    ("C13c", "本人確認・代理人", "法37条・令12条・13条", [r"本人確認|代理人"], False),
    ("C14", "苦情・問合せ窓口", "法40条・令10条2号", [r"窓口|苦情|お問い?合わせ"], False),
    ("C14b", "認定個人情報保護団体", "令10条3号", [r"認定個人情報保護団体"], True),
    ("C17", "制定日・改定日・改定手続", "法21条3項", [r"制定日|改定日|最終更新|施行日|改訂|改定"], False),
]

# 取り残しの穴埋め記号
LEFTOVERS = [
    (r"【要入力[^】]*】", "【要入力】が残っている"),
    (r"【要確認[^】]*】", "【要確認】が残っている"),
    (r"[＜<][^＞>\n]{1,30}[＞>]", "＜＞の穴埋めが残っている可能性"),
    (r"\u3008[^\u3009\n]{1,30}\u3009", "山括弧の穴埋めが残っている"),
    (r"○○|△△|□□|XXX|xxx", "○○・XXX などの仮の文字が残っている"),
]


def read_text(path):
    try:
        if path == "-":
            return sys.stdin.read()
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write("読み込みに失敗: %s (%s)\n次の手: UTF-8 のテキスト（.txt か .md）で保存し直して、パスを確かめてください。"
                         "Word や PDF は本文をコピーしてテキストにします。\n" % (path, e))
        sys.exit(3)


def scan(text):
    items = []
    for cid, name, article, patterns, conditional in ITEMS:
        found = all(re.search(p, text) for p in patterns)
        items.append({
            "id": cid, "item": name, "article": article,
            "keyword_found": found, "conditional": conditional,
        })
    leftovers = []
    for pat, label in LEFTOVERS:
        hits = re.findall(pat, text)
        if hits:
            leftovers.append({"label": label, "count": len(hits), "examples": sorted(set(hits))[:3]})
    return items, leftovers


def main(argv):
    ap = argparse.ArgumentParser(description="プライバシーポリシーの項目をキーワードで一次スクリーニングする（法適合の判断はしない）")
    ap.add_argument("path", help="ポリシー本文のテキストファイル。標準入力は -")
    ap.add_argument("--json", action="store_true", help="JSON で出力する")
    ap.add_argument("--strict", action="store_true", help="未検出（該当する場合のみの項目を除く）や取り残しがあれば終了コード1")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        sys.exit(2 if e.code not in (0, None) else 0)

    text = read_text(args.path)
    if not text.strip():
        sys.stderr.write("本文が空です。次の手: ポリシー本文を貼ったファイルを渡してください。\n")
        sys.exit(2)

    items, leftovers = scan(text)
    missing = [i for i in items if not i["keyword_found"] and not i["conditional"]]

    if args.json:
        print(json.dumps({"items": items, "leftovers": leftovers}, ensure_ascii=False, indent=2))
    else:
        print("| ID | 項目 | 条文 | キーワード |")
        print("|---|---|---|---|")
        for i in items:
            if i["keyword_found"]:
                mark = "検出"
            elif i["conditional"]:
                mark = "未検出（該当する場合のみ。事実を要確認）"
            else:
                mark = "未検出"
            print("| %s | %s | %s | %s |" % (i["id"], i["item"], i["article"], mark))
        print()
        if leftovers:
            print("取り残し:")
            for l in leftovers:
                print("- %s（%d件。例: %s）" % (l["label"], l["count"], " / ".join(l["examples"])))
        else:
            print("取り残し: なし")
        print()
        print("注: 「検出」は言葉があるだけで、内容の適否は判断していない。references/checklist.md で確かめること。")

    if args.strict and (missing or leftovers):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
