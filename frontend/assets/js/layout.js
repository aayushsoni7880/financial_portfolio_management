async function loadComponent(id, file) {
  const res = await fetch(file);
  const html = await res.text();
  document.getElementById(id).innerHTML = html;
}

async function initLayout() {
  await loadComponent("sidebar", "/components/sidebar.html");
  await loadComponent("header", "/components/header.html");

  setActiveNav();
}

function setActiveNav() {
  const currentPath = window.location.pathname;

  document.querySelectorAll(".nav-item").forEach(link => {
    const href = link.getAttribute("href");

    if (currentPath.includes(href)) {
      link.classList.remove("text-slate-500");

      link.classList.add(
        "bg-[#b4c5ff]/10",
        "text-[#b4c5ff]",
        "border-r-2",
        "border-[#b4c5ff]"
      );
    }
  });
}


function goToTrade() {
    window.location.href = "/pages/execute_trade.html";
}

function goToProfile() {
    window.location.href = "/pages/profile_summary.html";
}

function goToChangePassword() {
    window.location.href = "/pages/change_password.html";
}


function handleGlobalSearch(value) {
  const dashboardInput = document.getElementById("marketSearch");

  if (dashboardInput) {
    dashboardInput.value = value;
  }

  if (typeof handleMarketSearch === "function") {
    handleMarketSearch();
  }
}
