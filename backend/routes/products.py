import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, Product, User, QRCode, Favorite
from utils.jwt_handler import token_required, role_required, optional_token
from utils.qr_generator import generate_qr_code
from utils.blockchain_service import create_block
from utils.database import push_notification
from utils.image_generator import save_product_image

products_bp = Blueprint("products", __name__)

EXTRA_FIELDS = ["skin_type", "benefits", "usage_instructions", "warnings", "country_of_origin"]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


@products_bp.route("", methods=["POST"])
@role_required("manufacturer")
def create_product():
    data = request.form or request.get_json(silent=True) or {}

    required = ["product_name", "brand", "batch_number"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "message": f"Missing required fields: {', '.join(missing)}"}), 400

    if Product.query.filter_by(batch_number=data["batch_number"]).first():
        return jsonify({"success": False, "message": "A product with this batch number already exists"}), 409

    image_path = None
    file = request.files.get("image") if request.files else None
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4().hex[:10]}_{file.filename}")
        folder = current_app.config["IMAGE_UPLOAD_FOLDER"]
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        image_path = f"uploads/images/{filename}"

    product = Product(
        manufacturer_id=request.user_id,
        product_name=data["product_name"],
        brand=data["brand"],
        batch_number=data["batch_number"],
        category=data.get("category", "Skincare"),
        ingredients=data.get("ingredients", ""),
        description=data.get("description", ""),
        manufacturing_date=parse_date(data.get("manufacturing_date")),
        expiry_date=parse_date(data.get("expiry_date")),
        image_path=image_path,
        price=float(data.get("price") or 0),
        **{f: data.get(f, "") for f in EXTRA_FIELDS},
    )
    db.session.add(product)
    db.session.commit()

    if not product.image_path:
        # No photo uploaded — generate clean placeholder packaging art so the
        # product never shows a broken image anywhere in the catalog.
        filename = save_product_image(product.product_name, product.brand, product.category,
                                       current_app.config["IMAGE_UPLOAD_FOLDER"], f"product_{product.id}")
        product.image_path = f"uploads/images/{filename}"
        db.session.commit()

    qr_data, qr_path = generate_qr_code(product.id, product.batch_number)
    qr = QRCode(product_id=product.id, qr_data=qr_data, qr_image_path=qr_path)
    db.session.add(qr)

    create_block(product.id, request.user_id, status="registered")

    db.session.commit()

    push_notification(request.user_id, "Product Registered",
                       f"'{product.product_name}' was registered and a QR code was generated.", "success")

    return jsonify({"success": True, "message": "Product registered successfully", "product": product.to_dict()}), 201


@products_bp.route("", methods=["GET"])
@optional_token
def list_products():
    """Public product catalog with search + filters. Works for logged-out
    visitors (browsing) and personalizes results (favorites, 'my products')
    when a valid token is supplied."""
    query = Product.query

    if request.args.get("mine") == "true" and request.user_role == "manufacturer":
        query = query.filter_by(manufacturer_id=request.user_id)

    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(
            Product.product_name.ilike(like),
            Product.brand.ilike(like),
            Product.batch_number.ilike(like),
            Product.ingredients.ilike(like),
            Product.skin_type.ilike(like),
            Product.category.ilike(like),
        ))

    brand = request.args.get("brand")
    if brand:
        query = query.filter(Product.brand.ilike(brand))

    category = request.args.get("category")
    if category:
        query = query.filter(Product.category.ilike(category))

    skin_type = request.args.get("skin_type")
    if skin_type:
        query = query.filter(Product.skin_type.ilike(f"%{skin_type}%"))

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    sort = request.args.get("sort", "newest")
    if sort == "newest":
        query = query.order_by(Product.created_at.desc())
    elif sort == "most_scanned":
        query = query.order_by(Product.scan_count.desc())
    elif sort == "name_asc":
        query = query.order_by(Product.product_name.asc())

    limit = request.args.get("limit", type=int)
    products = query.all()
    if limit:
        products = products[:limit]

    return jsonify({
        "success": True,
        "products": [p.to_dict(current_user_id=request.user_id) for p in products],
        "count": len(products),
    }), 200


