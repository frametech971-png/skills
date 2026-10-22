<!-- jp-data-normalizer v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-data-normalizer（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-data-normalizer
description: >-
  日本語の業務データ（名簿・顧客リスト・CSV）の表記ゆれを直す。全角半角、電話番号のハイフン、郵便番号の7桁、住所の都道府県・市区町村・番地の分割、和暦と西暦（昭和63年・令和8年3月）、文字化け（Shift_JIS/CP932 と UTF-8）を扱う。「この顧客リストの全角半角と電話番号の表記を揃えて」「住所を都道府県・市区町村・番地に分けて」「昭和63年を西暦に」「令和8年3月は西暦で何年」「CSVが文字化けする」「郵便番号をハイフンつき7桁に」と頼まれたときに使う。確信が持てない行は直さず「要確認」に出す。Keywords: normalize Japanese CSV, zenkaku hankaku, NFKC, wareki, Shift_JIS, CP932, BOM, phone number, postal code, address split。住所の実在確認・ジオコーディング、個人情報の外部送信、データベース設計、文章の言い回しの修正は対象外。
license: MIT
compatibility: "scripts/normalize.py は Python 3.9 以上（標準ライブラリのみ・通信なし）。実行できない環境でも本文の手順で判断できる。"
metadata:
  version: "1.0.0"
  author: frametech
---

# 日本語データの表記ゆれ直し

目的: 名簿・顧客リスト・CSV の全角半角、電話番号、郵便番号、住所、和暦、文字コードの表記ゆれを、列ごとに安全に揃える。
入力: CSV（またはその一部を貼ったもの）と、どの列を直したいか。単発の質問（和暦の換算、文字化けの原因）でもよい。
出力: 直した別ファイル（元は上書きしない）と、変更の要約、「要確認」の一覧。直せなかった値は理由つきで返す。

**個人情報（氏名・電話・住所）を外部のサービスへ送らない。** 処理は手元の `scripts/normalize.py` で行う。通信はしない。データを外のツールに貼るよう勧めない。

## 1. 頼まれたことで分ける

| 頼まれたこと | やること |
|---|---|
| CSV の表記を揃えて・直して | §2 の手順で `scripts/normalize.py` を使う |
| 和暦↔西暦、「令和8年3月は？」 | `python3 scripts/normalize.py --try date "令和8年3月"` / `--to-wareki 1989-01-07`。境界日は [references/wareki.md](references/wareki.md) |
| 文字化けする、Shift_JIS か UTF-8 か | [references/text-and-encoding.md](references/text-and-encoding.md) の文字コードの節。判別は `normalize.py` の要約に出る |
| 電話番号・郵便番号の桁と区切り | [references/phone-postal-address.md](references/phone-postal-address.md) |
| 住所を分けて | 同上の「住所の分割」。辞書なしでは誤るので要確認を残す設計を説明する |
| 全角半角（NFKC）の質問 | [references/text-and-encoding.md](references/text-and-encoding.md) の落とし穴の表 |

## 2. CSV を直す手順

1. **列を確かめる。** ヘッダーを見て、直す列と型を決める。曖昧なら**1回にまとめて**聞く（どの列が電話か、住所を分けた列が要るか、日付の出力形式）。型:

   | 型 | 直すこと |
   |---|---|
   | `text` | NFKC（全角英数→半角、半角カナ→全角カナ、濁点を合成、㈱→(株)）、空白の整理、不可視文字の除去 |
   | `name` | text と同じ。互換漢字は変えない。姓名の間は空白1つ。**髙/高 などの異体字は統一しない** |
   | `phone` | 数字を取り出し、種別に応じてハイフンを付ける。`+81` を `0` に。先頭の0が消えた9〜10桁は補って要確認 |
   | `zip` | `〒` を取り、7桁なら `123-4567`（`--zip-style plain` で数字のみ）。6桁は0を補って要確認 |
   | `address` | 全角数字→半角、数字間のダッシュ→`-`。3列（`_都道府県` `_市区町村` `_番地以降`）に分割 |
   | `date` | 和暦・西暦を `YYYY-MM-DD`（`--date-format slash` `jp` も）。年のみ・年月のみも可 |
   | `number` | 全角→半角、桁区切りと「円」を除く、全角マイナスを `-` に |

