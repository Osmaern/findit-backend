const results = document.getElementById("results");
const message = document.getElementById("message");
const searchInput = document.getElementById("q");
const kindSelect = document.getElementById("kind");
const categorySelect = document.getElementById("category");
const locationInput = document.getElementById("location");
const daysSelect = document.getElementById("days");
const countText = document.getElementById("count");
const clearButton = document.getElementById("clear");
const moreButton = document.getElementById("more");
const PAGE_SIZE = 24;
let shown = 0;

for (const [value, label] of Object.entries(CATEGORY_LABELS)) {
  categorySelect.append(new Option(label, value));
}

function itemCard(item) {
  const link = el("a", "item-card");
  link.href = `item.html?id=${item.id}`;

  const thumb = el("div", "thumb");
  if (item.photo_ids.length) {
    const img = el("img");
    img.src = `/api/v1/items/${item.id}/photos/${item.photo_ids[0]}`;
    img.alt = item.title;
    thumb.append(img);
  } else {
    thumb.textContent = "No photo";
  }

  const body = el("div", "item-body");
  body.append(
    el("span", `tag ${item.kind}`, item.kind === "lost" ? "Lost" : "Found"),
    el("h3", null, item.title),
    el("p", "meta", CATEGORY_LABELS[item.category] || item.category),
    el("p", "meta", `${item.location} · ${formatDate(item.event_date)}`),
  );
  link.append(thumb, body);
  return link;
}

function hasFilters() {
  return Boolean(
    searchInput.value.trim() || kindSelect.value || categorySelect.value || locationInput.value.trim() || daysSelect.value,
  );
}

function queryFor(offset) {
  const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) });
  if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
  if (kindSelect.value) params.set("kind", kindSelect.value);
  if (categorySelect.value) params.set("category", categorySelect.value);
  if (locationInput.value.trim()) params.set("location", locationInput.value.trim());
  if (daysSelect.value) params.set("days", daysSelect.value);
  return params;
}

// loadItems(true) starts a new search; loadItems(false) adds the next page below the current ones.
async function loadItems(fresh = true) {
  if (fresh) shown = 0;
  const result = await apiGet(`/api/v1/items?${queryFor(shown)}`);
  if (fresh) results.innerHTML = "";
  clearButton.hidden = !hasFilters();
  if (!result.ok) {
    moreButton.hidden = true;
    showNotice(message, errorText(result.data), "error");
    return;
  }
  message.hidden = true;
  for (const item of result.data) results.append(itemCard(item));
  shown += result.data.length;

  if (shown === 0) {
    results.append(el("p", "empty", "No open items match your search."));
    countText.textContent = "";
  } else {
    countText.textContent = shown === 1 ? "Showing 1 item" : `Showing ${shown} items`;
  }
  // A full page means there may be more; a short page means we reached the end.
  moreButton.hidden = result.data.length < PAGE_SIZE;
}

let searchTimer;
function searchSoon() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => loadItems(true), 300);
}
searchInput.addEventListener("input", searchSoon);
locationInput.addEventListener("input", searchSoon);
kindSelect.addEventListener("change", () => loadItems(true));
categorySelect.addEventListener("change", () => loadItems(true));
daysSelect.addEventListener("change", () => loadItems(true));
moreButton.addEventListener("click", () => loadItems(false));
clearButton.addEventListener("click", () => {
  searchInput.value = "";
  locationInput.value = "";
  kindSelect.value = "";
  categorySelect.value = "";
  daysSelect.value = "";
  loadItems(true);
});

searchInput.value = new URLSearchParams(window.location.search).get("q") || "";
loadItems(true);
