<!-- jp-nta-corporate-api v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-nta-corporate-api（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-nta-corporate-api
description: >-
  国税庁の法人番号 Web-API（法人名・法人番号での検索、差分取得）と、適格請求書発行事業者公表システム Web-API（登録番号での照会）を呼ぶコードを書き、アプリケーションIDの取り方、件数上限と分割取得、エラーの原因を調べる。「法人番号から会社名を取得するコードを書いて」「適格請求書の登録番号が有効かAPIで調べたい」「国税庁APIのアプリケーションIDの取り方は」「法人番号の差分データを毎日取りたい」「404や403が返る」と頼まれたときに使う。公式仕様書（確認日つき）に沿い、照会スクリプトを同梱。IDは環境変数から読み、会話に書かない。Keywords: houjin-bangou Web-API, invoice-kohyo Web-API, NTA, 法人番号, 登録番号, T番号, application ID。法人番号の検査桁の計算（jp-invoice-check）、登録の有無の法的判断、画面のスクレイピングは対象外。
license: MIT
compatibility: "Python 3.9 以上（標準ライブラリだけ）。国税庁への通信にはインターネット接続とアプリケーションIDが必要。通信できない環境では --dry-run と手順の提示まで"
metadata:
  version: "1.0.0"
  author: frametech
---

# 国税庁 法人番号／適格請求書 Web-API の照会

目的: 法人番号システムと適格請求書発行事業者公表システムの Web-API を使うコードを書き、ID・制限・エラーの答えを公式仕様どおりに出す。
入力: やりたいこと（番号から名称／名称から検索／登録番号の照会／差分）、手元の番号、エラーメッセージ。**アプリケーションIDは聞かない・書き写さない。**
出力: 動くコード（またはスクリプトの実行コマンド）と、効いている制限の一言。エラー調べなら「原因の候補 → 確かめ方 → 直し方」。

事実は [references/](references/) にある（確認日 2026-10-23）。**確認日から90日を過ぎたら、各ファイル冒頭の公式URLを読み直してから答える。** 仕様書は改版される（利用規約は 2026-09-24 に改正済み）。

## 鍵の扱い（最初に守る）

- アプリケーションIDは**コード・コマンド引数・ファイル・会話に書かない**。貼られても書き写さず、環境変数から読む形で書く。ID は第三者への開示が規約で禁止されているので、貼られた場合は漏れた可能性を伝え、国税庁へ連絡する選択肢を添える。
- 環境変数: `NTA_HOUJIN_APP_ID`（法人番号 API。無ければ `NTA_INVOICE_APP_ID` を使う）、`NTA_INVOICE_APP_ID`（インボイス API）。
- **ID は2種類**: インボイス用ID は両 API に使える。法人番号用ID は法人番号 API だけ（インボイス API を呼ぶと404）。ID が無ければ取得手続を先に案内する（references/app-id-and-terms.md。無料、書面不可、1〜数週間かかる）。

## 手順

1. 依頼を分ける: (a) 法人番号→名称・所在地 (b) 名称→法人番号 (c) 登録番号の照会 (d) 差分取得・日次同期 (e) ID・規約・出典表示 (f) エラー・制限。
2. **API と機能を選ぶ**（詳細は references/api-spec.md）:

   | やりたいこと | API・機能 | 上限・注意 |
   |---|---|---|
   | 法人番号（13桁）から | 法人番号 `/4/num` | 1回10件 |
   | 名称から探す | 法人番号 `/4/name` | 2,000件で分割。多すぎると180。`name` は UTF-8 で URL エンコード |
   | 登録番号（T＋13桁）から | インボイス `/1/num` | 1回10件。履歴は `history=1` |
   | ある日付時点の登録状況 | インボイス `/1/valid`（`day`） | 1回10件 |
   | 更新分だけ | `/diff`（両方） | 期間50日以内。分割は法人番号が2,000件、インボイスが**500件** |

   形式は法人番号が CSV(Shift-JIS)／CSV(UTF-8)／XML、インボイスが CSV／XML／JSON。**法人番号 API に JSON は無い。** コードは法人番号 XML（type=12）、インボイス JSON（type=21）が扱いやすい。
3. 通信できるなら同梱スクリプトを使う。まず `--dry-run` で URL を見せ、環境変数が揃っていれば実行する。

   ```bash
   python3 scripts/nta_lookup.py houjin-num --number 5111101000006 --dry-run
   python3 scripts/nta_lookup.py invoice-valid --number T8040001999011 --day 2026-10-23
   python3 scripts/nta_lookup.py houjin-name --name 国税 --mode 2 --address 13 --all --format csv --bom -o out.csv
   ```

   通信できない・スクリプトを実行できない環境では、references/recipes.md のコードと URL を示し、手元で実行してもらう（結果は貼ってもらう）。
4. **分割取得**: 応答ヘッダーの分割数が1以外なら `divide=2,3,…` を分割数まで繰り返す。間隔を空ける（短時間の大量アクセスは規約違反で、403 の原因）。スクリプトは `--all`（既定の間隔1秒）。
5. **差分取得**: 開始日は法人番号 2015-12-01 以降／インボイス 2021-10-01 以降、期間は50日以内。全件の土台は公表サイトのダウンロード。同じ番号が複数回出るので `sequenceNumber` 順に処理して上書き（recipes.md の運用）。
6. **サービスとして公開するなら出典表示が必要**（規約第6条）。定型文は references/app-id-and-terms.md。
7. エラーは HTTP ステータスとエラーコード（法人番号3桁／インボイス4桁）を聞き、references/errors.md の表で原因候補を出す。ID が無効だと HTML の404 が返る。

## 守ること

- **法人番号の検査桁の検証はしない**（jp-invoice-check の領分）。このスキルが見るのは桁数と T の有無だけ。
- **登録の有無・失効の意味を法的に判断しない。** 返るのは公表されている項目の値だけ。応答に番号が出てこない理由は仕様書に明記が見つからないので断定せず、公表サイトの画面で確かめるよう案内する。取引・仕入税額控除への効き方は税理士・国税庁へ。
- 画面のスクレイピングは勧めない（API と規約がある）。
- 取得した個人事業者の氏名などは個人情報になり得る。保存・再配布の範囲は規約原文で確かめるよう添える。

## 返す形

```
（コードまたは実行コマンド）

効いている制限: 今回に関係するものだけ（10件／50日／2,000件・500件で分割 など）
確認が要ること: アプリケーションIDの種類、出典表示、規約（原文）、実環境での動作
```

## 同梱物

| ファイル | 内容 |
|---|---|
| scripts/nta_lookup.py | `houjin-num` `houjin-name` `houjin-diff` `invoice-num` `invoice-valid` `invoice-diff`。分割取得（`--all`）、JSON/CSV 出力、`--dry-run`（IDを伏せる）。終了コード 0 正常／1 API・通信の失敗／2 引数・環境変数の誤り |
| scripts/selftest_mock.py | 手元にモックの国税庁APIを立てて、分割・エラー・伏せ字を確かめる自己検証（本物には接続しない） |
| references/api-spec.md | エンドポイント・バージョン・パラメーター・応答形式・上限・応答項目（出典URLと確認日つき） |
| references/app-id-and-terms.md | アプリケーションIDの取得と管理、検証環境、規約の要点、出典表示の定型文 |
| references/errors.md | HTTPステータスとエラーコードの表、症状別の対処 |
| references/recipes.md | curl・Python 標準ライブラリのコード、差分の運用 |

## 限界

実際のアプリケーションIDでの成功は、このスキルの作成時点では未検証（モックサーバーと公式仕様書の突き合わせ、無効IDで両サーバーが404を返すことまで）。エラー時の CSV 本文の列の並びも未確認。初めて本番に向けるときは、1件の照会から始める。

=== FILE: references/api-spec.md ===
# 国税庁 Web-API の仕様（法人番号システム／適格請求書発行事業者公表システム）

確認日: 2026-10-23。**確認日から90日を過ぎたら、下の出典を読み直してから答える。** 仕様書は PDF で、改版される（法人番号側の共通編は 2026-09 に 4.10 版、利用規約は 2026-09-24 施行）。

出典（すべて国税庁。2026-10-23 に PDF 本文を取得して確認）:
- 法人番号 Web-API トップ: https://www.houjin-bangou.nta.go.jp/webapi/
  - 第一編 共通編（4.10版）: https://www.houjin-bangou.nta.go.jp/pc/webapi/images/k-web-api-tetuduki.pdf
  - 第二編 概要編（リクエスト条件・エラー一覧・リソース定義書）: https://www.houjin-bangou.nta.go.jp/webapi/images/k-web-api-kinou-gaiyo.pdf
  - 第六編 Ver.4.0: https://www.houjin-bangou.nta.go.jp/webapi/images/k-web-api-kinou-ver4.pdf
  - 版ごとの一覧: https://www.houjin-bangou.nta.go.jp/webapi/kyuusiyousyo.html
- インボイス Web-API トップ: https://www.invoice-kohyo.nta.go.jp/web-api/index.html
  - 第二編 リクエスト設定・提供データ（Ver.1.0、1.5版）: https://www.invoice-kohyo.nta.go.jp/files/k-web-api-kinou.pdf
  - 第一編 利用手続: https://www.invoice-kohyo.nta.go.jp/files/k-web-api-tetuduki.pdf （画像主体の PDF で、本文のテキスト抽出は不可。手続は同サイトのHTMLで確認）

## 1. 共通

