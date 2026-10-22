<!-- jp-business-days v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-business-days（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-business-days
description: >-
  日本の祝日・振替休日・国民の休日を踏まえて、営業日を計算する。「2026年の祝日を一覧にして」「10月30日から3営業日後は？」「今月の営業日数は？」「支払期限が土日祝なら翌営業日に直して」「この日は祝日？」「年末年始（12/29〜1/3）を休みにして営業日を数えて」と頼まれたときに使う。祝日は暗算や記憶で答えず、法令のルール（ハッピーマンデー・春分秋分・振替休日・国民の休日）を実装したスクリプトで出し、内閣府の祝日CSVと全年一致を確認済み（1955〜2027年）。年末年始・お盆は法定の祝日ではなく会社の休みとして別に扱う。2028年以降の春分・秋分は推定と明記する。Keywords: Japanese holidays, business days, working days, next business day, add business days, 祝日, 振替休日, 営業日。銀行の営業日・振込日の個別判断、他国の祝日、契約や法令上の期限の法的な結論は対象外。
license: MIT
compatibility: python3（3.9 以上、標準ライブラリだけ）が実行できる環境。実行できなくても手順は書けるが、祝日と営業日の数え上げは誤りやすいので結果に「未検算」と付ける。
metadata:
  version: "1.0.0"
  author: frametech
---

# 日本の営業日の計算

目的: 日本の祝日を踏まえた営業日の計算（N営業日後・期間内の営業日数・期限の休日繰り延べ・祝日の一覧）を、日付を間違えずに出す。
入力: 起点の日付・期間・年・会社の休み（あれば）。足りないものは §2 のとおり扱う。
出力: 結果の日付（曜日つき）と、計算に効いた祝日・休みの名前、前提の一覧。

## 1. 手順

1. 依頼を §3 のコマンドに当てはめる。相対表現（「今日」「来週の月曜」）は、基準日を確かめてから日付にする。基準日が分からなければ聞く。
2. **祝日・曜日・営業日の数え上げは自分で暗算せず、`python3 scripts/jbd.py` で出す。** 出力の日付・曜日・祝日名は、そのまま書き写す。
3. 結果に前提を添える（§5）。会社の休み（年末年始・お盆）は §4。
4. スクリプトを実行できない環境では、`references/holidays-law.md` の表で祝日を出し、1日ずつ数えて、末尾に「スクリプトで未検算」と書く。

## 2. 足りない情報の扱い

| 状況 | 扱い |
|---|---|
| 起点の日付・年が無い（「3営業日後は？」だけ） | 日付を作らず、起点の日付を聞く。「今日」なら基準日の確認も |
| 土日祝以外の会社の休みが分からない | まず土日祝だけで計算し、「年末年始・お盆などの会社休みは含めていません」と添える。年末年始をまたぐなら休みの範囲を聞く |
| 「N営業日以内」など、起点を含めるか不明 | 既定（起点を数えない・両端を含める）で出し、その前提を書く |
| 土曜営業の会社 | `--weekend sun`（日曜だけ休み） |

## 3. コマンド

```
python3 scripts/jbd.py holidays 2026                  # 年の祝日・休日の一覧（振替休日・国民の休日つき）
python3 scripts/jbd.py is-holiday 2026-09-22          # 祝日か。営業日か
python3 scripts/jbd.py add 2026-10-30 3               # 3営業日後（起点は数えない。負の数で前）
python3 scripts/jbd.py count 2026-10-01 2026-10-31    # 期間内の営業日数（両端を含む）
python3 scripts/jbd.py next-business-day 2026-11-21   # 休みなら翌営業日（--previous で前営業日）
python3 scripts/jbd.py month-end 2026-11              # 月末が休みなら翌営業日（支払期限）
python3 scripts/jbd.py verify-csv syukujitsu.csv      # 内閣府の祝日CSVと全年を突き合わせる
```

共通の指定: `--extra-closed 12-29..01-03`（会社の休み。毎年・年またぎ可。カンマで複数）、`--weekend sun`、`--json`、`--csv <内閣府CSV>`。`--help` で全部出る。

| 終了コード | 意味 | 次の手 |
|---|---|---|
| 0 | 正常 | — |
| 1 | `verify-csv` で CSV と不一致 | 一覧の行を確認し、新しい法改正・特例が無いか `references/holidays-law.md` §1 の一次情報で確かめる |
| 2 | 入力の誤り（日付の形・存在しない日付など） | 表示された原因を直す。日付は `YYYY-MM-DD` |
| 3 | 対応範囲（1955〜2099 年）の外 | その年は計算しない。公式の発表を案内する |

通信もファイルの書き込みもしない（`verify-csv` と `--csv` は渡されたファイルを読むだけ）。

## 4. 年末年始・お盆は法定の祝日ではない

- 法律で決まった休日は元日（1月1日）だけ。**12/29〜1/3 の年末年始休みやお盆休みは会社ごとの休み。** 祝日として扱わず、`--extra-closed 12-29..01-03` のように別に渡す。
- 年末年始の休みが入るかで結果が変わる計算（12月下旬の期限・「年内最終営業日」など）は、休みの範囲を確かめるか、含める・含めないの2通りを出す。

## 5. 返す形

```
結果: 2026-11-05（木）
前提: 土日祝を休み。起点の 2026-10-30（金）は数えない。会社の休みなし
効いた休み: 10/31(土)・11/1(日)・11/3(火) 文化の日
注: （2028年以降を含むときだけ）春分・秋分の日は推定。官報で確定するのは前年2月
```

## 6. 評価の罠（間違えやすい点）

- **2026 年**: 9/21（月）敬老の日と 9/23（水）秋分の日に挟まれた **9/22（火）は国民の休日**（法第3条第3項）。5/3（日）が憲法記念日なので **5/6（水）は振替休日**。9月の営業日は 19 日。
- 春分・秋分の日は固定日ではない。**2028 年以降は官報で未公表の推定**（確定は前年2月）。確かめずに断定しない。
- ハッピーマンデーの月曜移動（成人の日・海の日・敬老の日・スポーツの日）と、制定・改称の年（スポーツの日は 2020 年から、それ以前は体育の日。山の日は 2016 年から）。年によって日付が違う。
- 2019 年（4/30 と 5/2 が休日、5/1 は即位の日）、2020・2021 年（東京大会で海の日・スポーツの日・山の日が移動）は特例。
- 「N営業日後」は起点を数えない。起点が休みでも、起点の翌日から数える。
- 銀行の営業日・手形の満期・役所の開庁日は別の規定。このスキルは決めない（`references/business-day-rules.md` §3）。

