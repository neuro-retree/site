# -*- coding: utf-8 -*-
"""check_links.py — проверка внутренних и внешних ссылок сайта.

Внутренние: каждая локальная ссылка (src/href на файл или каталог)
должна существовать относительно страницы.
Внешние: SVG/маленькие ссылки проверяются HEAD-запросом (с таймаутом);
проверку можно пропустить флагом --no-external.

Запуск: python scripts/check_links.py [--no-external]
"""
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTERNAL_TIMEOUT = 15


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    check_external = "--no-external" not in sys.argv
    errors, warnings, ext_checked = [], [], 0

    html_files = list(ROOT.rglob("index.html"))
    for page in html_files:
        text = page.read_text(encoding="utf-8")
        for ref in re.findall(r'(?:src|href)="([^"#][^"]*)"', text):
            if ref.startswith(("mailto:", "tel:", "data:", "//")):
                continue
            if ref.startswith("http"):
                if check_external:
                    ext_checked += 1
                    try:
                        req = urllib.request.Request(ref, method="HEAD",
                                                     headers={"User-Agent": "Mozilla/5.0"})
                        urllib.request.urlopen(req, timeout=EXTERNAL_TIMEOUT)
                    except urllib.error.HTTPError as e:
                        if e.code >= 400:
                            errors.append(f"{page.relative_to(ROOT)}: внешняя ссылка {ref} -> HTTP {e.code}")
                    except Exception:
                        warnings.append(f"{page.relative_to(ROOT)}: не удалось проверить внешнюю {ref}")
                continue
            if ref.endswith("/"):
                ok = (page.parent / ref / "index.html").exists() or (page.parent / ref).exists()
            elif ref.startswith("/"):
                ok = (ROOT / ref.lstrip("/")).exists()
            else:
                ok = (page.parent / ref).exists()
            if not ok:
                errors.append(f"{page.relative_to(ROOT)}: битая локальная ссылка {ref}")

    print("Проверено страниц:", len(html_files))
    print("Внешних ссылок проверено:", ext_checked)
    print("Ошибок:", len(errors))
    for e in errors:
        print("  [ERROR]", e)
    print("Предупреждений:", len(warnings))
    for w in warnings:
        print("  [WARN]", w)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())