2. **必ず先に `--dry-run`。** 何も書かずに変更件数・要確認・変更の例を見る。

   ```
   python3 scripts/normalize.py 顧客.csv --map "氏名=name,電話=phone,郵便番号=zip,住所=address,生年月日=date" --dry-run
   ```

3. **要約を読んで、おかしい例がないか確かめてから実行する。** `--dry-run` を外す。出力は `顧客.normalized.csv`（既にあれば止まる。`-o` で別名、上書きは `--force`）。元のファイルは変更されない。

4. **「要確認」列を人に見てもらう。** 直せなかった・推測を含む行が理由つきで入っている。要確認の行は、全部を人が確かめるまで本番データに入れない、と伝える。

5. **文字コード。** 入力の文字コード（BOMつき UTF-8 → UTF-8 → CP932 の順に自動判別）は要約に出る。Excel で開く用途なら `--out-encoding utf-8-sig`（BOMつき）か `cp932`。BOMなしの UTF-8 は Windows の Excel で文字化けしうる。CP932 に無い文字（絵文字など）があると cp932 出力は失敗するので UTF-8（BOMつき）にする。

実行の失敗は、メッセージに「原因と次の手」が出る。終了コード: 0 正常（要確認があっても 0）、2 引数の誤り、3 入力を読めない、4 出力を書けない。

## 3. 守ること

- **直せないものを直さない。** 確信が持てない値（市区町村の切れ目、市外局番の桁が決まらない、存在しない日付、内線つきの電話番号）は元の値を残して「要確認」にする。推測で埋めない（都道府県を市名から推測しない、2桁の年の世紀を推測しない）。
- **元のファイルを書き換えない。** 出力は別名。
- **異体字・人名は統一しない。** `髙橋` と `高橋` は別の人かもしれない。
- NFKC は万能ではない。長音「ー」はハイフンではない（`サーバー` を壊さない）、`〜` と `～`、丸数字、合字、単位記号の扱いは [references/text-and-encoding.md](references/text-and-encoding.md)。展開された文字の件数は要約に出る。
- 和暦は元号の境界日（昭和64年1月7日まで、平成は1月8日から、令和は2019-05-01 から など）と、明治5年12月2日までが旧暦である点に注意する。境界で存在しない日付は直さず指摘する。
- 郵便番号・住所が**実在するか**は確かめない（対象外）。必要なら日本郵便のデータを利用者が使う。

## 4. 返す形

```
変更の要約: 12行中 8行を変更（電話 6件・住所 4件・生年月日 5件）／ 文字コード cp932 → 出力 utf-8-sig
出力: 顧客.normalized.csv（元は変更なし）

要確認（3行）
- 行6 電話: 内線つき（03-1234-5678 内線123）— 直していない
- 行9 住所: 都道府県が先頭に無い — 市区町村のみ分割
- 行7 生年月日: 昭和64年1月8日は存在しない（平成元年1月8日） — 直していない
```

件数は `normalize.py` の出力から写す。数えずに推測しない。

## 5. 実行できない環境では

`scripts/normalize.py` は Python 3.9 の標準ライブラリだけで動き、通信もファイル削除もしない。実行できない環境（コード実行のないチャットなど）では、数行〜数十行なら手順を応用して直し、**できない部分（市外局番の桁、和暦の境界）は references の表を見て判断し、自信がなければ「要確認」にする**。件数の多いファイルは、ユーザーに `python3 scripts/normalize.py --help` を手元で実行してもらう。

貼り付け版（1ファイルにまとめた版）では `scripts/normalize.py` と `references/area-codes.txt` は大きいので省略してよい。その場合、固定電話の市外局番の桁は 03・06（2桁）など確実なものだけ直し、他は「要確認」にする。

## 6. 事実の確認日

電話番号の種別・桁数、市外局番、元号の境界日、郵便番号の桁数は、各 reference に出典 URL と確認日（2026-10-21）を書いてある。**確認日から90日を過ぎたら、出典を読み直して `references/` と `references/area-codes.txt` を更新する。** 最新は公式で確認する: 総務省の電気通信番号制度 https://www.soumu.go.jp/main_sosiki/joho_tsusin/top/tel_number/index.html 、国立天文台 暦Wiki「元号」 https://eco.mtk.nao.ac.jp/koyomi/wiki/CEF2BBCB2FB8B5B9E6.html 、日本郵便 郵便番号データ https://www.post.japanpost.jp/zipcode/dl/readme.html 。

