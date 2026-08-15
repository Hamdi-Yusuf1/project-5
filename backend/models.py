from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def now():
    return datetime.utcnow()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="consumer")  # manufacturer | consumer | admin
    phone = db.Column(db.String(30))
    company_name = db.Column(db.String(150))
    profile_image = db.Column(db.String(255), default="")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    products = db.relationship("Product", backref="manufacturer", lazy=True, foreign_keys="Product.manufacturer_id")
    notifications = db.relationship("Notification", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "role_label": "User" if self.role == "consumer" else self.role.capitalize(),
            "phone": self.phone,
            "company_name": self.company_name,
            "profile_image": self.profile_image,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    brand = db.Column(db.String(150), nullable=False)
    batch_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), default="Skincare")
    ingredients = db.Column(db.Text)
    description = db.Column(db.Text)
    skin_type = db.Column(db.String(150))
    benefits = db.Column(db.Text)
    usage_instructions = db.Column(db.Text)
    warnings = db.Column(db.Text)
    country_of_origin = db.Column(db.String(100))
    price = db.Column(db.Float, default=0.0)
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    image_path = db.Column(db.String(255))
    gallery_images = db.Column(db.Text)  # JSON-encoded list of extra image paths
    status = db.Column(db.String(20), default="active")  # active | recalled | expired
    scan_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    qrcode = db.relationship("QRCode", backref="product", uselist=False, lazy=True)
    blockchain_records = db.relationship("BlockchainRecord", backref="product", lazy=True)
    verifications = db.relationship("VerificationHistory", backref="product", lazy=True)

    def to_dict(self, current_user_id=None):
        import json
        gallery = []
        if self.gallery_images:
            try:
                gallery = json.loads(self.gallery_images)
            except (ValueError, TypeError):
                gallery = []
        is_favorited = False
        if current_user_id:
            is_favorited = Favorite.query.filter_by(user_id=current_user_id, product_id=self.id).first() is not None
        return {
            "id": self.id,
            "manufacturer_id": self.manufacturer_id,
            "manufacturer_name": self.manufacturer.company_name or self.manufacturer.full_name if self.manufacturer else None,
            "product_name": self.product_name,
            "brand": self.brand,
            "batch_number": self.batch_number,
            "category": self.category,
            "ingredients": self.ingredients,
            "description": self.description,
            "skin_type": self.skin_type,
            "benefits": self.benefits,
            "usage_instructions": self.usage_instructions,
            "warnings": self.warnings,
            "country_of_origin": self.country_of_origin,
            "price": self.price,
            "manufacturing_date": self.manufacturing_date.isoformat() if self.manufacturing_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "image_path": self.image_path,
            "gallery_images": gallery,
            "status": self.status,
            "scan_count": self.scan_count,
            "is_favorited": is_favorited,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "qr_code_path": self.qrcode.qr_image_path if self.qrcode else None,
        }


class QRCode(db.Model):
    __tablename__ = "qrcodes"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False, unique=True)
    qr_data = db.Column(db.String(255), nullable=False, unique=True)
    qr_image_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now)


class BlockchainRecord(db.Model):
    __tablename__ = "blockchain_records"

    id = db.Column(db.Integer, primary_key=True)
    block_index = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    verification_status = db.Column(db.String(30), default="registered")
    data_hash = db.Column(db.String(255), nullable=False)
    previous_hash = db.Column(db.String(255), nullable=False)
    block_hash = db.Column(db.String(255), nullable=False)
    nonce = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "block_index": self.block_index,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else None,
            "manufacturer_id": self.manufacturer_id,
            "verification_status": self.verification_status,
            "data_hash": self.data_hash,
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,
            "nonce": self.nonce,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class VerificationHistory(db.Model):
    __tablename__ = "verification_history"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    consumer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    scan_method = db.Column(db.String(20), default="qr")  # qr | image | camera
    result = db.Column(db.String(20), nullable=False)  # genuine | suspicious | counterfeit
    risk_level = db.Column(db.String(20), default="low")
    confidence_score = db.Column(db.Float, default=0.0)
    ip_address = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=now)

    ai_analysis = db.relationship("AIAnalysis", backref="verification", uselist=False, lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else "Unknown Product",
            "product_brand": self.product.brand if self.product else None,
            "product_image": self.product.image_path if self.product else None,
            "consumer_id": self.consumer_id,
            "scan_method": self.scan_method,
            "result": self.result,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIAnalysis(db.Model):
    __tablename__ = "ai_analysis"

    id = db.Column(db.Integer, primary_key=True)
    verification_id = db.Column(db.Integer, db.ForeignKey("verification_history.id"), nullable=False)
    match_score = db.Column(db.Float, default=0.0)
    similarity_score = db.Column(db.Float, default=0.0)
    authenticity_confidence = db.Column(db.Float, default=0.0)
    anomalies_detected = db.Column(db.Text)  # JSON encoded list
    final_decision = db.Column(db.String(30))
    explanation = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "verification_id": self.verification_id,
            "match_score": self.match_score,
            "similarity_score": self.similarity_score,
            "authenticity_confidence": self.authenticity_confidence,
            "anomalies_detected": self.anomalies_detected,
            "final_decision": self.final_decision,
            "explanation": self.explanation,
        }


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    generated_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    report_type = db.Column(db.String(50), nullable=False)
    report_format = db.Column(db.String(10), default="csv")
    parameters = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "generated_by": self.generated_by,
            "report_type": self.report_type,
            "report_format": self.report_format,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=now)

    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_user_product_favorite"),)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notif_type = db.Column(db.String(30), default="info")  # info | success | warning | danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notif_type": self.notif_type,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
