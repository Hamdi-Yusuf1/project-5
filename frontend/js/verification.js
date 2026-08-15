/* ==========================================================
   AuthenChain — Product Verification Logic
   QR Scan (manual/camera-based simulated decode) / Image Upload / Live Camera Capture
   ========================================================== */

let cameraStream = null;

function switchVerifyTab(tab) {
  document.querySelectorAll(".verify-tab-pane").forEach((p) => p.classList.add("d-none"));
  document.querySelectorAll(".verify-tab-btn").forEach((b) => b.classList.remove("active"));
  document.getElementById(`tab-${tab}`).classList.remove("d-none");
  document.querySelector(`[data-verify-tab="${tab}"]`).classList.add("active");

  if (tab !== "camera") stopCamera();
}

/* ---------- QR (manual code entry simulating a scan) ---------- */
function initQrForm() {
  const form = document.getElementById("qrScanForm");
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const qrData = document.getElementById("qrCodeInput").value.trim();
    if (!qrData) { showToast("Enter or paste a QR code value", "warning"); return; }
    await runVerification("/verification/scan-qr", { method: "POST", body: { qr_data: qrData }, auth: Auth.isLoggedIn() });
  });
}

/* ---------- Image upload ---------- */
function initImageUploadForm() {
  const form = document.getElementById("imageScanForm");
  const preview = document.getElementById("imagePreview");
  const fileInput = document.getElementById("imageFileInput");

  fileInput?.addEventListener("change", () => {
    const file = fileInput.files[0];
    if (file && preview) {
      preview.src = URL.createObjectURL(file);
      preview.classList.remove("d-none");
    }
  });

  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const batch = document.getElementById("imageBatchInput").value.trim();
    const file = fileInput.files[0];
    if (!file) { showToast("Please choose a product photo to upload", "warning"); return; }

    const fd = new FormData();
    fd.append("batch_number", batch);
    fd.append("image", file);

    await runVerification("/verification/scan-image", { method: "POST", body: fd, isForm: true, auth: Auth.isLoggedIn() });
  });
}

/* ---------- Live camera capture ---------- */
async function startCamera() {
  const video = document.getElementById("cameraVideo");
  if (!video) return;
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    video.srcObject = cameraStream;
    document.getElementById("cameraStartBtn").classList.add("d-none");
    document.getElementById("cameraCaptureBtn").classList.remove("d-none");
    video.classList.remove("d-none");
  } catch (err) {
    showToast("Camera access was denied or is unavailable on this device", "danger");
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach((t) => t.stop());
    cameraStream = null;
  }
}

async function captureFromCamera() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("cameraCanvas");
  const batch = document.getElementById("cameraBatchInput").value.trim();
  if (!video || !video.srcObject) { showToast("Start the camera first", "warning"); return; }

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const imageData = canvas.toDataURL("image/png");

  const preview = document.getElementById("cameraPreview");
  if (preview) { preview.src = imageData; preview.classList.remove("d-none"); }

  await runVerification("/verification/scan-camera", { method: "POST", body: { batch_number: batch, image_data: imageData }, auth: Auth.isLoggedIn() });
  stopCamera();
}

/* ---------- Shared verification runner + results rendering ---------- */
async function runVerification(path, options) {
  const btn = document.querySelector(`#tab-${currentVisibleTab()} button[type=submit], #tab-${currentVisibleTab()} .verify-action-btn`);
  const resultsSection = document.getElementById("verifyResults");
  const loadingSection = document.getElementById("verifyLoading");

  resultsSection?.classList.add("d-none");
  loadingSection?.classList.remove("d-none");

  try {
    const data = await apiRequest(path, options);
    renderVerificationResult(data);
  } catch (err) {
    showToast(err.message, "danger");
  } finally {
    loadingSection?.classList.add("d-none");
  }
}

function currentVisibleTab() {
  const active = document.querySelector(".verify-tab-btn.active");
  return active ? active.dataset.verifyTab : "qr";
}

