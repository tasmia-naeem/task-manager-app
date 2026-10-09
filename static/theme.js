
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
  });
})();
