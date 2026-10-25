from .base import BaseRepository


class CategoryRepository(BaseRepository):
    table = "categories"
    pk = "category_id"
    columns = ("name", "description")

    def get_by_name(self, name):
        row = self.db.execute("SELECT * FROM categories WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None
