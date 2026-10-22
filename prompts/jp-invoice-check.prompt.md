<!-- jp-invoice-check v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-invoice-check（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-invoice-check
description: >-
  日本のインボイス制度（適格請求書・適格簡易請求書）の記載事項の不足を指摘し、税率ごとの消費税額を検算し、登録番号（T+13桁）の形式と検査桁を確認する。「この請求書の記載がインボイスの要件を満たしているか見て」「税率ごとの消費税を計算して」「登録番号 T1234567890123 は形式として正しい？」「領収書をインボイスにするには何が足りない？」「10%と8%が混在する請求書の消費税額の出し方」と頼まれたときに使う。出力は断定せず「該当要件・不足箇所・直し方」。時限措置（経過措置・少額特例など）は確認日つきで案内し、最新は国税庁で確認する。Keywords: qualified invoice, Japan invoice system, tax registration number, consumption tax calculation, reduced tax rate。仕訳・確定申告書の作成、個別の税務判断の断定、会計ソフトの操作は対象外。
license: MIT
compatibility: "スクリプトは Python 3.9 以上（標準ライブラリのみ、通信なし）。実行できない環境でも、references の式で手計算して進められる。"
metadata:
  version: "1.0.0"
  author: frametech
---

# 日本のインボイス制度チェック

目的: 請求書・領収書がインボイスの要件を満たすかを見て、不足箇所と直し方を示す。税率ごとの消費税額と登録番号の形式も確かめる。
入力: 請求書・領収書の文面（テキストで貼る。画像を読めない環境では書き起こしてもらう）、明細の金額と税率、登録番号。
出力: 「該当要件・状況・直し方」の表と、計算結果。末尾に「要確認」の一覧。税務上の判断は断定せず、根拠（国税庁の資料）を示す。

## 1. 最初に確かめる

素材に無いものだけ、1回にまとめて聞く。

- 立場: 自分が発行する側（売手）か、受け取った側（買手）か。直し方が変わる
- 取引の相手と業種: 小売・飲食・タクシー等の不特定多数向けなら、簡易インボイスを出せる（宛名と、税率か税額のどちらかを省ける）
- 税込か税抜か、10%と8%（軽減税率）が混ざるか
- 取引日。時限措置は取引日で扱いが変わる（§5）

## 2. 記載事項を照合する

`references/requirements.md` の表の①〜⑥を、素材と1つずつ突き合わせる。簡易インボイスの場合は省略できる項目を除く。

- ①発行者の氏名・名称と**登録番号**（T + 13桁） ②取引年月日 ③取引内容と**軽減税率の旨** ④税率ごとの対価の額と**適用税率** ⑤税率ごとの**消費税額等** ⑥宛名
- 一つの書類で足りなくても、関連が明確な複数の書類（請求書と納品書など）全体で満たせばよい
- 素材から読み取れない項目は「記載なし」と決めつけず「読み取れず（要確認）」にする。素材に無い数字・番号・日付は作らない

## 3. 登録番号を確かめる

```
python3 scripts/invoice.py regno T7000012050002
```

- 形式（T + 半角数字13桁）と、法人番号としての検査桁を確かめる。全角・ハイフン・小文字 t は表記ゆれとして指摘する
- 検査桁が合っても登録の証明にはならない。登録の有無・登録日・失効は国税庁の適格請求書発行事業者公表サイト（https://www.invoice-kohyo.nta.go.jp/）での照会を案内する
- 個人事業者の番号は検査桁を判定できない。「形式のみ確認」と書く
- 実行できない環境では `references/calculation.md` §3 の式で手計算する

## 4. 消費税額を検算する

```
python3 scripts/invoice.py tax --basis excl --round floor 8:13861 8:13199 10:4389 10:23769 --stated 8=2164 --stated 10=2815
```

