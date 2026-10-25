import os
import tempfile
import unittest

from app import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.path)
        self.app = create_app({"DATABASE": self.path, "TESTING": True})
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    # helpers
    def make_category(self, name="Electronics"):
        return self.client.post("/api/categories", json={"name": name}).get_json()

    def make_product(self, **kw):
        body = {"name": "Phone", "price": 199.99, "stock": 10}
        body.update(kw)
        return self.client.post("/api/products", json=body).get_json()

    def make_customer(self, email="a@b.com"):
        return self.client.post(
            "/api/customers", json={"name": "Asha", "email": email}
        ).get_json()


class CategoryTests(ApiTestCase):
    def test_crud(self):
        c = self.make_category()
        self.assertEqual(c["name"], "Electronics")
        self.assertEqual(self.client.get(f"/api/categories/{c['category_id']}").status_code, 200)
        r = self.client.put(f"/api/categories/{c['category_id']}", json={"description": "Gadgets"})
        self.assertEqual(r.get_json()["description"], "Gadgets")
        self.assertEqual(self.client.get("/api/categories").get_json()["total"], 1)
        self.assertEqual(self.client.delete(f"/api/categories/{c['category_id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/categories/{c['category_id']}").status_code, 404)

    def test_duplicate_name_conflict(self):
        self.make_category()
        r = self.client.post("/api/categories", json={"name": "Electronics"})
        self.assertEqual(r.status_code, 409)


class ProductTests(ApiTestCase):
    def test_crud_and_filter(self):
        cat = self.make_category()
        p = self.make_product(category_id=cat["category_id"])
        self.make_product(name="Book", price=10)
        pid = p["product_id"]
        self.assertEqual(self.client.get(f"/api/products/{pid}").get_json()["name"], "Phone")
        r = self.client.get(f"/api/products?category_id={cat['category_id']}").get_json()
        self.assertEqual(r["total"], 1)
        r = self.client.get("/api/products?q=boo").get_json()
        self.assertEqual(r["items"][0]["name"], "Book")
        r = self.client.put(f"/api/products/{pid}", json={"price": 150})
        self.assertEqual(r.get_json()["price"], 150)
        self.assertEqual(self.client.delete(f"/api/products/{pid}").status_code, 204)

    def test_validation(self):
        self.assertEqual(self.client.post("/api/products", json={"name": "x"}).status_code, 400)
        self.assertEqual(
            self.client.post("/api/products", json={"name": "x", "price": -1}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                "/api/products", json={"name": "x", "price": 1, "category_id": 99}
            ).status_code,
            400,
        )
        self.assertEqual(self.client.post("/api/products", data="nope").status_code, 400)

    def test_pagination(self):
        for i in range(5):
            self.make_product(name=f"P{i}")
        r = self.client.get("/api/products?page=2&per_page=2").get_json()
        self.assertEqual((len(r["items"]), r["total"], r["page"]), (2, 5, 2))


class CustomerTests(ApiTestCase):
    def test_crud(self):
        c = self.make_customer()
        cid = c["customer_id"]
        r = self.client.put(f"/api/customers/{cid}", json={"phone": "9999999999"})
        self.assertEqual(r.get_json()["phone"], "9999999999")
        self.assertEqual(self.client.delete(f"/api/customers/{cid}").status_code, 204)

    def test_email_rules(self):
        self.make_customer()
        self.assertEqual(
            self.client.post("/api/customers", json={"name": "B", "email": "a@b.com"}).status_code,
            409,
        )
        self.assertEqual(
            self.client.post("/api/customers", json={"name": "B", "email": "bad"}).status_code, 400
        )


