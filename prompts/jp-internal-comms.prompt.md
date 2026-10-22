<!-- jp-internal-comms v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-internal-comms（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-internal-comms
description: >-
  日本の職場で使う社内文書（日報・週報・3P報告・議事録・稟議書・社内通達・社内報・障害報告とお詫び・社内FAQ）を、型に沿って書く。「日報を書いて」「議事録にまとめて」「稟議書の文面を作って」「障害報告を書いて」「週報を3行で」「全社向けのお知らせを作って」と頼まれたときに使う。メモや箇条書きの素材から整える。素材に無い数字・日付・担当者は作らず「要確認」に回し、「来週水曜」などの相対日付は曜日つきの日付に直す。Keywords: daily report, weekly update, 3P update, meeting minutes, ringi, approval request, incident report, internal announcement。社外向けの文書（プレスリリース・お客様へのお詫び）、契約書・就業規則、文章の自然さだけを直す依頼は対象外。
license: Apache-2.0
metadata:
  version: "1.0.0"
  author: frametech
---

# 日本の社内文書

元: https://github.com/anthropics/skills@dbd4588（Apache-2.0、`skills/internal-comms`）を改変

目的: 日報・週報・議事録・稟議書・社内通達・障害報告などを、日本の職場でそのまま出せる型で書く。
入力: メモ・箇条書き・チャットのログ・会議の書き起こし。足りない情報は聞く（下記）。
出力: 本文だけを返し、末尾に「要確認」の一覧を付ける。

## 1. 型を選ぶ

| 頼まれたこと | 読むファイル |
|---|---|
| 日報（営業日報を含む） | [references/daily-report.md](references/daily-report.md) |
| 週報・3P（進捗・計画・課題） | [references/weekly-3p.md](references/weekly-3p.md) |
| 議事録・会議メモ | [references/minutes.md](references/minutes.md) |
| 稟議書・起案・購入や契約の申請 | [references/ringi.md](references/ringi.md) |
| 障害報告・インシデント報告・社内向けのお詫び | [references/incident.md](references/incident.md) |
| 社内通達・全社向けのお知らせ・社内報・社内FAQ | [references/announcement.md](references/announcement.md) |

どれにも当てはまらないときは、宛先・目的・口調（丁寧／カジュアル／緊急）の3つだけ聞く。複数の型にまたがるときは、主な型のファイルを読み、他は必要な節だけ借りる。

## 2. 書く前に確かめること

素材に無いものだけ、**1回にまとめて**聞く。聞かずに進められるものは、仮置きして「要確認」に載せる。

- 宛先（上長・チーム・全社）と、書き手の立場
- 対象期間・会議の日時・今日の日付（相対日付の基準になる）
- 素材。Slack・メール・ドキュメント・カレンダーを読める連携があれば、まずそこから集める。無ければ箇条書きでもらう

## 3. 共通ルール

- **素材に無い数字・日付・金額・人名・原因を作らない。** 必要なのに無いものは本文に `【要確認】` と置き、末尾の一覧にも書く。推測は「推定」「可能性」と明示して事実と分ける。
- **相対日付は日付に直す。** 「来週水曜」「再来週の月曜」「今週中」は、基準日から `10月28日（水）` の形にする。曜日を頭の中で計算しない。`node scripts/jpdate.mjs --help` で曜日・期間・営業日後を出せる。実行できない環境では、確かな基準日（会議の日付）から数えて曜日を示し、不安なら「要確認」に回す。
- 日付は日本時間。年をまたぐ文書は年から書く。和暦は、会社の規程や官公庁向けで求められたときだけ。
- 金額は円。税込か税抜かを必ず書き、両方わかるなら併記する。桁区切りは半角カンマ、数字は半角。
- 結論（決定・依頼・お願い）を先頭に置く。経緯は後。
- 敬語は上長宛でも `です・ます` を基本にし、「させていただく」を重ねない。メールやチャットの書き出しの「お疲れ様です」は入れてよいが、文書の本文（日報・議事録・稟議書）には入れない。
- 社内で通じる略語と部署名は素材のまま使う。勝手に正式名称へ直さない。
- 画面1枚（約400〜800字）に収まらない文書は、先頭に3行の要約を置く。

## 4. 返す形