- 明細を `税率:金額` で渡す。`--basis` は明細が税抜か税込か、`--round` は切捨て・切上げ・四捨五入、`--stated` は請求書の記載税額との照合
- ルール: **税率ごとに合計してから、一の請求書につき税率ごとに1回**だけ端数処理する。切上げ・切捨て・四捨五入のどれかは任意。品目ごとに端数処理した合計は記載事項の税額として認められない（`references/calculation.md`）
- 記載税額が合わないときは、別の端数処理なら一致するか、品目ごとの合計と一致するかを添える。方法の違いだけなら不備とは言い切れない
- 実行できない環境では、合計金額に税率（税込なら 10/110・8/108）を掛けて1回だけ端数処理し、「手計算」と明記する

## 5. 時限措置・改正

経過措置（免税事業者等からの仕入れの控除割合）、少額特例、2割・3割特例、登録の経過措置、飲食料品の税率変更案は**変更が続いている**。`references/transitional.md` に確認日つきで書いてある。

- 使う前に、その表の確認日を見る。**確認日から90日を過ぎたら公式を読み直す**。90日以内でも、利用者の判断に使うなら国税庁で最新を確認するよう必ず添える
- 最新は国税庁で確認: インボイス制度特設サイト https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/invoice.htm
- 「この仕入れは控除できるか」「どの特例が有利か」は個別の税務判断。該当しうる措置と確認先を示し、結論は税理士・税務署に委ねる

## 6. 返す形

```
## 結論（1〜2行）
記載事項のうち、②・⑤に不足の可能性があります。

| 該当要件 | 状況 | 直し方 |
|---|---|---|
| ①登録番号 | T7000012050002（形式・検査桁は一致。登録の有無は公表サイトで要確認） | 問題が見つかっていません |
| ⑤税率ごとの消費税額等 | 記載なし | 税率ごとに合計した対価に10%（税込は10/110）を掛け、1回だけ端数処理して記載 |

## 計算
（invoice.py の結果。税率ごとの合計・税額・端数処理の方法）

## 要確認
- 項目: 理由（例: 取引日 — 時限措置の適用時期が変わる）
```

表現は「〜の可能性があります」「〜が確認できません」を基本にし、「違法です」「控除できません」と断定しない。根拠は国税庁の資料名で示す。

## 7. 対象外

仕訳・確定申告書・消費税申告書の作成、個別の税務判断の断定、会計ソフトの操作は扱わない。必要なら税理士や税務署（インボイスコールセンター 0120-205-553）を案内する。

=== FILE: references/calculation.md ===
# 消費税額等の計算と登録番号の検査桁

確認日: 2026-10-22。90日を過ぎたら下の出典を読み直す。

出典:
- 国税庁「適格請求書等保存方式の概要」（令和8年5月改訂）P7「税率ごとに区分した消費税額等の端数処理」https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/pdf/0026004-099-02.pdf
- 国税庁タックスアンサー No.6498（積上げ計算・割戻し計算）https://www.nta.go.jp/taxes/shiraberu/taxanswer/shohi/6498.htm
- 国税庁 法人番号公表サイト「チェックデジットの計算」https://www.houjin-bangou.nta.go.jp/documents/checkdigit.pdf

## 1. 請求書に書く消費税額等の端数処理

- 計算は **税率ごとに区分して合計した金額** に対して行う。税抜なら `合計 x 10%`（または `x 8%`）、税込なら `合計 x 10/110`（または `x 8/108`）。
- 1円未満の端数が出るときの処理は **一の適格請求書につき、税率ごとに1回**。
- 方法は「切上げ」「切捨て」「四捨五入」など**事業者が任意に選べる**（国税庁の説明）。
- **認められない**: 明細（品目）ごとに消費税額を計算して端数処理し、その合計を「税率ごとの消費税額等」として記載すること。
- 税込金額を作るために品目ごとの消費税額を計算し端数処理するのは値決めの参考で任意。ただし、それを税率ごとに合計して記載事項の消費税額等にはできない。品目ごとの消費税額を参考として書き添えること自体は差し支えない。

### 国税庁パンフレットの数値例（検算済み）

税抜の明細（トマト13,861 / ピーマン13,199 が8%、花4,389 / 肥料23,769 が10%）:

| 区分 | 税率ごとの合計 | 消費税額等（税率ごとに1回・切捨て） | 品目ごとに切り捨てて合計（認められない） |
|---|---|---|---|
| 8% | 27,060円 | 27,060 x 8% = 2,164.8 → **2,164円** | 1,108 + 1,055 = 2,163円 |
| 10% | 28,158円 | 28,158 x 10% = 2,815.8 → **2,815円** | 438 + 2,376 = 2,814円 |

請求金額（税込）= 27,060 + 28,158 + 2,164 + 2,815 = 60,197円。
税込の明細（8%: 14,969 + 14,254 = 29,223 / 10%: 4,827 + 26,145 = 30,972）なら、29,223 x 8/108 = 2,164.8 → 2,164円、30,972 x 10/110 = 2,815.2 → 2,815円（切捨て）、請求金額 60,195円。

`python3 scripts/invoice.py tax --basis excl --round floor 8:13861 8:13199 10:4389 10:23769` で再現できる。

## 2. 積上げ計算と割戻し計算（売上税額・仕入税額の計算方法）

申告時の売上税額と仕入税額の計算は次のどちらかを選べる（No.6498）。ただし、**売上税額を積上げ計算にしたら、仕入税額も積上げ計算**にしなければならない。

- 積上げ計算: 適格請求書に記載のある消費税額等を積み上げる
- 割戻し計算: 適用税率ごとの取引総額を割り戻して計算する

詳細は国税庁インボイスQ&A 問118〜問130。本スキルは申告書の作成は扱わない。

## 3. 登録番号の検査桁（法人番号の場合）

- 登録番号 = `T` + 13桁。法人は `T` + 法人番号。
- 法人番号は、12桁の基礎番号の前に1桁の検査用数字（チェックデジット）を付けた13桁（先頭が検査用数字）。
- 検査用数字の計算（国税庁・法人番号公表サイトの例示）:
  1. 基礎番号12桁を最下位から数え、奇数桁（1・3・5…桁目）の和を A、偶数桁（2・4・6…桁目）の和を B とする
  2. `A + B x 2` を 9 で割った余りを r とする
  3. 検査用数字 = `9 - r`
- 例（国税庁の例示）: 基礎番号 700110005901 → A = 1+9+0+0+1+0 = 11、B = 0+5+0+1+0+7 = 13 → 11 + 26 = 37 → 37 ÷ 9 の余り 1 → 9 - 1 = **8** → 法人番号 8700110005901。
- 例（国税庁の法人番号 7000012050002）: 基礎番号 000012050002 → A = 9、B = 1 → 11 → 余り 2 → 検査用数字 **7**。一致。
- 個人事業者等の `T` + 13桁は法人番号ではない。検査桁の公開仕様は確認できていないので、形式（T + 半角数字13桁）だけ確認し、「検査桁は判定できない」と伝える。
- 検査桁が合っても、その番号が登録されているかは別問題。公表サイト https://www.invoice-kohyo.nta.go.jp/ で照会する。

`python3 scripts/invoice.py regno T7000012050002` で確認できる。

=== FILE: references/requirements.md ===
# 記載事項と書類の種類（国税庁の一次情報）

確認日: 2026-10-22（国税庁サイトを直接読んで確認。法令等の基準日はタックスアンサー上で「令和8年4月1日現在」）。90日を過ぎたら下の出典を読み直す。

出典:
- 国税庁「インボイス制度について」https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/invoice_about.htm
- 国税庁タックスアンサー No.6625「適格請求書等の記載事項」https://www.nta.go.jp/taxes/shiraberu/taxanswer/shohi/6625.htm （根拠法令: 消費税法30条・57条の4、消費税法施行令49・50・70条の9〜70条の11 ほか。条文の本文は未確認）
- 国税庁「適格請求書等保存方式の概要」（令和8年5月改訂）https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/pdf/0026004-099-02.pdf
- 国税庁インボイスQ&A 問24（簡易インボイスを交付できる事業）https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/pdf/qa/24.pdf

## 1. 適格請求書（インボイス）の記載事項

請求書・納品書・領収書・レシートなど名称は問わない。様式は定められておらず、必要な事項が載っていれば手書きでもよい。

