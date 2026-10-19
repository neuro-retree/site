# -*- coding: utf-8 -*-
"""rebuild_site.py — сборка статических страниц сайта «Нейросети для жизни».

Генерирует из Markdown-статей в корне site_project:
  - articles/<slug>/index.html   — отдельная HTML-страница каждой статьи
  - articles/index.html          — каталог статей с поиском и фильтром
  - tools/index.html             — инструменты (конструктор промптов, проверка сообщений)
  - learning/index.html          — три учебных маршрута
  - data/articles.json           — машинный реестр статей
  - sitemap.xml, rss.xml         — обновляются реальными адресами
  - index.html                   — главная пересобирается (карточки-ссылки)

Запуск: python scripts/rebuild_site.py
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://neuro-retree.github.io/site/"
AUTHOR = "Татьяна Зенина"
SITE_NAME = "Нейросети для жизни"

ARTICLES = [
    {"slug": "article_2fa_zashchita", "title": "Двухфакторная защита за 5 минут: второй замок для пенсии и Госуслуг", "tags": ["безопасность"], "desc": "Как включить подтверждение входа по коду и зачем это нужно для ваших денег и документов."},
    {"slug": "article_33_dipfeyki", "title": "Поддельный голос внука: как распознать дипфейк и не отдать деньги", "tags": ["безопасность"], "desc": "Как проверить подозрительный звонок и защитить близких от мошенников с новыми технологиями."},
    {"slug": "article_gosuslugi_vyplaty", "title": "Госуслуги: как узнать, какие выплаты и льготы вам положены", "tags": ["госуслуги"], "desc": "Какие сведения доступны на Госуслугах и в ЕГИССО и что делать дальше."},
    {"slug": "article_spisali_za_prilozhenie", "title": "Списали деньги за бесплатное приложение — как отключить подписку и вернуть своё", "tags": ["деньги"], "desc": "Пошагово: где найти подписку, как её отключить и попробовать вернуть деньги."},
    {"slug": "article_152fz_dannye", "title": "152-ФЗ: ваши данные, ваши права — просто о главном", "tags": ["право"], "desc": "Что компаниям можно делать с вашими данными и как потребовать их удалить."},
    {"slug": "article_statiny_6_mifov", "title": "Статины: 6 мифов, о которых важно знать", "tags": ["здоровье"], "desc": "Разбираем самые распространённые страхи про препараты, снижающие холестерин."},
    {"slug": "article_bady_riski", "title": "БАДы: правда и риски, чтобы не навредить себе", "tags": ["здоровье"], "desc": "Как читать состав, где искать проверенную информацию и почему БАДы не заменяют лекарства."},
    {"slug": "article_davlenie_posle_60", "title": "Давление после 60: какая норма и как контролировать", "tags": ["здоровье"], "desc": "Понятно о цифрах тонометра, дневнике измерений и визите к врачу."},
    {"slug": "article_20_cheklist_10_vecherov", "title": "Чек-лист «10 вечеров»: бесплатный старт в нейросетях", "tags": ["нейросети"], "desc": "Простые первые шаги: как за десять вечеров подружиться с нейросетью и не испугаться."},
]

CATEGORY_LABELS = {
    "безопасность": "Безопасность",
    "нейросети": "Нейросети",
    "здоровье": "Здоровье",
    "деньги": "Деньги",
    "право": "Право",
    "госуслуги": "Госуслуги",
}

BUILD_DATE = date(2026, 10, 19).isoformat()


# ---------- Markdown -> HTML (безопасная минимальная реализация) ----------

def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(t):
    s = esc(t)
    s = re.sub(r"\[([^\]]+)\]\((https?:[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(^|[^*])\*([^*\n]+)\*", r"\1<em>\2</em>", s)
    return s


def md_to_html(t):
    """Возвращает (html_body, toc), где toc — список (id, уровень, текст)."""
    lines = t.split("\n")
    out = []
    list_type = None
    toc = []
    h_count = 0

    def close_list():
        nonlocal list_type
        if list_type:
            out.append("</%s>" % list_type)
            list_type = None

    for raw in lines:
        s = raw.strip()
        if not s:
            close_list()
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            close_list()
            level = len(m.group(1))
            txt = inline(m.group(2))
            h_count += 1
            hid = "h%d" % h_count
            tag = "h2" if level <= 2 else "h3" if level == 3 else "h4"
            out.append('<%s id="%s">%s</%s>' % (tag, hid, txt, tag))
            if level <= 3:
                toc.append((hid, level, re.sub(r"<[^>]+>", "", m.group(2))))
        elif re.match(r"^\s*[-*•]\s+", s):
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            out.append("<li>%s</li>" % inline(re.sub(r"^\s*[-*•]\s+", "", s)))
        elif re.match(r"^\s*\d+[.)]\s+", s):
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append("<li>%s</li>" % inline(re.sub(r"^\s*\d+[.)]\s+", "", s)))
        elif re.match(r"^\s*>+\s?", s):
            close_list()
            out.append("<blockquote>%s</blockquote>" % inline(re.sub(r"^\s*>+\s?", "", s)))
        elif re.match(r"^\s*-{3,}\s*$", s):
            close_list()
            out.append("<hr>")
        else:
            close_list()
            out.append("<p>%s</p>" % inline(s))
    close_list()
    return "\n".join(out), toc


# ---------- Каркас страницы ----------

CSS = """
*{box-sizing:border-box}
:root{--bg:#f4f7f9;--card:#fff;--ink:#1f2d3a;--accent:#0e7c66;--accent2:#1565a8;--soft:#5b7080;--line:#e2e9ee;--shadow:0 2px 10px rgba(20,40,60,.08);--fs:1.1875rem}
html[data-contrast="high"]{--bg:#000;--card:#111;--ink:#fff;--soft:#e6e6e6;--line:#666;--accent:#ffe14d;--accent2:#9fd8ff;--shadow:none}
body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,'Arial',sans-serif;background:var(--bg);color:var(--ink);line-height:1.7;font-size:var(--fs)}
a{color:var(--accent2);text-decoration:underline;text-underline-offset:0.18em}
a:hover{text-decoration-thickness:2px}
.wrap{max-width:1080px;margin:0 auto;padding:0 18px}
header{background:linear-gradient(135deg,#133a33,#0e7c66 60%%,#1565a8);color:#fff;padding:28px 0 24px}
header .inline{display:flex;flex-wrap:wrap;gap:18px;align-items:center}
header .title{font-size:24px;margin:0;color:#fff}
header .links a{display:inline-block;background:rgba(255,255,255,.16);color:#fff;border:1px solid rgba(255,255,255,.35);padding:7px 14px;border-radius:20px;margin:4px 8px 4px 0;font-size:15px}
.breadcrumbs{font-size:14px;color:#5b7080;margin:18px 0 8px}
main{padding:10px 0 60px}
.card{background:#fff;border:1px solid #e2e9ee;border-radius:14px;box-shadow:0 2px 10px rgba(20,40,60,.08);overflow:hidden;display:flex;flex-direction:column;height:100%%}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px;margin-top:18px}
.card img{width:100%%;height:100%%;object-fit:cover;object-position:center;display:block}
.card .cov{width:100%%;aspect-ratio:16/9;overflow:hidden;background:#dfe9e4;display:flex;align-items:center;justify-content:center}
.card .body{padding:14px 16px 18px;flex:1;display:flex;flex-direction:column}
.card h3{margin:0 0 8px;font-size:19px;line-height:1.3}
.card p{margin:0 0 12px;color:#5b7080;font-size:15px}
.tag{font-size:12.5px;background:#dcebe6;color:#0e6a57;padding:3px 9px;border-radius:12px;align-self:flex-start;margin-bottom:8px}
.btn-read{margin-top:auto;background:#0e7c66;color:#fff;border:0;padding:11px 0;border-radius:10px;font-size:16px;cursor:pointer;text-align:center;min-height:44px;display:inline-flex;align-items:center;justify-content:center}
.btn-read:hover{background:#0b6a58;text-decoration:none}
.article{background:#fff;border:1px solid #e2e9ee;border-radius:14px;padding:30px 32px;box-shadow:0 2px 10px rgba(20,40,60,.08)}
.article h1{margin:0 0 8px;color:#133a33;font-size:28px;line-height:1.3}
.article .meta{color:#5b7080;font-size:14px;margin-bottom:16px}
.article h2{margin:26px 0 10px;color:#0e7c66;font-size:23px}
.article h3{margin:22px 0 8px;color:#153a4d;font-size:20px}
.article p{margin:10px 0}
.article ul,.article ol{margin:10px 0;padding-left:26px}
.article blockquote{border-left:4px solid #e2e9ee;margin:12px 0;padding:6px 16px;color:#5b7080}
.article hr{border:0;border-top:1px solid #e2e9ee;margin:20px 0}
.article img{max-width:100%%;height:auto}
.toc{background:#f4f7f9;border:1px solid #e2e9ee;border-radius:10px;padding:12px 18px;margin:18px 0}
.toc b{color:#153a4d}
.toc ul{margin:6px 0 0;padding-left:20px;font-size:15px}
.tools-bar{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 6px}
.tools-bar button{padding:10px 16px;font-size:15px;border:1px solid #e2e9ee;border-radius:10px;background:#f4f7f9;color:#1f2d3a;cursor:pointer;min-height:44px}
.tools-bar button:hover{background:#e7eef2}
.related{background:#f4f7f9;border:1px solid #e2e9ee;border-radius:10px;padding:14px 18px;margin-top:24px}
.related a{display:block;margin:6px 0}
.cta{background:#e7f4f0;border-left:4px solid #0e7c66;padding:12px 16px;border-radius:8px;margin-top:24px}
.footer{border-top:1px solid #e2e9ee;margin-top:40px;padding:18px 0;color:#5b7080;font-size:14px}
.a11ybar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:center;padding:10px 16px;max-width:1080px;margin:0 auto;font-size:15px;color:var(--soft)}
.a11ybar button{min-height:44px;min-width:44px;font-size:16px;font-weight:600;color:var(--ink);background:#fff;border:2px solid var(--line);border-radius:8px;cursor:pointer;padding:6px 12px}
.a11ybar button:hover{background:#eef2f5}
.skip{position:absolute;left:-999px;top:0}
.skip:focus{left:8px;top:8px;background:#fff;padding:10px 14px;z-index:60;border:2px solid var(--accent);border-radius:8px}
html[data-contrast="high"]{--bg:#000;--card:#111;--ink:#fff;--soft:#e6e6e6;--line:#666;--accent:#ffe14d;--accent2:#9fd8ff}
button:focus-visible,a:focus-visible{outline:3px solid #e5a000;outline-offset:3px}
.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:18px}
.toolbar input[type=search]{flex:1;min-width:220px;padding:11px 14px;font-size:16px;border:1px solid #e2e9ee;border-radius:10px;background:#fff}
.toolbar select{padding:11px 14px;font-size:16px;border:1px solid #e2e9ee;border-radius:10px;background:#fff}
.search-status{color:#5b7080;font-size:14px}
.tool-page{background:#fff;border:1px solid #e2e9ee;border-radius:14px;padding:28px 30px;box-shadow:0 2px 10px rgba(20,40,60,.08)}
.tool-page h1{margin:0 0 10px;color:#133a33;font-size:26px}
.tool-page label{display:block;font-weight:600;margin:16px 0 6px;color:#153a4d}
.tool-page input,.tool-page select,.tool-page textarea{width:100%%;padding:11px 14px;font-size:16px;border:1px solid #e2e9ee;border-radius:10px;background:#fff;color:#1f2d3a}
.tool-page textarea{min-height:120px}
.tool-page .out{background:#f4f7f9;border:1px solid #e2e9ee;border-radius:10px;padding:16px;margin-top:16px;white-space:pre-wrap;font-size:16px}
.btn{display:inline-block;background:#0e7c66;color:#fff;border:0;padding:11px 20px;border-radius:10px;font-size:16px;cursor:pointer;margin-top:12px;min-height:44px}
.btn:hover{background:#0b6a58}
@media(max-width:560px){.wrap{padding-inline:14px}.h1{font-size:26px}.grid{grid-template-columns:1fr}.article{padding:20px 15px}.card .body{padding:12px 12px 14px}.panel{padding:20px 14px}.tools-bar{flex-direction:column}.toolbar select{width:100%%}}@media(min-width:561px) and (max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}.article{padding:22px 18px}.article h1{font-size:24px}}
@media print{.tools-bar,.breadcrumbs,.footer,.related{display:none}.article{border:0;box-shadow:none;padding:0}}
"""


def page(title, desc, body, canonical, extra_head=""):
    return """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%s</title>
<meta name="description" content="%s">
<meta name="theme-color" content="#0b5c4f">
<link rel="canonical" href="%s">
<meta property="og:type" content="website">
<meta property="og:locale" content="ru_RU">
<meta property="og:site_name" content="Нейросети для жизни">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%schannel-avatar-neuro-retree.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="Нейросети для жизни — RSS" href="%srss.xml">
%s
<style>%s</style>
</head>
<body>
<a class="skip" href="#content" style="position:absolute;left:-999px">Перейти к тексту</a>
<div class="a11ybar" id="a11y-toolbar" aria-label="Настройки чтения"></div>
<header><div class="wrap inline">
  <div class="title">Нейросети для жизни</div>
  <div class="links">
    <a href="%s">Главная</a>
    <a href="%sarticles/">Статьи</a>
    <a href="%stools/">Инструменты</a>
    <a href="%slearning/">Обучение</a>
    <a href="%sslovar/">Словарь</a>
  </div>
</div></header>
<main><div class="wrap">
%s
</div></main>
<footer><div class="wrap footer">© 2026 Нейросети для жизни · %s, Астрахань · <a href="mailto:neuro-retree@yandex.ru?subject=Ошибка на сайте">Нашли ошибку? Напишите нам</a> · <a href="%srss.xml">RSS</a></div></footer>
<script src="/a11y-toggle.js" defer></script>
</body>
</html>""" % (
        html.escape(title), html.escape(desc[:190]), canonical,
        html.escape(title), html.escape(desc[:190]), canonical, BASE_URL,
        BASE_URL, extra_head, CSS, BASE_URL, BASE_URL, BASE_URL, BASE_URL, BASE_URL,
        body, AUTHOR, BASE_URL
    )


HEADER_HOME = """
<h1 style="font-size:30px;margin:20px 0 6px;color:#133a33">Нейросети для жизни</h1>
<p style="color:#5b7080;font-size:17px;margin:0 0 10px">Просто о главном: для людей в возрасте. Статьи, советы, личный опыт.</p>
<div style="display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 18px">
  <a style="background:#0e7c66;color:#fff;padding:11px 18px;border-radius:10px;font-size:16px" href="articles/">Все статьи</a>
  <a style="background:#1565a8;color:#fff;padding:11px 18px;border-radius:10px;font-size:16px" href="tools/">Инструменты</a>
  <a style="background:#5b7080;color:#fff;padding:11px 18px;border-radius:10px;font-size:16px" href="learning/">Обучение</a>
</div>
"""


def related_block(slug, tags):
    related = [a for a in ARTICLES if a["slug"] != slug and set(a["tags"]) & set(tags)]
    if not related:
        return ""
    items = "".join('<a href="%sarticles/%s/">%s</a>' % (BASE_URL, a["slug"], html.escape(a["title"])) for a in related[:3])
    return '<div class="related"><b>Читайте также по теме:</b>%s</div>' % items


# ---------- Страница статьи ----------

def build_article(a, md_text):
    body_html, toc = md_to_html(md_text)
    cat = CATEGORY_LABELS.get(a["tags"][0], a["tags"][0])
    toc_html = ""
    if len(toc) > 2:
        items = []
        for hid, level, txt in toc:
            items.append('<li style="margin-left:%dpx;list-style:%s"><a href="#%s">%s</a></li>' % (
                (level - 2) * 14 if level > 2 else 0,
                "none" if level > 2 else "disc",
                hid, html.escape(txt)))
        toc_html = '<div class="toc"><b>Содержание</b><ul>%s</ul></div>' % "".join(items)

    body = """
<div class="breadcrumbs"><a href="%s">Главная</a> → <a href="%sarticles/">Статьи</a> → %s</div>
<div class="article">
  <span class="tag">%s</span>
  <h1>%s</h1>
  <div class="meta">Проект «Нейросети для жизни» · %s, Астрахань · проверено %s</div>
  <div class="tools-bar">
    <button type="button" onclick="window.print()">Печать</button>
    <button type="button" onclick="copyLink()">Скопировать ссылку</button>
  </div>
  %s
  %s
  %s
  <div class="cta"><strong>Дорогие мои, напоследок.</strong> Больше простых историй про нейросети — в моём канале <a href="https://t.me/neuro_retree">t.me/neuro_retree</a>. Подпишитесь, чтобы не потерять. А если нужна книга «Нейросети для жизни» — напишите <a href="https://t.me/tatzenbot">@tatzenbot</a>.</div>
</div>
<script>function copyLink(){const u=location.href;if(navigator.clipboard){navigator.clipboard.writeText(u).then(()=>alert('Ссылка скопирована: '+u));}else{alert(u);}}</script>
""" % (BASE_URL, BASE_URL, html.escape(a["title"]), html.escape(cat), html.escape(a["title"]),
       AUTHOR, BUILD_DATE, toc_html, body_html, related_block(a["slug"], a["tags"]))

    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["title"],
        "inLanguage": "ru",
        "description": a["desc"],
        "author": {"@type": "Person", "name": AUTHOR},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "mainEntityOfPage": {"@type": "WebPage", "@id": "%sarticles/%s/" % (BASE_URL, a["slug"])}
    }, ensure_ascii=False)
    extra = '<script type="application/ld+json">%s</script>' % jsonld

    out = page(a["title"] + " — Нейросети для жизни", a["desc"],
               body, "%sarticles/%s/" % (BASE_URL, a["slug"]), extra)
    p = ROOT / "articles" / a["slug"] / "index.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(out, encoding="utf-8")
    # копируем обложку статьи в папку
    img_src = ROOT / (a["slug"] + ".png")
    img_dst = p.parent / (a["slug"] + ".png")
    if img_src.exists():
        img_dst.write_bytes(img_src.read_bytes())


# ---------- Каталог статей ----------

def build_catalog():
    cards = []
    for a in ARTICLES:
        cat = CATEGORY_LABELS.get(a["tags"][0], a["tags"][0])
        cards.append("""
<div class="card" data-slug="%s" data-title="%s" data-tags="%s">
  <a href="%sarticles/%s/"><span class="cov"><img src="%sarticles/%s/%s.png" alt="%s" loading="lazy"></span></a>
  <div class="body">
    <span class="tag">%s</span>
    <h3><a href="%sarticles/%s/">%s</a></h3>
    <p>%s</p>
    <a class="btn-read" href="%sarticles/%s/">Читать статью</a>
  </div>
</div>""" % (a["slug"], html.escape(a["title"]), ",".join(a["tags"]),
             BASE_URL, a["slug"], BASE_URL, a["slug"], a["slug"], html.escape(a["title"]),
             html.escape(cat), BASE_URL, a["slug"], html.escape(a["title"]),
             html.escape(a["desc"]), BASE_URL, a["slug"]))

    opts = "".join('<option value="%s">%s</option>' % (c, CATEGORY_LABELS[c]) for c in CATEGORY_LABELS)
    body = """
<div class="breadcrumbs"><a href="%s">Главная</a> → Статьи</div>
<h1 style="color:#133a33;font-size:28px;margin:8px 0 4px">Все статьи</h1>
<p style="color:#5b7080">Простые объяснения нейросетей, безопасности, денег, здоровья и государственных услуг.</p>
<div class="toolbar">
  <input id="catSearch" type="search" placeholder="Поиск: например, защита аккаунта" aria-label="Поиск по статьям">
  <select id="catSelect" aria-label="Тема"><option value="">Все темы</option>%s</select>
  <span id="catStatus" class="search-status" aria-live="polite"></span>
</div>
<div class="grid" id="catGrid">%s</div>
<script>
const cards=[].slice.call(document.querySelectorAll('#catGrid .card'));
const st=document.getElementById('catStatus');
function norm(v){return String(v||'').toLocaleLowerCase('ru-RU').replace(/ё/g,'е').trim();}
function upd(){
  const q=norm(document.getElementById('catSearch').value);
  const c=norm(document.getElementById('catSelect').value);
  let n=0;
  cards.forEach(cd=>{
    const hay=norm(cd.dataset.title+' '+cd.dataset.tags);
    const ok=(!q||hay.includes(q))&&(!c||cd.dataset.tags.split(',').indexOf(c)>=0);
    cd.style.display=ok?'':'none';
    if(ok)n++;
  });
  st.textContent='Найдено: '+n;
}
document.getElementById('catSearch').addEventListener('input',upd);
document.getElementById('catSelect').addEventListener('change',upd);
upd();
</script>
""" % (BASE_URL, opts, "".join(cards))
    out = page("Все статьи — Нейросети для жизни",
               "Каталог статей о нейросетях, цифровой безопасности, деньгах, здоровье и госуслугах простыми словами.",
               body, BASE_URL + "articles/")
    (ROOT / "articles" / "index.html").write_text(out, encoding="utf-8")


# ---------- Инструменты ----------

TOOLS_CSS = """
.tool-card{display:block;background:#fff;border:1px solid #e2e9ee;border-radius:14px;padding:22px 24px;margin:14px 0;box-shadow:0 2px 10px rgba(20,40,60,.08);color:#1f2d3a}
.tool-card:hover{text-decoration:none;border-color:#0e7c66}
.tool-card h2{margin:0 0 8px;color:#0e7c66;font-size:21px}
.tool-card p{margin:0;color:#5b7080}
"""


def build_tools():
    (ROOT / "tools").mkdir(parents=True, exist_ok=True)
    (ROOT / "tools" / "prompt-builder").mkdir(parents=True, exist_ok=True)
    (ROOT / "tools" / "sms-checker").mkdir(parents=True, exist_ok=True)
    card_prompt = """
<a class="tool-card" href="prompt-builder/">
  <h2>Конструктор запросов к нейросети</h2>
  <p>Соберите понятный промпт по шагам: задача, роль, исходные данные, формат ответа. Готовый текст можно скопировать.</p>
</a>"""
    card_sms = """
<a class="tool-card" href="sms-checker/">
  <h2>Проверка подозрительного сообщения</h2>
  <p>Ответьте на несколько вопросов про звонок или сообщение — и получите понятную памятку, как действовать.</p>
</a>"""
    card_memo = """
<a class="tool-card" href="pamiatka/">
  <h2>Генератор памятки из статьи</h2>
  <p>Выберите статью — получите короткую памятку «пять главных шагов» для печати или отправки близким.</p>
</a>"""

    body = """
<div class="breadcrumbs"><a href="%s">Главная</a> → Инструменты</div>
<h1 style="color:#133a33;font-size:28px;margin:8px 0 4px">Инструменты</h1>
<p style="color:#5b7080">Простые помощники, которые работают прямо в браузере. Никакие данные не отправляются на сервер.</p>
%s%s%s
""" % (BASE_URL, card_prompt, card_sms, card_memo)
    out = page("Инструменты — Нейросети для жизни", "Конструктор промптов и проверка подозрительных сообщений — бесплатные инструменты на сайте.", body, BASE_URL + "tools/", "<style>%s</style>" % TOOLS_CSS)
    (ROOT / "tools" / "index.html").write_text(out, encoding="utf-8")

    # ---- prompt-builder ----
    pb_body = """
<div class="breadcrumbs"><a href="%s">Главная</a> → <a href="%stools/">Инструменты</a> → Конструктор запросов</div>
<div class="tool-page">
<h1>Конструктор запросов к нейросети</h1>
<p style="color:#5b7080">Выберите задачу, опишите исходные данные и получите готовый промпт. Скопируйте его в любую нейросеть (GigaChat, Алиса, ChatGPT и другие).</p>

<label for="pbTask">Что нужно сделать?</label>
<select id="pbTask">
  <option value="объясни">Объяснить простыми словами</option>
  <option value="напиши">Написать текст (письмо, поздравление, заявление)</option>
  <option value="проверь">Проверить документ или текст на ошибки</option>
  <option value="план">Составить план или список шагов</option>
  <option value="переведи">Перевести и объяснить</option>
</select>

<label for="pbData">Что известно? Опишите своими словами</label>
<textarea id="pbData" placeholder="Например: нужно объяснить соседке, что такое нейросеть, простыми словами, с примером из огорода"></textarea>

<label for="pbAudience">Для кого ответ?</label>
<select id="pbAudience">
  <option value="для меня, человека старшего возраста, простыми словами, без сложных терминов">Для меня (простыми словами, без терминов)</option>
  <option value="для новичка, первого знакомства">Для новичка, первого знакомства</option>
  <option value="без ограничений">Без ограничений</option>
</select>

<label for="pbFormat">Какой формат ответа нужен?</label>
<select id="pbFormat">
  <option value="короткий понятный ответ">Короткий понятный ответ</option>
  <option value="пошаговая инструкция">Пошаговая инструкция</option>
  <option value="список из 5 пунктов">Список из 5 пунктов</option>
  <option value="пример текста">Пример текста</option>
</select>

<button class="btn" id="pbMake" type="button">Собрать запрос</button>
<div class="out" id="pbOut">Здесь появится готовый запрос.</div>
<button class="btn" id="pbCopy" type="button" style="display:none;background:#1565a8">Скопировать</button>
<p style="font-size:14px;color:#5b7080;margin-top:18px">Важно: не сообщайте нейросети пароли, коды из СМС, номера карт и паспортные данные. Проверяйте важные ответы по официальным источникам.</p>
</div>
<script>
const pbTask=document.getElementById('pbTask'),pbData=document.getElementById('pbData'),
pbAudience=document.getElementById('pbAudience'),pbFormat=document.getElementById('pbFormat'),
pbOut=document.getElementById('pbOut'),pbCopy=document.getElementById('pbCopy');
document.getElementById('pbMake').addEventListener('click',()=>{
  const t=pbTask.value,d=pbData.value.trim(),a=pbAudience.value,f=pbFormat.value;
  if(!d){pbOut.textContent='Пожалуйста, опишите, что вам нужно — одним-двумя предложениями.';pbCopy.style.display='none';return;}
  const taskText={объясни:'Объясни',напиши:'Напиши',проверь:'Проверь',план:'Составь план',переведи:'Переведи'}[t]||'Сделай';
  const pr='РОЛЬ: Ты — терпеливый и доброжелательный собеседник.\n\nЗАДАЧА: '+taskText+' следующее '+a+'.\n\nСОДЕРЖИМОЕ: '+d+'\n\nФОРМАТ ОТВЕТА: '+f+'. Не выдумывай факты. Если чего-то не знаешь — скажи честно. Не спрашивай лишнего, сразу приступай к делу.';
  pbOut.textContent=pr;pbCopy.style.display='inline-block';
});
pbCopy.addEventListener('click',()=>{navigator.clipboard.writeText(pbOut.textContent).then(()=>{pbCopy.textContent='Скопировано!';setTimeout(()=>pbCopy.textContent='Скопировать',1800);});});
</script>
""" % (BASE_URL, BASE_URL)
    page("Конструктор запросов — Нейросети для жизни", "Соберите понятный запрос к нейросети по шагам и скопируйте его.", pb_body, BASE_URL + "tools/prompt-builder/", "").__str__()
    (ROOT / "tools" / "prompt-builder" / "index.html").write_text(page("Конструктор запросов — Нейросети для жизни", "Соберите понятный запрос к нейросети по шагам и скопируйте его.", pb_body, BASE_URL + "tools/prompt-builder/"), encoding="utf-8")

    # ---- sms-checker ----
    sc_body = """
<div class="breadcrumbs"><a href="%s">Главная</a> → <a href="%stools/">Инструменты</a> → Проверка сообщения</div>
<div class="tool-page">
<h1>Проверка подозрительного сообщения</h1>
<p style="color:#5b7080">Отметьте, что происходит, — и получите памятку. Это подсказка для размышления, а не точный диагноз.</p>
<div id="scChecks">
<label><input type="checkbox" class="sc" value="srochno"> Вас торопят: «срочно», «прямо сейчас», «иначе будет поздно»</label>
<label><input type="checkbox" class="sc" value="money"> Просят перевести деньги или назвать данные карты</label>
<label><input type="checkbox" class="sc" value="code"> Просят назвать код из СМС или пароль</label>
<label><input type="checkbox" class="sc" value="link"> Прислали ссылку и просят перейти по ней</label>
<label><input type="checkbox" class="sc" value="relative"> Говорят, что они родственник, сотрудник банка или госоргана</label>
<label><input type="checkbox" class="sc" value="secret"> Просят никому не рассказывать о разговоре</label>
</div>
<button class="btn" id="scGo" type="button">Показать памятку</button>
<div class="out" id="scOut" style="display:none"></div>
</div>
<script>
document.getElementById('scGo').addEventListener('click',()=>{
  const vals=[].slice.call(document.querySelectorAll('.sc:checked')).map(x=>x.value);
  const o=document.getElementById('scOut');
  let lines=[];
  if(vals.length===0){lines.push('По отмеченным признакам сообщение выглядит обычным.');}
  else{
    lines.push('Вы отметили признаков риска: '+vals.length+'. Это повод остановиться и проверить.');
    if(vals.includes('srochno')||vals.includes('secret'))lines.push('• Торопят и просят молчать — главный признак давления. Настоящие банки и госорганы так не делают.');
    if(vals.includes('code'))lines.push('• Код из СМС — это доступ к вашим деньгам и аккаунтам. Его нельзя называть никому и никогда.');
    if(vals.includes('money'))lines.push('• Не переводите деньги и не называйте данные карты. Перезвоните сами по официальному номеру.');
    if(vals.includes('link'))lines.push('• Не переходите по ссылкам из подозрительных сообщений. Откройте сайт сами через поиск.');
    if(vals.includes('relative'))lines.push('• Если «родственник» просит денег — позвоните ему на тот номер, который вы знаете, и задайте вопрос, ответ на который знаете только вы двое.');
  }
  lines.push('', 'Что делать: 1) Не спешите. 2) Посоветуйтесь с близкими. 3) Сами позвоните в банк или организацию по номеру с официального сайта. 4) Не сообщайте коды и пароли.', 'Если вам кажется, что это мошенники, — расскажите родным и сообщите в банк.');
  o.style.display='block';o.textContent=lines.join('\\n');
});
</script>
""" % (BASE_URL, BASE_URL)
    (ROOT / "tools" / "sms-checker" / "index.html").write_text(page("Проверка подозрительного сообщения — Нейросети для жизни", "Интерактивная памятка: как распознать мошенническое сообщение и что делать.", sc_body, BASE_URL + "tools/sms-checker/"), encoding="utf-8")




def build_memo():
    (ROOT / "tools" / "pamiatka").mkdir(parents=True, exist_ok=True)
    _lines = []
    for _a in ARTICLES:
        _lines.append('ART[%s]={title:%s};' % (json.dumps(_a["slug"]), json.dumps(_a["title"], ensure_ascii=False)))
    json_articles = "\n".join(_lines)
    opts = ""
    for a in ARTICLES:
        opts += '<option value="%s">%s</option>' % (a["slug"], html.escape(a["title"]))
    body = """
<div class="breadcrumbs"><a href="%s">Главная</a> → <a href="%stools/">Инструменты</a> → Генератор памятки</div>
<div class="tool-page">
<h1>Генератор памятки из статьи</h1>
<p style="color:#5b7080">Выберите статью — ниже появится короткая памятка: пять главных шагов, что сделать сегодня и как проверить результат. Можно распечатать или отправить близким.</p>
<label for="memoArt">Статья</label>
<select id="memoArt">%s</select>
<button class="btn" id="memoGo" type="button">Показать памятку</button>
<div class="out" id="memoOut" style="display:none"></div>
<button class="btn" id="memoPrint" type="button" style="display:none;background:#1565a8">Печать памятки</button>
</div>
<script>
const memoArt=document.getElementById('memoArt'),memoOut=document.getElementById('memoOut'),memoPrint=document.getElementById('memoPrint');
const ART={};
%s
document.getElementById('memoGo').addEventListener('click',async()=>{
  const slug=memoArt.value;
  if(!ART[slug])return;
  const resp=await fetch('../../'+slug+'.md');
  if(!resp.ok){memoOut.textContent='Не удалось загрузить статью.';memoOut.style.display='block';return;}
  const md=await resp.text();
  const body=md.split(/[#
]+\s*/);
  const steps=[];
  for(const ln of md.split('\n')){
    const s=ln.trim();
    if(/^\d+[.)]/.test(s)&&s.length<180)steps.push(s.replace(/^\d+[.)]\s+/,''));
    if(steps.length>=5)break;
  }
  const out=['ПАМЯТКА: '+ART[slug].title,'','Пять шагов:']+steps.slice(0,5).map((x,i)=>(i+1)+'. '+x)+['','Что сделать сегодня: открыть статью и выполнить первый шаг.','Как проверить результат: следовать инструкциям в статье, сверяться с источниками.','','Полная статья: https://neuro-retree.github.io/site/articles/'+slug+'/'];
  memoOut.style.display='block';memoOut.textContent=out.join('\n');
  memoPrint.style.display='inline-block';
});
memoPrint.addEventListener('click',()=>{window.print();});
</script>
""" % (BASE_URL, BASE_URL, opts, json_articles)
    # json_articles подставим ниже
    page("Генератор памятки — Нейросети для жизни", "Короткая памятка из любой статьи: пять шагов, что сделать сегодня, как проверить. Печать и отправка близким.", body, BASE_URL + "tools/pamiatka/").__str__()
    (ROOT / "tools" / "pamiatka" / "index.html").write_text(page("Генератор памятки — Нейросети для жизни", "Короткая памятка из любой статьи: пять шагов, что сделать сегодня, как проверить. Печать и отправка близким.", body, BASE_URL + "tools/pamiatka/"), encoding="utf-8")


# ---------- Обучение ----------

def build_learning():
    (ROOT / "learning").mkdir(parents=True, exist_ok=True)
    routes = [
        ("level0", "Уровень 0 — Без нейросетей. Фундамент", "Что полезно знать каждому: защита аккаунтов, деньги, здоровье, госуслуги. Нейросети тут не нужны — только спокойные инструкции.",
         [("Списали деньги за приложение", "article_spisali_za_prilozhenie"),
          ("Двухфакторная защита", "article_2fa_zashchita"),
          ("Куда записать пароль", "article_kuda_zapisat_parol")]),
        ("level1", "Уровень 1 — Первое знакомство с нейросетью", "Что такое нейросеть, как её открыть и не испугаться. Первые 10 вечеров.",
         [("Чек-лист «10 вечеров»", "article_20_cheklist_10_vecherov"),
          ("Как объяснить соседке", "article_obyasni_sosedke"),
          ("Первый запрос вместе", "article_otkrytyj_urok")]),
        ("level2", "Уровень 2 — Нейросети в быту", "Помощник в обычных делах: поздравления, тексты, переводы, озвучка, отдых и творчество.",
         [("Нейросеть в быту: 10 дел", "article_10_scenariev_byta"),
          ("Нейросеть-собеседник", "article_nejroset_sobesednik"),
          ("Нейросеть-художник", "article_nejroset_hudozhnik")]),
        ("level3", "Уровень 3 — Промты: как просить правильно", "Мастерство запросов: формула промта, готовые шаблоны, как не попасться на выдумки.",
         [("Что такое промт", "article_chto_takoe_promt"),
          ("Промт — не страшно", "article_promt_ne_strashno"),
          ("Готовые промты для заработка", "article_15_promty_dlya_zarabotka")]),
        ("level4", "Уровень 4 — Агенты и автоматизация", "Нейросети, которые работают сами: уровни автоматизации, агенты, проверка галлюцинаций, заработок.",
         [("5 уровней автоматизации", "article_5_urovnej_avtomatizacii"),
          ("Агенты — работают сами", "article_agenty_rabotayut_sami"),
          ("Галлюцинации нейросети", "article_gallyucinacii")]),
    ]
    blocks = []
    for rid, title, desc, items in routes:
        lis = "".join('<li><a href="%sarticles/%s/">%s</a></li>' % (BASE_URL, slug, html.escape(name)) for name, slug in items)
        blocks.append("""
<div class="tool-card" style="cursor:default">
  <h2>%s</h2>
  <p>%s</p>
  <ul style="margin:12px 0 0;padding-left:22px">%s</ul>
</div>""" % (html.escape(title), html.escape(desc), lis))
    body = """
<div class="breadcrumbs"><a href="%s">Главная</a> → Обучение</div>
<h1 style="color:#133a33;font-size:28px;margin:8px 0 4px">Учебные маршруты</h1>
<p style="color:#5b7080">Пять уровней — от «без нейросетей» до «нейросети работают сами». Каждый уровень опирается на предыдущий: начните с нуля и двигайтесь вверх по лестнице.</p>
%s
""" % (BASE_URL, "".join(blocks))
    out = page("Обучение — Нейросети для жизни", "Пять учебных уровней: от основ безопасности и денег до нейросетей, промтов и агентов.", body, BASE_URL + "learning/", "<style>%s</style>" % TOOLS_CSS)
    (ROOT / "learning" / "index.html").write_text(out, encoding="utf-8")


# ---------- Главная ----------

def build_home():
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Нейросети для жизни",
        "inLanguage": "ru",
        "description": "Нейросети, цифровая безопасность и полезные интернет-сервисы простыми словами для людей старшего возраста.",
        "url": BASE_URL,
        "author": {"@type": "Person", "name": AUTHOR}
    }, ensure_ascii=False)
    extra = '<script type="application/ld+json">%s</script>' % jsonld
    cards = []
    for a in ARTICLES:
        cat = CATEGORY_LABELS.get(a["tags"][0], a["tags"][0])
        cards.append("""
<div class="card">
  <a href="%sarticles/%s/"><span class="cov"><img src="articles/%s/%s.png" alt="%s" loading="lazy"></span></a>
  <div class="body">
    <span class="tag">%s</span>
    <h3><a href="%sarticles/%s/">%s</a></h3>
    <p>%s</p>
    <a class="btn-read" href="%sarticles/%s/">Читать статью</a>
  </div>
</div>""" % (BASE_URL, a["slug"], a["slug"], a["slug"], html.escape(a["title"]),
             html.escape(cat), BASE_URL, a["slug"], html.escape(a["title"]),
             html.escape(a["desc"]), BASE_URL, a["slug"]))
    body = HEADER_HOME + """
<div class="about" style="background:#fff;border:1px solid #e2e9ee;border-radius:14px;padding:20px 24px;margin:18px 0;box-shadow:0 2px 10px rgba(20,40,60,.08)">
  <h2 style="margin-top:0;color:#0e7c66">Здравствуйте, дорогие мои!</h2>
  <p>Меня зовут <strong>Татьяна Зенина</strong>, я живу в Астрахани, мне за шестьдесят. Этот сайт — про нейросети, но написано здесь совсем не научно: простыми словами, с примерами из жизни. Здесь я отвечаю на вопросы, которые чаще всего задают люди в возрасте.</p>
  <p>Подписывайтесь на <a href="https://t.me/neuro_retree">канал</a>, чтобы не потеряться. Мои книги — «Нейросети для жизни» в четырёх томах — можно получить любым удобным способом (см. ниже).</p>
</div>
<h2 style="color:#133a33">Что я пишу</h2>
<div class="grid">%s</div>

<div class="about" style="background:#fff;border:1px solid #e2e9ee;border-radius:14px;padding:20px 24px;margin:22px 0;box-shadow:0 2px 10px rgba(20,40,60,.08)" id="books">
  <h2 style="margin-top:0;color:#0e7c66">Книги «Нейросети для жизни» — четыре тома</h2>
  <p>Выберите, как вам удобнее получить книги:</p>
  <p style="display:flex;gap:10px;flex-wrap:wrap">
    <a style="background:#0e7c66;color:#fff;padding:11px 18px;border-radius:10px;font-size:16px" href="mailto:neuro-retree@yandex.ru?subject=Книги&body=Здравствуйте, Татьяна! Пришлите, пожалуйста, книги">Скачать на сайте (по почте)</a>
    <a style="background:#1565a8;color:#fff;padding:11px 18px;border-radius:10px;font-size:16px" href="https://t.me/tatzenbot">Получить в Telegram</a>
    <a style="background:#5b7080;color:#fff;padding:11px 18px;border-radius:10px;font-size:16px" href="https://vk.com/club242405739">Получить во ВКонтакте</a>
  </p>
  <p class="note" style="color:#5b7080;font-size:15px">Если Telegram у вас открывается плохо, это не ваша вина. Выберите другой способ выше — книги пришлю письмом или через ВКонтакте.</p>
</div>

<div class="about" style="background:#fff;border:1px solid #e2e9ee;border-radius:14px;padding:20px 24px;margin:22px 0;box-shadow:0 2px 10px rgba(20,40,60,.08)" id="verify">
  <h2 style="margin-top:0;color:#0e7c66">Как убедиться, что это действительно я</h2>
  <p>Мошенники копируют страницы авторов и «продают» курсы от их имени. Мои настоящие адреса — только эти:</p>
  <ul>
    <li>Этот сайт: <strong>neuro-retree.github.io/site</strong></li>
    <li>Telegram-канал: <a href="https://t.me/neuro_retree">t.me/neuro_retree</a></li>
    <li>Бот для книг: <a href="https://t.me/tatzenbot">@tatzenbot</a></li>
    <li>ВКонтакте: <a href="https://vk.com/club242405739">vk.com/club242405739</a></li>
    <li>Поддержка на Boosty: <a href="https://boosty.to/tatzen">boosty.to/tatzen</a></li>
    <li>Почта: <a href="mailto:neuro-retree@yandex.ru">neuro-retree@yandex.ru</a></li>
  </ul>
  <p><strong>Я никогда не прошу</strong> номер карты, коды из СМС, паспортные данные или «срочный перевод». Если кто-то пишет от моего имени и просит такое — это мошенники.</p>
</div>

<div class="about" style="background:#fff;border:1px solid #e2e9ee;border-radius:14px;padding:20px 24px;margin:22px 0;box-shadow:0 2px 10px rgba(20,40,60,.08)" id="support">
  <h2 style="margin-top:0;color:#0e7c66">Поддержать автора</h2>
  <p>Материалы на сайте бесплатны. Если захотите сказать спасибо, можете угостить меня чашкой чая — это лучшее признание. Возможно, в будущем появятся платные курсы; о них я буду писать отдельно и честно.</p>
  <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:14px">
    <a href="https://boosty.to/tatzen" style="background:var(--accent);color:#fff;padding:11px 18px;border-radius:10px;font-size:16px;">Поддержать на Boosty</a>
    <a href="https://vk.com/club242405739" style="background:var(--accent2);color:#fff;padding:11px 18px;border-radius:10px;font-size:16px;">Вступить в VK-сообщество</a>
  </div>
  <p style="color:#5b7080;font-size:14px;margin-top:12px">Перевод по СБП или QR-коду появятся позже — как только разберусь с оформлением. Пока что Boosty и VK — самые простые пути.</p>
</div>
""" % "".join(cards)
    out = page("Нейросети для жизни — Татьяна Зенина, Астрахань",
               "Нейросети простыми словами для людей в возрасте: статьи, советы, личный опыт. Татьяна Зенина, Астрахань.",
               body, BASE_URL, extra)
    (ROOT / "index.html").write_text(out, encoding="utf-8")


# ---------- sitemap, rss, articles.json ----------

def build_aux():
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    urls = ["", "articles/", "tools/", "tools/prompt-builder/", "tools/sms-checker/", "learning/"]
    urls += ["articles/%s/" % a["slug"] for a in ARTICLES]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        sitemap.append("  <url><loc>%s%s</loc></url>" % (BASE_URL, u))
    sitemap.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(sitemap) + "\n", encoding="utf-8")

    rss_items = []
    for a in ARTICLES:
        rss_items.append("""    <item>
      <title>%s</title>
      <link>%sarticles/%s/</link>
      <guid>%sarticles/%s/</guid>
      <description>%s</description>
    </item>""" % (html.escape(a["title"]), BASE_URL, a["slug"], BASE_URL, a["slug"], html.escape(a["desc"])))
    rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Нейросети для жизни — Татьяна Зенина</title>
    <link>%s</link>
    <description>Нейросети, цифровая безопасность и полезные интернет-сервисы простыми словами для людей старшего возраста.</description>
    <language>ru</language>
    <atom:link href="%srss.xml" rel="self" type="application/rss+xml"/>
%s  </channel>
</rss>
""" % (BASE_URL, BASE_URL, "\n".join(rss_items))
    (ROOT / "rss.xml").write_text(rss, encoding="utf-8")

    registry = {"schema_version": 1, "generated": BUILD_DATE, "articles": []}
    for a in ARTICLES:
        registry["articles"].append({
            "slug": a["slug"], "title": a["title"], "tags": a["tags"],
            "description": a["desc"], "url": "%sarticles/%s/" % (BASE_URL, a["slug"]),
            "sources_md": "%s%s.md" % (BASE_URL, a["slug"]),
            "category": a["tags"][0], "status": "published"
        })
    (ROOT / "data" / "articles.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- Словарь терминов ----------

GLOSSARY = {
    "БАД": "Биологически активная добавка: витамины, минералы и вещества, которые принимают дополнительно к еде. Это не лекарство.",
    "антибиотики": "Лекарства, которые борются с бактериями (микробами). Про вирусы они почти не действуют.",
    "антидепрессанты": "Лекарства, которые назначает врач, чтобы выровнять настроение при подавленности и тревоге.",
    "анамнез": "История болезни: врач расспрашивает, что вас беспокоит, чем вы болели, что принимаете.",
    "генетика": "Наследственность: какие особенности и склонности достались вам от родителей.",
    "гормоны": "Вещества-сигналы, которые управляют работой тела: настроением, сном, обменом веществ.",
    "дефицит": "Нехватка чего-либо в организме, например железа или витамина D.",
    "дипфейк": "Поддельные видео или голос, созданные нейросетью: человека можно «заставить» говорить то, чего он не говорил.",
    "двухфакторная защита": "Вход в аккаунт по двум ступеням: сначала пароль, потом код из СМС. Как второй замок на двери.",
    "ЖКТ": "Желудочно-кишечный тракт: желудок, кишечник и органы, которые переваривают пищу.",
    "иммунитет": "Защитные силы организма: как он борется с болезнями.",
    "интерфейс": "Внешний вид программы: кнопки, окна и меню, по которым вы работаете.",
    "контрацептивы": "Средства, предохраняющие от беременности.",
    "маркетинг": "Продвижение товара: реклама, скидки, упаковка — всё, что убеждает вас купить.",
    "маркетплейс": "Онлайн-магазин, где продают товары разные продавцы. Примеры: Ozon, Wildberries.",
    "метаболизм": "Обмен веществ: все химические процессы, которые постоянно идут в теле.",
    "мета-анализ": "Самое надёжное исследование: учёные собрали и сверили результаты многих отдельных работ по одной теме.",
    "микронутриенты": "Витамины и минералы: их нужно совсем немного, но без них организм не работает.",
    "нейросеть": "Компьютерная программа, обученная на огромном количестве текстов: отвечает на вопросы, пишет тексты, рисует.",
    "нутриенты": "Питательные вещества: витамины, минералы, белки, жиры, углеводы.",
    "нутрициолог": "Специалист по питанию: помогает разобраться, что и как есть, чтобы было полезно.",
    "паразиты": "Организмы, которые живут за счёт другого существа (например, глисты в кишечнике).",
    "пестициды": "Яды, которыми обрабатывают растения, чтобы защитить их от вредителей.",
    "пробиотики": "Полезные бактерии для кишечника: помогают пищеварению и микрофлоре.",
    "пребиотики": "Пища для полезных бактерий: вещества, которые помогают им размножаться.",
    "промпт": "Текстовая инструкция для нейросети: что вы хотите получить и как оформить ответ.",
    "рецепторы": "Особые приёмники на поверхности клеток: клетка «слышит» сигнал вещества и реагирует.",
    "стимуляторы": "Вещества, которые искусственно бодрят и разгоняют сердце (например, кофеин в больших дозах).",
    "токсины": "Яды: вредные вещества, которые отравляют организм.",
    "ферменты": "«Работники» тела: помогают переваривать пищу и расщеплять лекарства.",
    "ферритин": "Показатель запаса железа в организме (по анализу крови).",
    "фолиевая кислота": "Витамин B9: особенно важен женщинам при беременности.",
    "25(OH)D": "Анализ крови на витамин D: так врачи обозначают его форму, которая показывает, хватает ли вам витамина.",
    "аутентификация": "Проверка личности: что вы — это вы (пароль, код из СМС, отпечаток пальца).",
    "фишинг": "Мошенничество: вас обманом заставляют ввести пароль или данные карты на поддельном сайте.",
}


def build_glossary():
    (ROOT / "slovar").mkdir(parents=True, exist_ok=True)
    items = []
    for term in sorted(GLOSSARY, key=lambda x: x.lower()):
        items.append('<div class="gloss"><h2>%s</h2><p>%s</p></div>' % (html.escape(term), html.escape(GLOSSARY[term])))
    body = ('<div class="breadcrumbs"><a href="{0}">Главная</a> → Словарь</div>\n'
            '<div class="tool-page">\n'
            '<h1>Словарь простыми словами</h1>\n'
            '<p style="color:#5b7080">Здесь собраны слова, которые встречаются в статьях, - с простыми объяснениями. '
            'Если встретите незнакомый термин, загляните сюда: я объясняю так, как объяснила бы соседке.</p>\n'
            '<div class="gloss-list">\n{1}\n</div>\n</div>\n'
            '<style>.gloss{{background:#fff;border:1px solid #e2e9ee;border-radius:12px;padding:14px 18px;margin:10px 0}}'
            '.gloss h2{{margin:0 0 4px;color:#0e7c66;font-size:19px}}.gloss p{{margin:0;color:#1f2d3a}}</style>\n').format(
                BASE_URL, "\n".join(items))
    html_out = page("Словарь терминов — Нейросети для жизни", "Простые объяснения слов из наших статей: БАД, дефицит, метаболизм, промпт, ферменты и другие.", body, BASE_URL + "slovar/")
    (ROOT / "slovar" / "index.html").write_text(html_out, encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    for a in ARTICLES:
        md_file = ROOT / (a["slug"] + ".md")
        if not md_file.exists():
            print("MISS:", a["slug"])
            continue
        build_article(a, md_file.read_text(encoding="utf-8"))
        print("статья:", a["slug"])
    build_catalog()
    build_tools()
    build_memo()
    build_learning()
    build_glossary()
    build_home()
    build_aux()
    print("Готово. Страницы собраны в", ROOT)


if __name__ == "__main__":
    main()