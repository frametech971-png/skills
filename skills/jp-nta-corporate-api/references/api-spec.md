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