```
（本文）

---
要確認
- 項目: 理由（例: 予算科目 — 素材に無い）
```

要確認が無ければ「要確認: なし」と1行書く。

## 5. 実行環境が無いとき

`scripts/jpdate.mjs` は Node 18 以上で動く、日付の計算だけのスクリプト。実行できない環境では §3 のとおり基準日から数える。外部へ通信せず、ファイルも書かない。

=== FILE: references/announcement.md ===
# 社内通達・社内報・社内FAQ

## 社内通達（全社・部門へのお知らせ）

```
件名: 【依頼】10月30日（金）までにパスワードの変更をお願いします
対象: 全従業員　発信: ＜部署＞　問い合わせ: ＜窓口＞

＜1文: 誰に何をお願いするか・いつまでに＞

■ 内容
- ＜やること1＞
- ＜やること2＞

■ 期限
10月30日（金）17:00

■ 背景（任意・短く）
＜なぜ必要か＞
```

- 件名の頭に種類のタグを付ける: 【重要】【依頼】【周知】【共有】。迷ったら【周知】。
- **期限・対象者・問い合わせ先**の3つは必須。素材に無ければ要確認。
- 背景は最後。長くなるなら別ドキュメントへのリンクにする。
- 「再来週の月曜」などは日付（曜日つき）に直す。

## 社内報・ニュースレター（週次／月次）

- 全社に関わる話を優先し、チーム内の細かい進捗は載せない（それは週報）。
- 箇条書き20個前後。1項目は1〜2文。社内の視点の「私たちは〜しました」で書く。
- 見出しでまとまりに分ける（例: 製品・営業・採用・制度のお知らせ）。リンクは素材にあるものだけ。
- 絵文字は社内チャット配信なら可。メールや紙は付けない。

## 社内FAQ

- 形式は `Q:` 1文／`A:` 1〜2文。
- 多くの従業員が迷っている・同じ質問が繰り返されているものを選ぶ。個人の事情の質問は載せない。
- 公式の通達・規程に根拠があるものだけ断定する。確定していないことは「現時点では未定。〇日に周知予定」と書く。経営判断が要る質問は、答えを作らず要確認に回す。
- 各 A の末尾に根拠（通達の件名・日付・規程名）を添える。

=== FILE: references/daily-report.md ===
# 日報

宛先は直属の上長。読む時間は1分以内。**実績は「何を・どこまで」まで書く。** 「対応した」「進めた」だけの行は書かない。

## 型

```
【日報】10月21日（水） 氏名

■ 本日の実績
- ＜案件・業務名＞: ＜やったこと＞→＜結果／どこまで進んだか＞（所要 約〇時間）
- …

■ 課題・相談
- ＜困っていること＞／＜判断してほしいこと＞。なければ「特になし」

■ 明日の予定
- ＜案件・業務名＞: ＜やること＞（〜まで）

■ 所感（任意）
＜気づき 1〜2行＞
```

## 営業日報で足す欄

訪問先（会社名・担当者の役職）／商談内容／相手の反応（確度は素材にあるときだけ）／次のアクション（誰が・いつまでに）／見込み金額（素材にあるときだけ）。

## 外しやすい点

- 時間の合計が所定の勤務時間と合わなくても、素材に無い作業を足して埋めない。
- 「課題・相談」は、上長の判断が要る形で書く（「〜で悩んでいます」で終えず、「A案かB案か、金曜までに判断をください」）。
- 所感は書き手が言っていないことを作らない。素材に無ければ欄ごと省く。

=== FILE: references/incident.md ===
# 障害報告・社内向けのお詫び

対象は**社内（上長・関係部署・経営）向け**の報告。お客様に出す文面は対象外。

## 型

```
【障害報告】＜件名: 何が／どのサービスで＞
報告日: 10月21日（水）　報告者: ＜氏名（部署）＞　状態: 復旧済み／対応中

1. 概要（1〜2文）
＜何が起き、いま何が済んでいるか＞

2. 発生と復旧
発生: 10月18日（日）14:05　検知: ＜時刻・手段＞　復旧: 10月18日（日）15:40　継続時間: 1時間35分

3. 影響範囲
＜影響を受けた利用者・件数・業務・金額。数字は素材にあるものだけ＞

4. 原因
- 確認できた事実: …
- 推定（未確認）: …

5. 対応の経過（時系列）
| 時刻 | 出来事・対応 | 担当 |

6. 再発防止策
| 対策 | 担当 | 期限 |

7. 未確認・残件
```

