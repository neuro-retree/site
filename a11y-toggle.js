/* a11y-toggle.js — кнопки «А−», «А+», «Контраст». Работает без библиотек.
   Если JS отключён, сайт остаётся читаемым: кнопки просто не появятся. */
(function () {
  var root = document.documentElement;
  var KEY = "a11y-prefs";
  var prefs = { size: 1.125, contrast: "normal" };
  try { var saved = JSON.parse(localStorage.getItem(KEY) || "null"); if (saved) prefs = saved; } catch (e) {}
  function apply() {
    root.style.setProperty("--fs", prefs.size + "rem");
    if (prefs.contrast === "high") root.setAttribute("data-contrast", "high");
    else root.removeAttribute("data-contrast");
    try { localStorage.setItem(KEY, JSON.stringify(prefs)); } catch (e) {}
  }
  function make(label, aria, handler) {
    var b = document.createElement("button");
    b.type = "button"; b.textContent = label; b.setAttribute("aria-label", aria);
    b.addEventListener("click", handler); return b;
  }
  var bar = document.getElementById("a11y-toolbar");
  if (bar) {
    bar.appendChild(document.createTextNode("Размер букв: "));
    bar.appendChild(make("А−", "Уменьшить буквы", function () { prefs.size = Math.max(1, +(prefs.size - 0.125).toFixed(3)); apply(); }));
    bar.appendChild(make("А+", "Увеличить буквы", function () { prefs.size = Math.min(2, +(prefs.size + 0.125).toFixed(3)); apply(); }));
    bar.appendChild(make("Контраст", "Включить или выключить высокий контраст", function () { prefs.contrast = prefs.contrast === "high" ? "normal" : "high"; apply(); }));
  }
  apply();
})();