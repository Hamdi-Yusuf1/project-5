/* ==========================================================
   AuthenChain — Dashboard Logic
   Manufacturer product management / Admin stats / Consumer overview
   ========================================================== */

function statusBadge(status) {
  const map = { active: "badge-genuine", recalled: "badge-counterfeit", expired: "badge-suspicious" };
  return `<span class="badge-status ${map[status] || "badge-genuine"}">${status}</span>`;
}
function resultBadge(result) {
  const map = { genuine: "badge-genuine", suspicious: "badge-suspicious", counterfeit: "badge-counterfeit" };
  const icon = { genuine: "fa-circle-check", suspicious: "fa-triangle-exclamation", counterfeit: "fa-circle-xmark" };
  return `<span class="badge-status ${map[result]}"><i class="fa-solid ${icon[result]} me-1"></i>${result}</span>`;
}
function riskBadge(level) {
  return `<span class="badge-status badge-${level}">${level} risk</span>`;
}
function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

/* =================== MANUFACTURER DASHBOARD =================== */

async function loadManufacturerOverview() {
  const grid = document.getElementById("mfrStatsGrid");
  if (!grid) return;
  try {
    const data = await apiRequest("/products?mine=true");
    const products = data.products;
    const totalScans = products.reduce((sum, p) => sum + p.scan_count, 0);
    const active = products.filter((p) => p.status === "active").length;
    const recalled = products.filter((p) => p.status === "recalled").length;

    grid.innerHTML = `
      ${statCard("blue", "fa-box-open", products.length, "Registered Products")}
      ${statCard("green", "fa-qrcode", totalScans, "Total Verification Scans")}
      ${statCard("orange", "fa-circle-check", active, "Active Products")}
      ${statCard("red", "fa-triangle-exclamation", recalled, "Recalled Products")}
    `;
    grid.querySelectorAll("[data-count]").forEach((el) => animateCount(el, parseInt(el.dataset.count)));

    renderRecentProducts(products.slice(0, 5));
  } catch (err) { showToast(err.message, "danger"); }
}

function statCard(color, icon, value, label) {
  return `
    <div class="col-md-3 col-6">
      <div class="stat-card">
        <div class="stat-icon ${color}"><i class="fa-solid ${icon}"></i></div>
        <div>
          <div class="stat-value" data-count="${value}">0</div>
          <div class="stat-label">${label}</div>
        </div>
      </div>
    </div>`;
}

/* Like statCard, but for values that can't be integer-animated (e.g. "12.5%") — displays instantly instead. */
function staticStatCard(color, icon, valueText, label) {
  return `
    <div class="col-md-3 col-6">
      <div class="stat-card">
        <div class="stat-icon ${color}"><i class="fa-solid ${icon}"></i></div>
        <div>
          <div class="stat-value">${valueText}</div>
          <div class="stat-label">${label}</div>
        </div>
      </div>
    </div>`;
}

function renderRecentProducts(products) {
  const el = document.getElementById("recentProductsBody");
  if (!el) return;
  el.innerHTML = products.length ? products.map((p) => `
    <tr>
      <td><strong>${p.product_name}</strong><div class="text-muted-soft" style="font-size:0.78rem;">${p.batch_number}</div></td>
      <td>${p.brand}</td>
      <td>${statusBadge(p.status)}</td>
      <td>${p.scan_count}</td>
      <td>${fmtDate(p.created_at)}</td>
    </tr>`).join("") : `<tr><td colspan="5" class="text-center text-muted-soft py-4">No products registered yet</td></tr>`;
}

async function loadAllManufacturerProducts() {
  const container = document.getElementById("productsGrid");
  if (!container) return;
  try {
    const search = document.getElementById("productSearch")?.value || "";
    const data = await apiRequest(`/products?mine=true&search=${encodeURIComponent(search)}`);
    renderProductGrid(data.products, container);
  } catch (err) { showToast(err.message, "danger"); }
}

