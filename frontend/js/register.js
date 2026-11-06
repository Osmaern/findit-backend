const form = document.getElementById("register-form");
const message = document.getElementById("message");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(form));

  if (values.password !== values.confirm) {
    showNotice(message, "The passwords do not match.", "error");
    return;
  }

  const button = form.querySelector("button.primary");
  button.disabled = true;
  const result = await apiPost("/api/v1/auth/register", {
    full_name: values.full_name.trim(),
    email: values.email.trim(),
    phone: values.phone.trim(),
    password: values.password,
  });
  button.disabled = false;

  if (result.ok) {
    sessionStorage.setItem("pendingPhone", values.phone.trim());
    window.location.href = "verify.html";
  } else {
    showNotice(message, errorText(result.data), "error");
  }
});
