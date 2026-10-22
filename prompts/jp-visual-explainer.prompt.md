<!-- jp-visual-explainer v1.0.0 貼り付け版。Agent Skills を読み込めない環境（チャット・API）で、この1ファイルをプロジェクトの知識ファイルに入れるか、会話の最初・システムプロンプトに貼って使う -->
# スキル: jp-visual-explainer（v1.0.0）

以下はひとつのスキルのファイル一式です。最初の SKILL.md の指示に従ってください。
本文が `references/…` などのファイルを読むよう指示したら、下の同じパスの `=== FILE: … ===` の節を読んでください。
スクリプトを実行できない環境では、SKILL.md に書かれた代替の手順で進めてください。

=== FILE: SKILL.md ===
---
name: jp-visual-explainer
description: >-
  仕組み・業務フロー・設計・コードの変更・計画・数字を、日本語の図解ページ（1ファイルの HTML。手描きの SVG 図、比較、KPI、スライド）にする。和文の組版（lang="ja"、和文フォント、行長30〜40字、禁則、見出しの字間）を守る。「この仕組みを図解して」「承認フローを1枚のページで見せて」「設計を図にしてHTMLで」「この数字をダッシュボード風にまとめて」「日本語のスライドを作って」と頼まれたとき、またはターミナルに収まらない表・図を見せたいときに使う。Keywords: visual explainer, diagram, architecture overview, HTML, SVG, slides, 図解, 構成図, フロー図。PowerPoint・Keynote のファイル作成、写真・イラストの生成、印刷用の DTP は対象外。
license: MIT
compatibility: 生成した HTML を見るのにブラウザが要る。フォントは Google Fonts から読む（オフラインでは OS の和文フォントで表示）
metadata:
  version: "1.0.0"
  author: frametech
---

# 日本語の図解ページ

目的: 分かっていることを、読む人が10秒で分かる日本語の図解ページにする。
入力: 説明したい対象（仕組み・フロー・コードの差分・計画・数字）と、分かれば読む人と保存先。
出力: 1つの完結した HTML ファイル（CSS・JS・SVG を中に含む。外部はフォントとライブラリの CDN だけ）と、内容を1行で言う返事。

元: https://github.com/nicobailon/visual-explainer@0cc6f15（MIT、`LICENSE`）を改変。日本語の組版（references/japanese-typography.md）を足し、テンプレートを日本語向けにし、動画・PPTX・MCP・プランの各ツールを外した。

```
文章  ──►  図  ──►  触れるページ（既定）  ──►  動く図解（頼まれたら）
```

## 渡し方

- 保存先はユーザーの指定どおり。指定が無ければ作業フォルダの `diagrams/<内容が分かる名前>.html`。1ファイルで完結させる。
- ファイルを書けない環境（チャットだけ）では、HTML 全体を1つのコードブロックで出し、「`.html` で保存してブラウザで開く」と添える。
- ターミナルの表が4行以上か3列以上になるなら HTML にして、返事は要約1行にする。
- ページの本文が日本語なら、**最初に [references/japanese-typography.md](references/japanese-typography.md) を読む**。style-guide.md より優先する。

## 書かずに見せる

1. **図1つに主張1つ。** 図は `<figure>`、`<figcaption>` は「図1」で始めて主張を1文で書く。
2. **図が先、言葉はラベル。** たいていの節は図で始める。理由・定義・トレードオフは文章で始めてよいが、1〜2文に抑える。図を説明する文は、図の中のラベルにする。
3. **最初の画面＝答え。** 主な考えを図と1文で。飾りのヒーローは置かない。
4. **名前ではなく仕組みを描く。** 「キャッシュ」と書いた箱より、キャッシュを通るリクエストの道筋。矢印には動詞を付ける（「書き込む」「無効化」「30秒ごとに取得」）。
5. **違いを描く。** 選択肢の比較は、それぞれが足す・消す箱や矢印を見せる。
6. **状態は形でも表す。** 形・位置・模様に色を重ねる。色だけで区別しない。
7. **数字には必ず絵を添える。** ワッフル・棒・スパークライン。文中の数字は読み飛ばされる。
8. **場合分けは小さな図の並び。** 障害のパターン・選択肢・環境ごとに、同じ小さな図を並べる。

| ページ | 典型の形 |
|---|---|
| 仕組みの説明 | 問い → 直感の図 → 仕組み（ステッパー）→ 例外 → 覚えておくこと |
| 業務フロー・承認フロー | 全体の流れ図（スイムレーン）→ 分岐と差し戻し → 期限・担当 → 例外 |
| レビュー・監査 | 結論 → 根拠の図 → リスク → 次の手 |
| 比較 | 違いを横に並べて描く → トレードオフ → 推奨 |
| 長い読み物 | 文章の列に図を添える。文章が多くてよい |
| 図1枚 | 大きな図1つ、見出し、キャプション。節は無し |

| 内容 | 図 |
|---|---|
| 構成・データの流れ・パイプライン・状態・シーケンス・スキーマ・前後比較 | 手描きのインライン SVG → `references/diagrams.md` |
| カード・年表・ファイルの地図・並べて比較 | CSS grid / flex |
| シナリオ・障害のパターン・選択肢 | 小さな図の並び → `references/diagrams.md` |
| マトリクス・監査・多数の行 | `<table>` と状態のチップ |
| 割合・指標・推移 | SVG のワッフル・棒・スパークライン。系列が多く操作が要るときだけ Chart.js |
| 時間で変わる手順 | ステッパー・シーンプレーヤー → `references/diagrams.md` |
| スライド | `references/slides.md` ＋ `templates/slide-deck.html`（頼まれたときだけ） |

図はすべて手で描く（SVG）。Mermaid はユーザーが頼んだか Mermaid のソースを渡されたときだけ。`templates/page.html` が見本の実装。部品（トークン・CSS・スクリプト・コンポーネント）を写し、構成は内容に合わせて変える。

## 見た目

