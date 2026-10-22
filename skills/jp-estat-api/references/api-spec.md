# e-Stat API 仕様の要点（バージョン 3.0）

確認日: 2026-10-21。90 日（2027-01-19）を過ぎたら公式を読み直す。
出典（一次情報）:
- API 仕様 3.0（HTML）: https://www.e-stat.go.jp/api/api-info/e-stat-manual3-0
- API 仕様の一覧（版・エンドポイント）: https://www.e-stat.go.jp/api/api-info/api-spec
- 利用ガイド（利用登録・appId）: https://www.e-stat.go.jp/api/api-info/api-guide
- よくあるご質問: https://www.e-stat.go.jp/api/api-dev/faq
- APIの使い方: https://www.e-stat.go.jp/api/api-dev/how_to_use

仕様の全文は上の HTML が正。ここに無い機能（データセット登録 postDataset、一括取得 getStatsDatas、データカタログ）は対象外。

## 1. 利用登録と appId

1. e-Stat のユーザ登録をする（https://www.e-stat.go.jp/mypage/user/preregister）。
2. マイページの「API機能（アプリケーションID発行）」で appId を発行する。名称・URL・概要を入力する。公開サイトで使わないなら URL は `http://test.localhost/` のようなローカルアドレスでよい。登録内容は後から変更できる（変更しても ID は変わらない）。
3. 取得できる appId は 3 つまで（FAQ Q3-x）。ID を差し替えるときは削除して再発行で、古い ID は使えなくなる。
4. appId は第三者に譲渡・貸与しない（API 利用規約 第3条）。スクリプトやチャットに直接貼らず、環境変数 `ESTAT_APP_ID` に入れる。

## 2. バージョンとエンドポイント

- 現行は **3.0**（2019-07-26）。2.1・2.0・1.0 も残っている。ホストは全版 `api.e-stat.go.jp`。HTTPS は 2018-01-04 から全版で使える（HTTP も動く）。
- 基底 URL: `https://api.e-stat.go.jp/rest/3.0/app/`
- 形式は URL で選ぶ。メソッドはすべて GET、パラメータ値は UTF-8 で URL エンコードする（コード中の `#` は `%23`）。

| 形式 | 例（getStatsData） |
|---|---|
| XML（既定） | `/rest/3.0/app/getStatsData?...` |
| JSON | `/rest/3.0/app/json/getStatsData?...` |
| JSONP | `/rest/3.0/app/jsonp/getStatsData?...`（`callback` 必須） |
| CSV | `/rest/3.0/app/getSimpleStatsData?...`（getSimpleStatsList・getSimpleMetaInfo も同様） |

- `Accept-Encoding: gzip` を送ると gzip で返る（自分で解凍する）。
- 同梱の `scripts/estat_fetch.py` は JSON を使う（記号・注記・名称を取りこぼさないため）。

## 3. 3 つの関数

### getStatsList（統計表を探す）

| パラメータ | 意味 | 既定 |
|---|---|---|
| appId | 必須 | |
| searchWord | 表題・メタ情報のキーワード。AND / OR / NOT 可 | |
| surveyYears / openYears | 調査年・公開年。`yyyy` `yyyymm` `yyyymm-yyyymm` | |
| statsCode | 5 桁=府省、8 桁=政府統計コード | |
| statsField | 統計分野。2 桁=大分類、4 桁=小分類 | |
| collectArea | 1 全国 / 2 都道府県 / 3 市区町村 | |
| searchKind | 1 統計情報 / 2 小地域・地域メッシュ | 1 |
| statsNameList | `Y` で統計名の一覧（表ではなく調査名） | |
| startPosition / limit | 開始位置（1 始まり）と件数 | 1 / 100000 |
| updatedDate | 更新日 | |

応答: `GET_STATS_LIST.DATALIST_INF` に `NUMBER`（総数）、`RESULT_INF`（`FROM_NUMBER` `TO_NUMBER` `NEXT_KEY`）、表ごとの `TABLE_INF`（属性 `@id` が **statsDataId**）。`TABLE_INF` に `STAT_NAME` `GOV_ORG` `STATISTICS_NAME` `TITLE` `CYCLE` `SURVEY_DATE` `OPEN_DATE` `UPDATED_DATE` など。

