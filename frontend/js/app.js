/* ==========================================================
   AuthenChain — Core App Utilities
   Shared across every page: API client, auth helpers, toasts,
   navbar/notification wiring, scroll reveal.
   ========================================================== */

const API_BASE = "/api";

const Auth = {
  getToken() { return localStorage.getItem("ac_token"); },
  setToken(t) { localStorage.setItem("ac_token", t); },
  getUser() {
    try { return JSON.parse(localStorage.getItem("ac_user") || "null"); }
    catch (e) { return null; }
  },
  setUser(u) { localStorage.setItem("ac_user", JSON.stringify(u)); },
  logout() {
    localStorage.removeItem("ac_token");
    localStorage.removeItem("ac_user");
    window.location.href = "login.html";
  },
  isLoggedIn() { return !!this.getToken(); },
  requireRole(roles) {
    const user = this.getUser();
    if (!this.isLoggedIn() || !user || !roles.includes(user.role)) {
      window.location.href = "login.html";
      return null;
    }
    return user;
  },
};

async function apiRequest(path, { method = "GET", body = null, isForm = false, auth = true } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth && Auth.getToken()) headers["Authorization"] = `Bearer ${Auth.getToken()}`;

  const options = { method, headers };
  if (body) options.body = isForm ? body : JSON.stringify(body);

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, options);
  } catch (err) {
    throw new Error("Unable to reach the server. Please check that the backend is running.");
  }

  let data;
  try { data = await response.json(); }
  catch (e) { data = { success: false, message: "Unexpected server response" }; }

  if (response.status === 401) {
    Auth.logout();
    return data;
  }

  if (!response.ok) {
    throw new Error(data.message || "Something went wrong. Please try again.");
  }
  return data;
}

