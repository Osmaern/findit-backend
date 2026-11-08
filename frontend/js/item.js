const message = document.getElementById("message");
const container = document.getElementById("item");
const itemId = new URLSearchParams(window.location.search).get("id");

async function loadItem() {
  if (!itemId) {
    showNotice(message, "No item was selected.", "error");
    return;
  }
  const result = await apiGet(`/api/v1/items/${encodeURIComponent(itemId)}`);
  if (!result.ok) {
    showNotice(message, errorText(result.data), "error");
    return;
  }
  render(result.data);
  addClaimArea(result.data);
  addReportArea(result.data);
}

// Owners get a link to review claims; everyone else gets the claim form (or a login link).
async function addClaimArea(item) {
  const box = el("section", "claim-box");

  if (item.is_owner) {
    const link = el("a", null, "Review claims on your items →");
    link.href = "claims.html";
    box.append(link);
    container.append(box);
    return;
  }
  if (item.status !== "open") return;

  const me = await apiGet("/api/v1/auth/me");
  if (!me.ok) {
    const link = el("a", null, "Log in to claim this item");
    link.href = "login.html";
    box.append(link);
    container.append(box);
    return;
  }

  const isFound = item.kind === "found";
  const form = el("form");
  const field = el("textarea");
  field.name = "message";
  field.required = true;
  field.minLength = 10;
  field.maxLength = 500;
  field.placeholder = isFound
    ? "Describe something only the owner would know: marks, contents, lock screen..."
    : "Tell the owner where and when you found it.";
  const notice = el("div", "notice error");
  notice.hidden = true;
  const button = el("button", "primary", isFound ? "Claim this item" : "I found this");
  button.type = "submit";
  form.append(field, notice, button);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    notice.hidden = true;
    const result = await apiPost(`/api/v1/items/${item.id}/claims`, { message: field.value });
    if (result.ok) {
      box.innerHTML = "";
      const done = el("div", "notice success", "Your claim was sent. The owner has been texted and will review it.");
      const link = el("a", null, "See my claims →");
      link.href = "claims.html";
      box.append(done, link);
      return;
    }
    showNotice(notice, errorText(result.data), "error");
    button.disabled = false;
  });

  box.append(
    el("h2", null, isFound ? "Is this yours?" : "Did you find this?"),
    el("p", "help", isFound
      ? "The owner of this report will compare your answer with a detail only they know."
      : "Send the owner a message. They will review it and get back to you."),
    form,
  );
  container.append(box);
}

function render(item) {
  container.innerHTML = "";
  container.append(
    el("span", `tag ${item.kind}`, item.kind === "lost" ? "Lost" : "Found"),
    el("h1", null, item.title),
    el("p", "meta", `${CATEGORY_LABELS[item.category] || item.category} · ${item.location} · ${formatDate(item.event_date)}`),
  );

  if (item.photo_ids.length) {
    const gallery = el("div", "photos");
    for (const photoId of item.photo_ids) {
      const img = el("img");
      img.src = `/api/v1/items/${item.id}/photos/${photoId}`;
      img.alt = item.title;
      gallery.append(img);
    }
    container.append(gallery);
  }

  container.append(el("p", "description", item.description));

  if (item.private_detail) {
    const box = el("div", "private-box");
    box.append(
      el("strong", null, "Private detail (only you can see this)"),
      el("p", null, item.private_detail),
    );
    container.append(box);
  }

  container.hidden = false;
}

loadItem();

// Lets a logged-in member tell the moderators that this post breaks the rules.
async function addReportArea(item) {
  if (item.is_owner || item.status !== "open") return;
  const me = await apiGet("/api/v1/auth/me");
  if (!me.ok) return;

  const box = el("section", "report-box");
  const openButton = el("button", "link-like", "Report this post");
  openButton.type = "button";

  const form = el("form");
  form.hidden = true;
  const reason = el("select");
  reason.name = "reason";
  for (const [value, label] of [["spam", "Spam"], ["inappropriate", "Inappropriate"], ["fake", "Fake or false"], ["other", "Something else"]]) {
    const option = el("option", null, label);
    option.value = value;
    reason.append(option);
  }
  const details = el("textarea");
  details.maxLength = 300;
  details.placeholder = "Anything else the moderators should know? (optional)";
  const notice = el("div", "notice error");
  notice.hidden = true;
  const actions = el("div", "claim-actions");
  const send = el("button", "primary", "Send report");
  send.type = "submit";
  const cancel = el("button", "secondary", "Cancel");
  cancel.type = "button";
  actions.append(send, cancel);
  form.append(reason, details, notice, actions);

  openButton.addEventListener("click", () => { form.hidden = false; openButton.hidden = true; });
  cancel.addEventListener("click", () => { form.hidden = true; openButton.hidden = false; });
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    send.disabled = true;
    const result = await apiPost(`/api/v1/items/${item.id}/report`, { reason: reason.value, details: details.value });
    if (result.ok) {
      box.innerHTML = "";
      box.append(el("div", "notice success", "Thank you. A moderator will look at this post."));
      return;
    }
    showNotice(notice, errorText(result.data), "error");
    send.disabled = false;
  });

  box.append(openButton, form);
  container.append(box);
}
