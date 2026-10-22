<!-- jp-line-messaging-api v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-line-messaging-api（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-line-messaging-api
description: >-
  LINE公式アカウントの Messaging API を使う Bot・通知のコードを書き、Webhook の署名検証・reply/push・メッセージ上限・エラー・料金プランの原因を調べる。「LINE Bot の Webhook を受けて返信するコードを書いて」「x-line-signature の検証が合わない」「reply と push の違い、replyToken の期限は」「LINE Notify の代わりに通知を送りたい」「LINE公式アカウントで無料で送れる通数は」と頼まれたときに使う。署名はチャネルシークレットで HMAC-SHA256 を Base64 にし、パース前の生のボディで検証する。LINE Notify は 2025-03-31 に終了済み。料金は変わるので公式で再確認する。Keywords: LINE Messaging API, webhook signature, reply token, push message, LINE Notify alternative, LINE Official Account pricing。リッチメニューの画像制作、LINE以外のチャット、LIFF アプリ全般は対象外。
license: MIT
compatibility: "scripts は Python 3.9 以上（標準ライブラリだけ）。署名検証は外部通信なし。line_send.py の実送信にはネットワークと自分の LINE チャネルが必要。実行できない環境ではコードと手順の説明だけで使える。"
metadata:
  version: "1.0.0"
  author: frametech
---

# LINE Messaging API（Bot・通知）

目的: LINE公式アカウントの Messaging API で Webhook を受けて返信・通知する実装を、公式仕様どおりに書き、動かないときの原因を絞る。
入力: やりたいこと（言語・フレームワークも）、またはエラー文・受信したボディとヘッダー・料金や通数の質問。
出力: 動くコード（署名検証つき）か、原因と直し方。仕様の数値には出典を添え、変わりやすいもの（料金）は公式で確認するよう書く。

## 1. 何を頼まれたか

| 頼まれたこと | 読むもの |
|---|---|
| Webhook を受ける・返信する Bot のコード | [references/webhook-examples.md](references/webhook-examples.md) と [references/webhook-signature.md](references/webhook-signature.md) |
| 署名検証が合わない（`x-line-signature`） | [references/webhook-signature.md](references/webhook-signature.md)。実データがあれば `scripts/line_verify_signature.py --diagnose` |
| reply と push の違い、replyToken、メッセージ数・文字数の上限、429 などのエラー | [references/sending-and-limits.md](references/sending-and-limits.md) |
| 無料で送れる通数、料金プラン、LINE Notify の代わり | [references/pricing-and-notify.md](references/pricing-and-notify.md) |
| 試しに送ってみたい | `scripts/line_send.py`（§4） |

## 2. 外せない規則

- **署名は、パースする前の生のボディで検証する。** チャネルシークレットを鍵に HMAC-SHA256 → Base64 → `x-line-signature` と定数時間で比較。JSON のパース・整形・再生成、フレームワークの自動パースの後では合わない。不一致・ヘッダー無しは処理せずエラーで終える。ヘッダー名は大文字小文字を区別せず読む。
- **200 を先に返し、処理は非同期にする。** 同じイベントが複数回届きうるので `webhookEventId` で重複を捨てる。
- **replyToken は1回限り・受信から約1分以内。** 1回の reply で最大5メッセージ。遅れる・複数回返したいなら push（ユーザー ID が要る）。reply は通数に数えられず、push は数えられる。
- **push は `X-Line-Retry-Key`（UUID）を最初から付ける。** reply には付けられない（400）。push は相手がブロックしていても 200 が返る（届いたとは限らない）。
- **鍵を書かない。** チャネルシークレット・チャネルアクセストークンは環境変数から読むコードにする。ユーザーが会話に貼ってきたら、コードや説明に写さず、貼ったものは再発行（コンソールの Issue）を勧める。
- **LINE Notify は 2025年3月31日に終了済み。** 「LINE Notify で送りたい」には使えないと伝え、Messaging API への移行（[references/pricing-and-notify.md](references/pricing-and-notify.md)）を案内する。
- **料金プラン・無料通数・追加メッセージ単価は変わる。** references の値は確認日つきの目安として示し、答えるときは「確認日 2026-10-21 時点。契約前に公式（下記 URL）で現行の値を確認」と添える。追加メッセージの単価は 2026-10-01 に改定されており、このスキルでは金額を断定しない。
- **確認日から90日（2027-01-19）を過ぎたら、公式を読み直してから答える。** 仕様・上限・料金のどれも。

## 3. 返し方

コードを書くとき:
1. 受け口の言語・フレームワークを確認（不明なら Python 標準ライブラリか Node 18 以上の例を出す）。
2. 検証 → 200 → 非同期処理の順で書き、検証にはパース前のボディ（Buffer／bytes）を使う。
3. 末尾に「動作確認の手順」（`--dry-run`、コンソールの Verify ボタン、署名の自作テスト）と「実アカウントでは未確認の部分」を書く。

原因調べのとき（出力の形）:

```
原因の候補（可能性の高い順）
1. <原因> — 根拠: <公式の記述 or 手元の観測>
2. ...
確かめ方: <手順やコマンド>
直し方: <コード or 設定>
未確認: <手元の情報だけでは判断できない点>
```

通数・料金の質問:
- 計算は「送信回数 × 受信した友だちの数」。reply は含めない。式と結果を見せ、どのプランの無料枠に収まるかを答える。金額（円）が絡む追加メッセージは公式の単価表を見るよう案内する。

## 4. スクリプト

どちらも Python 3.9 の標準ライブラリだけ。`--help` あり。

