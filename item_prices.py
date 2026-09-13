from typing import Optional, Dict, Tuple
import config

# Benchmark tier reference valuations (standard realistic average prices for CS2 rarity tiers)
BENCHMARK_TIER_PRICES: Dict[str, float] = {
    "Mil-Spec": 0.35,
    "Restricted": 2.00,
    "Classified": 12.00,
    "Covert": 35.00,
    "Rare Special": 250.00
}

# Individual Market Value Database for all known CS2 skins
ITEM_MARKET_PRICES: Dict[str, float] = {
    # Iconic / Requested specific skins
    "AK-47 | Slate": 3.00,
    "AWP | Oni Taiji": 250.00,
    "AWP | Dragon Lore": 4500.00,
    "M4A4 | Howl": 3800.00,

    # Covert Weapons
    "AK-47 | Inheritance": 95.00,
    "AWP | Chrome Cannon": 70.00,
    "Desert Eagle | Printstream": 75.00,
    "AK-47 | Asiimov": 45.00,
    "USP-S | Printstream": 40.00,
    "AWP | Neo-Noir": 32.00,
    "M4A1-S | Player Two": 28.00,
    "Five-SeveN | Hyper Beast": 24.00,
    "Desert Eagle | Code Red": 22.00,
    "M4A4 | The Emperor": 20.00,
    "AK-47 | Nightwish": 15.00,
    "AWP | Chromatic Aberration": 14.00,
    "AK-47 | Legion of Anubis": 12.00,
    "Glock-18 | Bullet Queen": 10.00,
    "M4A4 | In Living Color": 8.00,
    "MP9 | Starlight Protector": 6.00,
    "AWP | PAW": 4.50,

    # Classified Weapons
    "M4A4 | Hellfire": 55.00,
    "AK-47 | Neon Rider": 45.00,
    "M4A1-S | Black Lotus": 18.00,
    "USP-S | Jawbreaker": 16.00,
    "AK-47 | Ice Coaled": 15.00,
    "Galil AR | Sugar Rush": 14.00,
    "MAC-10 | Printstream": 12.00,
    "P250 | Visions": 11.00,
    "Zeus x27 | Olympus": 9.00,
    "MP5-SD | Phosphor": 8.50,
    "FAMAS | Eye of Athena": 7.50,
    "AK-47 | Phantom Disruptor": 7.00,
    "Desert Eagle | Mecha Industries": 6.50,
    "Glock-18 | Vogue": 6.00,
    "M4A4 | Tooth Fairy": 5.50,
    "MP7 | Bloodsport": 4.00,
    "MAC-10 | Disco Tech": 3.50,
    "AK-47 | Uncharted": 1.50,
    "CZ75-Auto | Vendetta": 2.20,
    "Desert Eagle | Light Rail": 3.80,
    "Desert Eagle | Trigger Discipline": 2.80,
    "Dual Berettas | Cobra Strike": 6.00,
    "Dual Berettas | Melondrama": 3.20,
    "FAMAS | Rapid Eye Movement": 2.60,
    "Galil AR | Chromatic Aberration": 3.00,
    "MAG-7 | Justice": 4.50,
    "MP7 | Abyssal Apparition": 3.80,
    "Sawed-Off | Kiss♥Love": 5.00,
    "Tec-9 | Bamboozle": 2.50,
    "UMP-45 | Momentum": 3.50,

    # Restricted Weapons
    "M4A1-S | Nightmare": 18.00,
    "AK-47 | Orbit Mk01": 16.00,
    "USP-S | The Traitor": 12.00,
    "AUG | Momentum": 2.20,
    "AWP | Atheris": 2.50,
    "M4A1-S | Night Terror": 1.80,
    "USP-S | Ticket to Hell": 1.50,
    "USP-S | Flashback": 1.20,
    "M4A4 | Etch Lord": 1.50,
    "Glock-18 | Block-18": 0.80,
    "Five-SeveN | Angry Mob": 3.50,
    "Five-SeveN | Hybrid": 1.40,
    "G3SG1 | Dream Glade": 0.90,
    "G3SG1 | Scavenger": 1.10,
    "Galil AR | Signal": 1.20,
    "Glock-18 | Clear Polymer": 0.70,
    "M249 | Downtown": 0.85,
    "MAC-10 | Pipe Down": 1.30,
    "MAG-7 | Petroglyph": 0.80,
    "MP7 | Just Smile": 1.10,
    "Nova | Windblown": 0.75,
    "P2000 | Acid Etched": 1.20,
    "P2000 | Gnarled": 0.65,
    "P2000 | Woodsman": 1.00,
    "P250 | Nevermore": 1.30,
    "P250 | Red Rock": 1.40,
    "P90 | Death Grip": 1.80,
    "P90 | Vent Rush": 1.20,
    "PP-Bizon | Space Cat": 0.90,
    "R8 Revolver | Crazy 8": 1.10,
    "R8 Revolver | Skull Crusher": 1.50,
    "SCAR-20 | Enforcer": 1.00,
    "SG 553 | Darkwing": 1.40,
    "SG 553 | Dragon Tech": 1.10,
    "SSG 08 | Death's Head": 1.30,
    "SSG 08 | Fever Dream": 1.60,
    "SSG 08 | Mainframe 001": 0.80,
    "Sawed-Off | Analog Input": 0.60,
    "Sawed-Off | Apocalypto": 0.75,
    "Sawed-Off | Devourer": 1.50,
    "Tec-9 | Brother": 0.95,
    "UMP-45 | Gold Bismuth": 0.85,
    "UMP-45 | Moonrise": 1.20,
    "XM1014 | Oxide Blaze": 0.70,
    "XM1014 | XOXO": 1.60,
    "XM1014 | Zombie Offensive": 0.85,
    "AUG | Amber Slipstream": 0.65,
    "CZ75-Auto | Framework": 0.90,
    "Dual Berettas | Flora Carnivora": 1.10,
    "Dual Berettas | Shred": 0.80,

    # Mil-Spec Weapons
    "USP-S | Blueprint": 4.50,
    "M4A1-S | Briefing": 0.75,
    "AWP | Capillary": 0.40,
    "SSG 08 | Dezastre": 0.35,
    "M4A4 | Magnesium": 0.35,
    "M4A4 | Poly Mag": 0.30,
    "Glock-18 | Oxide Blaze": 0.30,
    "Glock-18 | Warhawk": 0.28,
    "MAC-10 | Light Box": 0.25,
    "Glock-18 | Winterized": 0.25,
    "Dual Berettas | Hideout": 0.20,
    "AUG | Tom Cat": 0.22,
    "CZ75-Auto | Circaetus": 0.25,
    "CZ75-Auto | Distressed": 0.20,
    "CZ75-Auto | Eco": 0.35,
    "Desert Eagle | Blue Ply": 0.35,
    "Dual Berettas | Moon in Libra": 0.30,
    "FAMAS | Crypsis": 0.22,
    "FAMAS | Macabre": 0.25,
    "FAMAS | Meow 36": 0.28,
    "Five-SeveN | Scrawl": 0.24,
    "G3SG1 | High Seas": 0.25,
    "Galil AR | Akoben": 0.22,
    "Galil AR | Connexion": 0.30,
    "Galil AR | Destroyer": 0.25,
    "M249 | O.S.I.P.R.": 0.20,
    "MAC-10 | Allure": 0.32,
    "MAC-10 | Aloha": 0.20,
    "MAC-10 | Button Masher": 0.25,
    "MAC-10 | Ensnared": 0.24,
    "MAC-10 | Monkeyflage": 0.22,
    "MAC-10 | Whitefish": 0.20,
    "MAG-7 | Foresight": 0.22,
    "MAG-7 | Hard Water": 0.20,
    "MP5-SD | Desert Strike": 0.25,
    "MP5-SD | Kitbash": 0.28,
    "MP5-SD | Necro Jr.": 0.30,
    "MP7 | Mischief": 0.22,
    "MP9 | Capillary": 0.22,
    "MP9 | Food Chain": 0.45,
    "MP9 | Modest Threat": 0.20,
    "Negev | Drop Me": 0.25,
    "Negev | Prototype": 0.22,
    "Negev | Ultralight": 0.20,
    "Nova | Dark Sigil": 0.20,
    "Nova | Toy Soldier": 0.28,
    "Nova | Wood Fired": 0.22,
    "P2000 | Lifted Spirits": 0.25,
    "P250 | Cassette": 0.22,
    "P250 | Cyber Shell": 0.28,
    "P250 | Verdigris": 0.25,
    "PP-Bizon | Runic": 0.20,
    "R8 Revolver | Bone Forged": 0.25,
    "R8 Revolver | Survivalist": 0.22,
    "SCAR-20 | Poultrygeist": 0.20,
    "SG 553 | Danger Close": 0.22,
    "SG 553 | Heavy Metal": 0.25,
    "SG 553 | Ol' Rusty": 0.20,
    "Sawed-Off | Black Sand": 0.20,
    "Sawed-Off | Spirit Board": 0.22,
    "Tec-9 | Cut Out": 0.22,
    "Tec-9 | Fubar": 0.24,
    "Tec-9 | Slag": 0.20,
    "UMP-45 | Metal Flowers": 0.25,
    "UMP-45 | Motorized": 0.22,
    "UMP-45 | Oscillator": 0.20,
    "UMP-45 | Roadblock": 0.22,
    "XM1014 | Irezumi": 0.20,

    # Knives & Gloves (Rare Special)
    "★ Butterfly Knife | Fade": 1850.00,
    "★ Butterfly Knife | Doppler": 1650.00,
    "★ Butterfly Knife | Night": 450.00,
    "★ Karambit | Doppler": 1150.00,
    "★ Karambit | Night": 380.00,
    "★ M9 Bayonet | Doppler": 950.00,
    "★ M9 Bayonet | Night": 280.00,
    "★ Skeleton Knife | Fade": 1400.00,
    "★ Talon Knife | Fade": 1100.00,
    "★ Talon Knife | Doppler": 900.00,
    "★ Talon Knife | Forest DDPAT": 220.00,
    "★ Stiletto Knife | Doppler": 600.00,
    "★ Stiletto Knife | Crimson Web": 350.00,
    "★ Stiletto Knife | Damascus Steel": 260.00,
    "★ Stiletto Knife | Urban Masked": 160.00,
    "★ Kukri Knife | Doppler": 750.00,
    "★ Kukri Knife | Fade": 650.00,
    "★ Kukri Knife | Slaughter": 380.00,
    "★ Kukri Knife | Crimson Web": 260.00,
    "★ Kukri Knife | Case Hardened": 220.00,
    "★ Kukri Knife | Blue Steel": 160.00,
    "★ Kukri Knife | Night": 115.00,
    "★ Kukri Knife | Stained": 110.00,
    "★ Kukri Knife | Night Stripe": 105.00,
    "★ Kukri Knife | Urban Masked": 95.00,
    "★ Kukri Knife | Boreal Forest": 92.00,
    "★ Kukri Knife | Scorched": 90.00,
    "★ Kukri Knife | Forest DDPAT": 88.00,
    "★ Kukri Knife | Safari Mesh": 85.00,
    "★ Ursus Knife | Doppler": 420.00,
    "★ Ursus Knife | Case Hardened": 180.00,
    "★ Ursus Knife | Boreal Forest": 95.00,
    "★ Navaja Knife | Doppler": 190.00,
    "★ Navaja Knife | Marble Fade": 170.00,
    "★ Navaja Knife | Stained": 85.00,
    "★ Nomad Knife | Scorched": 140.00,
    "★ Paracord Knife | Urban Masked": 110.00,
    "★ Survival Knife | Boreal Forest": 95.00,
    "★ Huntsman Knife | Case Hardened": 190.00,
    "★ Sport Gloves | Pandora's Box": 2800.00,
    "★ Sport Gloves | Hedge Maze": 2200.00,
    "★ Specialist Gloves | Crimson Kimono": 1800.00,
    "★ Moto Gloves | Spearmint": 1500.00,
    "★ Driver Gloves | Snow Leopard": 850.00,
    "★ Hand Wraps | CAUTION!": 320.00,
    "★ Hydra Gloves | Emerald Web": 240.00,
    "★ Broken Fang Gloves | Yellow-banded": 120.00
}