function renderProductGrid(products, container) {
  container.innerHTML = products.length ? products.map((p) => `
    <div class="col-lg-4 col-md-6">
      <div class="product-card">
        <div class="product-card-img">
          ${p.image_path ? `<img src="/${p.image_path}" alt="${p.product_name}">` : `<i class="fa-solid fa-flask-vial"></i>`}
        </div>
        <div class="product-card-body">
          <div class="d-flex justify-content-between align-items-start mb-1">
            <h6 class="mb-0">${p.product_name}</h6>
            ${statusBadge(p.status)}
          </div>
          <div class="text-muted-soft" style="font-size:0.85rem;">${p.brand} • ${p.batch_number}</div>
          <div class="d-flex justify-content-between align-items-center mt-3">
            <small class="text-muted-soft"><i class="fa-solid fa-qrcode me-1"></i>${p.scan_count} scans</small>
            <div class="d-flex gap-2">
              <a class="btn btn-sm btn-outline-royal" href="product-details.html?id=${p.id}" title="View Details"><i class="fa-solid fa-eye"></i></a>
              <button class="btn btn-sm btn-outline-royal" onclick="openEditProduct(${p.id})"><i class="fa-solid fa-pen"></i></button>
              <a class="btn btn-sm btn-outline-royal" href="${p.qr_code_path ? '/' + p.qr_code_path : '#'}" download title="Download QR"><i class="fa-solid fa-download"></i></a>
              <button class="btn btn-sm btn-primary-gradient" onclick="deleteProduct(${p.id})"><i class="fa-solid fa-trash"></i></button>
            </div>
          </div>
        </div>
      </div>
    </div>`).join("") : `<div class="col-12"><div class="empty-state"><i class="fa-solid fa-box-open"></i><p>No products found. Register your first product to get started.</p></div></div>`;
}

let editingProductId = null;

function openAddProduct() {
  editingProductId = null;
  document.getElementById("productForm").reset();
  document.getElementById("productModalTitle").textContent = "Register New Product";
  new bootstrap.Modal(document.getElementById("productModal")).show();
}

async function openEditProduct(id) {
  try {
    const data = await apiRequest(`/products/${id}`);
    const p = data.product;
    editingProductId = id;
    document.getElementById("productModalTitle").textContent = "Update Product";
    document.getElementById("pName").value = p.product_name;
    document.getElementById("pBrand").value = p.brand;
    document.getElementById("pBatch").value = p.batch_number;
    document.getElementById("pBatch").disabled = true;
    document.getElementById("pCategory").value = p.category || "";
    document.getElementById("pIngredients").value = p.ingredients || "";
    document.getElementById("pDescription").value = p.description || "";
    document.getElementById("pMfgDate").value = p.manufacturing_date || "";
    document.getElementById("pExpDate").value = p.expiry_date || "";
    document.getElementById("pStatus").value = p.status;
    document.getElementById("pSkinType").value = p.skin_type || "All Skin Types";
    document.getElementById("pCountry").value = p.country_of_origin || "";
    document.getElementById("pPrice").value = p.price || "";
    document.getElementById("pBenefits").value = p.benefits || "";
    document.getElementById("pUsage").value = p.usage_instructions || "";
    document.getElementById("pWarnings").value = p.warnings || "";
    new bootstrap.Modal(document.getElementById("productModal")).show();
  } catch (err) { showToast(err.message, "danger"); }
}

async function deleteProduct(id) {
  if (!confirm("Delete this product? This cannot be undone.")) return;
  try {
    await apiRequest(`/products/${id}`, { method: "DELETE" });
    showToast("Product deleted", "success");
    loadAllManufacturerProducts();
  } catch (err) { showToast(err.message, "danger"); }
}