| 項目 | 内容 |
|---|---|
| 方式 | REST、メソッドは **GET** だけ（法人番号の共通編 §3） |
| 認証 | クエリの `id=<アプリケーションID 13桁>`（ヘッダー認証ではない） |
| 応答形式 | `type` で指定。**エラー応答は形式に関わらず CSV**（エラーコードとメッセージ） |
| 番号指定 | 1回に**最大10件**、カンマ区切り |
| 期間指定 | 開始日から**50日以内**。日付は `YYYY-MM-DD` |
| 分割 | 応答ヘッダーの「分割数」が1以外なら、`divide=2,3,…` を分割数になるまで繰り返す。分割番号は 1〜99999（法人番号）／1〜999999（インボイス）の範囲 |
| ヘッダー（4項目） | 最終更新年月日、総件数、分割番号、分割数（CSV は1行目、XML/JSON は要素） |

## 2. 法人番号 Web-API

- ホスト: `https://api.houjin-bangou.nta.go.jp/<バージョン>/<機能>`
- バージョン: 現在の最新は **4**（4.0）。1.0〜3.0 も引き続き使える。違いは項目の追加だけ: 2.0 で英語表記（2017-04）、3.0 でフリガナ（2018-04）、4.0 で検索対象除外（2019-03）。**名称検索（name）は 2 以上**
- 3機能: `num`（法人番号で）、`diff`（期間で差分）、`name`（法人名で）

### 応答形式 `type`（必須）

| 値 | 形式・文字コード |
|---|---|
| 01 | CSV／Shift-JIS（JIS 第一・第二水準） |
| 02 | CSV／Unicode（UTF-8。JIS 第一〜第四水準） |
| 12 | XML／Unicode（UTF-8） |

JSON は無い。第一・第二水準にない字（外字）は `nameImageId` 等のイメージID が入り、`https://www.houjin-bangou.nta.go.jp/image?imageid=<ID>` で画像を見られる。名称が150文字を超えると151文字目以降は入らず、イメージで確認する。

### `num`（法人番号を指定）

`/4/num?id=…&number=<13桁,…>&type=12&history=0`

| パラメーター | 必須 | 内容 |
|---|---|---|
| number | 必須 | 13桁の法人番号、最大10件 |
| type | 必須 | 上表 |
| history | 任意 | 0 変更履歴なし（既定）／1 あり。履歴ありは古い順に返る |

### `diff`（期間を指定。更新年月日が対象）

`/4/diff?id=…&from=2026-10-01&to=2026-10-03&type=12`

| パラメーター | 必須 | 内容 |
|---|---|---|
| from | 必須 | 開始日。**2015-12-01 より前はエラー 013**（API 公開日以後の差分しか取れない。全件は公表サイトのダウンロード） |
| to | 必須 | 終了日。from から50日以内 |
| type | 必須 | 上表 |
| address | 任意 | 都道府県コード2桁（国外は 99）か、都道府県＋市区町村の5桁。**市区町村コードだけはエラー 051** |
| kind | 任意 | 法人種別 01 国の機関／02 地方公共団体／03 設立登記法人／04 外国会社等・その他。カンマ区切りで最大4 |
| divide | 任意 | 分割番号。省略は1 |

並び順は 更新年月日→法人番号（昇順）。応答が **2,000件を超えると分割**。

### `name`（法人名を指定。Ver.2.0 以降）

`/4/name?id=…&name=<UTF-8でURLエンコード>&type=12&mode=1&target=1`

| パラメーター | 必須 | 内容 |
|---|---|---|
| name | 必須 | 商号又は名称を **UTF-8 で URL エンコード**。複数の名前は不可。日本語150字・英語300字以内。「株式会社」等だけは不可（エラー 103） |
| type | 必須 | 上表 |
| mode | 任意 | 1 前方一致（既定。株式会社等を除いた名前の先頭から）／2 部分一致（株式会社等を含めて検索できる） |
| target | 任意 | 1 JIS第一・第二水準のあいまい検索（既定）／2 JIS第一〜第四水準の完全一致／3 英語表記。1・2 は全角、3 は半角でエンコード |
| address | 任意 | diff と同じ |
| kind | 任意 | diff と同じ |
| change | 任意 | 0 旧名称・旧所在地を含めない（既定）／1 含める。**1 で旧情報が当たると、その法人の最新情報は返らない**。最新が要るなら、返った法人番号で `num` を呼び直す |
| close | 任意 | 1 登記記録の閉鎖等を含める（既定）／0 含めない |
| from / to | 任意 | **法人番号指定年月日**の範囲（ここでの from は 2015-10-05 以降。違反はエラー 152） |
| divide | 任意 | 分割番号。省略は1 |

並び順は 法人名の UTF-8 コード昇順→法人番号。**2,000件を超えると分割**。ただし件数が多すぎると分割以前に**エラー 180**（「検索結果件数が多いため結果をお返しできません」）になる。住所・種別・名称を足して絞る。

あいまい検索（target=1）は、ひらがな→カタカナ、英小文字→大文字、中点と全角スペースの削除をして検索する。

### 応答項目（Ver.4。XML のタグ／CSV の列順は同じ並び・全30項目）

sequenceNumber 一連番号, corporateNumber 法人番号, process 処理区分, correct 訂正区分, updateDate 更新年月日, changeDate 変更年月日, name 商号又は名称, nameImageId, kind 法人種別, prefectureName, cityName, streetNumber, addressImageId, prefectureCode, cityCode, postCode, addressOutside, addressOutsideImageId, closeDate, closeCause, successorCorporateNumber, changeCause, assignmentDate 法人番号指定年月日, latest 最新履歴, enName, enPrefectureName, enCityName, enAddressOutside, furigana, hihyoji 検索対象除外（0 対象／1 除外）。

- process: 01 新規／11 商号又は名称の変更／12 国内所在地の変更／13 国外所在地の変更／21 登記記録の閉鎖等／22 閉鎖等の復活等／71 吸収合併／72 吸収合併無効／81 商号の登記の抹消／99 削除（99 は一連番号・法人番号・更新年月日以外が空）
- kind: 101 国の機関／201 地方公共団体／301 株式会社／302 有限会社／303 合名会社／304 合資会社／305 合同会社／399 その他の設立登記法人／401 外国会社等／499 その他
- 違う版のとき、使える項目は仕様書のリソース定義書の「提供項目」欄で確かめる（Ver.1 は英語表記・フリガナ・検索対象除外が無い）。
- 時系列に処理するときは一連番号の小さい順（分割しても通し番号は全体で連続）。

### 更新タイミング（共通編 §4）

法人番号を指定する機能と法人名を指定する機能は1日2回（登記完了日の16時、または翌稼働日の11時）、期間指定は登記完了日の翌日午前0時。休祝日と12/29〜1/3は更新しない。遅れることがある。

## 3. 適格請求書発行事業者公表システム Web-API

- ホスト: `https://web-api.invoice-kohyo.nta.go.jp/<バージョン>/<機能>`。バージョンは **1**（Ver.1.0）だけ
- 3機能: `num`（登録番号で）、`diff`（期間で差分）、`valid`（登録番号＋判定基準日）
- 応答形式 `type`: **01 CSV／11 XML／21 JSON**。文字コードはすべて Unicode（UTF-8）

### `num`

`/1/num?id=…&number=T8040001999011&type=21&history=0`

| パラメーター | 必須 | 内容 |
|---|---|---|
| number | 必須 | **T＋13桁**（計14桁）、最大10件 |
| type | 必須 | 01/11/21 |
| history | 任意 | 0 最新のみ（既定）／1 登録・取消・失効の履歴も |

### `valid`

`/1/valid?id=…&number=T…,T…&day=2026-10-23&type=21`

`day`（判定基準日）を基準にした**直近の登録年月日・取消年月日・失効年月日に紐づく情報**を返す。並びはリクエストした登録番号の順（ソートなし）。

### `diff`

`/1/diff?id=…&from=2026-10-01&to=2026-10-03&type=21`

| パラメーター | 必須 | 内容 |
|---|---|---|
| from / to | 必須 | 更新年月日の範囲。**from は 2021-10-01 以降**（エラー 0104）。to は from から50日以内 |
| type | 必須 | 01/11/21 |
| division | 任意 | 人格区分 1 個人／2 法人。省略は両方 |
| divide | 任意 | 分割番号。省略は1 |

並びは 更新年月日→登録番号→履歴の日付。**500件を超えると分割**（法人番号側の2,000件とは違う）。

### 応答項目（JSON のキー名。綴りは仕様書どおり `registratedNumber`）

sequenceNumber, registratedNumber 登録番号, process 事業者処理区分, correct 訂正区分, kind 人格区分(1 個人／2 法人), country 国内外区分(1 国内／2 特定国外／3 特定国外以外の国外), latest 最新履歴(0 過去／1 最新), registrationDate 登録年月日, updateDate 更新年月日, disposalDate 取消年月日, expireDate 失効年月日, address（法人の本店等の所在地）, addressPrefectureCode, addressCityCode, addressRequest（公表申出の所在地。個人・人格のない社団等）, addressRequestPrefectureCode, addressRequestCityCode, kana, name 氏名又は名称, addressInside, addressInsidePrefectureCode, addressInsideCityCode, tradeName 主たる屋号, popularName_previousName 通称・旧姓。

- process: 01 新規／02 公表内容の変更／03 登録の失効／04 登録の取消／99 削除（99 はダウンロード差分のみで、API では作られない）
- correct は API では常に 0（リソース定義書）。氏名・所在地（公表申出）・屋号・通称などは、公表の申出書に記載があるものだけ入る項目で、空のことがある
- 項目名の見出しは応答に入らない。意味は仕様書のリソース定義書（別紙1）で引く