HTML を書く前に `references/style-guide.md` を必ず読む（日本語なら japanese-typography.md も）。優先順位: ユーザーの言葉 → プロジェクトのデザインシステム → japanese-typography.md → style-guide.md。

- 静かな地に、合図は1つ。アクセント色は今見るべきものだけに。
- 図がインターフェース。本文の語と図の要素は一緒に光る（diagrams.md の Linked highlighting）。
- 動きは変化と流れだけ。視差効果・スクロールの乗っ取り・飾りのループは使わない。`prefers-reduced-motion` では最終状態を出す。
- スケール外の大きさ・余白・角丸・色を使わない。色は `:root` のトークンに置き、`prefers-color-scheme` ではトークンだけを上書きする。
- 使わない: 和文フォントの無いページ、欧文フォントだけのフォント指定、紫・マゼンタのアクセント、ネオン、すりガラス、グラデーションの文字・背景、クリップアート、絵文字のマーカー、全部中央揃え。
- 読みやすさ: 本文 16px 以上、ラベル 12px 以上。コントラストは文字 4.5:1、線 3:1 以上。1画面に焦点は1つ。
- テーマの切り替え・名前付きのパレット（Dracula、Nord…）を頼まれたら `references/themes.md`。

## はまりどころ

- grid / flex の子に `min-width:0`、1列の grid に `grid-template-columns:minmax(0,1fr)`、パスに `overflow-wrap:anywhere`。幅の広い表・コード・SVG はスクロールする枠に入れる。
- マーカーが要る `<li>` に `display:flex` を付けない。
- `history.replaceState` は `try/catch` で包む（`file://` で例外になる）。
- 節が4つ以上のときだけ目次（スクロールに追従）を付ける。
- 和文の SVG ラベルは1行9〜10字まで。箱の幅は字数から決める（japanese-typography.md §4）。

## 動く図解とスライド

- 「動く図解」を頼まれたら、HTML のシーンプレーヤー（再生・一時停止・シークバー・字幕を1ファイルで）を作る。`references/diagrams.md` の Stepper and scene player。1場面に主張1つ、文が変わるたびに図も変わる。
- スライドは頼まれたときだけ作る。`references/slides.md` を読み、`templates/slide-deck.html` のエンジンをそのまま写す。動画ファイル（MP4）と PPTX の書き出しはこのスキルの対象外。

## 渡す前の確認

```
□ 指定の場所に完結した HTML が1つ。開いてもコンソールにエラーが無い
□ 日本語のページ: lang="ja"、和文フォントの読み込みとフォントの並び、本文の行長30〜40字、見出しの字間0、斜体なし
□ 最初の画面: 主な考えが図と1文で分かる
□ 図の数が文章の段落より多い。数字には絵がある。場合分けは小さな図の並び
□ 各図: <figure> ＋「図N」で始まる主張のキャプション。描画に role="img" と aria-label
□ SVG の和文ラベルが箱からはみ出していない
□ 幅 1280px と 390px で横にはみ出さない。明暗どちらの配色でも読める
□ 見出しは結論を書いている。段落は短い
```

=== FILE: references/diagrams.md ===
# Hand-drawn SVG figures

Inline SVG is the default figure. You control every position, it uses page tokens and fonts, and it can animate. `templates/page.html` has the CSS and JS for every pattern here. Copy those blocks as they are; this file gives the markup contracts and the rules.

## Plan on a grid

```
x:  40        280        520        760      columns 240 apart
    ┌──────┐  GET /u   ┌──────┐  miss   ┌──────┐
y:90│Client│──────────►│ API  │────────►│  DB  │
    └──────┘           └──┬───┘         └──────┘
                     hit  │ reads
y:210                  ┌──▼───┐
                       │Cache │
                       └──────┘
```

- Sketch in ASCII first, then turn columns and rows into coordinates.
- Make the viewBox width close to the display width (720–1000) so `14` units ≈ 14px. On narrow screens the `.frame` scrolls and the SVG keeps a `min-width`. Text never shrinks below the type minimums.
- At least 40 units between boxes. Orthogonal edges (`M x y H x V y`). Labels 9 units above their line, with the `.ve-el` halo.
- SVG text does not wrap: keep lines short (about 18 characters), `<tspan x=".." dy="1.2em">` for a second line.
- Draw edges first and nodes after, so nodes sit on top.
- A boundary (process, network, trust zone) is a dashed rect with a mono label in its top-left corner.
- Over about 12 nodes, draw a 5–8 node overview and put the detail in cards or a second figure.
- Sequence: one column per actor with a thin lifeline, one row per message, time runs down, each arrow labeled with its call. Schema: one box per table with its key fields in mono, crow's-foot ends for many.

## Kit

```
page   <svg width=0 height=0> defs once: #ve-ah marker (fill="context-stroke"), #ve-node gradient
figure <figure> → .frame (dot-grid stage) → svg.ve-svg[role=img][aria-label] → <figcaption>Fig. N + claim
node   <g class="ve-n [is-key]"> <rect class="sh"/> [<path class="gl"/>] <text/> [<text class="sub"/>] </g>
edge   <path class="ve-e [is-hot|is-async]"/>  + <text class="ve-el [l|r]">verb or value</text>
```

- **Shape says what a thing is.** Rect for a service. Cylinder for a datastore (`path.sh` body + `ellipse.sh.lid`, as Postgres in the template). Rect with 3 short dividers for a queue. Dashed rect for something optional or down.
- **Glyph** (`.gl`): a 16-unit line drawing in the node's top-left corner, only when the kind is not clear from the name. Stroke `--text-dim`, never filled, never emoji.
- **Edge language:** solid = sync call · dashed = async or optional · thick glowing accent = the path this figure is about · red ✕ = blocked.

## Flow dots

Moving dots show direction and volume at a glance. Use them on the main figure when traffic or data moves. The rate must mean something: the ratio of spawn intervals is the real split.