function initProductForm() {
  const form = document.getElementById("productForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("product_name", document.getElementById("pName").value);
    fd.append("brand", document.getElementById("pBrand").value);
    fd.append("batch_number", document.getElementById("pBatch").value);
    fd.append("category", document.getElementById("pCategory").value);
    fd.append("ingredients", document.getElementById("pIngredients").value);
    fd.append("description", document.getElementById("pDescription").value);
    fd.append("manufacturing_date", document.getElementById("pMfgDate").value);
    fd.append("expiry_date", document.getElementById("pExpDate").value);
    fd.append("status", document.getElementById("pStatus").value);
    fd.append("skin_type", document.getElementById("pSkinType").value);
    fd.append("country_of_origin", document.getElementById("pCountry").value);
    fd.append("price", document.getElementById("pPrice").value || "0");
    fd.append("benefits", document.getElementById("pBenefits").value);
    fd.append("usage_instructions", document.getElementById("pUsage").value);
    fd.append("warnings", document.getElementById("pWarnings").value);
    const imageFile = document.getElementById("pImage").files[0];
    if (imageFile) fd.append("image", imageFile);

    try {
      if (editingProductId) {
        await apiRequest(`/products/${editingProductId}`, { method: "PUT", body: fd, isForm: true });
        showToast("Product updated successfully", "success");
      } else {
        await apiRequest("/products", { method: "POST", body: fd, isForm: true });
        showToast("Product registered and QR code generated!", "success");
      }
      bootstrap.Modal.getInstance(document.getElementById("productModal"))?.hide();
      document.getElementById("pBatch").disabled = false;
      loadAllManufacturerProducts();
      loadManufacturerOverview();
    } catch (err) { showToast(err.message, "danger"); }
  });
}

/* =================== ADMIN DASHBOARD =================== */

async function loadAdminOverview() {
  const grid = document.getElementById("adminStatsGrid");
  if (!grid) return;
  try {
    const data = await apiRequest("/admin/stats");
    const s = data.stats;
    grid.innerHTML = `
      ${statCard("blue", "fa-industry", s.total_manufacturers, "Manufacturers")}
      ${statCard("green", "fa-users", s.total_consumers, "Users")}
      ${statCard("orange", "fa-box-open", s.total_products, "Total Products")}
      ${statCard("blue", "fa-circle-check", s.verified_products, "Verified Products")}
      ${statCard("red", "fa-triangle-exclamation", s.counterfeit_products, "Counterfeit Flags")}
      ${statCard("green", "fa-link", s.total_blocks, "Blockchain Blocks")}
    `;
    document.querySelectorAll("[data-count]").forEach((el) => animateCount(el, parseInt(el.dataset.count)));

    const activity = await apiRequest("/admin/recent-activity");
    const activityEl = document.getElementById("recentActivityBody");
    if (activityEl) {
      activityEl.innerHTML = activity.activity.length ? activity.activity.map((v) => `
        <tr>
          <td>${v.product_name}</td>
          <td>${v.scan_method.toUpperCase()}</td>
          <td>${resultBadge(v.result)}</td>
          <td>${riskBadge(v.risk_level)}</td>
          <td>${fmtDate(v.created_at)}</td>
        </tr>`).join("") : `<tr><td colspan="5" class="text-center text-muted-soft py-4">No verification activity yet</td></tr>`;
    }

    if (window.Chart) renderAdminCharts();
  } catch (err) { showToast(err.message, "danger"); }
}

async function renderAdminCharts() {
  try {
    const [monthly, risk] = await Promise.all([
      apiRequest("/admin/monthly-registrations"),
      apiRequest("/ai/risk-summary"),
    ]);

    const regCtx = document.getElementById("monthlyRegChart");
    if (regCtx) {
      new Chart(regCtx, {
        type: "line",
        data: {
          labels: monthly.monthly_registrations.map((m) => m.month),
          datasets: [{
            label: "Product Registrations",
            data: monthly.monthly_registrations.map((m) => m.count),
            borderColor: "#2952e3",
            backgroundColor: "rgba(41,82,227,0.12)",
            fill: true,
            tension: 0.4,
            pointBackgroundColor: "#2952e3",
          }],
        },
        options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
      });
    }

    const riskCtx = document.getElementById("riskDistChart");
    if (riskCtx) {
      new Chart(riskCtx, {
        type: "doughnut",
        data: {
          labels: ["Low Risk", "Medium Risk", "High Risk"],
          datasets: [{
            data: [risk.risk_distribution.low || 0, risk.risk_distribution.medium || 0, risk.risk_distribution.high || 0],
            backgroundColor: ["#2fd18a", "#f5a623", "#ef4460"],
            borderWidth: 0,
          }],
        },
        options: { plugins: { legend: { position: "bottom" } }, cutout: "68%" },
      });
    }
  } catch (err) { /* charts are optional enhancements */ }
}

