import config
from item_prices import (
    get_item_market_price,
    calculate_scaled_tier_odds,
    BENCHMARK_TIER_PRICES,
    ITEM_MARKET_PRICES
)

CASES = {

    # ---------------------------
    # KILOWATT CASE (CS2)
    # ---------------------------

    "Kilowatt Case": {
        "price": 0.45,
        "multiplier": 1.0,
        "items": {
            "Mil-Spec": [
                ("MAC-10 | Light Box", "blue"),
                ("SSG 08 | Dezastre", "blue"),
                ("XM1014 | Irezumi", "blue"),
                ("UMP-45 | Motorized", "blue"),
                ("Tec-9 | Slag", "blue"),
                ("Dual Berettas | Hideout", "blue"),
                ("Nova | Dark Sigil", "blue")
            ],
            "Restricted": [
                ("Glock-18 | Block-18", "purple"),
                ("M4A4 | Etch Lord", "purple"),
                ("Five-SeveN | Hybrid", "purple"),
                ("MP7 | Just Smile", "purple"),
                ("Sawed-Off | Analog Input", "purple")
            ],
            "Classified": [
                ("M4A1-S | Black Lotus", "pink"),
                ("Zeus x27 | Olympus", "pink"),
                ("USP-S | Jawbreaker", "pink")
            ],
            "Covert": [
                ("AK-47 | Inheritance", "red"),
                ("AWP | Chrome Cannon", "red")
            ],
            "Rare Special": [
                ("★ Kukri Knife | Fade", "gold"),
                ("★ Kukri Knife | Slaughter", "gold"),
                ("★ Kukri Knife | Crimson Web", "gold"),
                ("★ Kukri Knife | Case Hardened", "gold"),
                ("★ Kukri Knife | Blue Steel", "gold"),
                ("★ Kukri Knife | Stained", "gold"),
                ("★ Kukri Knife | Night Stripe", "gold"),
                ("★ Kukri Knife | Safari Mesh", "gold"),
                ("★ Kukri Knife | Boreal Forest", "gold"),
                ("★ Kukri Knife | Forest DDPAT", "gold"),
                ("★ Kukri Knife | Urban Masked", "gold"),
                ("★ Kukri Knife | Scorched", "gold")
            ]
        }
    },

    # ---------------------------
    # DREAMS & NIGHTMARES CASE
    # ---------------------------

    "Dreams & Nightmares Case": {
        "price": 1.60,
        "multiplier": 1.4,
        "items": {
            "Mil-Spec": [
                ("Five-SeveN | Scrawl", "blue"),
                ("MP5-SD | Necro Jr.", "blue"),
                ("MAC-10 | Ensnared", "blue"),
                ("P2000 | Lifted Spirits", "blue"),
                ("Sawed-Off | Spirit Board", "blue"),
                ("MAG-7 | Foresight", "blue"),
                ("SCAR-20 | Poultrygeist", "blue")
            ],
            "Restricted": [
                ("G3SG1 | Dream Glade", "purple"),
                ("M4A1-S | Night Terror", "purple"),
                ("USP-S | Ticket to Hell", "purple"),
                ("PP-Bizon | Space Cat", "purple"),
                ("XM1014 | Zombie Offensive", "purple")
            ],
            "Classified": [
                ("Dual Berettas | Melondrama", "pink"),
                ("MP7 | Abyssal Apparition", "pink"),
                ("FAMAS | Rapid Eye Movement", "pink")
            ],
            "Covert": [
                ("AK-47 | Nightwish", "red"),
                ("MP9 | Starlight Protector", "red")
            ],
            "Rare Special": [
                ("★ Butterfly Knife | Night", "gold"),
                ("★ Karambit | Night", "gold"),
                ("★ M9 Bayonet | Night", "gold"),
                ("★ Kukri Knife | Night", "gold")
            ]
        }
    },

    # ---------------------------
    # RECOIL CASE
    # ---------------------------

    "Recoil Case": {
        "price": 0.20,
        "multiplier": 0.8,
        "items": {
            "Mil-Spec": [
                ("M4A4 | Poly Mag", "blue"),
                ("FAMAS | Meow 36", "blue"),
                ("MAC-10 | Monkeyflage", "blue"),
                ("Glock-18 | Winterized", "blue"),
                ("Negev | Drop Me", "blue"),
                ("UMP-45 | Roadblock", "blue"),
                ("Galil AR | Destroyer", "blue")
            ],
            "Restricted": [
                ("Dual Berettas | Flora Carnivora", "purple"),
                ("R8 Revolver | Crazy 8", "purple"),
                ("M249 | Downtown", "purple"),
                ("SG 553 | Dragon Tech", "purple"),
                ("P90 | Vent Rush", "purple")
            ],
            "Classified": [
                ("AK-47 | Ice Coaled", "pink"),
                ("Sawed-Off | Kiss♥Love", "pink"),
                ("P250 | Visions", "pink")
            ],
            "Covert": [
                ("AWP | Chromatic Aberration", "red"),
                ("USP-S | Printstream", "red")
            ],
            "Rare Special": [
                ("★ Kukri Knife | Doppler", "gold"),
                ("★ Karambit | Doppler", "gold"),
                ("★ M9 Bayonet | Doppler", "gold"),
                ("★ Butterfly Knife | Doppler", "gold")
            ]
        }
    },

    # ---------------------------
    # OPERATION HYDRA CASE
    # ---------------------------

    "Operation Hydra Case": {
        "price": 22.00,
        "multiplier": 6.0,
        "items": {
            "Mil-Spec": [
                ("UMP-45 | Metal Flowers", "blue"),
                ("Tec-9 | Cut Out", "blue"),
                ("FAMAS | Macabre", "blue"),
                ("MAG-7 | Hard Water", "blue"),
                ("MAC-10 | Aloha", "blue"),
                ("M4A1-S | Briefing", "blue"),
                ("USP-S | Blueprint", "blue")
            ],
            "Restricted": [
                ("P250 | Red Rock", "purple"),
                ("P90 | Death Grip", "purple"),
                ("P2000 | Woodsman", "purple"),
                ("SSG 08 | Death's Head", "purple"),
                ("AK-47 | Orbit Mk01", "purple")
            ],
            "Classified": [
                ("Galil AR | Sugar Rush", "pink"),
                ("M4A4 | Hellfire", "pink"),
                ("Dual Berettas | Cobra Strike", "pink")
            ],
            "Covert": [
                ("Five-SeveN | Hyper Beast", "red"),
                ("AWP | Oni Taiji", "red")
            ],
            "Rare Special": [
                ("★ Sport Gloves | Hedge Maze", "gold"),
                ("★ Sport Gloves | Pandora's Box", "gold"),
                ("★ Specialist Gloves | Crimson Kimono", "gold"),
                ("★ Moto Gloves | Spearmint", "gold")
            ]
        }
    },

    # ---------------------------
    # DANGER ZONE CASE
    # ---------------------------

    "Danger Zone Case": {
        "price": 1.75,
        "multiplier": 1.5,
        "items": {
            "Mil-Spec": [
                ("Glock-18 | Oxide Blaze", "blue"),
                ("M4A4 | Magnesium", "blue"),
                ("MP9 | Modest Threat", "blue"),
                ("Nova | Wood Fired", "blue"),
                ("Sawed-Off | Black Sand", "blue"),
                ("SG 553 | Danger Close", "blue"),
                ("Tec-9 | Fubar", "blue")
            ],
            "Restricted": [
                ("G3SG1 | Scavenger", "purple"),
                ("Galil AR | Signal", "purple"),
                ("MAC-10 | Pipe Down", "purple"),
                ("P250 | Nevermore", "purple"),
                ("USP-S | Flashback", "purple")
            ],
            "Classified": [
                ("Desert Eagle | Mecha Industries", "pink"),
                ("MP5-SD | Phosphor", "pink"),
                ("UMP-45 | Momentum", "pink")
            ],
            "Covert": [
                ("AK-47 | Asiimov", "red"),
                ("AWP | Neo-Noir", "red")
            ],
            "Rare Special": [
                ("★ Huntsman Knife | Case Hardened", "gold"),
                ("★ Talon Knife | Fade", "gold"),
                ("★ Ursus Knife | Doppler", "gold"),
                ("★ Stiletto Knife | Crimson Web", "gold")
            ]
        }
    },

    # ---------------------------
    # PRISMA 2 CASE
    # ---------------------------

    "Prisma 2 Case": {
        "price": 1.20,
        "multiplier": 1.2,
        "items": {
            "Mil-Spec": [
                ("Desert Eagle | Blue Ply", "blue"),
                ("CZ75-Auto | Distressed", "blue"),
                ("MP5-SD | Desert Strike", "blue"),
                ("Negev | Prototype", "blue"),
                ("R8 Revolver | Bone Forged", "blue"),
                ("AUG | Tom Cat", "blue"),
                ("AWP | Capillary", "blue")
            ],
            "Restricted": [
                ("SSG 08 | Fever Dream", "purple"),
                ("SG 553 | Darkwing", "purple"),
                ("P2000 | Acid Etched", "purple"),
                ("Sawed-Off | Apocalypto", "purple"),
                ("SCAR-20 | Enforcer", "purple")
            ],
            "Classified": [
                ("AK-47 | Phantom Disruptor", "pink"),
                ("MAC-10 | Disco Tech", "pink"),
                ("MAG-7 | Justice", "pink")
            ],
            "Covert": [
                ("Glock-18 | Bullet Queen", "red"),
                ("M4A1-S | Player Two", "red")
            ],
            "Rare Special": [
                ("★ Ursus Knife | Doppler", "gold"),
                ("★ Navaja Knife | Doppler", "gold"),
                ("★ Stiletto Knife | Doppler", "gold"),
                ("★ Talon Knife | Doppler", "gold")
            ]
        }
    },

    # ---------------------------
    # PRISMA CASE
    # ---------------------------

    "Prisma Case": {
        "price": 0.90,
        "multiplier": 1.1,
        "items": {
            "Mil-Spec": [
                ("MP7 | Mischief", "blue"),
                ("P250 | Verdigris", "blue"),
                ("Galil AR | Akoben", "blue"),
                ("FAMAS | Crypsis", "blue"),
                ("AWP | Atheris", "blue"),
                ("Dual Berettas | Moon in Libra", "blue"),
                ("MAC-10 | Whitefish", "blue")
            ],
            "Restricted": [
                ("UMP-45 | Moonrise", "purple"),
                ("R8 Revolver | Skull Crusher", "purple"),
                ("XM1014 | Oxide Blaze", "purple"),
                ("AUG | Momentum", "purple"),
                ("Five-SeveN | Angry Mob", "purple")
            ],
            "Classified": [
                ("AK-47 | Uncharted", "pink"),
                ("Desert Eagle | Light Rail", "pink"),
                ("Tec-9 | Bamboozle", "pink")
            ],
            "Covert": [
                ("AWP | Neo-Noir", "red"),
                ("M4A4 | The Emperor", "red")
            ],
            "Rare Special": [
                ("★ Stiletto Knife | Urban Masked", "gold"),
                ("★ Ursus Knife | Boreal Forest", "gold"),
                ("★ Navaja Knife | Stained", "gold"),
                ("★ Talon Knife | Forest DDPAT", "gold")
            ]
        }
    },

    # ---------------------------
    # FRACTURE CASE
    # ---------------------------

    "Fracture Case": {
        "price": 0.60,
        "multiplier": 1.0,
        "items": {
            "Mil-Spec": [
                ("Negev | Ultralight", "blue"),
                ("P250 | Cassette", "blue"),
                ("PP-Bizon | Runic", "blue"),
                ("SG 553 | Ol' Rusty", "blue"),
                ("MP5-SD | Kitbash", "blue"),
                ("MAC-10 | Allure", "blue"),
                ("Galil AR | Connexion", "blue")
            ],
            "Restricted": [
                ("SSG 08 | Mainframe 001", "purple"),
                ("Tec-9 | Brother", "purple"),
                ("P2000 | Gnarled", "purple"),
                ("CZ75-Auto | Framework", "purple"),
                ("UMP-45 | Gold Bismuth", "purple")
            ],
            "Classified": [
                ("M4A4 | Tooth Fairy", "pink"),
                ("Glock-18 | Vogue", "pink"),
                ("MAC-10 | Printstream", "pink")
            ],
            "Covert": [
                ("Desert Eagle | Printstream", "red"),
                ("AK-47 | Legion of Anubis", "red")
            ],
            "Rare Special": [
                ("★ Skeleton Knife | Fade", "gold"),
                ("★ Paracord Knife | Urban Masked", "gold"),
                ("★ Nomad Knife | Scorched", "gold"),
                ("★ Survival Knife | Boreal Forest", "gold")
            ]
        }
    },

    # ---------------------------
    # SNAKEBITE CASE
    # ---------------------------

    "Snakebite Case": {
        "price": 0.60,
        "multiplier": 1.0,
        "items": {
            "Mil-Spec": [
                ("CZ75-Auto | Circaetus", "blue"),
                ("M249 | O.S.I.P.R.", "blue"),
                ("UMP-45 | Oscillator", "blue"),
                ("P250 | Cyber Shell", "blue"),
                ("MP9 | Food Chain", "blue"),
                ("MAC-10 | Button Masher", "blue"),
                ("SG 553 | Heavy Metal", "blue")
            ],
            "Restricted": [
                ("USP-S | The Traitor", "purple"),
                ("XM1014 | XOXO", "purple"),
                ("Glock-18 | Clear Polymer", "purple"),
                ("MAG-7 | Petroglyph", "purple"),
                ("Nova | Windblown", "purple")
            ],
            "Classified": [
                ("Desert Eagle | Trigger Discipline", "pink"),
                ("CZ75-Auto | Vendetta", "pink"),
                ("Galil AR | Chromatic Aberration", "pink")
            ],
            "Covert": [
                ("AK-47 | Slate", "red"),
                ("M4A4 | In Living Color", "red")
            ],
            "Rare Special": [
                ("★ Hydra Gloves | Emerald Web", "gold"),
                ("★ Broken Fang Gloves | Yellow-banded", "gold"),
                ("★ Driver Gloves | Snow Leopard", "gold"),
                ("★ Hand Wraps | CAUTION!", "gold")
            ]
        }
    },

    # ---------------------------
    # HORIZON CASE
    # ---------------------------

    "Horizon Case": {
        "price": 0.90,
        "multiplier": 1.1,
        "items": {
            "Mil-Spec": [
                ("G3SG1 | High Seas", "blue"),
                ("P250 | Nevermore", "blue"),
                ("MP9 | Capillary", "blue"),
                ("Glock-18 | Warhawk", "blue"),
                ("R8 Revolver | Survivalist", "blue"),
                ("Nova | Toy Soldier", "blue"),
                ("CZ75-Auto | Eco", "blue")
            ],
            "Restricted": [
                ("M4A1-S | Nightmare", "purple"),
                ("UMP-45 | Momentum", "purple"),
                ("AUG | Amber Slipstream", "purple"),
                ("Dual Berettas | Shred", "purple"),
                ("Sawed-Off | Devourer", "purple")
            ],
            "Classified": [
                ("AK-47 | Neon Rider", "pink"),
                ("FAMAS | Eye of Athena", "pink"),
                ("MP7 | Bloodsport", "pink")
            ],
            "Covert": [
                ("Desert Eagle | Code Red", "red"),
                ("AWP | PAW", "red")
            ],
            "Rare Special": [
                ("★ Talon Knife | Fade", "gold"),
                ("★ Stiletto Knife | Damascus Steel", "gold"),
                ("★ Ursus Knife | Case Hardened", "gold"),
                ("★ Navaja Knife | Marble Fade", "gold")
            ]
        }
    }
}

