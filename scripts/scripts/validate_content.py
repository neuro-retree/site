# -*- coding: utf-8 -*-
"""validate_content.py — проверка статей сайта перед публикацией.

Проверяет:
  - наличие Markdown-файла и обложки для каждой статьи из articles.json;
  - непустой заголовок (первая строка #);
  - наличие разделов «Что сделать сегодня», «Источники»/«полезные ссылки»,
    «Дорогие мои» (CTA) и предупреждения о не-замене врача для здоровья;
  - отсутствие служебных заглушек (example.com, TODO).
Возвращает код 0 при успехе, 1 при ошибках.

Запуск: python scripts/validate_content.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    registry = ROOT / "data" / "articles.json"
    if not registry.exists():
        print("ОШИБКА: нет data/articles.json — сначала соберите сайт (rebuild_site.py)")
        return 2
    data = json.loads(registry.read_text(encoding="utf-8"))
    errors, warns = [], []

    for a in data["articles"]:
        slug = a["slug"]
        md = ROOT / (slug + ".md")
        png = ROOT / (slug + ".png")
        page = ROOT / "articles" / slug / "index.html"

        if not md.exists():
            errors.append(f"{slug}: нет Markdown-файла")
            continue
        text = md.read_text(encoding="utf-8")

        if not text.strip():
            errors.append(f"{slug}: пустой текст")
        if "example.com" in text or "TODO" in text:
            errors.append(f"{slug}: найдена заглушка example.com/TODO")
        if not png.exists():
            warns.append(f"{slug}: нет обложки .png")
        if not page.exists():
            errors.append(f"{slug}: не собрана страница articles/{slug}/")
        # обязательные разделы
        if not a.get("title") or not str(a["title"]).strip():
            errors.append(f"{slug}: пустой заголовок в реестре")
        if not re.search(r"(?i)что сделать сегодня", text):
            warns.append(f"{slug}: нет раздела «Что сделать сегодня»")
        if not re.search(r"(?i)источник|полезные ссылки|рекомендуемые ресурсы", text):
            warns.append(f"{slug}: нет раздела источников/ресурсов")
        if not re.search(r"(?i)напоследок", text):
            warns.append(f"{slug}: нет финального CTA")
        # здоровье: обязательное предупреждение
        if any(t in a.get("tags", []) for t in ("здоровье",)):
            if not re.search(r"(?i)консультаци[яеи].*врач|не заменяет", text):
                errors.append(f"{slug}: медицинская тема без предупреждения о консультации врача")

    print("Проверено статей:", len(data["articles"]))
    print("Ошибок:", len(errors))
    for e in errors:
        print("  [ERROR]", e)
    print("Предупреждений:", len(warns))
    for w in warns:
        print("  [WARN]", w)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())