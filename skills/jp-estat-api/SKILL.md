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
