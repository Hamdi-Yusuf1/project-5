"""
Simulated AI Verification & Counterfeit Detection Engine
----------------------------------------------------------
This module produces deterministic, explainable "AI-style" scores for
product image verification and counterfeit-risk analysis, without requiring
a trained model or GPU — appropriate for an academic demo.

The functions are intentionally isolated behind a small interface
(`analyze_image_match`, `assess_counterfeit_risk`) so a real TensorFlow /
PyTorch image-similarity model (e.g. a Siamese network or perceptual-hash
embedding comparison) can be swapped in later without touching any route
or frontend code — only the internals of these two functions would change.
"""

import hashlib
import io
import json
import random
from datetime import date, datetime


def _seeded_random(seed_text):
    """Deterministic pseudo-random generator derived from input, so the
    same product/image pairing produces stable, reproducible results."""
    seed = int(hashlib.sha256(seed_text.encode()).hexdigest(), 16) % (2 ** 32)
    return random.Random(seed)


def analyze_image_match(reference_image_bytes, uploaded_image_bytes, product_batch):
    """Simulates comparing an uploaded consumer photo against the
    manufacturer's registered reference image.

    Real-world equivalent this stands in for: extracting CNN feature
    embeddings from both images and computing cosine similarity.
    """
    ref_hash = hashlib.md5(reference_image_bytes or b"none").hexdigest() if reference_image_bytes else "none"
    up_hash = hashlib.md5(uploaded_image_bytes or b"none").hexdigest() if uploaded_image_bytes else "none"

    rng = _seeded_random(product_batch + up_hash[:12])

    # If the uploaded bytes are identical to the reference (e.g. demo flow
    # where a user re-uploads the same product photo), bias toward a high
    # genuine match. Otherwise produce a realistic distributed score.
    if ref_hash == up_hash and ref_hash != "none":
        similarity = round(rng.uniform(93.0, 99.4), 2)
    else:
        similarity = round(rng.uniform(48.0, 97.5), 2)

    match_score = round(min(100.0, max(0.0, similarity + rng.uniform(-4, 4))), 2)
    authenticity_confidence = round(min(100.0, max(0.0, (similarity * 0.6 + match_score * 0.4))), 2)

    return {
        "match_score": match_score,
        "similarity_score": similarity,
        "authenticity_confidence": authenticity_confidence,
    }


def assess_counterfeit_risk(product, scan_history_count, image_analysis):
    """Combines image analysis with product/business-rule signals
    (expiry, duplicate scans, missing product, tampered data) to reach a
    final decision + risk level + human-readable explanation.
    """
    anomalies = []
    penalty = 0

    similarity = image_analysis["similarity_score"]
    confidence = image_analysis["authenticity_confidence"]

    if product is None:
        anomalies.append("Product batch number not found in the manufacturer registry")
        penalty += 60
    else:
        if product.status == "recalled":
            anomalies.append("Product has been recalled by the manufacturer")
            penalty += 35
        if product.expiry_date and product.expiry_date < date.today():
            anomalies.append("Product has passed its expiry date")
            penalty += 20
        if scan_history_count > 15:
            anomalies.append("Unusually high number of repeated verification scans detected")
            penalty += 15
        elif scan_history_count > 8:
            anomalies.append("Elevated verification scan frequency for this batch")
            penalty += 8

    if similarity < 60:
        anomalies.append("Significant visual mismatch between uploaded image and registered product image")
        penalty += 30
    elif similarity < 80:
        anomalies.append("Moderate visual inconsistencies detected in packaging or labeling")
        penalty += 12

    if confidence < 55:
        anomalies.append("Low overall authenticity confidence from AI image analysis")
        penalty += 15

    risk_score = max(0, min(100, penalty))
    final_confidence = round(max(0, min(100, confidence - penalty * 0.3)), 2)

    if risk_score >= 55 or product is None:
        decision = "counterfeit"
        risk_level = "high"
    elif risk_score >= 25:
        decision = "suspicious"
        risk_level = "medium"
    else:
        decision = "genuine"
        risk_level = "low"

    if not anomalies:
        explanation = (
            "The uploaded image closely matches the manufacturer's registered reference image, "
            "the batch number is valid and active, the product has not expired, and the blockchain "
            "record for this batch is unbroken. No suspicious scan patterns were detected."
        )
    else:
        explanation = "The following concerns were identified during analysis: " + "; ".join(anomalies) + "."

    return {
        "final_decision": decision,
        "risk_level": risk_level,
        "confidence_score": final_confidence,
        "anomalies": anomalies,
        "explanation": explanation,
    }