| 番号 | 記載事項 | 見るポイント |
|---|---|---|
| ① | 適格請求書発行事業者の氏名または名称**および登録番号** | 登録番号は `T` + 13桁。売手のもの |
| ② | 取引年月日 | まとめて記載する場合は課税期間内の一定期間でもよい |
| ③ | 取引内容（**軽減税率の対象品目である旨**） | 8%対象に `※` `☆` 等の印を付け、凡例を書く。税率ごとに区分する、税率ごとに請求書を分ける方法も可 |
| ④ | 税率ごとに区分して合計した対価の額（税抜きまたは税込み）および**適用税率** | 10%対象・8%対象を別々に合計する |
| ⑤ | 税率ごとに区分した**消費税額等** | 端数処理は税率ごとに1回（`calculation.md`） |
| ⑥ | 書類の交付を受ける事業者の氏名または名称 | 宛名。簡易インボイスでは省略できる |

- 国税庁の説明では、特に注意する項目は登録番号・軽減税率の対象である旨・税率ごとの対価と税額。
- 一の書類だけで全部を満たす必要はない。請求書と納品書など、相互の関連が明確な複数の書類全体で満たしていればよい（概要 P6）。
- 取引先コード表を相手方と共有し、そこから登録番号が確認できる場合は、取引先コードの記載で①の氏名・登録番号の記載があるものとして扱われる（概要 P6）。
- 電磁的記録（電子データ）での提供も可。記録事項は書面と同じ。
- 契約書と通帳（または銀行の振込金受取書）を合わせて満たす例も示されている（家賃など、取引ごとに請求書を出さない取引）。

## 2. 適格簡易請求書（簡易インボイス）

不特定かつ多数の者に対する取引で、**次の事業**のとき、適格請求書に代えて交付できる（Q&A 問24）。

- ①小売業 ②飲食店業 ③写真業 ④旅行業 ⑤タクシー業（①〜⑤は「不特定かつ多数」の限定なし）
- ⑥駐車場業（不特定かつ多数の者に対するものに限る）
- ⑦これらに準ずる事業で不特定かつ多数の者に資産の譲渡等を行う事業（個々の事業の性質で判断）

**省略できるもの**（概要 P4、インボイス制度について）:

| 適格請求書の項目 | 簡易インボイスでは |
|---|---|
| ⑥ 交付を受ける事業者の氏名または名称（宛名） | 省略できる |
| ④ 適用税率 と ⑤ 消費税額等 | **どちらか一方の記載でよい**（両方書いてもよい） |

- 受け取ったインボイスに宛名がなくても、不備ではなく簡易インボイスの場合がある。
- 「簡易インボイス対象である旨」の記載は法令上の記載事項ではない（誤解を避けるために余白へ書くのは一案、と国税庁が説明している）。
- 登録番号・取引年月日・取引内容（軽減税率の旨）・税率ごとの対価の額は、簡易でも必要。

## 3. 領収書をインボイスにするには

領収書もインボイスになりうる。足りないことが多い項目:

1. 登録番号がない、または自社（発行者）のものではない
2. 税率ごとに区分した対価の額・適用税率・消費税額等がない（「消費税込み」とだけ書いてある、内訳がない）
3. 軽減税率対象の印と凡例がない（飲食料品などが混ざる場合）
4. 宛名（上様・空欄）: 簡易インボイスを出せる事業（小売・飲食等）以外では宛名が必要
5. 但し書きだけで取引内容が分からない（「お品代」だけ等）

## 4. 買手が作る書類（仕入明細書等）

買手が作成する仕入明細書でも、売手の確認を受けたもので、次を満たせば仕入税額控除の請求書等になる（概要 P5）。

①作成者の氏名または名称 ②課税仕入れの相手方の氏名または名称**および登録番号** ③課税仕入れの年月日 ④課税仕入れの内容（軽減税率の対象品目である旨） ⑤税率ごとに区分して合計した支払対価の額および適用税率 ⑥税率ごとに区分した消費税額等。登録番号は**売手のもの**になる点に注意。

## 5. 適格返還請求書（値引き・返品）

