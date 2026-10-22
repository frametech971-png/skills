<!-- jp-zengin-format v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-zengin-format（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-zengin-format
description: >-
  全銀フォーマット（全国銀行協会の規定形式・固定長120バイトの総合振込／給与振込／賞与振込データ）を作る・検証する。「振込データを全銀フォーマットで作って」「このファイルの桁数が合っているか検証して」「半角カナに変換して（濁点・小文字）」「トレーラの合計が合わない」「給与振込のファイルを作りたい」と頼まれたときに使う。ヘッダー・データ・トレーラ・エンドの4種のレコード、桁数と属性、使える文字、振込指定日、新規コード等を全銀協の公開資料（確認日つき）に沿って扱い、CSV から生成する generate と、桁・文字・件数・金額を調べる validate のスクリプトを同梱。銀行ごとの差は断定せず取引銀行の仕様書で確認する。Keywords: zengin format, 全銀協, 総合振込, 給与振込, fixed-length 120 byte, halfwidth katakana, Shift_JIS。銀行への送信、口座の実在確認、EBCDIC、税務・会計の判断、請求書や口座振替は対象外。
license: MIT
compatibility: "Python 3.9 以上（標準ライブラリだけ）。通信しない。Shift_JIS 系（cp932）のみ。EBCDIC は対象外。実行できない環境では references のレイアウト表で手作業の手順を示す"
metadata:
  version: "1.0.0"
  author: frametech
---

# 全銀フォーマット（総合振込・給与振込・賞与振込）の作成と検証

目的: 全銀協規定形式（120バイト固定長）の振込データを、仕様どおりに作る・検証する。
入力: 振込先の一覧（CSV か貼り付け）と依頼人の情報（依頼人コード・名義・振込指定日 MMDD・取引銀行・支店）、または検証したいファイル。**口座番号などの個人情報は書き写して残さない。サンプルは架空の値を使う。**
出力: ファイル（または生成コマンド）と、効いている規則の一言。検証なら「どのレコードの何桁目が何の理由で誤りか → 直し方」。

事実は [references/](references/) にある（確認日 2026-10-23。全銀協の別冊が一次情報）。**確認日から90日を過ぎたら、各ファイル冒頭の出典URLを読み直してから答える。** 仕様の要点: 1ファイル = ヘッダー(1)・データ(2)×N・トレーラ(8)・エンド(9)、各120バイト、数字は右詰め前ゼロ、文字は左詰めスペース。

## 守ること（最初に）

- **銀行への送信・口座の実在確認はしない。** 作ったファイルは、取引銀行の仕様書（改行・固定値・必須項目・営業日）に照らしてから、利用者が銀行のサービスで取り込む。
- **銀行ごとに差がある部分は断定しない**（新規コード・振込指定区分・仕向銀行番号・改行など）。分かる差は references/bank-differences.md。ここに無い銀行は「取引銀行の仕様書で確認」と答える。
- 文字コードは Shift_JIS 系（cp932。半角カナ1バイト）だけ。ヘッダーのコード区分 1（EBCDIC）は対象外と伝える。
- **漢字の読みは決めない。** 「山田花子」は読みを聞いてカナで受ける。長音「ー」・中黒「・」・ヲの扱いは銀行・届出名義で違うので、勝手に確定せず確認を促す。
- 振込金額・合計は円の整数。計算はスクリプトに任せ、暗算で合計を言わない。

## 手順

1. 依頼を分ける: (a) 作る (b) 検証する (c) 名義の変換 (d) トレーラの不一致などの原因調べ (e) 仕様の質問。
2. 種別を決める: 総合振込 `21`、給与振込 `11`、賞与振込 `12`（レイアウトは zengin-spec.md §2・§3）。
3. (a) 作る:
   - 足りない入力（依頼人コード＝銀行が採番した10桁、振込指定日、仕向銀行・支店番号、各振込先の銀行・支店番号・預金種目・口座番号・カナ名義・金額）を聞く。個人名・口座は例示に実在風の値を使わない。
   - CSV を用意し（列は zengin-spec.md §6）、**まず `--dry-run`**。問題がなければ出力する。

   ```bash
   python3 scripts/zengin.py generate --input assets/sample_transfers.csv --client-code 1234 \
     --client-name "テストショウジ株式会社" --abbrev --date 1125 --bank-no 9999 --branch-no 1 --crlf --dry-run
   python3 scripts/zengin.py generate --input assets/sample_transfers.csv --output out.txt --client-code 1234 \
     --client-name "テストショウジ株式会社" --abbrev --date 1125 --bank-no 9999 --branch-no 1 --crlf
   ```

   Excel の CSV は `--input-encoding cp932`。給与は `--type 11`、賞与は `--type 12`（見本 assets/sample_salary.csv）。漢字・使えない文字・不正な桁があると**ファイルを作らず**一覧で止まる。上書きは `--force`。書き出す前に自分の検証も通す。
