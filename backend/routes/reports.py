import csv
import io
import os
import uuid
from flask import Blueprint, request, jsonify, send_file, current_app
from models import db, Product, VerificationHistory, Report
from utils.jwt_handler import token_required

reports_bp = Blueprint("reports", __name__)


def _scoped_products():
    query = Product.query
    if request.user_role == "manufacturer":
        query = query.filter_by(manufacturer_id=request.user_id)
    return query.all()


@reports_bp.route("/products/csv", methods=["GET"])
@token_required
def export_products_csv():
    products = _scoped_products()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Product Name", "Brand", "Batch Number", "Category", "Status", "Scan Count", "Manufacturing Date", "Expiry Date", "Created At"])
    for p in products:
        writer.writerow([p.id, p.product_name, p.brand, p.batch_number, p.category, p.status, p.scan_count,
                          p.manufacturing_date, p.expiry_date, p.created_at])

    report = Report(generated_by=request.user_id, report_type="products", report_format="csv")
    db.session.add(report)
    db.session.commit()

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="products_report.csv")


@reports_bp.route("/verifications/csv", methods=["GET"])
@token_required
def export_verifications_csv():
    query = VerificationHistory.query
    if request.user_role == "manufacturer":
        product_ids = [p.id for p in _scoped_products()]
        query = query.filter(VerificationHistory.product_id.in_(product_ids))
    records = query.order_by(VerificationHistory.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Product", "Scan Method", "Result", "Risk Level", "Confidence", "Date"])
    for r in records:
        writer.writerow([r.id, r.product.product_name if r.product else "Unknown", r.scan_method, r.result,
                          r.risk_level, r.confidence_score, r.created_at])

    report = Report(generated_by=request.user_id, report_type="verifications", report_format="csv")
    db.session.add(report)
    db.session.commit()

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="verifications_report.csv")


@reports_bp.route("/summary/pdf", methods=["GET"])
@token_required
def export_summary_pdf():
    """Generates a simple, clean summary PDF using reportlab-free pure
    text-to-PDF rendering (fpdf) so no heavyweight PDF engine is required."""
    from fpdf import FPDF

    products = _scoped_products()
    verifications_query = VerificationHistory.query
    if request.user_role == "manufacturer":
        product_ids = [p.id for p in products]
        verifications_query = verifications_query.filter(VerificationHistory.product_id.in_(product_ids))
    verifications = verifications_query.all()

    genuine = len([v for v in verifications if v.result == "genuine"])
    suspicious = len([v for v in verifications if v.result == "suspicious"])
    counterfeit = len([v for v in verifications if v.result == "counterfeit"])

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 43, 109)
    pdf.cell(0, 12, "AuthenChain Verification Summary Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, f"Generated for: {request.user_role.title()} account", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Overview", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Total Products: {len(products)}", ln=True)
    pdf.cell(0, 8, f"Total Verifications: {len(verifications)}", ln=True)
    pdf.cell(0, 8, f"Genuine: {genuine}   Suspicious: {suspicious}   Counterfeit: {counterfeit}", ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Product List", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for p in products[:40]:
        pdf.cell(0, 7, f"- {p.product_name} | Batch: {p.batch_number} | Status: {p.status} | Scans: {p.scan_count}", ln=True)

    report = Report(generated_by=request.user_id, report_type="summary", report_format="pdf")
    db.session.add(report)
    db.session.commit()

    out_bytes = bytes(pdf.output(dest="S"))
    mem = io.BytesIO(out_bytes)
    return send_file(mem, mimetype="application/pdf", as_attachment=True, download_name="summary_report.pdf")


@reports_bp.route("/product/<int:product_id>/pdf", methods=["GET"])
@token_required
def export_single_product_pdf(product_id):
    """Generates a one-page PDF report for a single specific product — lets
    a manufacturer or admin print/download a report for just the one item
    they're looking at, instead of only the full bulk export."""
    from fpdf import FPDF

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found"}), 404
    if request.user_role == "manufacturer" and product.manufacturer_id != request.user_id:
        return jsonify({"success": False, "message": "You can only generate reports for your own products"}), 403

    verifications = VerificationHistory.query.filter_by(product_id=product_id).order_by(VerificationHistory.created_at.desc()).all()
    genuine = len([v for v in verifications if v.result == "genuine"])
    suspicious = len([v for v in verifications if v.result == "suspicious"])
    counterfeit = len([v for v in verifications if v.result == "counterfeit"])

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 43, 109)
    pdf.cell(0, 12, "AuthenChain Product Report", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, f"Generated: {product.updated_at.strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, product.product_name, ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Brand: {product.brand}", ln=True)
    pdf.cell(0, 7, f"Batch Number: {product.batch_number}", ln=True)
    pdf.cell(0, 7, f"Category: {product.category}   |   Status: {product.status}", ln=True)
    pdf.cell(0, 7, f"Manufacturing Date: {product.manufacturing_date}   Expiry Date: {product.expiry_date}", ln=True)
    pdf.cell(0, 7, f"Country of Origin: {product.country_of_origin or 'N/A'}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Verification Summary", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Total Scans: {product.scan_count}", ln=True)
    pdf.cell(0, 8, f"Genuine: {genuine}   Suspicious: {suspicious}   Counterfeit: {counterfeit}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Recent Verification History", ln=True)
    pdf.set_font("Helvetica", "", 10)
    for v in verifications[:25]:
        pdf.cell(0, 7, f"- {v.created_at.strftime('%Y-%m-%d')} | {v.scan_method} | {v.result} | risk: {v.risk_level}", ln=True)
    if not verifications:
        pdf.cell(0, 7, "No verification scans recorded yet for this product.", ln=True)

    report = Report(generated_by=request.user_id, report_type=f"product:{product.batch_number}", report_format="pdf")
    db.session.add(report)
    db.session.commit()

    out_bytes = bytes(pdf.output(dest="S"))
    mem = io.BytesIO(out_bytes)
    safe_name = "".join(c for c in product.product_name if c.isalnum() or c in " -_").strip().replace(" ", "_")
    return send_file(mem, mimetype="application/pdf", as_attachment=True, download_name=f"{safe_name}_report.pdf")


@reports_bp.route("", methods=["GET"])
@token_required
def list_reports():
    reports = Report.query.filter_by(generated_by=request.user_id).order_by(Report.created_at.desc()).all()
    return jsonify({"success": True, "reports": [r.to_dict() for r in reports]}), 200