## 7. 参照

- 祝日のルール・制定改称の年・春分秋分の式と検証・出典: [references/holidays-law.md](references/holidays-law.md)
- 数え方の約束・会社の休み・制度が関わる場面: [references/business-day-rules.md](references/business-day-rules.md)

**確認日は 2026-10-22。確認日から90日を過ぎたら、`references/holidays-law.md` §1 の公式（内閣府・法令）を読み直す。** 2027 年2月に 2028 年分の春分・秋分が官報で公表されたら、`scripts/jbd.py` の `OFFICIAL_EQUINOX_THROUGH` を更新し、`verify-csv` で確かめる。

=== FILE: references/business-day-rules.md ===
# 営業日の数え方の約束事と会社ごとの休み

確認日: 2026-10-22。ここに書くのは計算の約束事（制度ではないので出典は不要なもの）と、制度に関わる注意。

## 1. 数え方の約束（`scripts/jbd.py` の既定）

| 言い方 | 数え方 |
|---|---|
| 「N営業日後」 | 起点の日は数えない。起点の翌日から数えて N 番目の営業日（`add <起点> <N>`）。N が負なら前 |
| 「N営業日以内」「N営業日目まで」 | 起点を含めるかは依頼者の約束による。`add` の結果（起点を含めない）を出し、起点を含めるなら1日早いと添える |
| 「◯日から◯日までの営業日数」 | 両端を含める（`count <開始> <終了>`）。開始を含めない・終了を含めないなら `--exclude-start` / `--exclude-end` |
| 「期限が休みなら翌営業日」（繰り延べ） | `next-business-day <期限>`。営業日ならそのまま |
| 「期限が休みなら前営業日」（繰り上げ） | `next-business-day <期限> --previous` |
| 「月末払い、月末が休みなら翌営業日」 | `month-end <年月>`（繰り上げは `--previous`） |

どちらの約束か分からないときは、既定で計算して「起点を数えない・両端を含める」と一言書く。聞き返してまで止めない。

## 2. 年末年始・お盆などは「会社の休み」

- 法定の祝日は元日（1月1日）だけ。**12/29〜1/3 の年末年始休みは法律で決まった休日ではなく、会社ごとの休み**（就業規則・カレンダー）。お盆休み・創立記念日も同じ。
- `--extra-closed` で渡す。毎年同じなら年なし（`12-29..01-03`。年またぎ可）、その年だけなら年あり（`2026-08-13..2026-08-16`）。カンマで複数。
- 会社の休みが分からないときは、まず「土日祝だけ」で計算し、「年末年始・お盆の会社休みは含めていません」と添える。年末年始をまたぐ計算では、休みの範囲を聞くか、2通り（含める・含めない）を出す。
- 土曜に営業する会社は `--weekend sun`（日曜だけ休み）、曜日が不定なら `--weekend none` にして休みを `--extra-closed` で全部渡す。

## 3. 制度が関わる場面（判定せず、確認先を示す）

- **銀行の営業日・振込日・手形の満期**: 銀行の休日は銀行法施行規則など別の規定で決まり、国民の祝日と一致するとは限らない。このスキルは個別に判定しない。振込日・手形などは金融機関・契約書で確認するよう案内する。
- **契約や法令上の期限**（期間の末日が休日のときの扱い）: 契約書の定めが先。定めが無いときの扱いは法令（民法の期間の規定など）で変わりうる。このスキルは営業日の計算だけを出し、法的な結論は出さない。条文の確認先は e-Gov法令検索 https://laws.e-gov.go.jp/ 。
- **役所の窓口の営業日（行政機関の休日）**: 「行政機関の休日に関する法律」で別に決まり、民間の会社の休みとは一致しない。このスキルでは条文を確認していないので、役所の開庁日を聞かれたら当該機関で確認するよう案内する。

## 4. 出力に必ず付けること

1. 前提: 休みにした曜日、会社の休み（あれば）、祝日の年。
2. 起点・期間の数え方（起点を数えない／両端を含める）。
3. 計算に効いた祝日・休みの名前（例: 11/3 文化の日）。日付と曜日はスクリプトの出力をそのまま書き写す。
4. 2028 年以降は春分・秋分の日が推定であること（官報で確定は前年2月）。

=== FILE: references/holidays-law.md ===
# 日本の祝日のルール（国民の祝日に関する法律）

`scripts/jbd.py` が実装しているルールの根拠と、制定・改称の年。確認日: 2026-10-22。確認日から90日を過ぎたら、下の一次情報を読み直す。

## 1. 出典（一次情報）

| 何 | URL | 確認日 |
|---|---|---|
| 国民の祝日に関する法律（昭和23年法律第178号）の現行条文。最終改正 平成30年法律第57号 | https://www.japaneselawtranslation.go.jp/ja/laws/view/4846/ja （法務省の日本法令外国語訳DB。日本語の現行条文）。条文の正本は e-Gov法令検索 https://laws.e-gov.go.jp/law/323AC1000000178 | 2026-10-22（e-Gov 法令検索はこの日メンテナンス中で取得できず、法務省DBの現行条文で確認） |
| 内閣府「国民の祝日について」（祝日一覧・振替休日・国民の休日・2026/2027 年の祝日・東京大会の特例） | https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html | 2026-10-22 |
| 内閣府の祝日CSV（1955〜2027 年、Shift_JIS） | https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv （Last-Modified 2026-02-02） | 2026-10-22 |
| 国立天文台「春分の日・秋分の日はどのように決まるのか」（前年2月1日の官報の暦要項で決まる。2028〜2050 年の予想表つき） | https://www.nao.ac.jp/faq/a0301.html | 2026-10-22 |
| 内閣府「天皇の即位の日及び即位礼正殿の儀の行われる日を休日とする法律案の概要」（平成30年法律第99号。2019-05-01・2019-10-22 を「国民の祝日」として第3条第2項・第3項を適用） | https://www.cao.go.jp/houan/doc/197_2gaiyou.pdf | 2026-10-22 |