- `python3 scripts/line_verify_signature.py --self-test` — 公式ドキュメントの例と自作のテストベクトルでこのスクリプトを確かめる。
- `LINE_CHANNEL_SECRET=... python3 scripts/line_verify_signature.py --body-file body.bin --signature "<ヘッダー値>" [--diagnose]` — 受信ボディ（保存したバイト列）の署名を検証。`--diagnose` は不一致のとき、末尾の改行・JSON 再生成・SHA1・hex のどれで合うかを調べる。`--sign` でテスト用の署名を作る。終了コード 0=一致、1=不一致、2=入力の不備。
- `python3 scripts/line_send.py push --to <userId> --text "..." --dry-run` — 送るリクエストをトークン伏せ字で表示（通信しない）。実送信は `--yes` が必要。環境変数 `LINE_CHANNEL_ACCESS_TOKEN`。メッセージは最大5件・テキスト5000文字（UTF-16）を事前に検査する。`reply --reply-token ...` も同様。終了コード 0=成功、1=APIエラー・通信失敗（原因と次の手を表示）、2=入力の不備。
- **実際に送る前に**、宛先と本文をユーザーに確認し、`--dry-run` の結果を見せる。送信は取り消せず、push は無料枠を消費する。

スクリプトを実行できない環境（外部通信が禁止のコード実行環境など）の代替: 署名検証は references の式（HMAC-SHA256 → Base64）を手元の言語で書いて確かめ、送信は `--dry-run` 相当の curl をユーザーに渡して自分の端末で実行してもらう。

## 5. 公式の一次情報（確認日 2026-10-21）

- 署名検証: https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/
- API リファレンス（reply・push・上限・レート制限・エラー）: https://developers.line.biz/en/reference/messaging-api/
- Messaging API の料金: https://developers.line.biz/en/docs/messaging-api/pricing/
- 日本の料金プラン（LINE for Business）: https://www.lycbiz.com/jp/service/line-official-account/plan/
- LINE Notify 終了のお知らせ: https://notify-bot.line.me/closing-announce

## 6. 既知の制限

- **実アカウントでの送受信は未検証。** 署名検証は公式ドキュメントの例と openssl の出力で一致を確認した。送信は手元のダミーサーバーに対するリクエストの形と、エラー応答の扱いまで。LINE 本番への実通信の成功は確認していない。
- 対象外: リッチメニューの画像制作、LINE以外のチャットサービス、LIFF アプリ全般。
- 料金は日本の LINE公式アカウントのみ。他の国・地域は公式の各ページを案内する。

=== FILE: references/pricing-and-notify.md ===
# 料金プラン（メッセージ通数）と LINE Notify の終了

**この表は変わりやすい。** 回答や見積もりの前に、必ず下の公式を開いて現行の値を確かめる。

## LINE公式アカウントの料金プラン（日本）

出典（確認日 2026-10-21）:
- https://www.lycbiz.com/jp/service/line-official-account/plan/ （LINE for Business の料金プラン）
- https://developers.line.biz/en/docs/messaging-api/pricing/ （Messaging API の料金。日本は上の LINE for Business へ誘導）

| プラン | 月額固定費（税別） | 無料メッセージ（月） | 追加メッセージ |
|---|---|---|---|
| コミュニケーションプラン | 0円 | 200通 | 不可 |
| ライトプラン | 5,000円 | 5,000通 | 不可 |
| スタンダードプラン | 15,000円 | 30,000通 | 従量課金（上限目安の設定が必要）。単価は配信数で異なり、上限は3円/通（税別）と記載 |

- 開設時はコミュニケーションプラン。ライト／スタンダードは開設後にプラン変更が必要。月の途中で上げると差額を払って、その月から枠が増える。
- 公式ページに「**2026年10月1日に追加メッセージ料金の改定を行いました**」とある。追加メッセージの単価の表は画像で、本文から読めなかった。追加メッセージの単価を答えるときは、このスキルで断定せず、公式の単価表（ページ内「追加メッセージの単価」）を見るよう案内する。
- 上限を超えて送ろうとすると、API は 429（`You have reached your monthly limit.`）でエラーを返し、送られない。
- 使用量の確認 API: `Get the target limit for sending messages this month`（今月の上限）、`Get number of messages sent this month`（今月の送信数）。

### 通数の数え方（「LINE Notify の代わり」「無料で何通」に答える核心）

- 通数 ＝ 「**送信回数 × 受信した友だちの数**」。1回の配信に入れるメッセージ（吹き出し）は、LINE公式アカウントの管理画面からの配信では最大3つ。Messaging API では1リクエスト最大5件だが、**通数はメッセージオブジェクトの件数では増えない**（公式の例: 4件を5人のトークルームへ push すると5通）。
- **数えられる**: Messaging API の Push / Multicast / Broadcast / Narrowcast。絞り込み配信・ステップ配信。
- **数えられない**: **Reply API**、応答メッセージ、あいさつメッセージ、LINEチャットの送受信。
- ブロックされている・存在しない userId への送信は、届かないので数えられない。
- 例（ライトプランの無料枠 5,000 通）: 友だち 100 人に毎日 1 回 push ＝ 100 通 × 30 日 ＝ 3,000 通／月 → ライトプランに収まる。コミュニケーションプラン（200 通）では 2 日で超える。自分1人への通知だけなら 1通 × 30日 ＝ 30通で、コミュニケーションプラン（無料）に収まる。
- 友だちから受け取ったメッセージへ reply で返す Bot は、通数を消費しない。

## LINE Notify の終了

出典（確認日 2026-10-21）:
- https://notify-bot.line.me/closing-announce （LINE Notify 提供終了のお知らせ）
- https://developers.line.biz/en/news/2025/04/01/line-notify/ （表題: LINE Notify service has been terminated as of March 31, 2025）