import os
import json
from security import save_encrypted_file, load_encrypted_file

CUSTOM_CASES_FILE = config.CUSTOM_CASES_FILE
CUSTOM_CASES = {}

def load_custom_cases() -> dict:
    """Loads user-created custom cases from secure custom_cases.dat in the writable app directory."""
    global CUSTOM_CASES
    data = None
    is_tampered = False

    # 1. Attempt loading encrypted custom_cases.dat
    if os.path.exists(CUSTOM_CASES_FILE):
        data, is_tampered = load_encrypted_file(CUSTOM_CASES_FILE)
        if is_tampered:
            print(f"[SECURITY ALERT] Custom cases file '{CUSTOM_CASES_FILE}' failed HMAC verification! Resetting to safe defaults.")
            data = {}

    # 2. Backward compatibility: if .dat doesn't exist, check legacy custom_cases.json
    if data is None:
        legacy_file = getattr(config, "LEGACY_CUSTOM_CASES_FILE", None)
        if legacy_file and os.path.exists(legacy_file):
            try:
                with open(legacy_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"[*] Migrated legacy custom cases from '{legacy_file}' to encrypted format '{CUSTOM_CASES_FILE}'")
                save_custom_cases(data)
            except Exception as e:
                print(f"Warning: Could not load legacy custom cases: {e}")

    # 3. Check bundled resource template (e.g. Inside PyInstaller binary)
    if data is None:
        bundled_file = config.get_resource_path("custom_cases.dat")
        if not os.path.exists(bundled_file):
            bundled_file = config.get_resource_path("custom_cases.json")

        if os.path.exists(bundled_file) and os.path.abspath(bundled_file) != os.path.abspath(CUSTOM_CASES_FILE):
            try:
                b_data, _ = load_encrypted_file(bundled_file)
                if b_data is None:
                    with open(bundled_file, "r", encoding="utf-8") as bf:
                        b_data = json.load(bf)
                if b_data:
                    save_custom_cases(b_data)
                    return CUSTOM_CASES
            except Exception as e:
                print(f"Warning: Could not copy bundled custom cases: {e}")

    # 4. Fallback: Create initial sample custom case so users see an example
    if data is None:
        sample_cases = {
            "Community Legends Case": {
                "price": 2.50,
                "multiplier": 1.5,
                "items": {
                    "Mil-Spec": [
                        ("Glock-18 | High Beam", "blue"),
                        ("USP-S | Lead Conduit", "blue"),
                        ("M4A4 | Magnesium", "blue")
                    ],
                    "Restricted": [
                        ("AWP | Atheris", "purple"),
                        ("AK-47 | Uncharted", "purple")
                    ],
                    "Classified": [
                        ("M4A1-S | Hyper Beast", "pink"),
                        ("Desert Eagle | Mecha Industries", "pink")
                    ],
                    "Covert": [
                        ("AK-47 | Bloodsport", "red"),
                        ("AWP | Asiimov", "red")
                    ],
                    "Rare Special": [
                        ("★ Karambit | Doppler", "gold"),
                        ("★ Butterfly Knife | Fade", "gold")
                    ]
                }
            }
        }
        save_custom_cases(sample_cases)
        return CUSTOM_CASES

    CUSTOM_CASES = data if isinstance(data, dict) else {}
    return CUSTOM_CASES

