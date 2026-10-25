from flask import Blueprint, jsonify, request

from ..db import get_db
from ..services.product_service import ProductService
from .helpers import int_arg, json_body, page_params, paged_response

bp = Blueprint("products", __name__, url_prefix="/api/products")


@bp.post("")
def create_product():
    return jsonify(ProductService(get_db()).create(json_body())), 201


@bp.get("")
def list_products():
    page, per_page, offset = page_params()
    items, total = ProductService(get_db()).search(
        int_arg("category_id"), request.args.get("q"), per_page, offset
    )
    return paged_response(items, total, page, per_page)


@bp.get("/<int:product_id>")
def get_product(product_id):
    return jsonify(ProductService(get_db()).get(product_id))


@bp.put("/<int:product_id>")
def update_product(product_id):
    return jsonify(ProductService(get_db()).update(product_id, json_body()))


@bp.delete("/<int:product_id>")
def delete_product(product_id):
    ProductService(get_db()).delete(product_id)
    return "", 204