class OrderTests(ApiTestCase):
    def place(self, customer, product, qty):
        return self.client.post(
            "/api/orders",
            json={
                "customer_id": customer["customer_id"],
                "items": [{"product_id": product["product_id"], "quantity": qty}],
            },
        )

    def stock(self, product):
        return self.client.get(f"/api/products/{product['product_id']}").get_json()["stock"]

    def test_place_order_reduces_stock_and_totals(self):
        c, p = self.make_customer(), self.make_product(price=100, stock=5)
        r = self.place(c, p, 2)
        self.assertEqual(r.status_code, 201)
        body = r.get_json()
        self.assertEqual(body["total_amount"], 200)
        self.assertEqual(body["status"], "PENDING")
        self.assertEqual(body["items"][0]["line_total"], 200)
        self.assertEqual(self.stock(p), 3)

    def test_insufficient_stock_rolls_back_everything(self):
        c = self.make_customer()
        p1 = self.make_product(name="A", stock=5)
        p2 = self.make_product(name="B", stock=1)
        r = self.client.post(
            "/api/orders",
            json={
                "customer_id": c["customer_id"],
                "items": [
                    {"product_id": p1["product_id"], "quantity": 2},
                    {"product_id": p2["product_id"], "quantity": 3},
                ],
            },
        )
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.stock(p1), 5)  # rolled back
        self.assertEqual(self.client.get("/api/orders").get_json()["total"], 0)

    def test_invalid_payloads(self):
        c, p = self.make_customer(), self.make_product()
        self.assertEqual(self.client.post("/api/orders", json={"customer_id": 1}).status_code, 400)
        self.assertEqual(self.place({"customer_id": 999}, p, 1).status_code, 400)
        self.assertEqual(self.place(c, {"product_id": 999}, 1).status_code, 400)
        self.assertEqual(self.place(c, p, 0).status_code, 400)

    def test_status_flow_and_cancel_restocks(self):
        c, p = self.make_customer(), self.make_product(stock=5)
        oid = self.place(c, p, 3).get_json()["order_id"]
        self.assertEqual(self.stock(p), 2)
        r = self.client.patch(f"/api/orders/{oid}/status", json={"status": "PAID"})
        self.assertEqual(r.get_json()["status"], "PAID")
        r = self.client.patch(f"/api/orders/{oid}/status", json={"status": "DELIVERED"})
        self.assertEqual(r.status_code, 409)  # illegal jump
        r = self.client.patch(f"/api/orders/{oid}/status", json={"status": "CANCELLED"})
        self.assertEqual(r.get_json()["status"], "CANCELLED")
        self.assertEqual(self.stock(p), 5)  # stock returned

    def test_delete_rules_and_guards(self):
        c, p = self.make_customer(), self.make_product(stock=5)
        oid = self.place(c, p, 1).get_json()["order_id"]
        # customer and product are protected while orders exist
        self.assertEqual(self.client.delete(f"/api/customers/{c['customer_id']}").status_code, 409)
        self.assertEqual(self.client.delete(f"/api/products/{p['product_id']}").status_code, 409)
        self.client.patch(f"/api/orders/{oid}/status", json={"status": "PAID"})
        self.assertEqual(self.client.delete(f"/api/orders/{oid}").status_code, 409)
        self.client.patch(f"/api/orders/{oid}/status", json={"status": "CANCELLED"})
        self.assertEqual(self.client.delete(f"/api/orders/{oid}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/orders/{oid}").status_code, 404)

    def test_list_filters(self):
        c, p = self.make_customer(), self.make_product(stock=10)
        self.place(c, p, 1)
        self.place(c, p, 1)
        self.assertEqual(self.client.get(f"/api/orders?customer_id={c['customer_id']}").get_json()["total"], 2)
        self.assertEqual(self.client.get("/api/orders?status=PAID").get_json()["total"], 0)
        self.assertEqual(self.client.get("/api/orders?status=BOGUS").status_code, 400)


class ConcurrencyTests(ApiTestCase):
    def test_no_overselling_under_concurrent_orders(self):
        import threading

        c, p = self.make_customer(), self.make_product(stock=5)
        results = []

        def buy():
            r = self.app.test_client().post(
                "/api/orders",
                json={"customer_id": c["customer_id"],
                      "items": [{"product_id": p["product_id"], "quantity": 1}]},
            )
            results.append(r.status_code)

        threads = [threading.Thread(target=buy) for _ in range(20)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(results.count(201), 5)
        self.assertEqual(results.count(409), 15)
        stock = self.client.get(f"/api/products/{p['product_id']}").get_json()["stock"]
        self.assertEqual(stock, 0)


class MiscTests(ApiTestCase):
    def test_health_and_404(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "UP"})
        self.assertEqual(self.client.get("/api/nothing").status_code, 404)


if __name__ == "__main__":
    unittest.main()
