<!-- jp-estat-api v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-estat-api（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-estat-api
description: >-
  政府統計の総合窓口 e-Stat の API で日本の公的統計を取得し、CSV に整えて出典つきで集計する（統計表の検索、メタ情報、統計データの取得、NEXT_KEY のページング、欠損・秘匿記号の扱い）。「e-Stat API で都道府県別の人口を取得して」「統計表ID の探し方を教えて」「国勢調査のデータを CSV にして」「appId の取り方は」「値が - や … になっているのは何」「取得件数の上限を超えるときは」と頼まれたときに使う。appId は環境変数から読み、実在しない統計表ID・コードは作らない。Keywords: e-Stat API, statsDataId, getStatsData, getStatsList, getMetaInfo, appId, NEXT_KEY, 政府統計, 国勢調査。統計の解釈・政策提言、民間データ、画面からの手動ダウンロード手順だけの案内は対象外。
license: MIT
compatibility: "scripts は Python 3.9 以上（標準ライブラリのみ）。実行には外部通信（api.e-stat.go.jp）と e-Stat の appId が要る。通信できない環境では URL の組み立てと手順の案内に切り替える。"
metadata:
  version: "1.0.0"
  author: frametech
---

# e-Stat API で日本の公的統計を取る

目的: e-Stat API で統計表を探し、条件で絞って全件取得し、欠損記号を残した CSV にして、出典つきで集計する。
入力: 知りたい統計（例「都道府県別の人口」）、年・地域などの条件、または statsDataId。appId は環境変数 `ESTAT_APP_ID`。
出力: 取得に使った統計表ID・絞り込み条件・CSV のパス・集計結果・出典表記・「要確認」の一覧。

確認日から 90 日を過ぎたら、`references/` の出典 URL（公式）を読み直してから答える。API の版・上限・記号の意味は変わりうる。

## 1. 先に確かめること

- **appId があるか。** 無いときは取り方を案内する（`references/api-spec.md` §1: ユーザ登録 → マイページの「API機能（アプリケーションID発行）」。最大 3 つ）。appId をチャットに貼らせない。環境変数 `ESTAT_APP_ID` に入れてもらい、貼られたら「伏せて使い、共有しない」と伝える。
- **通信とシェルが使えるか。** 使えない環境では §5 の代替に進む。
- 統計表ID（statsDataId）が分からなければ §2、分かっていれば §3 から。

## 2. 統計表を探す（statsDataId）

```
python3 scripts/estat_fetch.py list --search-word 人口 --survey-years 2020 --collect-area 2
```

- 出力は statsDataId・政府統計名・表題・調査年月・更新日。候補を 3〜5 件に絞って見せ、**ユーザーに選んでもらう**。似た表が多い（男女別・年齢別・世帯別）ので、勝手に決めない。
- 国勢調査は `--stats-code 00200521`（例）。統計名で探すなら `--search-word`（AND/OR/NOT 可）。
- ID を推測で書かない。見つからなければ検索語を変える案を出す。

## 3. 表の次元とコードを見る

```
python3 scripts/estat_fetch.py meta --stats-data-id <statsDataId>
```

次元は `tab`（表章項目）・`cat01`〜（分類）・`area`（地域）・`time`（時間軸）。絞り込みに使うコードはここに出たものだけを使う。「総数」と内訳が同じ次元に並ぶ表では、足し合わせると二重に数えるので、総数と内訳を混ぜない。地域には全国・都道府県・市区町村が同居する表が多い（絞らずに合計しない）。

## 4. 取得して CSV にする

まず `--dry-run` で URL を確かめる（通信しない・appId は伏せる）。

```
python3 scripts/estat_fetch.py data --stats-data-id <statsDataId> --cd-area 13000,27000 --cd-time 2020000000 --out population.csv --dry-run
python3 scripts/estat_fetch.py data --stats-data-id <statsDataId> --cd-area 13000,27000 --cd-time 2020000000 --out population.csv
```

- 他の絞り込みは `--cd-tab` `--cd-cat01`、それ以外は `--param lvArea=2` のように足す。1 つのコード指定は 100 個まで。
- 1 回の取得は最大 10 万件。超える分は `NEXT_KEY` を `startPosition` に入れて続きを取る。スクリプトが全ページ分を自動でたどる（間隔 1 秒。短時間の大量アクセスは規約違反）。
- `--out` は全ページ成功してから書く。失敗しても既存ファイルは壊れない。
- 文字コードは既定が Excel 向けの BOM つき UTF-8。他は `--encoding cp932` など。

CSV の列: 次元ごとの `<dim>_code` と `<dim>_name`、`unit`、`value`（原文）、`value_num`（数値のときだけ）、`symbol`（`-` `…` `X` など数値でないとき）、`symbol_note`（その表の NOTE にある意味）、`annotation_code` と `annotation_text`。例:

```
area_code,area_name,unit,value,value_num,symbol,symbol_note
13000,東京都,人,13960000,13960000,,
27000,大阪府,人,-,,-,事実のないもの
```

## 5. 実行できないとき

シェルや外部通信が使えない環境では、`references/api-spec.md` §2・§3 のとおり URL（`https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?appId=<あなたのappId>&statsDataId=…&cdArea=…`）を組み立てて、ユーザーのブラウザかシェルで実行してもらい、結果の JSON か CSV を貼ってもらう。appId は `<あなたのappId>` のまま書く。

## 6. 欠損・秘匿の記号と集計

