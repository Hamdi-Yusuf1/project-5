/* ==========================================================
   AuthenChain — Auth Pages Logic (login / register / forgot)
   ========================================================== */

function redirectToDashboard(role) {
  const map = { manufacturer: "manufacturer-dashboard.html", consumer: "consumer-dashboard.html", admin: "admin-dashboard.html" };
  window.location.href = map[role] || "index.html";
}

document.addEventListener("DOMContentLoaded", () => {
  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    if (user && window.location.pathname.includes("login")) redirectToDashboard(user.role);
  }

  /* ---------- Role tabs (login page) ---------- */
  const roleCards = document.querySelectorAll(".role-select-card");
  const roleInput = document.getElementById("loginRole");
  roleCards.forEach((card) => {
    card.addEventListener("click", () => {
      roleCards.forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      if (roleInput) roleInput.value = card.dataset.role;
    });
  });

  /* ---------- Login form ---------- */
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector("button[type=submit]");
      const original = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Signing in...`;

      try {
        const payload = {
          email: document.getElementById("loginEmail").value.trim(),
          password: document.getElementById("loginPassword").value,
          role: roleInput ? roleInput.value : undefined,
        };
        const data = await apiRequest("/auth/login", { method: "POST", body: payload, auth: false });
        Auth.setToken(data.token);
        Auth.setUser(data.user);
        showToast("Welcome back, " + data.user.full_name.split(" ")[0] + "!", "success");
        setTimeout(() => redirectToDashboard(data.user.role), 600);
      } catch (err) {
        showToast(err.message, "danger");
        btn.disabled = false;
        btn.innerHTML = original;
      }
    });
  }

  /* ---------- Register form ---------- */
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    const roleToggle = document.querySelectorAll("[data-register-role]");
    const companyGroup = document.getElementById("companyNameGroup");
    let selectedRole = "consumer";

    roleToggle.forEach((btn) => {
      btn.addEventListener("click", () => {
        roleToggle.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        selectedRole = btn.dataset.registerRole;
        if (companyGroup) companyGroup.style.display = selectedRole === "manufacturer" ? "block" : "none";
      });
    });

    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const password = document.getElementById("regPassword").value;
      const confirm = document.getElementById("regConfirmPassword").value;
      if (password !== confirm) { showToast("Passwords do not match", "danger"); return; }

      const btn = registerForm.querySelector("button[type=submit]");
      const original = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Creating account...`;

      try {
        const payload = {
          full_name: document.getElementById("regName").value.trim(),
          email: document.getElementById("regEmail").value.trim(),
          phone: document.getElementById("regPhone").value.trim(),
          password,
          role: selectedRole,
          company_name: document.getElementById("regCompany")?.value.trim() || "",
        };
        const data = await apiRequest("/auth/register", { method: "POST", body: payload, auth: false });
        Auth.setToken(data.token);
        Auth.setUser(data.user);
        showToast("Account created successfully!", "success");
        setTimeout(() => redirectToDashboard(data.user.role), 600);
      } catch (err) {
        showToast(err.message, "danger");
        btn.disabled = false;
        btn.innerHTML = original;
      }
    });
  }

  /* ---------- Forgot password form ---------- */
  const forgotForm = document.getElementById("forgotForm");
  if (forgotForm) {
    forgotForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      try {
        const email = document.getElementById("forgotEmail").value.trim();
        const data = await apiRequest("/auth/forgot-password", { method: "POST", body: { email }, auth: false });
        document.getElementById("forgotResult").innerHTML = `
          <div class="alert alert-success mt-3">
            ${data.message}
            ${data.reset_token ? `<div class="mt-2"><small>Demo reset token: <code>${data.reset_token.slice(0, 40)}...</code></small></div>` : ""}
          </div>`;
      } catch (err) {
        showToast(err.message, "danger");
      }
    });
  }
});
