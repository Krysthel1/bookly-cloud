from uuid import uuid4
from tests.conftest import make_token


def test_health_and_readiness(client):
    tc, _, _ = client
    assert tc.get("/health").status_code == 200
    assert tc.get("/ready").status_code == 200


def test_auth_and_role_protection(client):
    tc, ids, _ = client
    # Sin token -> 401
    assert tc.get("/api/v1/auth/me").status_code == 401

    # Token cliente -> rol customer, sin acceso admin
    cust_headers = {"Authorization": f"Bearer {make_token(ids['customer'], 'cliente@bookly.pe')}"}
    me = tc.get("/api/v1/auth/me", headers=cust_headers)
    assert me.status_code == 200
    assert "customer" in me.json()["roles"]
    assert "admin" not in me.json()["roles"]

    assert tc.get("/api/v1/admin/dashboard", headers=cust_headers).status_code == 403

    # Nuevo usuario auto-provisionado solo recibe rol customer
    new_uid = uuid4()
    new_headers = {"Authorization": f"Bearer {make_token(new_uid, 'nuevo@bookly.pe')}"}
    new_me = tc.get("/api/v1/auth/me", headers=new_headers)
    assert new_me.status_code == 200
    assert new_me.json()["roles"] == ["customer"]


def test_catalog_search_and_admin_crud(client):
    tc, ids, _ = client
    res = tc.get("/api/v1/books?search=Ribeyro")
    assert res.status_code == 200
    assert res.json()["meta"]["total"] == 2

    admin_headers = {"Authorization": f"Bearer {make_token(ids['admin'], 'admin@bookly.pe')}"}
    create_res = tc.post(
        "/api/v1/admin/books",
        headers=admin_headers,
        json={
            "title": "El Aleph",
            "isbn": "9788499089515",
            "synopsis": "Libro fundamental de cuentos de Jorge Luis Borges.",
            "price": 60.0,
            "discount_percent": 0,
            "stock": 8,
            "author_ids": [str(ids["author"])],
            "category_ids": [str(ids["cat"])],
        },
    )
    assert create_res.status_code == 201
    assert create_res.json()["title"] == "El Aleph"


def test_cart_checkout_idempotency_stock_and_ownership(client):
    tc, ids, _ = client
    cust_headers = {"Authorization": f"Bearer {make_token(ids['customer'], 'cliente@bookly.pe')}"}
    other_headers = {"Authorization": f"Bearer {make_token(ids['other'], 'otro@bookly.pe')}"}
    admin_headers = {"Authorization": f"Bearer {make_token(ids['admin'], 'admin@bookly.pe')}"}

    # Validar stock en carrito: book1 tiene 5 unidades
    over_stock = tc.post(
        "/api/v1/cart/items",
        headers=cust_headers,
        json={"book_id": str(ids["book1"]), "quantity": 10},
    )
    assert over_stock.status_code == 409

    # Agregar 2 unidades (precio final 90.00 c/u -> subtotal 180.00)
    add_res = tc.post(
        "/api/v1/cart/items",
        headers=cust_headers,
        json={"book_id": str(ids["book1"]), "quantity": 2},
    )
    assert add_res.status_code == 201
    assert float(add_res.json()["subtotal"]) == 180.0

    # Checkout transaccional con cupón BOOKLY10 (10% de 180 = 18 -> neto 162 >= 120 -> envío gratis = 162.00)
    checkout_payload = {
        "shipping_address": {
            "recipient_name": "Cliente Uno",
            "phone": "999888777",
            "street_address": "Av. Arequipa 1234",
            "district": "Lince",
            "city": "Lima",
            "region": "Lima",
        },
        "shipping_method": "estandar",
        "payment_method": "yape",
        "coupon_code": "BOOKLY10",
        "idempotency_key": "idem-key-001",
    }
    order_res = tc.post("/api/v1/orders/checkout", headers=cust_headers, json=checkout_payload)
    assert order_res.status_code == 201
    order = order_res.json()
    assert order["order_code"].startswith("BKL-")
    assert float(order["subtotal"]) == 180.0
    assert float(order["discount_amount"]) == 18.0
    assert float(order["shipping_cost"]) == 0.0
    assert float(order["total"]) == 162.0
    assert order["payment"]["status"] == "simulado_aprobado"

    # Idempotencia: reintentar con mismo idempotency_key devuelve mismo pedido sin duplicar
    dup_res = tc.post("/api/v1/orders/checkout", headers=cust_headers, json=checkout_payload)
    assert dup_res.status_code == 201
    assert dup_res.json()["id"] == order["id"]

    # Stock decrementado: 5 - 2 = 3
    book_after = tc.get(f"/api/v1/books/{ids['book1']}").json()
    assert book_after["stock"] == 3

    # Otro cliente NO puede ver ni cancelar el pedido
    assert tc.get(f"/api/v1/orders/{order['id']}", headers=other_headers).status_code == 403
    assert tc.post(f"/api/v1/orders/{order['id']}/cancel", headers=other_headers).status_code == 403

    # Otro cliente intenta comprar 4 unidades cuando solo quedan 3 -> 409
    assert (
        tc.post(
            "/api/v1/cart/items",
            headers=other_headers,
            json={"book_id": str(ids["book1"]), "quantity": 4},
        ).status_code
        == 409
    )

    # Cancelación por dueño devuelve stock una sola vez
    cancel_res = tc.post(f"/api/v1/orders/{order['id']}/cancel", headers=cust_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelado"
    assert cancel_res.json()["stock_restored"] is True
    assert tc.get(f"/api/v1/books/{ids['book1']}").json()["stock"] == 5

    # Segundo intento de cancelación falla y no duplica stock
    assert tc.post(f"/api/v1/orders/{order['id']}/cancel", headers=cust_headers).status_code == 400
    assert tc.get(f"/api/v1/books/{ids['book1']}").json()["stock"] == 5

    # Dashboard, reporte CSV y auditoría como admin
    assert tc.get("/api/v1/admin/dashboard", headers=admin_headers).status_code == 200
    csv_res = tc.get("/api/v1/admin/reports/sales?format=csv", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "order_code" in csv_res.text
    assert tc.get("/api/v1/admin/audit-logs", headers=admin_headers).status_code == 200