### getMetaInfo（表の次元とコードを見る）

必須は `appId` と `statsDataId`。応答の `METADATA_INF.CLASS_INF.CLASS_OBJ` が次元ごとにあり、`@id` は次のどれか: `tab`（表章項目）・`cat01`〜`cat15`（分類事項）・`area`（地域）・`time`（時間軸）。各 `CLASS` に `@code` `@name` `@level` `@unit` `@parentCode`。**getStatsData で絞り込むコードはここで調べる。**

### getStatsData（統計データ）

`statsDataId` か `dataSetId` のどちらか 1 つが必須（両方・どちらも無しはエラー）。

| パラメータ | 意味 | 既定・上限 |
|---|---|---|
| cdTab / cdCat01〜15 / cdArea / cdTime | カンマ区切りのコードで絞る | 1 パラメータにつき **100 個まで**（超えると STATUS 105） |
| cdXxxFrom / cdXxxTo | コード範囲の始点・終点（片方だけも可） | |
| lvTab / lvCat01〜15 / lvArea / lvTime | 階層レベル。`X` `X-X` `-X` `X-` | |
| startPosition | 開始位置（1 始まり）。前の応答の NEXT_KEY を入れる | 1 |
| limit | 1 回に返す件数 | 100000 |
| metaGetFlg | `Y` でメタ情報も返す（CSV では常に N） | Y |
| cntGetFlg | `Y` で件数だけ返す | N |
| annotationGetFlg / explanationGetFlg | 注釈・解説を含める | Y |
| replaceSpChar | 特殊文字の置換。0 しない / 1 を 0 に / 2 を空文字に / 3 を `NA` に | 0 |
| sectionHeaderFlg | CSV のみ。1 見出しあり / 2 なし | 1 |

- 同じ次元の lv と cd は AND。`min` `max` はその次元の最小・最大コードを指す特別な値で、他のコードとカンマで並べられない。
- パラメータ名は **`replaceSpChar`**（s なし）。
- 値のコードは getMetaInfo の `@code`。

## 4. 件数の上限と続きの取り方

- 1 回の取得は最大 **10 万件**（FAQ Q5-7「一度に最大で10万件のデータを返却します」）。`limit` の既定も 100,000。
- 超える分があると `STATISTICAL_DATA.RESULT_INF.NEXT_KEY` が付く。その値を次の `startPosition` に入れて繰り返す。`NEXT_KEY` が無くなったら終わり。
- `RESULT_INF.TOTAL_NUMBER` は全体の件数、`FROM_NUMBER`〜`TO_NUMBER` は今回の範囲。最後に取得行数と TOTAL_NUMBER を突き合わせる。
- 仕様ページには getStatsData の件数上限の別記が無い（100,000 の明記は FAQ と、一括取得 API の「全体で 100000 件」のみ）。迷ったら cd* と lv* で絞ってから取る。
- アクセス回数の上限は「現在のところない」（FAQ Q1-3）。ただし短時間の大量アクセスは規約で禁止、負荷に応じて制限されうる（terms-and-credit.md）。ページ間は 1 秒ほど空ける。

## 5. 応答の構造（JSON）

- XML の要素 → キー、属性 → `@` 付きのキー、属性を持つ要素の本文 → `$` キー。同名の繰り返しは配列。**要素が 1 つだけのとき配列でなく単独のオブジェクトで返ることがある**ので、必ず「配列でなければ 1 要素の配列にする」処理を入れる。
- 全角は Unicode エスケープされる（`json.loads` が戻す）。
- getStatsData の骨格:

