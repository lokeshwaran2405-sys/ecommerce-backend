"""Load a small demo data set:  python scripts/seed.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config  # noqa: E402
from app.db import connect, init_db  # noqa: E402

CATEGORIES = [("Electronics", "Phones, laptops and accessories"),
              ("Books", "Printed and digital books"),
              ("Clothing", "Men's and women's apparel")]
PRODUCTS = [("Smartphone X", "6.5 inch display", 14999.00, 50, "Electronics"),
            ("Laptop Pro 14", "16GB RAM, 512GB SSD", 64999.00, 20, "Electronics"),
            ("Wireless Earbuds", "Noise cancelling", 2999.00, 100, "Electronics"),
            ("Clean Code", "Robert C. Martin", 599.00, 80, "Books"),
            ("Designing Data-Intensive Applications", "Martin Kleppmann", 899.00, 40, "Books"),
            ("Cotton T-Shirt", "100% cotton", 499.00, 200, "Clothing")]
CUSTOMERS = [("Asha Raman", "asha@example.com", "9876543210", "Chennai"),
             ("Ravi Kumar", "ravi@example.com", "9123456780", "Bengaluru")]


def main():
    init_db(Config.DATABASE)
    db = connect(Config.DATABASE)
    for name, desc in CATEGORIES:
        db.execute("INSERT OR IGNORE INTO categories(name, description) VALUES (?, ?)", (name, desc))
    ids = {r["name"]: r["category_id"] for r in db.execute("SELECT * FROM categories")}
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        for name, desc, price, stock, cat in PRODUCTS:
            db.execute("INSERT INTO products(name, description, price, stock, category_id) "
                       "VALUES (?, ?, ?, ?, ?)", (name, desc, price, stock, ids[cat]))
    for c in CUSTOMERS:
        db.execute("INSERT OR IGNORE INTO customers(name, email, phone, address) VALUES (?, ?, ?, ?)", c)
    db.close()
    print("Seeded", Config.DATABASE)


if __name__ == "__main__":
    main()
