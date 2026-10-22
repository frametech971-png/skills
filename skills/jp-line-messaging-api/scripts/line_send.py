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
