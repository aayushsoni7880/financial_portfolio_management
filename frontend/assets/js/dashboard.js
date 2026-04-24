let IS_SEARCH_ACTIVE = false;
let CURRENT_SECTOR = "all"; // all | Technology | Energy | etc

const BTN_CLASS = `
whitespace-nowrap px-4 py-2
bg-surface-container-highest text-on-surface
rounded-md font-label text-sm
hover:bg-surface-bright transition-colors
`;


async function initDashboard() {
    if (!localStorage.getItem("access_token")) {
        window.location.href = "/pages/auth.html";
        return;
    }

    await loadSummary();
    await loadDashboardPositions();
}

function goToPositions() {
    window.location.href = "/pages/positions.html";
}

async function loadSummary() {
    try {
        const data = await api("/portfolio/summary/");

        if (!data || data.length === 0) return;

        let totalInvested = 0;
        let currentValue = 0;
        let totalPnl = 0;

        data.forEach(item => {
            totalInvested += item.invested_value;
            currentValue += item.current_value;
            totalPnl += item.unrealized_pnl;
        });

        const pnlPct = (totalPnl / totalInvested) * 100;

        document.getElementById("current_value_display").innerText =
            formatCurrency(currentValue);

        document.getElementById("total_invested_display").innerText =
            formatCurrency(totalInvested);

        document.getElementById("unrealized_pnl_display").innerText =
            formatCurrency(totalPnl);

        document.getElementById("unrealized_pnl_pct_display").innerText =
            `(${pnlPct.toFixed(2)}%)`;

    } catch (err) {
        console.error("Summary load failed:", err.message);
    }
}

async function loadDashboardPositions() {
    try {
        const data = await api("/positions");

        const tbody = document.getElementById("positions_table_body");
        tbody.innerHTML = "";

        const top5 = data.slice(0, 5);

        top5.forEach(p => {
            const pnl = (p.last_price - p.avg_price) * p.quantity;
            const pnlPct = ((p.last_price - p.avg_price) / p.avg_price) * 100;

            const pnlColor = pnl >= 0 ? "text-secondary" : "text-tertiary";

            const row = `
                <tr class="hover:bg-surface-container-high transition-colors duration-150 group cursor-pointer">
                    <td class="py-5 px-6">
                        <div class="flex items-center gap-4">
                            <div class="w-10 h-10 rounded-full bg-surface-container-highest flex items-center justify-center font-headline font-bold text-primary">
                                ${p.symbol[0]}
                            </div>
                            <div>
                                <div class="font-headline font-semibold text-base group-hover:text-primary transition-colors">
                                    ${p.symbol}
                                </div>
                            </div>
                        </div>
                    </td>
                    <td class="py-5 px-6 text-right font-medium">${p.quantity}</td>
                    <td class="py-5 px-6 text-right text-on-surface-variant">
                        ${formatCurrency(p.avg_price)}
                    </td>
                    <td class="py-5 px-6 text-right font-medium">
                        ${formatCurrency(p.last_price)}
                    </td>
                    <td class="py-5 px-6 text-right">
                        <div class="${pnlColor} font-semibold">
                            ${formatCurrency(pnl)}
                        </div>
                        <div class="text-xs ${pnlColor}/80 mt-0.5">
                            ${pnlPct.toFixed(2)}%
                        </div>
                    </td>
                </tr>
            `;

            tbody.innerHTML += row;
        });

    } catch (err) {
        toast.error("Positions load failed:", err.message);
    }
}

