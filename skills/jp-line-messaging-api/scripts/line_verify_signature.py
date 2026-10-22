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
