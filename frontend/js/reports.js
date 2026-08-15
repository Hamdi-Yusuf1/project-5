/* ==========================================================
   AuthenChain — Reports Module
   ========================================================== */

async function downloadReport(path, filename) {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { Authorization: `Bearer ${Auth.getToken()}` },
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ message: "Failed to generate report" }));
      throw new Error(err.message);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast("Report downloaded successfully", "success");
    loadReportsHistory();
  } catch (err) {
    showToast(err.message, "danger");
  }
}

async function loadReportsHistory() {
  const el = document.getElementById("reportsHistoryBody");
  if (!el) return;
  try {
    const data = await apiRequest("/reports");
    el.innerHTML = data.reports.length ? data.reports.map((r) => `
      <tr>
        <td><i class="fa-solid ${r.report_format === "pdf" ? "fa-file-pdf text-danger" : "fa-file-csv text-success"} me-2"></i>${r.report_type.charAt(0).toUpperCase() + r.report_type.slice(1)} Report</td>
        <td>${r.report_format.toUpperCase()}</td>
        <td>${fmtDate(r.created_at)}</td>
      </tr>`).join("") : `<tr><td colspan="3" class="text-center text-muted-soft py-4">No reports generated yet</td></tr>`;
  } catch (err) { /* optional */ }
}

async function loadReportsTable() {
  const el = document.getElementById("productsReportBody");
  if (!el) return;
  try {
    const search = document.getElementById("reportSearch")?.value || "";
    const user = Auth.getUser();
    const scopeParam = user && user.role === "manufacturer" ? "mine=true&" : "";
    const data = await apiRequest(`/products?${scopeParam}search=${encodeURIComponent(search)}`);
    el.innerHTML = data.products.length ? data.products.map((p) => `
      <tr>
        <td>${p.product_name}</td>
        <td>${p.brand}</td>
        <td>${p.batch_number}</td>
        <td>${statusBadge(p.status)}</td>
        <td>${p.scan_count}</td>
        <td>${fmtDate(p.created_at)}</td>
        <td><button class="btn btn-sm btn-outline-royal" onclick="downloadSingleProductReport(${p.id}, '${p.product_name.replace(/'/g, "\\'")}')" title="Download this product's report"><i class="fa-solid fa-file-pdf me-1"></i>Report</button></td>
      </tr>`).join("") : `<tr><td colspan="7" class="text-center text-muted-soft py-4">No products found</td></tr>`;
  } catch (err) { showToast(err.message, "danger"); }
}

async function downloadSingleProductReport(id, name) {
  await downloadReport(`/reports/product/${id}/pdf`, `${name.replace(/[^a-z0-9]/gi, "_")}_report.pdf`);
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("downloadProductsCsv")?.addEventListener("click", () => downloadReport("/reports/products/csv", "products_report.csv"));
  document.getElementById("downloadVerificationsCsv")?.addEventListener("click", () => downloadReport("/reports/verifications/csv", "verifications_report.csv"));
  document.getElementById("downloadSummaryPdf")?.addEventListener("click", () => downloadReport("/reports/summary/pdf", "summary_report.pdf"));
  document.getElementById("reportSearch")?.addEventListener("input", debounce(loadReportsTable, 350));

  loadReportsHistory();
  loadReportsTable();
  window.print && document.getElementById("printReportBtn")?.addEventListener("click", () => window.print());
});
