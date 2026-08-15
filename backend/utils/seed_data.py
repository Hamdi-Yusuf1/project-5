"""
Generates a realistic, populated skincare product catalog (brands, products,
ingredients, benefits, usage instructions) plus months of simulated
verification activity, so the platform feels like a live commercial system
from the very first run rather than an empty student demo.
"""

import random
from datetime import date, timedelta, datetime

BRANDS = [
    ("CeraVe", "USA"),
    ("Cetaphil", "USA"),
    ("La Roche-Posay", "France"),
    ("The Ordinary", "Canada"),
    ("Neutrogena", "USA"),
    ("Eucerin", "Germany"),
    ("Bioderma", "France"),
    ("Aveeno", "USA"),
    ("COSRX", "South Korea"),
    ("Simple", "United Kingdom"),
    ("Garnier", "France"),
    ("Nivea", "Germany"),
    ("Vaseline", "USA"),
    ("Dove", "USA"),
    ("Olay", "USA"),
    ("Beauty of Joseon", "South Korea"),
    ("Innisfree", "South Korea"),
    ("Paula's Choice", "USA"),
    ("Vichy", "France"),
    ("Clinique", "USA"),
]

CATEGORIES = [
    "Cleanser", "Moisturizer", "Serum", "Sunscreen", "Night Cream",
    "Eye Care", "Toner", "Exfoliant", "Face Oil", "Body Lotion",
    "Lip Care", "Mask", "Micellar Water",
]

SKIN_TYPES = [
    "All Skin Types", "Dry Skin", "Oily Skin", "Combination Skin",
    "Sensitive Skin", "Acne-Prone Skin", "Mature Skin",
]

DESCRIPTORS = {
    "Cleanser": ["Foaming Facial Cleanser", "Gentle Hydrating Cleanser", "Purifying Gel Cleanser", "Creamy Cleansing Wash"],
    "Moisturizer": ["Daily Moisturizing Cream", "Ultra Repair Moisturizer", "Ceramide Moisturizing Lotion", "Ultra-Light Daily Moisturizer"],
    "Serum": ["Hyaluronic Acid Serum", "Vitamin C Brightening Serum", "Niacinamide Serum", "Peptide Renewal Serum"],
    "Sunscreen": ["Mineral SPF 50 Sunscreen", "Anthelios Ultra-Light Sunscreen", "Hydro Boost SPF 30", "Invisible Daily Defense SPF 50"],
    "Night Cream": ["Overnight Repair Cream", "Retinol Renewal Night Cream", "Restorative Night Balm", "Regenerating Night Cream"],
    "Eye Care": ["Advanced Eye Repair Cream", "Brightening Eye Cream", "Hydrating Eye Gel", "Firming Eye Contour Cream"],
    "Toner": ["Balancing Facial Toner", "Soothing Micellar Toner", "Glycolic Acid Toner", "Hydrating Essence Toner"],
    "Exfoliant": ["AHA/BHA Exfoliating Solution", "Gentle Enzyme Exfoliant", "Renewing Peel Pads", "Weekly Resurfacing Scrub"],
    "Face Oil": ["Rosehip Facial Oil", "Nourishing Squalane Oil", "Radiance Face Oil", "Overnight Repair Oil"],
    "Body Lotion": ["Intensive Repair Body Lotion", "Cocoa Butter Body Lotion", "Daily Moisture Body Lotion", "Deep Moisture Body Cream"],
    "Lip Care": ["Repairing Lip Balm", "Hydrating Lip Therapy", "Overnight Lip Mask", "Nourishing Lip Treatment"],
    "Mask": ["Clay Detox Mask", "Hydrating Sheet Mask", "Overnight Recovery Mask", "Brightening Sleep Mask"],
    "Micellar Water": ["Micellar Cleansing Water", "3-in-1 Micellar Solution", "Gentle Micellar Water", "Sensitive Skin Micellar Water"],
}

