import sqlite3

from ..errors import ConflictError, NotFoundError
from ..repositories.category_repository import CategoryRepository
from .validation import clean_str, require_json


class CategoryService:
    def __init__(self, db):
        self.repo = CategoryRepository(db)

    def _parse(self, payload):
        payload = require_json(payload)
        return {
            "name": clean_str(payload, "name", max_len=100),
            "description": clean_str(payload, "description", required=False, max_len=500),
        }

    def create(self, payload):
        data = self._parse(payload)
        try:
            return self.repo.create(data)
        except sqlite3.IntegrityError:
            raise ConflictError(f"Category '{data['name']}' already exists")

    def get(self, category_id):
        category = self.repo.get(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")
        return category

    def list(self, limit, offset):
        return self.repo.list(limit=limit, offset=offset), self.repo.count()

    def update(self, category_id, payload):
        existing = self.get(category_id)
        data = self._parse({**existing, **require_json(payload)})
        try:
            return self.repo.update(category_id, data)
        except sqlite3.IntegrityError:
            raise ConflictError(f"Category '{data['name']}' already exists")

    def delete(self, category_id):
        self.get(category_id)
        self.repo.delete(category_id)  # products.category_id is set to NULL
