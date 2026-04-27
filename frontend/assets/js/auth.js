// assets/js/auth.js
function initLogin() {
    document.querySelector("form").addEventListener("submit", async (e) => {
        e.preventDefault();

        const user_id = document.getElementById("userid").value;
        const password = document.getElementById("password").value;

        const res = await api("/login", "POST", { user_id, password });

        if (res.success) {
            localStorage.setItem("access_token", res.access_token);
            localStorage.setItem("refresh_token", res.refresh_token);
            window.location.href = "/pages/summary.html";
        } else {
            toast.error(res.message);
        }
    });
}

function goToSignup() {
    window.location.href = "/pages/create_account.html";
}

function initResetPassword() {
    const form = document.getElementById("resetPasswordForm");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email_address = document.getElementById("email").value;

        try {
            const res = await api("/reset_password", "POST", {
                email_address
            });

            if (res.success) {
                // show success UI
                document.getElementById("successMessage").classList.remove("hidden");

                // optional: hide form
                form.classList.add("hidden");
            } else {
                toast.error(res.message || "Failed to send reset link");
            }
        } catch (err) {
            toast.error("Error sending reset link");
        }
    });
}

function initSignup() {
    const form = document.getElementById("signupForm");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const user_name = document.getElementById("username").value;
        const email_address = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
            const res = await api("/signup", "POST", {
                user_name,
                email_address,
                password
            });

            if (res.success) {
                toast.success("Account created successfully");

                // redirect to login
                window.location.href = "/pages/auth.html";
            } else {
                toast.error(res.message || "Signup failed");
            }

        } catch (err) {
            toast.error("Error creating account");
        }
    });
}

function logout() {
    localStorage.clear();
    window.location.href = "/pages/auth.html";
}

// 👇 expose globally
window.logout = logout;
