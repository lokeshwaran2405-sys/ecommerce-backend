"""Benchmark the effect of database indexes through the real HTTP layer.

    python scripts/benchmark.py            # 200k products / 100k orders
    python scripts/benchmark.py 50000 20000
"""
import os
import random
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.db import connect, init_db, run_script  # noqa: E402

N_PRODUCTS = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
N_ORDERS = int(sys.argv[2]) if len(sys.argv) > 2 else 100_000
N_CATEGORIES, N_CUSTOMERS, RUNS = 100, 5_000, 30


def build_db(path):
    random.seed(42)
    init_db(path, with_indexes=False)  # start WITHOUT indexes
    db = connect(path)
    db.execute("BEGIN")
    db.executemany("INSERT INTO categories(name) VALUES (?)",
                   [(f"cat-{i}",) for i in range(N_CATEGORIES)])
    db.executemany("INSERT INTO customers(name, email) VALUES (?, ?)",
                   [(f"c{i}", f"c{i}@x.com") for i in range(N_CUSTOMERS)])
    db.executemany("INSERT INTO products(name, price, stock, category_id) VALUES (?, ?, ?, ?)",
                   [(f"product-{i}", round(random.uniform(5, 500), 2), 100,
                     random.randint(1, N_CATEGORIES)) for i in range(N_PRODUCTS)])
    db.executemany("INSERT INTO orders(customer_id, status, total_amount) VALUES (?, 'PAID', 10)",
                   [(random.randint(1, N_CUSTOMERS),) for _ in range(N_ORDERS)])
    db.execute("COMMIT")
    return db


def measure(client, url):
    client.get(url)  # warm-up
    samples = []
    for _ in range(RUNS):
        t = time.perf_counter()
        r = client.get(url)
        samples.append((time.perf_counter() - t) * 1000)
        assert r.status_code == 200
    return statistics.median(samples)


def main():
    path = os.path.join(tempfile.mkdtemp(), "bench.db")
    db = build_db(path)
    app = create_app({"DATABASE": path, "TESTING": True})
    client = app.test_client()
    for idx in ("idx_products_category", "idx_orders_customer", "idx_order_items_order"):
        db.execute(f"DROP INDEX IF EXISTS {idx}")  # create_app() adds them; remove for baseline
    endpoints = {
        "GET /api/products?category_id=42": "/api/products?category_id=42",
        "GET /api/orders?customer_id=1234": "/api/orders?customer_id=1234",
    }
    print(f"Rows: {N_PRODUCTS} products, {N_ORDERS} orders  (median of {RUNS} runs, ms)")
    plan = [tuple(r)[3] for r in db.execute(
        "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM products WHERE category_id = 42")]
    print("Query plan without index:", plan)
    before = {k: measure(client, u) for k, u in endpoints.items()}
    run_script(db, "indexes.sql")
    db.execute("ANALYZE")
    after = {k: measure(client, u) for k, u in endpoints.items()}
    print(f"{'Endpoint':40}{'No index':>12}{'Indexed':>12}{'Speed-up':>12}")
    for k in endpoints:
        print(f"{k:40}{before[k]:>12.2f}{after[k]:>12.2f}{before[k] / after[k]:>11.1f}x")
    print()
    sql = "SELECT COUNT(*) FROM products WHERE category_id = 42"
    print("Query plan with index:", [tuple(r)[3] for r in db.execute("EXPLAIN QUERY PLAN " + sql)])


if __name__ == "__main__":
    main()
