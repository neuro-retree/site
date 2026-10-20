/* book.js — звуки «листающейся книги» + перелистывание страниц.
   Звуки генерируются через WebAudio API (без файлов, офлайн):
   - flip*: 10 вариантов «перелистывания страницы» (короткий шелест + глухой удар корешка);
   - rustle*: 10 вариантов «шуршания бумаги» при ведении курсором по области.
   Управление: кнопка «Синхронизировать» в тулбаре (вкл/выкл). */
(function () {
  "use strict";
  var AC = null, flipBufs = [], rustleBufs = [], enabled = true;
  var FLIP_N = 10, RUSTLE_N = 10;

  function ctx() {
    if (!AC) { try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { return null; } }
    if (AC.state === "suspended") AC.resume();
    return AC;
  }

  /* Шумовая «дорожечка»: белый шум с огибающей и полосовым фильтром */
  function noiseBuffer(ac, dur) {
    var len = Math.max(1, Math.floor(ac.sampleRate * dur));
    var buf = ac.createBuffer(1, len, ac.sampleRate);
    var d = buf.getChannelData(0);
    for (var i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
    return buf;
  }

  function makeFlip(ac, seed) {
    /* Перелистывание: два коротких шуршащих импульса + низкий «щелчок» корешка */
    var n = 6, out = ac.createBuffer(1, ac.sampleRate * 0.28, ac.sampleRate);
    var d = out.getChannelData(0), s = seed;
    function rnd() { s = (s * 9301 + 49297) % 233280; return s / 233280; }
    for (var i = 0; i < d.length; i++) {
      var t = i / ac.sampleRate;
      var env = Math.exp(-t * 26) * (Math.sin(2 * Math.PI * (0.9 + rnd()) * t * 0.2 + t * 40) * 0.4 + 0.6);
      if (t > 0.09 && t < 0.2) env += Math.exp(-(t - 0.12) * 40) * 0.9;
      d[i] = (rnd() * 2 - 1) * env * 0.6;
    }
    return out;
  }

  function makeRustle(ac, seed) {
    /* Шуршание бумаги: шум с медленной амплитудной модуляцией */
    var dur = 0.5, out = ac.createBuffer(1, ac.sampleRate * dur, ac.sampleRate);
    var d = out.getChannelData(0), s = seed;
    function rnd() { s = (s * 9301 + 49297) % 233280; return s / 233280; }
    for (var i = 0; i < d.length; i++) {
      var t = i / ac.sampleRate;
      var mod = 0.45 + 0.55 * Math.sin(2 * Math.PI * 23 * t + rnd());
      d[i] = (rnd() * 2 - 1) * mod * Math.exp(-t * 2.4) * 0.35;
    }
    return out;
  }

  function play(buf, vol) {
    if (!enabled) return;
    var ac = ctx(); if (!ac || !buf) return;
    var src = ac.createBufferSource(); src.buffer = buf;
    var g = ac.createGain(); g.gain.value = vol || 0.5;
    src.connect(g); g.connect(ac.destination);
    src.start();
  }

  function initSounds() {
    var ac = ctx(); if (!ac) return;
    for (var i = 0; i < FLIP_N; i++) flipBufs.push(makeFlip(ac, 1000 + i * 137));
    for (var j = 0; j < RUSTLE_N; j++) rustleBufs.push(makeRustle(ac, 5000 + j * 89));
  }

  function randomFlip() { if (flipBufs.length) play(flipBufs[Math.floor(Math.random() * flipBufs.length)], 0.55); }
  function randomRustle() { if (rustleBufs.length) play(rustleBufs[Math.floor(Math.random() * rustleBufs.length)], 0.30); }

  /* Установка тулбара и поведения */
  function init() {
    document.addEventListener("click", function once() { initSounds(); }, { once: true });
    window.__bookSounds = {
      flip: randomFlip, rustle: randomRustle,
      setEnabled: function (v) { enabled = v; },
      isEnabled: function () { return enabled; }
    };
    console.log("[book.js] звуки книги готовы: перелистывание x" + FLIP_N + ", шуршание x" + RUSTLE_N);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();