def get_item_market_price(item_name: str, rarity: Optional[str] = None) -> float:
    """
    Returns the individual market value of a skin from the master database.
    If not found in explicit registry, estimates based on item keywords or tier benchmark.
    """
    if not item_name:
        return BENCHMARK_TIER_PRICES.get(rarity, 5.0)

    clean_name = item_name.strip()
    if clean_name in ITEM_MARKET_PRICES:
        return float(ITEM_MARKET_PRICES[clean_name])

    # Try without star prefix if present
    no_star = clean_name.lstrip("★ ").strip()
    if no_star in ITEM_MARKET_PRICES:
        return float(ITEM_MARKET_PRICES[no_star])

    with_star = f"★ {no_star}"
    if with_star in ITEM_MARKET_PRICES:
        return float(ITEM_MARKET_PRICES[with_star])

    # Pattern / knife-based keyword heuristic for user-created custom names
    lower = clean_name.lower()
    if "dragon lore" in lower:
        return 4500.0
    elif "howl" in lower:
        return 3800.0
    elif "butterfly" in lower:
        if "doppler" in lower or "fade" in lower:
            return 1650.0
        return 850.0
    elif "karambit" in lower:
        if "doppler" in lower or "fade" in lower:
            return 1200.0
        return 650.0
    elif "m9 bayonet" in lower:
        return 750.0
    elif "doppler" in lower:
        return 600.0
    elif "knife" in lower or "gloves" in lower or "★" in clean_name:
        return 220.0

    return float(BENCHMARK_TIER_PRICES.get(rarity, config.SELL_PRICES.get(rarity, 5.0)))

