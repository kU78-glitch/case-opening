# CONFIG & CONSTANTS

SAVE_FILE = "save.json"
KEY_PRICE = 2.49  # Real CS2 key cost

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