4. (b) 検証する: `python3 scripts/zengin.py validate <ファイル>`（`--type 21` で種別を固定、`--json` で機械可読）。桁・文字・数字項目・レコード順・種別・日付 MMDD・預金種目・新規コード・トレーラの件数と金額（実数との差まで）を見る。**営業日・口座の実在・銀行固有の規則は検証できない**と必ず添える。
5. (c) 名義の変換: `python3 scripts/zengin.py kana "キャッシュ" "ヴァイオリン"`。小文字→大文字（ｷﾔﾂｼﾕ）、濁点・半濁点は独立した1文字（ｶﾞ は2バイト）、全角英数→半角英大文字、`--abbrev` で株式会社などを法人略語に（先頭 `ｶ)`、末尾 `(ｶ`）、`--middot space|period|drop` で中黒の扱いを指定。
6. (d) 原因調べは troubleshooting.md の表から。トレーラが合わないときは validate の「トレーラ N / 実数 M（差）」を示し、件数にヘッダー等を含めていないか、金額の単位、手で消した行がないかを順に確認させる。
7. (e) 仕様の質問は zengin-spec.md を読んで答える。確認できていない項目（zengin-spec.md §7）は「要確認」と言う。

スクリプトを実行できない環境では、zengin-spec.md のレイアウト表（位置・桁・属性）から1レコードずつ組み立てて示し、利用者の手元で validate してもらう。合計は表計算で足して貼ってもらう。

## 返す形

```
（コマンドまたは生成結果の要約: 種別・件数・合計金額・バイト数・改行の有無）

効いている規則: 120バイト固定長／使える文字／トレーラの件数と金額 など、今回に関係するものだけ
確認が要ること: 取引銀行の仕様書（改行・新規コード・振込指定区分・固定値）、振込指定日が営業日か、口座名義の読み
```

## 同梱物

| ファイル | 内容 |
|---|---|
| scripts/zengin.py | `generate`（CSV→120バイト固定長）、`validate`（既存ファイルの検証）、`kana`（名義の変換）。`--help` `--dry-run`。終了コード 0 正常／1 データに問題あり／2 引数・ファイルの誤り |
| scripts/selftest_zengin.py | 実際に生成・検証して確かめる自己検証（改ざんしたファイルの検出も含む。通信しない） |
| assets/sample_transfers.csv, sample_salary.csv | 架空の値のサンプル |
| references/zengin-spec.md | レコードのレイアウト（位置・桁・属性）、使える文字、名義の書き方、CSV の列、未確認の事項 |
| references/bank-differences.md | 確認できた銀行ごとの差（出典URLつき） |
| references/troubleshooting.md | 症状別の原因と直し方 |

## 限界

銀行の取り込み画面での成功は未検証（全銀協の公開仕様と、検証スクリプトでの突き合わせまで）。統一金融機関番号の一覧は持たない。初めて本番に出すときは、少額・少件数で銀行の検証機能を通してから。

=== FILE: references/bank-differences.md ===
# 銀行ごとの差（確認できた範囲）

確認日: 2026-10-23。**確認日から90日を過ぎたら各行の最新の仕様書を読み直す。** ここに無い銀行・項目は「取引銀行の仕様書で確認」と答える。

出典: 全銀協別冊（https://www.zenginkyo.or.jp/fileadmin/res/abstract/efforts/system/jba_protocol_pc.pdf）、三菱UFJ信託銀行（https://www.tr.mufg.jp/houjin/mbd/manual/pdf/manual05.pdf）、群馬銀行（https://www.gunmabank.co.jp/hojin/biznb/service/pdf/z_format1.pdf）