- 値が `-` `…` `X` `*` などの行は**数値として足さない**。空欄・0 にも置き換えない。`symbol` 列で件数を数え、「記号の行が N 件あり、集計から除いた」と必ず書く。
- 記号の意味は**表ごとに違う**。`symbol_note`（その表の NOTE）を根拠にし、無いものは「この表の注記を確認」と書く。`***` のように確認できない記号の意味は断定しない。`replaceSpChar` は 0 のまま取る（置換すると区別が消える）。
- 集計はユーザーの指定した範囲だけ（合計・平均・順位・前回比など）。単位（`unit`）がそろっているか確かめる。千人と人、年度と暦年を混ぜない。
- 「なぜ増えたか」「どうすべきか」の解釈・提言はしない。聞かれたら、この範囲は対象外と伝え、数値と出典だけを渡す。
- 公開や配布をするなら、`references/terms-and-credit.md` のとおり出典を書き、**加工した旨**も併記する。API を使ったサービスを公開するなら公式のクレジット文を表示する。条文の判定は断定せず、該当箇所を指す。

## 7. 失敗したとき

スクリプトは「原因」と「次の手」を出して終了する。終了コード: 0 正常 / 1 API・HTTP エラー / 2 引数・環境 / 3 通信不可 / 4 該当データなし。

| 症状 | 原因と次の手 |
|---|---|
| exit 2「ESTAT_APP_ID が未設定」 | §1 の appId を設定する |
| STATUS 100 | appId の誤り・削除済み。マイページで確認 |
| STATUS 105 / exit 2 | コードが 100 個超。分けて実行 |
| STATUS 300 | statsDataId が存在しない。§2 に戻る |
| exit 4（STATUS 1） | 該当なし。§3 でコードを確かめ直す |
| exit 3 | 通信できない。通信できる環境で実行するか §5 |

エラーコードの全体は `references/api-spec.md` §7。

## 8. 返す形

```
取得条件: 統計表ID <id>（表題）/ 地域 … / 時間 …
ファイル: population.csv（N 行。うち記号の行 M 件）
集計: （ユーザーの指定どおり）
出典: 政府統計の総合窓口（e-Stat）「<統計名>」（<府省>）を加工して作成

---
要確認
- 項目: 理由（例: 記号 X の意味 — この表の NOTE に説明が無い）
```

要確認が無ければ「要確認: なし」と書く。

## 9. 動作確認の範囲

`scripts/selftest_mock.py`（`python3 scripts/selftest_mock.py`）はモックサーバーで、NEXT_KEY のページング・欠損記号・エラー終了を確かめる。**実際の e-Stat への通信は、この版の作成時には確かめていない**（appId が無かったため）。実通信で動かないときは、まず `--dry-run` の URL をブラウザで開いて比べる。

## 参照

- `references/api-spec.md` — 登録と appId、エンドポイント、パラメータ、件数上限と NEXT_KEY、応答の構造、記号、STATUS 表
- `references/terms-and-credit.md` — 利用規約、出典・加工の表記、公開時のクレジット、アクセスの注意

=== FILE: references/api-spec.md ===
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

=== FILE: references/terms-and-credit.md ===
# 利用規約・出典表示のルール

確認日: 2026-10-21。90 日（2027-01-19）を過ぎたら公式を読み直す。ここは根拠の指摘であって法的助言ではない。判断が分かれる使い方（再配布・有料サービスへの組み込みなど）は公式の規約と問い合わせ窓口で確かめる。

出典（一次情報）:
- e-Stat 利用規約: https://www.e-stat.go.jp/terms-of-use
- API 機能の利用規約: https://www.e-stat.go.jp/api/terms-of-use
- クレジット表示: https://www.e-stat.go.jp/api/api-info/credit
- 利用ガイド: https://www.e-stat.go.jp/api/api-info/api-guide

## 1. 利用条件

- e-Stat のコンテンツは**政府標準利用規約（第2.0版）に準拠**し、クリエイティブ・コモンズ・ライセンス 表示 4.0 国際（CC BY 4.0）と互換。商用利用・加工・再配布ができる。ロゴ・シンボル、第三者の権利が付くものは別（e-Stat 利用規約）。
- 数値データ、単純な表・グラフは著作権の対象でない旨の記載がある（e-Stat 利用規約）。それでも出典は書く。
- API で取得したコンテンツの権利は、元の提供者（統計を作った府省等）の規約に従う。統計表の注記に別の条件があれば、そちらを見る。
- 政府は利用結果について責任を負わない。内容は予告なく変更・削除されることがある。

## 2. 出典の書き方

- 出典を明示する。例:「出典：政府統計の総合窓口（e-Stat）」にポータルの URL。または統計名と作成した府省名（例:「令和2年国勢調査」（総務省））。
- **加工したら、出典とは別に加工した旨を書く**。例:「「○○調査結果」（A省）を加工して作成」。集計・結合・単位変換・欠損の補完はすべて加工。
- 加工した情報を、国や府省が作ったかのように見せない。「総務省発表」のように書かない。

## 3. API を使ったサービスを公開するときのクレジット

API 機能を使ったサービスを**公開する**場合は、次の文を利用者の見える所に表示する（API 利用規約 第7条・クレジット表示ページ。位置の指定は無い）。

> このサービスは、政府統計総合窓口(e-Stat)のAPI機能を使用していますが、サービスの内容は国によって保証されたものではありません。

個人の分析・社内利用・手元の CSV 化だけなら、このクレジットは公開時の話。ただしレポートや記事にするなら §2 の出典と加工の表記は要る。

## 4. API 利用の禁止事項と注意

- 短時間の大量アクセス、その他 API の運用に支障を与える行為は禁止（API 利用規約 第8条）。違反すると利用停止、予告なしの解除になりうる。ページ取得の間隔を空け、1 回の取得を `cd*` で絞る。
- 負荷状況に応じて、運営側がアクセスを制限することがある（第5条）。
- appId は譲渡・貸与しない。不正利用の疑いがあれば速やかに報告する。不正が疑われる ID は直ちに停止されうる（第3条）。
- アプリを公開すると、API の活用事例として紹介されることがあるのに同意する扱い（利用ガイド）。

