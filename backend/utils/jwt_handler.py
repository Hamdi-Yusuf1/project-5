import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app


def generate_token(user_id, role):
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"],
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")


def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"


def get_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({"success": False, "message": "Authentication token is missing"}), 401
        payload, error = decode_token(token)
        if error:
            return jsonify({"success": False, "message": error}), 401
        request.user_id = payload["user_id"]
        request.user_role = payload["role"]
        return f(*args, **kwargs)
    return decorated


def optional_token(f):
    """Like token_required, but doesn't fail if no token is present — sets
    request.user_id / request.user_role to None so public catalog pages work
    for logged-out visitors while still personalizing for logged-in users."""
    @wraps(f)
    def decorated(*args, **kwargs):
        request.user_id = None
        request.user_role = None
        token = get_token_from_header()
        if token:
            payload, error = decode_token(token)
            if not error:
                request.user_id = payload["user_id"]
                request.user_role = payload["role"]
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_header()
            if not token:
                return jsonify({"success": False, "message": "Authentication token is missing"}), 401
            payload, error = decode_token(token)
            if error:
                return jsonify({"success": False, "message": error}), 401
            if payload["role"] not in roles:
                return jsonify({"success": False, "message": "You do not have permission to perform this action"}), 403
            request.user_id = payload["user_id"]
            request.user_role = payload["role"]
            return f(*args, **kwargs)
        return decorated
    return wrapper