```html
<path data-flow="hit"  data-every="420"  d="M95 105H375V80H695V105H375"/>   <!-- invisible route -->
<path data-flow="miss" data-every="7000" d="M95 105H355V270H395V130H695"/>  <!-- 420:7000 ≈ 94:6 -->
<g class="ve-dots" aria-hidden="true"></g>                                   <!-- after edges, before nodes -->
```

Routes pass through node centers. The dots move under the opaque nodes, so they enter one box and leave the next. One moving layer per page. The script runs dots only while the figure is on screen and the stepper shows the full picture, and never under reduced motion.

## Linked highlighting

Elements that share a `data-ref` light up together: a prose term, a node, an edge, a card, a button. Hovering any of them, or focusing a prose term or button, lights all of them while the other shapes dim. Prose terms get `tabindex="0"`. One element can carry several refs (`data-ref="hit miss"`). Link 2–4 key terms per figure, not every noun.

## Stepper and scene player

The most useful interaction for teaching: each step brings its parts forward with a one-line caption. Add Play and a scrub bar and it becomes a scene player, a small explainer video in one file.

```
<figure class="ve-steps">  parts: data-s="N" (appears at step N) · paths with pathLength="1" draw in
  .ve-player → ol.ve-cap > li[data-n="1/5"] · button[data-go=-1] · button[data-play] · input[type=range] · button[data-go=1]
```

Open on the complete picture, because the first viewport must show the answer. One claim per scene; something visibly changes at every step. Never autoplay. Play stays available under reduced motion, because the reader starts it.

## Before / after

One drawing, same coordinates, a toggle (`button[aria-pressed]` flips `figure[data-view]`; `.only-before` / `.only-after` groups). The reader sees exactly what moves. Added = `--ok` stroke; removed = `--risk` dashed. For a static version, two panels side by side at the same scale.

## Live figure

Controls that recompute the picture, so the reader feels a setting instead of reading about it: a TTL slider moves the hit rate, the flow-dot split, the load bar, and the headline. A policy toggle is a why-demo: on the same data the bad rule gives a nicer, wrong number.

- One to three controls (`input[type=range]`, `button[aria-pressed]`). Each changes something the reader cares about.
- One pure `model(settings)` feeds the figure, the numbers, and the sentence. Nothing else holds state.
- Default to the real current value and mark it on the scale, so the first screen is still the answer. Print and no-JS show that state with no controls: insert them from JS and hide them in print. Reduced motion keeps the controls live and drops only the transitions.
- Show the formula in the caption or a `<details>`. Label a simplified model "illustrative".
- Model the concept, never copy production logic into the page; a copy drifts.

## Small multiples

For a set of cases (failure modes, options, environments), draw the same small diagram once per case instead of writing a table. Same coordinates in each, so the eye sees only the difference. The part that changes takes the case's status color (`.case[data-st]` sets `--st`; mark the changed parts `.is-st`). Each card: status chip, short title, mini diagram, no sentence. Mini labels 13 units or more, cards at least 14.5rem wide.

## Small charts

Every number gets a picture beside it. Each chart has `role="img"` and an `aria-label` with the values.

- **Waffle** (rates, "N of 100"): 10×10 cells, two `<pattern>` fills over three rects.
- **Bars** (2–5 values): value label just past each bar's end. The bar that matters is accent; the rest `--border-bright`. Bars grow in when their block enters.
- **Sparkline** (trend): `0 0 100 24`, one `polyline`, `vector-effect: non-scaling-stroke`.

## Entrance motion

Each top-level block rises 1rem and fades in once. `data-count` numbers count up and bars grow. JS adds `.js-motion` only when motion is allowed, so no-JS, print, and reduced motion show the final state. Nothing beyond this: no parallax, no scroll-jacking, no looping effects other than flow dots.

## 3D with three.js

Use 3D only when depth carries data: embeddings and point clouds, physical or spatial layouts (racks, regions, floor plans), stacks where height is a real quantity, meshes and geometry. A graph of boxes and arrows is never 3D.

```html
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.186/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.186/examples/jsm/"}}</script>
```

- Canvas in a `.frame` with a fixed aspect ratio, `role="img"`, an `aria-label`, a `Fig. N` caption, and a one-line text fallback with the key numbers.
- Colors from the page tokens via `getComputedStyle`. Labels with `CSS2DRenderer`, so they use the page font. One directional light plus ambient. No bloom, fog, or decorative particles.
- `OrbitControls` with damping and zoom limits, plus a "Reset view" button. Open on an angle that already shows the answer. Auto-rotate only until the first interaction, never under reduced motion.
- `setPixelRatio(Math.min(devicePixelRatio, 2))`, a `ResizeObserver`, and render only while visible.

## Page structure for 4+ sections

Sticky `<nav>` table of contents on the left, content on the right; below 1000px it becomes a sticky top bar. In the top bar, only the link list scrolls sideways: hide its scrollbar (`scrollbar-width:none`, `::-webkit-scrollbar{display:none}`), fade its right edge with `mask-image`, and keep buttons outside it. Mark the active section with an `IntersectionObserver` (`rootMargin:'-10% 0px -80% 0px'`). Wrap `history.replaceState` in `try/catch`, because it throws on `file://` pages.

## Other shapes

- **File map:** nested `<ul>` in mono. Each path gets a status chip (added, modified, deleted) and a `+12 −3` count.
- **Timeline:** a CSS grid with one rail line and dated nodes. The newest item gets the accent.

=== FILE: references/japanese-typography.md ===
# 日本語のページの組版

ページの本文・見出し・図のラベルが日本語なら、style-guide.md より**こちらを優先**する。欧文の規則（`ch` の行長、負の字間、斜体、大文字化）は和文にそのまま当てると崩れる。

## 1. 必ず入れる指定

```html
<html lang="ja">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">
```

