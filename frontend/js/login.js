const form = document.getElementById("login-form");
const message = document.getElementById("message");
const phoneInput = document.getElementById("phone");
const rememberBox = document.getElementById("remember");

// Sent here by the forgot-password page after a successful reset
if (sessionStorage.getItem("passwordReset")) {
  sessionStorage.removeItem("passwordReset");
  showNotice(message, "Your password was changed. Log in with your new password.", "success");
}

// "Remember me" keeps only the phone number on this device.
// Keeping a login alive for weeks needs refresh tokens, which are not built yet.
const remembered = localStorage.getItem("rememberedPhone");
if (remembered) {
  phoneInput.value = remembered;
  rememberBox.checked = true;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const phone = phoneInput.value.trim();
  const password = document.getElementById("password").value;

  const button = form.querySelector("button.primary");
  button.disabled = true;
  const result = await apiPost("/api/v1/auth/login", { phone, password });
  button.disabled = false;

  if (result.ok) {
    if (rememberBox.checked) localStorage.setItem("rememberedPhone", phone);
    else localStorage.removeItem("rememberedPhone");
    window.location.href = "dashboard.html";
  } else {
    showNotice(message, errorText(result.data), "error");
  }
});