function renderVerificationResult(data) {
  const section = document.getElementById("verifyResults");
  if (!section) return;
  section.classList.remove("d-none");
  section.scrollIntoView({ behavior: "smooth", block: "start" });

  const product = data.product;
  const verification = data.verification;
  const ai = data.ai_analysis;
  const decision = verification.result;

  const iconMap = { genuine: "fa-shield-halved", suspicious: "fa-triangle-exclamation", counterfeit: "fa-circle-xmark" };
  const titleMap = { genuine: "✅ Genuine Product", suspicious: "⚠ Suspicious Product", counterfeit: "❌ Counterfeit Product" };

  document.getElementById("resultBadgeIcon").innerHTML = `<i class="fa-solid ${iconMap[decision]}"></i>`;
  document.getElementById("resultBadgeIcon").className = `verify-badge-xl ${decision}`;
  document.getElementById("resultTitle").textContent = titleMap[decision];
  document.getElementById("resultRisk").innerHTML = riskBadge(verification.risk_level);

  const warningBanner = document.getElementById("counterfeitWarning");
  if (decision === "counterfeit") {
    warningBanner.classList.remove("d-none");
  } else {
    warningBanner.classList.add("d-none");
  }

  document.getElementById("aiExplanation").textContent = ai.explanation;

  drawGauge("matchGauge", ai.match_score, "Match Score");
  drawGauge("similarityGauge", ai.similarity_score, "Similarity");
  drawGauge("confidenceGauge", ai.authenticity_confidence, "Confidence");

  document.getElementById("qrStatusBadge").innerHTML = data.qr_status === "valid"
    ? '<span class="badge-status badge-genuine"><i class="fa-solid fa-qrcode me-1"></i>QR Verified</span>'
    : '<span class="badge-status badge-counterfeit"><i class="fa-solid fa-qrcode me-1"></i>QR Invalid</span>';

  document.getElementById("blockchainStatusBadge").innerHTML = data.blockchain_status === "verified"
    ? '<span class="badge-status badge-genuine"><i class="fa-solid fa-link me-1"></i>Blockchain Verified</span>'
    : '<span class="badge-status badge-counterfeit"><i class="fa-solid fa-link-slash me-1"></i>Not On-Chain</span>';

  const productDetailsEl = document.getElementById("productDetailsCard");
  if (product) {
    productDetailsEl.innerHTML = `
      <div class="row g-3">
        <div class="col-md-6"><small class="text-muted-soft">Product Name</small><div class="fw-bold">${product.product_name}</div></div>
        <div class="col-md-6"><small class="text-muted-soft">Brand</small><div class="fw-bold">${product.brand}</div></div>
        <div class="col-md-6"><small class="text-muted-soft">Manufacturer</small><div class="fw-bold">${product.manufacturer_name || "—"}</div></div>
        <div class="col-md-6"><small class="text-muted-soft">Batch Number</small><div class="fw-bold">${product.batch_number}</div></div>
        <div class="col-md-6"><small class="text-muted-soft">Manufacturing Date</small><div class="fw-bold">${fmtDate(product.manufacturing_date)}</div></div>
        <div class="col-md-6"><small class="text-muted-soft">Expiry Date</small><div class="fw-bold">${fmtDate(product.expiry_date)}</div></div>
        <div class="col-12"><small class="text-muted-soft">Ingredients</small><div>${product.ingredients || "Not specified"}</div></div>
      </div>`;
    const imgEl = document.getElementById("registeredProductImage");
    if (imgEl) imgEl.src = product.image_path ? `/${product.image_path}` : "https://placehold.co/400x400/eef1f8/7c86a3?text=No+Image";
  } else {
    productDetailsEl.innerHTML = `<div class="empty-state"><i class="fa-solid fa-circle-question"></i><p>This batch number was not found in the manufacturer registry.</p></div>`;
  }
}

function drawGauge(canvasId, value, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  // Always show the real number as text first — this must never depend on
  // whether the charting library loaded, since a numeric readout matters
  // more than the decorative ring around it.
  const valueLabel = document.getElementById(canvasId + "Value");
  if (valueLabel) valueLabel.textContent = `${value.toFixed(1)}%`;
  const textLabel = document.getElementById(canvasId + "Label");
  if (textLabel) textLabel.textContent = label;

  if (!window.Chart) {
    canvas.closest(".gauge-wrap")?.classList.add("gauge-fallback");
    return;
  }

  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  const color = value >= 75 ? "#2fd18a" : value >= 50 ? "#f5a623" : "#ef4460";
  new Chart(canvas, {
    type: "doughnut",
    data: { datasets: [{ data: [value, 100 - value], backgroundColor: [color, "#eef1f8"], borderWidth: 0 }] },
    options: { cutout: "78%", rotation: -90, circumference: 180, plugins: { legend: { display: false }, tooltip: { enabled: false } } },
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initQrForm();
  initImageUploadForm();
  document.getElementById("cameraStartBtn")?.addEventListener("click", startCamera);
  document.getElementById("cameraCaptureBtn")?.addEventListener("click", captureFromCamera);

  const params = new URLSearchParams(window.location.search);
  const prefillBatch = params.get("batch");
  if (prefillBatch) {
    const el = document.getElementById("qrCodeInput");
    if (el) el.value = prefillBatch;
  }
});