| 項目 | 全銀協（別冊） | 三菱UFJ信託銀行 | 群馬銀行 |
|---|---|---|---|
| 取組日 | MMDD | MMDD。**金融機関営業日に限る** | MMDD（銀行営業日） |
| 仕向銀行番号 | 統一金融機関番号 | 固定値（0288） | 固定値（0128） |
| 依頼人の預金種目（ヘッダー） | 1/2/9、任意 | 1/2、必須扱い | 1/2/9 |
| 新規コード | 0/1/2 | 0/1/2（必須） | **未使用（0とする）** |
| 手形交換所番号 | 統一手形交換所番号（任意） | 0（全てゼロ） | 未使用（0） |
| 振込区分 | 7 テレ振込 / 8 文書振込 | **7 電信振込のみ** | **7 電信振込のみ** |
| 顧客コード | N(10)×2 | N(10)×2 | C(10)×2（項目名は「顧客番号」） |
| 改行 | （別冊本文では確認できず） | CRLF を付ける場合は120バイトの後ろに2バイト | CRLF を付ける場合は後付けで122バイト |
| 文字コード | JIS / EBCDIC | JIS / EBCDIC | JIS（資料の題が「JISコード」） |

読み方:
- 上の差は、**同じ「全銀フォーマット」でも銀行ごとに必須・固定の値が違う**という例。generate の既定値（新規コード 0、振込指定区分 7、手形交換所番号 0000、改行なし）は多くの銀行で通りやすい側に寄せてあるが、通ると断定しない。
- 取り込み画面でエラーになったら、その銀行の「ファイルフォーマット」ページのエラー表（項目名と行番号を示す銀行が多い）と、validate の結果を突き合わせる。
- この表に無い銀行（ゆうちょ・信用金庫・メガバンクの Biz 系など）の仕様は未確認。公開PDFの本文を読めた範囲だけを書いている。

=== FILE: references/troubleshooting.md ===
# 症状別: 検証が通らない・銀行で弾かれるとき

確認日: 2026-10-23（仕様は zengin-spec.md、出典もそちら）。

| 症状 | 見る場所 | 直し方 |
|---|---|---|
| 「トレーラの合計が合わない」 | validate の「合計件数/合計金額が合いません」。トレーラ 8-19 桁と、データ・レコード 81-90 桁の合計 | トレーラは「データ・レコードの件数」「振込金額の合計」。ヘッダー・トレーラ・エンドを数えていないか、金額を万円・千円単位や手数料込みで足していないか、データ行を手で消していないか確認。直したら validate をやり直す |
| 「レコード長が 119/121 バイト」 | 桁がずれたレコード。全角文字が混ざると1文字で2バイト | 全角を半角カナに変換（`kana` サブコマンド）。名義が項目より長いと切れるか、他の項目を押し出す |
| 「改行なしのファイルで 120 の倍数でない」 | どこかのレコードで桁が欠けている | 先頭から順に validate。最初の不正レコードを直す。CRLF が必要な銀行なら `--crlf` |
| 「使えない文字」 | 小文字カナ ｯｬｭｮ、英小文字、ｰ（長音）、中黒、カンマ・円記号など | 小文字→大文字（キャッシュ→ｷﾔﾂｼﾕ）、英小文字→大文字。長音・中黒は銀行・届出名義を確認して決める（自動では決めない） |
| ヲが弾かれる | 給与・賞与の名義ではヲ不可 | 取引銀行・受取人の登録名義を確認。勝手にオに置換しない |
| 全角の名前・漢字が入力 | `kana` で変換不可 | 漢字の読みは使い手が決めてカナで渡す |
| 口座番号が 7 桁にならない | Excel が先頭のゼロを落とす／ハイフン入り | CSV は文字列（テキスト）で保存。generate は不足桁を左ゼロ埋めして注意を出す |
| EBCDIC のファイル | ヘッダー 4 桁目が 1、または先頭バイトが 0xF1 | 対象外。銀行の変換ツールか仕様書で |
| 振込指定日が不正 | MMDD の月日として不正（1332 など） | 4 桁の月日。営業日かどうかは銀行のカレンダーで（このスキルは検証しない） |
| 銀行のサービスで取込エラー | 銀行固有の必須・固定値 | bank-differences.md と取引銀行の仕様書。エラー表の項目名を validate の field と照らす |