- LINE Notify は **2025年3月31日に提供を終了した**（終了のお知らせが「2025年3月31日にサービスを終了させていただく」、後日の開発者ニュースの表題が「終了しました」）。2026年現在、LINE Notify のトークンや API は使えない。
- 公式のお知らせは、代替として **Messaging API**（LINE公式アカウントからメッセージを送る）を案内し、「一定数のメッセージを毎月無料で送信できる」としている。
- 移行の考え方:
  1. LINE公式アカウントを作り、Messaging API のチャネルを作る（LINE Developers コンソール）。
  2. 通知を受け取りたい人（自分・家族・チーム）が、その公式アカウントを**友だち追加**する。
  3. 受け取る人の **userId** を知る必要がある。Webhook を受けるとイベントに userId が入る（友だち追加イベントやメッセージイベント）。自分用なら、公式アカウントに自分からメッセージを送り、webhook で userId を控える。
  4. 通知は `push`（または複数人なら `multicast`）で送る。無料枠は上の表（コミュニケーションプランは月 200 通）。
  5. グループに通知したいなら、公式アカウントをグループに招待（アカウント側で「グループ・複数人トークへの参加を許可」の設定が要る）し、webhook で得た groupId へ push する。
- Messaging API で通知を送るには、宛先の userId（または groupId）を知る手段が要る。userId は webhook のイベントで得るので、受け口になる HTTPS の URL を一度は用意する。ここが移行で最初につまずきやすい。

=== FILE: references/sending-and-limits.md ===
# 送信（reply / push）と上限

出典（確認日 2026-10-21）:
- https://developers.line.biz/en/reference/messaging-api/ （Send reply message / Send push message / Rate limits / Status codes / Error responses / Message objects / Retrying an API request）
- https://developers.line.biz/en/docs/messaging-api/sending-messages/
- https://developers.line.biz/en/docs/messaging-api/retrying-api-request/
- https://developers.line.biz/en/faq/ （429 の項）

数値は変わりうる。実装前に上の公式を見直すこと（確認日から90日を過ぎたら必ず）。

## reply と push の違い

| | reply（返信） | push（プッシュ） |
|---|---|---|
| エンドポイント | `POST https://api.line.me/v2/bot/message/reply` | `POST https://api.line.me/v2/bot/message/push` |
| 宛先の指定 | webhook イベントの `replyToken` | `to` に userId / groupId / roomId |
| いつ送れるか | イベントを受けた直後に限る | 好きなタイミング |
| 送れる相手の条件 | トークンを持っていれば足りる | 友だち、参加中のグループ・複数人トーク、または**1対1トークで7日以内にメッセージをくれたユーザー** |
| 通数（料金） | **数えられない** | **数えられる**（受信者の数 × 回数） |
| retry key | 使えない（付けると 400） | `X-Line-Retry-Key` を付けられる／付けるべき |
| 1リクエストのメッセージ数 | 最大5 | 最大5 |
| レート制限 | 2,000 リクエスト/秒（チャネル単位） | 2,000 リクエスト/秒（チャネル単位） |

### replyToken の扱い
- **1回しか使えない。** 受信から**1分以内**に使う（超えると動作の保証がない。制限時間は予告なく変わる。時間に頼らず、なるべく早く使う）。
- 再配信された webhook の replyToken は、再配信を受けてから1分以内なら使える。ただし、元の webhook で使用済み、またはイベント発生から20分経過のときは使えない。
- 期限切れ・使用済みで送ると 400 `Invalid reply token`。
- 1回の reply で最大5件のメッセージまで送れる。**2回目の reply はできない**ので、返したい内容は1回にまとめる。足りなければ push に切り替える（通数に数えられる）。
- 準備に時間がかかる返信は、先にローディングアニメーション（`Display a loading animation`）を出せる。

### push の注意
- 相手がブロックしている・アカウントを削除している・友だちでない（7日ルール外）場合も **HTTP 200 が返るが届かない**。200 ＝ 配達成功ではない。そのメッセージは通数に数えられない。
- `to` には webhook などで得た、**そのチャネル（プロバイダー）の** userId を使う。別プロバイダーのチャネルの userId は 400。
- 複数人に同じ内容なら multicast（最大500 userId。友だちのみ、グループ不可。200 リクエスト/秒）。全員向けは broadcast、条件指定は narrowcast（いずれも 60 リクエスト/時のレート制限があるので頻繁には送れない）。

## メッセージオブジェクトの上限

| 項目 | 上限 |
|---|---|
| 1リクエストの `messages` | 最大 **5** 件（reply・push・multicast・narrowcast・broadcast 共通） |
| テキスト（`text`）の長さ | 最大 **5000 文字**。数え方は **UTF-16 のコードユニット**（サロゲートペアの絵文字は2文字分）。Python は `len(s.encode("utf-16-le"))//2`、JavaScript は `s.length` |
| テキストに入れる LINE 絵文字（`emojis`） | 最大 20 |
| 画像 | `originalContentUrl` は HTTPS（TLS 1.2 以上）・JPEG/PNG・最大 10MB、`previewImageUrl` は最大 1MB。URL は最大 2000 文字 |
| 動画・音声 | ファイル最大 200MB（動画は preview 画像が別に要る） |
| クイックリプライ（`quickReply`） | 最大 13 個。複数メッセージのときは**最後のメッセージ**のものだけ表示される |
| リクエスト全体 | 最大 2MB（超えると 413） |
| メッセージの種類 | text / textV2 / sticker / image / video / audio / location / imagemap / template / flex / coupon |

送る前にメッセージ形式だけ検証する API がある（`Validate message objects of a reply/push/multicast/narrowcast/broadcast message`）。送信はされない。

## ステータスコードと原因

| コード | 主な原因 → 次の手 |
|---|---|
| 400 | 形式不正（`details[].property` に場所が出る）／`Invalid reply token`（期限切れ・使用済み）／reply に retry key を付けた／別プロバイダーの userId |
| 401 | チャネルアクセストークンが無効・別チャネルのもの → コンソールで再発行 |
| 403 | 権限なし（アカウントやプランの確認） |
| 409 | 同じ retry key が受理済み（二重送信にはなっていない）。`x-line-accepted-request-id` に受理済みのリクエスト ID |
| 413 | リクエストが 2MB 超 |
| 429 | (1) レート制限 (2) **無料メッセージ数・追加メッセージの上限を超えた**（本文に `You have reached your monthly limit.`）。(2) は、配信中の予約で一時的に残りが0になって、月の残りがあっても出ることがある（FAQ） |
| 500 | LINE 側のエラー。送信済みのことがあるので、retry key 付きで再試行 |