売上げに係る対価の返還等（値引き・返品・販売奨励金等）を行うとき、返還等の税込価額が1万円未満なら交付義務は免除される（概要の適格返還請求書の節）。記載事項は、発行者の氏名・登録番号、返還等の年月日、元の取引の年月日、返還等の取引内容、税率ごとに区分して合計した返還等の金額、返還等の金額に係る消費税額等または適用税率（細部は原文で確認）。

## 6. 交付義務の免除

次の取引は適格請求書の交付義務が免除される（概要 P11）。

1. 公共交通機関である船舶・バス・鉄道による旅客の運送（3万円未満）
2. 出荷者等が卸売市場で行う生鮮食料品等の譲渡（受託者が卸売の業務として行うもの）
3. 生産者が農協・漁協・森林組合等に委託して行う農林水産物の譲渡（無条件委託方式かつ共同計算方式）
4. 自動販売機・自動サービス機による課税資産の譲渡等（3万円未満）
5. 郵便切手を対価とする郵便サービス（ポスト投函に限る）

## 7. 登録番号の構成

- 法人番号を持つ課税事業者: `T` + 法人番号（13桁）
- それ以外の課税事業者（個人事業者等）: `T` + 13桁の数字
- 出典: タックスアンサー No.6498 の注（https://www.nta.go.jp/taxes/shiraberu/taxanswer/shohi/6498.htm 、2026-10-22 確認）
- 登録の有無・登録日・失効日は国税庁「適格請求書発行事業者公表サイト」https://www.invoice-kohyo.nta.go.jp/ で確認する。形式と検査桁が合っていても、登録されている証明にはならない。
- 検査桁の式は `calculation.md` §3。個人事業者の番号の検査桁について、国税庁の公開仕様は確認できていない（形式のみ確認する）。

=== FILE: references/transitional.md ===
# 時限措置・経過措置・改正（変わり続ける事項）

確認日: 2026-10-22。**ここに書いたのは確認日時点で国税庁のページから確認できた範囲だけ。** 時限措置は改正が続いている。確認日から90日を過ぎる前でも、利用者の判断に使う前に必ず次の公式ページで最新を確認するよう伝える。

公式の入口:
- インボイス制度特設サイト https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/invoice.htm
- 令和8年度税制改正特集 https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/invoice-review/index.htm
- 消費税率引下げ特設サイト https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/zeiritsuhikisage.htm
- 消費税軽減税率・インボイスコールセンター 0120-205-553（平日9:00〜17:00。リーフレットの記載）

個別の税務判断（この取引で控除できるか、どの特例が有利か）は断定しない。該当しうる措置と確認先を示すところまでにする。

## 1. 免税事業者等からの課税仕入れの経過措置（80%控除 → 7・5・3割控除）

出典: 令和8年度税制改正リーフレット https://www.nta.go.jp/taxes/shiraberu/zeimokubetsu/shohi/keigenzeiritsu/invoice-review/pdf/0026004-099-01-2.pdf と上記特集ページ、タックスアンサー No.6498（2026-10-22 確認）。

インボイス発行事業者以外の者（免税事業者・消費者等）からの課税仕入れについて、仕入税額相当額の一定割合を控除できる措置。令和8年度改正で適用期限が2年延長され、控除割合が見直された。

| 課税仕入れの時期 | 控除できる割合（改正後） |
|---|---|
| 令和5年10月1日〜令和8年9月30日 | 80% |
| 令和8年10月1日〜令和10年9月30日 | 70% |
| 令和10年10月1日〜令和12年9月30日 | 50% |
| 令和12年10月1日〜令和13年9月30日 | 30% |
| 令和13年10月1日以後 | 控除不可 |

- 改正前は 80%（〜令和8年9月30日）→ 50%（令和8年10月1日〜令和11年9月30日）→ 0%。
- **上限**: 一のインボイス発行事業者以外の者からの課税仕入れの税込合計が、その年または事業年度で **1億円（改正前: 10億円）** を超えた部分は、この措置を適用できない。令和8年10月1日以後に開始する課税期間から。
- 適用には、区分記載請求書等と同様の事項が記載された請求書等の保存と、この措置の適用を受ける課税仕入れである旨を記載した帳簿の保存が必要（リーフレットの記載）。
- 時期は**課税仕入れの時期**で判定する。年度や課税期間の途中で割合が変わるので、請求書の日付ごとに当てはめる。