## 2. 条文の要点（第2条・第3条）

- 第3条第1項: 「国民の祝日」は休日とする。
- 第3条第2項（振替休日）: 「国民の祝日」が日曜日に当たるときは、その日後においてその日に最も近い「国民の祝日」でない日を休日とする。
- 第3条第3項（国民の休日）: その前日及び翌日が「国民の祝日」である日（「国民の祝日」でない日に限る。）は、休日とする。
- 第2条の日付は §3 の表。春分の日・秋分の日は条文に月日が無く「春分日」「秋分日」（天文学上の日）。建国記念の日は政令で定める日（2月11日。昭和41年政令第376号。内閣府の概要ページ）。

## 3. 各祝日の日付と制定・改称の年（実装と一致）

法改正の施行日は、法務省DBの附則（平成7年法22＝1996-01-01、平成10年法141＝2000-01-01、平成13年法59＝2003-01-01、平成17年法43＝2007-01-01、平成26年法43＝2016-01-01、平成30年法57＝2020-01-01）で確かめた。各改正の中身（どの祝日がどう変わったか）は、内閣府CSV の名称・日付が年ごとに変わる点（1955〜2027 年の全行）と一致することで確かめた。改正法の逐条は読んでいない。

| 祝日 | 年による違い |
|---|---|
| 元日 | 1月1日 |
| 成人の日 | 〜1999 年は1月15日。2000 年〜は1月の第2月曜日（ハッピーマンデー） |
| 建国記念の日 | 1967 年〜。2月11日 |
| 天皇誕生日 | 〜1988 年は4月29日。1989〜2018 年は12月23日。**2019 年は無し**。2020 年〜は2月23日 |
| 春分の日 | 春分日（§4）。1955 年以前から |
| 昭和の日 | 2007 年〜。4月29日 |
| みどりの日 | 1989〜2006 年は4月29日。2007 年〜は5月4日（それまで5月4日は「国民の休日」だった） |
| 憲法記念日・こどもの日 | 5月3日・5月5日 |
| 海の日 | 1996〜2002 年は7月20日。2003 年〜は7月の第3月曜日。2020 年は7月23日、2021 年は7月22日（東京大会の特例） |
| 山の日 | 2016 年〜。8月11日。2020 年は8月10日、2021 年は8月8日（8月9日が振替休日） |
| 敬老の日 | 1966〜2002 年は9月15日。2003 年〜は9月の第3月曜日 |
| 秋分の日 | 秋分日（§4） |
| 体育の日 → スポーツの日 | 1966〜1999 年は10月10日。2000〜2019 年は10月の第2月曜日（体育の日）。**2020 年〜「スポーツの日」**（2020 年は7月24日、2021 年は7月23日、2022 年〜は10月の第2月曜日） |
| 文化の日・勤労感謝の日 | 11月3日・11月23日 |

1回限りの休日（内閣府の法律案概要の「過去の立法例」と CSV）: 1959-04-10 皇太子明仁親王の結婚の儀 / 1989-02-24 昭和天皇の大喪の礼 / 1990-11-12 即位礼正殿の儀 / 1993-06-09 皇太子徳仁親王の結婚の儀 / 2019-05-01 天皇の即位の日 / 2019-10-22 即位礼正殿の儀。2019 の2日は「国民の祝日」として第3条第2項・第3項が適用され、そのため 2019-04-30 と 2019-05-02 が国民の休日になった。

## 4. 振替休日・国民の休日の年による違い

| ルール | 実装 |
|---|---|
| 振替休日 | 1973-04-12 から（昭和48年法律第10号の公布日）。**〜2006 年は日曜の祝日の翌日（月曜）**。**2007 年〜は「その日後で最も近い祝日でない日」**（5/3 が日曜なら 5/4・5/5 が祝日なので 5/6） |
| 国民の休日 | 1985-12-27 から（昭和60年法律第103号の公布日）。前日・翌日が祝日の祝日でない日。**日曜日に当たる分は記録しない**（内閣府CSV も載せない。日曜は元から休み） |
| 振替休日・国民の休日の名称 | 内閣府CSV は両方とも「休日」。実装は「振替休日」「国民の休日」と区別して出す |
| 土曜の祝日 | 土曜日に当たる祝日に振替は無い（振替休日は日曜の祝日だけ） |

2026 年の例: 5/3（日）憲法記念日 → 5/6（水）が振替休日（5/4・5/5 が祝日）。9/21（月）敬老の日と 9/23（水）秋分の日に挟まれた 9/22（火）が国民の休日（シルバーウィークの仕組み。2009・2015・2026 年。以後は 2037・2043 年が該当する見込みで、どちらも秋分日の推定による）。

## 5. 春分の日・秋分の日

- 条文は「春分日」「秋分日」。国立天文台の計算で、**前年2月1日の官報（暦要項）で公表**されて確定する。公表済みは内閣府CSV の収録する 2027 年まで（確認日時点）。
- それ以降は式による**推定**。`jbd.py` の式: `floor(c + 0.242194*(Y-1980) - floor((Y-1980)/4))`。c は春分 20.8431・秋分 23.2488（1980〜2099 年）、1955〜1979 年は 20.8357・23.2588。式が使えるのは 1900〜2099 年。
- 推定の検証（2026-10-22）: ①1955〜2027 年は CSV と全年一致。②2028〜2050 年は国立天文台の予想表と全年一致。③2051〜2099 年は、独立に実装した天文計算（Meeus『Astronomical Algorithms』第27章の太陽黄経 0°/180° の時刻＋ΔT の近似式。1955〜2099 年を日本時間に直す）と全年一致。ただし日本時間で日付の境目の40分以内に当たる年は、計算の誤差で日付が動きうる: 2041 秋分・2045 秋分・2055 春分・2059 春分・2074 秋分（境目の3分後）・2078 秋分・2088 春分・2092 春分。`jbd.py` はこれらの年の出力に注意を付ける。
- 官報公表前の年は、必ず「推定。官報で確定」と書く。

