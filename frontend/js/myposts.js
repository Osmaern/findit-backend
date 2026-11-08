const message = document.getElementById("message");
const posts = document.getElementById("posts");

const STATUS_LABELS = {
  open: "Open",
  claim_pending: "Claim approved",
  returned: "Returned",
  closed: "Closed",
  expired: "Expired",
  removed: "Removed by a moderator",
};

async function closeReport(item) {
  if (!window.confirm("Close this report? It will disappear from Browse and any waiting claims will be declined.")) return;
  message.hidden = true;
  const result = await apiPost(`/api/v1/items/${item.id}/close`, {});
  if (!result.ok) showNotice(message, errorText(result.data), "error");
  await load();
}

function postCard(item) {
  const card = el("article", "claim-card post-card");

  const thumb = el("div", "post-thumb");
  if (item.photo_ids.length) {
    const img = el("img");
    img.src = `/api/v1/items/${item.id}/photos/${item.photo_ids[0]}`;
    img.alt = item.title;
    thumb.append(img);
  } else {
    thumb.textContent = item.kind === "lost" ? "Lost" : "Found";
  }

  const body = el("div", "post-body");
  const header = el("header");
  const left = el("div");
  left.append(el("span", `tag ${item.kind}`, item.kind === "lost" ? "Lost" : "Found"), " ", el("strong", null, item.title));
  header.append(left, el("span", `status-pill ${item.status === "removed" ? "closed" : item.status}`, STATUS_LABELS[item.status] || item.status));
  body.append(
    header,
    el("p", "meta", `${CATEGORY_LABELS[item.category] || item.category} · ${item.location} · ${formatDate(item.event_date)}`),
  );

  const actions = el("div", "claim-actions");
  const view = el("a", "link-button", "View");
  view.href = `item.html?id=${item.id}`;
  actions.append(view);

  if (item.pending_claims > 0) {
    const waiting = el("a", "link-button highlight", `${item.pending_claims} claim${item.pending_claims === 1 ? "" : "s"} waiting →`);
    waiting.href = "claims.html";
    actions.append(waiting);
  }
  if (item.status === "open") {
    const close = el("button", "secondary", "Close report");
    close.type = "button";
    close.addEventListener("click", async () => {
      close.disabled = true;
      await closeReport(item);
      close.disabled = false;
    });
    actions.append(close);
  }
  body.append(actions);

  card.append(thumb, body);
  return card;
}

async function load() {
  const result = await apiGet("/api/v1/items/mine");
  if (result.status === 401) {
    window.location.href = "login.html";
    return;
  }
  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  posts.innerHTML = "";
  if (result.data.length === 0) {
    const note = el("p", "empty-note", "You have not reported anything yet. ");
    const link = el("a", null, "Report an item");
    link.href = "report.html";
    note.append(link);
    posts.append(note);
    return;
  }
  for (const item of result.data) posts.append(postCard(item));
}

load();