## 書き方

- 継続時間は発生と復旧の時刻から**計算して**書く（日をまたぐときは日数も）。
- 原因は「確認できた事実」と「推定」を分ける。調査中なら「調査中。〇日までに追報する」と期限を書く。
- 再発防止は「注意する」「気をつける」で終わらせない。仕組み・手順・監視の変更で、担当と期限をつける。素材に無ければ要確認。
- 謝罪は冒頭に1回、事実の前に置く。「ご迷惑をおかけし申し訳ありません」を段落ごとに繰り返さない。言い訳（「たまたま」「想定外」）と、他部署・個人への責任転嫁に読める書き方は避ける。
- 個人名は事実の記録に必要なときだけ。人ではなく手順・仕組みの問題として書く。
- 顧客に影響が出ている場合の社外向け文面や、法令上の報告義務（個人情報の漏えい等の報告など）の判断は、このスキルの範囲外。必要そうなら要確認に「社外・法令対応の要否を担当部署に確認」と書く。

=== FILE: references/minutes.md ===
# 議事録

**発言録にしない。** 読む人が知りたいのは、決まったこと・誰が何をいつまでにやるか。議論の経過は後ろに回す。

## 型

```
【議事録】＜会議名＞
日時: 10月20日（火）14:00〜15:00　場所: ＜会議室／URL＞
出席: ＜氏名（所属）＞、…　欠席: ＜氏名＞　記録: ＜氏名＞
目的: ＜1行＞

■ 決定事項
1. ＜決まったこと＞

■ ToDo
| 内容 | 担当 | 期限 |
|---|---|---|
| ＜やること＞ | ＜氏名＞ | 10月28日（水） |

■ 議論の要点
- ＜論点1＞: ＜出た意見と結論＞
- ＜論点2＞: …

■ 保留・次回
- ＜持ち越し事項＞／次回: ＜日時＞
```

## 書き方

- 決定事項と ToDo は、議論の要点より**上**に置く。
- ToDo の期限は日付（曜日つき）。「来週水曜まで」は会議の日付から数えて直す。会議の日付が素材に無ければ聞く。
- 担当者が話されていない ToDo は `【担当未定】`、期限が話されていなければ `【期限未定】` と書き、要確認にも載せる。誰かを当てはめない。
- 氏名は敬称略。社外の参加者は会社名を添える。
- 「〜と思う」「〜かもしれない」の発言を決定事項に格上げしない。決まっていなければ「保留」。
- 数字は発言のまま。聞き取りが不確かなものは `【要確認】`。

=== FILE: references/ringi.md ===
# 稟議書（起案・申請書）

会社により呼び方（稟議書・起案書・購入申請書・決裁願い）と様式が違う。**ユーザーの社内様式があればその項目に合わせる。** 無ければ下の型で書く。決裁欄・承認ルート・金額ごとの決裁権限は会社ごとに違うので、作らずに空欄（「決裁欄: 社内様式に従う」）にする。

## 型

```
【稟議書】＜件名: 何を（購入／契約／実施）するか＞
申請日: 10月21日（水）　申請者: ＜氏名（部署）＞　希望決裁日: ＜日付（曜日）＞

1. 申請の要旨（結論）
＜何を、いくらで、いつまでに行いたいか。承認をお願いしたい旨＞

2. 目的・背景
＜なぜ必要か。現状の課題＞

3. 内容
＜対象・数量・取引先・実施時期・実施者＞

4. 金額
| 項目 | 単価 | 数量 | 金額（税込） |
|---|---|---|---|
合計: 〇〇円（税込）／〇〇円（税抜）　予算科目: ＜要確認＞

5. 期待される効果
＜できれば数値。無ければ定性で。素材に無い数値は作らない＞

6. リスクと対策

7. 代替案と不採用の理由
＜比較した案を最低1つ。素材に無ければ要確認＞

8. 添付資料
＜見積書・比較表など＞
```

## 外しやすい点

