/* books.js — вьюер «листающейся книги» для томов.
   - загружает data/tomes.json;
   - рендерит разворот (две страницы) с эффектом перелистывания и тенью корешка;
   - кнопки ◀ ▶ перелистывают страницы со звуком;
   - ведение курсором по страницам -> лёгкое шуршание;
   - кнопка «Лупа» в тулбаре подключает magnification поверх страниц. */
(function () {
  "use strict";
  var tomes = [], current = { tome: 0, page: 0 };
  var pageEls = null;
  var PAGES_PER_VIEW = 2;

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  function loadJSON(url, cb) {
    fetch(url).then(function (r) { return r.json(); }).then(cb).catch(function (err) {
      console.error("books.js: не удалось загрузить", url, err);
    });
  }

  function renderTome() {
    var t = tomes[current.tome];
    if (!t) return;
    var spread = document.getElementById("bookSpread");
    if (!spread) return;
    spread.innerHTML = "";
    var pages = [t.cover].concat(t.pages || []);
    var start = current.page * PAGES_PER_VIEW;
    var left = pages[start], right = pages[start + 1];
    var pl = el("div", "page book-page-left", left || '<p style="color:#aaa">·</p>');
    var pr = el("div", "page book-page-right", right || '<p style="color:#aaa">·</p>');
    pl.style.minHeight = "420px"; pr.style.minHeight = "420px";
    spread.appendChild(pl); spread.appendChild(pr);
    pageEls = [pl, pr];
    var total = Math.ceil(pages.length / PAGES_PER_VIEW);
    var pos = el("div", "book-pos", "Стр. " + (start + 1) + "–" + Math.min(start + 2, pages.length) + " из " + pages.length + " · ' + t.title + '");
    spread.appendChild(pos);
    var nav = document.getElementById("bookNav");
    if (nav) {
      nav.innerHTML = "";
      var d = null;
      var prevBtn = el("button", "", "◀ Назад");
      prevBtn.onclick = function () { if (current.page > 0) { current.page--; flipPage(); } };
      var nextBtn = el("button", "", "Вперёд ▶");
      nextBtn.onclick = function () { if (current.page < total - 1) { current.page++; flipPage(); } };
      nav.appendChild(prevBtn); nav.appendChild(nextBtn);
      var info = el("span", "", t.title + " · с." + (start + 1) + "-" + Math.min(start + 2, pages.length) + "/" + pages.length);
      nav.appendChild(info);
    }
  }

  function flipPage() {
    if (window.__bookSounds) window.__bookSounds.flip();
    renderTome();
  }

  function initRustle() {
    document.getElementById("bookSpread").addEventListener("mousemove", function (e) {
      if (!window.__soundSeen) { window.__soundSeen = true; }
      if (window.__bookSounds && Math.random() < 0.12) window.__bookSounds.rustle();
    });
  }

  function init() {
    if (!document.getElementById("bookSpread")) return;
    var url = document.querySelector('script[data-tomes]');
    loadJSON("data/tomes.json", function (data) {
      tomes = data.tomes || [];
      if (!tomes.length) return;
      // селектор тома (если на странице несколько) — просто первый
      renderTome();
      initRustle();
      if (window.__magnifier) {
        // перенацеливаем лупу на страницы книги
        var old = window.__magnifier;
        window.__magnifier = Object.assign({}, old, { targetSelector: ".book-spread .page" });
      }
      console.log("[books.js] томов загружено: " + tomes.length);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();