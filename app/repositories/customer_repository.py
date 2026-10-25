from .base import BaseRepository


class CustomerRepository(BaseRepository):
    table = "customers"
    pk = "customer_id"
    columns = ("name", "email", "phone", "address")

    def get_by_email(self, email):
        row = self.db.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None