=== FILE: references/area-codes.txt ===
# 市外局番の一覧（先頭の0を除く。[codes] 節は1行に1つ）
# 出典1: 総務省「市外局番の一覧」（令和8年3月1日現在） https://www.soumu.go.jp/main_sosiki/joho_tsusin/top/tel_number/shigai_list.html
# 出典2（[short] 節）: 総務省「電気通信番号指定状況」の固定電話の指定表（先頭桁ごとの PDF。各ファイルの時点は令和5年7月〜令和8年9月） https://www.soumu.go.jp/main_sosiki/joho_tsusin/top/tel_number/number_shitei.html
# 確認日: 2026-10-21。機械的に取り出した（手で直さない）。確認日から90日を過ぎたら出典を開き直して作り直す。
# [short] 節: 先頭に市外局番の候補が複数ある番号のうち、長い方ではなく『短い方の市外局番』が指定されている市内局番の先頭5桁（0を除く）。
#   書式: <市外局番の桁数>:<先頭3桁> <続く2桁> <続く2桁> …   例: 2:255 12 13 → 25512・25513 は市外局番が2桁（025）
[codes]
3
4
6
11
15
17
18
19
22
23
24
25
26
27
28
29
42
43
44
45
46
47
48
49
52
53
54
55
58
59
72
73
75
76
77
78
79
82
83
84
86
87
88
89
92
93
95
96
97
98
99
123
124
125
126
133
134
135
136
137
138
139
142
143
144
145
146
152
153
154
155
156
157
158
162
163
164
165
166
167
172
173
174
175
176
178
179
182
183
184
185
186
187
191
192
193
194
195
197
198
220
223
224
225
226
228
229
233
234
235
237
238
240
241
242
243
244
246
247
248
250
254
255
256
257
258
259
260
261
263
264
265
266
267
268
269
270
274
276
277
278
279
280
282
283
284
285
287
288
289
291
293
294
295
296
297
299
422
428
436
438
439
460
463
465
466
467
470
475
476
478
479
480
493
494
495
531
532
533
536
537
538
539
544
545
547
548
550
551
553
554
555
556
557
558
561
562
563
564
565
566
567
568
569
572
573
574
575
576
577
578
581
584
585
586
587
594
595
596
597
598
599
721
725
735
736
737
738
739
740
742
743
744
745
746
747
748
749
761
763
765
766
767
768
770
771
772
773
774
776
778
779
790
791
794
795
796
797
798
799
820
823
824
826
827
829
833
834
835
836
837
838
845
846
847
848
852
853
854
855
856
857
858
859
863
865
866
867
868
869
875
877
879
880
883
884
885
887
889
892
893
894
895
896
897
898
920
930
940
942
943
944
946
947
948
949
950
952
954
955
956
957
959
964
965
966
967
968
969
972
973
974
977
978
979
980
982
983
984
985
986
987
993
994
995
996
997
1267
1372
1374
1377
1392
1397
1398
1456
1457
1466
1547
1558
1564
1586
1587
1632
1634
1635
1648
1654
1655
1656
1658
4992
4994
4996
4998
5769
5979
7468
8387
8388
8396
8477
8512
8514
9802
9912
9913
9969
[short]
1:420 00 01 02 03 04 05 06 07 08 09
1:429 00 01 02 03 04 05 06 07 08 09 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 90 91 92 93 94 95 96 97 98 99
1:470 00 01 02 03 04 05 06 07 08 09 90 91 92 93 94 95 96 97 98 99
1:471 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
2:154 10 11 12 13 14 15 16 18 19 80 82 83 84 85 86 87 88 89
2:155 10 11 12 13 14 15 16 18 19 70 72 73 74 75 76 77 78 79
2:223 00 01 02 03 04 05 06 07 08 09 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
2:255 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 90 92 93 94 95 96 97 98 99
2:256 00 01 02 03 04 05 06 07 08 09
2:257 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 18 19 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 92 93 94 95 96 97 98 99
2:258 00 01 02 03 04 05 06 07 08 09
2:264 00 01 02 03 04 05 06 07 08 09 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
2:278 00 01 02 03 04 05 06 07 08 09 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
2:283 00 01 02 03 04 05 06 07 08 09 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49
2:289 00 01 02 03 04 05 06 07 08 09 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59
2:293 00 01 02 03 04 05 06 07 08 09 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99
2:422 00 01 02 03 04 05 06 07 08 09
2:428 00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 18 19 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69
2:539 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 64 65 66 67 68 69 70 71 72 73 75 76 78 79 80 81 82 83 84 85 86 87 88 89
2:599 90 91 92 93 94 95 96 97 98 99
2:794 00 01 02 03 04 05 06 07 08 09 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 90 91 92 93 94 95 96 97 98 99
2:795 00 01 02 03 04 05 06 07 08 09 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 90 91 92 93 94 95 96 97 98 99
2:796 00 01 02 03 04 05 06 07 08 09 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79
2:824 00 01 02 03 04 05 06 07 08 09 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 90 91 92 93 94 95 96 97 98 99
2:829 00 01 02 03 04 05 06 07 08 09 21 22 23 24 25 26 27 28 29 41 42 43 60 61 62 63 64 65 66 67 68 69 90 91 92 93 94 95 96 97 98 99
2:836 00 01 02 03 04 05 06 07 08 09
2:837 66 67 68 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89
2:839 60 63 66
2:863 62 63 64 65 67 68 69
2:865 20 21 22 23 24 25 26 27 28 29 52 53
2:866 00 01 02 03 04 05 06 07 08 09 91 97 98
2:867 22 23 24 26 28 37 38
2:868 00 01 02 03 04 05 06 07 08 09 90 91 92 93 94 95 96 97 98 99
2:869 00 01 02 03 04 05 06 07 08 09 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 94 95 96 97 98 99
2:993 31 43 45 47
2:994 00 01 02 03 04 05 06 07 08 09 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89
3:597 90 97 98