レート制限は**トークンバケット方式**（一定間隔でリセットされるのではなく、少しずつ回復する）。チャネル単位で、エンドポイント（HTTP メソッドも別扱い）ごとにかかる。

## 重複送信を防ぐ retry key

- push / multicast / narrowcast / broadcast にだけ付けられる。**最初のリクエストから必ず付ける**（付けていないリクエストは再試行できない）。
- 値は16進表記の UUID を自分で作る。管理期間は **24時間**。同じキーを24時間より後に使うと新しいリクエストとして送られ、重複する。
- 500 やタイムアウトのときだけ、同じキー・同じ内容で再試行する。409 が返れば受理済み。
- 受理（200）されたあとにブロックされていて届かなかった場合も、同じキーでは再送できない。

## Webhook を受ける側の要点
- 配信は HTTPS の POST。2xx 以外だと、再配信を有効にしていれば再配信される（回数・間隔は非公開で変わる）。
- 重複は `webhookEventId`、再配信かどうかは `deliveryContext.isRedelivery`。
- 送信元 IP は非公開。IP 制限ではなく署名検証で守る（署名検証の節を参照）。

=== FILE: references/webhook-examples.md ===
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

=== FILE: references/webhook-signature.md ===
# Webhook の署名検証

出典（確認日 2026-10-21）:
- https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/
- https://developers.line.biz/en/reference/messaging-api/#signature-validation
- https://developers.line.biz/en/docs/messaging-api/receiving-messages/

## 仕様（公式の記述）

| 項目 | 内容 |
|---|---|
| ヘッダー | `x-line-signature`。ヘッダー名の大文字小文字は通知なく変わる（`X-Line-Signature` と来ることもある）ので、区別せずに読む |
| アルゴリズム | HMAC-SHA256。HMAC-SHA1 などでは失敗する |
| 鍵 | そのチャネルの **チャネルシークレット**（LINE Developers コンソール → チャネル → Basic settings。Admin 権限が要る）。チャネルごとに違う |
| 入力 | **受け取ったリクエストボディの文字列そのまま**（UTF-8）。パース・整形・エスケープの解釈をしない |
| 出力 | Base64。ヘッダーの値と比べる（比較は定数時間で） |
| 不一致・ヘッダー無し | イベントを処理せず、エラーで終える |
| IP 制限 | LINE は webhook の送信元 IP を公開していない。IP ではなく署名で守る |

公式の手順例（openssl）:

```sh
echo -n '{"destination":"U8e742f61d673b39c7fff3cecb7536ef0","events":[]}' | openssl dgst -sha256 -hmac '8c570fa6dd201bb328f1c1eac23a96d8' -binary | openssl base64
# => GhRKmvmHys4Pi8DxkF4+EayaH0OqtJtaZxgTD9fMDLs=
```

この値は `python3 scripts/line_verify_signature.py --self-test` で再現できる（確認済み）。上のシークレットは公式ドキュメントに載っている見本で、実在のチャネルのものではない。

## 「署名が合わない」ときの原因（公式が挙げるもの＋実務で多いもの）

| 原因 | 見分け方・直し方 |
|---|---|
| ボディをパースしてから検証している | `json.loads` / `JSON.parse` / フレームワークの自動パース（Express の `express.json()`、Flask の `request.json`、FastAPI のモデル引数）より前に、生のバイト列を取る |
| 再シリアライズした文字列で検証している | `json.dumps` は区切りに空白を入れ、非 ASCII を `\u` にする。元の文字列と別物になる |
| 整形（インデント）した | 読みやすくするための整形は検証後にする |
| プロキシ・ロードバランサー・CDN・ミドルウェアがボディを書き換えた | 圧縮の解除・改行の変換・文字コード変換を疑う。受信直後の生のバイト列とヘッダーを保存して比べる |
| アルゴリズム違い（SHA1）／出力形式違い（hex） | Base64 でなく16進にしていないか |
| 別チャネルのシークレット | ボディの `destination`（ボットのユーザー ID）のチャネルのシークレットか。複数チャネルを扱うなら `destination` でシークレットを選ぶ |
| シークレットの再発行 | 他の開発者が再発行すると古い値は無効になる |
| エスケープ文字の解釈 | `\n` や `\"` を改行や引用符に直さない。Python のテストでは raw 文字列 |
| 文字コードが UTF-8 でない | LF→CRLF、絵文字の破損が起きる |
| 末尾の改行を足した・落とした | curl のテストで `-d` を使うと改行が落ちる／ファイル由来で改行が付く。`--data-binary` を使う |
| 環境変数の値に余計な空白・改行 | `.env` の読み込みで末尾に空白や引用符が付いていないか |

調べる順番:
1. ボディ（生のバイト列）とヘッダーの値をファイルに保存する（本番では漏れないよう、検証後すぐ消す）。
2. `python3 scripts/line_verify_signature.py --body-file body.bin --signature "<ヘッダーの値>" --diagnose` を実行する。改行・JSON 再生成・SHA1・hex のどれで合うかが出る。
3. どれでも合わなければ、シークレットの取り違え（別チャネル・再発行）を確かめる。

テスト用に自分で署名を作るとき: `python3 scripts/line_verify_signature.py --sign --body-file body.bin`（シークレットは環境変数）。

## 実装の最小形（検証済みの動作例）

