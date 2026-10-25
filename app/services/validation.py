import re

from ..errors import ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def require_json(payload):
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    return payload


def clean_str(payload, key, required=True, max_len=255, default=""):
    value = payload.get(key)
    if value is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return default
    if not isinstance(value, str):
        raise ValidationError(f"'{key}' must be a string")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"'{key}' must not be empty")
    if len(value) > max_len:
        raise ValidationError(f"'{key}' must be at most {max_len} characters")
    return value


def clean_int(payload, key, minimum=0, required=True):
    value = payload.get(key)
    if value is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"'{key}' must be an integer")
    if value < minimum:
        raise ValidationError(f"'{key}' must be >= {minimum}")
    return value


def clean_price(payload, key="price", required=True):
    value = payload.get(key)
    if value is None:
        if required:
            raise ValidationError(f"'{key}' is required")
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"'{key}' must be a number")
    if value < 0:
        raise ValidationError(f"'{key}' must be >= 0")
    return round(float(value), 2)


def clean_email(payload, required=True):
    email = clean_str(payload, "email", required=required)
    if email and not EMAIL_RE.match(email):
        raise ValidationError("'email' is not a valid email address")
    return email.lower() if email else email


def pagination(args, default_size, max_size):
    try:
        page = max(int(args.get("page", 1)), 1)
        per_page = int(args.get("per_page", default_size))
    except ValueError:
        raise ValidationError("'page' and 'per_page' must be integers")
    per_page = min(max(per_page, 1), max_size)
    return page, per_page, (page - 1) * per_page
