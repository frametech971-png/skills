import os, requests

APP_ID = os.environ["RAKUTEN_APP_ID"]
URL = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"

def search(keyword):
    r = requests.get(URL, params={"applicationId": APP_ID, "keyword": keyword, "format": "json", "hits": 3})
    r.raise_for_status()
    return [i["Item"]["itemName"] for i in r.json()["Items"]]

print(search("電気ケトル"))
