import os
import uuid
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from flask import current_app


def generate_qr_code(product_id, batch_number):
    """Generates a styled QR code encoding a verification URL for the
    product and saves it to the qrcodes upload folder. Returns
    (qr_data, relative_file_path)."""
    qr_data = f"AUTHENCHAIN-{batch_number}-{uuid.uuid4().hex[:8]}"

    verification_payload = f"VERIFY::{qr_data}"

    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_payload)
    qr.make(fit=True)

    try:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
        )
    except Exception:
        img = qr.make_image(fill_color="#1a2b6d", back_color="white")

    filename = f"qr_{product_id}_{uuid.uuid4().hex[:6]}.png"
    folder = current_app.config["QR_UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, filename)
    img.save(filepath)

    relative_path = f"uploads/qrcodes/{filename}"
    return qr_data, relative_path
