import json
from pathlib import Path
from slugify import slugify
from jinja2 import Environment, FileSystemLoader, select_autoescape
import shutil
import random
from markupsafe import Markup


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
    Собирает один сайт в dist/<slug-domain>:
    - плоские поля навигации (site_nav1..5)
    - рандомная тема (если theme пусто/== 'random')
    - копирование темы -> style.css и скрипта -> main.js
    - копирование templates/images -> dist/images
    - подстановка рандомных картинок для hero (images/Hero)
    - рендер секций (с поддержкой variant/random в render_sections)
    - рендер base.html с {{ content | safe }}
    """
    # === Директория сайта ===
    domain = (ctx["site_domain"] or "").strip()
    site_dir = DIST / slugify(domain)
    site_dir.mkdir(parents=True, exist_ok=True)

    # === Навигация (плоские поля для текущего base.html) ===
    nav = ctx.get("nav", []) or []
    for i in range(1, 6):
        item = nav[i - 1] if len(nav) >= i else {"label": "", "id": ""}
        ctx[f"site_nav{i}"] = item.get("label", "")
        ctx[f"site_nav{i}_sharp"] = item.get("id", "")

    # === Картинки: копия images и рандом для hero ===
    hero = ctx.get("hero", {}) or {}
    if hero:
        ensure_images_copied(site_dir)  # templates/images -> dist/images (разово)
        # random / random_from:Hero
        hero["image_url"] = resolve_random_image(hero.get("image_url"), default_subdir="Hero") or hero.get("image_url")
        hero["bg_image"]  = resolve_random_image(hero.get("bg_image"),  default_subdir="Hero") or hero.get("bg_image")
        ctx["hero"] = hero  # вернуть в контекст (на случай pass-by-value)

    # === Тема (рандом, если не задана/== 'random') ===
    theme = (ctx.get("theme") or "random").strip().lower()
    if theme in ("", "random"):
        theme = pick_random_theme(include_default=False)
    copy_theme(theme, site_dir)  # кладём выбранную тему как dist/style.css

    # === Пути ассетов в шаблоне ===
    from time import time
    ctx["style_path"] = "./style.css"
    ctx["script_path"] = "./main.js"
    ctx["build_id"] = int(time())  # можно для cache-busting: ?v={{ build_id }}

    # === Контент из секций ===
    sections = ctx.get("sections", []) or []
    content_html = render_sections(sections, ctx)  # возвращает Markup(...)
    ctx["content"] = content_html

    # === Рендер base.html ===
    base_tpl = env.get_template("base.html")
    html = base_tpl.render(**ctx)
    (site_dir / "index.html").write_text(html, encoding="utf-8")

    # === Скрипты ===
    copy_scripts(site_dir)  # кладём dist/main.js

    print(f"[ok] {domain} → {site_dir} (theme: {theme})")


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
