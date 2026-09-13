"""
image_loader.py - High-performance Skin Image Loader and Cache for Case Opening Simulator.
Provides thread-safe local caching, asynchronous downloading from public CDN,
and procedural fallback placeholders with rarity styling.
"""
import os
import re
import urllib.request
import threading
from typing import Tuple, Optional, Dict
from PIL import Image, ImageDraw, ImageFont, ImageTk
import customtkinter as ctk
import config

SKINS_DIR = config.get_resource_path(os.path.join("assets", "skins"))
WRITABLE_SKINS_DIR = config.get_writable_path(os.path.join("assets", "skins"))
os.makedirs(WRITABLE_SKINS_DIR, exist_ok=True)

# Memory cache for loaded images
_CTK_CACHE: Dict[str, ctk.CTkImage] = {}
_TK_CACHE: Dict[str, ImageTk.PhotoImage] = {}
_PIL_CACHE: Dict[str, Image.Image] = {}

# CDN Database URL
SKINS_API_URL = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
_CDN_INDEX: Optional[Dict[str, str]] = None
_INDEX_LOCK = threading.Lock()
_ACTIVE_DOWNLOADS = set()

def sanitize_filename(name: str) -> str:
    """Produces a clean filesystem filename for a skin name."""
    clean = re.sub(r'^[★\s]+', '', name).strip().lower()
    clean = re.sub(r'[^a-z0-9_-]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return f"{clean}.png"

def normalize_name(name: str) -> str:
    """Normalizes skin name for CDN index matching."""
    return re.sub(r'^[★\s]+', '', name).strip().lower()

def _load_cdn_index():
    """Loads CDN index mapping normalized skin names to Steam CDN image URLs."""
    global _CDN_INDEX
    with _INDEX_LOCK:
        if _CDN_INDEX is not None:
            return
        try:
            req = urllib.request.Request(SKINS_API_URL, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                import json
                data = json.load(response)
                mapping = {}
                for s in data:
                    norm = normalize_name(s.get("name", ""))
                    img_url = s.get("image")
                    if norm and img_url:
                        mapping[norm] = img_url
                _CDN_INDEX = mapping
        except Exception:
            _CDN_INDEX = {}

ASSETS_DIR = config.get_resource_path("assets")

def clean_lookup_key(name: str) -> str:
    """Produces a clean filesystem key for skin names, stripping stars, stattraks, and punctuation."""
    clean = re.sub(r'^[★\*\[\]\(\)\s]+', '', name).strip().lower()
    clean = clean.replace('stattrak™', '').replace('stattrak', '').strip()
    clean = re.sub(r'[^a-z0-9_-]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean

def get_cached_file_path(skin_name: str) -> str:
    """Finds existing file path in writable dir, bundled resource dir, or default target."""
    c_key = clean_lookup_key(skin_name)
    filename = f"{c_key}.png"
    target_writable = os.path.join(WRITABLE_SKINS_DIR, filename)
    if os.path.exists(target_writable):
        return target_writable

    target_bundled = os.path.join(SKINS_DIR, filename)
    if os.path.exists(target_bundled):
        return target_bundled

    return target_writable

def find_local_skin_file(skin_name: str, rarity: str = "Mil-Spec") -> Optional[str]:
    """
    Comprehensive fallback search for a skin or knife image on disk.
    Chain: Exact Skin PNG -> Fuzzy Match PNG -> Same Weapon Family PNG -> Knife Silhouette -> Gold Badge.
    """
    c_key = clean_lookup_key(skin_name)
    fn = f"{c_key}.png"

    # 1. Exact sanitized filename
    for d in [WRITABLE_SKINS_DIR, SKINS_DIR]:
        p = os.path.join(d, fn)
        if os.path.exists(p):
            return p

    # 2. Finish-only match if name contains |
    if "|" in skin_name:
        finish = clean_lookup_key(skin_name.split("|")[-1])
        fn_finish = f"{finish}.png"
        for d in [WRITABLE_SKINS_DIR, SKINS_DIR]:
            p = os.path.join(d, fn_finish)
            if os.path.exists(p):
                return p

    # 3. Fuzzy search in skin directories
    weapon_model = clean_lookup_key(skin_name.split("|")[0])
    finish_words = [w for w in clean_lookup_key(skin_name.split("|")[-1]).split("_")
                    if len(w) > 2 and w not in ("the", "knife", "phase")] if "|" in skin_name else []

    best_file = None
    best_score = 0
    for d in [WRITABLE_SKINS_DIR, SKINS_DIR]:
        if not os.path.exists(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith(".png") or fname in ("gold_icon.png", "knife_silhouette.png"):
                continue
            name_no_ext = fname[:-4]
            score = 0
            if weapon_model in name_no_ext:
                score += 20
            for fw in finish_words:
                if fw in name_no_ext:
                    score += 5
            if score > best_score:
                best_score = score
                best_file = os.path.join(d, fname)

    if best_file and best_score >= 20:
        return best_file

    # 4. Fallback for Knives / Gloves / Rare Special
    is_knife = rarity == "Rare Special" or any(k in skin_name.lower() for k in ["knife", "bayonet", "karambit", "daggers", "gloves"])
    if is_knife:
        # Same knife family (e.g. any kukri_knife_*.png if a Kukri knife is requested)
        if best_file and best_score >= 10:
            return best_file

        # Generic Knife Silhouette PNG
        for d in [ASSETS_DIR, SKINS_DIR]:
            p = os.path.join(d, "knife_silhouette.png")
            if os.path.exists(p):
                return p

        # Generic Gold Badge
        for d in [ASSETS_DIR, SKINS_DIR]:
            p = os.path.join(d, "gold_icon.png")
            if os.path.exists(p):
                return p

    # 5. Fallback for Guns (same weapon family)
    if best_file and best_score >= 10:
        return best_file

    return None

def download_skin_image_async(skin_name: str, on_complete=None):
    """Downloads skin image in background thread if not present."""
    filename = sanitize_filename(skin_name)
    target_path = os.path.join(WRITABLE_SKINS_DIR, filename)
    if os.path.exists(target_path) or skin_name in _ACTIVE_DOWNLOADS:
        return

    def worker():
        _ACTIVE_DOWNLOADS.add(skin_name)
        try:
            if _CDN_INDEX is None:
                _load_cdn_index()
            if not _CDN_INDEX:
                return

            norm = normalize_name(skin_name)
            url = _CDN_INDEX.get(norm)
            if not url:
                # Try partial match (e.g. knife names without star)
                for k, u in _CDN_INDEX.items():
                    if norm in k or k in norm:
                        url = u
                        break

            if url:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    img_data = resp.read()
                tmp_path = f"{target_path}.tmp"
                with open(tmp_path, "wb") as f:
                    f.write(img_data)
                os.replace(tmp_path, target_path)

                # Clear all caches for this skin so the newly downloaded image is loaded next render
                for k in list(_PIL_CACHE.keys()):
                    if k.startswith(skin_name):
                        del _PIL_CACHE[k]
                for k in list(_CTK_CACHE.keys()):
                    if k.startswith(skin_name):
                        del _CTK_CACHE[k]
                for k in list(_TK_CACHE.keys()):
                    if k.startswith(f"tk_{skin_name}"):
                        del _TK_CACHE[k]

                if on_complete:
                    on_complete()
        except Exception:
            pass
        finally:
            _ACTIVE_DOWNLOADS.discard(skin_name)

    threading.Thread(target=worker, daemon=True).start()

def create_gold_special_card(size: Tuple[int, int] = (44, 32)) -> Image.Image:
    """
    Returns the official CS2 Gold Special Rare Item badge icon.
    Loads assets/gold_icon.png directly, or renders a crisp gold badge.
    Never draws empty missing glyph boxes [].
    """
    for d in [ASSETS_DIR, SKINS_DIR]:
        p = os.path.join(d, "gold_icon.png")
        if os.path.exists(p):
            try:
                with Image.open(p) as src:
                    return src.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
            except Exception:
                pass

    # Procedural fallback without font dependency
    w, h = size
    img = Image.new("RGBA", size, (25, 18, 5, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([1, 1, w - 2, h - 2], outline=(255, 215, 0, 255), width=2)
    draw.rectangle([3, 3, w - 4, h - 4], fill=(50, 36, 10, 255))
    return img

def create_placeholder_image(skin_name: str, rarity: str = "Mil-Spec", size: Tuple[int, int] = (100, 100)) -> Image.Image:
    """Creates a stylized placeholder. For Rare Special/knives, returns the gold badge."""
    is_knife = rarity == "Rare Special" or any(k in skin_name.lower() for k in ["knife", "bayonet", "karambit", "daggers", "gloves"])
    if is_knife:
        return create_gold_special_card(size)

    rarity_color_map = {
        "Mil-Spec":   (75,  105, 255),
        "Restricted": (136,  71, 255),
        "Classified": (211,  44, 230),
        "Covert":     (235,  75,  75),
    }
    accent_rgb = rarity_color_map.get(rarity, (100, 116, 139))
    bg_rgb = (18, 21, 28)

    img = Image.new("RGBA", size, bg_rgb)
    draw = ImageDraw.Draw(img)
    w, h = size

    # Sleek border glow
    draw.rectangle([2, 2, w - 3, h - 3], outline=accent_rgb, width=2)
    # Bottom accent line
    draw.rectangle([2, h - 6, w - 3, h - 3], fill=accent_rgb)

    # Clean ASCII weapon model initials
    clean = re.sub(r'^[★\*\[\]\(\)\s]+', '', skin_name).strip()
    clean = re.sub(r'[^\x20-\x7E]', ' ', clean)
    weapon_part = clean.split("|")[0].strip()
    initials = "".join([p[0] for p in weapon_part.split()[:2] if p and p[0].isalnum()]).upper()

    font = None
    for fpath in ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(fpath):
            try:
                font = ImageFont.truetype(fpath, max(10, min(18, h // 3)))
                break
            except Exception:
                continue

    if initials:
        try:
            if font:
                draw.text((w // 2, h // 2 - 4), initials, fill=(220, 220, 220), font=font, anchor="mm")
            else:
                draw.text((w // 2 - len(initials) * 3, h // 2 - 6), initials, fill=(220, 220, 220))
        except Exception:
            pass

    return img

def get_pil_image(skin_name: str, rarity: str = "Mil-Spec", size: Tuple[int, int] = (100, 100)) -> Image.Image:
    """
    Returns a resized PIL Image for a skin.
    Fallback chain: cached PNG -> sanitized-name PNG -> knife silhouette -> gold badge -> dark placeholder.
    """
    cache_key = f"{skin_name}_{size[0]}x{size[1]}"
    if cache_key in _PIL_CACHE:
        return _PIL_CACHE[cache_key]

    # Full fallback disk search
    file_path = find_local_skin_file(skin_name, rarity)
    if file_path and os.path.exists(file_path):
        try:
            with Image.open(file_path) as src:
                img = src.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                _PIL_CACHE[cache_key] = img
                return img
        except Exception:
            pass

    # Trigger background download if missing
    download_skin_image_async(skin_name)

    # Return styled placeholder
    placeholder = create_placeholder_image(skin_name, rarity, size)
    return placeholder

def get_skin_image(skin_name: str, rarity: str = "Mil-Spec", size: Tuple[int, int] = (100, 100)) -> ctk.CTkImage:
    """Returns a CTkImage suitable for CustomTkinter labels and buttons."""
    cache_key = f"{skin_name}_{size[0]}x{size[1]}"
    if cache_key in _CTK_CACHE:
        return _CTK_CACHE[cache_key]

    pil_img = get_pil_image(skin_name, rarity, size)
    ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    _CTK_CACHE[cache_key] = ctk_img
    return ctk_img

def get_tk_photo_image(skin_name: str, rarity: str = "Mil-Spec", size: Tuple[int, int] = (64, 48)) -> ImageTk.PhotoImage:
    """Returns an ImageTk.PhotoImage for Tkinter Canvas rendering."""
    cache_key = f"tk_{skin_name}_{size[0]}x{size[1]}"
    if cache_key in _TK_CACHE:
        return _TK_CACHE[cache_key]

    pil_img = get_pil_image(skin_name, rarity, size)
    photo = ImageTk.PhotoImage(pil_img)
    _TK_CACHE[cache_key] = photo
    return photo

_GOLD_CARD_PHOTO_CACHE: Dict[str, ImageTk.PhotoImage] = {}

def get_gold_special_tk_photo(size: Tuple[int, int] = (44, 32)) -> ImageTk.PhotoImage:
    """
    Returns a cached ImageTk.PhotoImage of the gold ★ special item badge.
    Always instant and authentic.
    """
    cache_key = f"gold_special_{size[0]}x{size[1]}"
    if cache_key in _GOLD_CARD_PHOTO_CACHE:
        return _GOLD_CARD_PHOTO_CACHE[cache_key]

    pil_img = create_gold_special_card(size)
    photo = ImageTk.PhotoImage(pil_img)
    _GOLD_CARD_PHOTO_CACHE[cache_key] = photo
    return photo

def prefetch_case_images(items: dict):
    """
    Pre-downloads all skin/knife images for every item in a case's item pool.
    Call whenever a new case is selected so images are ready before the user spins.
    """
    for rarity_items in items.values():
        for entry in rarity_items:
            name = entry[0] if isinstance(entry, (list, tuple)) else entry
            download_skin_image_async(name)

