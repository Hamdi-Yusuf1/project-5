# AuthenChain — AI & Blockchain-Based Counterfeit Skincare Product Verification System

Final Year Project — BSc Information Technology

AuthenChain lets skincare **manufacturers** register products and generate tamper-evident QR codes, lets **consumers** verify authenticity in seconds via QR scan / photo upload / live camera capture, and gives **admins** a full analytics view of platform activity — all backed by a simulated AI image-verification engine and a simulated hash-linked blockchain ledger.

---

## 1. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, Flask-CORS, Flask-SQLAlchemy, PyJWT |
| Frontend | HTML5, CSS3, Vanilla JavaScript, Bootstrap 5, Chart.js, Font Awesome 6 |
| Database | SQLite (zero-config default) or MySQL (production-style schema included) |
| QR Codes | `qrcode` + Pillow |
| PDF Reports | `fpdf2` |
| "Blockchain" | Custom SHA-256 hash-linked ledger (see `backend/utils/blockchain_service.py`) |
| "AI" | Deterministic simulated image-comparison + rule-based risk engine (see `backend/utils/ai_detector.py`) — built with a clean interface so a real TensorFlow/PyTorch model can be swapped in later |

---

## 2. Quick Start (runs in under a minute)

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
python app.py
```

Then open **http://localhost:5000** in your browser. That's it — the app serves both the API and the frontend from the same Flask process, and a SQLite database (`backend/skincare_verification.db` / `authenchain.db`) is created and auto-seeded with demo data on first run.

### Demo accounts (auto-created on first run)

| Role | Login | Password |
|---|---|---|
| **Admin** | username **`Hamdi`** | `12345` |
| **Manufacturer / Retail Partner** | username **`riyaq`** | `12345` |
| Admin (secondary) | admin@authenchain.com | Admin@123 |
| Manufacturer | manufacturer@authenchain.com | Manu@123 |
| Manufacturer | manufacturer2@authenchain.com | Manu@123 |
| User | consumer@authenchain.com | User@123 |
| User | sarah@authenchain.com | User@123 |
| User | james@authenchain.com | User@123 |

You can log in with either a **username** (`riyaq`, `Hamdi`) or an **email address** — both work in the same login field.

**Why does `riyaq` own 80+ products across 20 brands?** That account represents a retail/distribution partner (like a pharmacy chain or beauty retailer) that manages verification for multiple brands on the platform — a very common real-world model for this kind of system, and it's why a single account can plausibly hold a large multi-brand catalog. The five `PureGlow`/`DermaCare` products are still owned by the two smaller `manufacturer@`/`manufacturer2@` demo accounts, showing the single-brand-manufacturer use case too.

### The product catalog

On first run, the database is seeded with **~85 realistic skincare products across 20 real brands** — CeraVe, Cetaphil, La Roche-Posay, The Ordinary, Neutrogena, Eucerin, Bioderma, Aveeno, COSRX, Simple, Garnier, Nivea, Vaseline, Dove, Olay, Beauty of Joseon, Innisfree, Paula's Choice, Vichy, and Clinique — each with full ingredients, benefits, usage instructions, skin type, country of origin, pricing, batch numbers, and (for a handful) deliberately expired stock so you can demo the expiry-detection logic live. About 220 simulated verification scans are also backfilled over the past 5 months so the analytics dashboards, charts, and "recent activity" feeds look like a system that's actually been in use.

**A note on the product images:** the 80 products across the 20 real brands (CeraVe, La Roche-Posay, etc., managed by the `riyaq` account) now use real product photos, supplied directly and bundled into the project so it still works fully offline. There was no caption or filename data indicating which photo belongs to which specific product, so rather than guess a "smart" match and risk mislabeling something, each photo was assigned one-to-one across the catalog in a stable order — every photo gets used, every one of those 80 products gets a real image. If a specific pairing looks off, any manufacturer can swap a product's photo at any time via **Edit Product** in the dashboard. The 5 `PureGlow`/`DermaCare` demo products (owned by the smaller `manufacturer@`/`manufacturer2@` accounts) still use procedurally generated placeholder packaging art (`backend/utils/image_generator.py`), since no real photos exist for that fictional demo brand.

---

## 3. Switching to MySQL (optional, for formal submission)

The project defaults to SQLite so it runs instantly with zero setup for your presentation. If your supervisor requires MySQL:

1. Create the database and tables:
   ```bash
   mysql -u root -p < backend/database.sql
   ```
2. In `backend/config.py`, set:
   ```python
   USE_SQLITE_FALLBACK = os.environ.get("USE_SQLITE_FALLBACK", "false").lower() == "true"
   ```
   or simply run with the environment variable set:
   ```bash
   set USE_SQLITE_FALLBACK=false      # Windows
   export USE_SQLITE_FALLBACK=false   # macOS/Linux
   ```
3. Set your MySQL credentials via environment variables (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME`) or edit the defaults directly in `config.py`.
4. Install `PyMySQL` (already in `requirements.txt`) and restart the app.