/* ---------- Toast notifications ---------- */
function showToast(message, type = "info") {
  let container = document.getElementById("ac-toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "ac-toast-container";
    container.style.cssText = "position:fixed;top:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;max-width:340px;";
    document.body.appendChild(container);
  }

  const icons = { success: "fa-circle-check", danger: "fa-circle-exclamation", warning: "fa-triangle-exclamation", info: "fa-circle-info" };
  const colors = { success: "#2fd18a", danger: "#ef4460", warning: "#f5a623", info: "#2952e3" };

  const toast = document.createElement("div");
  toast.className = "toast-slide-in";
  toast.style.cssText = `background:white;border-left:4px solid ${colors[type] || colors.info};border-radius:12px;padding:14px 16px;box-shadow:0 10px 30px rgba(13,27,76,0.18);display:flex;align-items:center;gap:10px;font-size:0.9rem;font-weight:600;color:#0d1b4c;`;
  toast.innerHTML = `<i class="fa-solid ${icons[type] || icons.info}" style="color:${colors[type] || colors.info};font-size:1.1rem;"></i><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = "opacity 0.4s ease";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 400);
  }, 4200);
}

/* ---------- Navbar / shared layout wiring ---------- */
function initNavbar() {
  const authArea = document.getElementById("navAuthArea");
  if (!authArea) return;

  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    const dashLink = { manufacturer: "manufacturer-dashboard.html", consumer: "consumer-dashboard.html", admin: "admin-dashboard.html" }[user.role] || "login.html";
    const favLink = user.role === "consumer"
      ? `<a href="consumer-dashboard.html#favorites" class="btn btn-outline-royal btn-sm px-3 me-2" title="My Favorites"><i class="fa-solid fa-heart"></i></a>`
      : "";
    authArea.innerHTML = `
      ${favLink}
      <a href="${dashLink}" class="btn btn-primary-gradient btn-sm px-4">
        <i class="fa-solid fa-gauge-high me-1"></i> Dashboard
      </a>`;
  } else {
    authArea.innerHTML = `
      <a href="login.html" class="btn btn-outline-royal btn-sm px-4 me-2">Login</a>
      <a href="register.html" class="btn btn-primary-gradient btn-sm px-4">Get Started</a>`;
  }

  const path = window.location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav-link-custom").forEach((link) => {
    if (link.getAttribute("href") === path) link.classList.add("active");
  });
}

/* ---------- Sidebar / dashboard shell wiring ---------- */
function initSidebar() {
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("dashSidebar");
  const overlay = document.getElementById("sidebarOverlay");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
      overlay?.classList.toggle("show");
    });
  }
  overlay?.addEventListener("click", () => {
    sidebar.classList.remove("open");
    overlay.classList.remove("show");
  });

  const path = window.location.pathname.split("/").pop() || "";
  document.querySelectorAll(".sidebar-link").forEach((link) => {
    if (link.getAttribute("href") === path) link.classList.add("active");
  });

  const user = Auth.getUser();
  const nameEl = document.getElementById("sidebarUserName");
  const roleEl = document.getElementById("sidebarUserRole");
  const avatarEl = document.getElementById("sidebarUserAvatar");
  if (user) {
    if (nameEl) nameEl.textContent = user.full_name;
    if (roleEl) roleEl.textContent = user.role === "consumer" ? "User" : user.role.charAt(0).toUpperCase() + user.role.slice(1);
    if (avatarEl) avatarEl.textContent = user.full_name.charAt(0).toUpperCase();
  }

  document.querySelectorAll(".logout-btn").forEach((btn) => btn.addEventListener("click", (e) => { e.preventDefault(); Auth.logout(); }));
}

/* ---------- Notifications dropdown ---------- */
async function loadNotifications() {
  const bell = document.getElementById("notifBell");
  const list = document.getElementById("notifList");
  const dot = document.getElementById("notifDot");
  if (!bell || !Auth.isLoggedIn()) return;

  try {
    const data = await apiRequest("/notifications");
    if (dot) dot.style.display = data.unread_count > 0 ? "block" : "none";
    if (list) {
      list.innerHTML = data.notifications.length
        ? data.notifications.slice(0, 8).map((n) => `
          <div class="dropdown-item-text px-3 py-2 border-bottom" style="white-space:normal;">
            <div class="d-flex justify-content-between">
              <strong style="font-size:0.85rem;">${n.title}</strong>
              ${!n.is_read ? '<span class="badge rounded-pill" style="background:#2952e3;">new</span>' : ""}
            </div>
            <div class="text-muted-soft" style="font-size:0.8rem;">${n.message}</div>
          </div>`).join("")
        : `<div class="px-3 py-4 text-center text-muted-soft">No notifications yet</div>`;
    }
  } catch (e) { /* silent fail on dashboards without connectivity */ }
}

/* ---------- Scroll reveal for landing page ---------- */
function initScrollReveal() {
  const items = document.querySelectorAll(".reveal-on-scroll");
  if (!items.length) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => { if (entry.isIntersecting) entry.target.classList.add("visible"); });
  }, { threshold: 0.15 });
  items.forEach((item) => observer.observe(item));
}

/* ---------- Number count-up ---------- */
function animateCount(el, target, duration = 1400) {
  const start = 0;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * eased).toLocaleString();
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ---------- Shared product card (used on homepage, products.html, favorites) ---------- */
function productCardHTML(p) {
  const statusBadge = p.status === "expired"
    ? '<span class="badge-status badge-counterfeit" style="position:absolute;top:12px;left:12px;">Expired Stock</span>'
    : '<span class="badge-status badge-genuine" style="position:absolute;top:12px;left:12px;"><i class="fa-solid fa-shield-halved"></i> Verified</span>';
  const heartClass = p.is_favorited ? "fa-solid" : "fa-regular";
  const heartColor = p.is_favorited ? "#ef4460" : "#7c86a3";
  return `
    <div class="col-lg-3 col-md-4 col-6">
      <div class="pcard h-100">
        <div class="position-relative">
          <a href="product-details.html?id=${p.id}">
            <img src="/${p.image_path}" class="pcard-img" alt="${p.product_name}" loading="lazy">
          </a>
          ${statusBadge}
          <button class="pcard-fav-btn" onclick="toggleFavoriteFromCard(event, ${p.id}, this)" title="Save to favorites">
            <i class="${heartClass} fa-heart" style="color:${heartColor};"></i>
          </button>
        </div>
        <div class="p-3">
          <div class="text-muted-soft" style="font-size:0.72rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;">${p.brand}</div>
          <a href="product-details.html?id=${p.id}" class="pcard-title">${p.product_name}</a>
          <div class="d-flex justify-content-between align-items-end mt-2">
            <div>
              <div class="text-muted-soft" style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.04em;">Est. Retail</div>
              <span class="text-royal fw-bold">$${(p.price || 0).toFixed(2)}</span>
            </div>
            <span class="text-muted-soft" style="font-size:0.78rem;"><i class="fa-solid fa-qrcode me-1"></i>${p.scan_count || 0} scans</span>
          </div>
        </div>
      </div>
    </div>`;
}

async function toggleFavoriteFromCard(event, productId, btn) {
  event.preventDefault();
  event.stopPropagation();
  if (!Auth.isLoggedIn()) {
    window.location.href = "login.html";
    return;
  }
  try {
    const res = await apiRequest(`/products/${productId}/favorite`, { method: "POST" });
    const icon = btn.querySelector("i");
    if (res.favorited) {
      icon.classList.remove("fa-regular");
      icon.classList.add("fa-solid");
      icon.style.color = "#ef4460";
      showToast("Added to favorites", "success");
    } else {
      icon.classList.remove("fa-solid");
      icon.classList.add("fa-regular");
      icon.style.color = "#7c86a3";
      showToast("Removed from favorites", "info");
    }
  } catch (e) { showToast(e.message, "danger"); }
}

/* ---------- Homepage dynamic sections: featured products, brands, categories, latest verified ---------- */
async function loadHomepageDynamicContent() {
  const featuredGrid = document.getElementById("featuredProductsGrid");
  const brandsStrip = document.getElementById("popularBrandsStrip");
  const categoriesGrid = document.getElementById("topCategoriesGrid");
  const latestGrid = document.getElementById("latestVerifiedGrid");
  if (!featuredGrid && !brandsStrip && !categoriesGrid && !latestGrid) return;

  try {
    const data = await apiRequest("/products?sort=most_scanned&limit=8");
    if (featuredGrid) {
      featuredGrid.innerHTML = data.products.length
        ? data.products.map(productCardHTML).join("")
        : '<div class="col-12 text-center text-muted-soft py-4">No products yet.</div>';
    }
    if (brandsStrip) {
      const brands = [...new Set(data.products.map((p) => p.brand))];
      brandsStrip.innerHTML = brands.map((b) => `
        <a href="products.html?brand=${encodeURIComponent(b)}" class="brand-pill">${b}</a>`).join("");
    }
  } catch (e) { /* silent */ }

  if (categoriesGrid) {
    try {
      const meta = await apiRequest("/products/meta/filters");
      const icons = { Cleanser: "fa-pump-soap", Moisturizer: "fa-droplet", Serum: "fa-flask-vial", Sunscreen: "fa-sun",
        "Night Cream": "fa-moon", "Eye Care": "fa-eye", Toner: "fa-spray-can", Exfoliant: "fa-hand-sparkles",
        "Face Oil": "fa-oil-can", "Body Lotion": "fa-bottle-droplet", "Lip Care": "fa-kiss-wink-heart",
        Mask: "fa-mask-face", "Micellar Water": "fa-water" };
      categoriesGrid.innerHTML = meta.categories.slice(0, 8).map((c) => `
        <div class="col-lg-3 col-md-4 col-6">
          <a href="products.html?category=${encodeURIComponent(c)}" class="category-tile">
            <i class="fa-solid ${icons[c] || "fa-flask"}"></i>
            <span>${c}</span>
          </a>
        </div>`).join("");
    } catch (e) { /* silent */ }
  }

  if (latestGrid) {
    try {
      const recent = await apiRequest("/verification/recent?limit=6");
      latestGrid.innerHTML = recent.history.length
        ? recent.history.map((h) => `
          <div class="col-lg-4 col-md-6">
            <div class="latest-verified-card">
              <img src="/${h.product_image || ''}" onerror="this.style.display='none'">
              <div>
                <div class="text-muted-soft" style="font-size:0.72rem;font-weight:700;text-transform:uppercase;">${h.product_brand || ''}</div>
                <div class="fw-bold">${h.product_name}</div>
                <span class="badge-status badge-genuine mt-1"><i class="fa-solid fa-circle-check"></i> Genuine</span>
              </div>
            </div>
          </div>`).join("")
        : '<div class="col-12 text-center text-muted-soft py-4">No verifications yet.</div>';
    } catch (e) { /* silent */ }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initNavbar();
  initSidebar();
  loadNotifications();
  initScrollReveal();
  loadHomepageDynamicContent();
  setInterval(loadNotifications, 20000);
});
