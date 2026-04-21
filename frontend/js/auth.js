async function login() {
    const res = await apiRequest("/login", "POST", {
        user_name: document.getElementById("login_user").value,
        password: document.getElementById("login_pass").value
    }, false);

    handleAuthResponse(res);
}


async function signup() {
    const res = await apiRequest("/signup", "POST", {
        user_name: document.getElementById("signup_user").value,
        email: document.getElementById("signup_email").value,
        password: document.getElementById("signup_pass").value
    }, false);

    handleAuthResponse(res);
}

async function resetPassword() {
    const res = await apiRequest("/reset_password", "POST", {
        email: document.getElementById("reset_email").value
    }, false);

    document.getElementById("message").innerText = res.message;
}

function handleAuthResponse(res) {
    const msg = document.getElementById("message");

    if (res.success) {
        msg.innerText = res.message;

        if (res.access_token) {
            localStorage.setItem("access_token", res.access_token);
            localStorage.setItem("refresh_token", res.refresh_token);
            window.location.href = "/dashboard.html";
        }
    } else {
        msg.innerText = res.message;
    }
}

function switchTab(tab) {
    ["login", "signup", "reset"].forEach(t => {
        document.getElementById(t + "View").classList.add("hidden");
    });

    document.getElementById(tab + "View").classList.remove("hidden");
}