async function loadAdminUsers(role) {
  const el = document.getElementById("usersTableBody");
  if (!el) return;
  try {
    const data = await apiRequest(`/admin/users${role ? "?role=" + role : ""}`);
    el.innerHTML = data.users.length ? data.users.map((u) => `
      <tr>
        <td><div class="table-avatar d-flex align-items-center justify-content-center fw-bold text-royal">${u.full_name.charAt(0)}</div></td>
        <td><strong>${u.full_name}</strong>${u.company_name ? `<div class="text-muted-soft" style="font-size:0.78rem;">${u.company_name}</div>` : ""}</td>
        <td>${u.email}</td>
        <td><span class="badge-status badge-genuine">${u.role}</span></td>
        <td>${u.is_active ? '<span class="badge-status badge-genuine">active</span>' : '<span class="badge-status badge-counterfeit">disabled</span>'}</td>
        <td><button class="btn btn-sm btn-outline-royal" onclick="toggleUserActive(${u.id})">${u.is_active ? "Disable" : "Enable"}</button></td>
      </tr>`).join("") : `<tr><td colspan="6" class="text-center text-muted-soft py-4">No users found</td></tr>`;
  } catch (err) { showToast(err.message, "danger"); }
}

async function toggleUserActive(id) {
  try {
    await apiRequest(`/admin/users/${id}/toggle-active`, { method: "PUT" });
    showToast("User status updated", "success");
    loadAdminUsers();
  } catch (err) { showToast(err.message, "danger"); }
}

async function loadAdminProducts(search = "") {
  const el = document.getElementById("adminProductsBody");
  if (!el) return;
  try {
    const data = await apiRequest(`/products?search=${encodeURIComponent(search)}`);
    el.innerHTML = data.products.length ? data.products.map((p) => `
      <tr>
        <td><strong>${p.product_name}</strong><div class="text-muted-soft" style="font-size:0.78rem;">${p.batch_number}</div></td>
        <td>${p.brand}</td>
        <td>${p.manufacturer_name || "—"}</td>
        <td>${statusBadge(p.status)}</td>
        <td>${p.scan_count}</td>
        <td>
          <a class="btn btn-sm btn-outline-royal me-1" href="product-details.html?id=${p.id}" title="View"><i class="fa-solid fa-eye"></i></a>
          <button class="btn btn-sm btn-primary-gradient" onclick="adminDeleteProduct(${p.id})" title="Delete"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>`).join("") : `<tr><td colspan="6" class="text-center text-muted-soft py-4">No products found</td></tr>`;
  } catch (err) { showToast(err.message, "danger"); }
}

async function adminDeleteProduct(id) {
  if (!confirm("Delete this product permanently? This cannot be undone.")) return;
  try {
    await apiRequest(`/products/${id}`, { method: "DELETE" });
    showToast("Product deleted", "success");
    loadAdminProducts(document.getElementById("adminProductSearch")?.value || "");
  } catch (err) { showToast(err.message, "danger"); }
}

/* =================== CONSUMER DASHBOARD =================== */

async function loadConsumerOverview() {
  const el = document.getElementById("consumerHistoryBody");
  const statsGrid = document.getElementById("consumerStatsGrid");
  if (!el && !statsGrid) return;

  try {
    const data = await apiRequest("/verification/history");
    const history = data.history;

    if (statsGrid) {
      const genuine = history.filter((h) => h.result === "genuine").length;
      const counterfeit = history.filter((h) => h.result === "counterfeit").length;
      statsGrid.innerHTML = `
        ${statCard("blue", "fa-qrcode", history.length, "Total Scans")}
        ${statCard("green", "fa-shield-halved", genuine, "Genuine Products")}
        ${statCard("red", "fa-triangle-exclamation", counterfeit, "Counterfeit Alerts")}
      `;
      statsGrid.querySelectorAll("[data-count]").forEach((el) => animateCount(el, parseInt(el.dataset.count)));
    }

    if (el) {
      el.innerHTML = history.length ? history.map((h) => `
        <tr>
          <td>${h.product_name}</td>
          <td>${h.scan_method.toUpperCase()}</td>
          <td>${resultBadge(h.result)}</td>
          <td>${riskBadge(h.risk_level)}</td>
          <td>${h.confidence_score}%</td>
          <td>${fmtDate(h.created_at)}</td>
        </tr>`).join("") : `<tr><td colspan="6" class="text-center text-muted-soft py-4">You haven't verified any products yet. Try scanning one!</td></tr>`;
    }
  } catch (err) { showToast(err.message, "danger"); }
}