どちらも「生のバイト列で検証 → 不一致は 400 → 先に 200 を返す → 処理は非同期」。Python 3.9 標準ライブラリ版は 別ファイル webhook-examples の「Python 3.9」の節。

要点:
- **検証が先、パースが後。**
- 200 を返すまでの時間制限は公式ドキュメントに数値がない。重い処理は非同期にし、先に 200 を返す（公式の推奨）。
- Webhook 再配信を有効にしている場合、2xx を返さないと再配信される。同じイベントが複数回届きうるので `webhookEventId` で重複を捨てる。順序は入れ替わりうるので、順番が大事なら `timestamp` を見る。
- `events` が空配列の確認用リクエストが来ることがある。署名を検証して 200 を返す。
- コンソールの「Verify」ボタンは、この空イベントの webhook を送る。

## SDK を使う場合

公式 SDK（line-bot-sdk-python / -nodejs / -java / -php など）は署名検証の関数を持つ。使うときも「生のボディ」を渡すこと（フレームワークがパース済みのオブジェクトを渡すと失敗する）。SDK のバージョンごとの関数名は変わるので、その版の README を読んでから書く。

=== FILE: scripts/line_send.py ===
#!/usr/bin/env python3
"""LINE Messaging API でプッシュ／リプライを送る（またはリクエストを組み立てて表示する）。

Python 3.9 の標準ライブラリだけで動く。

チャネルアクセストークンは環境変数 LINE_CHANNEL_ACCESS_TOKEN から読む（引数に書かない）。

使い方:
  # まず --dry-run。トークンは伏せ字で、送るリクエストをそのまま表示する（通信しない）
  python3 scripts/line_send.py push --to Uxxxxxxxx --text "こんにちは" --dry-run
  python3 scripts/line_send.py reply --reply-token <webhook の replyToken> --text "了解" --dry-run
  # 複数メッセージ・テキスト以外は JSON ファイル（messages の配列、最大5件）で渡す
  python3 scripts/line_send.py push --to Uxxxxxxxx --messages-file msgs.json --dry-run
  # 実際に送る（外部への送信になる。--yes が必須）
  python3 scripts/line_send.py push --to Uxxxxxxxx --text "こんにちは" --yes

ポイント:
  - push は X-Line-Retry-Key（UUID）を付ける（重複送信を防ぐ）。未指定なら自動で作って表示する。
    再試行するときは、表示された同じ値を --retry-key に渡す（24時間以内）。
  - reply は replyToken が1回限り・受信から約1分以内。retry key は reply では使えない（400 になる）。
  - push は通数に数えられる（料金プランの無料枠を消費）。reply は数えられない。

終了コード:
  0 送信に成功（--dry-run の表示も 0）
  1 API がエラーを返した／通信に失敗した（原因と次の手を表示）
  2 入力の不備（トークン未設定・件数や文字数の超過・--yes が無いなど）
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid

DEFAULT_BASE = "https://api.line.me"
TOKEN_ENV = "LINE_CHANNEL_ACCESS_TOKEN"
MAX_MESSAGES = 5          # 1リクエストのメッセージオブジェクト数の上限（公式 Messaging API reference）
MAX_TEXT_UNITS = 5000     # テキストの上限。UTF-16 のコードユニット数で数える（絵文字は2）


def utf16_len(s):
    """LINE が数えるのと同じ UTF-16 コードユニット数。"""
    return len(s.encode("utf-16-le")) // 2


def build_messages(args):
    """--text か --messages-file から messages 配列を作る。不備があれば ValueError。"""
    if args.messages_file:
        try:
            with open(args.messages_file, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            raise ValueError("--messages-file を読めません（%s）。UTF-8 の JSON 配列にしてください。" % e)
        if isinstance(data, dict) and "messages" in data:
            data = data["messages"]
        if not isinstance(data, list):
            raise ValueError("--messages-file は messages の配列（または {\"messages\": [...]}）にしてください。")
        messages = data
    elif args.text:
        messages = [{"type": "text", "text": t} for t in args.text]
    else:
        raise ValueError("送る内容がありません。--text か --messages-file を指定してください。")
    if not 1 <= len(messages) <= MAX_MESSAGES:
        raise ValueError("メッセージは1〜%d件です（今は%d件）。1リクエストの上限なので、分けて送ってください。"
                         % (MAX_MESSAGES, len(messages)))
    for i, m in enumerate(messages):
        if not isinstance(m, dict) or "type" not in m:
            raise ValueError("messages[%d] に type がありません。" % i)
        if m["type"] == "text":
            t = m.get("text", "")
            if not isinstance(t, str) or not t:
                raise ValueError("messages[%d].text が空です。" % i)
            n = utf16_len(t)
            if n > MAX_TEXT_UNITS:
                raise ValueError("messages[%d].text が %d 文字（UTF-16）で上限 %d を超えています。分割してください。"
                                 % (i, n, MAX_TEXT_UNITS))
    return messages


def build_request(args, messages, token):
    base = args.base_url.rstrip("/")
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + token}
    if args.cmd == "push":
        url = base + "/v2/bot/message/push"
        body = {"to": args.to, "messages": messages}
        headers["X-Line-Retry-Key"] = args.retry_key
    else:
        url = base + "/v2/bot/message/reply"
        body = {"replyToken": args.reply_token, "messages": messages}
    if args.no_notification:
        body["notificationDisabled"] = True
    return url, headers, body


def mask(token):
    """トークンを伏せ字にする（長さも分からないよう固定表記）。"""
    return "Bearer ***MASKED***" if token else "Bearer (未設定)"


def explain_error(status, text):
    """HTTP ステータスと本文から、原因と次の手の説明を返す。"""
    msg = ""
    try:
        msg = json.loads(text).get("message", "")
    except (ValueError, AttributeError):
        pass
    if status == 400 and "Invalid reply token" in msg:
        return ("replyToken が期限切れか使用済みです（1回限り・受信から約1分以内）。"
                "遅れて返したい場合は、ユーザー ID を使って push に切り替えます（通数に数えられる）。")
    if status == 400:
        return ("リクエストの形式が不正です。本文の details（property）を見て該当の項目を直します。"
                "reply に X-Line-Retry-Key は使えません。")
    if status == 401:
        return ("チャネルアクセストークンが無効です。LINE Developers コンソールの Messaging API タブで発行し直し、"
                "環境変数 %s を更新してください（別チャネルのトークンも 401 になります）。" % TOKEN_ENV)
    if status == 403:
        return "この API を使う権限がありません。アカウントやプランを確認してください。"
    if status == 409:
        return ("同じ retry key のリクエストは受理済みです。もう送信されています。"
                "新しい内容を送るなら新しい UUID を使ってください。")
    if status == 413:
        return "リクエストが 2MB を超えています。小さくしてください。"
    if status == 429:
        return ("レート制限か、月の無料メッセージ数・追加上限の超過です。メッセージに 'monthly limit' とあれば通数の枠です"
                "（料金プランを確認。配信中の予約で一時的に残りが0になることもある）。それ以外は間隔をあけて再試行します。")
    if status >= 500:
        return ("LINE 側のエラーです。送信済みの可能性があるため、同じ retry key（push）で再試行すると二重送信になりません。")
    return "想定外の応答です。X-Line-Request-Id を控えて LINE のサポートへ問い合わせられます。"


def main(argv=None):
    p = argparse.ArgumentParser(
        description="LINE Messaging API のプッシュ／リプライ送信。トークンは環境変数から読む。",
        epilog="終了コード: 0=成功 1=APIエラー・通信失敗 2=入力の不備。まず --dry-run で確かめる。")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("push", "reply"):
        s = sub.add_parser(name, help="プッシュ送信" if name == "push" else "リプライ送信")
        if name == "push":
            s.add_argument("--to", required=True, help="送り先の userId / groupId / roomId")
            s.add_argument("--retry-key", help="X-Line-Retry-Key（UUID）。未指定なら自動生成して表示")
        else:
            s.add_argument("--reply-token", required=True, help="webhook イベントの replyToken（1回限り・約1分以内）")
        s.add_argument("--text", action="append", help="テキストメッセージ（複数回指定で複数件、最大5件）")
        s.add_argument("--messages-file", help="messages の配列を書いた JSON ファイル（テキスト以外はこちら）")
        s.add_argument("--no-notification", action="store_true", help="通知を鳴らさない（notificationDisabled）")
        s.add_argument("--dry-run", action="store_true", help="通信せず、トークンを伏せたリクエストを表示する")
        s.add_argument("--yes", action="store_true", help="実際に送信することを確認済みとする（外部送信に必須）")
        s.add_argument("--base-url", default=DEFAULT_BASE, help="API のベース URL（テスト用。既定 %s）" % DEFAULT_BASE)
    args = p.parse_args(argv)

    try:
        messages = build_messages(args)
    except ValueError as e:
        print("エラー: %s" % e, file=sys.stderr)
        return 2

    if args.cmd == "push":
        if not args.retry_key:
            args.retry_key = str(uuid.uuid4())
            print("retry key を自動生成しました: %s（再試行するときはこの値を --retry-key に）" % args.retry_key,
                  file=sys.stderr)
        else:
            try:
                uuid.UUID(args.retry_key)
            except ValueError:
                print("エラー: --retry-key は UUID（例 123e4567-e89b-12d3-a456-426614174000）にしてください。",
                      file=sys.stderr)
                return 2

    token = os.environ.get(TOKEN_ENV, "")
    if not token and not args.dry_run:
        print("エラー: 環境変数 %s が未設定です。\n"
              "次の手: LINE Developers コンソールの Messaging API タブでチャネルアクセストークンを発行し、"
              "`export %s=...` してから再実行してください（値をコマンドや会話に貼らないこと）。" % (TOKEN_ENV, TOKEN_ENV),
              file=sys.stderr)
        return 2

    url, headers, body = build_request(args, messages, token)

    if args.dry_run:
        print("DRY-RUN（通信しません）")
        print("POST " + url)
        for k, v in headers.items():
            print("%s: %s" % (k, mask(token) if k == "Authorization" else v))
        print(json.dumps(body, ensure_ascii=False, indent=2))
        if not token:
            print("注: %s が未設定です。実送信には必要です。" % TOKEN_ENV)
        return 0

    if not args.yes:
        print("エラー: 実際に送信するには --yes が必要です（外部への送信で、取り消せません）。\n"
              "次の手: 先に --dry-run で宛先と内容を確認し、問題なければ --yes を付けて再実行してください。",
              file=sys.stderr)
        return 2

    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            text = res.read().decode("utf-8", "replace")
            print("成功: HTTP %d  X-Line-Request-Id: %s" % (res.status, res.headers.get("X-Line-Request-Id", "-")))
            if text.strip():
                print(text)
            return 0
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", "replace")
        print("失敗: HTTP %d  X-Line-Request-Id: %s" % (e.code, e.headers.get("X-Line-Request-Id", "-")), file=sys.stderr)
        if text.strip():
            print(text, file=sys.stderr)
        print("原因と次の手: " + explain_error(e.code, text), file=sys.stderr)
        return 1
    except (urllib.error.URLError, OSError) as e:
        print("失敗: 通信できませんでした（%s）。\n"
              "次の手: ネットワークを確認する。コード実行環境が外部通信を禁止している場合は、--dry-run の出力を"
              "自分の端末で curl に貼って実行する。push は同じ retry key で再試行しても二重送信になりません。" % e,
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

=== FILE: scripts/line_verify_signature.py ===
#!/usr/bin/env python3
"""LINE Messaging API の Webhook 署名（x-line-signature）を検証する。

