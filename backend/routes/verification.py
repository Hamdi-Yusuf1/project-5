import os
import uuid
import base64
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, Product, QRCode, VerificationHistory, AIAnalysis
from utils.jwt_handler import token_required
from utils.ai_detector import analyze_image_match, assess_counterfeit_risk
from utils.blockchain_service import create_block, get_product_chain
from utils.database import push_notification

verification_bp = Blueprint("verification", __name__)


def _get_optional_user_id():
    """Verification can happen anonymously (public verify page) or while
    logged in as a consumer; either way we attach a user id if available."""
    from utils.jwt_handler import get_token_from_header, decode_token
    token = get_token_from_header()
    if not token:
        return None
    payload, error = decode_token(token)
    if error:
        return None
    return payload.get("user_id")


def _save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None, None
    filename = secure_filename(f"scan_{uuid.uuid4().hex[:10]}_{file_storage.filename}")
    folder = current_app.config["IMAGE_UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file_storage.save(path)
    with open(path, "rb") as f:
        data = f.read()
    return f"uploads/images/{filename}", data


def _save_base64_image(b64_string):
    if not b64_string:
        return None, None
    try:
        header, encoded = b64_string.split(",", 1) if "," in b64_string else ("", b64_string)
        raw = base64.b64decode(encoded)
    except Exception:
        return None, None
    filename = f"scan_{uuid.uuid4().hex[:10]}.png"
    folder = current_app.config["IMAGE_UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(raw)
    return f"uploads/images/{filename}", raw


def _run_verification(product, uploaded_image_bytes, scan_method, consumer_id):
    reference_bytes = None
    if product and product.image_path:
        ref_full_path = os.path.join(current_app.root_path, product.image_path)
        if os.path.exists(ref_full_path):
            with open(ref_full_path, "rb") as f:
                reference_bytes = f.read()

    batch = product.batch_number if product else "UNKNOWN"
    image_analysis = analyze_image_match(reference_bytes, uploaded_image_bytes, batch)

    prior_scans = VerificationHistory.query.filter_by(product_id=product.id).count() if product else 0
    risk = assess_counterfeit_risk(product, prior_scans, image_analysis)

    verification = VerificationHistory(
        product_id=product.id if product else None,
        consumer_id=consumer_id,
        scan_method=scan_method,
        result=risk["final_decision"],
        risk_level=risk["risk_level"],
        confidence_score=risk["confidence_score"],
        ip_address=request.remote_addr,
    )
    db.session.add(verification)
    db.session.commit()

    ai_record = AIAnalysis(
        verification_id=verification.id,
        match_score=image_analysis["match_score"],
        similarity_score=image_analysis["similarity_score"],
        authenticity_confidence=image_analysis["authenticity_confidence"],
        anomalies_detected=json.dumps(risk["anomalies"]),
        final_decision=risk["final_decision"],
        explanation=risk["explanation"],
    )
    db.session.add(ai_record)

    if product:
        product.scan_count = (product.scan_count or 0) + 1
        create_block(product.id, product.manufacturer_id, status=f"verified:{risk['final_decision']}")

        if risk["final_decision"] == "counterfeit":
            push_notification(product.manufacturer_id, "Counterfeit Alert",
                               f"A verification scan flagged '{product.product_name}' (batch {product.batch_number}) as potentially counterfeit.",
                               "warning")
        push_notification(product.manufacturer_id, "Verification Completed",
                           f"'{product.product_name}' was scanned and verified as {risk['final_decision']}.", "info")

    db.session.commit()

    return {
        "verification": verification.to_dict(),
        "ai_analysis": ai_record.to_dict(),
        "product": product.to_dict() if product else None,
        "blockchain_status": "verified" if product else "not_found",
        "qr_status": "valid" if product else "invalid",
    }


@verification_bp.route("/scan-qr", methods=["POST"])
def scan_qr():
    data = request.get_json(silent=True) or {}
    qr_data = data.get("qr_data", "").strip()
    if qr_data.startswith("VERIFY::"):
        qr_data = qr_data.split("::", 1)[1]

    qr = QRCode.query.filter_by(qr_data=qr_data).first()
    product = qr.product if qr else None

    consumer_id = _get_optional_user_id()
    result = _run_verification(product, None, "qr", consumer_id)
    return jsonify({"success": True, **result}), 200


@verification_bp.route("/scan-image", methods=["POST"])
def scan_image():
    batch_number = request.form.get("batch_number", "").strip()
    product = Product.query.filter_by(batch_number=batch_number).first() if batch_number else None

    file = request.files.get("image")
    image_path, image_bytes = _save_uploaded_image(file)

    consumer_id = _get_optional_user_id()
    result = _run_verification(product, image_bytes, "image", consumer_id)
    result["uploaded_image_path"] = image_path
    return jsonify({"success": True, **result}), 200


@verification_bp.route("/scan-camera", methods=["POST"])
def scan_camera():
    data = request.get_json(silent=True) or {}
    batch_number = data.get("batch_number", "").strip()
    product = Product.query.filter_by(batch_number=batch_number).first() if batch_number else None

    image_path, image_bytes = _save_base64_image(data.get("image_data"))

    consumer_id = _get_optional_user_id()
    result = _run_verification(product, image_bytes, "camera", consumer_id)
    result["uploaded_image_path"] = image_path
    return jsonify({"success": True, **result}), 200


@verification_bp.route("/recent", methods=["GET"])
def recent_public_verifications():
    """Public feed of recently verified-genuine products, used by the
    homepage's 'Latest Verified Products' section. Deliberately excludes
    suspicious/counterfeit results from this public marketing feed."""
    limit = min(request.args.get("limit", 8, type=int), 20)
    records = (VerificationHistory.query
               .filter_by(result="genuine")
               .order_by(VerificationHistory.created_at.desc())
               .limit(limit).all())
    return jsonify({"success": True, "history": [r.to_dict() for r in records]}), 200


@verification_bp.route("/history", methods=["GET"])
@token_required
def verification_history():
    query = VerificationHistory.query
    if request.user_role == "consumer":
        query = query.filter_by(consumer_id=request.user_id)
    elif request.user_role == "manufacturer":
        product_ids = [p.id for p in Product.query.filter_by(manufacturer_id=request.user_id).all()]
        query = query.filter(VerificationHistory.product_id.in_(product_ids))

    records = query.order_by(VerificationHistory.created_at.desc()).limit(200).all()
    return jsonify({"success": True, "history": [r.to_dict() for r in records]}), 200


@verification_bp.route("/product-chain/<int:product_id>", methods=["GET"])
@token_required
def product_chain(product_id):
    blocks = get_product_chain(product_id)
    return jsonify({"success": True, "blocks": [b.to_dict() for b in blocks]}), 200