=== FILE: references/phone-postal-address.md ===
# 電話番号・郵便番号・住所の分割

確認日: 2026-10-21（90日後の 2027-01-19 を過ぎたら出典を読み直す）。番号は総務省が指定を増やし続けている。このファイルと `references/area-codes.txt` は確認日時点の写し。

## 電話番号

出典（すべて総務省、確認日 2026-10-21）
- 電気通信番号制度（番号の種別と構成表）: https://www.soumu.go.jp/main_sosiki/joho_tsusin/top/tel_number/index.html
- 電話番号に関するQ&A: https://www.soumu.go.jp/main_sosiki/joho_tsusin/top/tel_number/q_and_a.html
- 電気通信番号指定状況（電気通信番号計画 令和元年総務省告示第6号による公表。ページの時点は令和8年10月1日）: https://www.soumu.go.jp/main_sosiki/joho_tsusin/top/tel_number/number_shitei.html
- 市外局番の一覧（令和8年3月1日現在）: https://www.soumu.go.jp/main_sosiki/joho_tsusin/top/tel_number/shigai_list.html

### 桁数（市外局番の 0 を含めた全体）

| 種別 | 先頭 | 全体の桁 | 構成表での書き方 |
|---|---|---|---|
| 固定電話 | 0 + 市外局番 | 10 | `0ABCDEFGHJ`。「市外局番と市内局番の桁数は合せて5桁」、市外局番は1〜4桁、市内局番も1〜4桁 |
| 携帯電話 | 070 / 080 / 090（060 も携帯番号） | 11 | `090CDEFGHJK`（C は 0 以外） |
| IP電話 | 050 | 11 | `050CDEFGHJK`（C は 0 以外） |
| フリーダイヤル | 0120 | 10 | 「0120 の番号は全部で10桁」 |
| フリーダイヤル（0800） | 0800 | 11 | 「0800 は携帯電話、PHSと同様に全部で11桁」 |
| ナビダイヤル（統一番号） | 0570 | 10 | 付加的役務電話番号 `0AB0DEFGHJ`（AB は 12, 17, 18, 57, 80, 99） |
| 情報料代理徴収など | 0990 / 0180 / 0170 | — | 区切り方は決まっていないので `scripts/normalize.py` は区切らない |
| 国際表記 | +81 | 先頭の 0 を除いた形 | `+81 90-…` は `090-…`、`+81 (0)3-…` は `03-…` に戻す |

