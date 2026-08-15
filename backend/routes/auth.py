import re
from flask import Blueprint, request, jsonify
from models import db, User
from utils.jwt_handler import generate_token, token_required
from utils.database import push_notification

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_registration(data, role):
    errors = []
    if not data.get("full_name") or len(data.get("full_name", "").strip()) < 2:
        errors.append("Full name is required")
    email = data.get("email", "").strip().lower()
    if not email or not EMAIL_REGEX.match(email):
        errors.append("A valid email address is required")
    password = data.get("password", "")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters")
    if role == "manufacturer" and not data.get("company_name"):
        errors.append("Company name is required for manufacturer accounts")
    return errors


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    role = data.get("role", "consumer")
    if role not in ("consumer", "manufacturer"):
        return jsonify({"success": False, "message": "Invalid role for self-registration"}), 400

    errors = _validate_registration(data, role)
    if errors:
        return jsonify({"success": False, "message": "; ".join(errors)}), 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "An account with this email already exists"}), 409

    username = (data.get("username") or "").strip() or email.split("@")[0]
    base_username, suffix = username, 1
    while User.query.filter(db.func.lower(User.username) == username.lower()).first():
        suffix += 1
        username = f"{base_username}{suffix}"

    user = User(
        full_name=data["full_name"].strip(),
        username=username,
        email=email,
        role=role,
        phone=data.get("phone", "").strip(),
        company_name=data.get("company_name", "").strip() if role == "manufacturer" else None,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    push_notification(user.id, "Welcome to AuthenChain", "Your account has been created successfully.", "success")

    token = generate_token(user.id, user.role)
    return jsonify({"success": True, "message": "Registration successful", "token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("email") or data.get("username") or "").strip().lower()
    password = data.get("password", "")
    expected_role = data.get("role")

    if not identifier or not password:
        return jsonify({"success": False, "message": "Email/username and password are required"}), 400

    # Accept either an email address or a plain username in the same field
    user = User.query.filter(
        db.or_(User.email == identifier, db.func.lower(User.username) == identifier)
    ).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"success": False, "message": "This account has been deactivated. Contact an administrator."}), 403

    if expected_role and expected_role != user.role:
        return jsonify({"success": False, "message": f"This account is not registered as a {expected_role}"}), 403

    token = generate_token(user.id, user.role)
    return jsonify({"success": True, "message": "Login successful", "token": token, "user": user.to_dict()}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """Simulated password-reset flow: generates a reset token and returns it
    directly in the response (in place of sending a real email), which is
    sufficient for an academic demo environment."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user:
        # Do not reveal whether the account exists
        return jsonify({"success": True, "message": "If that account exists, reset instructions have been generated."}), 200

    reset_token = generate_token(user.id, user.role)
    return jsonify({
        "success": True,
        "message": "Password reset token generated. In production this would be emailed to the user.",
        "reset_token": reset_token,
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("reset_token")
    new_password = data.get("new_password", "")

    from utils.jwt_handler import decode_token
    payload, error = decode_token(token or "")
    if error:
        return jsonify({"success": False, "message": error}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400

    user = User.query.get(payload["user_id"])
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "Password reset successful"}), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user():
    user = User.query.get(request.user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    return jsonify({"success": True, "user": user.to_dict()}), 200


@auth_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile():
    user = User.query.get(request.user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    data = request.form or request.get_json(silent=True) or {}
    if data.get("full_name"):
        user.full_name = data["full_name"].strip()
    if "phone" in data:
        user.phone = data.get("phone", "").strip()
    if "company_name" in data and user.role == "manufacturer":
        user.company_name = data.get("company_name", "").strip()

    file = request.files.get("profile_image") if request.files else None
    if file and file.filename:
        import os, uuid
        from werkzeug.utils import secure_filename
        from flask import current_app
        filename = secure_filename(f"profile_{user.id}_{uuid.uuid4().hex[:8]}_{file.filename}")
        folder = current_app.config["IMAGE_UPLOAD_FOLDER"]
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        user.profile_image = f"uploads/images/{filename}"

    db.session.commit()
    return jsonify({"success": True, "message": "Profile updated successfully", "user": user.to_dict()}), 200


@auth_bp.route("/change-password", methods=["PUT"])
@token_required
def change_password():
    user = User.query.get(request.user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    if not user.check_password(current_password):
        return jsonify({"success": False, "message": "Current password is incorrect"}), 400
    if len(new_password) < 6:
        return jsonify({"success": False, "message": "New password must be at least 6 characters"}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True, "message": "Password changed successfully"}), 200
