const message = document.getElementById("message");
const detailsForm = document.getElementById("details-form");
const passwordForm = document.getElementById("password-form");

function fillDetails(profile) {
  document.getElementById("full-name").value = profile.full_name;
  document.getElementById("email").value = profile.email || "";
  document.getElementById("phone").value = `0${profile.phone.slice(3)}`;
}

async function load() {
  const result = await apiGet("/api/v1/profile");
  if (result.status === 401) {
    window.location.href = "login.html";
    return;
  }
  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  fillDetails(result.data);
}

detailsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.hidden = true;
  const button = detailsForm.querySelector("button");
  button.disabled = true;
  const result = await apiPut("/api/v1/profile", {
    full_name: document.getElementById("full-name").value,
    email: document.getElementById("email").value,
  });
  button.disabled = false;
  if (result.ok) {
    fillDetails(result.data);
    showNotice(message, "Your details were saved.", "success");
  } else {
    showNotice(message, errorText(result.data), "error");
  }
});

passwordForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.hidden = true;
  const newPassword = document.getElementById("new-password").value;
  if (newPassword !== document.getElementById("confirm-password").value) {
    showNotice(message, "The two new passwords do not match.", "error");
    return;
  }
  const button = passwordForm.querySelector("button");
  button.disabled = true;
  const result = await apiPost("/api/v1/profile/password", {
    current_password: document.getElementById("current-password").value,
    new_password: newPassword,
  });
  button.disabled = false;
  if (result.ok) {
    passwordForm.reset();
    showNotice(message, "Your password was changed. Other devices have been signed out.", "success");
  } else {
    showNotice(message, errorText(result.data), "error");
  }
});

load();
