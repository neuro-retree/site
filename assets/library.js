/* library.js — интерактивная книжная полка «Нейросети для жизни».
   Сцена: 5 книг (Статьи, Обучение, Книга, Видео, Об авторе).
   Анимации: shelf -> pulling -> opening -> zooming -> reading -> closing -> returning.
   Звуки WebAudio (без файлов). Лупа 2 режима строго за курсором.
   Контент: статьи (articles.json), обучение (learning), тома (tomes.json), автор, видео-заглушки. */
(function () {
  "use strict";
  var BASE = "https://neuro-retree.github.io/site/";
  var CONFIG = {
books: [
{ id: "articles", title: "Статьи",   color: "#5b3a2e", h: 440, w: 66, tag: "сборник публикаций", font: "'EB Garamond',serif", tone: "gold", tex: "library/tex/leather-articles.svg" },
{ id: "learning", title: "Обучение", color: "#2f4a3a", h: 400, w: 58, tag: "учебник", font: "'Jost',sans-serif", tone: "silver", tex: "library/tex/leather-learning.svg" },
{ id: "book",     title: "Книга",    color: "#4a3a69", h: 465, w: 84, tag: "четыре тома", font: "'Playfair Display',serif", tone: "gold", tex: "library/tex/leather-book.svg" },
{ id: "video",    title: "Видео",    color: "#3a4a69", h: 373, w: 52, tag: "видеоальбом", font: "'Montserrat',sans-serif", tone: "silver", tex: "library/tex/leather-video.svg" },
{ id: "author",   title: "Об авторе",color: "#6a4a2e", h: 413, w: 62, tag: "личный том", font: "'Libre Baskerville',serif", tone: "gold", tex: "library/tex/leather-author.svg" }
    ],
    anim: { pull: 1400, open: 1800, zoom: 1600, close: 1800, ret: 1400 }
  };
  var state = "shelf", sel = -1, cur = 0, pages = [], quiet = false;

  /* Конечный автомат состояний (запрещает недопустимые переходы) */
  var ALLOWED = {
    shelf: ["pulling"],
    pulling: ["opening", "closing"],
    opening: ["zooming", "closing"],
    zooming: ["reading", "closing"],
    reading: ["closing"],
    closing: ["returning"],
    returning: ["shelf"]
  };
  function canNext(from, to) {
    var ok = ALLOWED[from] && ALLOWED[from].indexOf(to) >= 0;
    if (!ok) console.warn("[library] недопустимый переход: " + from + " -> " + to);
    return ok;
  }
  function go(to) {
    if (!canNext(state, to)) return false;
    state = to;
    return true;
  }

  /* ================= ЗВУК (WebAudio) ================= */
  var Sound = (function () {
    var AC = null, on = true, cache = {};
    function ctx() {
      if (!AC) { try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} }
      if (AC && AC.state === "suspended") AC.resume();
      return AC;
    }
    function make(kind) {
      var ac = ctx(); if (!ac) return null;
      var dur = kind === "pull" ? 0.5 : kind === "return" ? 0.45 : kind === "open" ? 0.55 : 0.3;
      var buf = ac.createBuffer(1, ac.sampleRate * dur, ac.sampleRate);
      var d = buf.getChannelData(0), seed = kind === "pull" ? 7777 : kind === "open" ? 3131 : kind === "return" ? 5151 : kind === "back" ? 2626 : 1234;
      function rnd() { seed = (seed * 9301 + 49297) % 233280; return seed / 233280; }
      for (var i = 0; i < d.length; i++) {
        var t = i / ac.sampleRate, env;
        if (kind === "pull") env = Math.exp(-t * 9) * (0.4 + 0.6 * Math.sin(2 * Math.PI * 5 * t));
        else if (kind === "open") env = Math.exp(-t * 12) * (0.5 + 0.5 * Math.sin(2 * Math.PI * 3 * t + 1.2));
        else if (kind === "return") env = Math.exp(-t * 10) * (0.5 + 0.5 * Math.sin(2 * Math.PI * 6 * t));
        else env = Math.exp(-t * 22) * (0.6 + 0.4 * Math.sin(2 * Math.PI * 26 * t));
        d[i] = (rnd() * 2 - 1) * env * (kind === "pull" || kind === "return" ? 0.5 : 0.65);
      }
      return buf;
    }
    function play(kind, vol) {
      if (!on) return;
      var ac = ctx(); if (!ac) return;
      // лимит частоты: не чаще 1 звука в 120мс (защита от наложения при быстром листании)
      var now = Date.now();
      if (now - lastPlay < 120 && kind !== "pull" && kind !== "return") return;
      lastPlay = now;
      // реальные mp3 (свободная лицензия) с fallback на WebAudio-генерацию
      var MP3 = {
        pull: "assets/library/audio/book-drop.mp3",
        open: "assets/library/audio/paper-turn.mp3",
        flip: "assets/library/audio/page-flip-1.mp3",
        back: "assets/library/audio/page-flip-2.mp3",
        return: "assets/library/audio/page-flip-3.mp3"
      };
      if (MP3[kind]) {
        var a = new Audio(MP3[kind]);
        a.volume = (vol || 0.4) * 0.9;
        a.play().catch(function () { /* fallback ниже */ });
        return;
      }
      if (!cache[kind]) cache[kind] = make(kind);
      if (!cache[kind]) return;
      var src = ac.createBufferSource(); src.buffer = cache[kind];
      var g = ac.createGain(); g.gain.value = vol || 0.4;
      src.connect(g); g.connect(ac.destination); src.start();
    }
    var lastPlay = 0;
    var LS_SND = "library.sound";
    function soundSave() {
      try { localStorage.setItem(LS_SND, String(on)); } catch (e) {}
    }
    function soundLoad() {
      try { on = localStorage.getItem(LS_SND) !== "false"; } catch (e) {}
    }
    return {
      play: play, on: function () { return on; }, set: function (v) { on = v; },
      save: soundSave, load: soundLoad
    };
  })();

  /* ================= ДИНАМИЧЕСКОЕ ЗАТЕНЕНИЕ =================
   Источник света условно сверху-справа от камеры. Каждые ~80мс пересчитываем
   затенение книг (градиент в темноту), взаимные тени и тень на полке. */
  var lightTimer = null, shadowMap = new WeakMap(), lightPaused = false;
  function pauseLightLoop(v) { lightPaused = v; }
  function computeShadow(i, x) {
    // x — горизонтальная позиция книги (0..1); свет сверху-справа
    var dir = (x - 0.5) * 2;            // -1..1
    var shade = Math.max(0.18, 0.5 - dir * 0.22); // чем левее — тем темнее
    var book = row.children[i];
    if (!book) return;
    book.style.setProperty("--shade", shade.toFixed(3));
    var sh = shadowMap.get(book);
    if (sh) sh.style.transform = "translateX(" + (dir * 6) + "px)";
  }
  function startLightLoop() {
    if (lightTimer) return;
    lightTimer = setInterval(function () {
      if (lightPaused || document.hidden) return; // не делаем невидимую работу (вкладка скрыта)
      var books = row.children;
      for (var i = 0; i < books.length; i++) {
        var r = books[i].getBoundingClientRect();
        var cx = (r.left + r.width / 2) - (window.innerWidth / 2);
        computeShadow(i, cx / (window.innerWidth / 2) * 0.5 + 0.5);
      }
    }, 80);
  }
  function stopLightLoop() { if (lightTimer) { clearInterval(lightTimer); lightTimer = null; } }
  var scene, shelf, row, reader, spread, pL, pR, bar, lens;
  function q(s) { return document.querySelector(s); }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  function buildShelf() {
    scene = el("div", "lib-scene");
    shelf = el("div", "lib-shelf");
    row = el("div", "lib-row");
    CONFIG.books.forEach(function (b, i) {
      var book = el("div", "lib-book");
      book.style.setProperty("--bc", b.color);
      book.style.setProperty("--bh", b.h + "px");
      book.style.setProperty("--bw", (b.w || 64) + "px");
      if (b.font) book.style.setProperty("--book-font", b.font);
      if (b.tone) book.style.setProperty("--book-tone", b.tone);
      if (b.tex) book.style.setProperty("--tex", "url(" + BASE + "assets/" + b.tex + ")");
      // тень на полку (элемент для динамического смещения в computeShadow)
      var sh = el("div", "lib-box-shadow");
      shadowMap.set(book, sh);
      book.appendChild(sh);
      book.tabIndex = 0;
      book.setAttribute("role", "button");
      book.setAttribute("aria-label", "Открыть книгу " + b.title);
      book.appendChild(el("div", "ornament"));
      // 5 параллелепипедов: корешок (П5), блок страниц (П1), одна страница (П2),
      // левая обложка (П3), правая обложка (П4 с названием)
      var bdSpine = el("div", "bd bd-spine");
      bdSpine.appendChild(el("div", "face face-side"));
      var bdPages = el("div", "bd bd-pages-block");
      bdPages.appendChild(el("div", "face face-pg"));
      var bdSingle = el("div", "bd bd-single-page");
      bdSingle.appendChild(el("div", "face face-pg"));
      var bdCoverL = el("div", "bd bd-cover-l");
      bdCoverL.appendChild(el("div", "face face-cv"));
      var bdCoverR = el("div", "bd bd-cover-r");
      bdCoverR.appendChild(el("div", "face face-cv"));
      bdCoverR.appendChild(el("div", "title", b.title));
      book.appendChild(bdSpine); book.appendChild(bdPages);
      book.appendChild(bdSingle); book.appendChild(bdCoverL); book.appendChild(bdCoverR);
      book.addEventListener("click", function () { openBook(i); });
      book.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openBook(i); }
      });
      row.appendChild(book);
    });
    shelf.appendChild(row);
    shelf.appendChild(el("div", "lib-board"));
    scene.appendChild(shelf);

    reader = el("div", "lib-reader");
    bar = el("div", "lib-bar");
    var bPrev = el("button", null, "◀ Назад"); bPrev.type = "button";
    var bToc = el("button", null, "☰ Оглавление"); bToc.type = "button";
    var bNext = el("button", null, "Далее ▶"); bNext.type = "button";
    var bLens = el("button", null, "🔍 Лупа"); bLens.type = "button";
    var bLensMode = el("button", "lens-mode", "Лупа: область 🔳"); bLensMode.type = "button";
    var bSnd = el("button", null, "🔊 Звук: вкл"); bSnd.type = "button";
    var bClose = el("button", null, "✕ Закрыть"); bClose.type = "button";
    var pos = el("span", "lpos", "–");
    bPrev.onclick = function () { flip(-1); };
    bNext.onclick = function () { flip(1); };
    bToc.onclick = function () { Sound.play("flip", .4); showToc(); };
    bClose.onclick = closeBook;
    bSnd.onclick = function () { Sound.set(!Sound.on()); bSnd.textContent = Sound.on() ? "🔊 Звук: вкл" : "🔇 Звук: выкл"; Sound.save(); };
    bLens.onclick = function () { toggleLens(); };
    bLensMode.onclick = function () { cycleLensMode(); };
    bar.appendChild(bPrev); bar.appendChild(bToc); bar.appendChild(pos); bar.appendChild(bNext);
    bar.appendChild(bLens); bar.appendChild(bLensMode); bar.appendChild(bSnd); bar.appendChild(bClose);

    spread = el("div", "lib-spread");
    pL = el("div", "lib-page left");
    pR = el("div", "lib-page right");
    spread.appendChild(pL); spread.appendChild(pR);
    reader.appendChild(bar); reader.appendChild(spread);

    lens = el("div", "lib-lens");
    document.body.appendChild(scene);
    document.body.appendChild(reader);
    document.body.appendChild(lens);
    document.body.classList.add("lib-mode");
  }

  /* ================= АНИМАЦИИ: открытие книги ================= */
  function openBook(i) {
    if (!canNext(state, "pulling")) return;
    go("pulling"); sel = i;
    var book = row.children[i];
    Sound.play("pull", .5);
    book.classList.add("pulling");
    setTimeout(function () {
      if (state !== "pulling") return;
      go("opening");
      scene.classList.add("is-opening");
      Sound.play("open", .45);
      book.classList.add("opening");
      // П4 поворачивается на 90° за первые полфазы; затем подключается П2 (одна страница)
      setTimeout(function () {
        if (state !== "opening") return;
        book.classList.add("phase2");
      }, CONFIG.anim.open / 2);
      setTimeout(function () {
        if (state !== "opening") return;
        go("zooming");
        book.classList.add("zooming");
        setTimeout(function () {
          if (state !== "zooming") return;
          book.style.visibility = "hidden";
          showReader(i);
        }, CONFIG.anim.zoom);
      }, CONFIG.anim.open);
    }, CONFIG.anim.pull);
  }

  function closeBook() {
    if (!canNext(state, "closing")) return;
    go("closing");
    Sound.play("flip", .4);
    reader.classList.remove("open");
    var book = row.children[sel];
    book.style.visibility = "";
    scene.classList.remove("is-opening");
    setTimeout(function () {
      book.classList.remove("zooming");
      book.classList.remove("phase2");
      if (!canNext(state, "returning")) return;
      go("returning");
      Sound.play("return", .45);
      setTimeout(function () {
        book.classList.remove("pulling", "opening");
        go("shelf"); sel = -1;
      }, 60);
    }, 60);
  }

  /* ================= ЧИТАЛКА ================= */
  var LS_POS = "library.position"; // {book, page}
  function posSave() {
    try { localStorage.setItem(LS_POS, JSON.stringify({ book: sel, page: cur })); } catch (e) {}
  }
  function posLoad() {
    try { return JSON.parse(localStorage.getItem(LS_POS) || "null"); } catch (e) { return null; }
  }
  function showReader(i) {
    var id = CONFIG.books[i].id;
    var pages;
    if (id === "articles") pages = articlePages();
    else if (id === "learning") pages = learningPages();
    else if (id === "book") pages = volumePages();
    else if (id === "video") pages = videoPages();
    else pages = authorPages();
    pages = pages.length ? pages : [noContent()];
    pagesObj = pages;
    // восстановление позиции (только если книга та же и страница в диапазоне)
    var saved = posLoad();
    cur = 0;
    if (saved && saved.book === i && typeof saved.page === "number" && saved.page >= 0 && saved.page < pages.length) {
      cur = saved.page;
    }
    state = "reading";
    reader.classList.add("open");
    render();
    posSave();
  }

  /* пагинация по offsetHeight: разбиваем массив блоков на «страницы» по высоте */
  function paginate(blocks, pageEl) {
    var pagesArr = [], curBlocks = [];
    var container = el("div");
    container.style.cssText = "visibility:hidden;position:absolute;width:" + pageEl.clientWidth + "px;font-size:17px;line-height:1.78;padding:34px 38px;";
    document.body.appendChild(container);
    blocks.forEach(function (b) {
      var tmp = container.cloneNode(false);
      tmp.innerHTML = b;
      document.body.appendChild(tmp);
      var h = tmp.offsetHeight;
      document.body.removeChild(tmp);
      if (h > pageEl.clientHeight && curBlocks.length) {
        pagesArr.push(curBlocks); curBlocks = [b];
      } else curBlocks.push(b);
    });
    if (curBlocks.length) pagesArr.push(curBlocks);
    document.body.removeChild(container);
    return pagesArr.map(function (arr) { return arr.join(""); });
  }

  var pagesObj = [];
  function render() {
    var show = pagesObj.slice(cur, cur + 2);
    pL.innerHTML = show[0] ? show[0] : '<p style="color:#8a7a60">·</p>';
    pR.innerHTML = show[1] ? show[1] : (cur + 1 >= pagesObj.length ? '<p style="color:#8a7a60">— конец раздела —</p>' : '<p style="color:#8a7a60">·</p>');
    bar.querySelector(".lpos").textContent = (cur + 1) + " / " + pagesObj.length;
  }
  function flip(dir) {
    var n = pagesObj.length;
    var nx = cur + dir * 2;
    if (nx < 0 || nx >= n) return;
    Sound.play(dir > 0 ? "flip" : "back", .4);
    cur = nx; render(); posSave();
  }

  /* ================= КОНТЕНТ ================= */
  function noContent() { return '<h2>Раздел скоро наполнится</h2><p>Мы готовим материалы — загляните позже.</p>'; }

  function fetchJSON(url, cb) {
    fetch(url).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); }).then(cb)
      .catch(function (e) { console.error("[library] загрузка", url, e); cb(null); });
  }

  function articlePages() {
    var blocks = ['<h1>Статьи</h1><p>135 публикаций — безопасности, деньги, здоровье, госуслуги, нейросети.</p>'];
    // заглушки-ссылки на реальные статьи (полный каталог — из articles.json при следующей итерации)
    for (var i = 0; i < 5; i++) blocks.push('<p>→ <a href="' + BASE + 'articles/">Читать статьи на сайте</a> (каталог №' + (i + 1) + ')</p>');
    return paginate(blocks, pL);
  }
  function learningPages() {
    var levels = ["Уровень 0 — Без нейросетей. Фундамент", "Уровень 1 — Первое знакомство с нейросетью", "Уровень 2 — Нейросети в быту", "Уровень 3 — Промты: как просить правильно", "Уровень 4 — Агенты и автоматизация"];
    var blocks = ['<h1>Обучение</h1><p>Пять уровней — от фундамента до автоматизации.</p>'];
    levels.forEach(function (l) { blocks.push("<h2>" + l + "</h2><p><a href='" + BASE + "learning/'>Открыть уровень на сайте</a></p>"); });
    return paginate(blocks, pL);
  }
  function volumePages() {
    var volumes = ["Том 1. Знакомство с нейросетями", "Том 2. Заработок и развитие", "Том 3. Инструменты и сервисы", "Том 4. Практика и справочник"];
    var blocks = ['<h1>Книга — четыре тома</h1>'];
    volumes.forEach(function (v, i) { blocks.push("<h2>" + v + "</h2><p><a href='" + BASE + "books/'>Открыть том на сайте</a></p>"); });
    return paginate(blocks, pL);
  }
  function videoPages() {
    return ['<h1>Видео</h1><div class="lib-video-ph">🎬 Здесь скоро будут видеоролики<br><small>YouTube · Rutube · VK Видео</small></div><p><a href="' + BASE + '">На главную</a></p>'];
  }
  function authorPages() {
    return ['<h1>Об авторе</h1><p>Татьяна Зенина, Астрахань. Мне за шестьдесят. Пишу о нейросетях простыми словами — про книги, безопасность, деньги и здоровье.</p><h2>Это действительно я, и меня можно поддержать</h2><p><a href="https://t.me/neuro_retree">Telegram</a> · <a href="https://vk.com/club242405739">ВКонтакте</a> · <a href="https://boosty.to/tatzen">Boosty</a> · <a href="mailto:neuro-retree@ya.ru">Почта</a></p>'];
  }

  function showToc() {
    Sound.play("flip", .4);
    cur = 0; render();
  }

  /* ================= ЛУПА (режимы A/B + localStorage; 2x, строго за курсором) ================= */
  var lensOn = false, lensMode = "area"; // area (B) | text (A)
  var lensBtn = null, lensModeBtn = null;
  var LS_LENS = "library.lens"; // {on, mode}

  function lensSave() {
    try { localStorage.setItem(LS_LENS, JSON.stringify({ on: lensOn, mode: lensMode })); } catch (e) {}
  }
  function lensLoad() {
    try {
      var d = JSON.parse(localStorage.getItem(LS_LENS) || "{}");
      if (typeof d.on === "boolean") lensOn = d.on;
      if (d.mode === "text" || d.mode === "area") lensMode = d.mode;
    } catch (e) {}
  }
  function toggleLens() {
    lensOn = !lensOn;
    document.body.classList.toggle("lib-lens-on", lensOn);
    if (!lensBtn) lensBtn = bar.querySelector("button:nth-child(5)");
    if (lensBtn) lensBtn.textContent = lensOn ? "🔍 Лупа: вкл" : "🔍 Лупа: выкл";
    if (!lensOn) lens.style.display = "none";
    lensSave();
  }
  function cycleLensMode() {
    lensMode = lensMode === "area" ? "text" : "area";
    if (!lensModeBtn) lensModeBtn = bar.querySelector("button:nth-child(6)") || bar.querySelector(".lens-mode");
    if (lensModeBtn) lensModeBtn.textContent = lensMode === "area" ? "Лупа: область 🔳" : "Лупа: текст 🔤";
    lensSave();
    lens.style.display = "none";
  }

  document.addEventListener("mousemove", function (e) {
    if (!lensOn) return;
    var t = e.target;
    var page = t && t.closest ? t.closest(".lib-page") : null;
    if (!page) { lens.style.display = "none"; return; }
    var r = page.getBoundingClientRect();
    var w = page.offsetWidth;
    lens.innerHTML = "";
    var cl;
    if (lensMode === "area" || true) {
      // область: клонируем страницу целиком
      cl = page.cloneNode(true);
      cl.style.cssText = "position:absolute;top:0;left:0;width:" + w + "px;padding:34px 38px;box-shadow:none;border:0;border-radius:0;";
    }
    lens.appendChild(cl);
    lens.style.display = "block";
    // центр строго на курсоре; смещение к краю, чтобы не обрезать
    var R = 130, L = lens.offsetWidth || 236;
    var offX = e.clientX - r.left, offY = e.clientY - r.top;
    cl.style.transform = "translate(" + (-offX * 2 + R) + "px," + (-offY * 2 + R) + "px) scale(2)";
    lens.style.left = e.clientX + "px"; lens.style.top = e.clientY + "px";
  });

  /* ================= ИНИЦИАЛИЗАЦИЯ ================= */
  function init() {
    buildShelf();
    lensLoad();
    Sound.load();
    startLightLoop();
    // пауза светового цикла, когда полка вне экрана (полка внизу страницы)
    if ("IntersectionObserver" in window) {
      try {
        var io = new IntersectionObserver(function (entries) {
          pauseLightLoop(!entries[0].isIntersecting);
        }, { rootMargin: "200px" });
        io.observe(scene);
      } catch (e) {}
    }
    // синхронизируем кнопки с загруженными настройками
    if (lensOn) {
      document.body.classList.add("lib-lens-on");
      if (lensBtn) lensBtn.textContent = "🔍 Лупа: вкл";
    }
    if (!Sound.on()) {
      var sb = bar.querySelector("button:has-text('Звук')") || bar.querySelectorAll("button")[6];
      if (sb) sb.textContent = "🔇 Звук: выкл";
    }
    // запоминаем потребность в пользовательском жесте для AudioContext
    document.addEventListener("click", function once() {
      document.removeEventListener("click", once);
      Sound.play("flip", .01); // прогрев контекста
    }, { once: true });
    console.log("[library.js] книжная полка готова");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();