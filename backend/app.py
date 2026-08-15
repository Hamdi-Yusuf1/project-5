import os
import json
import glob
import shutil
import mimetypes
from datetime import date, timedelta
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from models import db, User, Product, QRCode, Notification, VerificationHistory, AIAnalysis, Report

from routes.auth import auth_bp
from routes.products import products_bp
from routes.verification import verification_bp
from routes.reports import reports_bp
from routes.admin import admin_bp
from routes.ai import ai_bp
from routes.blockchain import blockchain_bp
from routes.notifications import notifications_bp

# Not every OS ships .svg in its default mimetypes registry — register it
# explicitly so the generated product packaging artwork always serves with
# the correct content type.
mimetypes.add_type("image/svg+xml", ".svg")

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


def create_app():
    app = Flask(__name__, static_folder=None)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)

    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(products_bp, url_prefix="/api/products")
    app.register_blueprint(verification_bp, url_prefix="/api/verification")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(blockchain_bp, url_prefix="/api/blockchain")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    # --- Serve uploaded files ---
    @app.route("/uploads/<path:subpath>")
    def serve_uploads(subpath):
        return send_from_directory(app.config["UPLOAD_FOLDER"], subpath)

    # --- Serve the frontend (static site) ---
    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:path>")
    def serve_frontend(path):
        full_path = os.path.join(FRONTEND_DIR, path)
        if os.path.exists(full_path):
            return send_from_directory(FRONTEND_DIR, path)
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "An internal server error occurred"}), 500

    @app.route("/api/health")
    def health():
        return jsonify({"success": True, "message": "AuthenChain API is running"}), 200

    return app


