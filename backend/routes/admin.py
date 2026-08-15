from datetime import datetime, timedelta
from sqlalchemy import func
from flask import Blueprint, request, jsonify
from models import db, User, Product, VerificationHistory, BlockchainRecord
from utils.jwt_handler import role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/stats", methods=["GET"])
@role_required("admin")
def dashboard_stats():
    total_manufacturers = User.query.filter_by(role="manufacturer").count()
    total_consumers = User.query.filter_by(role="consumer").count()
    total_products = Product.query.count()
    verified_products = VerificationHistory.query.filter_by(result="genuine").count()
    counterfeit_products = VerificationHistory.query.filter_by(result="counterfeit").count()
    verification_requests = VerificationHistory.query.count()

    return jsonify({
        "success": True,
        "stats": {
            "total_manufacturers": total_manufacturers,
            "total_consumers": total_consumers,
            "total_products": total_products,
            "verified_products": verified_products,
            "counterfeit_products": counterfeit_products,
            "verification_requests": verification_requests,
            "total_blocks": BlockchainRecord.query.count(),
        }
    }), 200


@admin_bp.route("/monthly-registrations", methods=["GET"])
@role_required("admin")
def monthly_registrations():
    since = datetime.utcnow() - timedelta(days=365)
    rows = (
        db.session.query(func.strftime("%Y-%m", Product.created_at).label("month"), func.count(Product.id))
        .filter(Product.created_at >= since)
        .group_by("month")
        .order_by("month")
        .all()
    )
    return jsonify({"success": True, "monthly_registrations": [{"month": m, "count": c} for m, c in rows]}), 200


@admin_bp.route("/most-scanned", methods=["GET"])
@role_required("admin")
def most_scanned():
    products = Product.query.order_by(Product.scan_count.desc()).limit(10).all()
    return jsonify({"success": True, "products": [p.to_dict() for p in products]}), 200


@admin_bp.route("/recent-activity", methods=["GET"])
@role_required("admin")
def recent_activity():
    verifications = VerificationHistory.query.order_by(VerificationHistory.created_at.desc()).limit(15).all()
    return jsonify({"success": True, "activity": [v.to_dict() for v in verifications]}), 200


@admin_bp.route("/users", methods=["GET"])
@role_required("admin")
def list_users():
    role = request.args.get("role")
    query = User.query
    if role:
        query = query.filter_by(role=role)
    users = query.order_by(User.created_at.desc()).all()
    return jsonify({"success": True, "users": [u.to_dict() for u in users]}), 200


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["PUT"])
@role_required("admin")
def toggle_user_active(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"success": True, "message": "User status updated", "user": user.to_dict()}), 200


@admin_bp.route("/products", methods=["GET"])
@role_required("admin")
def all_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return jsonify({"success": True, "products": [p.to_dict() for p in products]}), 200
