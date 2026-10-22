# コード例（Python 標準ライブラリ・curl）

出典の仕様は api-spec.md（確認日 2026-10-23）。鍵は環境変数から読み、コードに書かない。

## curl

```bash
# 件数
curl -s -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues/count?projectId%5B%5D=123"
# 1ページ（100件）
curl -s -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues?projectId%5B%5D=123&count=100&offset=0&sort=created&order=asc"
# 登録（form 本文。-d は application/x-www-form-urlencoded になる）
curl -s -X POST -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues" \
  -d projectId=123 --data-urlencode "summary=テスト課題" -d issueTypeId=7 -d priorityId=3
# ステータス変更
curl -s -X PATCH -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues/PRJ-1" -d statusId=4
# コメント
curl -s -X POST -H "Backlog-API-Key: $BACKLOG_API_KEY" "https://$BACKLOG_SPACE/api/v2/issues/PRJ-1/comments" --data-urlencode "content=確認しました"
```

## Python（全件取得の骨格）

```python
import json, os, time, urllib.parse, urllib.request
BASE = "https://" + os.environ["BACKLOG_SPACE"]          # 例 example.backlog.jp
KEY = os.environ["BACKLOG_API_KEY"]

def get(path, params):
    url = BASE + path + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers={"Backlog-API-Key": KEY})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

issues, offset = [], 0
while True:
    page = get("/api/v2/issues", [("projectId[]", 123), ("count", 100), ("offset", offset), ("sort", "created"), ("order", "asc")])
    issues += page
    if len(page) < 100:
        break
    offset += 100
    time.sleep(1)            # 公式: 一括処理は1秒以上あける
```

登録・更新は `urllib.request.Request(url, data=urllib.parse.urlencode(form, doseq=True).encode(), method="POST"|"PATCH")`（Content-Type は `application/x-www-form-urlencoded`）。配列は `[("categoryId[]", 1), ("categoryId[]", 2)]`。

## ID の調べ方

`python3 scripts/backlog_issues.py meta`（プロジェクト一覧と優先度）→ `meta --project-id 123`（状態・種別・カスタム属性）。
