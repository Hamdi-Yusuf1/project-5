from flask import Blueprint, request, jsonify
from models import db, Notification
from utils.jwt_handler import token_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("", methods=["GET"])
@token_required
def list_notifications():
    notifs = Notification.query.filter_by(user_id=request.user_id).order_by(Notification.created_at.desc()).limit(50).all()
    unread_count = Notification.query.filter_by(user_id=request.user_id, is_read=False).count()
    return jsonify({"success": True, "notifications": [n.to_dict() for n in notifs], "unread_count": unread_count}), 200


@notifications_bp.route("/<int:notif_id>/read", methods=["PUT"])
@token_required
def mark_read(notif_id):
    notif = Notification.query.get(notif_id)
    if not notif or notif.user_id != request.user_id:
        return jsonify({"success": False, "message": "Notification not found"}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify({"success": True, "message": "Marked as read"}), 200


@notifications_bp.route("/read-all", methods=["PUT"])
@token_required
def mark_all_read():
    Notification.query.filter_by(user_id=request.user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True, "message": "All notifications marked as read"}), 200