## 6. 検証のやり方（自分で確かめる）

```
curl -o syukujitsu.csv https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv
python3 scripts/jbd.py verify-csv syukujitsu.csv
```

2026-10-22 の実行結果: 「全年一致: 1955〜2027 年、CSV 1067 行すべてが実装の出力と一致」（終了コード 0）。実装が出す日付と名称が CSV と食い違う行は、一覧にして終了コード 1 を返す。CSV が新しい年（2028 年〜）を含むようになったら、同じコマンドで推定が当たっていたかを確かめ、外れた年があれば `jbd.py` の式の注記を直す。

CSV を計算に使うこともできる（`--csv syukujitsu.csv`。CSV に含まれる年はルールの代わりに CSV の日付を使う。名称は「休日」だけになる）。

## 7. 対応範囲

1955〜2099 年。1955 年より前（法の制定は 1948 年）は CSV が無く突き合わせられないので対応しない。2100 年以降は式の定数が変わる（21.851 / 24.2488）ので対応しない。範囲外は終了コード 3 で、その旨を出す。

=== FILE: scripts/jbd.py ===
#!/usr/bin/env python3
"""日本の祝日（国民の祝日に関する法律）と営業日の計算。Python 3.9 の標準ライブラリだけ。通信もファイル書き込みもしない。

  python3 scripts/jbd.py holidays 2026
  python3 scripts/jbd.py is-holiday 2026-09-22
  python3 scripts/jbd.py add 2026-10-30 3 --extra-closed 12-29..01-03
  python3 scripts/jbd.py count 2026-10-01 2026-10-31
  python3 scripts/jbd.py next-business-day 2026-11-21
  python3 scripts/jbd.py month-end 2026-11 --previous
  python3 scripts/jbd.py verify-csv syukujitsu.csv

対応する年は 1955〜2099。1955〜2027 は内閣府の祝日CSVと全年一致することを確認済み
（verify-csv で自分でも確かめられる）。春分・秋分の日は、官報で公表済みの年（OFFICIAL_EQUINOX_THROUGH まで）以外は
天文計算式による推定で、出力にその旨を付ける。
終了コード: 0 正常 / 1 verify-csv で不一致あり / 2 入力の誤り / 3 対応範囲（1955〜2099）の外
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import unicodedata

MIN_YEAR = 1955
MAX_YEAR = 2099
# 官報（暦要項）で春分日・秋分日が公表済みの最後の年。確認日 2026-10-22（内閣府の祝日CSVが 2027 年まで）。
OFFICIAL_EQUINOX_THROUGH = 2027

WD = "月火水木金土日"  # date.weekday(): 月=0
WEEKEND_NAMES = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

KIND_HOLIDAY = "祝日"
KIND_SUBSTITUTE = "振替休日"
KIND_SANDWICH = "国民の休日"
KIND_SPECIAL = "臨時の休日"

# 官報の公表前の年のうち、独立に計算した春分・秋分の瞬間（日本時間）が日付の境目の40分以内にあり、
# 推定が外れやすい年（検証の方法は references/holidays-law.md §6）。
EQUINOX_NEAR_MIDNIGHT = {2041: "秋分", 2045: "秋分", 2055: "春分", 2059: "春分",
                         2074: "秋分", 2078: "秋分", 2088: "春分", 2092: "春分"}

# 1回限りの休日（特別法）。2019 の 2 日は「国民の祝日」とみなして振替・国民の休日の判定に使う。
SPECIAL_DAYS = {
    dt.date(1959, 4, 10): "結婚の儀",
    dt.date(1989, 2, 24): "大喪の礼",
    dt.date(1990, 11, 12): "即位礼正殿の儀",
    dt.date(1993, 6, 9): "結婚の儀",
    dt.date(2019, 5, 1): "天皇の即位の日",
    dt.date(2019, 10, 22): "即位礼正殿の儀",
}


class UserError(Exception):
    def __init__(self, msg, code=2):
        super().__init__(msg)
        self.code = code


# ---------------------------------------------------------------- 祝日の計算

def nth_monday(year, month, n):
    first = dt.date(year, month, 1)
    return first + dt.timedelta(days=(7 - first.weekday()) % 7 + 7 * (n - 1))


def equinox_days(year):
    """(春分日の3月の日, 秋分日の9月の日)。天文計算式の近似。1900〜2099 で使える式（ここでは 1955〜2099）。

    式: floor(c + 0.242194*(Y-1980) - floor((Y-1980)/4))
    c は 1900〜1979 が 20.8357 / 23.2588、1980〜2099 が 20.8431 / 23.2488。
    """
    if year < 1980:
        cs, ca = 20.8357, 23.2588
    else:
        cs, ca = 20.8431, 23.2488
    k = (year - 1980) // 4  # Python の // は負の数でも切り下げ
    spring = int(cs + 0.242194 * (year - 1980) - k)
    autumn = int(ca + 0.242194 * (year - 1980) - k)
    return spring, autumn


def base_holidays(year):
    """祝日（第2条）と特別法の休日。{date: name}。制定・改称の年は references/holidays-law.md。"""
    h = {}

    def put(m, d, name):
        h[dt.date(year, m, d)] = name

    put(1, 1, "元日")
    if year <= 1999:
        put(1, 15, "成人の日")
    else:
        h[nth_monday(year, 1, 2)] = "成人の日"
    if year >= 1967:
        put(2, 11, "建国記念の日")
    if year <= 1988:
        put(4, 29, "天皇誕生日")
    elif year <= 2006:
        put(4, 29, "みどりの日")
    else:
        put(4, 29, "昭和の日")
    if year >= 1989 and year <= 2018:
        put(12, 23, "天皇誕生日")
    if year >= 2020:
        put(2, 23, "天皇誕生日")
    sp, au = equinox_days(year)
    put(3, sp, "春分の日")
    put(9, au, "秋分の日")
    put(5, 3, "憲法記念日")
    if year >= 2007:
        put(5, 4, "みどりの日")
    put(5, 5, "こどもの日")
    # 海の日
    if year == 2020:
        put(7, 23, "海の日")
    elif year == 2021:
        put(7, 22, "海の日")
    elif year >= 2003:
        h[nth_monday(year, 7, 3)] = "海の日"
    elif year >= 1996:
        put(7, 20, "海の日")
    # 山の日
    if year == 2020:
        put(8, 10, "山の日")
    elif year == 2021:
        put(8, 8, "山の日")
    elif year >= 2016:
        put(8, 11, "山の日")
    # 敬老の日
    if year >= 2003:
        h[nth_monday(year, 9, 3)] = "敬老の日"
    elif year >= 1966:
        put(9, 15, "敬老の日")
    # 体育の日 → スポーツの日（2020 から）
    if year == 2020:
        put(7, 24, "スポーツの日")
    elif year == 2021:
        put(7, 23, "スポーツの日")
    elif year >= 2022:
        h[nth_monday(year, 10, 2)] = "スポーツの日"
    elif year >= 2000:
        h[nth_monday(year, 10, 2)] = "体育の日"
    elif year >= 1966:
        put(10, 10, "体育の日")
    put(11, 3, "文化の日")
    put(11, 23, "勤労感謝の日")
    for d, name in SPECIAL_DAYS.items():
        if d.year == year:
            h[d] = name
    return h


_cache = {}


def year_holidays(year):
    """その年の休日すべて。{date: (名称, 種別)}。振替休日と国民の休日を含む。"""
    if year in _cache:
        return _cache[year]
    if not (MIN_YEAR <= year <= MAX_YEAR):
        raise UserError("対応範囲は %d〜%d 年です（%d 年は対象外）" % (MIN_YEAR, MAX_YEAR, year), 3)
    # 年末年始の境目（前年12/31・翌年1/1 など）は、前後の年の祝日も参照する
    base = {}
    for y in (year - 1, year, year + 1):
        if MIN_YEAR <= y <= MAX_YEAR:
            base.update(base_holidays(y))
    result = {}
    for d, name in base.items():
        if d.year == year:
            result[d] = (name, KIND_SPECIAL if d in SPECIAL_DAYS else KIND_HOLIDAY)

    # 振替休日（第3条第2項）。1973-04-12 施行。2006 までは翌日、2007 からは「その日後で最も近い祝日でない日」
    for d, name in sorted(base.items()):
        if d.weekday() != 6 or d < dt.date(1973, 4, 12):
            continue
        sub = d + dt.timedelta(days=1)
        if d.year >= 2007:
            while sub in base:
                sub += dt.timedelta(days=1)
        if sub.year == year and sub not in base:
            result[sub] = ("休日", KIND_SUBSTITUTE)
    # 国民の休日（第3条第3項）。1985-12-27 施行。前日と翌日が祝日の祝日でない日。日曜日は記録しない（内閣府CSVも載せない）
    for d in list(base):
        mid = d + dt.timedelta(days=1)
        if (mid.year == year and mid not in base and (mid + dt.timedelta(days=1)) in base
                and mid >= dt.date(1985, 12, 27) and mid.weekday() != 6 and mid not in result):
            result[mid] = ("休日", KIND_SANDWICH)
    _cache[year] = result
    return result


def equinox_note(year):
    if year > OFFICIAL_EQUINOX_THROUGH:
        msg = ("%d 年の春分の日・秋分の日は官報で未公表のため計算式による推定です"
               "（前年2月の官報で確定。内閣府・国立天文台で確認）" % year)
        if year in EQUINOX_NEAR_MIDNIGHT:
            msg += "。特に%sは日付の境目に近く、外れやすい年です" % EQUINOX_NEAR_MIDNIGHT[year]
        return msg
    return None


# ---------------------------------------------------------------- 入力の解釈

def norm(s):
    return unicodedata.normalize("NFKC", str(s)).strip()


def today_jst():
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    return now.date()


def parse_date(s, what="日付"):
    t = norm(s)
    if t in ("today", "今日"):
        return today_jst()
    m = (re.match(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", t)
         or re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日?$", t)
         or re.match(r"^(\d{4})(\d{2})(\d{2})$", t))
    if not m:
        raise UserError("%sを読めません: %r（YYYY-MM-DD の形で。例: 2026-10-30）" % (what, s))
    try:
        return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        raise UserError("存在しない日付です: %s" % s)


def parse_month(s):
    t = norm(s)
    m = re.match(r"^(\d{4})[-/.](\d{1,2})$", t) or re.match(r"^(\d{4})年(\d{1,2})月$", t)
    if not m or not (1 <= int(m.group(2)) <= 12):
        raise UserError("年月を読めません: %r（YYYY-MM の形で。例: 2026-11）" % s)
    return int(m.group(1)), int(m.group(2))


def parse_year(s):
    t = norm(s)
    if not re.match(r"^\d{4}$", t):
        raise UserError("年を読めません: %r（西暦4桁。例: 2026）" % s)
    return int(t)


class ExtraClosed:
    """会社の休業日。'MM-DD..MM-DD'（毎年。年またぎ可）、'YYYY-MM-DD..YYYY-MM-DD'、単日 'MM-DD' / 'YYYY-MM-DD'。"""

    def __init__(self, specs):
        self.rules = []
        for spec in specs:
            for part in re.split(r"[,、]", norm(spec)):
                part = part.strip()
                if part:
                    self.rules.append(self._parse(part))

    @staticmethod
    def _one(tok, orig):
        tok = tok.replace("/", "-")
        m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", tok)
        if m:
            try:
                return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass
            raise UserError("休業日の指定を読めません: %r" % orig)
        m = re.match(r"^(\d{1,2})-(\d{1,2})$", tok)
        if m:
            mo, da = int(m.group(1)), int(m.group(2))
            if 1 <= mo <= 12 and 1 <= da <= 31:
                return (None, mo, da)
        raise UserError("休業日の指定を読めません: %r（例: 12-29..01-03 / 2026-08-13..2026-08-16 / 08-13）" % orig)

    def _parse(self, part):
        if ".." in part:
            a, b = part.split("..", 1)
        else:
            a = b = part
        sa, sb = self._one(a.strip(), part), self._one(b.strip(), part)
        if (sa[0] is None) != (sb[0] is None):
            raise UserError("休業日の指定で、年あり（YYYY-MM-DD）と年なし（MM-DD）を混ぜられません: %r" % part)
        if sa[0] is not None:
            try:
                s, e = dt.date(*sa), dt.date(*sb)
            except ValueError:
                raise UserError("存在しない日付が含まれます: %r" % part)
            if e < s:
                raise UserError("休業日の指定の終わりが始まりより前です: %r" % part)
            return ("abs", s, e)
        return ("yearly", (sa[1], sa[2]), (sb[1], sb[2]))

    def contains(self, d):
        for r in self.rules:
            if r[0] == "abs":
                if r[1] <= d <= r[2]:
                    return True
                continue
            (m1, d1), (m2, d2) = r[1], r[2]
            for sy in (d.year - 1, d.year):
                try:
                    s = dt.date(sy, m1, d1)
                    e = dt.date(sy if (m2, d2) >= (m1, d1) else sy + 1, m2, d2)
                except ValueError:
                    continue
                if s <= d <= e:
                    return True
        return False


def parse_weekend(s):
    t = norm(s).lower()
    if t in ("none", "なし", ""):
        return set()
    days = set()
    for p in re.split(r"[,、]", t):
        p = p.strip()
        if p in WEEKEND_NAMES:
            days.add(WEEKEND_NAMES[p])
        elif p in list(WD):
            days.add(WD.index(p))
        else:
            raise UserError("--weekend を読めません: %r（例: sat,sun / sun / none）" % s)
    return days


class Calendar:
    def __init__(self, weekend, extra, csv_holidays=None):
        self.weekend = weekend
        self.extra = extra
        self.csv = csv_holidays  # {year: {date: name}}。内閣府CSV。ある年はルールより優先

    def holiday(self, d):
        """(名称, 種別) か None。"""
        if self.csv is not None and d.year in self.csv:
            name = self.csv[d.year].get(d)
            return (name, "祝日（CSV）") if name else None
        return year_holidays(d.year).get(d)

    def why_closed(self, d):
        """休みの理由のリスト。空なら営業日。"""
        out = []
        if d.weekday() in self.weekend:
            out.append("%s曜日" % WD[d.weekday()])
        h = self.holiday(d)
        if h:
            out.append("%s（%s）" % (h[0], h[1]) if h[1] not in ("祝日", "祝日（CSV）") else h[0])
        if self.extra.contains(d):
            out.append("会社の休業日（--extra-closed）")
        return out

    def is_business(self, d):
        return not self.why_closed(d)

    def step(self, d, direction):
        n = d + dt.timedelta(days=direction)
        if not (dt.date(MIN_YEAR, 1, 1) <= n <= dt.date(MAX_YEAR, 12, 31)):
            raise UserError("対応範囲（%d〜%d 年）を出ました" % (MIN_YEAR, MAX_YEAR), 3)
        return n


# ---------------------------------------------------------------- 表示

def fmt(d):
    return "%04d-%02d-%02d（%s）" % (d.year, d.month, d.day, WD[d.weekday()])


def notes_for(years):
    out = []
    for y in sorted(set(years)):
        n = equinox_note(y)
        if n:
            out.append(n)
    return out


def emit(args, payload, lines, years):
    notes = notes_for(years)
    if args.json:
        payload = dict(payload)
        payload["notes"] = notes
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for ln in lines:
            print(ln)
        for n in notes:
            print("注: " + n)


# ---------------------------------------------------------------- コマンド

def holiday_label(h):
    """('休日', '国民の休日') → '休日［国民の休日］'。ふつうの祝日は名称だけ。"""
    return h[0] if h[1] in ("祝日", "祝日（CSV）") else "%s［%s］" % h

def cmd_holidays(args, cal):
    y = parse_year(args.year)
    hs = year_holidays(y)
    if cal.csv is not None and y in cal.csv:
        hs = {d: (n, "祝日（CSV）") for d, n in cal.csv[y].items()}
    items = sorted(hs.items())
    lines = ["%d 年の休日（%d 日）" % (y, len(items))]
    for d, (name, kind) in items:
        tag = "" if kind in ("祝日", "祝日（CSV）") else "［%s］" % kind
        lines.append("%s %s%s" % (fmt(d), name, tag))
    emit(args, {"year": y, "count": len(items),
                "holidays": [{"date": d.isoformat(), "weekday": WD[d.weekday()], "name": n, "kind": k}
                             for d, (n, k) in items]}, lines, [y])


def cmd_is_holiday(args, cal):
    d = parse_date(args.date)
    h = cal.holiday(d)
    why = cal.why_closed(d)
    if h:
        label = "祝日・休日です: %s" % (h[0] if h[1] in ("祝日", "祝日（CSV）") else "%s（%s）" % (h[0], h[1]))
    elif why:
        label = "祝日ではありませんが営業日でもありません: " + "、".join(why)
    else:
        label = "祝日ではなく、営業日です"
    emit(args, {"date": d.isoformat(), "weekday": WD[d.weekday()], "is_holiday": bool(h),
                "holiday": ({"name": h[0], "kind": h[1]} if h else None),
                "is_business_day": not why, "closed_reasons": why},
         ["%s %s" % (fmt(d), label)], [d.year])


def cmd_add(args, cal):
    d = parse_date(args.date)
    n = args.n
    direction = 1 if n >= 0 else -1
    cur, left, skipped = d, abs(n), []
    years = [d.year]
    while left > 0:
        cur = cal.step(cur, direction)
        why = cal.why_closed(cur)
        if why:
            skipped.append((cur, "、".join(why)))
        else:
            left -= 1
    years.append(cur.year)
    lines = ["%s の%s営業日%s: %s" % (fmt(d), abs(n), "後" if n >= 0 else "前", fmt(cur))]
    if n == 0 and not cal.is_business(d):
        lines.append("注: 起点自体が営業日ではありません（%s）。繰り延べるなら next-business-day を使います" % "、".join(cal.why_closed(d)))
    lines.append("起点の日は数えません。間にある休み: %s" % (
        "、".join("%s %s" % (s.strftime("%m/%d") + "(" + WD[s.weekday()] + ")", w) for s, w in skipped) if skipped else "なし"))
    lo, hi = sorted((d, cur))
    years = list(range(lo.year, hi.year + 1))
    emit(args, {"start": d.isoformat(), "n": n, "result": cur.isoformat(), "weekday": WD[cur.weekday()],
                "skipped": [{"date": s.isoformat(), "reason": w} for s, w in skipped]}, lines, years)


def cmd_count(args, cal):
    a, b = parse_date(args.start, "開始日"), parse_date(args.end, "終了日")
    if b < a:
        raise UserError("終了日が開始日より前です: %s > %s" % (a, b))
    first = a + dt.timedelta(days=1) if args.exclude_start else a
    last = b - dt.timedelta(days=1) if args.exclude_end else b
    days = []
    cur = first
    while cur <= last:
        days.append(cur)
        cur += dt.timedelta(days=1)
    for x in (first, last):
        if not (dt.date(MIN_YEAR, 1, 1) <= x <= dt.date(MAX_YEAR, 12, 31)):
            raise UserError("対応範囲（%d〜%d 年）を出ました" % (MIN_YEAR, MAX_YEAR), 3)
    closed = [(x, cal.why_closed(x)) for x in days]
    biz = [x for x, w in closed if not w]
    holi = [(x, w) for x, w in closed if w and cal.holiday(x)]
    extra = [(x, w) for x, w in closed if w and cal.extra.contains(x)]
    span = "%s 〜 %s" % (fmt(a), fmt(b))
    if not days:
        span += "（数える日がありません）"
    elif (first, last) != (a, b):
        span += "（数える範囲: %s 〜 %s）" % (fmt(first), fmt(last))
    lines = [span, "営業日: %d 日 / 暦日: %d 日" % (len(biz), len(days))]
    if holi:
        lines.append("期間内の祝日・休日: " + "、".join(
            "%s %s" % (x.strftime("%m/%d") + "(" + WD[x.weekday()] + ")", holiday_label(cal.holiday(x))) for x, _ in holi))
    if extra:
        lines.append("会社の休業日にあたる日: %d 日" % len(extra))
    emit(args, {"start": a.isoformat(), "end": b.isoformat(), "counted_from": first.isoformat(),
                "counted_to": last.isoformat(), "business_days": len(biz), "calendar_days": len(days),
                "holidays_in_range": [{"date": x.isoformat(), "name": cal.holiday(x)[0]} for x, _ in holi]},
         lines, list(range(a.year, b.year + 1)))


def move(cal, d, previous, strict):
    cur = d
    direction = -1 if previous else 1
    if strict:
        cur = cal.step(cur, direction)
    while not cal.is_business(cur):
        cur = cal.step(cur, direction)
    return cur


def cmd_next(args, cal):
    d = parse_date(args.date)
    r = move(cal, d, args.previous, args.strict)
    word = "前営業日" if args.previous else "翌営業日"
    if r == d:
        lines = ["%s は営業日です。そのまま: %s" % (fmt(d), fmt(r))]
    else:
        lines = ["%s → %s %s" % (fmt(d), word, fmt(r))]
        if not args.strict:
            lines.append("起点が休みの理由: " + "、".join(cal.why_closed(d)))
    lo, hi = sorted((d, r))
    emit(args, {"date": d.isoformat(), "result": r.isoformat(), "weekday": WD[r.weekday()],
                "moved": r != d, "direction": "previous" if args.previous else "next"},
         lines, list(range(lo.year, hi.year + 1)))


def cmd_month_end(args, cal):
    y, m = parse_month(args.month)
    nxt = dt.date(y + (m == 12), m % 12 + 1, 1)
    last = nxt - dt.timedelta(days=1)
    r = move(cal, last, args.previous, False)
    word = "前営業日（繰り上げ）" if args.previous else "翌営業日（繰り延べ）"
    if r == last:
        lines = ["%d年%d月の末日 %s は営業日です" % (y, m, fmt(last))]
    else:
        lines = ["%d年%d月の末日 %s は休みです（%s）→ %s %s" % (
            y, m, fmt(last), "、".join(cal.why_closed(last)), word, fmt(r))]
    lo, hi = sorted((last, r))
    emit(args, {"month": "%04d-%02d" % (y, m), "month_end": last.isoformat(), "result": r.isoformat(),
                "weekday": WD[r.weekday()], "moved": r != last}, lines, list(range(lo.year, hi.year + 1)))


# ---------------------------------------------------------------- 内閣府CSV

def read_csv(path):
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        raise UserError("CSV を開けません: %s（%s）。内閣府 https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv を保存して渡します" % (path, e))
    for enc in ("utf-8-sig", "cp932"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UserError("CSV の文字コードを判別できません: %s（UTF-8 か Shift_JIS）" % path)
    out = {}
    n = 0
    for row in csv.reader(text.splitlines()):
        if len(row) < 2:
            continue
        m = re.match(r"^\s*(\d{4})/(\d{1,2})/(\d{1,2})\s*$", row[0])
        if not m:
            continue  # ヘッダー行など
        d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        out.setdefault(d.year, {})[d] = row[1].strip()
        n += 1
    if n == 0:
        raise UserError("CSV から日付の行を読めませんでした: %s（1 列目が YYYY/M/D の形である必要があります）" % path)
    return out


def norm_csv_name(name):
    if name == "体育の日（スポーツの日）":
        return "体育の日"
    if name == "休日（祝日扱い）":
        return "天皇の即位の日・即位礼正殿の儀"
    return name


def cmd_verify(args, cal):
    data = read_csv(args.csv_file)
    years = sorted(data)
    bad = []
    checked = 0
    for y in years:
        if not (MIN_YEAR <= y <= MAX_YEAR):
            continue
        mine = {d: v for d, v in year_holidays(y).items()}
        theirs = {d: norm_csv_name(n) for d, n in data[y].items()}
        for d in sorted(set(mine) | set(theirs)):
            a = mine.get(d)
            b = theirs.get(d)
            if a is None:
                bad.append("%s CSV にあるが実装に無い: %s" % (d, b))
            elif b is None:
                bad.append("%s 実装にあるが CSV に無い: %s" % (d, a[0] if a[1] in ("祝日", KIND_SPECIAL) else a[1]))
            else:
                if a[1] in (KIND_SUBSTITUTE, KIND_SANDWICH):
                    ok = b == "休日"
                elif a[1] == KIND_SPECIAL and d.year == 2019:
                    ok = b == "天皇の即位の日・即位礼正殿の儀"
                else:
                    ok = a[0] == b
                if not ok:
                    bad.append("%s 名称が違う: 実装 %s / CSV %s" % (d, a[0], b))
        checked += len(theirs)
    lo = min(y for y in years if MIN_YEAR <= y <= MAX_YEAR)
    hi = max(y for y in years if MIN_YEAR <= y <= MAX_YEAR)
    if args.json:
        print(json.dumps({"years": [lo, hi], "csv_rows": checked, "mismatches": bad, "ok": not bad}, ensure_ascii=False, indent=2))
    else:
        if bad:
            print("不一致 %d 件（%d〜%d 年）" % (len(bad), lo, hi))
            for b in bad:
                print("  " + b)
        else:
            print("全年一致: %d〜%d 年、CSV %d 行すべてが実装の出力と一致" % (lo, hi, checked))
    return 1 if bad else 0


# ---------------------------------------------------------------- CLI

DESCRIPTION = """日本の祝日と営業日の計算。祝日は国民の祝日に関する法律のルール（ハッピーマンデー・春分秋分・振替休日・国民の休日）から計算する。
対応する年: %d〜%d。土日と祝日を休みにする。会社の休み（年末年始など）は --extra-closed で足す。""" % (MIN_YEAR, MAX_YEAR)

EPILOG = """例:
  jbd.py holidays 2026                          その年の祝日・休日の一覧
  jbd.py is-holiday 2026-09-22                  祝日か、営業日か
  jbd.py add 2026-10-30 3                       3営業日後（起点は数えない。負の数で前）
  jbd.py add 2026-12-25 3 --extra-closed 12-29..01-03    年末年始を休業にして数える
  jbd.py count 2026-10-01 2026-10-31            期間内の営業日数（両端を含む）
  jbd.py next-business-day 2026-11-21           休みなら翌営業日（--previous で前営業日、--strict で起点を含めない）
  jbd.py month-end 2026-11 [--previous]         月末が休みなら翌営業日（支払期限）
  jbd.py verify-csv syukujitsu.csv              内閣府の祝日CSV と全年を突き合わせる
