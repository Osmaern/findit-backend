// Shared helpers for all FindIt pages.

async function apiPut(path, body) {
  const response = await fetch(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "same-origin",
  });
  let data = null;
  try { data = await response.json(); } catch (_) { /* empty or non-JSON body */ }
  return { ok: response.ok, status: response.status, data };
}

async function apiPost(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    credentials: "same-origin",
  });
  let data = null;
  try { data = await response.json(); } catch (_) { /* empty or non-JSON body */ }
  return { ok: response.ok, status: response.status, data };
}

function errorText(data) {
  if (!data) return "Something went wrong. Please try again.";
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg.replace(/^Value error, /, "")).join(". ");
  }
  return data.detail || "Something went wrong. Please try again.";
}

function showNotice(el, text, kind) {
  el.textContent = text;
  el.className = "notice " + kind;
  el.hidden = false;
}

// Show/hide password buttons: <button type="button" class="toggle" data-toggle="fieldId">
document.querySelectorAll("[data-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.toggle);
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    button.textContent = showing ? "Show" : "Hide";
  });
});

async function apiGet(path) {
  const response = await fetch(path, { credentials: "same-origin" });
  let data = null;
  try { data = await response.json(); } catch (_) { /* no body */ }
  return { ok: response.ok, status: response.status, data };
}

async function apiUpload(path, formData) {
  const response = await fetch(path, { method: "POST", body: formData, credentials: "same-origin" });
  let data = null;
  try { data = await response.json(); } catch (_) { /* no body */ }
  return { ok: response.ok, status: response.status, data };
}

// Labels shared by all item pages (values must match the backend)
const CATEGORY_LABELS = {
  phone: "Phone", bag: "Bag", wallet: "Wallet", keys: "Keys", id_card: "ID card",
  electronics: "Electronics", clothing: "Clothing", books: "Books", other: "Other",
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

// Shows Logout instead of Login when someone is signed in
async function setupNav() {
  const loginLink = document.getElementById("nav-login");
  const logoutLink = document.getElementById("nav-logout");
  if (!logoutLink) return;
  if (loginLink) loginLink.hidden = true;
  const me = await apiGet("/api/v1/auth/me");
  if (me.ok) {
    logoutLink.hidden = false;
    window.currentUser = me.data;
  }
}

document.addEventListener("click", async (event) => {
  const link = event.target.closest("#nav-logout");
  if (!link) return;
  event.preventDefault();
  await apiPost("/api/v1/auth/logout", {});
  window.location.href = "login.html";
});

setupNav();