- 金額は税込・税抜の両方を出す。小計と合計は計算して合わせる（単価×数量の検算をする）。消費税率は素材に無ければ10%と仮置きして要確認に載せる。
- 予算科目・予算の残・稟議番号・承認者名は素材に無ければ書かず、要確認に回す。
- 「要旨」は決裁者が1段落で判断できる長さにする。背景から書き始めない。
- 代替案が素材に無いとき、でっち上げた比較を載せない。「検討した案があれば追記」と要確認に書く。

=== FILE: references/weekly-3p.md ===
# 週報・3P（進捗・計画・課題）

3P = Progress（進捗）・Plans（計画）・Problems（課題）。上長や他部署が30〜60秒で読める長さ。チームが大きいほど粒度を粗くする（個人なら「修正した」、全社なら「新規10社と契約」）。

## 型（形式は変えない）

```
【チーム名】10/14（水）〜10/20（火）
進捗: ＜1〜3文。出荷・達成・数値＞
計画: ＜1〜3文。来週の最優先＞
課題: ＜1〜3文。止まっていること・必要な支援。なければ「特になし」＞
```

- チャット（Slack・Teams）向けは先頭に絵文字を1つ付けてよい。上長へのメールや稟議の添付には付けない。
- 期間は曜日つきで書く。省略するなら「先週分」ではなく日付で。
- 数値は素材にあるものだけ。無ければ書かずに要確認へ。文を飾って埋めない。

## 素材の範囲

- 進捗・課題: 1週間前から今日
- 計画: 今日から1週間後
- Slack は反応の多い投稿、ドキュメントは閲覧の多いもの、カレンダーは単発で重要な会議を優先して拾う

## 外しやすい点

- 「頑張った」「順調」は進捗ではない。何が完了したかを1つ以上入れる。素材が足りなければ書かずに聞く。
- 課題に「特になし」と書く前に、素材に遅れ・差し戻し・人員不足が出ていないか見直す。

=== FILE: scripts/jpdate.mjs ===
#!/usr/bin/env node
// 日付の曜日・相対日付・営業日後を日本語の書式で出す。依存なし・Node 18以上。通信もファイル書き込みもしない。
//
//   node jpdate.mjs 2026-10-21                      → 2026年10月21日（水）
//   node jpdate.mjs --today                         → 今日（日本時間）
//   node jpdate.mjs --from 2026-10-20 --next-week 水  → 来週の水曜日
//   node jpdate.mjs --from 2026-10-21 --week-after-next 月  → 再来週の月曜日
//   node jpdate.mjs --from 2026-10-21 --add-business-days 3 [--holidays 2026-11-03,2026-11-23 | --holidays-file syukujitsu.csv]
//   node jpdate.mjs --range 2026-10-14 2026-10-20   → 10/14（水）〜10/20（火）
//   node jpdate.mjs --duration "2026-10-18 14:05" "2026-10-18 15:40"  → 1時間35分
//
// 週は月曜始まり。「来週」は --from の日を含む週の次の週。
// 祝日: 内閣府の国民の祝日CSV（https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv）を保存して
// --holidays-file で渡すか、--holidays に日付をカンマ区切りで渡す。渡さなければ土日だけを休みにする（その旨を出力に書く）。
// 終了コード: 0 正常 / 2 引数エラー

import { readFileSync } from "node:fs";

const USAGE = `使い方: node jpdate.mjs <日付> | --today | --from <日付> (--next-week <曜> | --week-after-next <曜> | --add-business-days <N>) |
        --range <開始> <終了> | --duration "<日付 時:分>" "<日付 時:分>"
  日付は YYYY-MM-DD。曜は 月 火 水 木 金 土 日。
  --holidays <日付,日付,…> / --holidays-file <内閣府CSV>  営業日の計算で休みにする日`;

const DOW = ["日", "月", "火", "水", "木", "金", "土"];
const fail = (msg) => { console.error(`✗ ${msg}\n${USAGE}`); process.exit(2); };