INGREDIENT_POOL = {
    "Cleanser": ["Ceramides", "Niacinamide", "Glycerin", "Salicylic Acid", "Panthenol", "Hyaluronic Acid"],
    "Moisturizer": ["Ceramides", "Hyaluronic Acid", "Shea Butter", "Glycerin", "Squalane", "Niacinamide"],
    "Serum": ["Hyaluronic Acid", "Vitamin C", "Niacinamide", "Peptide Complex", "Ferulic Acid", "Vitamin E"],
    "Sunscreen": ["Zinc Oxide", "Titanium Dioxide", "Niacinamide", "Vitamin E", "Glycerin", "Antioxidant Complex"],
    "Night Cream": ["Encapsulated Retinol", "Peptides", "Ceramides", "Squalane", "Niacinamide", "Shea Butter"],
    "Eye Care": ["Caffeine", "Peptide Complex", "Vitamin K", "Hyaluronic Acid", "Cucumber Extract", "Ceramides"],
    "Toner": ["Glycolic Acid", "Aloe Vera", "Witch Hazel", "Niacinamide", "Panthenol", "Rose Water"],
    "Exfoliant": ["Glycolic Acid", "Salicylic Acid", "Lactic Acid", "Papaya Enzyme", "Aloe Vera", "Chamomile Extract"],
    "Face Oil": ["Rosehip Oil", "Squalane", "Jojoba Oil", "Vitamin E", "Argan Oil", "Evening Primrose Oil"],
    "Body Lotion": ["Cocoa Butter", "Shea Butter", "Glycerin", "Ceramides", "Vitamin E", "Almond Oil"],
    "Lip Care": ["Shea Butter", "Beeswax", "Vitamin E", "Hyaluronic Acid", "Coconut Oil", "Peptides"],
    "Mask": ["Kaolin Clay", "Hyaluronic Acid", "Niacinamide", "Green Tea Extract", "Charcoal", "Aloe Vera"],
    "Micellar Water": ["Micellar Technology", "Glycerin", "Rose Extract", "Panthenol", "Cucumber Extract", "Aloe Vera"],
}

BENEFIT_POOL = {
    "Cleanser": ["removes dirt and makeup without stripping the skin barrier", "leaves skin feeling clean, soft and never tight", "helps restore and maintain the skin's natural protective barrier"],
    "Moisturizer": ["provides 24-hour hydration", "helps restore the skin's protective barrier", "absorbs quickly with a non-greasy, lightweight finish"],
    "Serum": ["visibly brightens and evens out skin tone", "plumps and hydrates for a dewy, radiant look", "targets fine lines and improves skin texture over time"],
    "Sunscreen": ["provides broad-spectrum UVA/UVB protection", "leaves no white cast on the skin", "lightweight, non-greasy formula suitable for daily wear"],
    "Night Cream": ["works overnight to renew and smooth the skin", "reduces the look of fine lines and wrinkles", "supports the skin's natural repair process while you sleep"],
    "Eye Care": ["reduces the appearance of puffiness and dark circles", "firms and smooths the delicate eye area", "hydrates without feeling heavy under makeup"],
    "Toner": ["balances the skin's pH after cleansing", "preps skin to better absorb serums and moisturizers", "gently removes residual impurities"],
    "Exfoliant": ["gently removes dead skin cells for smoother texture", "helps unclog pores and refine skin tone", "reveals brighter, more radiant-looking skin"],
    "Face Oil": ["deeply nourishes and softens the skin", "locks in moisture for lasting hydration", "adds a healthy, natural glow"],
    "Body Lotion": ["provides long-lasting all-day moisture", "soothes and softens rough, dry skin", "absorbs fast without a greasy after-feel"],
    "Lip Care": ["deeply moisturizes dry, chapped lips", "creates a protective barrier against moisture loss", "leaves lips soft, smooth and comfortable"],
    "Mask": ["deeply cleanses and detoxifies pores", "delivers an intensive boost of hydration", "leaves skin visibly smoother and more radiant"],
    "Micellar Water": ["removes makeup and impurities in one easy step", "cleanses without the need to rinse", "gentle enough for daily use, even on sensitive skin"],
}

USAGE_TEMPLATES = {
    "Cleanser": "Wet face with lukewarm water, massage gently in circular motions, then rinse thoroughly. Use morning and night.",
    "Moisturizer": "Apply a small amount to clean skin, gently massaging until fully absorbed. Use daily, morning and night.",
    "Serum": "Apply 2–3 drops to clean skin before moisturizer. Use morning and/or evening, gently patting into skin.",
    "Sunscreen": "Apply generously as the last step of your morning routine, 15 minutes before sun exposure. Reapply every 2 hours.",
    "Night Cream": "Apply a thin layer to clean skin as the last step of your evening routine. For nighttime use only.",
    "Eye Care": "Using your ring finger, gently pat a small amount around the orbital bone. Use morning and night.",
    "Toner": "Sweep across clean skin using a cotton pad, or pat in gently with hands. Use after cleansing.",
    "Exfoliant": "Apply to clean, dry skin 2–3 times per week. Avoid the eye area. Always follow with sunscreen during the day.",
    "Face Oil": "Warm a few drops between palms and press gently into skin as the last step of your routine.",
    "Body Lotion": "Apply generously to clean, dry skin, massaging until absorbed. Use daily after bathing.",
    "Lip Care": "Apply to lips as needed throughout the day, or generously before bed for overnight repair.",
    "Mask": "Apply an even layer to clean skin, avoiding the eye area. Leave on for 10–15 minutes, then rinse with warm water.",
    "Micellar Water": "Saturate a cotton pad and gently sweep across the face and eyes. No rinsing required.",
}

WARNING_TEXT = "For external use only. Discontinue use if irritation occurs. Keep out of reach of children. Store in a cool, dry place away from direct sunlight."


