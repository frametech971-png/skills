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