- ハイフンの位置を定めた規定は、上の総務省の資料では確認できなかった（番号の構成は定めているが表記の区切りは別）。市外局番・市内局番・加入者番号（下4桁）の区切りが慣習。携帯・050 は 3-4-4、0120・0570 は 4-3-3、0800 は 4-3-4、固定電話は市外局番-市内局番-4桁。
- 数字だけで書かれた固定電話の区切りは、市外局番の桁数を知らないと決められない。03 / 06 は2桁（`03-1234-5678`）、045 は3桁（`045-123-4567`）、0422 は4桁（`0422-12-3456`）、04992 は5桁（`04992-2-1234`）。
- **市外局番の候補が複数ある番号がある**。先頭が `04` の番号は 04（単独）・042・043…の候補があり、`04-2998-…` のように、同じ数字の並びが市外局番 04＋市内局番 2998 にも 042＋998 にも読める。総務省の指定状況の表で市内局番まで見ないと決まらない（`0429981111` は表では 04 の側）。`references/area-codes.txt` の `[short]` 節に、短い方の市外局番が指定されている市内局番（総務省の指定状況の表から機械的に取り出した 1,203 件）を入れてある。表に無い市内局番（確認日より後に指定されたものなど）は長い方に寄せるため、**新しい市内局番では誤ることがある**。確実さが要る用途では、番号の持ち主に確認する。
- 市外局番の一覧は更新される。`area-codes.txt` は確認日から90日を過ぎたら出典を開き直して作り直す。
- 9〜10桁で 0 から始まらない数字は、Excel が先頭の 0 を消した可能性が高い。`scripts/normalize.py` は 0 を補って「要確認」に書く。
- 「内線」「ext」「#」「／」「、」で複数の番号が1つの欄に入っているものは、直さず「要確認」にする。

## 郵便番号

- 7桁（日本郵便「郵便番号データの説明」の項目に「郵便番号（7桁）」と「（旧）郵便番号（5桁）」。https://www.post.japanpost.jp/zipcode/dl/readme.html 、確認日 2026-10-21）。表記は `123-4567` が一般的。ハイフンなしの7桁の数字でもよいので、受け側のシステムに合わせる（`--zip-style plain`）。
- 先頭が `0` の郵便番号（北海道など）は Excel で 6 桁になりやすい。`〒` は取る。
- 5桁（旧郵便番号）、6桁でハイフンあり、7桁を超えるものは直さず「要確認」。
- **郵便番号が実在するか、住所と一致するかは確かめない**（対象外）。必要なら日本郵便の郵便番号データ（KEN_ALL）や郵便番号・デジタルアドレス API を、利用者が自分で使う。

## 住所の分割

完全な辞書（日本郵便の KEN_ALL など）が無いと、市区町村の切れ目を必ず正しく決めることはできない。そこで次の規則で分け、**確信が持てない行は直さず「要確認」列に理由を書く**。

分け方（`scripts/normalize.py` の address 型。分けた結果は `<列名>_都道府県` `_市区町村` `_番地以降` の3列に出る）
1. 先頭が47都道府県のどれかなら都道府県。なければ空欄にして「都道府県が先頭に無い」と報告する（市区町村から都道府県を**推測しない**。同名の市がある）。
2. 東京都の23区、政令指定都市20市（札幌・仙台・さいたま・千葉・横浜・川崎・相模原・新潟・静岡・浜松・名古屋・京都・大阪・堺・神戸・岡山・広島・北九州・福岡・熊本。総務省「指定都市一覧」 https://www.soumu.go.jp/main_sosiki/jichi_gyousei/bunken/shitei_toshi-ichiran.html 、確認日 2026-10-21）は閉じた一覧で照合し、政令市は区まで1つの市区町村にする（`横浜市港北区`）。
3. 名前に 市区町村郡 の字を含む自治体のうち既知のもの（武蔵村山市・東村山市・東村山郡・町田市・市川市・四日市市・大町市・郡山市 など）は頭から照合する。
4. それ以外は、先頭から10字以内で最初に現れる 市・区・町・村・郡 までを市区町村とする。直後にも 市区町村郡 の字が続く、または先頭の字がそれ（`市川`、`町田`）のときは「名前の途中かもしれない」として要確認にする。郡は、その後の 町・村 までを含める（`空知郡南幌町`）。
5. 市区町村より後ろが空、番地の数字が無い、市区町村が10字を超える、は要確認。

直すこと: 全角数字・全角英字を半角に、数字に挟まれたダッシュ・長音（`１ー２ー３`、`1－2－3`）を `-` に、連続する空白を1つに。
直さないこと: 漢数字の丁目（`一丁目`）、`丁目`/`番`/`号` と `-` の書き換え（`1丁目2番3号` と `1-2-3` は同じ場所だが、システムによって使い分けるので勝手に統一しない）、ビル名・部屋番号の切り出し、旧字体・異体字、郵便番号との突き合わせ、住所の実在確認。