def _brand_code(brand):
    return "".join(w[0] for w in brand.replace("-", " ").replace("'", "").split())[:4].upper()


def _category_code(category):
    return "".join(w[0] for w in category.split())[:3].upper()


def build_catalog(manufacturer_id, start_index=1):
    """Returns a list of product dicts (not yet persisted) for all brands."""
    products = []
    counter = start_index
    for brand, country in BRANDS:
        # 4 distinct categories per brand, chosen deterministically for variety
        brand_categories = [CATEGORIES[(hash(brand) + i) % len(CATEGORIES)] for i in range(4)]
        seen = set()
        final_categories = []
        for c in brand_categories:
            if c not in seen:
                seen.add(c)
                final_categories.append(c)
        while len(final_categories) < 4:
            for c in CATEGORIES:
                if c not in seen:
                    seen.add(c)
                    final_categories.append(c)
                    break

        for i, category in enumerate(final_categories):
            descriptor = DESCRIPTORS[category][i % len(DESCRIPTORS[category])]
            name = f"{brand} {descriptor}"
            ingredients = ", ".join(INGREDIENT_POOL[category][:4])
            benefits = "; ".join(b.capitalize() for b in BENEFIT_POOL[category][:3])
            skin_type = SKIN_TYPES[(hash(name) + i) % len(SKIN_TYPES)]
            batch_number = f"{_brand_code(brand)}-{_category_code(category)}-{1000 + counter}"

            mfg_days_ago = 20 + (counter * 7) % 300
            shelf_life_days = 540 + (counter * 13) % 400
            is_expired = counter % 23 == 0  # a small realistic sprinkling of expired stock
            mfg_date = date.today() - timedelta(days=mfg_days_ago)
            exp_date = (date.today() - timedelta(days=5)) if is_expired else (mfg_date + timedelta(days=shelf_life_days))

            products.append(dict(
                manufacturer_id=manufacturer_id,
                product_name=name,
                brand=brand,
                batch_number=batch_number,
                category=category,
                ingredients=ingredients,
                description=f"{name} is formulated to work with your skin's natural barrier, using dermatologist-trusted ingredients suited for {skin_type.lower()}.",
                skin_type=skin_type,
                benefits=benefits,
                usage_instructions=USAGE_TEMPLATES[category],
                warnings=WARNING_TEXT,
                country_of_origin=country,
                price=round(6.5 + (counter * 3.7) % 38, 2),
                manufacturing_date=mfg_date,
                expiry_date=exp_date,
                status="expired" if is_expired else "active",
            ))
            counter += 1
    return products


def seed_verification_activity(db, Product, VerificationHistory, AIAnalysis, User, create_block, count=220):
    """Backfills months of realistic verification scans across the catalog so
    dashboards, charts and 'recent activity' feeds look like a live system."""
    products = Product.query.all()
    if not products:
        return

    users = User.query.filter_by(role="consumer").all()
    weights = [max(1, 30 - idx) for idx in range(len(products))]  # earlier/featured products scanned more

    for _ in range(count):
        product = random.choices(products, weights=weights, k=1)[0]
        days_ago = random.randint(0, 150)
        created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        scan_method = random.choices(["qr", "image", "camera"], weights=[60, 30, 10])[0]

        roll = random.random()
        if product.status == "expired" or roll < 0.08:
            result, risk, decision = "counterfeit", "high", "Counterfeit Product"
        elif roll < 0.20:
            result, risk, decision = "suspicious", "medium", "Suspicious Product"
        else:
            result, risk, decision = "genuine", "low", "Genuine Product"

        consumer = random.choice(users) if users and random.random() < 0.7 else None

        verification = VerificationHistory(
            product_id=product.id,
            consumer_id=consumer.id if consumer else None,
            scan_method=scan_method,
            result=result,
            risk_level=risk,
            confidence_score=round(random.uniform(70, 99) if result == "genuine" else random.uniform(35, 75), 1),
            ip_address=f"192.168.{random.randint(0,255)}.{random.randint(1,254)}",
            created_at=created_at,
        )
        db.session.add(verification)
        db.session.flush()

        ai = AIAnalysis(
            verification_id=verification.id,
            match_score=round(random.uniform(85, 99) if result == "genuine" else random.uniform(20, 60), 1),
            similarity_score=round(random.uniform(85, 99) if result == "genuine" else random.uniform(20, 65), 1),
            authenticity_confidence=verification.confidence_score,
            final_decision=decision,
            explanation=f"AI comparison against the registered reference image and blockchain record for batch {product.batch_number} returned a {decision.lower()} outcome.",
        )
        db.session.add(ai)

        product.scan_count = (product.scan_count or 0) + 1

        block = create_block(product.id, product.manufacturer_id, status=f"verified:{decision}")
        block.timestamp = created_at
        db.session.add(block)

    db.session.commit()