=== FILE: references/zengin-spec.md ===
# 全銀フォーマット（全銀協規定形式）の仕様

確認日: 2026-10-23。**確認日から90日を過ぎたら、下の一次情報を読み直してから答える。**

一次情報（全国銀行協会）:
- 全銀協パーソナル・コンピュータ用標準通信プロトコル（ベーシック手順）別冊「適用業務およびレコード・フォーマット」（令和8年10月版・188ページ） https://www.zenginkyo.or.jp/fileadmin/res/abstract/efforts/system/jba_protocol_pc.pdf
  - 総合振込: 本文34〜35ページ（PDF 38〜39枚目）／給与・賞与振込（民間）: 29〜31ページ／使用文字: 付録1（175ページ）／名義の書き方・法人略語: 付録2（176ページ）／預金種目コード: 付録3（177ページ）

銀行側の公開仕様（差の確認に使った。各行の最新版は各行のサイトで）:
- 三菱UFJ信託銀行「総合振込（全銀協規定形式）」 https://www.tr.mufg.jp/houjin/mbd/manual/pdf/manual05.pdf
- 群馬銀行「全銀協制定ファイルフォーマット【総合振込】」 https://www.gunmabank.co.jp/hojin/biznb/service/pdf/z_format1.pdf

## 1. ファイルの構成

- レコード長は **120バイト固定**。1ファイルは「ヘッダー(1) → データ(2)×N → トレーラ(8) → エンド(9)」。ヘッダーを複数持つファイルもあり、その場合の種別コードは全ヘッダーで同一（別冊 §2）。このスキルの generate は 1 ヘッダーだけ作る。
- 改行（CR LF）を付ける場合は各レコードの後ろに2バイト（120+2=122）。付けるか否かは銀行ごと。**取引銀行の仕様書で確認**。
- 文字コード区分（ヘッダーの4桁目）は 0=JIS / 1=EBCDIC。**このスキルは 0（JIS 8ビット相当 = Shift_JIS 系で半角カナ1バイト）だけ。EBCDIC は対象外。** 実装は cp932 で書き出す。Shift_JIS の半角カナ（0xA1〜0xDF）は JIS 8ビットのカナと同じバイトだが、0x5C が円記号になるかバックスラッシュになるか等の細部は銀行・環境で異なる。名義に円記号は使えないので実害は出にくい。
- 数字項目（N）は右詰めで残りを「0」。文字項目（C）は左詰めで残りをスペース。

## 2. 総合振込（種別コード 21）

位置は1始まりのバイト位置。内容は全銀協別冊 §8 による。

### ヘッダー・レコード（データ区分 1）

| 位置 | 項目 | 桁 | 内容 |
|---|---|---|---|
| 1 | データ区分 | N1 | 1 |
| 2-3 | 種別コード | N2 | 21 |
| 4 | コード区分 | N1 | 0=JIS |
| 5-14 | 振込依頼人コード | N10 | 銀行が採番した委託者コード |
| 15-54 | 振込依頼人名 | C40 | 左詰め |
| 55-58 | 取組日（振込指定日） | N4 | MMDD（銀行によっては金融機関営業日に限る） |
| 59-62 | 仕向銀行番号 | N4 | 統一金融機関番号 |
| 63-77 | 仕向銀行名 | C15 | 任意 |
| 78-80 | 仕向支店番号 | N3 | 統一店番号 |
| 81-95 | 仕向支店名 | C15 | 任意 |
| 96 | 預金種目（依頼人） | N1 | 1普通 2当座 9その他。任意 |
| 97-103 | 口座番号（依頼人） | N7 | 任意 |
| 104-120 | ダミー | C17 | スペース |

### データ・レコード（データ区分 2）

