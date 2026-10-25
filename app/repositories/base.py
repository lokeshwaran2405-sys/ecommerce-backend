class BaseRepository:
    """Generic CRUD data access. Subclasses define table, pk and writable columns."""

    table = ""
    pk = ""
    columns = ()

    def __init__(self, db):
        self.db = db

    def get(self, id_):
        row = self.db.execute(
            f"SELECT * FROM {self.table} WHERE {self.pk} = ?", (id_,)
        ).fetchone()
        return dict(row) if row else None

    def create(self, data):
        cols = [c for c in self.columns if c in data]
        placeholders = ", ".join("?" for _ in cols)
        cur = self.db.execute(
            f"INSERT INTO {self.table} ({', '.join(cols)}) VALUES ({placeholders})",
            [data[c] for c in cols],
        )
        return self.get(cur.lastrowid)

    def update(self, id_, data):
        cols = [c for c in self.columns if c in data]
        if cols:
            assignments = ", ".join(f"{c} = ?" for c in cols)
            self.db.execute(
                f"UPDATE {self.table} SET {assignments} WHERE {self.pk} = ?",
                [data[c] for c in cols] + [id_],
            )
        return self.get(id_)

    def delete(self, id_):
        cur = self.db.execute(f"DELETE FROM {self.table} WHERE {self.pk} = ?", (id_,))
        return cur.rowcount > 0

    def list(self, where="", params=(), order_by=None, limit=20, offset=0):
        order = order_by or self.pk
        sql = f"SELECT * FROM {self.table} {where} ORDER BY {order} LIMIT ? OFFSET ?"
        rows = self.db.execute(sql, [*params, limit, offset]).fetchall()
        return [dict(r) for r in rows]

    def count(self, where="", params=()):
        sql = f"SELECT COUNT(*) FROM {self.table} {where}"
        return self.db.execute(sql, params).fetchone()[0]