def save_custom_cases(cases_dict: dict):
    """Saves custom cases dictionary to encrypted custom_cases.dat atomically."""
    global CUSTOM_CASES
    CUSTOM_CASES = cases_dict
    success = save_encrypted_file(CUSTOM_CASES_FILE, CUSTOM_CASES)
    if not success:
        print(f"Warning: Failed to save custom cases to '{CUSTOM_CASES_FILE}'")

# Initialize custom cases
load_custom_cases()

def delete_custom_case(case_name: str) -> bool:
    """Deletes a custom case by name from custom_cases.json and updates in-memory registry."""
    global CUSTOM_CASES
    # Safety guard: Never allow deletion of official CS2 cases
    if case_name in CASES:
        return False

    load_custom_cases()
    if case_name in CUSTOM_CASES:
        del CUSTOM_CASES[case_name]
        save_custom_cases(CUSTOM_CASES)
        return True
    return False

def get_case(case_name: str) -> dict:
    """Returns case data from either official CASES or CUSTOM_CASES."""
    if case_name in CASES:
        return CASES[case_name]
    return CUSTOM_CASES.get(case_name)

def get_all_known_items() -> dict:
    """Aggregates all unique skins across all cases organized by rarity."""
    unique_by_rarity = {r: set() for r in config.RARITIES}
    for c in CASES.values():
        for r, items_list in c.get("items", {}).items():
            if r in unique_by_rarity:
                for name, color in items_list:
                    unique_by_rarity[r].add((name, color))

    # Convert sets back to sorted lists
    return {r: sorted(list(s)) for r, s in unique_by_rarity.items()}