Python 3.9 の標準ライブラリだけで動く。外部へ通信しない。

使い方:
  # 受け取った生のボディをファイルに保存してあるとき
  LINE_CHANNEL_SECRET=... python3 scripts/line_verify_signature.py \
      --body-file body.bin --signature "GhRKmv...="
  # ボディを標準入力から渡すとき
  cat body.bin | python3 scripts/line_verify_signature.py --body-stdin --signature "..."
  # 合わないとき、よくある原因（改行・整形・SHA1・hex）のどれで合うかを探す
  ... --diagnose
  # 自分でテスト用の署名を作る
  ... --sign --body-file body.bin
  # 公式ドキュメントのテストベクトルと自作ベクトルで、このスクリプト自体を確かめる
  python3 scripts/line_verify_signature.py --self-test

チャネルシークレットは環境変数（既定 LINE_CHANNEL_SECRET）から読む。
コマンドラインに直接書かない（履歴に残るため）。

終了コード:
  0 一致（--sign / --self-test の成功も 0）
  1 不一致（--diagnose のときは原因の候補を表示）
  2 入力の不備（シークレット未設定・ボディ未指定・署名が空など）
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import sys

# 公式ドキュメント「Verify webhook signature」の例。
# https://developers.line.biz/en/docs/messaging-api/verify-webhook-signature/ （確認日 2026-10-21）
# この channel secret はドキュメントに載っている見本で、実在のチャネルのものではない。
OFFICIAL_BODY = '{"destination":"U8e742f61d673b39c7fff3cecb7536ef0","events":[]}'
OFFICIAL_SECRET = "8c570fa6dd201bb328f1c1eac23a96d8"
OFFICIAL_SIGNATURE = "GhRKmvmHys4Pi8DxkF4+EayaH0OqtJtaZxgTD9fMDLs="


