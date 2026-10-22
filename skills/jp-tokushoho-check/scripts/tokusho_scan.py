#!/usr/bin/env python3
"""特商法表記（通信販売）の本文を読み、点検項目のキーワードが有るかを一覧にする（一次スクリーニング）。

使い方:
  python3 scripts/tokusho_scan.py hyouki.txt            # 表で出力
  python3 scripts/tokusho_scan.py hyouki.txt --json     # JSON で出力
  cat hyouki.txt | python3 scripts/tokusho_scan.py -    # 標準入力
  python3 scripts/tokusho_scan.py hyouki.txt --strict   # 未検出・取り残し・要注意の記載があれば終了コード 1

できること: キーワードの有無、穴埋め記号の取り残し（【要入力】、＜＞、山括弧、○○、XXX）、
古い条番号・古い用語（規則9条・16条の2、瑕疵担保）、注意が要る言い回し（屋号だけ、私書箱、
「入荷次第」、「返品はご相談」など）の検出。
できないこと: 記載内容が法に適合しているかの判断。「検出」は言葉があるという意味だけで、
中身が足りているかは人が references/checklist.md で確かめる。外部へ通信せず、ファイルも書かない。

終了コード: 0 正常 / 1 --strict で指摘あり / 2 引数エラー・本文が空 / 3 読み込み失敗
実行できない環境では: references/checklist.md の項目 T01〜T22 を、本文を読みながら手で確かめる。
Python 3.9 の標準ライブラリだけで動く。
"""
import argparse
import json
import re
import sys

# (ID, 項目, 条文, 検出パターン(すべて含む), 該当する場合のみ必要か)
ITEMS = [
    ("T01", "事業者の氏名（名称）", "法11条6号・規則23条1号", [r"(氏名|名称|事業者名|販売業者|販売事業者|運営会社|会社名|屋号)"], False),
    ("T02", "住所", "法11条6号・規則23条1号", [r"(住所|所在地)"], False),
    ("T03", "電話番号", "法11条6号・規則23条1号", [r"(電話|TEL|Tel|tel|ＴＥＬ)"], False),
    ("T04", "代表者・責任者（法人）", "規則23条2号", [r"(代表者|代表取締役|運営責任者|責任者|統括責任者)"], True),
    ("T05", "外国事業者の国内事務所", "規則23条3号", [r"(事務所|国内)"], True),
    ("T06", "販売価格・送料", "法11条1号・規則24条1号", [r"(販売価格|価格|料金|代金|税込|送料)"], False),
    ("T07", "販売価格・送料以外の負担金", "規則23条4号", [r"(手数料|必要料金|追加料金|通信料|梱包|商品代金以外)"], True),
    ("T08", "支払の時期・方法", "法11条2号", [r"(支払方法|お支払い?方法|決済方法|支払時期|お支払い?時期|支払い?期限)"], False),
    ("T09", "引渡時期・提供時期", "法11条3号・規則24条2号", [r"(引渡|引き渡し|提供時期|発送|お届け|配送|ダウンロード|ご利用いただけ|利用開始|ご利用可能)"], False),
    ("T10", "申込みの期間", "法11条4号", [r"(申込.{0,3}期間|申込期限|申込み?期限|販売期間|受付期間)"], True),
    ("T11", "返品・キャンセル・解約に関する事項", "法11条5号・規則24条3号", [r"(返品|返金|キャンセル|解約|撤回|解除)"], False),
    ("T12", "返品特約の内容（可否・条件・費用負担）", "法15条の3・規則44条", [r"(返品|返金)[^\n]{0,60}(不可|できません|応じません|お受けしません|可能|できます|期間|以内|負担)"], False),
    ("T13", "契約不適合責任の特約", "規則23条5号", [r"(契約.{0,4}適合|不具合|欠陥|瑕疵|初期不良)"], True),
    ("T14", "動作環境", "規則23条6号", [r"(動作環境|推奨環境|対応OS|対応ＯＳ|対応ブラウザ|必要な環境|システム要件|ブラウザ|OS)"], True),
    ("T15", "継続契約の条件", "規則23条7号", [r"(定期|継続|サブスク|月額|年額|自動更新|自動的に更新|更新)"], True),
    ("T16", "数量制限などの特別な条件", "規則23条8号", [r"(数量制限|個数制限|限定|制限)"], True),
    ("T17", "請求により開示する旨（一部省略）", "法11条ただし書・規則25条", [r"(請求|開示|ご連絡いただ|お問い合わせ).{0,40}(遅滞なく|速やかに|遅延なく|開示|提供)"], True),
]

# 取り残しの穴埋め記号
LEFTOVERS = [
    (r"【要入力[^】]*】", "【要入力】が残っている"),
    (r"【要確認[^】]*】", "【要確認】が残っている"),
    (r"[＜<][^＞>\n]{1,30}[＞>]", "＜＞の穴埋めが残っている可能性"),
    (r"\u3008[^\u3009\n]{1,30}\u3009", "山括弧の穴埋めが残っている"),
    (r"○○|△△|□□|XXX|xxx", "○○・XXX などの仮の文字が残っている"),
]

