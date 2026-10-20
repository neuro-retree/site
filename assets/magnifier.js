/* magnifier.js — кнопка-лупа с мягким кругом над содержимым страницы.
   Работает и над текстом, и над картинками: клонирует target-элемент один раз,
   показывает круглое «стекло» под курсором и увеличивает содержимое ~2x.
   Лупа всегда отцентрирована на курсоре (следует строго за ним).
   Включение/выключение — кнопкой с иконкой лупы в тулбаре. */
(function () {
  "use strict";
  var lens = null, zoomEl = null, active = false, targetEl = null, clone = null;
  var SCALE = 2.0, RADIUS = 118;

  function createLens() {
    lens = document.createElement("div");
    lens.className = "magnify-lens";
    zoomEl = document.createElement("div");
    zoomEl.className = "lens-zoom";
    lens.appendChild(zoomEl);
    document.body.appendChild(lens);
  }

  function buildClone() {
    if (!targetEl) return;
    clone = targetEl.cloneNode(true);
    clone.style.cssText = "position:absolute;top:0;left:0;width:" + targetEl.offsetWidth + "px;";
    zoomEl.appendChild(clone);
  }

  function move(e) {
    if (!lens || !active || !targetEl) return;
    var r = targetEl.getBoundingClientRect();
    var x = e.clientX, y = e.clientY;
    if (x < r.left || x > r.right || y < r.top || y > r.bottom) { lens.style.display = "none"; return; }
    lens.style.display = "block";
    lens.style.left = x + "px";
    lens.style.top = y + "px";
    var px = x - r.left, py = y - r.top;
    zoomEl.style.transform = "translate(" + (-px * SCALE + RADIUS) + "px," + (-py * SCALE + RADIUS) + "px) scale(" + SCALE + ")";
  }

  function setActive(on) {
    active = on;
    document.body.classList.toggle("magnify-active", on);
    if (!lens) createLens();
    if (on) {
      if (!targetEl) targetEl = document.querySelector(".article, .book-spread .page, main, .card") || document.body;
      if (!clone) buildClone();
      lens.style.display = "none";
    } else {
      lens.style.display = "none";
    }
  }

  function toggle() {
    setActive(!active);
    return active;
  }

  window.__magnifier = {
    toggle: toggle, setActive: setActive,
    isActive: function () { return active; }
  };
  document.addEventListener("mousemove", move);
  console.log("[magnifier.js] лупа готова: " + SCALE + "x, радиус " + RADIUS + "px");
})();