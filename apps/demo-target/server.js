const express = require("express");

const app = express();
const PORT = process.env.PORT || 3100;

const books = [
  { id: "1", title: "Observable Systems", author: "A. Rivera", price: 2400, isbn: "978-0001" },
  { id: "2", title: "State Graphs Explained", author: "M. Chen", price: 1850, isbn: "978-0002" },
  { id: "3", title: "Evidence-Driven Design", author: "S. Okonkwo", price: 2100, isbn: "978-0003" },
];

const cart = [];

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

function layout(title, body) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>${title}</title>
  <style>
    :root { --bg:#f7f3ea; --ink:#221f1b; --accent:#255f4b; --line:#d9d0c1; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Georgia, "Times New Roman", serif; background:radial-gradient(circle at top left,#fff8ea,var(--bg)); color:var(--ink); }
    header { border-bottom:1px solid var(--line); padding:16px 24px; display:flex; gap:16px; align-items:center; justify-content:space-between; }
    nav a { margin-right:12px; color:var(--accent); text-decoration:none; }
    main { max-width:960px; margin:0 auto; padding:32px 24px 64px; }
    .card { border:1px solid var(--line); padding:16px; margin:12px 0; background:#fffdf8; }
    button, .btn { background:var(--accent); color:white; border:0; padding:8px 12px; cursor:pointer; text-decoration:none; display:inline-block; }
    input { padding:8px; border:1px solid var(--line); width:100%; max-width:320px; }
    .muted { color:#666; }
  </style>
</head>
<body>
  <header>
    <div><strong data-testid="brand">Demo Bookstore</strong> <span class="muted">authorized test target</span></div>
    <nav>
      <a href="/" data-testid="nav-home">Home</a>
      <a href="/catalog" data-testid="nav-catalog">Catalog</a>
      <a href="/cart" data-testid="nav-cart">Cart (${cart.reduce((n,i)=>n+i.quantity,0)})</a>
      <a href="/login" data-testid="nav-login">Login</a>
      <a href="/about" data-testid="nav-about">About</a>
    </nav>
  </header>
  <main>
    <h1>${title}</h1>
    ${body}
  </main>
</body>
</html>`;
}

app.get("/health", (_req, res) => res.json({ status: "ok" }));

app.get("/", (_req, res) => {
  res.send(
    layout(
      "Welcome",
      `<p class="muted">A small bookstore used by REVERSEFORGE AI for deterministic demos.</p>
       <p><a class="btn" href="/catalog" data-testid="cta-browse">Browse catalog</a></p>`
    )
  );
});

app.get("/catalog", (_req, res) => {
  const items = books
    .map(
      (b) => `<div class="card" data-testid="book-${b.id}">
        <h2>${b.title}</h2>
        <p>by ${b.author}</p>
        <p>$${(b.price / 100).toFixed(2)}</p>
        <a href="/books/${b.id}" data-testid="book-link-${b.id}">View details</a>
      </div>`
    )
    .join("");
  res.send(layout("Catalog", items));
});

app.get("/books/:id", (req, res) => {
  const book = books.find((b) => b.id === req.params.id);
  if (!book) return res.status(404).send(layout("Not found", "<p>Book not found</p>"));
  res.send(
    layout(
      book.title,
      `<div class="card">
        <p>Author: ${book.author}</p>
        <p>ISBN: ${book.isbn}</p>
        <p>Price: $${(book.price / 100).toFixed(2)}</p>
        <form method="post" action="/cart/add">
          <input type="hidden" name="book_id" value="${book.id}"/>
          <label>Quantity <input name="quantity" type="number" value="1" min="1"/></label>
          <p><button type="submit" data-testid="add-to-cart">Add to cart</button></p>
        </form>
      </div>`
    )
  );
});

app.post("/cart/add", (req, res) => {
  const bookId = String(req.body.book_id || "");
  const quantity = Math.max(1, Number(req.body.quantity || 1));
  const existing = cart.find((c) => c.book_id === bookId);
  if (existing) existing.quantity += quantity;
  else cart.push({ book_id: bookId, quantity });
  res.redirect("/cart");
});

app.get("/cart", (_req, res) => {
  if (!cart.length) {
    return res.send(layout("Cart", `<p data-testid="empty-cart">Your cart is empty.</p>`));
  }
  const rows = cart
    .map((c) => {
      const book = books.find((b) => b.id === c.book_id);
      return `<div class="card">${book ? book.title : c.book_id} × ${c.quantity}</div>`;
    })
    .join("");
  res.send(layout("Cart", rows + `<p><a class="btn" href="/checkout">Checkout</a></p>`));
});

app.get("/checkout", (_req, res) => {
  res.send(
    layout(
      "Checkout",
      `<p class="muted">Demo checkout is non-destructive and does not process payments.</p>
       <form method="post" action="/checkout">
         <p><input name="email" placeholder="you@example.com" data-testid="checkout-email"/></p>
         <button type="submit" data-testid="place-order">Place demo order</button>
       </form>`
    )
  );
});

app.post("/checkout", (req, res) => {
  cart.length = 0;
  res.send(layout("Order placed", `<p data-testid="order-complete">Demo order recorded for ${req.body.email || "guest"}.</p>`));
});

app.get("/login", (_req, res) => {
  res.send(
    layout(
      "Login",
      `<form method="post" action="/login">
        <p><input name="email" type="email" placeholder="email" data-testid="login-email"/></p>
        <p><input name="password" type="password" placeholder="password" data-testid="login-password"/></p>
        <button type="submit" data-testid="login-submit">Sign in</button>
      </form>
      <p class="muted">Demo accepts any credentials and does not validate passwords strongly.</p>`
    )
  );
});

app.post("/login", (req, res) => {
  res.send(layout("Signed in", `<p data-testid="login-success">Welcome ${req.body.email || "user"}</p>`));
});

app.get("/about", (_req, res) => {
  res.send(layout("About", `<p>Authorized bundled target for REVERSEFORGE AI exploration demos.</p>`));
});

// Intentionally out-of-scope style path for negative tests when prefixes exclude it
app.get("/admin/secret", (_req, res) => {
  res.status(403).send(layout("Forbidden", "<p>Admin area</p>"));
});

app.listen(PORT, () => console.log(`Demo bookstore on ${PORT}`));
