/* ==========================================================
   AuthenChain — Profile Module
   ========================================================== */

async function loadProfile() {
  const form = document.getElementById("profileForm");
  if (!form) return;
  try {
    const data = await apiRequest("/auth/me");
    const u = data.user;
    document.getElementById("profileName").value = u.full_name;
    document.getElementById("profileEmail").value = u.email;
    document.getElementById("profilePhone").value = u.phone || "";
    if (document.getElementById("profileCompany")) document.getElementById("profileCompany").value = u.company_name || "";
    document.getElementById("profileAvatarText").textContent = u.full_name.charAt(0).toUpperCase();
    document.getElementById("profileRoleBadge").textContent = u.role.charAt(0).toUpperCase() + u.role.slice(1);
    if (u.profile_image) {
      const img = document.getElementById("profileAvatarImg");
      img.src = `/${u.profile_image}`;
      img.classList.remove("d-none");
      document.getElementById("profileAvatarText").classList.add("d-none");
    }
  } catch (err) { showToast(err.message, "danger"); }
}

document.addEventListener("DOMContentLoaded", () => {
  loadProfile();

  const form = document.getElementById("profileForm");
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("full_name", document.getElementById("profileName").value);
    fd.append("phone", document.getElementById("profilePhone").value);
    if (document.getElementById("profileCompany")) fd.append("company_name", document.getElementById("profileCompany").value);
    const file = document.getElementById("profileImageInput")?.files[0];
    if (file) fd.append("profile_image", file);

    try {
      const data = await apiRequest("/auth/profile", { method: "PUT", body: fd, isForm: true });
      Auth.setUser(data.user);
      showToast("Profile updated successfully", "success");
    } catch (err) { showToast(err.message, "danger"); }
  });

  const pwForm = document.getElementById("passwordForm");
  pwForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const current_password = document.getElementById("currentPassword").value;
    const new_password = document.getElementById("newPassword").value;
    const confirm = document.getElementById("confirmNewPassword").value;
    if (new_password !== confirm) { showToast("New passwords do not match", "danger"); return; }
    try {
      await apiRequest("/auth/change-password", { method: "PUT", body: { current_password, new_password } });
      showToast("Password changed successfully", "success");
      pwForm.reset();
    } catch (err) { showToast(err.message, "danger"); }
  });
});
