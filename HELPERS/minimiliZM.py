# minimiliZM.py
import os
import sys
from rjsmin import jsmin
from rcssmin import cssmin

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
OUTPUT_JS = os.path.join(BASE_DIR, "bundle.min.js")
OUTPUT_CSS = os.path.join(BASE_DIR, "bundle.min.css")

js_chunks = []
css_chunks = []

# Ищем только файлы из текущей папки (без подпапок)
for file in sorted(os.listdir(BASE_DIR)):
    path = os.path.join(BASE_DIR, file)
    if not os.path.isfile(path):
        continue

    lower = file.lower()

    # Пропускаем уже минифицированные
    if lower.endswith(".min.js") or lower.endswith(".min.css"):
        continue

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1", errors="ignore") as f:
            data = f.read()

    if lower.endswith(".js"):
        js_chunks.append(jsmin(data))
    elif lower.endswith(".css"):
        css_chunks.append(cssmin(data))

# Записываем только если есть контент
if js_chunks:
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("\n".join(js_chunks))
    # print(f"[OK] JS → {OUTPUT_JS}")
else:
    print("[i] JS файлов не найдено — bundle.min.js не создан.")

if css_chunks:
    with open(OUTPUT_CSS, "w", encoding="utf-8") as f:
        f.write("\n".join(css_chunks))
    print(f"[OK] CSS → {OUTPUT_CSS}")
else:
    print("[i] CSS файлов не найдено — bundle.min.css не создан.")
