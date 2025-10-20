import json
from pathlib import Path
from slugify import slugify
from jinja2 import Environment, FileSystemLoader, select_autoescape
import shutil
import random
from markupsafe import Markup
import urllib.parse

ROOT = Path(__file__).parent.resolve()
TEMPLATES_DIR = ROOT / "templates"
PARTIALS_DIR = TEMPLATES_DIR / "partials"
DATA_JSON = ROOT / "data" / "sites.json"
DIST = ROOT / "dist"
STYLE_VARIANTS = TEMPLATES_DIR / "style_variants"
SCRIPTS_SRC = TEMPLATES_DIR / "scripts"
IMAGES_DIR = TEMPLATES_DIR / "images"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".avif"}
GOOGLE_FONTS = [
    "Manrope", "Inter", "Outfit", "Urbanist", "DM Sans",
    "Plus Jakarta Sans", "Work Sans", "Rubik", "Nunito Sans", "Poppins"
]

def pick_random_gfont() -> str:
    if not GOOGLE_FONTS:
        return "Inter"
    return random.choice(GOOGLE_FONTS)

def build_gfonts_href(family: str, weights: list[int] | None = None, italic: bool = False) -> str:
    """
    Собирает css2 URL вида:
    https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&display=swap
    """
    fam = family.strip()
    if not weights:
        weights = [400, 600, 700]
    weights = sorted({int(w) for w in weights if 100 <= int(w) <= 900})

    # Кодируем имя семейства как в css2: пробелы → +
    fam_q = urllib.parse.quote_plus(fam)

    if italic:
        # семейства с италиком: wght,ital@0,400;0,600;1,400...
        pairs = []
        for it in (0, 1):
            for w in weights:
                pairs.append(f"{it},{w}")
        axis = "ital,wght@" + ";".join(pairs)
    else:
        axis = "wght@" + ";".join(str(w) for w in weights)

    return f"https://fonts.googleapis.com/css2?family={fam_q}:{axis}&display=swap"

def list_images(subdir: str | None) -> list[Path]:
    base = IMAGES_DIR / subdir if subdir else IMAGES_DIR
    if not base.exists():
        return []
    return [p for p in base.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS]

def pick_random_image(subdir: str | None) -> Path | None:
    files = list_images(subdir)
    return random.choice(files) if files else None

def ensure_images_copied(dist_dir: Path):
    dst = dist_dir / "images"
    if dst.exists():
        return
    if IMAGES_DIR.exists():
        shutil.copytree(IMAGES_DIR, dst)
    else:
        dst.mkdir(parents=True, exist_ok=True)

def resolve_random_image(value: str | None, default_subdir: str | None) -> str | None:
    if not value:
        return None
    val = value.strip()
    if val.startswith("random_from:"):
        sub = (val.split(":", 1)[1] or "").strip() or default_subdir
        p = pick_random_image(sub)
        return f"./images/{sub}/{p.name}" if p and sub else None
    if val == "random":
        p = pick_random_image(default_subdir)
        return f"./images/{default_subdir}/{p.name}" if p and default_subdir else None
    return val

_VARIANTS_CACHE = {}
def list_section_variants(base_name: str):
    if base_name in _VARIANTS_CACHE:
        return _VARIANTS_CACHE[base_name]

    base = PARTIALS_DIR / f"{base_name}.html"
    variants = ["default"] if base.exists() else []

    # ищем section.hero.v*.html
    for p in PARTIALS_DIR.glob(f"{base_name}.v*.html"):
        # имя файла вида: section.hero.v2.html → берём 'v2'
        v = p.stem.split(".")[-1]  # v2
        variants.append(v)

    # уникализируем, сохраняя порядок
    seen, uniq = set(), []
    for v in variants:
        if v not in seen:
            seen.add(v); uniq.append(v)

    _VARIANTS_CACHE[base_name] = uniq
    return uniq

def resolve_partial_path(base_name: str, variant: str | None):
    variants = list_section_variants(base_name)
    chosen = None

    if not variants:
        # вообще нет файлов секции
        return None

    if variant and variant != "random":
        # если задали явно и такой есть — используем
        if variant in variants:
            chosen = variant
        else:
            # нет такого → мягкий фолбэк на default/первый
            chosen = "default" if "default" in variants else variants[0]
    else:
        # random или None
        chosen = random.choice(variants)

    if chosen == "default":
        return f"partials/{base_name}.html"
    return f"partials/{base_name}.{chosen}.html"

def pick_random_theme(include_default=False):
    patterns = "*.css"
    themes = [p.stem for p in STYLE_VARIANTS.glob(patterns)]
    if not include_default:
        themes = [t for t in themes if t != "theme-default"]
    if not themes:
        raise RuntimeError("No CSS themes found in style_variants/")
    return random.choice(themes)

def resolve_random_tokens_in_obj(obj: dict, default_subdir: str | None) -> dict:
    """Возвращает КОПИЮ obj, где строки random/random_from:... заменены на реальные пути."""
    def _walk(v):
        if isinstance(v, dict):
            return {k: _walk(v2) for k, v2 in v.items()}
        if isinstance(v, list):
            return [_walk(x) for x in v]
        if isinstance(v, str):
            # для всех строк проверяем random-токены
            return resolve_random_image(v, default_subdir) or v
        return v
    return _walk(obj)

