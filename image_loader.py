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

def get_cached_file_path(skin_name: str) -> str:
    """Finds existing file path in writable dir, bundled resource dir, or default target."""
    filename = sanitize_filename(skin_name)
    target_writable = os.path.join(WRITABLE_SKINS_DIR, filename)
    if os.path.exists(target_writable):
        return target_writable

    target_bundled = os.path.join(SKINS_DIR, filename)
    if os.path.exists(target_bundled):
        return target_bundled

    return target_writable

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

def create_placeholder_image(skin_name: str, rarity: str = "Mil-Spec", size: Tuple[int, int] = (100, 100)) -> Image.Image:
    """Creates a sleek, stylized dark placeholder with rarity badge if image is not downloaded."""
    rarity_color_map = {
        "Mil-Spec": (75, 105, 255),
        "Restricted": (136, 71, 255),
        "Classified": (211, 44, 230),
        "Covert": (235, 75, 75),
        "Rare Special": (255, 215, 0)
    }
    accent_rgb = rarity_color_map.get(rarity, (100, 116, 139))
    bg_rgb = (18, 21, 28)

    img = Image.new("RGBA", size, bg_rgb)
    draw = ImageDraw.Draw(img)
    w, h = size

    # Inner subtle glow rectangle
    draw.rectangle([2, 2, w - 3, h - 3], outline=accent_rgb, width=2)

    # Diagonal accent line
    draw.line([(6, h - 12), (w - 6, 12)], fill=(accent_rgb[0]//2, accent_rgb[1]//2, accent_rgb[2]//2), width=2)

    # Weapon initials
    initials = "".join([part[0] for part in skin_name.replace("★", "").split()[:3] if part]).upper()
    try:
        draw.text((w // 2, h // 2), initials, fill=(240, 240, 240), anchor="mm")
    except Exception:
        draw.text((w // 4, h // 3), initials, fill=(240, 240, 240))

    return img

def get_pil_image(skin_name: str, rarity: str = "Mil-Spec", size: Tuple[int, int] = (100, 100)) -> Image.Image:
    """Returns a resized PIL Image for a skin, downloading asynchronously if missing."""
    cache_key = f"{skin_name}_{size[0]}x{size[1]}"
    if cache_key in _PIL_CACHE:
        return _PIL_CACHE[cache_key]

    file_path = get_cached_file_path(skin_name)
    if os.path.exists(file_path):
        try:
            with Image.open(file_path) as src:
                img = src.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
                _PIL_CACHE[cache_key] = img
                return img
        except Exception:
            pass

    # Trigger background download if missing
    download_skin_image_async(skin_name)

    # Return placeholder
    placeholder = create_placeholder_image(skin_name, rarity, size)
    _PIL_CACHE[cache_key] = placeholder
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


def create_gold_special_card(size: Tuple[int, int] = (44, 32)) -> Image.Image:
    """
    Generates a procedural gold ★ icon image for Rare Special roulette cards.
    No CDN download needed — always instant and correct.
    """
    w, h = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gold gradient-like background using layered rectangles (dark gold → bright gold)
    layers = [
        ((0,      0,      w,     h),     (45,  28,   0, 255)),   # darkest border ring
        ((1,      1,  w - 1, h - 1),     (90,  60,   0, 255)),
        ((2,      2,  w - 2, h - 2),     (140, 100,  0, 255)),
        ((3,      3,  w - 3, h - 3),     (184, 134,  11, 255)),  # #b8860b DarkGoldenrod
        ((4,      4,  w - 4, h - 4),     (212, 175,  55, 255)),  # #d4af37 Goldenrod
    ]
    for rect, color in layers:
        draw.rectangle(rect, fill=color)

    # Bright gold outer glow border
    draw.rectangle([0, 0, w - 1, h - 1], outline=(255, 215, 0, 255), width=1)

    # Centered ★ star symbol
    star = "★"
    star_font_size = max(10, h // 2)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("segoeui.ttf", star_font_size)
    except Exception:
        font = None  # PIL default

    cx, cy = w // 2, h // 2 - 1
    # Draw shadow
    shadow_offset = max(1, w // 22)
    try:
        draw.text((cx + shadow_offset, cy + shadow_offset), star, fill=(80, 50, 0, 180), font=font, anchor="mm")
    except Exception:
        draw.text((cx + shadow_offset - star_font_size // 2, cy + shadow_offset - star_font_size // 2),
                  star, fill=(80, 50, 0, 180))

    # Draw bright gold star
    try:
        draw.text((cx, cy), star, fill=(255, 235, 100, 255), font=font, anchor="mm")
    except Exception:
        draw.text((cx - star_font_size // 2, cy - star_font_size // 2), star, fill=(255, 235, 100, 255))

    return img


_GOLD_CARD_PHOTO_CACHE: Dict[str, ImageTk.PhotoImage] = {}


def get_gold_special_tk_photo(size: Tuple[int, int] = (44, 32)) -> ImageTk.PhotoImage:
    """
    Returns a cached ImageTk.PhotoImage of the gold ★ special item card.
    Always instant — no download, no CDN lookup.
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
    items: dict mapping rarity -> list of (name, color) tuples or just names.
    """
    for rarity_items in items.values():
        for entry in rarity_items:
            name = entry[0] if isinstance(entry, (list, tuple)) else entry
            download_skin_image_async(name)
