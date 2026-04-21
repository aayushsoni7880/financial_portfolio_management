const BASE_URL = "http://localhost:8080/api";

async function apiRequest(endpoint, method = "GET", body = null, auth = true) {
    const headers = {
        "Content-Type": "application/json"
    };

    if (auth) {
        headers["Authorization"] = "Bearer " + localStorage.getItem("access_token");
    }

    const res = await fetch(BASE_URL + endpoint, {
        method,
        headers,
        body: body ? JSON.stringify(body) : null
    });

    return res.json();
}