# コードの書き方（Python 標準ライブラリ版と curl）

確認日: 2026-10-21。仕様の数字は api-spec.md を正とする。**鍵はコードに書かず、環境変数から読む。**

## 全件取得（同梱スクリプト）

```bash
export KINTONE_SUBDOMAIN=example KINTONE_APP_ID=12     # 鍵は export KINTONE_API_TOKEN=... を手元のシェルで（会話・コードには書かない）
python3 scripts/kintone_records.py fetch --dry-run
python3 scripts/kintone_records.py fetch --count-only --query 'ステータス in ("対応中")'
python3 scripts/kintone_records.py fetch --query 'ステータス in ("対応中") order by $id asc' --fields 会社名,金額 --format csv -o out.csv
```
`--bom` で Excel 向けの BOM つき UTF-8。CSV のチェックボックスは `;` 区切り、ユーザー選択は code、サブテーブルは JSON 文字列。JSON 出力は元のレスポンス（type つき）のまま。

## コードを書くとき（カーソルで全件）

```python
import json, os, urllib.request

BASE = "https://%s.cybozu.com/k/v1" % os.environ["KINTONE_SUBDOMAIN"]
HEAD = {"X-Cybozu-API-Token": os.environ["KINTONE_API_TOKEN"], "Content-Type": "application/json"}

def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, headers=HEAD,
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")

cur = call("POST", "/records/cursor.json", {"app": os.environ["KINTONE_APP_ID"], "size": 500, "query": 'ステータス in ("対応中")'})
records, done = [], False
try:
    while True:
        page = call("GET", "/records/cursor.json?id=" + cur["id"])   # GET に本文は付けない
        records += page["records"]
        if not page["next"]:
            done = True          # 取り切るとカーソルは自動で消える
            break
finally:
    if not done:
        call("DELETE", "/records/cursor.json", {"id": cur["id"]})
```
- 429 のときは待って再試行する。`query` に limit / offset は書かない。
- offset ページング（10,000件まで）で済む件数でも、取りこぼしを避けたいならカーソルを使う。

## 登録（100件ずつ）

```python
for i in range(0, len(rows), 100):
    call("POST", "/records.json", {"app": APP, "records": [
        {"会社名": {"value": r["name"]}, "金額": {"value": str(r["amount"])}} for r in rows[i:i+100]]})
```
- 失敗した回は全件キャンセルされる。**それまでの回は登録済み**なので、再実行の前に件数を確かめる（重複を避ける）。
- 同梱スクリプト: `python3 scripts/kintone_records.py add --csv 登録.csv --dry-run` で内容を確かめ、`--yes` で送る。CSV の1行目はフィールドコード。Excel の CSV は `--encoding cp932`。空欄のセルは送らない（アプリの初期値になる）。値は文字列で送る（数値フィールドも文字列でよい）。複数選択・ユーザー選択・テーブルは CSV では扱えない（コードで書く）。

## 更新

```python
call("PUT", "/records.json", {"app": APP, "records": [
    {"id": 3, "record": {"金額": {"value": "2000"}}}]})          # 100件まで。updateKey でも指定できる
```
テーブルは全行を送る（api-spec.md §5）。楽観ロックが要るときは `revision` を付ける。

## curl

```bash
curl -s -X POST "https://${KINTONE_SUBDOMAIN}.cybozu.com/k/v1/records/cursor.json" \
  -H "X-Cybozu-API-Token: ${KINTONE_API_TOKEN}" -H "Content-Type: application/json" \
  -d '{"app": 12, "size": 500}'
```
パスワード認証は `-H "X-Cybozu-Authorization: $(printf '%s' "$LOGIN:$PASS" | base64)"`。

## JavaScript カスタマイズから呼ぶ場合

`kintone.api()`（ブラウザ内。ログイン中のユーザー権限で動き、鍵は不要）は対象外。このスキルは外部のスクリプトから REST API を呼ぶ場合を扱う。
