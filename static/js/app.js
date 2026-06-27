/* ==========================================================================
   Smart Parking System — shared front-end behaviors
   ========================================================================== */

// --- Mobile sidebar toggle ---
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".mobile-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (
        sidebar.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        !toggle.contains(e.target)
      ) {
        sidebar.classList.remove("open");
      }
    });
  }

  // --- Auto-dismiss flash messages ---
  document.querySelectorAll(".flash").forEach((el, i) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.3s ease";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 300);
    }, 4500 + i * 200);
  });

  // --- Dark mode toggle ---
  const darkToggle = document.querySelector("#darkModeToggle");
  const root = document.documentElement;
  const stored = sessionStorage.getItem("spms-theme"); // session-only; no persistent browser storage relied upon for core function
  if (stored === "dark") root.classList.add("dark-mode");
  if (darkToggle) {
    darkToggle.addEventListener("click", () => {
      root.classList.toggle("dark-mode");
      sessionStorage.setItem("spms-theme", root.classList.contains("dark-mode") ? "dark" : "light");
    });
  }

  // --- File upload preview (OCR upload page) ---
  const fileInput = document.querySelector("#plateImageInput");
  const previewImg = document.querySelector("#plateImagePreview");
  const previewWrap = document.querySelector("#plateImagePreviewWrap");
  if (fileInput && previewImg) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        if (previewWrap) previewWrap.style.display = "block";
      };
      reader.readAsDataURL(file);
    });
  }

  // --- Live vehicle search (admin) ---
  const searchInput = document.querySelector("#liveVehicleSearch");
  const searchResults = document.querySelector("#liveVehicleSearchResults");
  if (searchInput && searchResults) {
    let debounceTimer;
    searchInput.addEventListener("input", () => {
      clearTimeout(debounceTimer);
      const q = searchInput.value.trim();
      if (!q) {
        searchResults.innerHTML = "";
        searchResults.style.display = "none";
        return;
      }
      debounceTimer = setTimeout(async () => {
        try {
          const res = await fetch(`/api/search/vehicles?q=${encodeURIComponent(q)}`);
          const data = await res.json();
          if (!data.length) {
            searchResults.innerHTML = `<div class="empty-state" style="padding:20px;"><p>No vehicles found.</p></div>`;
          } else {
            searchResults.innerHTML = data
              .map(
                (v) => `
                <a href="/admin/vehicles/${v.id}" class="data-table-search-row" style="display:flex;justify-content:space-between;padding:10px 14px;border-bottom:1px solid #F1EFE8;">
                  <span><strong class="mono">${v.vehicle_number}</strong> &middot; ${v.owner_name}</span>
                  <span class="chip ${v.compliance_status === 'Valid' ? 'chip-go' : v.compliance_status === 'Expired' ? 'chip-stop' : 'chip-warn'}">${v.compliance_status}</span>
                </a>`
              )
              .join("");
          }
          searchResults.style.display = "block";
        } catch (err) {
          console.error("Search failed:", err);
        }
      }, 250);
    });
  }
});

// --- Chart.js helpers: shared default styling ---
function spmsChartDefaults() {
  if (typeof Chart === "undefined") return;
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.color = "#6B7280";
  Chart.defaults.plugins.legend.labels.boxWidth = 10;
  Chart.defaults.plugins.legend.labels.boxHeight = 10;
}
