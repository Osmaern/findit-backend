const form = document.getElementById("item-form");
const message = document.getElementById("message");
const categorySelect = document.getElementById("category");
const privateInput = document.getElementById("private_detail");
const privateHelp = document.getElementById("private-help");
const privateRequired = document.getElementById("private-required");
const photoInput = document.getElementById("photos");
const previews = document.getElementById("previews");
const dateInput = document.getElementById("event_date");
const MAX_PHOTO_BYTES = 3_000_000;

// Dates in the future are not allowed; use the local date
const now = new Date();
dateInput.max = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);

for (const [value, label] of Object.entries(CATEGORY_LABELS)) {
  categorySelect.append(new Option(label, value));
}

function setKindRules(kind) {
  if (kind === "found") {
    privateInput.required = true;
    privateRequired.textContent = "(required)";
    privateHelp.textContent = "A mark, a scratch, or what is on the lock screen. Only you can see it, and you use it to confirm the real owner.";
  } else {
    privateInput.required = false;
    privateRequired.textContent = "(optional)";
    privateHelp.textContent = "Something only the owner would know, such as a sticker or a password hint. Only you can see it.";
  }
}

document.querySelectorAll('input[name="kind"]').forEach((radio) => {
  radio.addEventListener("change", () => setKindRules(radio.value));
});
const presetKind = new URLSearchParams(window.location.search).get("kind") === "found" ? "found" : "lost";
document.querySelector(`input[name="kind"][value="${presetKind}"]`).checked = true;
setKindRules(presetKind);

photoInput.addEventListener("change", () => {
  previews.innerHTML = "";
  const files = Array.from(photoInput.files);
  if (files.length > 2) {
    showNotice(message, "You can add at most 2 photos.", "error");
    photoInput.value = "";
    return;
  }
  if (files.some((file) => file.size > MAX_PHOTO_BYTES)) {
    showNotice(message, "Each photo must be 3 MB or smaller.", "error");
    photoInput.value = "";
    return;
  }
  message.hidden = true;
  for (const file of files) {
    const img = el("img");
    img.src = URL.createObjectURL(file);
    img.alt = "Selected photo preview";
    previews.append(img);
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.hidden = true;

  const kind = document.querySelector('input[name="kind"]:checked').value;
  const privateDetail = privateInput.value.trim();
  const payload = {
    kind,
    title: document.getElementById("title").value.trim(),
    category: categorySelect.value,
    location: document.getElementById("location").value.trim(),
    description: document.getElementById("description").value.trim(),
    event_date: dateInput.value,
    private_detail: privateDetail || null,
    allow_contact: document.getElementById("allow_contact").checked,
  };

  if (kind === "found" && !privateDetail) {
    showNotice(message, "Found items need a private detail that only you can see.", "error");
    return;
  }

  const button = form.querySelector("button.primary");
  button.disabled = true;
  const created = await apiPost("/api/v1/items", payload);
  if (created.status === 401) {
    window.location.href = "login.html";
    return;
  }
  if (!created.ok) {
    button.disabled = false;
    showNotice(message, errorText(created.data), "error");
    return;
  }

  const itemId = created.data.id;
  for (const file of Array.from(photoInput.files)) {
    const body = new FormData();
    body.append("file", file);
    const upload = await apiUpload(`/api/v1/items/${itemId}/photos`, body);
    if (!upload.ok) {
      button.disabled = false;
      showNotice(message, "Your item was saved, but a photo failed: " + errorText(upload.data), "error");
      return;
    }
  }
  window.location.href = `item.html?id=${itemId}`;
});