### よくある誤分割（辞書なしでは見分けにくい）
- `東村山市`・`武蔵村山市`（村 で切ると誤る）、`四日市市`・`大町市`（途中の 市・町 で切ると誤る）、`町田市`・`市川市`（先頭の字が 町・市）。
- 町名に 市・区・町・村 が入る住所（例: `東京都千代田区神田町`）。市区町村は `千代田区`、`神田町` は町域。東京23区は閉じた一覧で先に決めるので誤らない。
- 都道府県が省略された住所（`新宿区西新宿…`）。同名の区がある（`中央区` は東京・大阪・札幌・千葉・福岡・神戸など）ので都道府県を補わない。
- 「郡」を含む（`北海道空知郡南幌町`）。郡を市区町村に含めるかは取り決め次第。ここでは `空知郡南幌町` を1つにする。受け側が郡を分けるなら後で分ける。

=== FILE: references/text-and-encoding.md ===
# 全角半角・NFKC の落とし穴と文字コード

確認日: 2026-10-21（90日後の 2027-01-19 を過ぎたら出典を読み直す）。下の変換結果は Python 3.9.6（Unicode 13.0.0）の `unicodedata` で実測した。Unicode のバージョンが上がると変わる字がある。

出典: Unicode Standard Annex #15 Unicode Normalization Forms https://www.unicode.org/reports/tr15/ （NFKC は互換等価の字を寄せて合成する）。

## NFKC でよくなること

- 全角英数・全角記号 → 半角（`Ａｂｃ１２３` → `Abc123`）。全角スペース → 半角スペース。
- 半角カナ → 全角カナ。濁点・半濁点は前の字と合成される（`ｶﾞ` → `ガ`、`ﾊﾟ` → `パ`、`ｳﾞ` → `ヴ`）。**濁点を別の字として扱う前処理（半角カナを1字ずつ変換する、など）は壊れる**。必ず NFKC のように文字列ごと処理する。濁点の前にスペースが入っている（`ｶ ﾞ`）と合成されず `カ ゙` になる。

## NFKC の落とし穴

| 入力 | NFKC の結果 | 問題と対処 |
|---|---|---|
| `－`(U+FF0D) | `-` | 良い。だが他のダッシュは残る |
| `−`(U+2212 マイナス)、`‐`(U+2010)、`―`(U+2015)、`—`(U+2014)、`ー`(U+30FC 長音) | そのまま | 電話・郵便・番地の区切りに使われていても `-` にならない。数字の区切りの位置では自分で `-` に寄せる（`scripts/normalize.py` の phone / zip / address / number）。**文字列の中の長音 `ー` は寄せない**（`サーバー` が壊れる） |
| `ｰ`(U+FF70 半角長音) | `ー`(U+30FC) | 数字の間にあれば `-` へ |
| `～`(U+FF5E) | `~`(ASCII) | `1～3階` が `1~3階` になる。`〜`(U+301C) は残る。`scripts/normalize.py` は `～` を `〜` に寄せてから NFKC をかけ、波ダッシュを ASCII にしない |
| `①`〜`⑳` | `1`〜`20` | 丸数字が数字になる。意味（項番・選択肢）が変わることがある。列に丸数字が混じっていたら件数を報告する |
| `㈱` `㈲` | `(株)` `(有)` | 合字の展開。`㍿` は `株式会社` になる。会社名の表記をそろえる目的なら良いが、社名に含まれる文字が変わるので報告する。`(株)` と `株式会社` を同一視するかは別の判断 |
| `㎡` `㌔` `㌫` | `m2` `キロ` `パーセント` | 単位記号が展開される。`㎡` → `m2`（`m²` ではない） |
| `Ⅲ` `№` `℡` | `III` `No` `TEL` | ローマ数字・記号が文字に展開される |
| 互換漢字 U+F900〜FAFF の一部（例: U+FA10） | 別の字（U+FA10 は `塚`(U+585A)） | 人名の字体が変わりうる。`scripts/normalize.py` の name 型は U+F900〜FAFF の字を NFKC にかけず残す |
| `髙`(U+9AD9) `﨑`(U+FA11) | そのまま | 異体字は NFKC では統一されない。`高橋` と `髙橋` は別の文字列。名簿の名寄せで同一視するかは人が決める |