def make_signature(secret, body):
    """body(bytes) に HMAC-SHA256 をかけて Base64 にした署名を返す。"""
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def verify(secret, body, signature):
    """署名が一致すれば True。比較は定数時間で行う。"""
    expected = make_signature(secret, body)
    return hmac.compare_digest(expected.encode("ascii"), signature.strip().encode("utf-8", "replace"))


def diagnose(secret, body, signature):
    """よくある失敗のそれぞれで署名を作り直し、受け取った署名と合うものを探す。

    見つかった候補の説明（日本語）のリストを返す。見つからなければ空リスト。
    """
    sig = signature.strip()
    found = []

    def check(label, data, algo="sha256", encoding="base64"):
        mac = hmac.new(secret.encode("utf-8"), data, getattr(hashlib, algo)).digest()
        out = base64.b64encode(mac).decode("ascii") if encoding == "base64" else mac.hex()
        if hmac.compare_digest(out.encode("ascii"), sig.encode("utf-8", "replace")):
            found.append(label)

    check("アルゴリズムが HMAC-SHA1 になっている（HMAC-SHA256 にする）", body, algo="sha1")
    check("Base64 ではなく16進（hex）で出力している（Base64 にする）", body, encoding="hex")
    if body.endswith(b"\r\n"):
        check("ボディ末尾の CRLF を足している／残している（LINE が送った文字列そのままにする）", body[:-2])
    if body.endswith(b"\n"):
        check("ボディ末尾に改行が付いている（LINE が送った文字列そのままにする）", body[:-1])
    else:
        check("ボディ末尾の改行を落としていない／足していない可能性（末尾に LF を足すと合う）", body + b"\n")
    if b"\r\n" in body:
        check("改行が CRLF になっている（受信ボディの改行コードを変えない）", body.replace(b"\r\n", b"\n"))
    elif b"\n" in body:
        check("改行が LF のまま（CRLF に変換されると合わなくなる。受信そのままにする）", body.replace(b"\n", b"\r\n"))
    try:
        parsed = json.loads(body.decode("utf-8"))
        compact = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        compact_ascii = json.dumps(parsed, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        spaced = json.dumps(parsed, ensure_ascii=False).encode("utf-8")
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False).encode("utf-8")
        if compact != body:
            check("JSON をパースして作り直したあとの文字列（コンパクト）で検証している", compact)
        if compact_ascii != body:
            check("JSON を再シリアライズして非 ASCII を \\u エスケープにしている", compact_ascii)
        if spaced != body:
            check("JSON を再シリアライズして区切りに空白が入っている（Python の json.dumps 既定など）", spaced)
        if pretty != body:
            check("JSON を整形（インデント）してから検証している", pretty)
    except (ValueError, UnicodeDecodeError):
        found.append("ボディが UTF-8 の JSON として読めない（文字コードの変換や途中の改変を疑う）")
    if body.startswith(b"\xef\xbb\xbf"):
        check("ボディ先頭に BOM が付いている（取り除くと合う）", body[3:])
    return found


def read_body(args):
    if args.body_file:
        with open(args.body_file, "rb") as f:
            return f.read()
    if args.body_stdin:
        return sys.stdin.buffer.read()
    if args.body_text is not None:
        return args.body_text.encode("utf-8")
    return None


