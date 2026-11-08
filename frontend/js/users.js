const message = document.getElementById("message");
const statsBox = document.getElementById("stats");
const usersBox = document.getElementById("users");
const searchInput = document.getElementById("search");
const suspendedOnly = document.getElementById("suspended-only");
const moreButton = document.getElementById("more");

const PAGE_SIZE = 50;
let offset = 0;
let me = null;

function joinedText(iso) {
  return new Date(iso + "Z").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function statGroup(title, rows) {
  const group = el("div", "stat-group");
  group.append(el("h2", null, title));
  for (const [label, value] of rows) {
    const row = el("div", "stat-row");
    row.append(el("span", null, label), el("strong", null, String(value)));
    group.append(row);
  }
  return group;
}

async function loadStats() {
  const result = await apiGet("/api/v1/admin/stats");
  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  const { users, items, claims, open_reports: reports } = result.data;
  statsBox.innerHTML = "";
  statsBox.append(
    statGroup("People", [
      ["All accounts", users.total],
      ["Phone verified", users.verified],
      ["Suspended", users.suspended],
      ["Moderators and admins", users.staff],
    ]),
    statGroup("Posts", [
      ["Lost, open", items.open_lost],
      ["Found, open", items.open_found],
      ["Returned to owner", items.returned],
      ["Closed by owner", items.closed],
      ["Removed by a moderator", items.removed],
      ["Expired", items.expired],
    ]),
    statGroup("Claims", [
      ["Waiting", claims.pending],
      ["Approved", claims.approved],
      ["Declined", claims.declined],
      ["Withdrawn", claims.withdrawn],
    ]),
  );
  const reportGroup = statGroup("Reports", [["Waiting for a moderator", reports]]);
  const link = el("a", "stat-link", "Open moderation →");
  link.href = "admin.html";
  reportGroup.append(link);
  statsBox.append(reportGroup);
}

async function act(path, confirmText) {
  if (!window.confirm(confirmText)) return;
  message.hidden = true;
  const result = await apiPost(path, {});
  if (!result.ok) showNotice(message, errorText(result.data), "error");
  await Promise.all([loadStats(), loadUsers(true)]);
}

function actionButton(label, className, handler) {
  const button = el("button", className, label);
  button.type = "button";
  button.addEventListener("click", async () => {
    button.disabled = true;
    await handler();
    button.disabled = false;
  });
  return button;
}

function userCard(user) {
  const card = el("article", "claim-card user-card");

  const header = el("header");
  header.append(el("strong", null, user.full_name));
  const pills = el("div", "pill-row");
  pills.append(el("span", "role-pill", user.role));
  if (!user.is_active) pills.append(el("span", "suspended-pill", "Suspended"));
  header.append(pills);
  card.append(header);

  const details = [`0${user.phone.slice(3)}`];
  if (user.email) details.push(user.email);
  details.push(`joined ${joinedText(user.created_at)}`);
  if (!user.phone_verified) details.push("phone not verified");
  card.append(el("p", "meta", details.join(" · ")));

  // An admin cannot suspend themselves or another admin
  if (user.role !== "admin" && user.id !== me.id) {
    const actions = el("div", "claim-actions");
    if (user.is_active) {
      actions.append(
        actionButton("Suspend", "danger", () =>
          act(`/api/v1/admin/users/${user.id}/suspend`,
            `Suspend ${user.full_name}? They are signed out, cannot log in, and get an SMS.`)),
      );
    } else {
      actions.append(
        actionButton("Restore", "secondary", () =>
          act(`/api/v1/admin/users/${user.id}/restore`, `Restore ${user.full_name}? They can log in again.`)),
      );
    }
    card.append(actions);
  }
  return card;
}

async function loadUsers(reset) {
  if (reset) {
    offset = 0;
    usersBox.innerHTML = "";
  }
  const params = new URLSearchParams({ limit: PAGE_SIZE, offset });
  if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
  if (suspendedOnly.checked) params.set("status", "suspended");

  const result = await apiGet(`/api/v1/admin/users?${params}`);
  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  if (reset && result.data.length === 0) {
    usersBox.append(el("p", "empty-note", "Nobody matches that search."));
  }
  for (const user of result.data) usersBox.append(userCard(user));
  offset += result.data.length;
  moreButton.hidden = result.data.length < PAGE_SIZE;
}

async function start() {
  const who = await apiGet("/api/v1/auth/me");
  if (who.status === 401) {
    window.location.href = "login.html";
    return;
  }
  if (!who.ok || who.data.role !== "admin") {
    showNotice(message, "This page is for admins only.", "error");
    return;
  }
  me = who.data;
  await Promise.all([loadStats(), loadUsers(true)]);
}

document.getElementById("search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  loadUsers(true);
});
suspendedOnly.addEventListener("change", () => loadUsers(true));
moreButton.addEventListener("click", () => loadUsers(false));

start();
