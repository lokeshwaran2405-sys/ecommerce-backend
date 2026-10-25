from flask import Blueprint, jsonify

from ..db import get_db
from ..services.customer_service import CustomerService
from .helpers import json_body, page_params, paged_response

bp = Blueprint("customers", __name__, url_prefix="/api/customers")


@bp.post("")
def create_customer():
    return jsonify(CustomerService(get_db()).create(json_body())), 201


@bp.get("")
def list_customers():
    page, per_page, offset = page_params()
    items, total = CustomerService(get_db()).list(per_page, offset)
    return paged_response(items, total, page, per_page)


@bp.get("/<int:customer_id>")
def get_customer(customer_id):
    return jsonify(CustomerService(get_db()).get(customer_id))


@bp.put("/<int:customer_id>")
def update_customer(customer_id):
    return jsonify(CustomerService(get_db()).update(customer_id, json_body()))


@bp.delete("/<int:customer_id>")
def delete_customer(customer_id):
    CustomerService(get_db()).delete(customer_id)
    return "", 204
