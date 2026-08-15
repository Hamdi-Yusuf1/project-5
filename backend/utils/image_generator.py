"""
Generates clean, premium-looking placeholder product packaging artwork as SVG.

We do not have network access to download real product photography, and even
if we did, reproducing real brand packaging photos would raise copyright
concerns. Instead this module procedurally generates attractive, brand-
consistent "packaging" artwork (bottle/jar/tube silhouette + brand wordmark +
category icon) so the catalog looks populated and visually varied without
using anyone else's imagery. Manufacturers can always replace these with real
photos by re-uploading through the dashboard.
"""

import hashlib
import os

# A curated palette per brand so every product from the same brand shares a
# consistent "packaging" color family, like a real product line would.
BRAND_PALETTES = {
    "CeraVe":            ("#1F6FEB", "#0B3D91"),
    "Cetaphil":          ("#2E86AB", "#134B70"),
    "La Roche-Posay":    ("#0072CE", "#003B73"),
    "The Ordinary":      ("#3A3A3A", "#101010"),
    "Neutrogena":        ("#F4A300", "#B97400"),
    "Eucerin":           ("#2E8B57", "#145A32"),
    "Bioderma":          ("#00A19A", "#00615C"),
    "Aveeno":            ("#6FBE44", "#3D7A1E"),
    "COSRX":             ("#8E44AD", "#4A235A"),
    "Simple":            ("#7FB9E0", "#3E7CA6"),
    "Garnier":           ("#3CB043", "#1E6B24"),
    "Nivea":             ("#0A3D91", "#04205A"),
    "Vaseline":          ("#5B8DEF", "#2E4E9E"),
    "Dove":              ("#8FB8DE", "#4E7BB0"),
    "Olay":              ("#C08A2E", "#7C561C"),
    "Beauty of Joseon":  ("#C9A15A", "#8A6A2F"),
    "Innisfree":         ("#4E9B4E", "#2C5E2C"),
    "Paula's Choice":    ("#E85D75", "#A13A50"),
    "Vichy":             ("#00879E", "#005566"),
    "Clinique":          ("#5FBF60", "#2F802F"),
}

CATEGORY_SHAPES = {
    "Cleanser": "tube",
    "Moisturizer": "jar",
    "Serum": "dropper",
    "Sunscreen": "tube",
    "Night Cream": "jar",
    "Eye Care": "tube",
    "Toner": "bottle",
    "Exfoliant": "bottle",
    "Face Oil": "dropper",
    "Body Lotion": "pump",
    "Lip Care": "stick",
    "Mask": "jar",
    "Micellar Water": "pump",
}

CATEGORY_ICON_PATHS = {
    "tube": "M -14,-4 h28 a4,4 0 0 1 4,4 v34 a10,10 0 0 1 -10,10 h-16 a10,10 0 0 1 -10,-10 v-34 a4,4 0 0 1 4,-4 z",
    "jar": "M -18,-2 h36 v10 a26,20 0 0 1 -36,0 z",
    "dropper": "M -8,-30 h16 v14 l6,8 v34 a6,6 0 0 1 -6,6 h-16 a6,6 0 0 1 -6,-6 v-34 l6,-8 z",
    "bottle": "M -9,-32 h18 v12 l7,10 v40 a6,6 0 0 1 -6,6 h-20 a6,6 0 0 1 -6,-6 v-40 l7,-10 z",
    "pump": "M -10,-34 h6 v10 h8 v-10 h6 v14 h4 v46 a6,6 0 0 1 -6,6 h-16 a6,6 0 0 1 -6,-6 v-46 h4 z",
    "stick": "M -6,-30 h12 v50 a6,10 0 0 1 -12,0 z",
}


def _hash_int(text, mod):
    h = hashlib.sha256(text.encode()).hexdigest()
    return int(h[:8], 16) % mod


def _wrap_text(text, max_chars=16):
    words = text.split()
    lines, current = [], ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = f"{current} {w}".strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines[:3]


def generate_product_svg(product_name, brand, category, width=500, height=500):
    color1, color2 = BRAND_PALETTES.get(brand, ("#2952E3", "#0B3D91"))
    shape_key = CATEGORY_SHAPES.get(category, "bottle")
    icon_path = CATEGORY_ICON_PATHS.get(shape_key, CATEGORY_SHAPES.get("bottle"))

    angle = _hash_int(product_name, 4) * 45
    seed = _hash_int(brand + product_name, 1000)
    gid = f"g{seed}"
    name_lines = _wrap_text(product_name, 18)

    name_tspans = "".join(
        f'<tspan x="0" dy="{"0" if i == 0 else "24"}">{line}</tspan>' for i, line in enumerate(name_lines)
    )

    svg = f'''<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="{gid}bg" x1="0%" y1="0%" x2="100%" y2="100%" gradientTransform="rotate({angle})">
      <stop offset="0%" stop-color="{color1}" stop-opacity="0.16"/>
      <stop offset="100%" stop-color="{color2}" stop-opacity="0.05"/>
    </linearGradient>
    <linearGradient id="{gid}pack" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{color1}"/>
      <stop offset="100%" stop-color="{color2}"/>
    </linearGradient>
    <filter id="{gid}shadow" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="{color2}" flood-opacity="0.25"/>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" fill="#FFFFFF"/>
  <rect width="{width}" height="{height}" fill="url(#{gid}bg)"/>
  <circle cx="{width*0.5}" cy="{height*0.42}" r="150" fill="{color1}" opacity="0.06"/>

  <g transform="translate({width/2},{height*0.46})" filter="url(#{gid}shadow)">
    <path d="{icon_path}" fill="url(#{gid}pack)" transform="scale(3.6)"/>
    <path d="{icon_path}" fill="#FFFFFF" opacity="0.14" transform="scale(3.6) translate(0,-2)"/>
    <rect x="-46" y="-8" width="92" height="34" rx="4" fill="#FFFFFF" opacity="0.92"/>
    <text x="0" y="12" text-anchor="middle" font-family="Sora, Arial, sans-serif" font-size="13" font-weight="700" fill="{color2}">{brand.upper()}</text>
  </g>

  <text x="{width/2}" y="{height*0.78}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="20" font-weight="700" fill="#1A2238">{name_tspans}</text>
  <text x="{width/2}" y="{height*0.90}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" fill="#7C86A3">{category}</text>
</svg>'''
    return svg


def save_product_image(product_name, brand, category, folder, filename_prefix):
    os.makedirs(folder, exist_ok=True)
    filename = f"{filename_prefix}.svg"
    with open(os.path.join(folder, filename), "w") as f:
        f.write(generate_product_svg(product_name, brand, category))
    return filename


def save_gallery_images(product_name, brand, category, folder, filename_prefix, count=3):
    """Generates a small gallery of slightly varied angle/label shots."""
    paths = []
    for i in range(count):
        filename = f"{filename_prefix}_{i}.svg"
        svg = generate_product_svg(f"{product_name} #{i}", brand, category)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, filename), "w") as f:
            f.write(svg)
        paths.append(filename)
    return paths
