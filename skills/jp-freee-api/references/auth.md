# freee API の認証（OAuth2）とトークン

確認日 2026-10-22。**確認日から90日を過ぎたら、下の公式ページを読み直してから使う。**

出典（すべて freee 公式の開発者サイト、2026-10-22 に取得）
- 認可の概要: https://developer.freee.co.jp/reference/%e8%aa%8d%e5%8f%af%e3%82%b3%e3%83%bc%e3%83%89
- アクセストークンを取得する: https://developer.freee.co.jp/startguide/getting-access-token
- トークンの有効期限について: https://developer.freee.co.jp/reference/faq/token_lifetime
- 【重要】リフレッシュトークンの有効期限の変更（2023-05-30 のお知らせ）: https://developer.freee.co.jp/news/6540
- 事業所の選択について: https://developer.freee.co.jp/reference/select-company
- アプリタイプ: https://developer.freee.co.jp/reference/application-types

## 1. 流れ（認可コードフロー。公式が推奨）

1. アプリを作る（freeeアプリストアの開発者向けアプリ管理）。**Client ID と Client Secret** が出る。コールバックURLを設定する。ローカルの試験だけ `urn:ietf:wg:oauth:2.0:oob`（画面に認可コードが表示される）。それ以外は自分の https URL にする（公式の注意）。
2. 認可URLをブラウザで開く（アプリ管理画面の「基本設定」に表示される）。ユーザーがログインして「許可する」を押すと認可コードが出る:
   `https://accounts.secure.freee.co.jp/public_api/authorize?response_type=code&client_id={client_id}&redirect_uri={エンコードしたコールバックURL}&state={ランダム文字列}&prompt=select_company`
   `state` は戻ってきた値と一致するか必ず確かめる（CSRF 対策）。
3. 認可コードをアクセストークンに換える:
   ```
   POST https://accounts.secure.freee.co.jp/public_api/token
   Content-Type: application/x-www-form-urlencoded
   grant_type=authorization_code&client_id=…&client_secret=…&code=…&redirect_uri=…
   ```
   応答: `access_token` / `token_type: bearer` / `expires_in: 21600` / `refresh_token` / `scope` / `created_at` / `company_id` / `external_cid`
4. API には `Authorization: Bearer {access_token}` を付けて呼ぶ。
5. 期限前に更新する:
   ```
   POST https://accounts.secure.freee.co.jp/public_api/token
   grant_type=refresh_token&client_id=…&client_secret=…&refresh_token=…
   ```
6. 失効させる: `POST https://accounts.secure.freee.co.jp/public_api/revoke`（`token=` にアクセストークンかリフレッシュトークン）。

## 2. 有効期限

| もの | 期限 | 出典 |
|---|---|---|
| アクセストークン | **6時間**（`expires_in: 21600`） | token_lifetime / getting-access-token |
| リフレッシュトークン | **発行後90日**（2023-12 頃に「期限なし」から変更） | token_lifetime / news/6540 |
| 認可コード | **要確認**（公式ページで数値を確認できなかった。短時間で、1回しか使えない前提で扱う） | — |

**リフレッシュトークンは1回しか使えない。** 更新するたびに新しいリフレッシュトークンが返るので、その都度保存し直す。同じものを2回使うと `invalid_grant`／401 になる（リトライで二重に送る・更新前のアクセストークンを revoke した、が典型）。90日以内に1回は更新しないと再認可になる。

注意: アクセストークン取得ページの本文に「リフレッシュトークンには有効期限はありません」という古い記述が残っている（同じページに「90日に変更される予定」とも書いてある）。**FAQ とお知らせの「90日」を正とする。** ネット上の古い記事（アクセストークン24時間・リフレッシュ無期限）も採らない。

## 3. 事業所ID（company_id）

- 認可URLに `prompt=select_company` を付けた（既定の）場合、**トークン応答に `company_id` が入る**。トークンと一緒に保存する。
- 後から調べる: `GET https://api.freee.co.jp/api/1/companies`（`Authorization: Bearer …`）。応答の `companies[].id` が、他の API の `company_id` に渡す値。`company_number`（10桁の英数字）は別物で、API の `company_id` には使えない。
- `prompt=select_company` を外した認可だと、そのユーザーが所属する**全事業所**にアクセスできるが、アプリ側で事業所を選ばせる実装が必須（アプリストア公開時の審査項目）。既定のままが公式推奨。

## 4. アプリ登録・利用の前提

- freee のアカウントがあり、**従業員として所属する事業所**でアプリを作る（顧問先として招待されただけの事業所では作れない）。アプリ名と概要を入れると Client ID/Secret が出る。
- アプリタイプは**作成後に変えられない**: プライベートアプリ（特定事業所用。利用事業所は5以下。ストア掲載不可）／パブリックアプリ（配布用。既定で20事業所以下、ストア公開か申請で無制限）。自社の事業所だけで使うならプライベート。
- 開発用テスト事業所と無料の開発者アカウントがある（freee 公式のスタートガイド https://developer.freee.co.jp/startguide ）。本番データに触れずに試せる。
- アプリの「権限設定」で、使うデータ（取引の参照・更新など）にチェックを入れる。権限を変えたら**トークンを取り直す**（古いトークンは古い権限のまま）。
- **鍵（Client Secret・アクセストークン・リフレッシュトークン）をコード・Git・チャットに書かない。** 環境変数か秘密情報の保管庫から読む。保存したリフレッシュトークンの読み書きは、書き込みが失敗しても古い値が消えない順序（新しい値を書いてから古い値を捨てる）にする。