// 日付はすべて UTC の 0 時として扱う（実行環境のタイムゾーンに依存させない）
function parse(s) {
  const m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(String(s ?? ""));
  if (!m) fail(`日付の形式が違う: ${s}（YYYY-MM-DD）`);
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  if (d.getUTCMonth() !== +m[2] - 1) fail(`存在しない日付: ${s}`);
  return d;
}
const iso = (d) => d.toISOString().slice(0, 10);
const full = (d) => `${d.getUTCFullYear()}年${d.getUTCMonth() + 1}月${d.getUTCDate()}日（${DOW[d.getUTCDay()]}）`;
const short = (d) => `${d.getUTCMonth() + 1}/${d.getUTCDate()}（${DOW[d.getUTCDay()]}）`;
const addDays = (d, n) => new Date(d.getTime() + n * 86400000);

function todayJst() {
  const p = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tokyo" }).format(new Date()); // YYYY-MM-DD
  return parse(p);
}

function weekdayIndex(name) {
  const i = DOW.indexOf(String(name ?? "").replace(/曜日?$/, ""));
  if (i < 0) fail(`曜日が読めない: ${name}（月 火 水 木 金 土 日）`);
  return i;
}

// その日を含む週（月曜始まり）の、指定した曜日の日付
function weekdayInWeek(d, dow, weeksAhead) {
  const sinceMon = (d.getUTCDay() + 6) % 7;
  const mon = addDays(d, -sinceMon + 7 * weeksAhead);
  return addDays(mon, (dow + 6) % 7);
}

function loadHolidays(args) {
  const set = new Set();
  const list = opt(args, "--holidays");
  if (list) for (const s of list.split(",")) set.add(iso(parse(s.trim())));
  const file = opt(args, "--holidays-file");
  if (file) {
    let buf;
    try { buf = readFileSync(file); } catch (e) { fail(`祝日ファイルを読めない: ${file}（${e.code ?? e.message}）`); }
    // 内閣府のCSVは Shift_JIS。UTF-8 で保存し直したものも読めるようにする
    let text;
    try { text = new TextDecoder("shift_jis").decode(buf); } catch { text = buf.toString("utf8"); }
    for (const line of text.split(/\r?\n/)) {
      const m = /^(\d{4})[\/-](\d{1,2})[\/-](\d{1,2})\s*,/.exec(line);
      if (m) set.add(iso(new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]))));
    }
    if (set.size === 0) fail(`祝日ファイルから日付を1件も読めなかった: ${file}`);
  }
  return set;
}

function opt(args, name) {
  const i = args.indexOf(name);
  if (i < 0) return null;
  if (i + 1 >= args.length) fail(`${name} に値が無い`);
  return args[i + 1];
}

const args = process.argv.slice(2);
if (args.length === 0 || args.includes("-h") || args.includes("--help")) {
  console.log(USAGE);
  process.exit(args.length === 0 ? 2 : 0);
}

if (args.includes("--today")) {
  console.log(full(todayJst()));
} else if (args[0] === "--range") {
  const a = parse(args[1]), b = parse(args[2]);
  if (b < a) fail("終了が開始より前");
  console.log(`${short(a)}〜${short(b)}`);
} else if (args[0] === "--duration") {
  const re = /^(\d{4})-(\d{1,2})-(\d{1,2})[ T](\d{1,2}):(\d{2})$/;
  const [m1, m2] = [re.exec(args[1] ?? ""), re.exec(args[2] ?? "")];
  if (!m1 || !m2) fail('時刻の形式が違う（"YYYY-MM-DD HH:MM"）');
  const t = (m) => Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
  const min = Math.round((t(m2) - t(m1)) / 60000);
  if (min < 0) fail("終了が開始より前");
  const d = Math.floor(min / 1440), h = Math.floor((min % 1440) / 60), mm = min % 60;
  console.log([d ? `${d}日` : "", h ? `${h}時間` : "", mm || (!d && !h) ? `${mm}分` : ""].join(""));
} else if (args.includes("--from")) {
  const from = parse(opt(args, "--from"));
  const nw = opt(args, "--next-week"), wan = opt(args, "--week-after-next"), n = opt(args, "--add-business-days");
  if (nw !== null) console.log(full(weekdayInWeek(from, weekdayIndex(nw), 1)));
  else if (wan !== null) console.log(full(weekdayInWeek(from, weekdayIndex(wan), 2)));
  else if (n !== null) {
    const count = Number(n);
    if (!Number.isInteger(count) || count < 0) fail(`営業日数は 0 以上の整数: ${n}`);
    const hol = loadHolidays(args);
    let d = from, left = count;
    while (left > 0) {
      d = addDays(d, 1);
      if (d.getUTCDay() !== 0 && d.getUTCDay() !== 6 && !hol.has(iso(d))) left--;
    }
    console.log(full(d) + (hol.size ? "" : "  ※土日のみ除外。祝日は考慮していない"));
  } else fail("--from のあとに --next-week / --week-after-next / --add-business-days のどれかが要る");
} else {
  console.log(full(parse(args[0])));
}