async function loadFavorites() {
  const grid = document.getElementById("favoritesGrid");
  if (!grid) return;
  try {
    const data = await apiRequest("/products/favorites/mine");
    grid.innerHTML = data.products.length
      ? data.products.map(productCardHTML).join("")
      : '<div class="col-12"><div class="empty-state"><i class="fa-solid fa-heart-crack"></i><p>No favorites yet. Browse the catalog and tap the heart on any product to save it here.</p></div></div>';
  } catch (err) {
    grid.innerHTML = `<div class="col-12 text-center text-muted-soft py-3">${err.message}</div>`;
  }
}

async function loadBlockchainLedger() {
  const body = document.getElementById("blockchainLedgerBody");
  const badge = document.getElementById("chainIntegrityBadge");
  if (!body) return;
  try {
    const [blocksRes, integrityRes] = await Promise.all([
      apiRequest("/blockchain?per_page=15"),
      apiRequest("/blockchain/integrity"),
    ]);
    if (badge) {
      badge.textContent = integrityRes.valid ? "Chain Verified ✓" : "Integrity Issue";
      badge.className = "badge-status " + (integrityRes.valid ? "badge-genuine" : "badge-counterfeit");
    }
    body.innerHTML = blocksRes.blocks.length ? blocksRes.blocks.map((b) => `
      <tr>
        <td>#${b.block_index}</td>
        <td>${b.product_name || "—"}</td>
        <td><span class="badge-status badge-genuine">${b.verification_status}</span></td>
        <td><code style="font-size:0.72rem;">${b.block_hash.slice(0, 14)}...</code></td>
      </tr>`).join("") : `<tr><td colspan="4" class="text-center text-muted-soft py-4">No blocks yet</td></tr>`;
  } catch (err) {
    body.innerHTML = `<tr><td colspan="4" class="text-center text-muted-soft py-4">${err.message}</td></tr>`;
  }
}

async function loadAiLogs() {
  const body = document.getElementById("aiLogsBody");
  if (!body) return;
  try {
    const data = await apiRequest("/ai/logs?limit=15");
    body.innerHTML = data.logs.length ? data.logs.map((l) => `
      <tr>
        <td>${l.product_name || "—"}</td>
        <td>${resultBadge((l.final_decision || "").toLowerCase().includes("counterfeit") ? "counterfeit" : (l.final_decision || "").toLowerCase().includes("suspicious") ? "suspicious" : "genuine")}</td>
        <td>${l.match_score}%</td>
        <td>${l.authenticity_confidence}%</td>
      </tr>`).join("") : `<tr><td colspan="4" class="text-center text-muted-soft py-4">No AI logs yet</td></tr>`;
  } catch (err) {
    body.innerHTML = `<tr><td colspan="4" class="text-center text-muted-soft py-4">${err.message}</td></tr>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadManufacturerOverview();
  loadAllManufacturerProducts();
  initProductForm();
  loadAdminOverview();
  loadConsumerOverview();
  loadFavorites();
  loadBlockchainLedger();
  loadAiLogs();

  document.getElementById("productSearch")?.addEventListener("input", debounce(loadAllManufacturerProducts, 350));

  document.querySelectorAll("[data-user-role-filter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-user-role-filter]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      loadAdminUsers(btn.dataset.userRoleFilter || "");
    });
  });
  if (document.getElementById("usersTableBody")) loadAdminUsers();
  if (document.getElementById("adminProductsBody")) loadAdminProducts();
  document.getElementById("adminProductSearch")?.addEventListener("input", debounce((e) => loadAdminProducts(e.target.value), 350));
});

function debounce(fn, delay) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}