```css
:root {
  --font-body: 'Geist', 'Noto Sans JP', 'Hiragino Sans', 'Yu Gothic UI', sans-serif;  /* 欧文 → 和文 → OS の和文 */
  --font-mono: 'Geist Mono', 'Noto Sans JP', ui-monospace, monospace;               /* 等幅にも和文の代替を */
}
:lang(ja) body { line-height: 1.8; line-break: strict; overflow-wrap: anywhere; }
:lang(ja) :is(h1, h2, h3) { letter-spacing: 0; line-height: 1.35; word-break: auto-phrase; font-feature-settings: "palt"; }
:lang(ja) :is(p, figcaption, li) { max-width: 36em; }
:lang(ja) :is(em, i) { font-style: normal; font-weight: 600; }
```

`templates/page.html` と `templates/slide-deck.html` には入っている。テンプレートを使わずに書くときも、この5つ（`lang="ja"`、和文フォントの読み込み、フォントの並び、行送りと禁則、見出しの字間 0）は省かない。

## 2. 欧文の規則との違い

| 項目 | 欧文（style-guide.md） | 和文 |
|---|---|---|
| 行長 | 本文 65ch | 本文 **30〜40字**（`max-width: 36em` 前後）。全角1字は約 2ch なので、`ch` で指定すると半分の字数で折り返す。和文の幅は `em` で書く |
| 行送り | 1.5〜1.6 | 本文 **1.7〜1.9**、見出し 1.3〜1.4 |
| 字間 | 見出しを −0.01〜−0.04em 詰める | **詰めない（0）**。詰めたいときは見出しだけ `font-feature-settings: "palt"`（約物の空きを詰める）。本文に `palt` は使わない |
| 強調 | 斜体・太字 | 和文フォントに斜体は無く、ブラウザが字形を傾けて汚くなる。**太字か色**で強調する |
| 大文字化 | ラベルを uppercase ＋ 字間 | 和文には効かない。ラベルの `text-transform` を外し、字間は .04em まで |
| 改行 | `text-wrap: balance` | 見出しは `word-break: auto-phrase`（文節で折り返す。Chrome 119 以降。他は無視されるので書いてよい）＋ `text-wrap: balance`。行頭に「、。）」が来ないよう `line-break: strict` |
| 図の番号 | `Fig. N` | **「図1」「図2」**。表は「表1」 |
| 引用符・ダッシュ | “ ” — – | 「」『』。範囲は「〜」、補足は（）。全角ダッシュ「——」で補足を挟まない |

## 3. 文章（ASD-STE100 の代わり）

- 一文一義。一文は**60字以内**を目安、長くても80字
- 文体は「です・ます」か「である」のどちらかに統一する。見出しと図のラベルは体言止めでよい
- 見出しは結論を書く（「キャッシュに当たれば DB を読まない」）。話題名だけにしない（「キャッシュについて」）
- 英字の固有名詞・コマンドは半角のまま。和文と英数字の間にスペースを入れるかどうかはページ内で統一する
- 数字は半角。4桁以上は「1,234」と区切る。大きな金額・人数は「1.2億円」「3万人」と万・億を使ってよい。単位は数字の直後（「30秒」「128MB」）
- 日付は「2026年10月10日（金）」か「2026-10-10」のどちらかに統一。和暦は頼まれたときだけ
- 金額は「円」。税込・税抜を書く

## 4. 図（インライン SVG）のラベル

- SVG の `<text>` は折り返さない。和文1字は欧文の約2倍の幅なので、**1行は全角9〜10字まで**（diagrams.md の「約18字」は半角の目安）。それ以上は `<tspan x=".." dy="1.2em">` で2行にするか、言葉を短くする
- 箱の幅は字数から決める: 幅 ≒ 字数 × フォントサイズ ＋ 左右の余白 24。14px のラベルが8字なら 112＋24＝136 以上
- `font-family` は CSS 変数を継承させる（`svg text { font-family: var(--font-body); }`）。SVG の中で欧文フォントだけを指定しない
- 矢印のラベルは動詞か値: 「書き込む」「無効化」「30秒ごとに取得」「失敗時に再送」
- 縦書きは使わない（図の読み順が崩れる）

## 5. 出典（確認日 2026-10-10。90日を過ぎたら読み直す）

- W3C「日本語組版処理の要件（JLREQ）」: https://www.w3.org/TR/jlreq/
- MDN `word-break`（`auto-phrase`）: https://developer.mozilla.org/ja/docs/Web/CSS/word-break
- MDN `line-break`: https://developer.mozilla.org/ja/docs/Web/CSS/line-break
- Google Fonts「Noto Sans JP」: https://fonts.google.com/noto/specimen/Noto+Sans+JP

=== FILE: references/slides.md ===
# Slides

Slides are a different medium, not a long page cut into pieces. Make them only when asked. Copy the engine in `templates/slide-deck.html` as it is: chrome, `SlideEngine`, `autoFit()`, and the delivery check. Restyle everything else.

## Plan before HTML

```
source ──► inventory every item ──► map item → slide ──► pick composition ──► write
           (sections, rows,         (nothing unmapped;    (vary: centered, left,
            decisions, details)      add slides, never     right, split, bleed)
                                     drop content)
```

A source with 7 sections usually needs 18–25 slides, not 10. Test: a reader who has never seen the source can rebuild every major point from the deck.

## Budget per slide (one `100dvh`, no scrolling)

| Type | Holds at most |
|---|---|
| Title / Full-bleed | heading + subtitle |
| Divider | number + heading + subhead |
| Content | heading + 5 bullets of ≤2 lines, or heading + one figure |
| Split | two panels, each within its own type's limits |
| Diagram | heading + one SVG figure (≤ 10 boxes, 18px+ labels, 2px+ edges) |
| Dashboard | heading + 6 KPIs; hero value ≤ 6 characters |
| Table | heading + 8 rows; continue on the next slide |
| Code | heading + 10 lines |
| Quote | ≤ 25 words + attribution |