@products_bp.route("/meta/filters", methods=["GET"])
def product_filters():
    """Returns distinct brands & categories for the search page's filter dropdowns."""
    brands = [b[0] for b in db.session.query(Product.brand).distinct().order_by(Product.brand).all() if b[0]]
    categories = [c[0] for c in db.session.query(Product.category).distinct().order_by(Product.category).all() if c[0]]
    return jsonify({"success": True, "brands": brands, "categories": categories}), 200


@products_bp.route("/favorites/mine", methods=["GET"])
@token_required
def my_favorites():
    favs = Favorite.query.filter_by(user_id=request.user_id).order_by(Favorite.created_at.desc()).all()
    products = [f.product.to_dict(current_user_id=request.user_id) for f in favs if f.product]
    return jsonify({"success": True, "products": products, "count": len(products)}), 200


@products_bp.route("/<int:product_id>/favorite", methods=["POST"])
@token_required
def toggle_favorite(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404

    existing = Favorite.query.filter_by(user_id=request.user_id, product_id=product_id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"success": True, "favorited": False, "message": "Removed from favorites"}), 200

    db.session.add(Favorite(user_id=request.user_id, product_id=product_id))
    db.session.commit()
    return jsonify({"success": True, "favorited": True, "message": "Added to favorites"}), 200


@products_bp.route("/<int:product_id>", methods=["GET"])
@optional_token
def get_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
    return jsonify({"success": True, "product": product.to_dict(current_user_id=request.user_id)}), 200


@products_bp.route("/<int:product_id>/related", methods=["GET"])
def related_products(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404

    related = Product.query.filter(
        Product.id != product_id,
        db.or_(Product.category == product.category, Product.brand == product.brand),
    ).order_by(Product.scan_count.desc()).limit(4).all()

    return jsonify({"success": True, "products": [p.to_dict() for p in related]}), 200


@products_bp.route("/<int:product_id>", methods=["PUT"])
@role_required("manufacturer", "admin")
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
    if request.user_role != "admin" and product.manufacturer_id != request.user_id:
        return jsonify({"success": False, "message": "You can only edit your own products"}), 403

    data = request.form or request.get_json(silent=True) or {}

    for field in ["product_name", "brand", "category", "ingredients", "description", "status"] + EXTRA_FIELDS:
        if field in data and data[field] not in (None, ""):
            setattr(product, field, data[field])

    if "price" in data:
        try:
            product.price = float(data.get("price") or 0)
        except ValueError:
            pass

    if "manufacturing_date" in data:
        product.manufacturing_date = parse_date(data.get("manufacturing_date"))
    if "expiry_date" in data:
        product.expiry_date = parse_date(data.get("expiry_date"))

    file = request.files.get("image") if request.files else None
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4().hex[:10]}_{file.filename}")
        folder = current_app.config["IMAGE_UPLOAD_FOLDER"]
        os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))
        product.image_path = f"uploads/images/{filename}"

    create_block(product.id, product.manufacturer_id, status="updated")
    db.session.commit()

    return jsonify({"success": True, "message": "Product updated successfully", "product": product.to_dict()}), 200


@products_bp.route("/<int:product_id>", methods=["DELETE"])
@role_required("manufacturer", "admin")
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
    if request.user_role != "admin" and product.manufacturer_id != request.user_id:
        return jsonify({"success": False, "message": "You can only delete your own products"}), 403

    db.session.delete(product)
    db.session.commit()
    return jsonify({"success": True, "message": "Product deleted successfully"}), 200


@products_bp.route("/<int:product_id>/stats", methods=["GET"])
@token_required
def product_stats(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404

    from models import VerificationHistory
    verifications = VerificationHistory.query.filter_by(product_id=product_id).all()
    genuine = len([v for v in verifications if v.result == "genuine"])
    suspicious = len([v for v in verifications if v.result == "suspicious"])
    counterfeit = len([v for v in verifications if v.result == "counterfeit"])

    return jsonify({
        "success": True,
        "stats": {
            "total_scans": product.scan_count,
            "total_verifications": len(verifications),
            "genuine": genuine,
            "suspicious": suspicious,
            "counterfeit": counterfeit,
        }
    }), 200