## 4. 実行・運用の注意

- 外部通信できないチャット環境では実行できない。URL の組み立てまでを示す（`python3 scripts/nta_lookup.py … --dry-run`）
- Web ブラウザで直接叩くとデータが表示できないことがある（共通編 §7.2 注2）。プログラムから呼ぶ
- 「短時間の大量アクセス」は利用規約の禁止事項で、同一IDへのアクセス制限（HTTP 403）の原因。分割取得は間隔を空ける（スクリプトの既定は1秒）
- 検証環境（架空の法人名のテストデータ）がある。IDは本番と同じものを使えるが、利用希望の連絡が必要（法人番号側は問合せフォームから、利用予定期間は3か月以内、案内メールは概ね1週間。詳細は app-id-and-terms.md）

=== FILE: references/app-id-and-terms.md ===
# アプリケーションID・利用規約・出典表示

確認日: 2026-10-23。**確認日から90日を過ぎたら出典を読み直す。**

出典:
- 法人番号 Web-API（共通編 4.10版・利用規約別添1）: https://www.houjin-bangou.nta.go.jp/pc/webapi/images/k-web-api-tetuduki.pdf
- 法人番号 Web-API トップ: https://www.houjin-bangou.nta.go.jp/webapi/
- インボイス Web-API トップ（ID の種類と手続）: https://www.invoice-kohyo.nta.go.jp/web-api/index.html
- インボイス Web-API 利用規約: https://www.invoice-kohyo.nta.go.jp/web-api/riyou_kiyaku.html （ページ内容の要約を取得して確認。条文の細部は原文を読む）

## 1. アプリケーションID の取り方

| 項目 | 内容 |
|---|---|
| 費用 | 無料（手数料なし） |
| 窓口 | **インボイス公表サイト内の Web-API 画面**から届出。法人番号の共通編 §5.1 も、届出の入口はここ（https://www.invoice-kohyo.nta.go.jp/web-api/）。**書面は受け付けない** |
| 流れ | 仮登録（メールアドレス）→ 本登録（基本情報と、データの取得方法・使い方を説明する書類）→ 審査 → ID をメールで通知 |
| 所要 | 法人番号用は登録からおよそ1か月、インボイス用は審査がある（トップページの記載。共通編は 2週間〜1か月ほどと案内するページもある）。**時間がかかるので早めに** |
| ID の形 | 13桁（仕様書の記載） |
| 種類 | **インボイス用ID**＝インボイス API と法人番号 API の両方に使える。**法人番号用ID**＝法人番号 API だけ。法人番号用IDにインボイス API の権限を足す手続もある |
| 発行単位 | 原則、Web-API サーバーと通信するシステムごと |
| メールアドレス | **同じメールアドレスで複数の ID は届け出られない**（別の ID に使っていないアドレスを1つ） |
| 変更・停止 | 登録内容の変更、ID の停止は同じ窓口の別フォーム（pre-change / pre-stop） |
| 未届出で | `invoice-web-api@nta.go.jp` に問い合わせる案内あり（トップページ）。法人番号側の問合せは https://www.houjin-bangou.nta.go.jp/webapi/toiawase/ |

**ユーザーが ID を持っていない場合は、まず取得手続を案内する。** ID を取る前に実装だけ進める場合は、スクリプトの `--dry-run` で URL を確かめられる（通信しない）。

### ID の管理（規約）

- ID は利用者が管理責任を負う。**第三者に譲渡・貸与・開示してはならない**。コード・リポジトリ・チャットに貼らない（環境変数で渡す）
- 第三者に不正利用された・紛失した・使わなくなったときは、速やかに国税庁へ連絡
- **3年以上アクセスがない ID は停止されることがある**
- 国税庁は不正利用の疑いがあれば直ちに利用停止できる

## 2. 検証環境（テスト用）

架空の法人名等のテストデータを返す検証環境がある（法人番号側の共通編 §7）。本番と同じ ID を使える。利用には連絡が必要で、法人番号側は問合せフォームに ID・法人名又は氏名・メール・電話・利用予定期間（3か月以内）を書く。案内は概ね1週間でメールが届く（nta.go.jp のメールを受信できるようにする）。インボイス側の検証環境は https://www.invoice-kohyo.nta.go.jp/web-api/kensyou.html （ID が要る）。**このスキルは検証環境の URL を持っていない**（案内メールに書かれる）。

## 3. 利用規約の要点（法人番号 Web-API 機能利用規約、2026-09-24 施行版。全文は原文を読む）

- 誰でも利用できるが、規約への同意が前提
- **第6条 出典の明示**: 本機能を使ったサービスを提供するときは、次の文を「適宜の場所に」明示する。
  - 法人番号: 「このサービスは、国税庁法人番号システムWeb-API機能を利用して取得した情報をもとに作成しているが、サービスの内容は国税庁によって保証されたものではない」
  - インボイス（要約で確認）: 「このサービスは、適格請求書発行事業者公表システムWeb-API機能を利用して取得した情報をもとに作成しているが、サービスの内容は国税庁によって保証されたものではない」
  - 両方を使うサービスは、両方の表示を入れる
- **第9条 禁止事項**: 運用の故意の妨害／ウイルス付きファイルの送信／**短時間における大量アクセスなど運用に支障を与えること**／規約違反・法令違反・**閲覧者に誤解を与えるおそれのある内容**のアプリの作成／**ID の譲渡・貸与・開示**
- 第8条: 利用が集中した場合などに国税庁は利用を制限できる。メンテナンス・障害で停止することがある（法人番号公表サイトに告知。緊急時は無告知）
- インボイス側（要約）: 違反による停止後は1年間は再申請できない旨の記載あり
- 第10条: 国税庁は故意・重過失を除いて損害の責任を負わない
- コンテンツ（取得した情報）の利用条件は「国税庁法人番号公表サイト利用規約」（別添3）に従う
- 第5条: 利用状況のアンケート依頼があり得る
- 個人情報の取扱いは国税庁の個人情報保護方針（別添2）。取得データの保存・再配布の範囲は規約原文で確かめる（このスキルは法的助言をしない）

=== FILE: references/errors.md ===
# エラーの読み方

確認日: 2026-10-23。出典: 法人番号 概要編 別紙2 https://www.houjin-bangou.nta.go.jp/webapi/images/k-web-api-kinou-gaiyo.pdf ／ インボイス 第二編 別紙2 https://www.invoice-kohyo.nta.go.jp/files/k-web-api-kinou.pdf 。**90日を過ぎたら読み直す。**

エラー時は HTTP ステータスのほか、エラーコードとメッセージが **CSV 形式**で本文に返る（`type` の指定に関わらず）。**CSV の列の並び（コードが何列目か等）は仕様書に図がなく未確認**。スクリプトは本文から該当コードの数字を拾って表を引く。

## 1. HTTP ステータス（両 API 共通）

| 状態 | 意味（公式） | 次の手 |
|---|---|---|
| 400 | リクエスト条件の誤り。エラーコードで内容が分かる | 下の表で直す |
| 403 | 同一アプリケーションID で一定期間に多数アクセスし、**アクセス制限された後**に、その ID で再アクセスした | 間隔を空け、件数を減らし、時間をおいて再開。解除方法は仕様書に記載なし（問合せフォーム）。インボイス側は「アクセス制御中」と表現 |
| 404 | ID が**未登録または無効**。インボイス側はこれに加え、**URL の機能が見つからない**場合も404 | ID の桁・コピーミス・停止（3年無アクセス等）を確認。URL のバージョン（法人番号 4／インボイス 1）と機能名（num/diff/name/valid）を確認。法人番号用 ID でインボイス API を呼んでいないか |
| 500 | 国税庁側の障害 | 時間をおいて再試行。長引けば法人番号公表サイトの告知を見る |

404 の本文は、実際に存在しない ID で呼ぶと HTML の「404 Not Found」ページが返った（2026-10-23 に両ホストで確認。ID は `0000000000000`）。つまり**ID が無効だと CSV のエラーではなく HTML になる**。

## 2. 400 のエラーコード（法人番号、3桁）

機能: 差=期間指定 num=法人番号指定 name=法人名指定。

| コード | 内容 | 機能 |
|---|---|---|
| 010/011/012 | 取得期間開始日が未指定／YYYY-MM-DD でない／存在しない日付 | 差 |
| 013 | 開始日が 2015-12-01 より前 | 差 |
| 020/021/022 | 終了日の同様の誤り | 差 |
| 030 | 開始日が終了日より後 | 差 |
| 031 | 期間が50日を超える | 差 |
| 040/041/042/043 | 法人番号が未指定／10件超／半角数字でない／13桁でない | num |
| 050/051/052 | 所在地が半角数字でない／2桁か5桁でない（**市区町村コードだけは051**）／存在しないコード | 差・name |
| 060〜063 | 法人種別が4件超／半角数字でない／2桁でない／01〜04以外 | 差・name |
| 070〜073 | type が未指定／半角数字でない／2桁でない／01・02・12以外（JSON は無い） | 全部 |
| 080〜082 | history が半角数字でない／1桁でない／0・1以外 | num |
| 090/091 | divide が半角数字でない／範囲外（分割数を超えた等） | 差・name |
| 100 | name が未指定 | name |
| 101 | name が UTF-8 でエンコードされていない（全角／半角の別あり） | name |
| 102 | name が日本語150字・英語300字を超える | name |
| 103 | name が「株式会社」「有限会社」等の組織名称だけ | name |
| 110〜112 | mode が半角数字でない／1桁でない／値が不正（**公式のメッセージ 112 は「前方一致(1)・部分一致(0)」と書かれているが、概要編の条件表は 1 前方一致・2 部分一致。条件表に従う**） | name |
| 120〜122 | target が半角数字でない／1桁でない／1〜3以外 | name |
| 130〜132 | change の同様の誤り | name |
| 140〜142 | close の同様の誤り | name |
| 150/151/152 | 法人番号指定年月日の開始日が形式不正／存在しない／**2015-10-05より前** | name |
| 160/161 | 終了日の形式不正／存在しない | name |
| 170 | 指定年月日の開始日が終了日より後 | name |
| **180** | **検索結果件数が多く返せない。条件を追加・変更**（分割で取れる範囲を超える） | name |