---

## 4. Project Structure

```
frontend/
  index.html, about.html, contact.html          # Public marketing pages
  login.html, register.html                     # Authentication
  products.html                                  # Full product catalog: search, filters, sort
  verify.html                                    # Consumer QR / image / camera verification
  product-details.html                           # Public product page: gallery, benefits, related products, favorites
  manufacturer-dashboard.html                    # Product CRUD + QR generation
  consumer-dashboard.html                        # Verification history + saved favorites
  admin-dashboard.html                           # Platform stats, charts, users, blockchain ledger, AI logs
  analytics.html                                 # Verification trend & risk charts
  reports.html                                   # CSV / PDF exports
  profile.html                                   # Edit profile & password
  css/  (style.css, dashboard.css, animations.css, responsive.css)
  js/   (app.js, auth.js, dashboard.js, verification.js, reports.js, analytics.js, profile.js)

backend/
  app.py            # App factory, static file serving, demo data seeding
  config.py         # Environment-driven configuration (SQLite/MySQL toggle)
  models.py         # SQLAlchemy models — the 10+ database tables
  database.sql      # MySQL schema (for formal submission / grading)
  requirements.txt
  routes/           # REST API blueprints (auth, products, verification, reports, admin, ai, blockchain, notifications)
  utils/            # JWT handling, QR generation, blockchain service, AI detector,
                     # image_generator.py (packaging art), seed_data.py (20-brand catalog generator)
  uploads/           # Uploaded product images & generated QR codes
```

---

## 5. Key REST API Endpoints

All endpoints are prefixed with `/api`. Protected endpoints require an `Authorization: Bearer <token>` header (returned by `/auth/login` and `/auth/register`).

- `POST /auth/register`, `POST /auth/login` (email or username), `POST /auth/forgot-password`, `POST /auth/reset-password`
- `GET /auth/me`, `PUT /auth/profile`, `PUT /auth/change-password`
- `POST /products`, `GET /products` (public catalog — search/filter/sort, `?mine=true` for a manufacturer's own), `GET/PUT/DELETE /products/<id>`, `GET /products/<id>/stats`, `GET /products/<id>/related`
- `GET /products/meta/filters` (distinct brands/categories for the search page)
- `POST /products/<id>/favorite` (toggle), `GET /products/favorites/mine`
- `POST /verification/scan-qr`, `POST /verification/scan-image`, `POST /verification/scan-camera`
- `GET /verification/history`, `GET /verification/recent` (public "latest verified" feed), `GET /verification/product-chain/<product_id>`
- `GET /blockchain`, `GET /blockchain/integrity`, `GET /blockchain/<id>`
- `GET /ai/analysis/<verification_id>`, `GET /ai/risk-summary`, `GET /ai/logs`
- `GET /reports/products/csv`, `GET /reports/verifications/csv`, `GET /reports/summary/pdf`
- `GET /admin/stats`, `GET /admin/monthly-registrations`, `GET /admin/most-scanned`, `GET /admin/recent-activity`, `GET /admin/users`, `PUT /admin/users/<id>/toggle-active`
- `GET /notifications`, `PUT /notifications/<id>/read`, `PUT /notifications/read-all`

---

## 6. How the "AI" and "Blockchain" simulations work (useful for your defense/viva)

**Blockchain (`utils/blockchain_service.py`):** every product registration, update, and verification scan creates a new block. Each block stores a SHA-256 hash of its contents plus the previous block's hash — an unbroken hash chain, exactly like a real blockchain's linking mechanism (minus the distributed/peer-to-peer network layer, which is out of scope for a local demo). `GET /blockchain/integrity` walks the entire chain and recomputes hashes to prove it hasn't been tampered with.

**AI verification (`utils/ai_detector.py`):** `analyze_image_match()` simulates comparing an uploaded image against the manufacturer's reference image (standing in for a real CNN embedding + cosine-similarity comparison), producing a match score, similarity score, and confidence score. `assess_counterfeit_risk()` then combines that with business-rule signals (expiry date, recall status, repeated-scan anomalies) to reach a final Genuine / Suspicious / Counterfeit decision with a plain-English explanation. The two functions are intentionally isolated so a real TensorFlow/PyTorch model can replace the internals later without touching any route or frontend code.

---

## 7. Notes

- No network access was available while generating this project, so dependencies could not be pip-installed and live-tested end-to-end in this environment. All backend Python files were syntax-checked, and every frontend DOM element ID referenced by the JavaScript was cross-checked against the HTML. On a normal machine with internet access, `pip install -r requirements.txt && python app.py` is expected to work immediately — if you hit any issue, check the exact error message first (missing package, port 5000 already in use, etc.).
- Notifications are implemented via short-interval polling (every 20s) rather than WebSockets, which keeps the stack simple for a student project while still feeling "real-time".
- Camera capture requires the browser to grant camera permission and (outside of `localhost`) generally requires HTTPS.
