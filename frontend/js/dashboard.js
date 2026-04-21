// ---------------- VIEW SWITCH ----------------
function showView(view, event) {
    ["positions", "transactions", "summary"].forEach(v => {
        document.getElementById(v + "View").classList.add("hidden");
    });

    document.getElementById(view + "View").classList.remove("hidden");

    document.querySelectorAll(".sidebar li").forEach(li => {
        li.classList.remove("active");
    });

    if (event) event.target.classList.add("active");
}

// ---------------- LOGOUT ----------------
function logout() {
    localStorage.clear();
    window.location.href = "/login.html";
}

// ---------------- POSITIONS ----------------
async function loadPositions() {
    const data = await apiRequest("/positions");

    const table = document.getElementById("positions");
    table.innerHTML = "";

    data.forEach(p => {
        table.innerHTML += `
        <tr>
            <td>${p.symbol}</td>
            <td>${p.quantity}</td>
            <td>${p.avg_price}</td>
            <td>${p.last_price}</td>
        </tr>`;
    });
}

// ---------------- TRANSACTIONS ----------------
async function loadTransactions() {
    const data = await apiRequest("/transactions");

    const table = document.getElementById("transactions");
    table.innerHTML = "";

    data.forEach(t => {
        table.innerHTML += `
        <tr>
            <td>${t.symbol}</td>
            <td>${t.quantity}</td>
            <td>${t.price}</td>
            <td>${t.type}</td>
        </tr>`;
    });
}

// ---------------- SUMMARY ----------------
async function loadSummary() {
    const data = await apiRequest("/portfolio/summary/");
    const container = document.getElementById("summaryView");

    container.innerHTML = `<h2>Portfolio Summary</h2>`;

    // CASE 1: Small → cards
    if (data.length <= 3) {
        data.forEach(item => {
            container.innerHTML += `
                <div class="summary-card">
                    <h3>${item.symbol}</h3>
                    <p>Qty: ${item.quantity}</p>
                    <p>P&L:
                        <span style="color:${item.unrealized_pnl >= 0 ? 'lime' : 'red'}">
                            ${item.unrealized_pnl.toFixed(2)}
                        </span>
                    </p>
                </div>
            `;
        });
        return;
    }

    container.innerHTML += `<canvas id="pnlChart"></canvas>`;

    // CASE 2: Medium → doughnut
    if (data.length <= 10) {
        const labels = data.map(x => x.symbol);
        const values = data.map(x => Math.abs(x.unrealized_pnl));

        new Chart(document.getElementById("pnlChart"), {
            type: "doughnut",
            data: {
                labels,
                datasets: [{
                    data: values,
                    borderWidth: 0
                }]
            },
            options: {
                cutout: "70%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#fff" }
                    }
                }
            },
            plugins: [{
                id: 'centerText',
                beforeDraw(chart) {
                    const {ctx, width, height} = chart;
                    ctx.save();
                    ctx.font = "bold 16px sans-serif";
                    ctx.fillStyle = "white";
                    ctx.textAlign = "center";

                    const total = values.reduce((a, b) => a + b, 0).toFixed(2);
                    ctx.fillText(`₹${total}`, width / 2, height / 2);
                }
            }]
        });

        return;
    }

    // CASE 3: Large → horizontal bar
    const labels = data.map(x => x.symbol);
    const pnl = data.map(x => x.unrealized_pnl);

    new Chart(document.getElementById("pnlChart"), {
        type: "bar",
        data: {
            labels,
            datasets: [{
                data: pnl,
                backgroundColor: pnl.map(v => v >= 0 ? "#22c55e" : "#ef4444")
            }]
        },
        options: {
            indexAxis: "y",
            plugins: { legend: { display: false } }
        }
    });
}

// ---------------- STOCKS ----------------
let STOCKS = [];

async function loadStocks() {
    STOCKS = await apiRequest("/stocks", "GET", null, false);
}

function searchStock() {
    const query = document.getElementById("symbolInput").value.toUpperCase();
    const list = document.getElementById("stockList");

    list.innerHTML = "";

    if (!query) return;

    STOCKS.filter(s => s.symbol.includes(query)).slice(0, 10)
        .forEach(s => {
            list.innerHTML += `<div onclick="selectStock('${s.symbol}')">${s.symbol}</div>`;
        });
}

function selectStock(symbol) {
    document.getElementById("symbolInput").value = symbol;
    document.getElementById("stockList").innerHTML = "";
}

// ---------------- CREATE TRANSACTION ----------------
async function createTransaction() {
    const symbol = document.getElementById("symbolInput").value;
    const quantity = Number(document.getElementById("qty").value);
    const price = Number(document.getElementById("price").value);
    const type = document.getElementById("type").value;

    if (!symbol || !quantity || !price) {
        alert("Fill all fields");
        return;
    }

    await apiRequest("/transactions", "POST", {
        symbol,
        quantity,
        price,
        type
    });

    alert("Trade added!");

    loadPositions();
    loadTransactions();
    loadSummary();
}

// ---------------- INIT ----------------
document.addEventListener("DOMContentLoaded", () => {
    loadStocks();
    loadPositions();
    loadTransactions();
    loadSummary();
});