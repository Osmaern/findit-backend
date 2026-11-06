// Shared helpers for all FindIt pages.

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