## 2. 少額特例（1万円未満の課税仕入れ）

出典: 適格請求書等保存方式の概要（令和8年5月改訂）P13。2026-10-22 確認。

- 対象: 基準期間の課税売上高が1億円以下、または特定期間（原則、個人は前年1月1日〜6月30日、法人は前事業年度開始の日以後6か月）の課税売上高が5,000万円以下の事業者
- 期間: 令和5年10月1日〜令和11年9月30日の課税仕入れ。令和11年10月1日以後は、課税期間の途中でも適用なし
- 内容: 税込1万円未満の課税仕入れは、帳簿のみの保存で仕入税額控除が認められる（インボイスの保存は不要）
- 判定単位: 商品1つごとではなく、**一回の取引**の課税仕入れ額（税込）が1万円未満かどうか
- 帳簿に「課税仕入れの相手方の住所又は所在地」や「特例の対象となる旨」を記載する必要はない
- 令和8年度税制改正特集の一覧では、少額特例の適用期限は「令和11年9月30日の属する課税期間中」と示されている

## 3. 2割特例・3割特例

出典: タックスアンサー No.6498、令和8年度税制改正特集（2026-10-22 確認）。

- 2割特例: インボイス発行事業者の登録を機に免税事業者から課税事業者になった事業者が、令和5年10月1日〜令和8年9月30日の日の属する課税期間で、納付税額を売上税額の2割にできる
- 3割特例（令和8年度改正で創設）: 登録を機に免税事業者から課税事業者になった**個人事業者**の令和9年分・令和10年分の申告で、納付税額を売上税額の3割にできる。法人は不可。主な要件は、個人事業者であること・基準期間（2年前）の課税売上高が1,000万円以下・インボイス発行事業者であること、など。適用できない場合の細目はインボイスQ&A 問115-2
- 2割特例・3割特例を使う場合、納付税額の計算ではインボイスの入手・保存は要らない（所得税等の観点では書類の保存は必要）
- 適用の可否・有利不利は個別事情による。この点の判断は断定せず、特集ページのフローチャートを案内する

## 4. 登録に関する経過措置

出典: No.6498 注1（2026-10-22 確認）。令和5年10月1日〜令和11年9月30日の日を含む課税期間中に免税事業者が登録を受けた場合、登録を受けた日から適格請求書発行事業者になれる。

## 5. 税率の変更予定（飲食料品）

出典: 消費税率引下げ特設サイト、リーフレット「飲食料品に係る2年間の消費税率引下げについて」（令和8年9月）、Q&A（令和8年9月）。2026-10-22 確認。

- 内容: 令和9年4月1日〜令和11年3月31日の2年間、飲食料品（現在の軽減税率8%の対象と同じ範囲）の消費税率（地方消費税を含む）を**1%**に引き下げる、というもの
- **状態**: 「飲食料品消費税率の臨時的な引下げ及び就業者負担軽減支援金の導入に関する大綱」（令和8年9月15日閣議決定）で示された改正案の内容。国税庁のページは「法案が国会に提出され、審議を経た上で可決・成立した場合のもの」と明記している。**確認日時点で成立したかは確認できていない**
- 請求書への影響（Q&A 問2-1・問2-2）: 1%対象と8%対象（令和9年3月以前の取引）が同じ請求書に混ざるときは、請求書を分けるか、同一請求書内で区分して記載する例が示されている
- 計算スクリプトの税率は引数で渡せるので、1% も `1:金額` で計算できる。ただし適用の可否は法の成立状況を公式で確認してから

## 6. 確認できていない事項

- 消費税法・同施行令の条文本文（e-Gov 法令検索）は、取得できなかったため直接は読んでいない。条文番号はタックスアンサーの「根拠法令等」の記載による
- 簡易課税のみなし仕入率の適用判断、2割・3割特例の有利不利、課税期間の短縮など、個別の税務判断

=== FILE: scripts/invoice.py ===
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
