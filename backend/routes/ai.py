from flask import Blueprint, jsonify, request
from models import VerificationHistory, AIAnalysis, Product
from utils.jwt_handler import token_required

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/analysis/<int:verification_id>", methods=["GET"])
@token_required
def get_analysis(verification_id):
    verification = VerificationHistory.query.get(verification_id)
    if not verification:
        return jsonify({"success": False, "message": "Verification record not found"}), 404
    analysis = AIAnalysis.query.filter_by(verification_id=verification_id).first()
    return jsonify({
        "success": True,
        "verification": verification.to_dict(),
        "analysis": analysis.to_dict() if analysis else None,
    }), 200


@ai_bp.route("/logs", methods=["GET"])
@token_required
def ai_logs():
    """Recent AI verification analysis logs, scoped by role, for the admin
    dashboard's 'AI Logs' panel."""
    query = AIAnalysis.query.join(VerificationHistory)
    if request.user_role == "manufacturer":
        product_ids = [p.id for p in Product.query.filter_by(manufacturer_id=request.user_id).all()]
        query = query.filter(VerificationHistory.product_id.in_(product_ids))

    limit = min(request.args.get("limit", 50, type=int), 200)
    records = query.order_by(AIAnalysis.created_at.desc()).limit(limit).all()

    logs = []
    for a in records:
        d = a.to_dict()
        d["product_name"] = a.verification.product.product_name if a.verification and a.verification.product else None
        d["scan_method"] = a.verification.scan_method if a.verification else None
        logs.append(d)

    return jsonify({"success": True, "logs": logs, "count": len(logs)}), 200


@ai_bp.route("/risk-summary", methods=["GET"])
@token_required
def risk_summary():
    """Aggregated risk distribution used by the analytics dashboard charts."""
    query = VerificationHistory.query
    if request.user_role == "manufacturer":
        product_ids = [p.id for p in Product.query.filter_by(manufacturer_id=request.user_id).all()]
        query = query.filter(VerificationHistory.product_id.in_(product_ids))

    records = query.all()
    summary = {"low": 0, "medium": 0, "high": 0}
    decisions = {"genuine": 0, "suspicious": 0, "counterfeit": 0}
    for r in records:
        summary[r.risk_level] = summary.get(r.risk_level, 0) + 1
        decisions[r.result] = decisions.get(r.result, 0) + 1

    return jsonify({"success": True, "risk_distribution": summary, "decision_distribution": decisions, "total": len(records)}), 200
