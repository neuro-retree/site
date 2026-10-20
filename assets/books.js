/* books.js — вьюер «листающейся книги»: тома + статьи.
   - режим «Тома»: загружает data/tomes.json, листает развороты книги (со звуком);
   - режим «Статьи»: загружает articles/catalog.json, листает обложки статей
     как страницы книги; клик по обложке открывает полный текст статьи;
   - кнопки ◀ ▶ перелистывают страницы со звуком;
   - ведение курсором -> лёгкое шуршание;
   - кнопка «Лупа» (из magnifier.js) работает поверх страниц. */
(function () {
  "use strict";
  var MODE = { TOMES: "tomes", ARTICLES: "articles" };
  var mode = MODE.TOMES;
  var tomes = [], articles = [], current = { tome: 0, page: 0, article: 0 };
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

  function pageTurn() {
    if (window.__bookSounds) window.__bookSounds.flip();
  }

  /* ---------- РЕЖИМ ТОМОВ ---------- */
  function renderTome() {
    var t = tomes[current.tome];
    if (!t) return;
    var spread = document.getElementById("bookSpread");
    if (!spread) return;
    spread.innerHTML = "";
    var pages = [t.cover].concat(t.pages || []);
    var total = Math.ceil(pages.length / PAGES_PER_VIEW);
    if (current.page > total - 1) current.page = total - 1;
    var start = current.page * PAGES_PER_VIEW;
    var left = pages[start], right = pages[start + 1];
    var pl = el("div", "page book-page-left", left || '<p style="color:#aaa">·</p>');
    var pr = el("div", "page book-page-right", right || '<p style="color:#aaa">·</p>');
    pl.style.minHeight = "420px"; pr.style.minHeight = "420px";
    spread.appendChild(pl); spread.appendChild(pr);
    renderNav(total, start, pages.length, t.title);
  }

  /* ---------- РЕЖИМ СТАТЕЙ ---------- */
  function renderArticles() {
    var spread = document.getElementById("bookSpread");
    if (!spread) return;
    spread.innerHTML = "";
    var total = Math.ceil(articles.length / PAGES_PER_VIEW);
    if (current.article > total - 1) current.article = total - 1;
    var start = current.article * PAGES_PER_VIEW;
    for (var i = start; i < Math.min(start + PAGES_PER_VIEW, articles.length); i++) {
      spread.appendChild(articleCard(articles[i]));
    }
    renderNav(total, start, articles.length, "Статьи «Нейросети для жизни»");
  }

  function articleCard(a) {
    var page = el("div", "page article-page");
    page.style.minHeight = "420px";
    page.style.cursor = "pointer";
    var link = el("a", null, "");
    link.href = a.url; link.target = "_blank"; link.rel = "noopener";
    link.style.textDecoration = "none"; link.style.color = "inherit";
    if (a.cover) {
      var img = el("img", null, "");
      img.src = a.cover; img.alt = a.title;
      img.loading = "lazy";
      img.style.cssText = "width:100%;height:auto;border-radius:6px;box-shadow:0 4px 16px rgba(60,40,10,.22);";
      link.appendChild(img);
    }
    var tag = el("span", "article-page-tag", a.tag || "");
    var h = el("div", "article-page-title", a.title);
    link.appendChild(tag); link.appendChild(h);
    page.appendChild(link);
    if (window.__magnifier && window.__magnifier.isActive && !window.__magnifier.isActive()) {
      /* лупа не мешает клику */
    }
    return page;
  }

  /* ---------- НАВИГАЦИЯ ---------- */
  function renderNav(total, start, all, title) {
    var nav = document.getElementById("bookNav");
    if (!nav) return;
    nav.innerHTML = "";
    var prevBtn = el("button", "", "◀ Назад");
    prevBtn.onclick = function () { if (total > 0 && ((mode === MODE.TOMES && current.page > 0) || (mode === MODE.ARTICLES && current.article > 0))) { if (mode === MODE.TOMES) current.page--; else current.article--; pageTurn(); render(); } };
    var nextBtn = el("button", "", "Вперёд ▶");
    nextBtn.onclick = function () { if (total > 0 && ((mode === MODE.TOMES && current.page < total - 1) || (mode === MODE.ARTICLES && current.article < total - 1))) { if (mode === MODE.TOMES) current.page++; else current.article++; pageTurn(); render(); } };
    nav.appendChild(prevBtn); nav.appendChild(nextBtn);
    var info = el("span", "", firstLine(title) + " · " + Math.min(start + 1, all) + "–" + Math.min(start + PAGES_PER_VIEW, all) + " / " + all);
    nav.appendChild(info);
  }

  function firstLine(s) {
    s = String(s || "");
    var i = s.indexOf("\n");
    return (i >= 0 ? s.slice(0, i) : s);
  }

  /* ---------- РЕЖИМ ПЕРЕКЛЮЧЕНИЯ ---------- */
  function switchMode(m) {
    mode = m;
    current.page = 0; current.article = 0;
    var bt = document.getElementById("btnMode");
    if (bt) bt.textContent = (mode === MODE.TOMES) ? "📚 Тома книги" : "📰 Статьи";
    render();
  }

  function render() {
    if (mode === MODE.TOMES) renderTome(); else renderArticles();
  }

  function initRustle() {
    var spread = document.getElementById("bookSpread");
    if (!spread) return;
    spread.addEventListener("mousemove", function () {
      if (window.__bookSounds && Math.random() < 0.12) window.__bookSounds.rustle();
    });
  }

  function init() {
    if (!document.getElementById("bookSpread")) return;
    var base = "https://neuro-retree.github.io/site/";
    loadJSON(base + "data/tomes.json", function (data) {
      tomes = data.tomes || [];
      loadJSON(base + "articles/catalog.json", function (adata) {
        articles = adata.articles || [];
        render();
        initRustle();
        var bt = document.getElementById("btnMode");
        if (bt && !bt.onclick) {
          bt.onclick = function () { switchMode(mode === MODE.TOMES ? MODE.ARTICLES : MODE.TOMES); };
        }
        if (window.__magnifier) {
          window.__magnifier = Object.assign({}, window.__magnifier, { targetSelector: ".book-spread .page" });
        }
        console.log("[books.js] томов: " + tomes.length + ", статей: " + articles.length);
      });
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();