def calculate_custom_case_ev(case_items: dict, margin_multiplier: float = 1.10) -> tuple[float, float, dict, str, dict]:
    """
    Calculates the statistical Expected Value (EV), final automated case price,
    individual tier contributions, volatility risk rating, and dynamically scaled odds.
    Returns: (base_ev, final_case_price, tier_contributions, risk_rating, scaled_odds)
    """
    has_any_items = any(bool(case_items.get(r)) for r in config.RARITIES)
    if not has_any_items:
        return 0.0, 0.0, {r: 0.0 for r in config.RARITIES}, "N/A", dict(config.RARITY_CHANCES)

    scaled_odds, tier_avg_prices, scale_factors = calculate_scaled_tier_odds(case_items)

    base_ev = 0.0
    tier_contributions = {}
    for r in config.RARITIES:
        avg_p = tier_avg_prices.get(r, 0.0)
        odds = scaled_odds.get(r, 0.0)
        contrib = avg_p * odds
        tier_contributions[r] = round(contrib, 2)
        base_ev += contrib

    base_ev = round(base_ev, 2)
    final_price = round(base_ev * margin_multiplier, 2)

    # Volatility / Risk Rating calculation
    # Evaluates EV concentration in top tiers or high-value jackpot items
    high_tier_contrib = tier_contributions.get("Covert", 0.0) + tier_contributions.get("Rare Special", 0.0)
    high_tier_ratio = (high_tier_contrib / base_ev) if base_ev > 0 else 0.0
    gold_avg = tier_avg_prices.get("Rare Special", 0.0)

    if high_tier_ratio >= 0.50 or gold_avg >= 600.0:
        risk_rating = "🔥 High Volatility / Degen"
    elif high_tier_ratio >= 0.28 or gold_avg >= 200.0:
        risk_rating = "⚖️ Medium Risk / Balanced"
    else:
        risk_rating = "🛡️ Safe / Low Risk"

    return base_ev, final_price, tier_contributions, risk_rating, scaled_odds