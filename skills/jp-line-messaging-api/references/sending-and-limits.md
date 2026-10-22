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