## 空白・不可視文字

ゼロ幅スペース（U+200B）、BOM（U+FEFF）、ノーブレークスペース（U+00A0）が貼り付けで混じることがある。NFKC は U+00A0 を空白にするが、U+200B と U+FEFF は消さない。`scripts/normalize.py` は不可視文字を消し、連続する空白を1つにして前後を削る。**氏名の姓と名の間の空白は消さず1つにする**（`山田　太郎` → `山田 太郎`）。

## 文字コード

| 呼び名 | 実体 | 注意 |
|---|---|---|
| UTF-8（BOMなし） | Unicode | Mac・Linux・Web・多くの API の標準。日本郵便の UTF-8 版の郵便番号データも BOM なし（https://www.post.japanpost.jp/zipcode/dl/utf-readme.html 、確認日 2026-10-21） |
| UTF-8（BOMつき） | 先頭に EF BB BF | **Windows の Excel で直接開くと文字化けしないのはこちら**。Microsoft: 「You can open a CSV file encoded with UTF-8 normally if it was saved with BOM」 https://support.microsoft.com/en-us/office/opening-csv-utf-8-files-correctly-in-excel-8a935af5-3416-4edd-ba7e-3dfd2bc4a032 （確認日 2026-10-21）。BOM がないと Excel は別の文字コードとみなして文字化けすることがある。BOM なしを開くときは「データ」→「テキストまたは CSV から」で文字コードを選ぶ |
| CP932（Windows-31J、Microsoft の Shift_JIS） | 日本語 Windows が「Shift_JIS」「ANSI」と呼ぶもの | 日本の業務システムや古い Excel の「CSV（コンマ区切り）」はこれ。日本郵便の KEN_ALL（Shift_JIS 版）は「MS漢字コード（SHIFT JIS）」（https://www.post.japanpost.jp/zipcode/dl/readme.html 、確認日 2026-10-21） |

**Python の `shift_jis` と `cp932` は別物**。`①` `㈱` `髙` などの機種依存文字は `cp932` にだけある。`shift_jis` で読む・書くとエラーになる（実測: `'①'.encode('shift_jis')` は失敗、`.encode('cp932')` は成功）。日本語 Windows 由来の「Shift_JIS」のファイルは `cp932` で読む。`scripts/normalize.py` は `shift_jis` と書かれても `cp932` として扱う。

`cp932` で読むと、`～` は U+FF5E、`－` は U+FF0D、`￠￡￢` は U+FFE0〜FFE2 になる（実測）。JIS 規格どおりの `shift_jis` だと `〜`(U+301C)・`−`(U+2212) になり、同じバイトでも別の文字になる。ファイルを往復すると波ダッシュやマイナスが別の字に化けるのはこのため。

判別の目安: 先頭が EF BB BF なら BOM つき UTF-8。UTF-8 として厳密に読めれば UTF-8。読めなければ CP932 を試す。短いファイルや英数字だけのファイルは両方で読めて区別できない（中身が同じなので問題ない）。`scripts/normalize.py` はこの順で自動判別し、結果を要約に出す。判別を間違えたら `--encoding` で指定する。

CP932 に無い文字（絵文字、一部の旧字体、ハングルなど）を CP932 で書き出すと失敗する。その場合は UTF-8（BOMつき）で出す。

**Excel で CSV を開くと壊れるもの**（コンピューターの設定ではなくデータの性質）: 先頭の 0 が消える（ハイフンなしで書いた電話番号 `0312345678`、郵便番号 `0600001`。日本郵便も「上1けたあるいは2けたの『0』『00』が表示されない場合や、年月日で表示される場合」と注意している）、長い数字が `1.23E+12` になる、`1-2` が日付になる。**CSV を Excel で開いて保存し直した後のファイルは、0 が欠けた値が混ざっている前提で扱う**（`scripts/normalize.py` は 9〜10桁の電話番号・6桁の郵便番号に 0 を補い、「要確認」に書く）。

=== FILE: references/wareki.md ===
# 和暦と西暦（明治〜令和）

確認日: 2026-10-21（90日後の 2027-01-19 を過ぎたら出典を読み直す）。元号は新しく増えることがある。今の最新は令和。

## 境界日