```json
{"GET_STATS_DATA": {
  "RESULT": {"STATUS": 0, "ERROR_MSG": "正常に終了しました。", "DATE": "..."},
  "STATISTICAL_DATA": {
    "RESULT_INF": {"TOTAL_NUMBER": 5, "FROM_NUMBER": 1, "TO_NUMBER": 2, "NEXT_KEY": 3},
    "TABLE_INF": {"@id": "…", "TITLE": {"@no": "…", "$": "…"}},
    "CLASS_INF": {"CLASS_OBJ": [{"@id": "area", "@name": "地域", "CLASS": [{"@code": "13000", "@name": "東京都"}]}]},
    "DATA_INF": {
      "NOTE": [{"@char": "-", "$": "…"}],
      "ANNOTATION": [{"@annotation": "J1", "$": "…"}],
      "VALUE": [{"@tab": "001", "@cat01": "000", "@area": "13000", "@time": "2020000000", "@unit": "人", "$": "13960000"}]}}}}
```

- `VALUE` の属性は `@tab` `@cat01`〜`@cat15` `@area` `@time` `@unit` `@annotation`（該当するものだけ付く）。セルの値は `$`。**`$` は文字列**で、数値とは限らない。
- `metaGetFlg=N` のページには `CLASS_INF` が付かない。名称（コード→名前）は最初のページの `CLASS_INF` から引く。`NOTE` `ANNOTATION` は応答ごとに付くので、ページをまたいで集める。
- 件数が 0、または `cntGetFlg=Y` のとき `DATA_INF` は無い。

## 6. 欠損・秘匿の記号

仕様が定義しているのは「`DATA_INF.NOTE` に記号ごとの説明が付く（`@char` が記号）」ことまで。記号の意味は**統計表ごとに違う**ので、その表の `NOTE` と注記を正とする。

- 仕様ページの例に出る記号は `*` `-` `...` `X`。`-` は「該当数字が皆無のもの、又は数字が得られないもの」、`X` は「数字が秘匿されているもの」と説明されている（例の表では `...` と `X` の説明が空のものもある）。
- 統計ごとの定義の例（https://www.e-stat.go.jp/help/data-definition-information/about-recorded-data 、確認日 2026-10-21）: 農林業センサス・漁業センサスの `-` は「調査は行ったが事実のないもの」、`X` は「統計数値を公表しないもの」、`…` は「事実不詳又は調査を欠くもの」、`0` は「単位に満たないもの」。国勢調査の小地域集計では `@` が合算地域、`*` が秘匿地域。
- `***` はこの確認では一次情報で定義を確認できなかった。**意味を断定せず、その表の NOTE と統計表の注記を見る。**
- `-` の「ゼロ」と「データなし」は表によって違う。0 として合計しない。
- 「0」でも「単位未満」のことがある。合計は四捨五入や不詳の分で内訳の和と一致しないことがある。
- `replaceSpChar` を 1・2・3 にすると記号が失われて元の区別がつかなくなる。取得時は **0（既定）** のまま取り、整形で扱いを決める。

## 7. STATUS（エラーコード）

`RESULT.STATUS` が 0〜2 なら成功、100 以上がエラー。HTTP ステータスも併せて返る。

| STATUS | HTTP | 意味 | 次の手 |
|---|---|---|---|
| 0 | 200 | 正常に終了 | |
| 1 | 200 | 正常終了だが該当データなし | 絞り込みコードを meta で確かめ直す |
| 2 | 200 | （一括取得のみ）一部の依頼で該当なし | |
| 100 | 403 | 認証に失敗（appId） | appId の誤り・削除済み・空白を確認 |
| 101 | 400 | 必須パラメータが無い | statsDataId など |
| 102 | 400 | 値が正しくない | コード・limit・startPosition を確認 |
| 103 | 400 | 値が長すぎる | |
| 104 | 400 | 使えない文字 | URL エンコードを確認 |
| 105 | 400 | 値が多すぎる（100 個以内） | コードを分割 |
| 200〜203 | 500 | e-Stat 側の DB エラー | 時間をおいて再実行 |
| 299 | 500 | 予期しないエラー | 時間をおいて再実行、続くなら問い合わせ |
| 300 | 400 | 指定 ID のデータが無い | statsDataId を getStatsList で調べ直す |
| 301〜303 | | データセット登録関連 | 対象外 |
| 400 | 200 | （一括取得のみ）全体で 100000 件超 | |
| 401 | 500 | （一括取得のみ）依頼のどれかでエラー | |

HTTP が 200 でも STATUS はエラーのことがある。必ず STATUS を見る。
