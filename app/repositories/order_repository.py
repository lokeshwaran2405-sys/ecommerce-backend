from .base import BaseRepository


class OrderRepository(BaseRepository):
    table = "orders"
    pk = "order_id"
    columns = ("customer_id", "status", "total_amount")

    def add_item(self, order_id, product_id, quantity, unit_price):
        self.db.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
            "VALUES (?, ?, ?, ?)",
            (order_id, product_id, quantity, unit_price),
        )

    def get_items(self, order_id):
        rows = self.db.execute(
            "SELECT oi.order_item_id, oi.product_id, p.name AS product_name, "
            "oi.quantity, oi.unit_price, ROUND(oi.quantity * oi.unit_price, 2) AS line_total "
            "FROM order_items oi JOIN products p ON p.product_id = oi.product_id "
            "WHERE oi.order_id = ? ORDER BY oi.order_item_id",
            (order_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def search(self, customer_id=None, status=None, limit=20, offset=0):
        clauses, params = [], []
        if customer_id is not None:
            clauses.append("customer_id = ?")
            params.append(customer_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        items = self.list(where, params, order_by="order_id DESC", limit=limit, offset=offset)
        return items, self.count(where, params)

    def customer_has_orders(self, customer_id):
        row = self.db.execute(
            "SELECT 1 FROM orders WHERE customer_id = ? LIMIT 1", (customer_id,)
        ).fetchone()
        return row is not None
