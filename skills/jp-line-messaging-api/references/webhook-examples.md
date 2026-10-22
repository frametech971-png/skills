# Webhook を受けて返信する最小の例

確認日 2026-10-21。手元で動かして確かめた内容（署名の正しい／誤り／無し、重複イベントの無視、reply リクエストの形）。実際の LINE との通信は未検証（実アカウントが無いため。`LINE_API_BASE` を手元のダミーサーバーに向けて確認した）。

## Python 3.9（標準ライブラリだけ）

```python
import base64, hashlib, hmac, json, os, threading, urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
API_BASE = os.environ.get("LINE_API_BASE", "https://api.line.me")  # テスト用。本番は未設定でよい
seen_event_ids = set()  # 本番は Redis や DB に。再配信・重複の検出用


def valid_signature(body, signature):
    mac = hmac.new(CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(mac), (signature or "").encode("utf-8"))


def reply(reply_token, text):
    req = urllib.request.Request(
        API_BASE + "/v2/bot/message/reply",
        data=json.dumps({"replyToken": reply_token,
                         "messages": [{"type": "text", "text": text}]}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + ACCESS_TOKEN},
        method="POST")
    urllib.request.urlopen(req, timeout=10).read()


def handle_events(payload):
    for ev in payload.get("events", []):
        if ev.get("webhookEventId") in seen_event_ids:
            continue
        seen_event_ids.add(ev.get("webhookEventId"))
        if ev.get("type") == "message" and ev["message"].get("type") == "text":
            reply(ev["replyToken"], "受け取りました: " + ev["message"]["text"])


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))  # 生のバイト列
        if not valid_signature(body, self.headers.get("x-line-signature")):
            self.send_response(400); self.end_headers(); return
        self.send_response(200); self.end_headers()           # 先に 200 を返す
        payload = json.loads(body.decode("utf-8"))             # 検証のあとでパースする
        threading.Thread(target=handle_events, args=(payload,)).start()  # 処理は非同期で


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8000"))), Handler).serve_forever()
```

実行: `LINE_CHANNEL_SECRET=... LINE_CHANNEL_ACCESS_TOKEN=... python3 server.py`。公開 URL（HTTPS）を LINE Developers コンソールの Webhook URL に設定し、Webhook を利用する設定をオンにする。ローカルで試すときはトンネルサービス等で HTTPS の URL を用意する。

本番にするときの注意:
- `seen_event_ids` はメモリ上なので、再起動や複数プロセスで消える。共有ストアに置く。
- `reply` が 400（`Invalid reply token`）を返したら、遅れたか使用済み。握りつぶさず記録し、必要なら push に切り替える（通数に数えられる）。
- ユーザー入力をそのまま返信に使わない（この例は動作確認のためのオウム返し）。

## Node.js 18 以上（署名検証部分）

```js
import http from "node:http";
import crypto from "node:crypto";

const SECRET = process.env.LINE_CHANNEL_SECRET;

function validSignature(rawBody, signature) {
  const expected = crypto.createHmac("sha256", SECRET).update(rawBody).digest(); // rawBody は Buffer のまま
  const given = Buffer.from(signature ?? "", "base64");
  return given.length === expected.length && crypto.timingSafeEqual(given, expected);
}

http.createServer((req, res) => {
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    const raw = Buffer.concat(chunks);                 // 生のバイト列。JSON.parse の前に検証する
    if (!validSignature(raw, req.headers["x-line-signature"])) {
      res.writeHead(400).end();
      return;
    }
    res.writeHead(200).end();                          // 先に 200 を返し、処理は非同期で
    const payload = JSON.parse(raw.toString("utf8"));
    for (const ev of payload.events) console.log(ev.type, ev.webhookEventId);
  });
}).listen(Number(process.env.PORT ?? 8000));
```

Express を使う場合は `express.json()` を webhook のルートに適用しない。`express.raw({ type: "*/*" })` で Buffer のまま受け、検証してから `JSON.parse` する（上の `validSignature` をそのまま使える）。この Express 構成は手元では未実行。

## Cloudflare Workers など

`await request.text()` では文字列になるが、UTF-8 のままなので HMAC の入力にできる（`new TextEncoder().encode(text)`）。`request.json()` を先に呼ぶとボディを読み終えて検証できなくなる。Web Crypto の `crypto.subtle.sign("HMAC", key, data)` の結果を Base64 にして比較する。この構成は手元では未実行。
