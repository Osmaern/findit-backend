const message = document.getElementById("message");
const reportsBox = document.getElementById("reports");
const tabs = document.querySelectorAll(".tab");

const REASON_LABELS = { spam: "Spam", inappropriate: "Inappropriate", fake: "Fake or false", other: "Other" };
const STATUS_LABELS = { open: "Waiting", actioned: "Post removed", dismissed: "Dismissed" };

let filter = "open";

function whenText(iso) {
  return new Date(iso + "Z").toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

async function act(path, confirmText) {
  if (confirmText && !window.confirm(confirmText)) return;
  message.hidden = true;
  const result = await apiPost(path, {});
  if (!result.ok) showNotice(message, errorText(result.data), "error");
  await load();
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

function reportCard(report) {
  const card = el("article", "claim-card");

  const header = el("header");
  const title = el("div");
  title.append(el("span", `tag ${report.item_kind}`, report.item_kind === "lost" ? "Lost" : "Found"), " ", el("strong", null, report.item_title));
  header.append(title, el("span", `status-pill ${report.status === "open" ? "pending" : "declined"}`, STATUS_LABELS[report.status] || report.status));
  card.append(header);

  card.append(el("p", "meta", `Posted by ${report.owner_name} · reported by ${report.reporter_name} · ${whenText(report.created_at)}`));
  const reason = el("p", "report-reason");
  reason.append(el("span", "reason-pill", REASON_LABELS[report.reason] || report.reason));
  if (report.status === "open" && report.open_reports_on_item > 1) {
    reason.append(` ${report.open_reports_on_item} people have reported this post`);
  }
  card.append(reason);
  if (report.details) card.append(el("p", "claim-message", report.details));

  const actions = el("div", "claim-actions");
  const view = el("a", "link-button", "Open post");
  view.href = `item.html?id=${report.item_id}`;
  actions.append(view);

  if (report.status === "open") {
    actions.append(
      actionButton("Remove post", "primary", () =>
        act(`/api/v1/admin/reports/${report.id}/remove`,
          "Remove this post? It disappears from Browse, waiting claims are declined, and the owner gets an SMS.")),
      actionButton("Dismiss report", "secondary", () => act(`/api/v1/admin/reports/${report.id}/dismiss`)),
    );
  } else if (report.item_status === "removed") {
    actions.append(
      actionButton("Restore post", "secondary", () =>
        act(`/api/v1/admin/items/${report.item_id}/restore`, "Put this post back on Browse?")),
    );
  }
  card.append(actions);
  return card;
}

async function load() {
  const result = await apiGet(`/api/v1/admin/reports?status=${filter}`);
  if (result.status === 401) {
    window.location.href = "login.html";
    return;
  }
  if (result.status === 403) {
    reportsBox.innerHTML = "";
    showNotice(message, "This page is for moderators only.", "error");
    return;
  }
  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  reportsBox.innerHTML = "";
  if (result.data.length === 0) {
    reportsBox.append(el("p", "empty-note", filter === "open" ? "No reports are waiting. 🎉" : "Nothing has been handled yet."));
    return;
  }
  for (const report of result.data) reportsBox.append(reportCard(report));
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    filter = tab.dataset.filter;
    tabs.forEach((other) => other.classList.toggle("active", other === tab));
    load();
  });
});

load();

apiGet("/api/v1/auth/me").then((who) => {
  if (who.ok && who.data.role === "admin") document.getElementById("nav-users").hidden = false;
});