| 位置 | 項目 | 桁 | 内容 |
|---|---|---|---|
| 1 | データ区分 | N1 | 2 |
| 2-5 | 被仕向銀行番号 | N4 | 統一金融機関番号 |
| 6-20 | 被仕向銀行名 | C15 | 任意 |
| 21-23 | 被仕向支店番号 | N3 | 統一店番号 |
| 24-38 | 被仕向支店名 | C15 | 任意 |
| 39-42 | 手形交換所番号 | N4 | 任意。0000 とする銀行が多い |
| 43 | 預金種目 | N1 | 1普通 2当座 4貯蓄 9その他 |
| 44-50 | 口座番号 | N7 | 右詰め・前ゼロ。ハイフン・スペース不可 |
| 51-80 | 受取人名 | C30 | 左詰め |
| 81-90 | 振込金額 | N10 | 円。右詰め・前ゼロ |
| 91 | 新規コード | N1 | 1=第1回振込分 2=変更分 0=その他（銀行により「未使用・0」） |
| 92-111 | 顧客コード1(10)+2(10)、または EDI 情報(20) | C20 | 識別表示が Y のとき EDI 情報 |
| 112 | 振込指定区分 | N1 | 7=テレ振込 8=文書振込（銀行により 7 のみ） |
| 113 | 識別表示 | C1 | Y または スペース |
| 114-120 | ダミー | C7 | スペース |

### トレーラ・レコード（データ区分 8）／エンド・レコード（データ区分 9）

| 位置 | 項目 | 桁 | 内容 |
|---|---|---|---|
| 1 | データ区分 | N1 | 8 |
| 2-7 | 合計件数 | N6 | データ・レコードの件数 |
| 8-19 | 合計金額 | N12 | データ・レコードの振込金額の合計 |
| 20-120 | ダミー | C101 | スペース |

エンド: 1桁目 9、2〜120桁目スペース（119桁）。

## 3. 給与振込（11）・賞与振込（12）（民間）

別冊 §4・§5。ヘッダー・トレーラ・エンドの形は総合振込と同じで、違いは次のとおり（賞与は種別コードが 12 なだけで給与と同一）。

- ヘッダー: 種別コード 11（給与）/ 12（賞与）、5-14 は「会社コード」、15-54 は「会社名」（事業所名等を含めてよい）、55-58 は「振込指定日」MMDD。預金種目（96）は 1/2 のみ。
- データ・レコードの 1〜50 桁目は総合振込と同じ。違う部分:

| 位置 | 項目 | 桁 | 内容 |
|---|---|---|---|
| 43 | 預金種目 | N1 | 1普通 2当座（貯蓄・その他は無い） |
| 51-80 | 預金者名 | C30 | |
| 91 | 新規コード | N1 | 1=第1回振込分 2=変更分 0=その他 |
| 92-101 | 社員番号 | N10 | 任意。右詰め・前ゼロ |
| 102-111 | 所属コード | N10 | 任意。右詰め・前ゼロ |
| 112-120 | ダミー | C9 | |

- 振込指定区分・識別表示・EDI 情報は給与・賞与には無い。

## 4. 使える文字（別冊 付録1 の JIS 表と注1〜注3）

| 項目 | 使える文字 |
|---|---|
| 名義（振込依頼人名・会社名・受取人名・預金者名） | カナ（**小文字を除く**）、濁点 ﾞ・半濁点 ﾟ（独立した1文字）、英大文字 A〜Z、数字 0〜9、スペース、記号4種 `( ) - .` |
| ヲ（ｦ） | 総合振込の名義では使える。給与・賞与の名義では使えない（注1の括弧書き） |
| 店舗名（支店名） | カナ（ヲ・小文字を除く）、濁点・半濁点、英大文字、数字、記号はハイフン `-` のみ |
| 給与・賞与の名義以外の項目 | カナ（ヲ・小文字を除く）、濁点・半濁点、数字、スペースのみ（注2） |
| EDI 情報（総合振込） | カナ（ヲを含む・小文字を除く）、濁点・半濁点、英大文字、数字、スペース、記号8種 `\ 「 」 ( ) - / .`。**カンマは使わない**（銀行システムの区切り文字と衝突。注3）。8種のうち一部の銀行で使えない記号がある |