=== FILE: LICENSE ===

                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

   1. Definitions.

      "License" shall mean the terms and conditions for use, reproduction,
      and distribution as defined by Sections 1 through 9 of this document.

      "Licensor" shall mean the copyright owner or entity authorized by
      the copyright owner that is granting the License.

      "Legal Entity" shall mean the union of the acting entity and all
      other entities that control, are controlled by, or are under common
      control with that entity. For the purposes of this definition,
      "control" means (i) the power, direct or indirect, to cause the
      direction or management of such entity, whether by contract or
      otherwise, or (ii) ownership of fifty percent (50%) or more of the
      outstanding shares, or (iii) beneficial ownership of such entity.

      "You" (or "Your") shall mean an individual or Legal Entity
      exercising permissions granted by this License.

      "Source" form shall mean the preferred form for making modifications,
      including but not limited to software source code, documentation
      source, and configuration files.

      "Object" form shall mean any form resulting from mechanical
      transformation or translation of a Source form, including but
      not limited to compiled object code, generated documentation,
      and conversions to other media types.

      "Work" shall mean the work of authorship, whether in Source or
      Object form, made available under the License, as indicated by a
      copyright notice that is included in or attached to the work
      (an example is provided in the Appendix below).

      "Derivative Works" shall mean any work, whether in Source or Object
      form, that is based on (or derived from) the Work and for which the
      editorial revisions, annotations, elaborations, or other modifications
      represent, as a whole, an original work of authorship. For the purposes
      of this License, Derivative Works shall not include works that remain
      separable from, or merely link (or bind by name) to the interfaces of,
      the Work and Derivative Works thereof.

      "Contribution" shall mean any work of authorship, including
      the original version of the Work and any modifications or additions
      to that Work or Derivative Works thereof, that is intentionally
      submitted to Licensor for inclusion in the Work by the copyright owner
      or by an individual or Legal Entity authorized to submit on behalf of
      the copyright owner. For the purposes of this definition, "submitted"
      means any form of electronic, verbal, or written communication sent
      to the Licensor or its representatives, including but not limited to
      communication on electronic mailing lists, source code control systems,
      and issue tracking systems that are managed by, or on behalf of, the
      Licensor for the purpose of discussing and improving the Work, but
      excluding communication that is conspicuously marked or otherwise
      designated in writing by the copyright owner as "Not a Contribution."

      "Contributor" shall mean Licensor and any individual or Legal Entity
      on behalf of whom a Contribution has been received by Licensor and
      subsequently incorporated within the Work.

   2. Grant of Copyright License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      copyright license to reproduce, prepare Derivative Works of,
      publicly display, publicly perform, sublicense, and distribute the
      Work and such Derivative Works in Source or Object form.

   3. Grant of Patent License. Subject to the terms and conditions of
      this License, each Contributor hereby grants to You a perpetual,
      worldwide, non-exclusive, no-charge, royalty-free, irrevocable
      (except as stated in this section) patent license to make, have made,
      use, offer to sell, sell, import, and otherwise transfer the Work,
      where such license applies only to those patent claims licensable
      by such Contributor that are necessarily infringed by their
      Contribution(s) alone or by combination of their Contribution(s)
      with the Work to which such Contribution(s) was submitted. If You
      institute patent litigation against any entity (including a
      cross-claim or counterclaim in a lawsuit) alleging that the Work
      or a Contribution incorporated within the Work constitutes direct
      or contributory patent infringement, then any patent licenses
      granted to You under this License for that Work shall terminate
      as of the date such litigation is filed.

   4. Redistribution. You may reproduce and distribute copies of the
      Work or Derivative Works thereof in any medium, with or without
      modifications, and in Source or Object form, provided that You
      meet the following conditions:

      (a) You must give any other recipients of the Work or
          Derivative Works a copy of this License; and

      (b) You must cause any modified files to carry prominent notices
          stating that You changed the files; and

      (c) You must retain, in the Source form of any Derivative Works
          that You distribute, all copyright, patent, trademark, and
          attribution notices from the Source form of the Work,
          excluding those notices that do not pertain to any part of
          the Derivative Works; and

      (d) If the Work includes a "NOTICE" text file as part of its
          distribution, then any Derivative Works that You distribute must
          include a readable copy of the attribution notices contained
          within such NOTICE file, excluding those notices that do not
          pertain to any part of the Derivative Works, in at least one
          of the following places: within a NOTICE text file distributed
          as part of the Derivative Works; within the Source form or
          documentation, if provided along with the Derivative Works; or,
          within a display generated by the Derivative Works, if and
          wherever such third-party notices normally appear. The contents
          of the NOTICE file are for informational purposes only and
          do not modify the License. You may add Your own attribution
          notices within Derivative Works that You distribute, alongside
          or as an addendum to the NOTICE text from the Work, provided
          that such additional attribution notices cannot be construed
          as modifying the License.

      You may add Your own copyright statement to Your modifications and
      may provide additional or different license terms and conditions
      for use, reproduction, or distribution of Your modifications, or
      for any such Derivative Works as a whole, provided Your use,
      reproduction, and distribution of the Work otherwise complies with
      the conditions stated in this License.

   5. Submission of Contributions. Unless You explicitly state otherwise,
      any Contribution intentionally submitted for inclusion in the Work
      by You to the Licensor shall be under the terms and conditions of
      this License, without any additional terms or conditions.
      Notwithstanding the above, nothing herein shall supersede or modify
      the terms of any separate license agreement you may have executed
      with Licensor regarding such Contributions.

   6. Trademarks. This License does not grant permission to use the trade
      names, trademarks, service marks, or product names of the Licensor,
      except as required for reasonable and customary use in describing the
      origin of the Work and reproducing the content of the NOTICE file.

   7. Disclaimer of Warranty. Unless required by applicable law or
      agreed to in writing, Licensor provides the Work (and each
      Contributor provides its Contributions) on an "AS IS" BASIS,
      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
      implied, including, without limitation, any warranties or conditions
      of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A
      PARTICULAR PURPOSE. You are solely responsible for determining the
      appropriateness of using or redistributing the Work and assume any
      risks associated with Your exercise of permissions under this License.

   8. Limitation of Liability. In no event and under no legal theory,
      whether in tort (including negligence), contract, or otherwise,
      unless required by applicable law (such as deliberate and grossly
      negligent acts) or agreed to in writing, shall any Contributor be
      liable to You for damages, including any direct, indirect, special,
      incidental, or consequential damages of any character arising as a
      result of this License or out of the use or inability to use the
      Work (including but not limited to damages for loss of goodwill,
      work stoppage, computer failure or malfunction, or any and all
      other commercial damages or losses), even if such Contributor
      has been advised of the possibility of such damages.

   9. Accepting Warranty or Additional Liability. While redistributing
      the Work or Derivative Works thereof, You may choose to offer,
      and charge a fee for, acceptance of support, warranty, indemnity,
      or other liability obligations and/or rights consistent with this
      License. However, in accepting such obligations, You may act only
      on Your own behalf and on Your sole responsibility, not on behalf
      of any other Contributor, and only if You agree to indemnify,
      defend, and hold each Contributor harmless for any liability
      incurred by, or claims asserted against, such Contributor by reason
      of your accepting any such warranty or additional liability.

   END OF TERMS AND CONDITIONS

   APPENDIX: How to apply the Apache License to your work.

      To apply the Apache License to your work, attach the following
      boilerplate notice, with the fields enclosed by brackets "[]"
      replaced with your own identifying information. (Don't include
      the brackets!)  The text should be enclosed in the appropriate
      comment syntax for the file format. We also recommend that a
      file or class name and description of purpose be included on the
      same "printed page" as the copyright notice for easier
      identification within third-party archives.

   Copyright 2026 Anthropic, PBC.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
