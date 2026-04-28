// assets/js/api.js

let isRefreshing = false;
let refreshPromise = null;

async function api(path, method = "GET", body = null) {
    let token = localStorage.getItem("access_token");

    try {
        return await fetchWithToken(path, method, body, token);
    } catch (err) {
        // 👇 Only handle token expiry
        if (err.status === 401) {
            await refreshTokenFlow();

            // retry original request with new token
            const newToken = localStorage.getItem("access_token");
            return fetchWithToken(path, method, body, newToken);
        }

        throw err;
    }
}

async function fetchWithToken(path, method, body, token) {
    const res = await fetch(CONFIG.BASE_URL + path, {
        method,
        headers: {
            "Content-Type": "application/json",
            ...(token && { Authorization: "Bearer " + token })
        },
        body: body ? JSON.stringify(body) : null
    });

    const data = await res.json();

    if (!res.ok) {
        const error = new Error(data.detail || "API Error");
        error.status = res.status;
        throw error;
    }

    return data;
}

async function refreshTokenFlow() {
    if (isRefreshing) {
        return refreshPromise; // wait for ongoing refresh
    }

    isRefreshing = true;

    refreshPromise = (async () => {
        try {
            const access = localStorage.getItem("access_token");
            const refresh = localStorage.getItem("refresh_token");

            const res = await fetch(CONFIG.BASE_URL + "/refresh_token", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    access_token: access,
                    refresh_token: refresh
                })
            });

            if (!res.ok) {
                throw new Error("Refresh failed");
            }

            const data = await res.json();

            // 🔥 Save new token
            localStorage.setItem("access_token", data.access_token);

        } catch (err) {
            // ❌ refresh failed → logout
            toast.error("Session expired. Please login again.");
            localStorage.clear();
            setTimeout(() => {
               window.location.href = "/pages/auth.html";
            }, 500); // 1.5 seconds delay

        } finally {
            isRefreshing = false;
        }
    })();

    return refreshPromise;
}

document.addEventListener("click", function (e) {
  if (e.target.closest("#menuBtn")) {
    const sidebar = document.querySelector("aside");
    const btn = document.getElementById("menuBtn");

    if (!sidebar || !btn) return;

    sidebar.classList.toggle("-translate-x-full");
  }
});



function toggleSidebar() {
  const sidebar = document.querySelector("aside");

  if (!sidebar) return;

  sidebar.classList.toggle("-translate-x-full");
}
