(function () {
  var KEY = "taskflow-theme";
  var saved = null;

  try { saved = localStorage.getItem(KEY); } catch (e) { /* private mode */ }

  // If nothing is saved yet, follow the device preference.
  var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  var isDark = saved ? saved === "dark" : prefersDark;

  // This script runs in <head> before <body> exists, so for now we put the class on
  // <html> (avoids a white flash). The CSS supports both.
  if (isDark) document.documentElement.classList.add("dark-theme");

  document.addEventListener("DOMContentLoaded", function () {
    var body = document.body;
    var btn = document.getElementById("theme-toggle");
    var icon = document.getElementById("theme-icon");

    // The body exists now: put the real class on it and remove the one on <html>.
    document.documentElement.classList.remove("dark-theme");
    body.classList.toggle("dark-theme", isDark);
    updateIcon();

    btn.addEventListener("click", function () {
      var nowDark = body.classList.toggle("dark-theme"); // add/remove "dark-theme"
      try { localStorage.setItem(KEY, nowDark ? "dark" : "light"); } catch (e) {}
      updateIcon();
    });

    // In dark mode show ☀️ (switch to light); in light mode show 🌙 (switch to dark).
    function updateIcon() {
      icon.textContent = body.classList.contains("dark-theme") ? "☀️" : "🌙";
    }

    // ---- Mobile sidebar (drawer) ----
    // On small screens the CSS hides the sidebar off-screen. Adding the "nav-open"
    // class to <body> slides it in and shows the dark overlay (scrim).
    var menuBtn = document.getElementById("menu-toggle");
    var scrim = document.getElementById("scrim");

    function setNav(open) {
      body.classList.toggle("nav-open", open);
      if (menuBtn) menuBtn.setAttribute("aria-expanded", String(open));
    }

    if (menuBtn) {
      menuBtn.addEventListener("click", function () {
        setNav(!body.classList.contains("nav-open"));
      });
    }
    if (scrim) scrim.addEventListener("click", function () { setNav(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setNav(false); });
    // If the window grows back to desktop size, make sure the drawer state is reset.
    window.addEventListener("resize", function () { if (window.innerWidth > 900) setNav(false); });
  });
})();