def load_manifest(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def deep_merge(a: dict, b: dict) -> dict:
    out = dict(a or {})
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out
def section_default_subdir(base_name: str) -> str | None:
    # "section.hero" -> "Hero"; "section.about" -> "About"
    try:
        return base_name.split(".", 1)[1].capitalize()
    except Exception:
        return None

def render_sections(sections, ctx):
    html_parts = []
    for s in sections:
        base_name = s["name"].strip()          # например, section.hero
        data_ref  = s.get("data")
        variant   = (s.get("variant") or "").strip() or None

        # достаём данные секции (ссылка на ключ или инлайн-объект)
        if isinstance(data_ref, str):
            raw_data = ctx.get(data_ref, {}) or {}
        else:
            raw_data = data_ref or {}

        # ❶ резолвим random/random_from в КОПИИ данных
        default_subdir = section_default_subdir(base_name)  # Hero / About / ...
        data = resolve_random_tokens_in_obj(raw_data, default_subdir)

        # ❷ мерджим: секционные данные перекрывают глобальные
        section_ctx = deep_merge(ctx, data)

        # ❸ выбираем файл варианта (как ты уже сделал ранее)
        tpl_rel = resolve_partial_path(base_name, variant)
        if not tpl_rel:
            print(f"[warn] No templates for section: {base_name} — skip")
            continue

        tpl = env.get_template(tpl_rel)
        html_parts.append(tpl.render(**section_ctx))

    return Markup("\n\n".join(html_parts))


def copy_theme(theme_name, dist_dir):
    css_src = STYLE_VARIANTS / f"{theme_name}.css"
    css_dst = dist_dir / "style.css"
    css_dst.parent.mkdir(parents=True, exist_ok=True)
    if not css_src.exists():
        raise FileNotFoundError(f"Theme CSS not found: {css_src}")
    shutil.copyfile(css_src, css_dst)

def copy_scripts(dist_dir):
    shutil.copyfile(SCRIPTS_SRC / "main.js", dist_dir / "main.js")

def build_site(ctx):
    """
    Собирает сайт в dist/<slug-domain>:
    - расплющивает навигацию (site_nav1..5)
    - копирует изображения templates/images -> dist/images
    - выбирает шрифт Google Fonts (random или заданный), формирует google_fonts_href
    - выбирает тему (random), копирует её как dist/style.css
    - задаёт пути ассетов (style_path/script_path) и build_id
    - рендерит секции (render_sections возвращает Markup)
    - рендерит base.html и кладёт dist/index.html
    - копирует scripts/main.js -> dist/main.js
    """
    # ========= базовые директории =========
    domain = (ctx.get("site_domain") or "").strip()
    if not domain:
        raise ValueError("site_domain is required in context")
    site_dir = DIST / slugify(domain)
    site_dir.mkdir(parents=True, exist_ok=True)

    # ========= навигация → плоские поля =========
    nav = ctx.get("nav", []) or []
    for i in range(1, 6):
        item = nav[i - 1] if len(nav) >= i else {"label": "", "id": ""}
        ctx[f"site_nav{i}"] = item.get("label", "")
        ctx[f"site_nav{i}_sharp"] = item.get("id", "")

    # ========= изображения =========
    # копируем templates/images → dist/images (разово на сайт)
    ensure_images_copied(site_dir)

    # ========= Google Fonts =========
    font_cfg = ctx.get("font", "random")
    if isinstance(font_cfg, dict):
        fam = (font_cfg.get("family") or "random").strip()
        wts = font_cfg.get("weights") or [400, 600, 700]
        italic = bool(font_cfg.get("italic", False))
    else:
        fam = str(font_cfg or "random").strip()
        wts = [400, 600, 700]
        italic = False

    if fam.lower() in ("", "random"):
        fam = pick_random_gfont()

    if fam not in GOOGLE_FONTS:
        # мягкий фолбэк, чтобы ссылка не билась
        print(f"[warn] '{fam}' may be unavailable on Google Fonts. Fallback to 'Manrope'.")
        fam = "Manrope"

    ctx["google_fonts_href"] = build_gfonts_href(fam, wts, italic)
    ctx["font_family"] = fam  # используется в <style> для --font-sans при желании

    # ========= тема (CSS) =========
    theme = (ctx.get("theme") or "random").strip().lower()
    if theme in ("", "random"):
        theme = pick_random_theme(include_default=False)
    copy_theme(theme, site_dir)  # кладём выбранную тему как dist/style.css

    # ========= пути ассетов и cache-busting =========
    from time import time as _now
    ctx["style_path"] = "./style.css"
    ctx["script_path"] = "./main.js"
    ctx["build_id"] = int(_now())

    # ========= контент из секций =========
    sections = ctx.get("sections", []) or []
    # render_sections должен:
    #  - поддерживать variant/random для шаблонов
    #  - резолвить random / random_from:Subdir в данных секции
    content_html = render_sections(sections, ctx)
    ctx["content"] = content_html

    # ========= рендер base.html =========
    base_tpl = env.get_template("base.html")
    html = base_tpl.render(**ctx)
    (site_dir / "index.html").write_text(html, encoding="utf-8")

    # ========= скрипты =========
    copy_scripts(site_dir)  # templates/scripts/main.js -> dist/main.js

    print(f"[ok] {domain} → {site_dir} (theme: {theme}, font: {ctx['font_family']})")

def main():
    manifest = load_manifest(DATA_JSON)
    defaults = manifest.get("defaults", {})
    sites = manifest.get("sites", [])
    if not sites:
        print("[err] No sites in data/sites.json"); return
    
    seed = manifest.get("seed")
    if seed is not None:
        random.seed(seed)

    for raw in sites:
        ctx = deep_merge(defaults, raw)
        build_site(ctx)

if __name__ == "__main__":
    main()
