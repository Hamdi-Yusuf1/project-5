from flask import Blueprint, jsonify, request
from models import BlockchainRecord
from utils.jwt_handler import token_required
from utils.blockchain_service import verify_chain_integrity

blockchain_bp = Blueprint("blockchain", __name__)


@blockchain_bp.route("", methods=["GET"])
@token_required
def list_blocks():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))
    query = BlockchainRecord.query.order_by(BlockchainRecord.block_index.desc())
    total = query.count()
    blocks = query.offset((page - 1) * per_page).limit(per_page).all()
    return jsonify({
        "success": True,
        "blocks": [b.to_dict() for b in blocks],
        "total": total,
        "page": page,
        "per_page": per_page,
    }), 200


@blockchain_bp.route("/integrity", methods=["GET"])
@token_required
def integrity_check():
    result = verify_chain_integrity()
    return jsonify({"success": True, **result}), 200


@blockchain_bp.route("/<int:block_id>", methods=["GET"])
@token_required
def get_block(block_id):
    block = BlockchainRecord.query.get(block_id)
    if not block:
        return jsonify({"success": False, "message": "Block not found"}), 404
    return jsonify({"success": True, "block": block.to_dict()}), 200
