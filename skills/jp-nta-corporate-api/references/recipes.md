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
