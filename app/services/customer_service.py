import sqlite3

from ..errors import ConflictError, NotFoundError
from ..repositories.customer_repository import CustomerRepository
from ..repositories.order_repository import OrderRepository
from .validation import clean_email, clean_str, require_json


class CustomerService:
    def __init__(self, db):
        self.repo = CustomerRepository(db)
        self.orders = OrderRepository(db)

    def _parse(self, payload):
        payload = require_json(payload)
        return {
            "name": clean_str(payload, "name", max_len=120),
            "email": clean_email(payload),
            "phone": clean_str(payload, "phone", required=False, max_len=20),
            "address": clean_str(payload, "address", required=False, max_len=300),
        }

    def create(self, payload):
        data = self._parse(payload)
        try:
            return self.repo.create(data)
        except sqlite3.IntegrityError:
            raise ConflictError(f"Email '{data['email']}' is already registered")

    def get(self, customer_id):
        customer = self.repo.get(customer_id)
        if not customer:
            raise NotFoundError(f"Customer {customer_id} not found")
        return customer

    def list(self, limit, offset):
        return self.repo.list(limit=limit, offset=offset), self.repo.count()

    def update(self, customer_id, payload):
        existing = self.get(customer_id)
        data = self._parse({**existing, **require_json(payload)})
        try:
            return self.repo.update(customer_id, data)
        except sqlite3.IntegrityError:
            raise ConflictError(f"Email '{data['email']}' is already registered")

    def delete(self, customer_id):
        self.get(customer_id)
        if self.orders.customer_has_orders(customer_id):
            raise ConflictError("Customer has orders and cannot be deleted")
        self.repo.delete(customer_id)