- One focal point per slide. The heading states the slide's takeaway. Body text 18px or larger, in the sans; keep the display face for headings. Contrast higher than on pages.
- Prefer a figure to bullets. A slide with only bullets should be the exception.
- Figures use the `diagrams.md` kit at slide scale: node text 24, edge labels 18, strokes 2.5 (hot 3.5), arrowheads 16 in `userSpaceOnUse`, `max-height: 56dvh`. Below 768px wide, give the SVG `min-width: 720px` inside a scroll wrapper so labels never shrink.
- Decks default to the Editorial register (`style-guide.md`). A deck about metrics or architecture may use Instrument or Blueprint.
- Never put three centered slides in a row.
- Keep type in `clamp(px, vw, px)`, not `rem`. Reduce padding and hide decoration at `max-height: 700/600/500px`.

## Engine contract (already in the template)

Progress bar · dot rail that expands to titles on hover or focus · `4 / 12 · 33%` counter · arrow, Space, Home, End, `O` outline, `?` help, Esc · `#slide-N` deep links (a hash beats resume) · `localStorage` resume · touch swipe · no slide navigation while focus is in `.diagram-shell`, `.table-scroll`, `.code-scroll`, or a form field. Entrance states hide behind `.js`, so the deck still reads without JS.

## Delivery check

`overflow:hidden` clips silently, so a clipped slide does not prove that the content fits. Before you ship:

1. Turn on `prefers-reduced-motion: reduce`. In Chrome DevTools: Rendering → Emulate CSS media feature.
2. Load the deck at the target size and at a short landscape size (about 1280×600).
3. The template marks each failing slide with a red (overflow) or amber (autoFit used) outline and logs `Slide delivery check failed`.
4. Split or cut the content until the console reports `passed`.

=== FILE: references/style-guide.md ===
# Style guide

One system, four registers, and a topic motif on top. Choose the register from the content, then let the subject tint it (Topic motif below). The scale, components, and polish pass apply to all of them. `templates/page.html` is the Instrument register built to this guide.

## Registers

| Register | Use for | Display / body / mono | Signature |
|---|---|---|---|
| **Instrument** | diff and plan reviews, audits, metrics, status | Geist 600 / Geist / Geist Mono | A KPI strip near the top when there are metrics. Tabular numbers everywhere. Cells split by hairlines, not floating cards. Status as shape + word. |
| **Blueprint** | architecture, data flow, systems, visual plans | IBM Plex Sans 600 / IBM Plex Sans / IBM Plex Mono | 24px grid on the background. Boundaries as dashed frames with a mono tag. Numbered callouts ① ② on the drawing. |
| **Paper** | concepts, how-it-works, fact-checks, long reading | Newsreader 500 / Atkinson Hyperlegible Next / Atkinson Hyperlegible Mono | Narrow text column, wide figures. Margin notes at ≥ 1200px. `Fig. N` labels. |
| **Editorial** | recaps, narratives, decks, showcases | Instrument Serif / Instrument Sans / JetBrains Mono | Display type at full scale. Asymmetric grid with large empty areas. One number or phrase per screen carries the page. |

The project's own design system overrides the register. If the user names a palette, use `themes.md`.

Token order: `--bg --surface --border --border-bright --text --text-dim --accent --ok --warn --risk --info`. The first scheme listed is the default; put the other one in `prefers-color-scheme`. Every text token reaches 4.5:1 on `--bg` and on `--surface`. `--border-bright` reaches 3:1, so it carries meaningful outlines (diagram nodes, controls). `--border` is for decorative frames and rules only.

| Register · scheme | Values |
|---|---|
| Instrument · dark | `#0b0d0c #121614 #1f2522 #5e6662 #e6ebe8 #919d97 #f2a93b #6fcf97 #e8c547 #ef6f5c #6cb6e0` |
| Instrument · light | `#f4f5f3 #ffffff #dfe3e0 #888e8b #121614 #545e59 #955700 #1c7443 #7a5e00 #b0341e #1a6890` |
| Blueprint · dark | `#0d1520 #132031 #22324a #596b87 #e3ecf5 #92a6bb #ffb547 #6fd3a0 #e8d36a #ff7b6b #7cc0f0` |
| Blueprint · light | `#f2f6fa #ffffff #d6e0ea #818f9e #0f1a26 #4d6074 #a34700 #1c7443 #776300 #b0341e #145f99` |
| Paper · light | `#f7f7f4 #ffffff #e3e3dc #8e8e8a #17191c #575c63 #2c4cd0 #1d7443 #836000 #b3301d #1b6a94` |
| Paper · dark | `#111316 #181b1f #262a30 #62676c #e8e8e3 #9ba1a9 #93a6ff #6cc492 #e3b94d #f0806b #6fb8dc` |
| Editorial · light | `#fbfbf9 #f1f0ec #e2e0da #8c8a85 #111111 #5a5853 #cc3418 #1d7443 #836000 #a01d48 #1b6a94` |
| Editorial · dark | `#0f0f0f #1a1a19 #2b2a28 #696763 #f2f0eb #a4a19b #ff6e50 #6cc492 #e3b94d #f57fa2 #7cb8e8` |

Effect tokens, per scheme. Dark: `--node-top: color-mix(in srgb, var(--text) 7%, var(--surface)); --lift: rgb(0 0 0 / .45); --halo: 32%`. Light: `--node-top: var(--surface); --lift: rgb(18 22 20 / .12); --halo: 22%`.

`--accent-dim` = the accent at 12–16% alpha. Blueprint grid: `background-image: linear-gradient(var(--border) 1px, transparent 1px), linear-gradient(90deg, var(--border) 1px, transparent 1px); background-size: 24px 24px` at about 50% opacity.

## Visual principles