=== FILE: scripts/estat_fetch.py ===
#!/usr/bin/env python3
"""e-Stat API 3.0 から統計表の検索・メタ情報・統計データを取得する。Python 3.9 の標準ライブラリだけで動く。

  python3 scripts/estat_fetch.py list --search-word 人口 --survey-years 2020
  python3 scripts/estat_fetch.py meta --stats-data-id 0000000000
  python3 scripts/estat_fetch.py data --stats-data-id 0000000000 --cd-area 13000,27000 --cd-time 2020000000 --out out.csv
  python3 scripts/estat_fetch.py data --stats-data-id 0000000000 --cd-area 13000 --out out.csv --dry-run

appId は環境変数 ESTAT_APP_ID から読む（コマンドラインには渡さない。履歴に残るため）。
data は NEXT_KEY をたどって全ページを取得し、CSV に書く。欠損・秘匿の記号（- … X * など）は
空欄にせず、value 列に原文、value_num 列に数値（記号なら空）、symbol 列に記号、symbol_note 列にその意味を残す。

終了コード: 0 正常 / 1 API エラー・HTTP エラー / 2 引数・環境の誤り / 3 通信できない / 4 該当データなし
実行できない環境（外部通信不可のコード実行環境など）では、references/api-spec.md のとおり URL を組み立てて
ユーザーのブラウザかシェルで実行してもらう。--dry-run は通信せず URL（appId は伏せる）だけ出す。
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.e-stat.go.jp/rest/3.0/app"
ENV_NAME = "ESTAT_APP_ID"
MAX_LIMIT = 100000  # 仕様の既定値。1 回の取得は最大 10 万件（FAQ Q5-7）
NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")
RESERVED = {"appid", "statsdataid", "startposition", "limit", "replacespchar", "lang", "metagetflg", "cntgetflg"}

# STATUS → (原因, 次の手)。出典: API 仕様 3.0 のエラーコード一覧（references/api-spec.md）
STATUS_HELP = {
    100: ("appId が認証されなかった（未指定・誤り・削除済み）", "マイページで appId を確かめ、ESTAT_APP_ID を設定し直す。前後の空白と、再発行で無効になった古い ID に注意"),
    101: ("必須パラメータが足りない", "メッセージの {0} に出ているパラメータを足す（statsDataId と appId は必須）"),
    102: ("パラメータの値が正しくない・範囲外", "コードは meta で調べ直す。limit は 1 以上、startPosition は 1 以上"),
    103: ("パラメータの値が長すぎる", "メッセージの上限バイト数以内に短くする"),
    104: ("パラメータに使えない文字が入っている", "URL エンコード（UTF-8）と文字種を確かめる。コードの # は %23"),
    105: ("1 つのパラメータに指定したコードが 100 個を超えた", "コードを 100 個以下に分けて、別々に実行する。lvArea などの階層指定で絞る手もある"),
    200: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する。続くなら e-Stat のお問い合わせへ"),
    201: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する"),
    202: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する"),
    203: ("e-Stat 側のデータベースエラー", "しばらく待ってから再実行する"),
    299: ("e-Stat 側の予期しないエラー", "しばらく待ってから再実行する。続くなら e-Stat のお問い合わせへ"),
    300: ("指定した ID のデータが存在しない", "statsDataId を list で調べ直す（桁のコピー漏れが多い）"),
}


class Fatal(Exception):
    def __init__(self, msg, code=1):
        Exception.__init__(self, msg)
        self.msg = msg
        self.code = code


def err(msg):
    sys.stderr.write(msg + "\n")


def mask(text, app_id):
    if app_id:
        text = text.replace(app_id, "***")
        text = text.replace(urllib.parse.quote(app_id, safe=""), "***")
    return text


# ───────── 通信 ─────────

def build_url(base, func, params, fmt="json"):
    path = base.rstrip("/") + "/" + (fmt + "/" if fmt else "") + func
    return path + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)


def http_get_json(url, app_id, retries=3, timeout=60):
    """JSON を取得する。5xx と通信エラーだけ再試行する（2 秒, 4 秒, 8 秒）。"""
    last = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "jp-estat-api-skill/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                raw = res.read()
                if res.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = b""
            try:
                body = e.read()
                if e.headers.get("Content-Encoding", "").lower() == "gzip":
                    body = gzip.decompress(body)
            except Exception:
                pass
            if e.code >= 500 and attempt < retries:
                last = "HTTP %d" % e.code
                time.sleep(2 ** (attempt + 1))
                continue
            # 本文に JSON の RESULT があれば、その STATUS を優先して読む
            try:
                return json.loads(body.decode("utf-8"))
            except Exception:
                raise Fatal("HTTP %d が返った。原因: appId の誤り・パラメータの誤り・e-Stat 側の障害のどれか。"
                            "次の手: --dry-run で URL を確かめ、数分おいて再実行する。" % e.code, 1)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            last = mask(str(getattr(e, "reason", e)), app_id)
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
    raise Fatal("api.e-stat.go.jp に通信できない（%s）。原因: ネットワーク遮断・プロキシ・外部通信できない実行環境。"
                "次の手: 通信できる環境で実行するか、--dry-run の URL をユーザーのブラウザで開いてもらう。" % last, 3)
    # unreachable


def find_result(doc):
    """応答のどこにあっても RESULT を探す（エラー時は包みのキーが違う可能性があるため）。"""
    if isinstance(doc, dict):
        if "RESULT" in doc and isinstance(doc["RESULT"], dict):
            return doc["RESULT"], doc
        for v in doc.values():
            if isinstance(v, dict):
                r = find_result(v)
                if r:
                    return r
    return None


def check_status(doc, app_id):
    """STATUS を確かめ、(status, body) を返す。100 以上は Fatal。"""
    found = find_result(doc)
    if not found:
        raise Fatal("応答に RESULT が無い。原因: e-Stat 側の仕様変更または想定外の応答。次の手: --dry-run の URL をブラウザで開いて確かめる。", 1)
    result, body = found
    try:
        status = int(result.get("STATUS"))
    except (TypeError, ValueError):
        raise Fatal("STATUS を読めなかった: %r" % (result.get("STATUS"),), 1)
    msg = result.get("ERROR_MSG", "")
    if status >= 100:
        cause, nxt = STATUS_HELP.get(status, ("未知のエラーコード", "references/api-spec.md のエラーコード表と公式仕様を確かめる"))
        raise Fatal(mask("STATUS %d: %s\n  原因: %s\n  次の手: %s" % (status, msg, cause, nxt), app_id), 1)
    return status, body


# ───────── JSON の正規化 ─────────

def aslist(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def text_of(x):
    """{"@no": "..", "$": "text"} または文字列 から文字列を取る。"""
    if isinstance(x, dict):
        return str(x.get("$", ""))
    return "" if x is None else str(x)


def class_map(class_inf):
    """CLASS_INF → ({dim: {code: name}}, {dim: 見出し}, {(dim, code): unit})。"""
    names, labels, units = {}, {}, {}
    for obj in aslist((class_inf or {}).get("CLASS_OBJ")):
        dim = obj.get("@id")
        labels[dim] = obj.get("@name", "")
        names[dim] = {}
        for c in aslist(obj.get("CLASS")):
            names[dim][c.get("@code")] = c.get("@name", "")
            if c.get("@unit"):
                units[(dim, c.get("@code"))] = c.get("@unit")
    return names, labels, units


def dim_order(keys):
    order = ["tab"] + ["cat%02d" % i for i in range(1, 16)] + ["area", "time"]
    return [d for d in order if d in keys]


def classify(value):
    """値の原文を (value_num, symbol) に分ける。数値なら symbol は空、記号なら value_num は空。"""
    v = value.strip()
    if NUMERIC.match(v):
        return v, ""
    return "", v if v else "(空)"


# ───────── 引数 ─────────

def parse_extra(pairs):
    out = []
    for p in pairs or []:
        if "=" not in p:
            raise Fatal("--param は KEY=VALUE の形で指定する: %s" % p, 2)
        k, v = p.split("=", 1)
        if k.lower() in RESERVED:
            raise Fatal("--param で %s は上書きできない（専用の引数を使う）" % k, 2)
        out.append((k, v))
    return out


def check_codes(name, value):
    n = len([c for c in value.split(",") if c])
    if n > 100:
        raise Fatal("%s のコードが %d 個ある。1 つのパラメータに指定できるのは 100 個まで（STATUS 105）。"
                    "次の手: 100 個以下に分けて複数回実行する。" % (name, n), 2)


def common_filters(args):
    params = []
    for flag, key in (("cd_tab", "cdTab"), ("cd_cat01", "cdCat01"), ("cd_area", "cdArea"), ("cd_time", "cdTime")):
        v = getattr(args, flag, None)
        if v:
            check_codes(key, v)
            params.append((key, v))
    for k, v in parse_extra(getattr(args, "param", None)):
        if k.startswith("cd"):
            check_codes(k, v)
        params.append((k, v))
    return params


def get_app_id(required):
    app_id = os.environ.get(ENV_NAME, "").strip()
    if not app_id and required:
        raise Fatal("環境変数 %s が未設定。原因: appId をまだ取っていない、または設定していない。\n"
                    "  次の手: e-Stat のユーザ登録 → マイページ「API機能（アプリケーションID発行）」で appId を取り、\n"
                    "  `export %s=（appId）` を実行してから再実行する。確認だけなら --dry-run。" % (ENV_NAME, ENV_NAME), 2)
    return app_id


# ───────── list / meta ─────────

def cmd_list(args):
    params = [("appId", "{APP_ID}"), ("lang", "J"), ("limit", str(args.limit))]
    for flag, key in (("search_word", "searchWord"), ("survey_years", "surveyYears"), ("stats_code", "statsCode"),
                      ("stats_field", "statsField"), ("collect_area", "collectArea"), ("open_years", "openYears")):
        v = getattr(args, flag)
        if v:
            params.append((key, v))
    params += parse_extra(args.param)
    return run_simple(args, "getStatsList", params, "GET_STATS_LIST")


def cmd_meta(args):
    params = [("appId", "{APP_ID}"), ("lang", "J"), ("statsDataId", args.stats_data_id), ("explanationGetFlg", "N")]
    return run_simple(args, "getMetaInfo", params, "GET_META_INFO")


def run_simple(args, func, params, root_key):
    app_id = get_app_id(required=not args.dry_run)
    shown = [(k, "***" if k == "appId" else v) for k, v in params]
    if args.dry_run:
        print("[dry-run] GET " + build_url(args.base_url, func, shown).replace("appId=%2A%2A%2A", "appId=***"))
        print("[dry-run] appId は環境変数 %s から読む（%s）" % (ENV_NAME, "設定済み" if app_id else "未設定"))
        return 0
    real = [(k, app_id if k == "appId" else v) for k, v in params]
    doc = http_get_json(build_url(args.base_url, func, real), app_id)
    status, body = check_status(doc, app_id)
    if status == 1:
        err("該当データはありませんでした（STATUS 1）。検索語・調査年・statsCode を変えて再実行する。")
        return 4
    if func == "getStatsList":
        inf = body.get("DATALIST_INF", {})
        rng = inf.get("RESULT_INF", {})
        print("# 該当 %s 件中 %s〜%s 件目。続きは --param startPosition=%s" % (
            inf.get("NUMBER", "?"), rng.get("FROM_NUMBER", "?"), rng.get("TO_NUMBER", "?"), rng.get("NEXT_KEY", "（なし）")))
        print("statsDataId\t政府統計名\t表題\t調査年月\t更新日")
        for t in aslist(inf.get("TABLE_INF")):
            print("\t".join([str(t.get("@id", "")), text_of(t.get("STAT_NAME")), text_of(t.get("TITLE")).replace("\t", " "),
                            text_of(t.get("SURVEY_DATE")), text_of(t.get("UPDATED_DATE"))]))
    else:
        inf = body.get("METADATA_INF", {})
        tinf = inf.get("TABLE_INF", {})
        print("# 統計表 %s: %s" % (tinf.get("@id", args.stats_data_id), text_of(tinf.get("TITLE"))))
        names, labels, _ = class_map(inf.get("CLASS_INF"))
        for dim in dim_order(names):
            print("\n[%s] %s（%d 件）" % (dim, labels.get(dim, ""), len(names[dim])))
            for i, (code, name) in enumerate(names[dim].items()):
                if i >= args.max_rows:
                    print("  …（残り %d 件。--max-rows で増やす）" % (len(names[dim]) - i))
                    break
                print("  %s\t%s" % (code, name))
    return 0


# ───────── data ─────────

def cmd_data(args):
    if args.limit < 1 or args.limit > MAX_LIMIT:
        raise Fatal("--limit は 1〜%d の範囲で指定する（1 回の取得は最大 10 万件）" % MAX_LIMIT, 2)
    filters = common_filters(args)
    app_id = get_app_id(required=not args.dry_run)

    def params_for(start, first):
        p = [("appId", app_id or "{APP_ID}"), ("lang", "J"), ("statsDataId", args.stats_data_id)] + filters
        p += [("startPosition", str(start)), ("limit", str(args.limit)),
              ("metaGetFlg", "Y" if first else "N"), ("cntGetFlg", "N"),
              ("annotationGetFlg", "Y"), ("replaceSpChar", "0")]  # 記号をそのまま受け取る
        return p

    if args.dry_run:
        p = [(k, "***" if k == "appId" else v) for k, v in params_for(1, True)]
        print("[dry-run] GET " + build_url(args.base_url, "getStatsData", p).replace("appId=%2A%2A%2A", "appId=***"))
        print("[dry-run] 続きは応答の NEXT_KEY を startPosition に入れて繰り返す（最大 %d ページ、間隔 %.1f 秒）" % (args.max_pages, args.sleep))
        print("[dry-run] 出力先: %s（既存ならページ取得が全部成功した後で置き換える）" % args.out)
        print("[dry-run] appId は環境変数 %s から読む（%s）" % (ENV_NAME, "設定済み" if app_id else "未設定"))
        return 0

    rows, notes, annots = [], {}, {}
    names, labels, units = {}, {}, {}
    start, page, total = 1, 0, None
    while True:
        page += 1
        if page > args.max_pages:
            raise Fatal("--max-pages(%d) に達したので止めた。取得途中のため CSV は書いていない。"
                        "次の手: cd* で絞り込むか、--max-pages を増やす。" % args.max_pages, 1)
        doc = http_get_json(build_url(args.base_url, "getStatsData", params_for(start, page == 1)), app_id)
        status, body = check_status(doc, app_id)
        if status == 1:
            err("該当データはありませんでした（STATUS 1）。cdArea・cdTime などの絞り込みコードを meta で確かめて直す。")
            return 4
        sd = body.get("STATISTICAL_DATA", {})
        inf = sd.get("RESULT_INF", {})
        if total is None:
            total = inf.get("TOTAL_NUMBER")
        if page == 1:
            names, labels, units = class_map(sd.get("CLASS_INF"))
        di = sd.get("DATA_INF") or {}
        for n in aslist(di.get("NOTE")):
            notes[n.get("@char", "")] = text_of(n)
        for a in aslist(di.get("ANNOTATION")):
            annots[a.get("@annotation", "")] = text_of(a)
        rows.extend(aslist(di.get("VALUE")))
        nxt = inf.get("NEXT_KEY")
        err("ページ %d: %s〜%s 件目 / 全 %s 件" % (page, inf.get("FROM_NUMBER", "?"), inf.get("TO_NUMBER", "?"), total))
        if nxt in (None, ""):
            break
        try:
            nxt = int(nxt)
        except ValueError:
            raise Fatal("NEXT_KEY が数値でない: %r" % (nxt,), 1)
        if nxt <= start:
            raise Fatal("NEXT_KEY(%d) が進んでいない（startPosition=%d）。無限ループを避けて止めた。" % (nxt, start), 1)
        start = nxt
        time.sleep(args.sleep)  # 短時間の大量アクセスは規約で禁止

    if total is not None and str(total).isdigit() and int(total) != len(rows):
        err("警告: TOTAL_NUMBER=%s だが取得できたのは %d 行。" % (total, len(rows)))
    write_csv(args, rows, names, notes, annots, units)
    sym = sum(1 for r in rows if not NUMERIC.match(text_of(r).strip()))
    err("書き出し完了: %s（%d 行、うち数値でない値 %d 行）" % (args.out, len(rows), sym))
    err("次元: " + " / ".join("%s=%s" % (d, labels.get(d, "")) for d in dim_order(names)))
    err("出典の書き方は references/terms-and-credit.md。加工したなら『加工して作成』を併記する。")
    return 0


def write_csv(args, rows, names, notes, annots, units):
    keys = set()
    for r in rows:
        keys.update(k[1:] for k in r if k.startswith("@"))
    dims = dim_order(keys | set(names))
    header = []
    for d in dims:
        header += [d + "_code", d + "_name"]
    header += ["unit", "value", "value_num", "symbol", "symbol_note", "annotation_code", "annotation_text"]
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".estat_", suffix=".csv", dir=out_dir)
    try:
        with os.fdopen(fd, "w", encoding=args.encoding, newline="") as f:
            w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            w.writerow(header)
            for r in rows:
                raw = text_of(r)
                num, sym = classify(raw)
                line = []
                for d in dims:
                    code = r.get("@" + d, "")
                    line += [code, names.get(d, {}).get(code, "")]
                unit = r.get("@unit") or next((units[(d, r.get("@" + d))] for d in dims if (d, r.get("@" + d)) in units), "")
                note = ""
                if sym:
                    note = notes.get(sym, "（この表の NOTE に説明なし。統計表の注記を確かめる）" if sym != "(空)" else "値が空")
                ac = r.get("@annotation", "")
                line += [unit, raw, num, sym, note, ac, annots.get(ac, "") if ac else ""]
                w.writerow(line)
        os.replace(tmp, args.out)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ───────── main ─────────

def build_parser():
    p = argparse.ArgumentParser(
        description="e-Stat API 3.0 で統計表の検索(list)・メタ情報(meta)・統計データ(data)を取得する。appId は環境変数 %s。" % ENV_NAME,
        epilog="終了コード: 0 正常 / 1 API・HTTP エラー / 2 引数・環境 / 3 通信不可 / 4 該当なし。例は SKILL.md を参照。")
    sub = p.add_subparsers(dest="cmd")

    def common(sp):
        sp.add_argument("--base-url", default=DEFAULT_BASE, help="既定 %s（テスト用に差し替え可）" % DEFAULT_BASE)
        sp.add_argument("--dry-run", action="store_true", help="通信せず、組み立てた URL（appId は伏せる）を出す")
        sp.add_argument("--param", action="append", metavar="KEY=VALUE", help="追加パラメータ（例 lvArea=2, cdCat02=001）。繰り返し可")

    sl = sub.add_parser("list", help="統計表を検索して statsDataId を調べる（getStatsList）")
    common(sl)
    sl.add_argument("--search-word", help="キーワード（AND/OR/NOT 可）")
    sl.add_argument("--survey-years", help="調査年 yyyy / yyyymm / yyyymm-yyyymm")
    sl.add_argument("--open-years", help="公開年")
    sl.add_argument("--stats-code", help="政府統計コード（5 桁=府省、8 桁=統計）。国勢調査は 00200521")
    sl.add_argument("--stats-field", help="統計分野（2 桁 / 4 桁）")
    sl.add_argument("--collect-area", choices=["1", "2", "3"], help="1 全国 / 2 都道府県 / 3 市区町村")
    sl.add_argument("--limit", type=int, default=20, help="表示する表の数（既定 20）")
    sl.set_defaults(func=cmd_list)

    sm = sub.add_parser("meta", help="統計表の次元（表章・分類・地域・時間）とコードを見る（getMetaInfo）")
    common(sm)
    sm.add_argument("--stats-data-id", required=True)
    sm.add_argument("--max-rows", type=int, default=50, help="次元ごとの表示件数（既定 50）")
    sm.set_defaults(func=cmd_meta)

    sd = sub.add_parser("data", help="統計データを全ページ取得して CSV に書く（getStatsData）")
    common(sd)
    sd.add_argument("--stats-data-id", required=True)
    sd.add_argument("--cd-tab", help="表章項目コード（カンマ区切り、100 個まで）")
    sd.add_argument("--cd-cat01", help="分類事項 01 のコード")
    sd.add_argument("--cd-area", help="地域コード（例 13000 は東京都）")
    sd.add_argument("--cd-time", help="時間軸コード（例 2020000000）")
    sd.add_argument("--limit", type=int, default=MAX_LIMIT, help="1 ページの件数（既定・上限 100000）")
    sd.add_argument("--max-pages", type=int, default=1000, help="安全弁のページ数上限（既定 1000）")
    sd.add_argument("--sleep", type=float, default=1.0, help="ページ間の待ち秒（既定 1.0。規約で短時間の大量アクセスは禁止）")
    sd.add_argument("--out", default="estat_data.csv", help="出力 CSV（既定 estat_data.csv）。同名は成功時に置き換える")
    sd.add_argument("--encoding", default="utf-8-sig", help="文字コード（既定 utf-8-sig=Excel 向け BOM つき。cp932 / utf-8 も可）")
    sd.set_defaults(func=cmd_data)
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        return args.func(args)
    except Fatal as e:
        err("エラー: " + e.msg)
        return e.code
    except LookupError as e:
        err("エラー: 文字コードが不正: %s" % e)
        return 2
    except OSError as e:
        err("エラー: ファイルを書けない（%s）。次の手: --out の場所と権限を確かめる。" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())

=== FILE: scripts/selftest_mock.py ===
#!/usr/bin/env python3
"""estat_fetch.py の自己検査。ローカルのモックサーバーで NEXT_KEY のページングと欠損記号の扱いなどを確かめる。
実際の e-Stat には接続しない（appId も要らない）。Python 3.9 標準ライブラリだけ。

  python3 scripts/selftest_mock.py        # 全部通れば "ALL PASSED" で終了コード 0
