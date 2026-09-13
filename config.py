# CONFIG & CONSTANTS
import sys
import os

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and for PyInstaller _MEIPASS.
    Used for read-only bundled assets (audio, images, default templates).
    """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    # Direct target path
    target = os.path.join(base_path, relative_path)
    if os.path.exists(target):
        return target

    # Check inside 'assets' directory
    assets_target = os.path.join(base_path, "assets", relative_path)
    if os.path.exists(assets_target):
        return assets_target

    # Check inside '_internal' (when --contents-directory "_internal" is used)
    internal_target = os.path.join(base_path, "_internal", relative_path)
    if os.path.exists(internal_target):
        return internal_target

    internal_assets = os.path.join(base_path, "_internal", "assets", relative_path)
    if os.path.exists(internal_assets):
        return internal_assets

    # Fallback to project root directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    root_target = os.path.join(root_dir, relative_path)
    if os.path.exists(root_target):
        return root_target

    return target

def get_writable_path(relative_path: str) -> str:
    """
    Get writable path for user data files (save.json, custom_cases.json).
    When running as frozen .exe, writes to the directory containing the executable.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, relative_path)

SAVE_FILE = get_writable_path("save.dat")
LEGACY_SAVE_FILE = get_writable_path("save.json")
CUSTOM_CASES_FILE = get_writable_path("custom_cases.dat")
LEGACY_CUSTOM_CASES_FILE = get_writable_path("custom_cases.json")
KEY_PRICE = 2.49  # Fixed key cost to open any case

# Official CS2 Drop Odds (Weighted Probability)
RARITY_CHANCES = {
    "Mil-Spec": 0.7992,
    "Restricted": 0.1598,
    "Classified": 0.0320,
    "Covert": 0.0064,
    "Rare Special": 0.0026
}

# Fixed 10% StatTrak chance across all drops
STATTRAK_CHANCE = 0.10

# Base selling prices by rarity tier
SELL_PRICES = {
    "Mil-Spec": 2.0,
    "Restricted": 10.0,
    "Classified": 40.0,
    "Covert": 150.0,
    "Rare Special": 500.0
}

# StatTrak price multiplier
STAT_TRACK_MULTIPLIER = 2.5

# Rarity Color Definitions
RARITY_COLORS = {
    "Mil-Spec": "#4b69ff",
    "Restricted": "#8847ff",
    "Classified": "#d32ce6",
    "Covert": "#eb4b4b",
    "Rare Special": "#ffd700"
}

RARITIES = ["Mil-Spec", "Restricted", "Classified", "Covert", "Rare Special"]