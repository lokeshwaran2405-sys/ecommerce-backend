from ..db import transaction
from ..errors import ConflictError, NotFoundError, ValidationError
from ..repositories.customer_repository import CustomerRepository
from ..repositories.order_repository import OrderRepository
from ..repositories.product_repository import ProductRepository
from .validation import clean_int, require_json

# Allowed status transitions (order life-cycle state machine)
TRANSITIONS = {
    "PENDING": {"PAID", "CANCELLED"},
    "PAID": {"SHIPPED", "CANCELLED"},
    "SHIPPED": {"DELIVERED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}


class OrderService:
    def __init__(self, db):
        self.db = db
        self.orders = OrderRepository(db)
        self.products = ProductRepository(db)
        self.customers = CustomerRepository(db)

    # ---- helpers -------------------------------------------------------
    def _parse_items(self, payload):
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            raise ValidationError("'items' must be a non-empty list")
        merged = {}
        for entry in items:
            entry = require_json(entry)
            pid = clean_int(entry, "product_id", minimum=1)
            qty = clean_int(entry, "quantity", minimum=1)
            merged[pid] = merged.get(pid, 0) + qty  # merge duplicate lines
        return merged

    def _with_items(self, order):
        order["items"] = self.orders.get_items(order["order_id"])
        return order

    # ---- use cases -----------------------------------------------------
    def place_order(self, payload):
        """Create an order atomically: reserve stock for every line or nothing."""
        payload = require_json(payload)
        customer_id = clean_int(payload, "customer_id", minimum=1)
        lines = self._parse_items(payload)
        if not self.customers.get(customer_id):
            raise ValidationError(f"Customer {customer_id} does not exist")

        with transaction(self.db):
            order = self.orders.create({"customer_id": customer_id})
            total = 0.0
            for product_id, qty in lines.items():
                product = self.products.get(product_id)
                if not product:
                    raise ValidationError(f"Product {product_id} does not exist")
                if not self.products.decrement_stock(product_id, qty):
                    raise ConflictError(
                        f"Insufficient stock for '{product['name']}' "
                        f"(requested {qty}, available {product['stock']})"
                    )
                self.orders.add_item(order["order_id"], product_id, qty, product["price"])
                total += product["price"] * qty
            order = self.orders.update(order["order_id"], {"total_amount": round(total, 2)})
        return self._with_items(order)

    def get(self, order_id):
        order = self.orders.get(order_id)
        if not order:
            raise NotFoundError(f"Order {order_id} not found")
        return self._with_items(order)

    def search(self, customer_id, status, limit, offset):
        if status and status not in TRANSITIONS:
            raise ValidationError(f"'status' must be one of {sorted(TRANSITIONS)}")
        return self.orders.search(customer_id, status, limit, offset)

    def _restock(self, order_id):
        for item in self.orders.get_items(order_id):
            self.products.increment_stock(item["product_id"], item["quantity"])

    def update_status(self, order_id, payload):
        payload = require_json(payload)
        new_status = payload.get("status")
        if new_status not in TRANSITIONS:
            raise ValidationError(f"'status' must be one of {sorted(TRANSITIONS)}")
        order = self.get(order_id)
        if new_status not in TRANSITIONS[order["status"]]:
            raise ConflictError(f"Cannot move order from {order['status']} to {new_status}")
        with transaction(self.db):
            if new_status == "CANCELLED":
                self._restock(order_id)
            self.orders.update(order_id, {"status": new_status})
        return self.get(order_id)

    def delete(self, order_id):
        order = self.get(order_id)
        if order["status"] not in ("PENDING", "CANCELLED"):
            raise ConflictError("Only PENDING or CANCELLED orders can be deleted")
        with transaction(self.db):
            if order["status"] == "PENDING":
                self._restock(order_id)
            self.orders.delete(order_id)  # order_items removed via ON DELETE CASCADE