--extra-closed の書式: 12-29..01-03（毎年、年またぎ可）/ 08-13..08-16 / 2026-08-14（その年だけ）/ カンマで複数
終了コード: 0 正常 / 1 verify-csv で不一致 / 2 入力の誤り / 3 対応範囲（%d〜%d 年）の外""" % (MIN_YEAR, MAX_YEAR)


def build_parser():
    p = argparse.ArgumentParser(prog="jbd.py", description=DESCRIPTION, epilog=EPILOG,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--extra-closed", action="append", default=[], metavar="範囲",
                        help="会社の休業日。例: 12-29..01-03（繰り返し・カンマ区切り可）")
    common.add_argument("--weekend", default="sat,sun", metavar="曜日",
                        help="休みにする曜日。既定 sat,sun。例: sun（土曜は営業）/ none")
    common.add_argument("--csv", metavar="ファイル", help="内閣府の祝日CSV。含まれる年はルールより CSV を優先")
    common.add_argument("--json", action="store_true", help="JSON で出力")
    sub = p.add_subparsers(dest="cmd", metavar="<コマンド>")
    sub.required = True
    s = sub.add_parser("holidays", parents=[common], help="年の祝日一覧")
    s.add_argument("year")
    s = sub.add_parser("is-holiday", parents=[common], help="祝日か・営業日か")
    s.add_argument("date")
    s = sub.add_parser("add", parents=[common], help="N営業日後（負の数は前）")
    s.add_argument("date")
    s.add_argument("n", type=int)
    s = sub.add_parser("count", parents=[common], help="期間内の営業日数")
    s.add_argument("start")
    s.add_argument("end")
    s.add_argument("--exclude-start", action="store_true", help="開始日を数えない")
    s.add_argument("--exclude-end", action="store_true", help="終了日を数えない")
    s = sub.add_parser("next-business-day", parents=[common], help="休みなら翌営業日（その日が営業日ならそのまま）")
    s.add_argument("date")
    s.add_argument("--previous", action="store_true", help="前営業日（繰り上げ）にする")
    s.add_argument("--strict", action="store_true", help="起点の日を含めず、必ず次（前）の営業日にする")
    s = sub.add_parser("month-end", parents=[common], help="月末（休みなら翌営業日／前営業日）")
    s.add_argument("month", help="YYYY-MM")
    s.add_argument("--previous", action="store_true", help="前営業日（繰り上げ）にする")
    s = sub.add_parser("verify-csv", parents=[common], help="内閣府の祝日CSV と実装を全年突き合わせる")
    s.add_argument("csv_file")
    return p


def main(argv=None):
    p = build_parser()
    try:
        args = p.parse_args(argv)
    except SystemExit as e:
        if e.code not in (0, None):
            sys.stderr.write("入力の誤りです。python3 scripts/jbd.py --help で使い方を確認してください\n")
            return 2
        return 0
    try:
        extra = ExtraClosed(args.extra_closed)
        cal = Calendar(parse_weekend(args.weekend), extra, read_csv(args.csv) if args.csv else None)
        if args.cmd == "verify-csv":
            return cmd_verify(args, cal)
        {"holidays": cmd_holidays, "is-holiday": cmd_is_holiday, "add": cmd_add, "count": cmd_count,
         "next-business-day": cmd_next, "month-end": cmd_month_end}[args.cmd](args, cal)
        return 0
    except UserError as e:
        sys.stderr.write("エラー: %s\n" % e)
        if e.code == 2:
            sys.stderr.write("次の手: python3 scripts/jbd.py --help で書式を確認する。日付は YYYY-MM-DD\n")
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