1. **Quiet ground, one signal.** About 90% of the page is neutral. The accent marks only what the reader must look at now: the key node, the hot path, the active control, the one number that matters.
2. **The figure is the interface.** A term in the prose and its element in the figure are linked. Hover either one, or focus the prose term, and both light up (`diagrams.md` → Linked highlighting).
3. **Overview, then detail.** The full picture comes first. The reader steps, hovers, or expands to get detail. Raw material goes in `<details>`. Sources are the exception: keep them in a visible section at the end, never collapsed.
4. **Every number gets a picture.** A waffle, bar, or sparkline beside it. Tabular figures, the unit smaller and in `--text-dim`, and the comparison stated (`from 5,600`).
5. **Motion shows change or flow.** Blocks rise in once. Dots move along edges at the real rate. Steps reveal parts. Nothing loops for its own sake.
6. **Craft is part of the meaning.** Nodes sit raised on a dot-grid stage. Shapes say what a thing is (a cylinder is a store). The one focal element gets a soft halo, the hot path a glow. No glassmorphism, neon, gradient text or backgrounds, blobs, clip-art, or emoji.

## Typography

| | Rule |
|---|---|
| Hierarchy | Few sizes, big jumps. Contrast comes from the gap between body and display, not from many middle steps. Each level changes one or two of size, weight, and color, never all three. Start with every word quiet, then promote only what must be read first. |
| Measure | Body about 65ch (45–75 characters per line; 66 is the classic ideal). Side notes and multi-column text 40–50. Lead 40–50ch. |
| Leading | Body 1.5–1.6 on screen; more for a longer measure, less for a shorter one. Display 1.0–1.15, tighter as it grows. |
| Tracking | Display tightens as it grows: −0.01em at `h2`, −0.03 to −0.04em at `h1` and big numbers. All caps and small caps get +0.05 to +0.12em. Never track lowercase body text. |
| Breaks | `text-wrap: balance` on headings, `pretty` on paragraphs and captions. Break display lines at phrase boundaries. Flush left, ragged right; never justify on the web. |
| Numerals | `tabular-nums` in tables, KPIs, and anything that updates. Proportional figures in prose (oldstyle in Paper). Number columns right-aligned. Format for reading (`5.6k`, `−86%`) and repeat the unit in every label. |
| Characters | Curly quotes and apostrophes. `–` for ranges, `—` for a break, `−` for minus, `×` for multipliers and sizes, `…`, `≤`. A no-break space between number and unit (`1&nbsp;ms`). |
| Font hygiene | `font-kerning: normal; font-synthesis: none`, and load every weight you use: no faux bold, italic, or small caps. Ligatures on in prose, off in code. Bold or italic, never both. Underline only links and linked terms. |
| Optical edges | `text-box: trim-both cap alphabetic` on headings and big numbers, so spacing is measured from the letters, not the line box (Chrome, Safari; harmless elsewhere). Hang bullets and opening quotes outside the text edge. |
| Pairing | One family plus its mono, or one display face plus one text face. The display face only at `h1`, `h2`, and hero sizes. |

## Layout

| | Rule |
|---|---|
| Grid | 12 columns on the 64rem container, `s-5` gutter. Text spans about 8 columns, figures 12, section labels and side notes 3. Every left edge lands on a column line. |
| One axis | Kicker, headline, deck, figures, captions, and section labels share one flush-left edge. Center only a single number or a title slide. |
| Entry points | Reading order: kicker → headline → deck → figure → caption → body. Each screen has one dominant element, one or two secondary ones, and quiet text. Squint test: blur the page and the dominant element still reads. |
| Section opener | Pick one per page and keep it. Swiss head: a hairline, a mono label in columns 1–3, the `h2` in 4–12 on a shared baseline (reports, reviews; `page.html`). Kicker head: a small label above the `h2` (explainers). Figure head: a full-width figure first, the `h2` as its title (narratives). |
| Proximity | Space above a heading is 2–3× the space below it. A caption sits `s-3` from its figure. Related things are always closer than unrelated things. |
| Rhythm | Vary width and density down the page: wide figure → number strip → grid of small multiples → short text. Avoid three identical blocks in a row. |
| Structure | Space first, a hairline second, a frame last. No card inside a card. Leave real empty space; asymmetric space reads as deliberate, evenly spread gaps read as unfinished. |

## Figures

| | Rule |
|---|---|
| Pick by relationship | Change over time → line or sparkline. Magnitude → bars. Part of a whole → waffle or stacked bar. Ranking → sorted bars. Deviation → bars around zero. Distribution → strip or histogram. Correlation → scatter. Flow → diagram with flow dots. Place → map. |
| Data-ink | Every mark carries data or guides the eye. No chart borders, plot backgrounds, heavy gridlines, or 3D bars. Gridlines in `--border`, only when values must be read. |
| Layering | Ground (texture, rules) < structure (nodes, axes) < data < signal (accent). Each layer is quieter than the one above it. Two lines close together make a third shape (1+1=3): add space or merge them. |
| Smallest difference | Make each distinction as subtle as it can be while it is still clear. Two label levels only: small and dim, larger and bright; bold for emphasis inside them. |
| Labels | On the data, horizontal, left-aligned. Repeat the unit. No legend under 5 series. A `--bg` halo where a label crosses a line. |
| Annotate | One or two notes per chart at the point the caption names: a short leader line and a plain phrase. |
| Honest scale | Bars start at zero. Small multiples share one scale. Sort by value unless the order means something. Line charts about 2:1 to 3:1. |
| Line weights | Three: 1 for structure, 1.5–1.75 for data and outlines, 2.5–3 for the signal. Glyph strokes match the stem weight of the labels beside them. |
| Color scales | Sequential: one hue in OKLCH lightness steps. Diverging: two hues around a neutral middle. Categorical: up to 5 hues at equal OKLCH lightness and chroma. Never color alone. |
| Optical alignment | Center a label on its cap height, not its box. Nudge triangles and play icons toward their point; round shapes overshoot a flat edge by about 2%. |

## Topic motif

The register sets the base. The subject adds a light touch of its own, so a page about Postgres does not look like a page about audio. Take the motif from the subject and use it in 2–3 places at most.

