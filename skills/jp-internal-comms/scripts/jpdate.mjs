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