## 3. 400 のエラーコード（インボイス、4桁）

| コード | 内容 | 機能 |
|---|---|---|
| 0001 | 登録番号が未指定 | num・valid |
| 0002 | 10件超 | num・valid |
| 0003 | 登録番号n に値がない（カンマの連続・末尾のカンマなど） | num・valid |
| 0004 | 14桁でない | num・valid |
| 0005 | **T＋数字13桁でない**（T が小文字、T が無い等） | num・valid |
| 0101〜0103 | 開始日が未指定／形式不正／存在しない日付 | diff |
| 0104 | 開始日が **2021-10-01 より前** | diff |
| 0201〜0203 | 終了日の同様の誤り | diff |
| 0204 | 終了日が開始日より前 | diff |
| 0205 | 期間が50日を超える | diff |
| 0301〜0303 | day が未指定／形式不正／存在しない | valid |
| 0401〜0403 | division が半角数字でない／1桁でない／1・2以外 | diff |
| 0501〜0504 | type が未指定／半角数字でない／2桁でない／01・11・21以外 | 全部 |
| 0601〜0603 | history の誤り | num |
| 0701/0702 | divide が半角数字でない／範囲外 | diff |

## 4. よくある症状

| 症状 | 原因の候補 |
|---|---|
| 404 が返る | ID の誤り・未登録・停止／URL の誤り／**インボイス API に法人番号用 ID**（法人番号用 ID は法人番号 API だけ） |
| 403 が返る | 短時間の連続アクセスによる制限。ループにスリープがあるか、並列で叩いていないか |
| 名称検索で件数が多く 180 | 住所（address）、法人種別（kind）、名称の長さで絞る。部分一致をやめて前方一致にする |
| 名称が文字化け／□ | 外字（第一・第二水準にない字）。type=02/12（UTF-8）にし、`nameImageId` のイメージで確かめる。CSV 01 は Shift-JIS なので UTF-8 として読むと壊れる |
| 旧社名で当たったのに住所が古い | `change=1` で旧情報が当たると最新情報は返らない。返った法人番号で `num` を呼び直す |
| 差分を取ったのに最近の変更が無い | 更新は1日1〜2回、休祝日・12/29〜1/3は更新なし。期間指定は登記完了日の翌日午前0時に反映 |
| 総件数と取れた件数が合わない | `divide` を回していない。ヘッダーの分割数まで繰り返す（`--all`） |
| invoice で番号が結果に出ない | 応答に載らなかった理由（未登録・失効後の扱い等）は仕様書に明記が見つからない。**断定せず**、`valid` の基準日を変えて確認、または公表サイトの画面で確かめるよう案内する |

=== FILE: references/recipes.md ===
# コード例（Python 標準ライブラリ・curl）

確認日: 2026-10-23。仕様は api-spec.md。ID は環境変数から読み、コードに書かない。実際の ID での成功は未検証（モックと、無効 ID で 404 が返ることまで）。

## curl（動作確認用。ID はシェルの環境変数から）

```bash
# 法人番号から会社名（XML, UTF-8）
curl -sS "https://api.houjin-bangou.nta.go.jp/4/num?id=${NTA_HOUJIN_APP_ID}&number=5111101000006&type=12&history=0"

# 適格請求書の登録番号（JSON）
curl -sS "https://web-api.invoice-kohyo.nta.go.jp/1/num?id=${NTA_INVOICE_APP_ID}&number=T8040001999011&type=21&history=0"

# 名称検索は --data-urlencode で UTF-8 エンコード（-G で GET のまま）
curl -sS -G "https://api.houjin-bangou.nta.go.jp/4/name" --data-urlencode "id=${NTA_HOUJIN_APP_ID}" \
  --data-urlencode "name=国税" --data-urlencode "type=12" --data-urlencode "mode=2"
```

## Python: 法人番号 → 名称・所在地（XML）

```python
import os, urllib.request, urllib.parse
import xml.etree.ElementTree as ET

def houjin_by_number(numbers):                      # 13桁の文字列のリスト（最大10件）
    q = urllib.parse.urlencode({"id": os.environ["NTA_HOUJIN_APP_ID"],
                                "number": ",".join(numbers), "type": "12", "history": "0"}, safe=",")
    with urllib.request.urlopen("https://api.houjin-bangou.nta.go.jp/4/num?" + q, timeout=30) as r:
        root = ET.fromstring(r.read())
    return [{c.tag: (c.text or "") for c in corp} for corp in root.findall("corporation")]

for c in houjin_by_number(["5111101000006"]):
    print(c["corporateNumber"], c["name"], c["prefectureName"] + c["cityName"] + c["streetNumber"])
```

## Python: インボイスの登録番号が基準日時点でどうか（JSON）

```python
import os, json, urllib.request, urllib.parse

def invoice_valid(numbers, day):                    # "T"+13桁のリスト、"YYYY-MM-DD"
    q = urllib.parse.urlencode({"id": os.environ["NTA_INVOICE_APP_ID"], "number": ",".join(numbers),
                                "day": day, "type": "21"}, safe=",")
    with urllib.request.urlopen("https://web-api.invoice-kohyo.nta.go.jp/1/valid?" + q, timeout=30) as r:
        return json.loads(r.read().decode("utf-8")).get("announcement", [])

for a in invoice_valid(["T8040001999011"], "2026-10-23"):
    print(a["registratedNumber"], a["name"], a["registrationDate"], a["disposalDate"] or "-", a["expireDate"] or "-")
```

返ってきた取消年月日・失効年月日が空かどうかを**表示する**ところまでがこのスキルの範囲。それが取引や仕入税額控除にどう効くかは判断しない（税理士・国税庁へ）。

## Python: 分割取得（差分でも名称検索でも同じ形）

```python
import time
def fetch_all(build_url, parse, sleep=1.0, max_pages=100):
    divide, out = 1, []
    while True:
        url = build_url(divide)                     # divide>1 のときだけ &divide=N を付ける
        header, rows = parse(url)                   # header["divideSize"] を見る
        out += rows
        if divide >= int(header["divideSize"] or 1) or divide >= max_pages:
            return out
        divide += 1
        time.sleep(sleep)                           # 短時間の大量アクセスは禁止・403 の原因
```

## 同梱スクリプトで同じことをする

```bash
export NTA_HOUJIN_APP_ID=…   # 値は会話に書かない
python3 scripts/nta_lookup.py houjin-num --number 5111101000006
python3 scripts/nta_lookup.py houjin-name --name 国税 --mode 2 --address 13 --all --format csv --bom -o out.csv
python3 scripts/nta_lookup.py houjin-diff --from 2026-10-01 --to 2026-10-03 --all
python3 scripts/nta_lookup.py invoice-num --number T8040001999011 --history
python3 scripts/nta_lookup.py invoice-valid --number T8040001999011 --day 2026-10-23
python3 scripts/nta_lookup.py invoice-diff --from 2026-10-01 --to 2026-10-03 --division 2 --all
```

## 差分の運用（日次同期の例）

1. 初回: 公表サイトの**全件ダウンロード**で土台を作る（API の差分は 2015-12-01 / 2021-10-01 以降だけで、全件取得には向かない）
2. 以後: 前回取得した日の翌日〜昨日を `diff` で取る（50日を超えて空けたら区切る）
3. 同じ番号が複数回出る。`sequenceNumber` の小さい順に処理し、法人番号／登録番号をキーに上書き。`process=99`（法人番号）は削除の意味
4. 更新は休祝日・年末年始にない。反映は登記完了日の翌日午前0時以降