# (パターン, ラベル, 項目ID, 参照)
FLAGS = [
    (r"施行規則\s*第?\s*(9|９)\s*条|規則\s*第?\s*(9|９)\s*条(?!の)|第\s*16\s*条の\s*2|第１６条の２",
     "旧い規則番号の可能性（返品特約の表示方法は現行 規則24条3号・44条）", "T21", "articles.md"),
    (r"瑕疵担保", "旧い用語の可能性（現行は「契約の内容に適合しない場合の責任」・規則23条5号）", "T21", "articles.md"),
    (r"(住所|所在地)[^\n]{0,20}(私書箱|ＰＯ?\s*BOX|PO\s*BOX)|私書箱", "私書箱は住所の表示にならない（消費者庁Q&A）", "T02", "omission.md"),
    (r"入荷次第", "「入荷次第」は引渡時期の表示にならない（消費者庁Q&A）", "T09", "checklist.md"),
    (r"(発送|お届け|ご利用|提供)[^\n]{0,12}(順次|追って)", "「順次」「追って」は期間・期限の表示になっていない可能性", "T09", "checklist.md"),
    (r"(返品|返金|キャンセル)[^\n]{0,30}(ご相談|相談に応じ|応相談|その都度)", "「ご相談」は返品特約の表示にならない（消費者庁Q&A）", "T12", "digital-subscription.md"),
    (r"(いかなる(場合|理由)でも|一切)[^\n]{0,20}(返品|返金)", "一律の返品・返金不可は、消費者契約法等で無効になり得る点を確認（要確認）", "T12", "digital-subscription.md"),
    (r"(電話番号|TEL|Tel|ＴＥＬ)[^\n]{0,30}(フォーム|メール)[^\n]{0,20}(ご連絡|ください|ご利用)", "電話番号の代わりにフォーム・メールだけの可能性（代替を認める一次情報は未確認。要確認）", "T03", "omission.md"),
    (r"(住所|所在地|電話番号|氏名)[^\n]{0,30}(非公開|公開していません|記載しません|掲載しません)", "非公開の記載。法11条ただし書の「請求により遅滞なく」の表示と体制が要る", "T17", "omission.md"),
    (r"(無料|0円|０円)[^\n]{0,40}(自動|その後|期間終了|経過)", "無料期間から有料への自動移行。移る時期と金額の表示を確認", "T15", "digital-subscription.md"),
    (r"(解約|退会)[^\n]{0,30}(電話のみ|電話でのみ|お電話のみ|メールのみ|平日|営業時間)", "解約方法・時間の限定。広告と最終確認画面にも明確に表示が要る", "T11", "digital-subscription.md"),
]


def read_text(path):
    try:
        if path == "-":
            return sys.stdin.read()
        with open(path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError) as e:
        sys.stderr.write("読み込みに失敗: %s (%s)\n次の手: UTF-8 のテキスト（.txt か .md）で保存し直して、パスを確かめてください。"
                         "Word や PDF、画面のスクリーンショットは本文をコピーしてテキストにします。\n" % (path, e))
        sys.exit(3)


def scan(text):
    items = []
    for cid, name, article, patterns, conditional in ITEMS:
        found = all(re.search(p, text) for p in patterns)
        items.append({"id": cid, "item": name, "article": article,
                      "keyword_found": found, "conditional": conditional})
    leftovers = []
    for pat, label in LEFTOVERS:
        hits = re.findall(pat, text)
        if hits:
            ex = [m.group(0) for m in re.finditer(pat, text)]
            leftovers.append({"label": label, "count": len(ex), "examples": sorted(set(ex))[:3]})
    flags = []
    for pat, label, cid, ref in FLAGS:
        ms = [m.group(0) for m in re.finditer(pat, text)]
        if ms:
            flags.append({"id": cid, "label": label, "count": len(ms),
                          "examples": sorted(set(ms))[:2], "see": "references/" + ref})
    return items, leftovers, flags


def main(argv):
    ap = argparse.ArgumentParser(
        description="特商法表記（通信販売）の項目をキーワードで一次スクリーニングする（法適合の判断はしない）")
    ap.add_argument("path", help="表記本文のテキストファイル。標準入力は -")
    ap.add_argument("--json", action="store_true", help="JSON で出力する")
    ap.add_argument("--strict", action="store_true",
                    help="未検出（該当する場合のみの項目を除く）・取り残し・要注意の記載があれば終了コード1")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        sys.exit(2 if e.code not in (0, None) else 0)

    text = read_text(args.path)
    if not text.strip():
        sys.stderr.write("本文が空です。次の手: 特商法表記の本文を貼ったファイルを渡してください。\n")
        sys.exit(2)

    items, leftovers, flags = scan(text)
    missing = [i for i in items if not i["keyword_found"] and not i["conditional"]]

    if args.json:
        print(json.dumps({"items": items, "leftovers": leftovers, "flags": flags},
                         ensure_ascii=False, indent=2))
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
        if flags:
            print("要注意の記載:")
            for f in flags:
                print("- [%s] %s（%d件。例: %s。%s）" % (f["id"], f["label"], f["count"], " / ".join(f["examples"]), f["see"]))
        else:
            print("要注意の記載: なし")
        print()
        if leftovers:
            print("取り残し:")
            for l in leftovers:
                print("- %s（%d件。例: %s）" % (l["label"], l["count"], " / ".join(l["examples"])))
        else:
            print("取り残し: なし")
        print()
        print("注: 「検出」は言葉があるだけで、内容の適否は判断していない。references/checklist.md で確かめること。"
              "最終確認画面（法12条の6）は表記の本文だけでは見えないので、画面の文言を別に確かめる。")

    if args.strict and (missing or leftovers or flags):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
