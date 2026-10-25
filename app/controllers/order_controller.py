from flask import Blueprint, jsonify, request

from ..db import get_db
from ..services.order_service import OrderService
from .helpers import int_arg, json_body, page_params, paged_response

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@bp.post("")
def place_order():
    return jsonify(OrderService(get_db()).place_order(json_body())), 201


@bp.get("")
def list_orders():
    page, per_page, offset = page_params()
    items, total = OrderService(get_db()).search(
        int_arg("customer_id"), request.args.get("status"), per_page, offset
    )
    return paged_response(items, total, page, per_page)


@bp.get("/<int:order_id>")
def get_order(order_id):
    return jsonify(OrderService(get_db()).get(order_id))


@bp.patch("/<int:order_id>/status")
def update_order_status(order_id):
    return jsonify(OrderService(get_db()).update_status(order_id, json_body()))


@bp.delete("/<int:order_id>")
def delete_order(order_id):
    OrderService(get_db()).delete(order_id)
    return "", 204
