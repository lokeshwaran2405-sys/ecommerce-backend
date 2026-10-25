from ..errors import ConflictError, NotFoundError, ValidationError
from ..repositories.category_repository import CategoryRepository
from ..repositories.product_repository import ProductRepository
from .validation import clean_int, clean_price, clean_str, require_json


class ProductService:
    def __init__(self, db):
        self.repo = ProductRepository(db)
        self.categories = CategoryRepository(db)

    def _parse(self, payload):
        payload = require_json(payload)
        category_id = clean_int(payload, "category_id", minimum=1, required=False)
        if category_id is not None and not self.categories.get(category_id):
            raise ValidationError(f"Category {category_id} does not exist")
        return {
            "name": clean_str(payload, "name", max_len=150),
            "description": clean_str(payload, "description", required=False, max_len=1000),
            "price": clean_price(payload),
            "stock": clean_int(payload, "stock", minimum=0, required=False) or 0,
            "category_id": category_id,
        }

    def create(self, payload):
        return self.repo.create(self._parse(payload))

    def get(self, product_id):
        product = self.repo.get(product_id)
        if not product:
            raise NotFoundError(f"Product {product_id} not found")
        return product

    def search(self, category_id, q, limit, offset):
        return self.repo.search(category_id=category_id, q=q, limit=limit, offset=offset)

    def update(self, product_id, payload):
        existing = self.get(product_id)
        data = self._parse({**existing, **require_json(payload)})
        return self.repo.update(product_id, data)

    def delete(self, product_id):
        self.get(product_id)
        if self.repo.is_referenced_by_orders(product_id):
            raise ConflictError("Product is part of existing orders and cannot be deleted")
        self.repo.delete(product_id)
