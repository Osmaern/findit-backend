const featured = document.getElementById("featured");
const activity = document.getElementById("activity");
const message = document.getElementById("message");
const who = document.getElementById("who");

function timeAgo(isoUtc) {
  const minutes = Math.round((Date.now() - new Date(isoUtc + "Z").getTime()) / 60000);
  if (minutes < 60) return `${Math.max(minutes, 1)} min ago`;
  if (minutes < 60 * 24) return `${Math.round(minutes / 60)} h ago`;
  return `${Math.round(minutes / (60 * 24))} day(s) ago`;
}

function thumbFor(item, className) {
  const box = el("div", className);
  if (item.photo_ids.length) {
    const img = el("img");
    img.src = `/api/v1/items/${item.id}/photos/${item.photo_ids[0]}`;
    img.alt = item.title;
    box.append(img);
  } else {
    box.textContent = item.kind === "lost" ? "Lost" : "Found";
  }
  return box;
}

function miniCard(item) {
  const link = el("a", "item-card");
  link.href = `item.html?id=${item.id}`;
  const thumb = thumbFor(item, "thumb");
  const body = el("div", "item-body");
  body.append(
    el("span", `tag ${item.kind}`, item.kind === "lost" ? "Lost" : "Found"),
    el("h3", null, item.title),
    el("p", "meta", `${item.location} · ${formatDate(item.event_date)}`),
  );
  link.append(thumb, body);
  return link;
}

async function init() {
  const me = await apiGet("/api/v1/auth/me");
  if (!me.ok) {
    window.location.href = "login.html";
    return;
  }
  const role = me.data.role.charAt(0).toUpperCase() + me.data.role.slice(1);
  if (["moderator", "admin"].includes(me.data.role)) document.getElementById("nav-admin").hidden = false;
  if (me.data.role === "admin") document.getElementById("nav-users").hidden = false;
  who.append(
    el("span", null, `Hello, ${me.data.full_name.split(" ")[0]}!`),
    el("span", "role", role),
  );

  const list = await apiGet("/api/v1/items?limit=12");
  if (!list.ok) {
    showNotice(message, errorText(list.data), "error");
    return;
  }
  const items = list.data;

  featured.innerHTML = "";
  if (items.length === 0) {
    featured.append(el("p", "empty", "No items have been reported yet."));
  } else {
    for (const item of items.slice(0, 4)) featured.append(miniCard(item));
  }

  activity.innerHTML = "";
  for (const item of items.slice(0, 5)) {
    const text = item.kind === "lost" ? "A lost item was reported" : "A found item was reported";
    const li = el("li", "activity-item");
    const textBox = el("div");
    textBox.append(el("span", null, `${text}: ${item.title}`), el("span", "when", timeAgo(item.created_at)));
    li.append(thumbFor(item, "act-thumb"), textBox);
    activity.append(li);
  }
  if (items.length === 0) activity.append(el("li", "activity-empty", "No activity yet."));
}

init();