def calculate_scaled_tier_odds(case_items: dict) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """
    Calculates dynamically scaled drop probability odds based on the item valuations in each tier.
    Inverse Price-to-Odds Scaling Formula:
        Scale_Factor = Benchmark_Tier_Price / Avg_Tier_Price (if Avg_Tier_Price > Benchmark else 1.0)
        Raw_Weight = Base_Rarity_Weight * Scale_Factor
    Normalizes across active tiers so total sum(odds) == 1.0.
    Returns: (scaled_odds, tier_avg_prices, scale_factors)
    """
    raw_weights: Dict[str, float] = {}
    tier_avg_prices: Dict[str, float] = {}
    scale_factors: Dict[str, float] = {}

    for rarity in config.RARITIES:
        pool = case_items.get(rarity, [])
        if pool:
            prices = [get_item_market_price(i[0] if isinstance(i, (list, tuple)) else i, rarity) for i in pool]
            avg_p = sum(prices) / len(prices) if prices else BENCHMARK_TIER_PRICES[rarity]
            tier_avg_prices[rarity] = round(avg_p, 2)

            benchmark = BENCHMARK_TIER_PRICES.get(rarity, 5.0)
            if avg_p > benchmark:
                # Inversely scale down drop weight proportionally to price increase
                scale = benchmark / avg_p
            else:
                scale = 1.0

            scale = max(0.0001, scale)
            scale_factors[rarity] = round(scale, 4)
            base_weight = config.RARITY_CHANCES.get(rarity, 0.01)
            raw_weights[rarity] = base_weight * scale
        else:
            tier_avg_prices[rarity] = 0.0
            scale_factors[rarity] = 1.0
            raw_weights[rarity] = 0.0

    total_weight = sum(raw_weights.values())
    if total_weight > 0.0:
        scaled_odds = {r: raw_weights[r] / total_weight for r in config.RARITIES}
    else:
        scaled_odds = dict(config.RARITY_CHANCES)

    return scaled_odds, tier_avg_prices, scale_factors

