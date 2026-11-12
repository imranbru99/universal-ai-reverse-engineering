from __future__ import annotations

from typing import Any


def infer_bookstore_domain(states: list[dict[str, Any]]) -> dict[str, Any]:
    """Deterministic domain inference from observed demo-target screens."""
    titles = " ".join(s.get("title", "") for s in states).lower()
    urls = " ".join(s.get("url", "") for s in states).lower()
    blob = titles + " " + urls
    for s in states:
        for c in s.get("components", []):
            blob += " " + str(c.get("name", "")).lower()

    entities = []
    claims = []

    if "book" in blob or "catalog" in blob:
        entities.append(
            {
                "name": "Book",
                "description": "Catalog item shown on listing/detail pages",
                "confidence": 0.85,
                "fields": [
                    {"name": "title", "data_type": "string", "nullable": False},
                    {"name": "author", "data_type": "string", "nullable": False},
                    {"name": "price_cents", "data_type": "integer", "nullable": False},
                    {"name": "isbn", "data_type": "string", "nullable": True},
                ],
            }
        )
        claims.append(
            {
                "content": "Application manages a Book catalog entity with title, author, and price.",
                "classification": "INFERRED",
                "confidence": 0.85,
                "rationale": "Observed book listing/detail UI labels and routes.",
                "open_questions": ["Is inventory quantity tracked server-side?"],
            }
        )

    if "cart" in blob:
        entities.append(
            {
                "name": "CartItem",
                "description": "Line item in a shopping cart",
                "confidence": 0.8,
                "fields": [
                    {"name": "book_id", "data_type": "uuid", "nullable": False},
                    {"name": "quantity", "data_type": "integer", "nullable": False},
                ],
            }
        )
        claims.append(
            {
                "content": "Users can add books to a cart with quantities.",
                "classification": "OBSERVED",
                "confidence": 0.9,
                "rationale": "Cart page and add-to-cart controls observed.",
                "open_questions": [],
            }
        )

    if "login" in blob or "sign in" in blob:
        entities.append(
            {
                "name": "UserAccount",
                "description": "Customer account for authenticated flows",
                "confidence": 0.7,
                "fields": [
                    {"name": "email", "data_type": "string", "nullable": False},
                    {"name": "password_hash", "data_type": "string", "nullable": False},
                ],
            }
        )
        claims.append(
            {
                "content": "Login screen implies UserAccount entity (password storage UNKNOWN).",
                "classification": "INFERRED",
                "confidence": 0.7,
                "rationale": "Login form observed; credential storage not observable.",
                "open_questions": ["Password hashing algorithm?", "SSO present?"],
            }
        )

    if not entities:
        entities.append(
            {
                "name": "Page",
                "description": "Generic content page observed during crawl",
                "confidence": 0.4,
                "fields": [{"name": "path", "data_type": "string", "nullable": False}],
            }
        )
        claims.append(
            {
                "content": "Insufficient domain signals; generic Page entity proposed.",
                "classification": "UNKNOWN",
                "confidence": 0.3,
                "rationale": "No strong domain keywords in observed UI.",
                "open_questions": ["What is the primary business object?"],
            }
        )

    endpoints = []
    for e in entities:
        name = e["name"].lower()
        endpoints.append(
            {
                "method": "GET",
                "path": f"/api/{name}s",
                "summary": f"List {e['name']} resources",
                "classification": "INFERRED",
            }
        )

    return {"entities": entities, "claims": claims, "endpoints": endpoints}