=== FILE: scripts/nta_lookup.py ===
#!/usr/bin/env python3
"""国税庁の法人番号システム Web-API と、適格請求書発行事業者公表システム Web-API を呼ぶ。

Python 3.9 以上・標準ライブラリだけ。法人番号の検査桁の検証はしない（形式＝桁数と T の有無だけ確かめる）。

  環境変数（アプリケーションID は引数に取らない）
    NTA_HOUJIN_APP_ID    法人番号 Web-API 用（13桁）。無ければ NTA_INVOICE_APP_ID を使う（インボイス用IDは両方に使える）
    NTA_INVOICE_APP_ID   適格請求書 Web-API 用（13桁）。インボイス用ID だけが使える
    NTA_HOUJIN_BASE / NTA_INVOICE_BASE   接続先の差し替え（テスト用。https か localhost/127.0.0.1 だけ）

  使い方
    python3 nta_lookup.py houjin-num   --number 5111101000006 --dry-run
    python3 nta_lookup.py houjin-num   --number 5111101000006,4111101000007 --history
    python3 nta_lookup.py houjin-name  --name 国税 --mode 2 --address 13 --all --format csv -o out.csv
    python3 nta_lookup.py houjin-diff  --from 2026-10-01 --to 2026-10-03 --all
    python3 nta_lookup.py invoice-num  --number T8040001999011
    python3 nta_lookup.py invoice-valid --number T8040001999011 --day 2026-10-23
    python3 nta_lookup.py invoice-diff --from 2026-10-01 --to 2026-10-03 --all

  終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り

通信できない環境（外部通信が禁止のチャット等）では実行できない。--dry-run は通信しないので、
組み立てた URL を確かめて、手元の環境で実行してもらう。
法的判断（登録の有無が何を意味するか）はしない。返すのは公表されている項目の値だけ。
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EXIT_OK, EXIT_FAIL, EXIT_USAGE = 0, 1, 2
HOUJIN_BASE = "https://api.houjin-bangou.nta.go.jp"
INVOICE_BASE = "https://web-api.invoice-kohyo.nta.go.jp"
HOUJIN_VER = "4"
INVOICE_VER = "1"
MASK = "＊＊＊＊（環境変数から読み込み済み・表示しない）"
MAX_NUMBERS = 10          # 番号指定は1回10件まで（両API）
MAX_DIFF_DAYS = 50        # 期間指定は50日まで（両API）
HOUJIN_DIFF_MIN = datetime.date(2015, 12, 1)
HOUJIN_ASSIGN_MIN = datetime.date(2015, 10, 5)
INVOICE_DIFF_MIN = datetime.date(2021, 10, 1)
RETRY_WAITS = (2, 5)      # 500 系・通信エラーのときだけ。400/403/404 は再試行しない

# 公式の別紙2から。法人番号 API は3桁、インボイス API は4桁
HOUJIN_ERRORS = {
    "010": "取得期間開始日が指定されていません", "011": "取得期間開始日は YYYY-MM-DD 形式", "012": "取得期間開始日が存在しない日付",
    "013": "取得期間開始日は 2015-12-01 以降", "020": "取得期間終了日が指定されていません", "021": "取得期間終了日は YYYY-MM-DD 形式",
    "022": "取得期間終了日が存在しない日付", "030": "開始日が終了日より後", "031": "取得期間が最大50日を超えている",
    "040": "法人番号が指定されていません", "041": "法人番号は10件以内", "042": "法人番号は半角数字", "043": "法人番号は13桁",
    "050": "所在地は半角数字", "051": "所在地は2桁又は5桁（市区町村コードだけは不可）", "052": "所在地コードが存在しない",
    "060": "法人種別は4件以内", "061": "法人種別は半角数字", "062": "法人種別は2桁", "063": "法人種別の値が 01〜04 以外",
    "070": "応答形式(type)が指定されていません", "071": "応答形式は半角数字", "072": "応答形式は2桁", "073": "応答形式は 01/02/12 以外",
    "080": "変更履歴要否(history)は半角数字", "081": "history は1桁", "082": "history は 0/1 以外",
    "090": "分割番号(divide)は半角数字", "091": "分割番号が範囲外（分割数を超えた等）",
    "100": "商号又は名称(name)が指定されていません", "101": "name は UTF-8 で URL エンコード（全角/半角の別あり）",
    "102": "name は日本語150文字・英語300文字以内", "103": "name が組織名称（株式会社等）だけ",
    "110": "検索方式(mode)は半角数字", "111": "mode は1桁", "112": "mode の値が正しくない（1 前方一致 / 2 部分一致）",
    "120": "検索対象(target)は半角数字", "121": "target は1桁", "122": "target の値が正しくない（1/2/3）",
    "130": "変更履歴(change)は半角数字", "131": "change は1桁", "132": "change は 0/1 以外",
    "140": "登記記録の閉鎖等(close)は半角数字", "141": "close は1桁", "142": "close は 0/1 以外",
    "150": "法人番号指定年月日開始日(from)は YYYY-MM-DD 形式", "151": "from が存在しない日付", "152": "from は 2015-10-05 以降",
    "160": "法人番号指定年月日終了日(to)は YYYY-MM-DD 形式", "161": "to が存在しない日付", "170": "from が to より後",
    "180": "検索結果件数が多く返せない。条件を足す",
}
INVOICE_ERRORS = {
    "0001": "登録番号が指定されていません", "0002": "登録番号は10件以内", "0003": "登録番号n に値が指定されていません",
    "0004": "登録番号は14桁（T＋13桁）", "0005": "登録番号は T＋数字13桁",
    "0101": "取得期間開始日が指定されていません", "0102": "from は YYYY-MM-DD 形式", "0103": "from が存在しない日付",
    "0104": "from は 2021-10-01 以降", "0201": "取得期間終了日が指定されていません", "0202": "to は YYYY-MM-DD 形式",
    "0203": "to が存在しない日付", "0204": "to が from より前", "0205": "取得期間が最大50日を超えている",
    "0301": "判定基準日(day)が指定されていません", "0302": "day は YYYY-MM-DD 形式", "0303": "day が存在しない日付",
    "0401": "人格区分(division)は半角数字", "0402": "division は1桁", "0403": "division の値が正しくない（1 個人 / 2 法人）",
    "0501": "応答形式(type)が指定されていません", "0502": "type は半角数字", "0503": "type は2桁", "0504": "type は 01/11/21 以外",
    "0601": "履歴情報要否(history)は半角数字", "0602": "history は1桁", "0603": "history は 0/1 以外",
    "0701": "分割番号(divide)は半角数字", "0702": "分割番号が範囲外",
}
HTTP_HINTS = {
    403: "同一アプリケーションIDでの短時間の大量アクセスによるアクセス制限中（公式）。間隔を空け、件数を減らし、時間をおいて再開する。解除の方法は公式に記載なし（問い合わせ先: 各Web-APIの問合せフォーム）",
    404: "アプリケーションIDが未登録・無効（公式）。または URL（バージョン・機能名）の誤り。法人番号用IDでインボイスAPIを呼んでいないかも確かめる",
    500: "国税庁側の障害（公式）。時間をおいて再試行。メンテナンス告知は法人番号公表サイトに載る",
}

HOUJIN_CSV_COLUMNS = [
    "sequenceNumber", "corporateNumber", "process", "correct", "updateDate", "changeDate", "name", "nameImageId", "kind",
    "prefectureName", "cityName", "streetNumber", "addressImageId", "prefectureCode", "cityCode", "postCode",
    "addressOutside", "addressOutsideImageId", "closeDate", "closeCause", "successorCorporateNumber", "changeCause",
    "assignmentDate", "latest", "enName", "enPrefectureName", "enCityName", "enAddressOutside", "furigana", "hihyoji",
]


class UsageError(Exception):
    pass


class ApiError(Exception):
    def __init__(self, status, body, hint):
        super().__init__(hint)
        self.status, self.body, self.hint = status, body, hint


# ───────── 入力の検査（形式だけ。検査桁は見ない） ─────────

def parse_date(s, label):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s or ""):
        raise UsageError("%s は YYYY-MM-DD の形式で指定してください（入力: %r）" % (label, s))
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:]))
    except ValueError:
        raise UsageError("%s は存在しない日付です（入力: %s）" % (label, s))


def split_numbers(raw, kind):
    nums = [x.strip() for x in (raw or "").replace("，", ",").split(",") if x.strip()]
    if not nums:
        raise UsageError("--number が空です")
    if len(nums) > MAX_NUMBERS:
        raise UsageError("番号は1回 %d 件までです（%d 件）。分けて呼んでください" % (MAX_NUMBERS, len(nums)))
    pat = r"\d{13}" if kind == "houjin" else r"T\d{13}"
    for n in nums:
        if not re.fullmatch(pat, n):
            if kind == "houjin":
                raise UsageError("法人番号は半角数字13桁です（入力: %r）。先頭の T や - は付けない" % n)
            raise UsageError("登録番号は T＋半角数字13桁です（入力: %r）。法人番号13桁の前に大文字の T を付ける" % n)
    return nums


def check_range(frm, to, minimum, label):
    f, t = parse_date(frm, "--from"), parse_date(to, "--to")
    if f < minimum:
        raise UsageError("--from は %s 以降です（%s の下限）" % (minimum.isoformat(), label))
    if t < f:
        raise UsageError("--to は --from 以降にしてください")
    if (t - f).days > MAX_DIFF_DAYS:
        raise UsageError("期間は --from から %d 日以内です（%d 日）。区切って呼んでください" % (MAX_DIFF_DAYS, (t - f).days))


def check_csv_list(val, allowed, label, maxn):
    items = [x.strip() for x in val.split(",") if x.strip()]
    if len(items) > maxn or any(i not in allowed for i in items):
        raise UsageError("%s は %s のうち最大 %d 個をカンマ区切りで指定します（入力: %r）" % (label, "/".join(allowed), maxn, val))


def check_address(val):
    if not re.fullmatch(r"(\d{2}|\d{5})", val):
        raise UsageError("--address は都道府県コード2桁（国外は 99）か、都道府県＋市区町村の5桁です。市区町村だけは不可（エラー 051）")


# ───────── 接続先 ─────────

def pick_base(env_name, default):
    base = os.environ.get(env_name, "").strip().rstrip("/") or default
    host = urllib.parse.urlparse(base)
    local = host.hostname in ("localhost", "127.0.0.1")
    if host.scheme != "https" and not (host.scheme == "http" and local):
        raise UsageError("%s は https か localhost だけ使えます（アプリケーションIDを平文で送らないため）: %s" % (env_name, base))
    return base


def get_app_id(api, dry):
    if api == "houjin":
        names = ["NTA_HOUJIN_APP_ID", "NTA_INVOICE_APP_ID"]   # インボイス用IDは法人番号APIにも使える（公式）
    else:
        names = ["NTA_INVOICE_APP_ID"]
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            if not re.fullmatch(r"\d{13}", v) and not dry:
                sys.stderr.write("注意: アプリケーションIDは13桁の数字のはずです（公式）。値が違う可能性があります\n")
            return v
    if dry:
        return None
    raise UsageError("環境変数 %s が未設定です。取得方法は references/app-id-and-terms.md（届出から発行まで2週間〜1か月ほど）。値をコードや会話に書かない" % names[0])


# ───────── 通信 ─────────

def build_url(api, path, params, app_id):
    base = pick_base("NTA_HOUJIN_BASE", HOUJIN_BASE) if api == "houjin" else pick_base("NTA_INVOICE_BASE", INVOICE_BASE)
    ver = HOUJIN_VER if api == "houjin" else INVOICE_VER
    q = [("id", app_id or "")] + [(k, v) for k, v in params if v not in (None, "")]
    return "%s/%s/%s?%s" % (base, ver, path, urllib.parse.urlencode(q, quote_via=urllib.parse.quote, safe=","))


def explain_error(api, status, body):
    table = HOUJIN_ERRORS if api == "houjin" else INVOICE_ERRORS
    hint = HTTP_HINTS.get(status, "")
    code_re = r"\b\d{3}\b" if api == "houjin" else r"\b\d{4}\b"
    found = []
    for m in re.finditer(code_re, body or ""):
        c = m.group(0)
        if c in table and c not in found:
            found.append(c)
    if status == 400 and found:
        hint = "; ".join("エラーコード %s: %s" % (c, table[c]) for c in found)
    elif status == 400:
        hint = "リクエスト条件の誤り。応答本文のエラーコードを references/errors.md の表と照らす"
    return hint or "想定外の HTTP ステータス。応答本文を確認"


def fetch(api, url, timeout):
    last = None
    for wait in (0,) + RETRY_WAITS:
        if wait:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": "nta-lookup/1.0 (+python-urllib)"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            raw = e.read() or b""
            body = decode_text(raw)
            if e.code >= 500:
                last = ApiError(e.code, body, explain_error(api, e.code, body))
                continue
            raise ApiError(e.code, body, explain_error(api, e.code, body))
        except (urllib.error.URLError, OSError) as e:
            last = ApiError(0, "", "通信できません: %s。ネットワーク・プロキシ・DNS を確認（外部通信が禁止された環境では実行できない）" % e)
    raise last


def decode_text(raw):
    for enc in ("utf-8", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", "replace")


# ───────── 応答の解釈 ─────────

def parse_houjin_xml(raw):
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise ApiError(200, decode_text(raw)[:300], "XML として読めません（%s）。エラー応答は CSV 形式で返る。本文を確認" % e)
    header = {k: (root.findtext(k) or "") for k in ("lastUpdateDate", "count", "divideNumber", "divideSize")}
    recs = []
    for c in root.findall("corporation"):
        recs.append({ch.tag: (ch.text or "").strip() for ch in c})
    return header, recs


def parse_invoice_json(raw):
    try:
        doc = json.loads(decode_text(raw))
    except ValueError as e:
        raise ApiError(200, decode_text(raw)[:300], "JSON として読めません（%s）。エラー応答は CSV 形式で返る。本文を確認" % e)
    header = {k: str(doc.get(k, "")) for k in ("lastUpdateDate", "count", "divideNumber", "divideSize")}
    recs = doc.get("announcement") or []
    if isinstance(recs, dict):
        recs = [recs]
    return header, recs


def run_query(api, path, params, args, app_id):
    """分割（divide）を順に取って (ヘッダー, 全レコード) を返す。--all が無ければ1回だけ。"""
    typ = "12" if api == "houjin" else "21"
    base_params = list(params) + [("type", typ)]
    divide, pages, records, header = max(1, getattr(args, "divide", 1)), 0, [], None
    while True:
        p = list(base_params)
        if divide > 1:
            p.append(("divide", str(divide)))
        url = build_url(api, path, p, app_id)
        raw = fetch(api, url, args.timeout)
        h, recs = parse_houjin_xml(raw) if api == "houjin" else parse_invoice_json(raw)
        header = header or h
        records.extend(recs)
        pages += 1
        size = int(h.get("divideSize") or 1)
        if not getattr(args, "all", False) or divide >= size:
            break
        if pages >= getattr(args, "max_pages", 100):
            sys.stderr.write("注意: --max-pages %d で打ち切りました（分割数 %d）。続きは --divide を使うか上限を上げる\n" % (getattr(args, "max_pages", 100), size))
            break
        divide += 1
        time.sleep(getattr(args, "sleep", 1.0))
    header["fetchedPages"] = str(pages)
    header["fetchedRecords"] = str(len(records))
    if not getattr(args, "all", False) and int(header.get("divideSize") or 1) > 1:
        sys.stderr.write("注意: 応答は %s 分割中の1つ目だけです（総件数 %s）。全部取るには --all\n" % (header["divideSize"], header["count"]))
    return header, records


# ───────── 出力 ─────────

def emit(header, records, args, api):
    if args.format == "csv":
        cols = HOUJIN_CSV_COLUMNS if api == "houjin" else None
        if cols is None:
            cols = []
            for r in records:
                for k in r:
                    if k not in cols:
                        cols.append(k)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(cols)
        for r in records:
            w.writerow([r.get(c, "") for c in cols])
        text = buf.getvalue()
    else:
        text = json.dumps({"header": header, "records": records}, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8-sig" if args.bom else "utf-8", newline="") as f:
            f.write(text)
        sys.stderr.write("%d 件を %s に書きました（総件数 %s）\n" % (len(records), args.output, header.get("count")))
    else:
        sys.stdout.write(text)


def note_missing(api, numbers, records):
    key = "corporateNumber" if api == "houjin" else "registratedNumber"
    got = {r.get(key) for r in records}
    missing = [n for n in numbers if n not in got]
    if missing:
        sys.stderr.write("応答に出てこなかった番号: %s（該当なしの可能性。意味づけは法的判断になるため、このスクリプトは断定しない）\n" % ", ".join(missing))


# ───────── サブコマンド ─────────

def build_request(args):
    cmd = args.cmd
    if cmd == "houjin-num":
        nums = split_numbers(args.number, "houjin")
        return "houjin", "num", [("number", ",".join(nums)), ("history", "1" if args.history else "0")], nums
    if cmd == "houjin-diff":
        check_range(args.frm, args.to, HOUJIN_DIFF_MIN, "法人番号 API の差分")
        p = [("from", args.frm), ("to", args.to)]
        if args.address:
            check_address(args.address); p.append(("address", args.address))
        if args.kind:
            check_csv_list(args.kind, ["01", "02", "03", "04"], "--kind", 4); p.append(("kind", args.kind))
        return "houjin", "diff", p, []
    if cmd == "houjin-name":
        if not args.name.strip():
            raise UsageError("--name が空です")
        if len(args.name) > 150:
            raise UsageError("--name は日本語150文字（英語表記検索は300文字）以内です")
        if args.target == "3" and re.search(r"[^\x20-\x7e]", args.name):
            raise UsageError("--target 3（英語表記）は半角英数記号で指定します。全角文字が含まれています")
        p = [("name", args.name), ("mode", args.mode), ("target", args.target), ("change", args.change), ("close", args.close)]
        if args.address:
            check_address(args.address); p.append(("address", args.address))
        if args.kind:
            check_csv_list(args.kind, ["01", "02", "03", "04"], "--kind", 4); p.append(("kind", args.kind))
        if args.assigned_from:
            if parse_date(args.assigned_from, "--assigned-from") < HOUJIN_ASSIGN_MIN:
                raise UsageError("--assigned-from は 2015-10-05 以降です（エラー 152）")
            p.append(("from", args.assigned_from))
        if args.assigned_to:
            parse_date(args.assigned_to, "--assigned-to"); p.append(("to", args.assigned_to))
        return "houjin", "name", p, []
    if cmd == "invoice-num":
        nums = split_numbers(args.number, "invoice")
        return "invoice", "num", [("number", ",".join(nums)), ("history", "1" if args.history else "0")], nums
    if cmd == "invoice-valid":
        nums = split_numbers(args.number, "invoice")
        parse_date(args.day, "--day")
        return "invoice", "valid", [("number", ",".join(nums)), ("day", args.day)], nums
    if cmd == "invoice-diff":
        check_range(args.frm, args.to, INVOICE_DIFF_MIN, "インボイス API の差分")
        p = [("from", args.frm), ("to", args.to)]
        if args.division:
            p.append(("division", args.division))
        return "invoice", "diff", p, []
    raise UsageError("不明なサブコマンド: " + cmd)


def main(argv=None):
    ap = argparse.ArgumentParser(description="国税庁 法人番号 Web-API / 適格請求書発行事業者公表 Web-API の照会（標準ライブラリだけ）。アプリケーションIDは環境変数から読む。",
                                 epilog="終了コード: 0 正常 / 1 API・通信の失敗 / 2 引数・環境変数の誤り")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, divide=True):
        p.add_argument("--dry-run", action="store_true", help="通信せず、組み立てた URL を表示する（IDは伏せ字）")
        p.add_argument("--format", choices=["json", "csv"], default="json", help="出力形式（既定 json）")
        p.add_argument("-o", "--output", help="出力ファイル（UTF-8）。省略時は標準出力")
        p.add_argument("--bom", action="store_true", help="CSV/JSON を BOM つきで書く（Excel で開く用）")
        p.add_argument("--timeout", type=float, default=30.0, help="1回の通信の待ち秒数（既定 30）")
        if divide:
            p.add_argument("--all", action="store_true", help="分割された応答を divideSize まで全部取る")
            p.add_argument("--divide", type=int, default=1, help="取り始める分割番号（既定 1。中断した続きから取る用）")
            p.add_argument("--max-pages", type=int, default=100, help="--all の最大リクエスト数（既定 100）")
            p.add_argument("--sleep", type=float, default=1.0, help="--all のリクエスト間隔の秒（既定 1.0。短時間の大量アクセスは禁止・403 の原因）")

    p = sub.add_parser("houjin-num", help="法人番号から法人情報（最大10件）"); common(p, False)
    p.add_argument("--number", required=True, help="13桁の法人番号。カンマ区切りで最大10件")
    p.add_argument("--history", action="store_true", help="変更履歴も取る（history=1）")

    p = sub.add_parser("houjin-name", help="法人名から検索（Ver.2.0 以降）"); common(p)
    p.add_argument("--name", required=True, help="商号又は名称（URLエンコードはこちらでする）")
    p.add_argument("--mode", choices=["1", "2"], default="1", help="1 前方一致（既定。株式会社等を除いた名前の先頭）/ 2 部分一致")
    p.add_argument("--target", choices=["1", "2", "3"], default="1", help="1 JIS第一第二水準のあいまい検索（既定）/ 2 JIS第一〜第四水準の完全一致 / 3 英語表記")
    p.add_argument("--address", help="都道府県コード2桁（国外99）か 5桁（都道府県＋市区町村）")
    p.add_argument("--kind", help="法人種別 01 国の機関 02 地方公共団体 03 設立登記法人 04 外国会社等・その他（カンマ区切り最大4）")
    p.add_argument("--change", choices=["0", "1"], default="0", help="1 で旧名称も検索対象（既定 0）。旧名称で当たると最新情報は返らない")
    p.add_argument("--close", choices=["0", "1"], default="1", help="0 で登記記録の閉鎖等を除く（既定 1＝含める）")
    p.add_argument("--assigned-from", help="法人番号指定年月日の開始日 YYYY-MM-DD（2015-10-05 以降）")
    p.add_argument("--assigned-to", help="法人番号指定年月日の終了日")

    p = sub.add_parser("houjin-diff", help="期間（更新年月日）を指定して差分を取る。最大50日"); common(p)
    p.add_argument("--from", dest="frm", required=True, help="開始日 YYYY-MM-DD（2015-12-01 以降）")
    p.add_argument("--to", required=True, help="終了日 YYYY-MM-DD（開始日から50日以内）")
    p.add_argument("--address", help="都道府県コード2桁か5桁")
    p.add_argument("--kind", help="法人種別（カンマ区切り最大4）")

    p = sub.add_parser("invoice-num", help="登録番号（T＋13桁）で照会（最大10件）"); common(p, False)
    p.add_argument("--number", required=True, help="T＋13桁。カンマ区切りで最大10件")
    p.add_argument("--history", action="store_true", help="登録・取消・失効の履歴も取る")

    p = sub.add_parser("invoice-valid", help="登録番号と判定基準日で、その日付に基づく直近の情報を取る"); common(p, False)
    p.add_argument("--number", required=True, help="T＋13桁。カンマ区切りで最大10件")
    p.add_argument("--day", required=True, help="判定基準日 YYYY-MM-DD")

    p = sub.add_parser("invoice-diff", help="期間（更新年月日）を指定して差分を取る。最大50日"); common(p)
    p.add_argument("--from", dest="frm", required=True, help="開始日 YYYY-MM-DD（2021-10-01 以降）")
    p.add_argument("--to", required=True, help="終了日 YYYY-MM-DD（開始日から50日以内）")
    p.add_argument("--division", choices=["1", "2"], help="1 個人 / 2 法人（省略で両方）")

    args = ap.parse_args(argv)
    try:
        api, path, params, numbers = build_request(args)
        app_id = get_app_id(api, args.dry_run)
        if args.dry_run:
            typ = "12" if api == "houjin" else "21"
            url = build_url(api, path, list(params) + [("type", typ)], "IDPLACEHOLDER").replace("IDPLACEHOLDER", MASK)
            print("GET " + url)
            print("（--dry-run: 通信していません。環境変数 %s は%s）" % ("NTA_HOUJIN_APP_ID" if api == "houjin" else "NTA_INVOICE_APP_ID", "設定済み" if app_id else "未設定"))
            return EXIT_OK
        header, records = run_query(api, path, params, args, app_id)
        emit(header, records, args, api)
        if numbers:
            note_missing(api, numbers, records)
        return EXIT_OK
    except UsageError as e:
        sys.stderr.write("入力エラー: %s\n" % e)
        return EXIT_USAGE
    except ApiError as e:
        sys.stderr.write("失敗: HTTP %s\n原因の候補: %s\n" % (e.status or "-", e.hint))
        if e.body:
            sys.stderr.write("応答本文（先頭300字）: %s\n" % e.body[:300].replace(os.environ.get("NTA_HOUJIN_APP_ID", "\0"), "＊＊＊＊").replace(os.environ.get("NTA_INVOICE_APP_ID", "\0"), "＊＊＊＊"))
        return EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())

=== FILE: scripts/selftest_mock.py ===
#!/usr/bin/env python3
"""nta_lookup.py の自己検証。手元にモックの国税庁 Web-API を立てて、分割取得・エラー・伏せ字を確かめる。

