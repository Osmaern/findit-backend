const results = document.getElementById("results");
const message = document.getElementById("message");
const searchInput = document.getElementById("q");
const kindSelect = document.getElementById("kind");
const categorySelect = document.getElementById("category");

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

async function loadItems() {
  const params = new URLSearchParams({ limit: "24" });
  if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
  if (kindSelect.value) params.set("kind", kindSelect.value);
  if (categorySelect.value) params.set("category", categorySelect.value);

  const result = await apiGet(`/api/v1/items?${params}`);
  results.innerHTML = "";
  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  message.hidden = true;
  if (result.data.length === 0) {
    results.append(el("p", "empty", "No open items match your search."));
    return;
  }
  for (const item of result.data) results.append(itemCard(item));
}

let searchTimer;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadItems, 300);
});
kindSelect.addEventListener("change", loadItems);
categorySelect.addEventListener("change", loadItems);

searchInput.value = new URLSearchParams(window.location.search).get("q") || "";
loadItems();
