const form = document.getElementById("verify-form");
const message = document.getElementById("message");
const phoneInput = document.getElementById("phone");
const resendButton = document.getElementById("resend");

phoneInput.value = sessionStorage.getItem("pendingPhone") || "";

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const phone = phoneInput.value.trim();
  const code = document.getElementById("code").value.trim();

  const button = form.querySelector("button.primary");
  button.disabled = true;
  const result = await apiPost("/api/v1/auth/verify-phone", { phone, code });
  button.disabled = false;

  if (result.ok) {
    sessionStorage.removeItem("pendingPhone");
    showNotice(message, "Your phone is verified. You can now log in.", "success");
    form.reset();
  } else {
    showNotice(message, errorText(result.data), "error");
  }
});

resendButton.addEventListener("click", async () => {
  const phone = phoneInput.value.trim();
  resendButton.disabled = true;
  const result = await apiPost("/api/v1/auth/resend-code", { phone });
  if (result.ok) {
    showNotice(message, "A new code has been sent to your phone.", "success");
    setTimeout(() => { resendButton.disabled = false; }, 60000);
  } else {
    resendButton.disabled = false;
    showNotice(message, errorText(result.data), "error");
  }
});