- 英小文字は文字表にない。長音「ｰ」も、このスキルが確認した文字表では見つからない（付録1 の表で確認できたのは上の記号）。長音をハイフンに置き換えてよいかは、銀行・届出名義で扱いが違うため**取引銀行（または受取人の口座名義）で確認**。
- 銀行名の項目の文字規定は、確認した範囲では付録1 に個別の記載が無い（任意項目）。
- 小文字カナの置換: ｧ→ｱ ｨ→ｲ ｩ→ｳ ｪ→ｴ ｫ→ｵ ｬ→ﾔ ｭ→ﾕ ｮ→ﾖ ｯ→ﾂ（例: キャッシュ → ｷﾔﾂｼﾕ）。付録2の例 `ｼﾖｳｼﾞ` も小文字を大文字で書いている。

## 5. 名義の書き方（別冊 付録2）

- 個人の姓と名、法人の種類名と名称、法人名と営業所名は、それぞれの間にスペースを1つ入れて分ち書きする（例: ヤマモト イチロウ）。
- 法人略語は括弧で判別: 先頭 `ｶ)ﾔﾏﾓﾄ`、末尾 `ﾔﾏﾓﾄ(ｶ`、中間 `ﾔﾏﾓﾄ(ｶ)ﾄｳｷﾖｳ`。1法人名につき略語は1個（法人略語・事業略語・営業所略語の併用は可）。
- 法人略語の主なもの: 株式会社 ｶ／有限会社 ﾕ／合名会社 ﾒ／合資会社 ｼ／合同会社 ﾄﾞ／相互会社 ｿ／医療法人 ｲ／学校法人 ｶﾞｸ／社会福祉法人 ﾌｸ／特定非営利活動法人 ﾄｸﾋ／独立行政法人 ﾄﾞｸ／弁護士法人 ﾍﾞﾝ／税理士法人 ｾﾞｲ。全一覧は付録2を読む。営業所略語: 営業所 ｴｲ、出張所 ｼﾕﾂ。
- 中黒「・」の扱いは別冊の本文では確認できていない。受取人の口座名義の登録に合わせる（銀行により異なる）。

## 6. generate の CSV の列

1行目は列名。必須: `bank_no, branch_no, account_type, account_no, name, amount`。任意: `bank_name, branch_name, new_code(既定0), customer1, customer2, edi, transfer_kbn(既定7)`（総合振込）／`employee_no, dept_code`（給与・賞与）。見本は `assets/sample_transfers.csv` `assets/sample_salary.csv`（架空の値）。

- 名義は全角でも渡せる（変換する）。**漢字は読みを決められないので変換せず中止する**（読みは使い手がカナで渡す）。
- Excel が先頭のゼロを落とした銀行番号・支店番号・口座番号は、桁が足りなければ左をゼロ埋めして注意を出す（元の桁を確認させる）。

## 7. このスキルが確認できていないこと

- 統一金融機関番号・統一店番号の一覧（変わるため。全銀協・各銀行の公開一覧で確認）と、口座の実在。
- 銀行ごとの固定値・必須項目・営業日の取り扱い（`bank-differences.md` に確認できた差だけ）。
- ゆうちょ銀行・信用金庫・Biz 系の各仕様書は PDF の本文を取得できず未確認。
- 全銀 TCP/IP 手順での送信、ZEDI（総合振込の EDI 拡張）、口座振替(91)・口座振替以外の種別。

=== FILE: scripts/selftest_zengin.py ===
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

=== FILE: scripts/zengin.py ===
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

=== FILE: assets/sample_salary.csv ===
bank_no,branch_no,account_type,account_no,name,amount,new_code,employee_no,dept_code
9999,001,1,0000011,テスト タロウ,250000,0,1,10
9999,001,1,0000012,テスト ハナコ,300000,0,2,10

=== FILE: assets/sample_transfers.csv ===
bank_no,bank_name,branch_no,branch_name,account_type,account_no,name,amount,new_code,customer1,customer2,edi,transfer_kbn
9999,テストギンコウ,001,ホンテン,1,0000001,テストショウジ株式会社,150000,0,,,,7
9999,テストギンコウ,002,ミナミ,1,0000002,ヤマダ ハナコ,32000,1,,,,7
9998,テストシンキン,010,キタ,2,0000003,ｱｲｳ ｷｬｯｼｭ（ｶ,1000,0,,,INV-0001,7
9998,テストシンキン,010,キタ,4,0000004,ヴァイオリン ワークス,500,0,,,,7

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
