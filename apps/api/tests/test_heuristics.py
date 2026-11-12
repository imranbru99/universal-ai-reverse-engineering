from workers.modeling.heuristics import infer_bookstore_domain


def test_bookstore_inference():
    states = [
        {
            "title": "Catalog",
            "url": "http://demo-target:3100/catalog",
            "components": [{"name": "Add to cart"}, {"name": "Book"}],
        },
        {"title": "Cart", "url": "http://demo-target:3100/cart", "components": []},
        {"title": "Login", "url": "http://demo-target:3100/login", "components": [{"name": "Sign in"}]},
    ]
    result = infer_bookstore_domain(states)
    names = {e["name"] for e in result["entities"]}
    assert "Book" in names
    assert "CartItem" in names
    assert result["claims"]