| Lever | Rule | Examples |
|---|---|---|
| Accent hue | The subject's own color (brand, material, convention), adjusted to 4.5:1 on `--bg` and `--surface` in both schemes. Keep the register accent if the hue reads as a status color (red ≈ risk, green ≈ ok). | Postgres blue · Rust orange · Kubernetes blue · Redis red → keep the register accent |
| Stage texture | Dot grid by default. 24px line grid for systems and plans, ruled lines for writing, isometric grid for hardware and 3D. Texture at 15% contrast or less. | |
| Glyphs | Node glyphs from the domain's own symbols, line-drawn. | circuit symbols · map pins · waveform · git branch |
| Type detail | One typographic habit of the domain. | price columns for finance · mono timestamps for incidents · small caps for specs · superscript citations for research |
| Shape language | The domain's own diagram convention. | swimlanes for processes · ledger for accounting · timing staff for protocols · floor plan for physical layout |

Test each touch: if removing it makes the page no harder to read and no less specific to the topic, cut it. No puns, mascots, or illustration.

## Scale

```css
:root {
  color-scheme: light dark;
  --t-label: .75rem; --t-small: .875rem; --t-body: 1rem; --t-lead: 1.25rem;
  --t-h2: 1.625rem; --t-h1: clamp(2.25rem, 5.5vw, 4rem); --t-hero: clamp(3rem, 9vw, 6.5rem);
  --s-1: .25rem; --s-2: .5rem; --s-3: .75rem; --s-4: 1rem;
  --s-5: 1.5rem; --s-6: 2rem; --s-7: 3rem; --s-8: 4.5rem;
  --r-1: 4px; --r-2: 10px;
  --ease: cubic-bezier(.16, 1, .3, 1); --fast: 150ms; --med: 300ms; --slow: 500ms;
}
```

| Decision | Rule |
|---|---|
| Spacing | Scale steps only. Inside a component: `s-2`–`s-4`. Between components: `s-5`–`s-6`. Between sections: `s-8`. A bigger gap means less related. |
| Type | Seven sizes, no others, plus sizes a component spec names (KPI value). The steps run about ×1.25 apart, with a big jump to display. `--t-hero` only in Editorial. `--t-small` only for buttons, code, and mono labels. Body 400; headings 600, or the display face at 400–500. Leading and tracking: see Typography. |
| Labels | Mono, `--t-label`, `--text-dim`. Uppercase with `.08em` tracking only for 3 words or fewer. |
| Radius | `r-1` for chips, buttons, inputs, and inline highlights. `r-2` for frames, tables, and overlays. Nothing else is rounded. Blueprint uses `r-1` everywhere. |
| Accent | One accent, on 10% of the screen or less. Status colors (`ok warn risk info`) only mean status. |
| Motion | Move and reveal only with `transform`, `opacity`, and `stroke-dashoffset`. Color changes on hover and highlight may fade at `fast`. `med` for state, `slow` for steps and entrances, 900ms for count-ups and bar growth. Always `--ease`. |
| Effects | Shadow (`--lift`): raised diagram nodes and overlays only. Glow: the key node (`--halo`) and the hot edge only. |
| Layout | Container max 64rem on a 12-column grid. Text about 65ch. Figures use the full width. Card grids: `repeat(auto-fit, minmax(13rem, 1fr))`. |

## Components

| Component | Spec |
|---|---|
| Page header | Kicker (mono label with a short accent rule) → `h1` that states the answer → deck: lead (`t-lead`, `--text-dim`, one bold phrase in `--text`, a sentence or two). If the answer is a number, the number leads the `h1` in accent. Then a quiet meta line (scope, period). `s-4` between them. |
| Figure | `<figure>` → `.frame` (stage: `--bg` with the motif texture, 1px border, `r-2`, padding `s-5`) → `<figcaption>` (`t-body`, `--text-dim`) that starts with `Fig. N` in mono and states the claim. |
| Dimming | To focus part of a figure, fade shapes and lines to 15–25% opacity. Never fade text: dimmed labels change to `--text-dim`, and labels of future steps are hidden. Never put accent-colored text on `--accent-dim`; use `--text` there. |
| Diagram | Node: `#ve-node` gradient fill, 1.5 `--border-bright` stroke, rx 6, `--lift` shadow. Key node: accent tint fill, 2 `--accent` stroke, halo. Edge: 1.75 `--text-dim`. Hot edge: 2.75 `--accent` with a 5px glow. Async: dash `6 5`. One arrowhead marker with `context-stroke`. Edge labels: mono, 14 units, 9 units above the line, `--bg` halo. Identical in every figure. |
| KPI strip | One frame. Cells split by 1px rules (flex-wrap, `gap:1px` over a `--border` background, cells `flex:1 1 14rem` so a wrapped row stretches). Each cell: label → value (2.75rem, 600, tabular, −0.04em, counts up) → its picture (waffle, bars, or sparkline). |
| Small multiples | Cards in `repeat(auto-fit, minmax(14.5rem, 1fr))`: chip → short title → mini diagram. The changed part takes the case's status color. Replaces a table when rows are scenarios. |
| Chip | Mono `t-label` 600, 1px `currentColor` border, `r-1`. Shape and word: ● ok · ▲ warn · ■ risk · ◆ info. |
| Table | Header: surface, label style. Cells: `t-body`, padding `s-3 s-4`. Row rules only. Numbers right-aligned and tabular. Inside `.table-scroll` with an `r-2` frame. |
| Button | Mono `t-small`, surface, 1px `--border-bright`, `r-1`, padding `s-2 s-3`. Hover and focus: accent border. |
| Callout | Surface, `r-2`, padding `s-4`, a status chip as its title. No colored side bar. |
| Code | Mono `t-small`, surface, `r-2`, padding `s-4`, scrolls horizontally. Inline code: `.875em`, no box. |

## Polish pass

