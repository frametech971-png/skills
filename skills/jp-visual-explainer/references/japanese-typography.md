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