| 元号 | 始まり | 終わり（その日を含む） | 根拠（一次情報へたどれる出典） |
|---|---|---|---|
| 明治 | 明治元年（1868）。慶応4年を明治元年とする | 1912-07-29（明治45年7月29日） | 明治元年9月8日 詔書「明治改元の詔」 |
| 大正 | 1912-07-30 | 1926-12-24 | 明治45年7月30日 詔書「07月30日以後を大正元年とする」 |
| 昭和 | 1926-12-25 | 1989-01-07 | 大正15年12月25日 詔書「12月25日以後を昭和元年とする」 |
| 平成 | 1989-01-08 | 2019-04-30 | 昭和64年1月7日 政令第1号「01月08日以後を平成元年とする」 |
| 令和 | 2019-05-01 | （続いている） | 平成31年4月1日 政令第143号「05月01日以後を令和元年とする」 |

出典（確認日 2026-10-21）: 国立天文台 暦計算室「暦Wiki／歴史／元号」 https://eco.mtk.nao.ac.jp/koyomi/wiki/CEF2BBCB2FB8B5B9E6.html （最終更新 2026-08-06。国立公文書館・国立国会図書館・法令データ提供システムの原典へのリンクつき）。

- 明治の開始日は、scripts では 1868-01-25（慶応4年1月1日にあたるとされる日）を置いている。この「西暦の日付」への換算は二次資料の変換表と一致するが、一次情報（詔書）が定めているのは「慶応4年を明治元年とする」まで。**明治元年〜5年の月日は西暦に直さない**（下記）。
- 年だけの換算は 西暦 = 開始年 + 元号の年 − 1。明治元年=1868、大正元年=1912、昭和元年=1926、平成元年=1989、令和元年=2019。

## 落とし穴

- **元号の切り替わりの年は2つの元号にまたがる**。1912 年は 明治45年と大正元年、1926 年は 大正15年と昭和元年、1989 年は 昭和64年と平成元年、2019 年は 平成31年と令和元年。西暦の年だけから和暦を決めない。日付まで分かれば1つに決まる（例: 1989-01-07 は昭和64年1月7日、1989-01-08 は平成元年1月8日）。
- **存在しない組み合わせ**: 昭和64年1月8日以降、平成31年5月1日以降、大正15年12月25日以降、明治45年7月30日以降、昭和元年1月1日〜12月24日、大正元年1月1日〜7月29日、平成元年1月1日〜7日、令和元年1月1日〜4月30日。入力にあったら誤りか別の元号の日付。`scripts/normalize.py` は直さず「要確認」にして、西暦の日付がどの元号にあたるかを添える。
- **明治5年12月2日までは旧暦（太陰太陽暦）**。明治5年12月3日が明治6年1月1日（太陽暦）にあたる（国立天文台「暦Wiki／歴史／日本の暦／6.明治維新と太陽暦」 https://eco.mtk.nao.ac.jp/koyomi/wiki/CEF2BBCB2FC6FCCBDCA4CECEF12F6.CCC0BCA3B0DDBFB7A4C8C2C0CDDBCEF1.html 、確認日 2026-10-21。改暦の布告は明治5年11月9日）。そのため明治5年12月3日という日付は存在せず、明治5年以前の月日をそのまま西暦の月日にしてはいけない。年だけなら換算してよい。明治6年1月1日以降は西暦と同じ暦。
- 「元年」「元」は 1 年。「令和元年5月」は 2019-05。略号は M T S H R（大文字・小文字とも）。
- 漢数字（昭和六十三年）、全角数字（令和８年）は半角に直してから読む。2桁の西暦（88/4/1）は世紀を決められないので読まない（「要確認」）。
- 年度（4月始まり）と暦年は別。「令和7年度」を 2025 年とだけ書かない。年度を聞かれたら 2025-04-01〜2026-03-31 と範囲で書く。

## 使い方

```
python3 scripts/normalize.py --try date "昭和63年4月1日"      # 1988-04-01
python3 scripts/normalize.py --try date "令和8年3月"          # 2026-03
python3 scripts/normalize.py --to-wareki 1989-01-07           # 昭和64年1月7日
python3 scripts/normalize.py --to-wareki 2019                 # 平成31年、令和元年（切り替わりの年）
```

スクリプトを実行できない環境では、上の表の「始まり」から年を数え、境界の年は両方の元号を書いて日付で確かめる。

=== FILE: scripts/normalize.py ===
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

=== FILE: LICENSE ===
MIT License

Copyright (c) 2026 frametech

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
