from flask import Blueprint, jsonify

from ..db import get_db
from ..services.category_service import CategoryService
from .helpers import json_body, page_params, paged_response

bp = Blueprint("categories", __name__, url_prefix="/api/categories")


@bp.post("")
def create_category():
    return jsonify(CategoryService(get_db()).create(json_body())), 201


@bp.get("")
def list_categories():
    page, per_page, offset = page_params()
    items, total = CategoryService(get_db()).list(per_page, offset)
    return paged_response(items, total, page, per_page)


@bp.get("/<int:category_id>")
def get_category(category_id):
    return jsonify(CategoryService(get_db()).get(category_id))


@bp.put("/<int:category_id>")
def update_category(category_id):
    return jsonify(CategoryService(get_db()).update(category_id, json_body()))


@bp.delete("/<int:category_id>")
def delete_category(category_id):
    CategoryService(get_db()).delete(category_id)
    return "", 204