- The same element looks the same everywhere: captions, chips, arrowheads, stroke widths.
- `::selection` uses `--accent-dim`. Sections get `scroll-margin-top` under a sticky nav.
- Hover and focus look the same. Every control has a visible focus ring.
- Nothing shifts on load: every SVG has a `viewBox`, and every image has a width and height.
- `@media print`: switch to the light-scheme values on a white ground, hide controls and moving dots, drop shadows and glows, show every step fully drawn, and keep figures and cards from splitting across pages.

=== FILE: references/themes.md ===
# Themes and runtime picker

Use this only when the user asks for switchable themes or fonts, or names a palette. Otherwise, commit to one palette.

A theme is one fixed palette, not a light/dark pair. The picker is the reader's light/dark control. Do not wrap theme values in `prefers-color-scheme`.

## Palettes

Columns map to tokens. `-dim` variants are the same hex at about 12% alpha (`#rrggbb1f`). Use `rgba(255,255,255,.08)` for `--border` on dark themes and `rgba(0,0,0,.08)` on light themes.

Text tokens (`--text --text-dim --accent --ok --warn --risk --info`) reach 4.5:1 on both `--bg` and `--surface`. Where a palette's own value failed, it is lifted toward the text color. `--node-a/b/c` are the canonical palette values: use them for fills, strokes, and chip markers, not for text. Set `--border-bright` to the `--text-dim` value, so diagram outlines and control borders reach 3:1.

| id | mode | --bg | --surface | --text | --text-dim | --accent | --node-a | --node-b | --node-c | --ok | --warn | --risk | --info |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dracula | dark | #282a36 | #44475a | #f8f8f2 | #adb6d0 | #caa8fa | #8be9fd | #50fa7b | #ff79c6 | #50fa7b | #ffb86c | #ff9b9b | #8be9fd |
| nord | dark | #2e3440 | #3b4252 | #eceff4 | #a9aeb7 | #88c0d0 | #88c0d0 | #a3be8c | #b48ead | #a3be8c | #daa08e | #d89fa4 | #88c0d0 |
| one-dark | dark | #282c34 | #2c313a | #abb2bf | #9398a1 | #61afef | #61afef | #98c379 | #c678dd | #98c379 | #e5c07b | #e37981 | #61afef |
| catppuccin-mocha | dark | #1e1e2e | #313244 | #cdd6f4 | #989baa | #cba6f7 | #89b4fa | #a6e3a1 | #f5c2e7 | #a6e3a1 | #fab387 | #f38ba8 | #89b4fa |
| tokyo-night | dark | #1a1b26 | #24283b | #a9b1d6 | #898fac | #7aa2f7 | #7aa2f7 | #9ece6a | #bb9af7 | #9ece6a | #ff9e64 | #f7768e | #7aa2f7 |
| gruvbox-dark | dark | #282828 | #3c3836 | #ebdbb2 | #afa18e | #fe8019 | #83a598 | #b8bb26 | #d3869b | #b8bb26 | #fe8019 | #fc7c6d | #88a99c |
| synthwave-84 | dark | #262335 | #241b2f | #ffffff | #848bbd | #ff7edb | #36f9f6 | #72f1b8 | #fede5d | #72f1b8 | #ff8b39 | #fe4652 | #36f9f6 |
| solarized-light | light | #fdf6e3 | #eee8d5 | #526970 | #526970 | #00629b | #00629b | #859900 | #d33682 | #606e00 | #b54314 | #c42d2a | #00629b |
| github-light | light | #ffffff | #f6f8fa | #1f2328 | #656d76 | #0969da | #0969da | #1a7f37 | #8250df | #1a7f37 | #bc4c00 | #cf222e | #0969da |
| catppuccin-latte | light | #eff1f5 | #ccd0da | #4c4f69 | #54565f | #7230c9 | #1e66f5 | #40a02b | #ea76cb | #29661c | #983c07 | #b30d30 | #1851c2 |
| gruvbox-light | light | #fbf1c7 | #ebdbb2 | #3c3836 | #6b5f56 | #ad3903 | #076678 | #79740e | #8f3f71 | #67630c | #ad3903 | #9d0006 | #076678 |

Font pairs (id → body / mono): `dm` DM Sans / Fira Code · `instrument` Instrument Sans / JetBrains Mono · `plex` IBM Plex Sans / IBM Plex Mono · `bricolage` Bricolage Grotesque / JetBrains Mono · `jakarta` Plus Jakarta Sans / Azeret Mono. Load all of them in one Google Fonts link, at every weight the page uses. A display serif for headings goes in its own `--font-display` and does not change with the picker.

## Picker contract

- Put one fixed bar at the top right: theme dots (fill `--surface`, ring `--accent`), a divider, then `Aa` font chips, each set in its own family. Every control uses `aria-pressed`.
- Build the dots and chips from the `THEMES` / `FONT_PAIRS` data. Never hand-write them, so a control cannot drift from the value it sets.
- Put the default theme and font in `:root` as plain CSS. Then the page renders correctly without JS, and you do not need to apply anything on load.
- `applyTheme(id)` sets every column above, including the status colors and `--border-bright`, with `root.style.setProperty`. `applyFont(id)` sets `--font-body` and `--font-mono`. Both are `async`, update `aria-pressed`, and then redraw anything that baked colors or measured text, such as a canvas chart.
- Rules must read fonts only through `var(--font-body)` and `var(--font-mono)`.
- Draw the active ring in `var(--text)`, not white, because white disappears on light themes. Give every control a focus ring. Hide the bar in print.
- Declare `DEFAULT_THEME`, `DEFAULT_FONT`, and the active state before any script that reads them. `let` and `const` are not hoisted.

## Project defaults

`visual-explainer.config.md` (harness-neutral) can set `theme:` and `font:` to the ids above. In Claude Code, `.claude/visual-explainer.local.md` overrides it only for personal preferences. Both only seed the defaults. The reader can still switch, and an unknown value falls back to the page's own choice.

=== FILE: LICENSE ===
MIT License

Copyright (c) 2025 Nico Bailon

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
