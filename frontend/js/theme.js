// Light / dark mode. The choice is remembered in this browser only.
(function () {
  var KEY = "findit-theme";
  function saved() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function systemPrefersDark() {
    return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  }
  function apply(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }
  apply(saved() || (systemPrefersDark() ? "dark" : "light"));

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "theme-toggle";
    function label() {
      var dark = document.documentElement.getAttribute("data-theme") === "dark";
      button.textContent = dark ? "Light mode" : "Dark mode";
      button.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    }
    button.addEventListener("click", function () {
      var dark = document.documentElement.getAttribute("data-theme") === "dark";
      var next = dark ? "light" : "dark";
      apply(next);
      try { localStorage.setItem(KEY, next); } catch (e) { /* private window: just skip saving */ }
      label();
    });
    label();
    document.body.appendChild(button);
  });
})();