def seed_database(app):
    """Populates the database with demo accounts, an 80+ product catalog
    across 20 real skincare brands (with generated packaging art, QR codes
    and blockchain records), and months of simulated verification activity —
    so the platform feels like a live commercial system on first run."""
    with app.app_context():
        db.create_all()

        if User.query.first():
            return  # already seeded

        admin = User(full_name="Hamdi Ahmed", username="Hamdi", email="hamdi@authenchain.com", role="admin")
        admin.set_password("12345")

        # Legacy secondary admin (kept for backward compatibility with earlier demos)
        admin2 = User(full_name="System Administrator", email="admin@authenchain.com", role="admin")
        admin2.set_password("Admin@123")

        # Primary manufacturer/retail-partner account: manages the full
        # multi-brand catalog, representing a retailer/pharmacy-style
        # distribution partner on the platform.
        riyaq = User(full_name="Riyaq Distribution Partners", username="riyaq", email="riyaq@authenchain.com",
                     role="manufacturer", company_name="Riyaq Verified Retail Partners", phone="+254700000001")
        riyaq.set_password("12345")

        manufacturer = User(full_name="Grace Wanjiru", email="manufacturer@authenchain.com", role="manufacturer",
                             company_name="PureGlow Cosmetics Ltd.", phone="+254700111222")
        manufacturer.set_password("Manu@123")

        manufacturer2 = User(full_name="David Otieno", email="manufacturer2@authenchain.com", role="manufacturer",
                              company_name="DermaCare Laboratories", phone="+254700333444")
        manufacturer2.set_password("Manu@123")

        consumer = User(full_name="Amina Hassan", email="consumer@authenchain.com", role="consumer",
                         phone="+254700555666")
        consumer.set_password("User@123")

        user2 = User(full_name="Sarah Kimani", email="sarah@authenchain.com", role="consumer", phone="+254700777888")
        user2.set_password("User@123")

        user3 = User(full_name="James Mwangi", email="james@authenchain.com", role="consumer", phone="+254700999000")
        user3.set_password("User@123")

        db.session.add_all([admin, admin2, riyaq, manufacturer, manufacturer2, consumer, user2, user3])
        db.session.commit()

        from utils.blockchain_service import create_block
        from utils.qr_generator import generate_qr_code
        from utils.image_generator import save_product_image, save_gallery_images
        from utils.seed_data import build_catalog, seed_verification_activity, BRANDS

        sample_products = [
            dict(product_name="Radiant Glow Vitamin C Serum", brand="PureGlow", batch_number="PG-VITC-1001",
                 category="Serum", ingredients="Vitamin C, Hyaluronic Acid, Vitamin E, Ferulic Acid",
                 description="Brightening antioxidant serum for radiant, even-toned skin.",
                 skin_type="All Skin Types", benefits="Brightens skin tone; Boosts collagen production; Fights free radical damage",
                 usage_instructions="Apply 2-3 drops to clean skin before moisturizer. Use morning and evening.",
                 country_of_origin="Kenya", price=24.99,
                 manufacturing_date=date.today() - timedelta(days=120), expiry_date=date.today() + timedelta(days=600),
                 manufacturer=manufacturer),
            dict(product_name="HydraBoost Daily Moisturizer", brand="PureGlow", batch_number="PG-HYD-2002",
                 category="Moisturizer", ingredients="Hyaluronic Acid, Glycerin, Ceramides, Shea Butter",
                 description="24-hour hydration for all skin types with a lightweight, non-greasy finish.",
                 skin_type="Dry Skin", benefits="24-hour hydration; Restores skin barrier; Lightweight non-greasy finish",
                 usage_instructions="Apply to clean skin, massaging until absorbed. Use daily, morning and night.",
                 country_of_origin="Kenya", price=19.99,
                 manufacturing_date=date.today() - timedelta(days=90), expiry_date=date.today() + timedelta(days=700),
                 manufacturer=manufacturer),
            dict(product_name="Gentle Renewal Retinol Cream", brand="DermaCare", batch_number="DC-RET-3003",
                 category="Night Cream", ingredients="Encapsulated Retinol, Niacinamide, Peptides, Squalane",
                 description="Nightly anti-aging cream that smooths fine lines while you sleep.",
                 skin_type="Mature Skin", benefits="Reduces fine lines; Improves skin texture; Supports overnight repair",
                 usage_instructions="Apply a thin layer to clean skin as the last step of your evening routine.",
                 country_of_origin="Kenya", price=32.50,
                 manufacturing_date=date.today() - timedelta(days=60), expiry_date=date.today() + timedelta(days=730),
                 manufacturer=manufacturer2),
            dict(product_name="ClearSkin Salicylic Acid Cleanser", brand="DermaCare", batch_number="DC-CLN-4004",
                 category="Cleanser", ingredients="Salicylic Acid, Tea Tree Oil, Aloe Vera, Zinc PCA",
                 description="Deep-pore cleanser formulated for acne-prone and oily skin.",
                 skin_type="Acne-Prone Skin", benefits="Unclogs pores; Controls excess oil; Calms breakouts",
                 usage_instructions="Massage onto wet skin, then rinse thoroughly. Use morning and night.",
                 country_of_origin="Kenya", price=16.99, status="expired",
                 manufacturing_date=date.today() - timedelta(days=200), expiry_date=date.today() - timedelta(days=5),
                 manufacturer=manufacturer2),
            dict(product_name="Restorative Peptide Eye Cream", brand="PureGlow", batch_number="PG-EYE-5005",
                 category="Eye Care", ingredients="Peptide Complex, Caffeine, Vitamin K, Cucumber Extract",
                 description="Targets puffiness and dark circles for a refreshed, youthful look.",
                 skin_type="All Skin Types", benefits="Reduces puffiness; Brightens dark circles; Firms delicate skin",
                 usage_instructions="Pat gently around the orbital bone using your ring finger, morning and night.",
                 country_of_origin="Kenya", price=27.00,
                 manufacturing_date=date.today() - timedelta(days=30), expiry_date=date.today() + timedelta(days=760),
                 manufacturer=manufacturer),
        ]

        # Full 20-brand catalog managed by the retail partner account
        real_catalog_start_index = len(sample_products)  # everything from here on gets a real photo, not a generated one
        sample_products += build_catalog(manufacturer_id=riyaq.id)

        image_folder = app.config["IMAGE_UPLOAD_FOLDER"]
        os.makedirs(image_folder, exist_ok=True)

        # Real product photos supplied for the 20-brand catalog (80 photos for
        # 80 products). There's no caption/filename data indicating which
        # photo belongs to which specific product, so rather than guess a
        # "smart" match (which would risk mislabeling), they're assigned
        # one-to-one in a stable order across the catalog — every photo gets
        # used, every product gets a real image. A manufacturer can always
        # swap a specific product's photo via Edit Product in the dashboard.
        photos_dir = os.path.join(os.path.dirname(__file__), "seed_assets", "product_photos")
        real_photos = sorted(glob.glob(os.path.join(photos_dir, "*.jpg"))) if os.path.isdir(photos_dir) else []

        for idx, p in enumerate(sample_products):
            mfr = p.pop("manufacturer", None)
            manufacturer_id = mfr.id if mfr else p.pop("manufacturer_id")

            product = Product(manufacturer_id=manufacturer_id, **p)
            db.session.add(product)
            db.session.commit()

            use_real_photo = idx >= real_catalog_start_index and real_photos
            if use_real_photo:
                src_path = real_photos[(idx - real_catalog_start_index) % len(real_photos)]
                ext = os.path.splitext(src_path)[1]
                dest_filename = f"product_{product.id}{ext}"
                shutil.copyfile(src_path, os.path.join(image_folder, dest_filename))
                product.image_path = f"uploads/images/{dest_filename}"
                product.gallery_images = json.dumps([])
            else:
                image_filename = save_product_image(product.product_name, product.brand, product.category,
                                                      image_folder, f"product_{product.id}")
                product.image_path = f"uploads/images/{image_filename}"

                gallery_filenames = save_gallery_images(product.product_name, product.brand, product.category,
                                                           image_folder, f"product_{product.id}_gallery", count=3)
                product.gallery_images = json.dumps([f"uploads/images/{g}" for g in gallery_filenames])
            db.session.commit()

            qr_data, qr_path = generate_qr_code(product.id, product.batch_number)
            db.session.add(QRCode(product_id=product.id, qr_data=qr_data, qr_image_path=qr_path))
            create_block(product.id, manufacturer_id, status="registered")
            db.session.commit()

        # Backfill months of realistic verification activity for dashboards/charts
        seed_verification_activity(db, Product, VerificationHistory, AIAnalysis, User, create_block, count=220)

        # Seed a little report-generation history so the Reports page isn't
        # empty on first login either — new downloads still append live.
        db.session.add_all([
            Report(generated_by=riyaq.id, report_type="products", report_format="csv"),
            Report(generated_by=riyaq.id, report_type="summary", report_format="pdf"),
            Report(generated_by=admin.id, report_type="verifications", report_format="csv"),
        ])

        for u in (admin, admin2, riyaq, manufacturer, manufacturer2, consumer, user2, user3):
            db.session.add(Notification(user_id=u.id, title="Welcome to AuthenChain",
                                         message="Your demo account is ready to explore.", notif_type="success"))
        db.session.commit()

        print("Database seeded with", Product.query.count(), "products across", len(BRANDS) + 2, "brands")
        print("Demo accounts:")
        print("  Admin (username):        Hamdi / 12345")
        print("  Manufacturer (username): riyaq / 12345   <- owns the full 20-brand catalog")
        print("  Admin (email):           admin@authenchain.com / Admin@123")
        print("  Manufacturer (email):    manufacturer@authenchain.com / Manu@123")
        print("  Manufacturer (email):    manufacturer2@authenchain.com / Manu@123")
        print("  User:                    consumer@authenchain.com / User@123")
        print("  User:                    sarah@authenchain.com / User@123")
        print("  User:                    james@authenchain.com / User@123")


app = create_app()
seed_database(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
