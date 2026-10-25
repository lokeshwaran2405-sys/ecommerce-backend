import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "ecommerce.db"))
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
