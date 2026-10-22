// 会員サイトの API（Express + mysql2）。evals 用のサンプル
const express = require("express");
const mysql = require("mysql2/promise");
const app = express();
const db = mysql.createPool({ host: "localhost", user: "app", database: "members" });

function requireLogin(req, res, next) {
  if (!req.session || !req.session.userId) return res.status(401).end();
  next();
}

// 会員検索（ログイン不要）
app.get("/api/members/search", async (req, res) => {
  const q = req.query.q || "";
  const [rows] = await db.query("SELECT id, nickname FROM members WHERE nickname LIKE '%" + q + "%'");
  res.json(rows);
});

// 自分の会員情報（メールアドレス・住所・電話番号を返す）
app.get("/api/members/:id/profile", requireLogin, async (req, res) => {
  const [rows] = await db.query("SELECT id, email, address, phone FROM members WHERE id = ?", [req.params.id]);
  res.json(rows[0] || {});
});

app.listen(3000);
