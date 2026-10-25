# E-Commerce Backend (Flask + SQLite)

A compact e-commerce REST API with full CRUD for **categories, products, customers and orders**.
Layered MVC architecture: `controllers → services → repositories → SQLite`.
No front end — test it with `curl`, Postman or the included test-suite.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed.py        # optional demo data
python run.py                 # http://127.0.0.1:5000
python -m unittest discover -s tests -v    # run the 15 tests
python scripts/benchmark.py   # index benchmark (200k products)
```

## Project layout

```
app/
  controllers/    HTTP routes (Flask blueprints), request/response mapping
  services/       business rules, validation, transactions
  repositories/   SQL / data access (generic BaseRepository + per-entity repos)
  schema.sql      table definitions        indexes.sql   performance indexes
  db.py  config.py  errors.py
tests/test_api.py scripts/seed.py scripts/benchmark.py docs/
```

## API

| Resource | Endpoints |
|---|---|
| Health | `GET /health` |
| Categories | `POST/GET /api/categories`, `GET/PUT/DELETE /api/categories/{id}` |
| Products | `POST/GET /api/products` (`?category_id=&q=&page=&per_page=`), `GET/PUT/DELETE /api/products/{id}` |
| Customers | `POST/GET /api/customers`, `GET/PUT/DELETE /api/customers/{id}` |
| Orders | `POST/GET /api/orders` (`?customer_id=&status=`), `GET/DELETE /api/orders/{id}`, `PATCH /api/orders/{id}/status` |

### Example

```bash
curl -X POST localhost:5000/api/orders -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"items":[{"product_id":1,"quantity":2}]}'
```

### Business rules
* Placing an order is **atomic**: stock is reserved for every line or the whole order is rolled back (HTTP 409).
* Stock is decremented with a conditional `UPDATE ... WHERE stock >= qty`, so concurrent buyers can never oversell.
* Order life-cycle: `PENDING → PAID → SHIPPED → DELIVERED`; `PENDING/PAID → CANCELLED` (stock is returned).
* Customers/products that appear in orders cannot be deleted; only `PENDING`/`CANCELLED` orders can be deleted.
* Errors are JSON: `{"error": "..."}` with 400 / 404 / 409 status codes.