def self_test():
    ok = True

    def expect(name, cond):
        nonlocal ok
        print(("  OK  " if cond else "  NG  ") + name)
        ok = ok and cond

    body = OFFICIAL_BODY.encode("utf-8")
    expect("公式の例: 署名を作ると公式の値と一致する",
           make_signature(OFFICIAL_SECRET, body) == OFFICIAL_SIGNATURE)
    expect("公式の例: verify が一致と判定する", verify(OFFICIAL_SECRET, body, OFFICIAL_SIGNATURE))
    expect("公式の例: 1文字違う署名は不一致", not verify(OFFICIAL_SECRET, body, OFFICIAL_SIGNATURE[:-2] + "X="))
    expect("公式の例: 違うシークレットは不一致", not verify("0" * 32, body, OFFICIAL_SIGNATURE))
    pretty = json.dumps(json.loads(OFFICIAL_BODY), indent=2).encode("utf-8")
    expect("公式の例: 整形し直したボディは不一致（パースしてから検証すると失敗する）",
           not verify(OFFICIAL_SECRET, pretty, OFFICIAL_SIGNATURE))
    pretty_sig = make_signature(OFFICIAL_SECRET, pretty)
    expect("診断: 整形（インデント）後のボディで作った署名の原因を見つける（署名側は整形後のボディで作成）",
           any("整形" in x for x in diagnose(OFFICIAL_SECRET, body, pretty_sig)))

    # 自作ベクトル: 日本語・絵文字・エスケープを含む本文。openssl でも同じ値になることを別途確認してある。
    own_secret = "test-secret-not-real-0123456789"
    own_body = ('{"destination":"Uffffffffffffffffffffffffffffffff","events":[{"type":"message",'
                '"message":{"type":"text","text":"こんにちは\\n世界 \U0001F600 \\"quote\\""},'
                '"replyToken":"dummy-reply-token"}]}').encode("utf-8")
    own_sig = make_signature(own_secret, own_body)
    expect("自作ベクトル: 自分で作った署名を verify が受け入れる", verify(own_secret, own_body, own_sig))
    expect("自作ベクトル: 末尾に改行が付くと不一致", not verify(own_secret, own_body + b"\n", own_sig))
    d = diagnose(own_secret, own_body + b"\n", own_sig)
    expect("診断: 末尾の改行が原因だと指摘する", any("改行" in x for x in d))
    sha1 = base64.b64encode(hmac.new(own_secret.encode(), own_body, hashlib.sha1).digest()).decode()
    expect("診断: SHA1 で作った署名を見分ける", any("SHA1" in x for x in diagnose(own_secret, own_body, sha1)))
    hexsig = hmac.new(own_secret.encode(), own_body, hashlib.sha256).hexdigest()
    expect("診断: hex 出力を見分ける", any("16進" in x for x in diagnose(own_secret, own_body, hexsig)))
    parsed_body = json.dumps(json.loads(own_body.decode("utf-8")), ensure_ascii=False).encode("utf-8")
    expect("診断: json.dumps で作り直した文字列を見分ける",
           any("json" in x.lower() or "JSON" in x for x in diagnose(own_secret, own_body, make_signature(own_secret, parsed_body))))
    print("self-test: " + ("すべて成功" if ok else "失敗あり"))
    return 0 if ok else 1


def main(argv=None):
    p = argparse.ArgumentParser(
        description="LINE Webhook の署名（x-line-signature）を HMAC-SHA256 + Base64 で検証する。",
        epilog="終了コード: 0=一致 1=不一致 2=入力の不備。シークレットは環境変数から読む。")
    p.add_argument("--signature", help="x-line-signature ヘッダーの値")
    p.add_argument("--body-file", help="受け取った生のリクエストボディを保存したファイル（バイト列のまま）")
    p.add_argument("--body-stdin", action="store_true", help="生のボディを標準入力から読む")
    p.add_argument("--body-text", help="ボディを引数で渡す（改行・エスケープが変わりやすいので --body-file を推奨）")
    p.add_argument("--secret-env", default="LINE_CHANNEL_SECRET",
                   help="チャネルシークレットが入っている環境変数名（既定 LINE_CHANNEL_SECRET）")
    p.add_argument("--diagnose", action="store_true", help="不一致のとき、よくある原因のどれで合うかを探す")
    p.add_argument("--sign", action="store_true", help="検証せず、ボディから署名を作って表示する（テスト用）")
    p.add_argument("--self-test", action="store_true", help="公式の例と自作ベクトルでこのスクリプトを確かめる")
    args = p.parse_args(argv)

    if args.self_test:
        return self_test()

    secret = os.environ.get(args.secret_env, "")
    if not secret:
        print("エラー: 環境変数 %s にチャネルシークレットが入っていません。\n"
              "次の手: LINE Developers コンソールの Basic settings でチャネルシークレットを確認し、"
              "`export %s=...` を実行してから再実行してください（値をコマンドや会話に貼らないこと）。"
              % (args.secret_env, args.secret_env), file=sys.stderr)
        return 2
    try:
        body = read_body(args)
    except OSError as e:
        print("エラー: ボディを読めません（%s）。--body-file のパスを確かめてください。" % e, file=sys.stderr)
        return 2
    if body is None:
        print("エラー: ボディが指定されていません。--body-file か --body-stdin を付けてください。", file=sys.stderr)
        return 2

    if args.sign:
        print(make_signature(secret, body))
        return 0

    if not args.signature or not args.signature.strip():
        print("エラー: --signature が空です。x-line-signature ヘッダーの値を渡してください。"
              "ヘッダーが無いリクエストは LINE からのものではないので、処理せずエラーで終えます。", file=sys.stderr)
        return 2

    if verify(secret, body, args.signature):
        print("一致: 署名は正しい（このボディは LINE から届き、改変されていません）。")
        return 0

    print("不一致: 署名が合いません。ボディ %d バイト。" % len(body))
    if args.diagnose:
        cands = diagnose(secret, body, args.signature)
        if cands:
            print("原因の候補:")
            for c in cands:
                print("  - " + c)
        else:
            print("よくある原因のどれでも合いませんでした。次に確かめること:")
            print("  - チャネルシークレットが別のチャネルのものではないか（ボディの destination のボットのチャネルか）")
            print("  - シークレットを再発行されていないか（コンソールの Basic settings）")
            print("  - プロキシ・ロードバランサー・フレームワークがボディを書き換えていないか（生のバイト列を取る設定か）")
            print("  - 保存したボディが、受信したそのままか（コピー時に改行や空白が変わっていないか）")
    else:
        print("次の手: --diagnose を付けると、改行・JSON 整形・SHA1・hex などのどれで合うかを調べます。")
    return 1


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
