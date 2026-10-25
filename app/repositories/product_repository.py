from .base import BaseRepository


class ProductRepository(BaseRepository):
    table = "products"
    pk = "product_id"
    columns = ("name", "description", "price", "stock", "category_id")

    def search(self, category_id=None, q=None, limit=20, offset=0):
        clauses, params = [], []
        if category_id is not None:
            clauses.append("category_id = ?")
            params.append(category_id)
        if q:
            clauses.append("name LIKE ?")
            params.append(f"%{q}%")
        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        items = self.list(where, params, limit=limit, offset=offset)
        return items, self.count(where, params)

    def decrement_stock(self, product_id, quantity):
        """Atomic conditional update: succeeds only if enough stock remains."""
        cur = self.db.execute(
            "UPDATE products SET stock = stock - ? WHERE product_id = ? AND stock >= ?",
            (quantity, product_id, quantity),
        )
        return cur.rowcount == 1

    def increment_stock(self, product_id, quantity):
        self.db.execute(
            "UPDATE products SET stock = stock + ? WHERE product_id = ?",
            (quantity, product_id),
        )

    def is_referenced_by_orders(self, product_id):
        row = self.db.execute(
            "SELECT 1 FROM order_items WHERE product_id = ? LIMIT 1", (product_id,)
        ).fetchone()
        return row is not None
