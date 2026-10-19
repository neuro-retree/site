# Сайт «Нейросети для жизни»

Практические объяснения нейросетей, цифровой безопасности, денег, здоровья и государственных услуг простыми словами для людей старшего возраста (50+). Автор — Татьяна Зенина, Астрахань.

**Адрес:** https://neuro-retree.github.io/site/

## Структура репозитория

```
.
├── index.html                 # главная (генерируется)
├── articles/
│   ├── index.html             # каталог статей с поиском и фильтром
│   └── <slug>/index.html      # отдельная страница каждой статьи
├── tools/
│   ├── prompt-builder/        # конструктор запросов к нейросети
│   └── sms-checker/           # проверка подозрительного сообщения
├── learning/                  # три учебных маршрута
├── data/articles.json         # машинный реестр статей (источник правды)
├── scripts/
│   ├── rebuild_site.py        # сборка всех страниц из Markdown
│   ├── validate_content.py    # проверка структуры статей
│   └── check_links.py         # проверка ссылок
├── .github/workflows/quality.yml  # CI: сборка + проверки
├── ACCESSIBILITY.md           # доступность: что сделано, как сообщить о проблеме
├── CHANGELOG.md               # журнал изменений
├── robots.txt
├── sitemap.xml
├── rss.xml
└── llms.txt
```

## Как всё обновлять

1. Положите (или отредактируйте) Markdown-статью в корень: `article_<slug>.md`, обложку — `article_<slug>.png`.
2. Обновите список в `scripts/rebuild_site.py` (массив `ARTICLES`).
3. Соберите и проверьте:

```bash
python scripts/rebuild_site.py
python scripts/validate_content.py
python scripts/check_links.py --no-external
```

4. Закоммитьте и запушьте в `main` — GitHub Pages пересоберётся автоматически (статические файлы на ветке `main`, Pages включает `source: main /`).

## Принципы

- Markdown-файлы — единственный источник текстов; HTML генерируется скриптом.
- Заголовок, описание и тема каждой статьи — в реестре `data/articles.json`, а не повторяются вручную.
- Источники в статьях сохраняются и показываются читателю.
- Критичные темы (здоровье, право, деньги) требуют проверки фактов и даты актуальности перед публикацией.
- Доступность — не косметика: см. `ACCESSIBILITY.md`.

## Каналы

- Telegram-канал: https://t.me/neuro_retree
- Бот для связи и книг: https://t.me/tatzenbot
- VK-сообщество: https://vk.com/club242405739
- Boosty (поддержка): https://boosty.to/tatzen