本物には接続しない（127.0.0.1 だけ）。Python 3.9 以上・標準ライブラリだけ。
モックの形式は公式仕様書（references/api-spec.md の出典）の説明に合わせたもの。実サーバーの応答との一致は未検証。

  python3 scripts/selftest_mock.py     # 終了コード 0 で全部合格
"""
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "nta_lookup.py")
GOOD_ID = "1234567890123"
FAILS = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name)
    if not ok:
        FAILS.append(name)
        print("     " + str(detail)[:400])


class State:
    def __init__(self):
        self.log = []          # (path, params)
        self.fail500 = 0       # 次の n 回は 500 を返す


def houjin_xml(count, divide, size, rows):
    items = "".join(
        "<corporation><sequenceNumber>%d</sequenceNumber><corporateNumber>%s</corporateNumber><process>01</process>"
        "<name>%s</name><kind>301</kind><prefectureName>東京都</prefectureName><latest>1</latest></corporation>" % r
        for r in rows)
    return ('<?xml version="1.0" encoding="UTF-8"?><corporations><lastUpdateDate>2026-10-22</lastUpdateDate><count>%d</count>'
            "<divideNumber>%d</divideNumber><divideSize>%d</divideSize>%s</corporations>" % (count, divide, size, items)).encode("utf-8")


def make_handler(st):
    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype="text/plain; charset=UTF-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
            st.log.append((u.path, q))
            if st.fail500 > 0:
                st.fail500 -= 1
                return self.send(500, "システムエラー".encode("utf-8"))
            if q.get("id") == "0000000000000":
                return self.send(404, b"")
            if q.get("id") == "9999999999999":
                return self.send(403, b"")
            if q.get("id") != GOOD_ID:
                return self.send(404, b"")
            parts = u.path.strip("/").split("/")
            ver, fn = parts[0], parts[1]
            if ver == "4":      # 法人番号
                if fn == "num":
                    nums = q.get("number", "").split(",")
                    if len(nums) > 10:
                        return self.send(400, '"400","041","法人番号は10件以内で指定してください。"'.encode("utf-8"))
                    rows = [(i + 1, n, "株式会社テスト%d" % (i + 1)) for i, n in enumerate(nums) if n != "9999999999990"]
                    return self.send(200, houjin_xml(len(rows), 1, 1, rows), "application/xml")
                if fn == "name":
                    if q.get("mode") == "9":
                        return self.send(400, '400,112,"商号又は名称検索方式の項目値が正しくありません。"'.encode("utf-8"))
                    div = int(q.get("divide", "1"))
                    # 4500 件を 2000 件ずつ 3 分割
                    total, size = 4500, 3
                    if div > size:
                        return self.send(400, '400,091,"分割番号はZZZZ9以下で指定してください。"'.encode("utf-8"))
                    start = (div - 1) * 2000
                    n = min(2000, total - start)
                    rows = [(start + i + 1, "%013d" % (start + i + 1), "名前" + urllib.parse.unquote(q.get("name", ""))) for i in range(n)]
                    return self.send(200, houjin_xml(total, div, size, rows), "application/xml")
                if fn == "diff":
                    if q.get("address") == "99999":
                        return self.send(400, '400,052,"所在地の項目値が正しくありません。"'.encode("utf-8"))
                    if q.get("from", "") < "2015-12-01":
                        return self.send(400, '400,013,"取得期間開始日は2015-12-01以降を指定してください。"'.encode("utf-8"))
                    return self.send(200, houjin_xml(1, 1, 1, [(1, "1000000000001", "差分株式会社")]), "application/xml")
            if ver == "1":      # インボイス
                def doc(div, size, total, nums):
                    return json.dumps({"lastUpdateDate": "2026-10-22", "count": str(total), "divideNumber": str(div), "divideSize": str(size),
                                       "announcement": [{"sequenceNumber": str(i + 1), "registratedNumber": n, "process": "01", "latest": "1",
                                                         "registrationDate": "2023-10-01", "name": "株式会社インボイス公表", "expireDate": "", "disposalDate": ""}
                                                        for i, n in enumerate(nums)]}, ensure_ascii=False).encode("utf-8")
                if fn in ("num", "valid"):
                    nums = [n for n in q.get("number", "").split(",") if n != "T0000000000000"]
                    if fn == "valid" and not q.get("day"):
                        return self.send(400, '400,0301,"判定基準日が指定されていません。"'.encode("utf-8"))
                    return self.send(200, doc(1, 1, len(nums), nums), "application/json")
                if fn == "diff":
                    div = int(q.get("divide", "1"))
                    total, size = 1200, 3
                    start = (div - 1) * 500
                    n = min(500, total - start)
                    return self.send(200, doc(div, size, total, ["T%013d" % (start + i + 1) for i in range(n)]), "application/json")
            return self.send(404, b"")
    return H


def run(port, args, env_extra=None, base_env=True):
    env = {"PATH": os.environ.get("PATH", ""), "NTA_HOUJIN_BASE": "http://127.0.0.1:%d" % port,
           "NTA_INVOICE_BASE": "http://127.0.0.1:%d" % port}
    if base_env:
        env["NTA_HOUJIN_APP_ID"] = GOOD_ID
        env["NTA_INVOICE_APP_ID"] = GOOD_ID
    env.update(env_extra or {})
    return subprocess.run([sys.executable, "-I", SCRIPT] + args, capture_output=True, text=True, env=env, timeout=60)


def main():
    st = State()
    srv = http.server.HTTPServer(("127.0.0.1", 0), make_handler(st))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    tmp = tempfile.mkdtemp()

    # 1. --dry-run: 通信ゼロ・IDが出ない
    n0 = len(st.log)
    r = run(port, ["houjin-num", "--number", "5111101000006", "--dry-run"])
    check("dry-run は通信せず ID を出さない", r.returncode == 0 and len(st.log) == n0 and GOOD_ID not in r.stdout + r.stderr and "＊＊＊＊" in r.stdout, (r.stdout, r.stderr))
    r = run(port, ["invoice-num", "--number", "T8040001999011", "--dry-run"], base_env=False)
    check("dry-run は ID 未設定でも動き、未設定と表示する", r.returncode == 0 and "未設定" in r.stdout, (r.stdout, r.stderr))

    # 2. 環境変数が無い → 終了コード2
    r = run(port, ["houjin-num", "--number", "5111101000006"], base_env=False)
    check("ID 未設定は終了コード2で取得先を案内", r.returncode == 2 and "NTA_HOUJIN_APP_ID" in r.stderr, r.stderr)

    # 3. 法人番号の取得（XML を解釈して JSON に）
    r = run(port, ["houjin-num", "--number", "5111101000006,4111101000007"])
    doc = json.loads(r.stdout) if r.returncode == 0 else {}
    check("houjin-num が2件を JSON で返す", r.returncode == 0 and len(doc.get("records", [])) == 2 and doc["header"]["count"] == "2", (r.stdout, r.stderr))
    check("type=12 と history=0 を付けて送る", st.log[-1][1].get("type") == "12" and st.log[-1][1].get("history") == "0", st.log[-1])
    r = run(port, ["houjin-num", "--number", "5111101000006,9999999999990"])
    check("応答に無い番号を知らせる（断定しない）", "9999999999990" in r.stderr and "断定しない" in r.stderr, r.stderr)

    # 4. 入力検査（通信前に弾く）
    n0 = len(st.log)
    r = run(port, ["houjin-num", "--number", ",".join(["5111101000006"] * 11)])
    check("11件は通信前に弾く", r.returncode == 2 and "10" in r.stderr and len(st.log) == n0, r.stderr)
    r = run(port, ["invoice-num", "--number", "8040001999011"])
    check("T 無しの登録番号は弾く", r.returncode == 2 and "T" in r.stderr and len(st.log) == n0, r.stderr)
    r = run(port, ["houjin-diff", "--from", "2026-01-01", "--to", "2026-03-01"])
    check("51日以上の期間は弾く", r.returncode == 2 and "50" in r.stderr and len(st.log) == n0, r.stderr)
    r = run(port, ["houjin-diff", "--from", "2015-11-30", "--to", "2015-12-02"])
    check("法人番号 diff の下限(2015-12-01)未満は弾く", r.returncode == 2 and "2015-12-01" in r.stderr, r.stderr)
    r = run(port, ["invoice-diff", "--from", "2021-09-30", "--to", "2021-10-02"])
    check("インボイス diff の下限(2021-10-01)未満は弾く", r.returncode == 2 and "2021-10-01" in r.stderr, r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--address", "131"])
    check("市区町村だけ/3桁の address は弾く", r.returncode == 2 and "address" in r.stderr, r.stderr)

    # 5. 名称検索: URL エンコードと分割取得
    r = run(port, ["houjin-name", "--name", "国税", "--mode", "2", "--all", "--sleep", "0", "-o", os.path.join(tmp, "n.json")])
    got = json.load(open(os.path.join(tmp, "n.json"), encoding="utf-8")) if r.returncode == 0 else {}
    divs = [q.get("divide", "1") for p, q in st.log[-3:]]
    check("4500件を3分割で全部取る", r.returncode == 0 and len(got.get("records", [])) == 4500 and divs == ["1", "2", "3"], (r.stderr, divs))
    check("name は UTF-8 で URL エンコードされて届く", st.log[-1][1].get("name") == "国税" and st.log[-1][1].get("mode") == "2", st.log[-1])
    check("2回目以降だけ divide を付ける（1回目は付けない）", "divide" not in st.log[-3][1], st.log[-3])
    r = run(port, ["houjin-name", "--name", "国税", "--sleep", "0"])
    check("--all 無しは1回だけ取り、分割を注意する", r.returncode == 0 and "--all" in r.stderr and json.loads(r.stdout)["header"]["fetchedPages"] == "1", r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--all", "--max-pages", "2", "--sleep", "0"])
    check("--max-pages で打ち切り、注意する", r.returncode == 0 and "打ち切り" in r.stderr and json.loads(r.stdout)["header"]["fetchedPages"] == "2", r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--all", "--sleep", "0", "--format", "csv", "--bom", "-o", os.path.join(tmp, "n.csv")])
    raw = open(os.path.join(tmp, "n.csv"), "rb").read()
    check("CSV は BOM つき UTF-8 で列名が1行目", raw.startswith(b"\xef\xbb\xbf") and raw.decode("utf-8-sig").splitlines()[0].startswith("sequenceNumber,corporateNumber"), raw[:80])

    # 6. インボイス
    r = run(port, ["invoice-valid", "--number", "T8040001999011,T0000000000000", "--day", "2026-10-23"])
    doc = json.loads(r.stdout) if r.returncode == 0 else {}
    check("invoice-valid が JSON を返し、無い番号を知らせる", r.returncode == 0 and len(doc["records"]) == 1 and "T0000000000000" in r.stderr, (r.stdout, r.stderr))
    check("valid に type=21 と day を付ける", st.log[-1][0] == "/1/valid" and st.log[-1][1].get("type") == "21" and st.log[-1][1].get("day") == "2026-10-23", st.log[-1])
    r = run(port, ["invoice-diff", "--from", "2026-10-01", "--to", "2026-10-03", "--all", "--sleep", "0"])
    check("invoice-diff を 500件ずつ3分割で1200件取る", r.returncode == 0 and len(json.loads(r.stdout)["records"]) == 1200, r.stderr)

    # 7. エラー
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": "0000000000000"})
    check("404 は ID 無効の可能性を案内（再試行しない）", r.returncode == 1 and "404" in r.stderr and "無効" in r.stderr, r.stderr)
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": "9999999999999"})
    check("403 はアクセス制限と案内", r.returncode == 1 and "アクセス制限" in r.stderr, r.stderr)
    r = run(port, ["houjin-name", "--name", "国税", "--no-such-option"])
    check("未知のオプションは argparse が終了コード2", r.returncode == 2, r.stderr)
    r = run(port, ["houjin-diff", "--from", "2026-10-01", "--to", "2026-10-02", "--address", "99999"])
    check("400 の本文からエラーコードを引いて原因を出す", r.returncode == 1 and "エラーコード 052" in r.stderr and "400" in r.stderr, r.stderr)
    st.fail500 = 1
    n0 = len(st.log)
    r = run(port, ["houjin-num", "--number", "5111101000006"])
    check("500 は1回再試行して成功する", r.returncode == 0 and len(st.log) - n0 == 2, (r.returncode, r.stderr))
    st.fail500 = 10
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": GOOD_ID})
    st.fail500 = 0
    check("500 が続けば終了コード1で国税庁側の障害と案内", r.returncode == 1 and "障害" in r.stderr, r.stderr)

    # 8. ID が出力に出ない
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_APP_ID": "0000000000000"})
    check("失敗時の出力にも ID が出ない", "0000000000000" not in r.stdout + r.stderr, r.stderr)

    # 9. https 以外の接続先は拒否（ID の平文送信防止）
    r = run(port, ["houjin-num", "--number", "5111101000006"], {"NTA_HOUJIN_BASE": "http://example.com"})
    check("http の外部ホストは拒否", r.returncode == 2 and "https" in r.stderr, r.stderr)

    # 10. --help
    r = subprocess.run([sys.executable, "-I", SCRIPT, "--help"], capture_output=True, text=True)
    check("--help が終了コード0", r.returncode == 0 and "houjin-num" in r.stdout and "invoice-valid" in r.stdout)

    srv.shutdown()
    print("\n" + ("OK 全部通りました" if not FAILS else "失敗 %d 件: %s" % (len(FAILS), FAILS)))
    return 1 if FAILS else 0


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