function formatCurrency(value) {
    return "$" + Number(value).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

let ALL_STOCKS = [];
let currentIndex = 0;
const PAGE_SIZE = 6;

async function loadStocks() {
  try {
    const res = await api("/stocks");

    ALL_STOCKS = res.data || res;

    extractSectors();        // ✅ NEW
    renderSectorFilters();   // ✅ NEW

    currentIndex = 0;
    applyFilters();          // instead of renderNextStocks

  } catch (err) {
    toast.error("Failed to load stocks");
  }
}

function renderNextStocks(reset = false) {
  const container = document.getElementById("stocksGrid");

  if (reset) {
    container.innerHTML = "";

      if (IS_SEARCH_ACTIVE && FILTERED_STOCKS.length === 0) {
        container.innerHTML = `
          <div class="col-span-full text-center text-slate-400 py-10">
            No stocks found
          </div>
        `;
        document.getElementById("loadMoreBtn").style.display = "none";
        return;
      }
  }

  const source = (IS_SEARCH_ACTIVE || CURRENT_SECTOR !== "all")
  ? FILTERED_STOCKS
  : ALL_STOCKS;
  const nextBatch = source.slice(currentIndex, currentIndex + PAGE_SIZE);

  const html = nextBatch.map(stock => `
    <article class="bg-surface-container-low rounded-xl p-6 flex flex-col gap-4 hover:bg-surface-container-high transition-colors duration-300 group cursor-pointer relative overflow-hidden shadow-[0_8px_40px_rgba(0,0,0,0.06)] border-none">
<!-- Decorative subtle gradient glow -->
<div class="absolute -top-10 -right-10 w-32 h-32 bg-secondary/5 rounded-full blur-2xl group-hover:bg-secondary/10 transition-colors"></div>
<div class="flex justify-between items-start z-10">
<div>
<h2 class="font-headline text-xl font-semibold text-on-surface">${stock.symbol}</h2>
<p class="font-body text-sm text-on-surface-variant mt-1">${stock.name || ""}</p>
</div>
<div class="flex items-center gap-1 bg-surface-container-highest px-2 py-1 rounded text-xs font-label text-on-surface-variant">
<span class="w-1.5 h-1.5 rounded-full bg-secondary animate-pulse"></span>
                        Live
                    </div>
</div>
<div class="flex flex-col gap-2 z-10 mt-2">
<div class="flex justify-between items-center border-b border-outline-variant/10 pb-2">
<span class="font-label text-xs text-on-surface-variant uppercase tracking-wider">Sector</span>
<span class="font-body text-sm text-on-surface">${stock.sector}</span>
</div>
<div class="flex justify-between items-center pt-1">
<span class="font-label text-xs text-on-surface-variant uppercase tracking-wider">Industry</span>
<span class="font-body text-sm text-on-surface">${stock.industry}</span>
</div>
</div>
<div class="mt-4 z-10 flex items-center justify-between">
<div class="flex flex-col">
<span class="font-headline text-lg font-bold text-on-surface">₹ ${stock.price}</span>
<span class="font-body text-sm text-secondary flex items-center gap-1">
<span class="material-symbols-outlined text-[16px]" data-icon="arrow_upward">arrow_upward</span>
                            ${stock.change >= 0 ? "▲" : "▼"} ${stock.change || 0}%
                        </span>
</div>
<button onclick="viewStock('${stock.symbol}')" class="px-4 py-2 bg-transparent text-primary hover:bg-primary/10 rounded-md font-label text-sm transition-colors border border-primary/20 group-hover:border-primary/50">View Details</button>
</div>
</article>
  `).join("");

  container.insertAdjacentHTML("beforeend", html);

  currentIndex += PAGE_SIZE;

  updateLoadMoreButton();
}

function viewStock(symbol) {
  window.location.href = `/pages/stock_detail.html?symbol=${symbol}`;
}

function updateLoadMoreButton() {
  const btn = document.getElementById("loadMoreBtn");
  const source = IS_SEARCH_ACTIVE ? FILTERED_STOCKS : ALL_STOCKS;

  if (currentIndex >= source.length) {
    btn.style.display = "none";
  } else {
    btn.style.display = "block";
  }
}

let FILTERED_STOCKS = [];

function handleMarketSearch() {
  CURRENT_SEARCH = document.getElementById("marketSearch").value.trim().toUpperCase();
  IS_SEARCH_ACTIVE = !!CURRENT_SEARCH;

  currentIndex = 0;

  applyFilters();
}
function closeSectorDropdown() {
  const dropdowns = document.querySelectorAll("#sectorDropdown");
  dropdowns.forEach(d => d.classList.add("hidden"));
}

function setSector(sector) {
  CURRENT_SECTOR = sector;
  currentIndex = 0;

  updateActiveSectorUI(sector);
  applyFilters();

  closeSectorDropdown(); // 🔥 better
}

function applyFilters() {
  let data = [...ALL_STOCKS];

  // 🔍 SEARCH
  if (IS_SEARCH_ACTIVE) {
    data = data.filter(stock =>
      stock.symbol.toUpperCase().includes(CURRENT_SEARCH) ||
      (stock.name || "").toUpperCase().includes(CURRENT_SEARCH)
    );
  }

  // 🎯 SECTOR FILTER
  if (CURRENT_SECTOR !== "all") {
    data = data.filter(stock =>
      (stock.sector || "").toLowerCase() === CURRENT_SECTOR.toLowerCase()
    );
  }

  FILTERED_STOCKS = data;

  renderNextStocks(true);
}

function updateActiveSectorUI(selected) {
  document.querySelectorAll(".btn-filter").forEach(btn => {
    btn.classList.remove("btn-filter-active");

    if (btn.innerText.trim() === selected ||
        (selected === "all" && btn.innerText.includes("All"))) {
      btn.classList.add("btn-filter-active");
    }
  });
}
function renderSectorFilters() {
  const container = document.getElementById("sectorFilters");
  const dropdown = document.getElementById("sectorDropdown");

  const sectorMap = {};

  ALL_STOCKS.forEach(s => {
    if (!s.sector) return;
    sectorMap[s.sector] = (sectorMap[s.sector] || 0) + 1;
  });

  const sectors = Object.keys(sectorMap)
    .sort((a, b) => sectorMap[b] - sectorMap[a]);

  const top = sectors.slice(0, 5);
  const more = sectors.slice(5);

  container.innerHTML = `
    ${top.map(sec => `
      <button onclick="setSector('${sec}')"
        class="btn-filter">
        ${sec}
      </button>
    `).join("")}

    ${more.length ? `
      <button onclick="toggleSectorDropdown()" class="btn-filter flex items-center gap-1">
        More
        <span class="material-symbols-outlined text-sm">expand_more</span>
      </button>
    ` : ""}
  `;

  // 🔥 Populate dropdown separately
  dropdown.innerHTML = more.map(sec => `
    <div onclick="setSector('${sec}')"
      class="px-4 py-2 hover:bg-surface-container-highest cursor-pointer">
      ${sec}
    </div>
  `).join("");
}

function toggleSectorDropdown() {
  document.getElementById("sectorDropdown").classList.toggle("hidden");
}


function extractSectors() {
  const sectorMap = {};

  ALL_STOCKS.forEach(s => {
    if (!s.sector) return;

    sectorMap[s.sector] = (sectorMap[s.sector] || 0) + 1;
  });

  // sort by frequency (top sectors first)
  ALL_SECTORS = Object.entries(sectorMap)
    .sort((a, b) => b[1] - a[1])
    .map(([sector]) => sector);
}