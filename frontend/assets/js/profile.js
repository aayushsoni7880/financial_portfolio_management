async function handleUpdatePassword() {
  const current = document.getElementById("currentPassword").value.trim();
  const next = document.getElementById("newPassword").value.trim();
  const confirm = document.getElementById("confirmPassword").value.trim();

  if (!current || !next || !confirm) {
    return toast.info("All fields are required");
  }

  if (next !== confirm) {
    return toast.error("Passwords do not match");
  }

  if (!validatePassword(next)) {
    return toast.info("Password must be strong");
  }

  try {
    const data = await api(
      "/change_password",
      "POST",
      {
        current_password: current,
        new_password: next
      }
    );

    toast.success("Password updated successfully");
    window.location.href = "/pages/profile_summary.html";

  } catch (err) {
    toast.error(err.message);
  }
}

function validatePassword(pwd) {
  return (
    pwd.length >= 8 &&
    /[A-Z]/.test(pwd) &&
    /[0-9]/.test(pwd) &&
    /[^A-Za-z0-9]/.test(pwd)
  );
}

function togglePassword(btn) {
  const input = btn.previousElementSibling;
  input.type = input.type === "password" ? "text" : "password";
}

async function loadProfile() {
  try {
    const data = await api("/profiles", "GET");

    document.getElementById("userName").innerText = data.user_name;
    document.getElementById("userEmail").innerText = data.user_email;
    document.getElementById("userId").innerText = data.user_id;

  } catch (err) {
    console.error(err);
    toast.error("Failed to load profile");
  }
}

loadProfile();


