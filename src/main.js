(function () {
  var root = document.documentElement;
  var toggle = document.querySelector("[data-theme-toggle]");
  var menu = document.querySelector("[data-menu-toggle]");
  var nav = document.querySelector("[data-nav]");
  var meta = document.querySelector('meta[name="theme-color"]');

  function current() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("theme", theme);
    } catch (err) {
      /* storage can be blocked; the attribute still updates this view */
    }
    if (meta) {
      var color = theme === "dark" ? meta.getAttribute("data-dark") : meta.getAttribute("data-light");
      if (color) meta.setAttribute("content", color);
    }
    if (toggle) {
      var next = theme === "dark" ? "light" : "dark";
      toggle.setAttribute("aria-label", "Switch to " + next + " theme");
      toggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    }
  }

  apply(current());

  if (toggle) {
    toggle.addEventListener("click", function () {
      apply(current() === "dark" ? "light" : "dark");
    });
  }

  function setMenu(open) {
    if (!nav || !menu) return;
    nav.classList.toggle("is-open", open);
    menu.setAttribute("aria-expanded", open ? "true" : "false");
    menu.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }

  if (menu && nav) {
    menu.addEventListener("click", function () {
      setMenu(!nav.classList.contains("is-open"));
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) setMenu(false);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") setMenu(false);
    });
    document.addEventListener("click", function (event) {
      if (!nav.classList.contains("is-open")) return;
      if (event.target.closest("[data-nav]") || event.target.closest("[data-menu-toggle]")) return;
      setMenu(false);
    });
  }
})();
