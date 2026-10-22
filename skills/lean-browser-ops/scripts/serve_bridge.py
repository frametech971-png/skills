#!/usr/bin/env python3
"""ブラウザのページ内 JS からローカルファイルを読ませるための一時サーバー。

使い方:
  python3 serve_bridge.py <公開するフォルダ> --origin <ページのオリジン> [--port 8765] [--max-seconds 600]

  例: python3 serve_bridge.py ./bridge-tmp --origin https://example.com
      ページ側: await (await fetch('http://127.0.0.1:8765/body.md')).text()

- 127.0.0.1 だけで待ち受ける。公開するのは指定フォルダの中のファイルだけ（一覧は出さない）。
- CORS で許すのは --origin に書いたオリジン1つだけ（ワイルドカードにしない）。
- 公開するフォルダは、必要なファイルだけを入れた一時フォルダにする。ホーム・ルート・
  .ssh や .aws を含むフォルダは拒否する。
- --max-seconds（既定 600）を過ぎると自動で終了する。終わったら Ctrl+C か
  `pkill -f serve_bridge.py` でも止める。
終了コード: 0 正常終了 / 2 引数・フォルダの問題 / 3 ポートが使えない
"""
import argparse
import http.server
import os
import socketserver
import sys
import threading

DENY_NAMES = {".ssh", ".aws", ".gnupg", ".git", ".env"}


def check_root(root):
    home = os.path.realpath(os.path.expanduser("~"))
    if root in (home, os.path.dirname(home), os.sep):
        return "ホーム・ルートは公開できません。必要なファイルだけを入れた一時フォルダを作って指定してください"
    for dirpath, dirnames, filenames in os.walk(root):
        hit = DENY_NAMES.intersection(dirnames) | DENY_NAMES.intersection(filenames)
        if hit:
            return "公開フォルダに %s が含まれています（%s）。一時フォルダへ必要なファイルだけコピーしてください" % (
                ", ".join(sorted(hit)), dirpath)
    return None


def make_handler(origin):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            super().end_headers()

        def do_OPTIONS(self):
            self.send_response(204)
            self.end_headers()

        def list_directory(self, path):
            self.send_error(404, "no listing")
            return None

        def log_message(self, *args):
            pass

    return Handler


def main():
    ap = argparse.ArgumentParser(description="ページ内 JS にローカルファイルを渡す一時サーバー（127.0.0.1 専用）")
    ap.add_argument("folder", help="公開するフォルダ（必要なファイルだけを入れた一時フォルダ）")
    ap.add_argument("--origin", required=True, help="fetch するページのオリジン（例: https://example.com）")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--max-seconds", type=int, default=600, help="この秒数で自動終了（既定 600）")
    args = ap.parse_args()

    if args.origin == "*":
        print("✗ --origin に * は指定できません。ページのオリジンを書いてください", file=sys.stderr)
        return 2
    root = os.path.realpath(args.folder)
    if not os.path.isdir(root):
        print("✗ フォルダが無い: %s" % args.folder, file=sys.stderr)
        return 2
    problem = check_root(root)
    if problem:
        print("✗ " + problem, file=sys.stderr)
        return 2
    os.chdir(root)

    socketserver.TCPServer.allow_reuse_address = True
    try:
        srv = socketserver.TCPServer(("127.0.0.1", args.port), make_handler(args.origin))
    except OSError as e:
        print("✗ ポート %d を使えません（%s）。--port で別の番号を指定するか、前のサーバーを止めてください" % (args.port, e),
              file=sys.stderr)
        return 3

    timer = threading.Timer(args.max_seconds, srv.shutdown)
    timer.daemon = True
    timer.start()
    print("公開中: http://127.0.0.1:%d/ （%s、%d秒で自動終了、許可オリジン %s）" % (args.port, root, args.max_seconds, args.origin),
          flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        timer.cancel()
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