"""
import contextlib
import csv
import gzip
import io
import json
import os
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import estat_fetch  # noqa: E402

estat_fetch.time.sleep = lambda s: None  # 再試行・ページ間の待ちを省く

SECRET = "TESTAPPID1234567890"
LOG = []
MODE = {"name": "normal"}

ROWS = [
    {"@tab": "001", "@cat01": "000", "@area": "13000", "@time": "2020000000", "@unit": "人", "$": "13960000"},
    {"@tab": "001", "@cat01": "000", "@area": "27000", "@time": "2020000000", "@unit": "人", "$": "-"},
    {"@tab": "001", "@cat01": "000", "@area": "01000", "@time": "2020000000", "@unit": "人", "$": "…"},
    {"@tab": "001", "@cat01": "000", "@area": "02000", "@time": "2020000000", "@unit": "人", "$": "X", "@annotation": "J1"},
    {"@tab": "001", "@cat01": "000", "@area": "03000", "@time": "2020000000", "@unit": "人", "$": "***"},
]
CLASS_INF = {"CLASS_OBJ": [
    {"@id": "tab", "@name": "表章項目", "CLASS": {"@code": "001", "@name": "人口"}},
    {"@id": "cat01", "@name": "男女", "CLASS": [{"@code": "000", "@name": "総数"}]},
    {"@id": "area", "@name": "地域", "CLASS": [{"@code": "13000", "@name": "東京都"}, {"@code": "27000", "@name": "大阪府"},
                                               {"@code": "01000", "@name": "北海道"}, {"@code": "02000", "@name": "青森県"},
                                               {"@code": "03000", "@name": "岩手県"}]},
    {"@id": "time", "@name": "時間軸", "CLASS": [{"@code": "2020000000", "@name": "2020年"}]},
]}


def ok(status=0, msg="正常に終了しました。"):
    return {"STATUS": status, "ERROR_MSG": msg, "DATE": "2026-10-21T00:00:00.000+09:00"}


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, obj, gz=False):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        if gz:
            raw = gzip.compress(raw)
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if gz:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        func = u.path.rsplit("/", 1)[-1]
        LOG.append((func, q))
        if q.get("appId") != SECRET:
            return self.send(403, {"GET_STATS_DATA": {"RESULT": ok(100, "認証に失敗しました。")}})
        m = MODE["name"]
        if func == "getStatsList":
            return self.send(200, {"GET_STATS_LIST": {"RESULT": ok(), "DATALIST_INF": {
                "NUMBER": 1, "RESULT_INF": {"FROM_NUMBER": 1, "TO_NUMBER": 1},
                "TABLE_INF": {"@id": "0000000000", "STAT_NAME": {"@code": "00200521", "$": "国勢調査"},
                              "TITLE": {"@no": "1", "$": "男女別人口"}, "SURVEY_DATE": "202010", "UPDATED_DATE": "2022-01-01"}}}})
        if func == "getMetaInfo":
            return self.send(200, {"GET_META_INFO": {"RESULT": ok(), "METADATA_INF": {
                "TABLE_INF": {"@id": q["statsDataId"], "TITLE": "男女別人口"}, "CLASS_INF": CLASS_INF}}})
        if m == "status1":
            return self.send(200, {"GET_STATS_DATA": {"RESULT": ok(1, "該当データはありませんでした。")}})
        if m == "status300":
            return self.send(400, {"GET_STATS_DATA": {"RESULT": ok(300, "statsDataId=[x]のデータは存在しません。")}})
        start, limit = int(q.get("startPosition", 1)), int(q.get("limit", 100000))
        chunk = ROWS[start - 1:start - 1 + limit]
        end = start - 1 + len(chunk)
        inf = {"TOTAL_NUMBER": len(ROWS), "FROM_NUMBER": start, "TO_NUMBER": end}
        if end < len(ROWS):
            inf["NEXT_KEY"] = start if m == "stuck" else end + 1
        sd = {"RESULT_INF": inf, "DATA_INF": {
            "NOTE": [{"@char": "-", "$": "事実のないもの"}, {"@char": "…", "$": "事実不詳又は調査を欠くもの"},
                     {"@char": "X", "$": "数字が秘匿されているもの"}],
            "ANNOTATION": {"@annotation": "J1", "$": "注記テスト"},
            "VALUE": chunk[0] if (m == "single" and len(chunk) == 1) else chunk}}
        if q.get("metaGetFlg") == "Y":
            sd["CLASS_INF"] = CLASS_INF
        self.send(200, {"GET_STATS_DATA": {"RESULT": ok(), "STATISTICAL_DATA": sd}}, gz=(m == "gzip"))


def run(argv, env=SECRET):
    out, errb = io.StringIO(), io.StringIO()
    if env is None:
        os.environ.pop("ESTAT_APP_ID", None)
    else:
        os.environ["ESTAT_APP_ID"] = env
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(errb):
        try:
            code = estat_fetch.main(argv)
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), errb.getvalue()


FAILS = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(detail)))
    if not cond:
        FAILS.append(name)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/rest/3.0/app" % srv.server_port
    tmp = tempfile.mkdtemp(prefix="estat_selftest_")
    out = os.path.join(tmp, "o.csv")
    data = ["data", "--stats-data-id", "0000000000", "--base-url", base, "--out", out]

    # 1. ページング: limit=2 で 5 行 → 3 ページ
    MODE["name"] = "normal"
    del LOG[:]
    code, so, se = run(data + ["--limit", "2", "--cd-area", "13000,27000"])
    reqs = [q for f, q in LOG if f == "getStatsData"]
    check("paging: exit 0", code == 0, se)
    check("paging: startPosition が NEXT_KEY をたどる 1,3,5", [q["startPosition"] for q in reqs] == ["1", "3", "5"], reqs)
    check("paging: metaGetFlg は初回だけ Y", [q["metaGetFlg"] for q in reqs] == ["Y", "N", "N"])
    check("paging: replaceSpChar=0 で記号をそのまま受ける", all(q["replaceSpChar"] == "0" for q in reqs))
    check("paging: cdArea が渡る", all(q["cdArea"] == "13000,27000" for q in reqs))
    rows = read_csv(out)
    check("paging: CSV は 5 行", len(rows) == 5, len(rows))
    check("paging: コードと名称の列", rows[0]["area_code"] == "13000" and rows[0]["area_name"] == "東京都" and rows[0]["time_name"] == "2020年")
    check("paging: 次のページの行にも名称が付く", rows[4]["area_name"] == "岩手県")
    check("secret: appId が stdout/stderr に出ない", SECRET not in so + se)

    # 2. 欠損記号
    check("symbol: 数値は value_num に入る", rows[0]["value_num"] == "13960000" and rows[0]["symbol"] == "")
    check("symbol: '-' は空欄にせず symbol 列に残す", rows[1]["value"] == "-" and rows[1]["symbol"] == "-" and rows[1]["value_num"] == "")
    check("symbol: '…' の意味が NOTE から付く", rows[2]["symbol"] == "…" and "不詳" in rows[2]["symbol_note"])
    check("symbol: 'X' の意味と注記", rows[3]["symbol"] == "X" and "秘匿" in rows[3]["symbol_note"]
          and rows[3]["annotation_code"] == "J1" and rows[3]["annotation_text"] == "注記テスト")
    check("symbol: NOTE に無い '***' は説明なしと明記", rows[4]["symbol"] == "***" and "NOTE に説明なし" in rows[4]["symbol_note"])

    # 3. 1 ページで終わる / 単一 VALUE が dict / gzip
    for m in ("normal", "single", "gzip"):
        MODE["name"] = m
        code, so, se = run(data + ["--limit", "1" if m == "single" else "100000"])
        check("mode %s: exit 0 で行が取れる" % m, code == 0 and len(read_csv(out)) == 5, se)

    # 4. エラー
    MODE["name"] = "normal"
    p = os.path.join(tmp, "n.csv")
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p], env="WRONG")
    check("STATUS 100: exit 1 で原因と次の手", code == 1 and "原因" in se and "次の手" in se, (code, se))
    check("STATUS 100: 渡した appId を表示しない", "WRONG" not in se)
    check("STATUS 100: ファイルを作らない", not os.path.exists(p))
    MODE["name"] = "status1"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p])
    check("STATUS 1: exit 4 でファイルなし", code == 4 and not os.path.exists(p), (code, se))
    MODE["name"] = "status300"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p])
    check("STATUS 300 (HTTP 400): exit 1 で STATUS を読む", code == 1 and "STATUS 300" in se, (code, se))
    MODE["name"] = "stuck"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p, "--limit", "2"])
    check("NEXT_KEY が進まない: 止めて exit 1、CSV を書かない", code == 1 and "進んでいない" in se and not os.path.exists(p), (code, se))
    MODE["name"] = "normal"
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", base, "--out", p, "--max-pages", "2", "--limit", "2"])
    check("max-pages 超過: exit 1、途中の CSV を書かない", code == 1 and not os.path.exists(p), (code, se))
    pre = os.path.join(tmp, "pre.csv")
    with open(pre, "w") as f:
        f.write("old")
    run(["data", "--stats-data-id", "x", "--base-url", base, "--out", pre, "--max-pages", "2", "--limit", "2"])
    with open(pre) as f:
        check("失敗しても既存ファイルを壊さない", f.read() == "old")

    # 5. 引数・環境
    code, so, se = run(data, env=None)
    check("ESTAT_APP_ID なし: exit 2 と取り方の案内", code == 2 and "ESTAT_APP_ID" in se and "マイページ" in se, (code, se))
    code, so, se = run(data + ["--cd-area", ",".join(str(i) for i in range(101))])
    check("コード 101 個: exit 2（STATUS 105 を先回り）", code == 2 and "100" in se, (code, se))
    code, so, se = run(data + ["--param", "appId=evil"])
    check("--param で appId は上書き不可", code == 2, (code, se))
    code, so, se = run(data + ["--limit", "100001"])
    check("limit 超過: exit 2", code == 2)

    # 6. dry-run
    del LOG[:]
    code, so, se = run(data + ["--cd-area", "13000", "--dry-run"])
    check("dry-run: 通信しない", code == 0 and not LOG, so)
    check("dry-run: appId を伏せる", SECRET not in so and "appId=***" in so, so)
    code, so, se = run(data + ["--dry-run"], env=None)
    check("dry-run: appId 未設定でも動く", code == 0 and "未設定" in so)

    # 7. list / meta
    MODE["name"] = "normal"
    code, so, se = run(["list", "--search-word", "人口", "--base-url", base])
    check("list: statsDataId と表題を出す", code == 0 and "0000000000" in so and "男女別人口" in so, so + se)
    code, so, se = run(["meta", "--stats-data-id", "0000000000", "--base-url", base])
    check("meta: 地域コードと名称を出す", code == 0 and "13000" in so and "東京都" in so, so + se)

    # 8. 通信不可
    code, so, se = run(["data", "--stats-data-id", "x", "--base-url", "http://127.0.0.1:1/rest/3.0/app", "--out", p])
    check("通信不可: exit 3", code == 3 and "次の手" in se, (code, se))

    srv.shutdown()
    print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
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
