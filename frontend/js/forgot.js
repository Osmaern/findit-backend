const phoneForm = document.getElementById("phone-form");
const resetForm = document.getElementById("reset-form");
const resendButton = document.getElementById("resend");
const message = document.getElementById("message");
const subtitle = document.getElementById("subtitle");
const phoneInput = document.getElementById("phone");

let phone = "";

function startResendTimer() {
  resendButton.disabled = true;
  setTimeout(() => { resendButton.disabled = false; }, 60000);
}

// Step 1: ask for a code. The answer is the same for every number, so we always move on to step 2.
phoneForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  phone = phoneInput.value.trim();
  const button = phoneForm.querySelector("button.primary");
  button.disabled = true;
  const result = await apiPost("/api/v1/auth/forgot-password", { phone });
  button.disabled = false;

  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  phoneForm.hidden = true;
  resetForm.hidden = false;
  resendButton.hidden = false;
  subtitle.textContent = "If that number has an account, a code is on its way. Enter it below with your new password. The code expires in 10 minutes.";
  showNotice(message, "Check your SMS for the code.", "success");
  startResendTimer();
  document.getElementById("code").focus();
});

// Step 2: send the code and the new password.
resetForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = document.getElementById("code").value.trim();
  const password = document.getElementById("new-password").value;
  const confirm = document.getElementById("confirm").value;

  if (password.length < 8) {
    showNotice(message, "Your new password must be at least 8 characters.", "error");
    return;
  }
  if (password !== confirm) {
    showNotice(message, "The two passwords do not match.", "error");
    return;
  }

  const button = resetForm.querySelector("button.primary");
  button.disabled = true;
  const result = await apiPost("/api/v1/auth/reset-password", { phone, code, new_password: password });
  button.disabled = false;

  if (result.ok) {
    sessionStorage.setItem("passwordReset", "1");
    window.location.href = "login.html";
  } else {
    showNotice(message, errorText(result.data), "error");
  }
});

resendButton.addEventListener("click", async () => {
  resendButton.disabled = true;
  const result = await apiPost("/api/v1/auth/forgot-password", { phone });
  if (result.ok) {
    showNotice(message, "If that number has an account, a new code has been sent.", "success");
    startResendTimer();
  } else {
    resendButton.disabled = false;
    showNotice(message, errorText(result.data), "error");
  }
});
