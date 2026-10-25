from flask import current_app, jsonify, request

from ..services.validation import pagination


def page_params():
    cfg = current_app.config
    return pagination(request.args, cfg["DEFAULT_PAGE_SIZE"], cfg["MAX_PAGE_SIZE"])


def paged_response(items, total, page, per_page):
    return jsonify({"items": items, "page": page, "per_page": per_page, "total": total})


def json_body():
    return request.get_json(silent=True)


def int_arg(name):
    from ..errors import ValidationError

    raw = request.args.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError(f"'{name}' must be an integer")
