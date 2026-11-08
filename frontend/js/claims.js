const message = document.getElementById("message");
const receivedBox = document.getElementById("received");
const mineBox = document.getElementById("mine");

const STATUS_LABELS = { pending: "Waiting", approved: "Approved", declined: "Declined", withdrawn: "Withdrawn" };

function whenText(iso) {
  return new Date(iso + "Z").toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function phoneLink(phone) {
  const link = el("a", null, `0${phone.slice(3)}`); // 233244123456 -> 0244123456
  link.href = `tel:+${phone}`;
  return link;
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

async function act(path, confirmText) {
  if (confirmText && !window.confirm(confirmText)) return;
  message.hidden = true;
  const result = await apiPost(path, {});
  if (!result.ok) showNotice(message, errorText(result.data), "error");
  await loadAll();
}

function cardHeader(claim, title) {
  const header = el("header");
  const left = el("div");
  left.append(el("span", `tag ${claim.item_kind}`, claim.item_kind === "lost" ? "Lost" : "Found"), " ");
  const strong = el("strong", null, title);
  left.append(strong);
  header.append(left, el("span", `status-pill ${claim.status}`, STATUS_LABELS[claim.status] || claim.status));
  return header;
}

function receivedCard(claim) {
  const card = el("article", "claim-card");
  card.append(cardHeader(claim, claim.item_title));
  card.append(el("p", "meta", `From ${claim.claimant_name} · ${whenText(claim.created_at)}`));
  card.append(el("p", "claim-message", claim.message));

  const actions = el("div", "claim-actions");
  if (claim.status === "pending") {
    actions.append(
      actionButton("Approve", "primary", () =>
        act(`/api/v1/claims/${claim.id}/approve`,
          "Approve this claim? Their phone number will be shown to you, other claims on this item will be closed, and the item leaves the public list.")),
      actionButton("Decline", "secondary", () => act(`/api/v1/claims/${claim.id}/decline`, "Decline this claim?")),
    );
  }
  if (claim.status === "approved") {
    const line = el("p", "contact-line", "Contact them: ");
    line.append(phoneLink(claim.claimant_phone));
    card.append(line);
    if (claim.item_status === "claim_pending") {
      actions.append(
        actionButton("Mark as returned", "primary", () =>
          act(`/api/v1/items/${claim.item_id}/returned`, "Mark this item as returned to its owner?")),
      );
    } else if (claim.item_status === "returned") {
      card.append(el("p", "returned-note", "Item returned ✓"));
    }
  }
  if (actions.children.length) card.append(actions);
  return card;
}

function mineCard(claim) {
  const card = el("article", "claim-card");
  card.append(cardHeader(claim, claim.item_title));
  card.append(el("p", "meta", whenText(claim.created_at)));
  card.append(el("p", "claim-message", claim.message));

  if (claim.status === "approved") {
    if (claim.contact_phone) {
      const line = el("p", "contact-line", "Owner's phone: ");
      line.append(phoneLink(claim.contact_phone));
      card.append(line);
    } else {
      card.append(el("p", "contact-line", "Approved. The owner has your phone number and will contact you."));
    }
  }
  if (claim.status === "pending") {
    const actions = el("div", "claim-actions");
    actions.append(
      actionButton("Withdraw claim", "secondary", () => act(`/api/v1/claims/${claim.id}/withdraw`, "Withdraw this claim?")),
    );
    card.append(actions);
  }
  return card;
}

function fill(box, claims, build, emptyText) {
  box.innerHTML = "";
  if (claims.length === 0) {
    box.append(el("p", "empty-note", emptyText));
    return;
  }
  for (const claim of claims) box.append(build(claim));
}

async function loadAll() {
  const [received, mine] = await Promise.all([
    apiGet("/api/v1/claims/received"),
    apiGet("/api/v1/claims/mine"),
  ]);
  if (received.status === 401 || mine.status === 401) {
    window.location.href = "login.html";
    return;
  }
  if (!received.ok || !mine.ok) {
    showNotice(message, errorText((received.ok ? mine : received).data), "error");
    return;
  }
  fill(receivedBox, received.data, receivedCard, "Nobody has claimed your items yet.");
  fill(mineBox, mine.data, mineCard, "You have not claimed anything yet. Open an item and press Claim.");
}

loadAll();
