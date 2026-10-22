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
