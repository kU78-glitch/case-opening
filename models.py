import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import config

def roll_float() -> float:
    """Generates a random float value bounded between 0.0000 and 1.0000."""
    return round(random.uniform(0.0000, 1.0000), 4)

def float_to_quality(wear_float: Optional[float]) -> str:
    """
    Wear Conversion:
    0.0000 - 0.0699: Factory New (FN)
    0.0700 - 0.1499: Minimal Wear (MW)
    0.1500 - 0.3799: Field-Tested (FT)
    0.3800 - 0.4499: Well-Worn (WW)
    0.4500 - 1.0000: Battle-Scarred (BS)
    """
    try:
        val = float(wear_float) if wear_float is not None else roll_float()
    except (TypeError, ValueError):
        val = roll_float()

    if val < 0.0700:
        return "Factory New"
    elif val < 0.1500:
        return "Minimal Wear"
    elif val < 0.3800:
        return "Field-Tested"
    elif val < 0.4500:
        return "Well-Worn"
    else:
        return "Battle-Scarred"

@dataclass
class Item:
    name: str
    rarity: str
    color: str
    is_st: bool
    wear_float: float
    quality: str
    case_name: str
    base_price: float = 5.0

    @property
    def price(self) -> float:
        """Returns the market base price of the item."""
        return self.base_price

    def get(self, key: str, default=None):
        """Allows dictionary-style access for item properties (e.g. item.get('price'))."""
        if key in ("price", "base_price"):
            return self.base_price
        return getattr(self, key, default)

    def get_value(self, prestige_level: int = 0, perk_bonus: float = 0.0) -> float:
        """
        Dynamic Price Calculation:
        Final Price = Base Price * Float Multiplier * StatTrak Multiplier * Prestige Multiplier
        Float Multipliers: FN = 1.5x (or 1.8x if float < 0.02), MW = 1.1x, FT = 0.8x, WW = 0.65x, BS = 0.5x.
        StatTrak™ Multiplier: 2.5x if is_st is True, else 1.0x.
        Prestige Bonus: +10% per prestige level + permanent perk bonus.
        """
        # Float multiplier
        wear = self.wear_float if self.wear_float is not None else 0.5
        if wear < 0.0200:
            float_mult = 1.8
        elif wear < 0.0700:
            float_mult = 1.5
        elif wear < 0.1500:
            float_mult = 1.1
        elif wear < 0.3800:
            float_mult = 0.8
        elif wear < 0.4500:
            float_mult = 0.65
        else:
            float_mult = 0.5

        st_mult = 2.5 if self.is_st else 1.0
        prestige_mult = 1.0 + (prestige_level * 0.10) + perk_bonus

        base = self.base_price if self.base_price is not None else 5.0
        final_price = base * float_mult * st_mult * prestige_mult
        return round(final_price, 2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "rarity": self.rarity,
            "color": self.color,
            "is_st": self.is_st,
            "wear_float": self.wear_float,
            "quality": self.quality,
            "case_name": self.case_name,
            "base_price": self.base_price
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Item':
        raw_float = data.get("wear_float") if isinstance(data, dict) else None
        if raw_float is None and isinstance(data, dict):
            raw_float = data.get("float_value")

        try:
            wear_float = float(raw_float) if raw_float is not None else roll_float()
        except (TypeError, ValueError):
            wear_float = roll_float()

        wear_float = round(wear_float, 4)

        quality = data.get("quality") if isinstance(data, dict) else None
        if not quality:
            quality = float_to_quality(wear_float)

        rarity = data.get("rarity") if isinstance(data, dict) else None
        if not rarity:
            rarity = "Mil-Spec"

        raw_price = data.get("base_price") if isinstance(data, dict) else None
        try:
            base_price = float(raw_price) if raw_price is not None else config.SELL_PRICES.get(rarity, 5.0)
        except (TypeError, ValueError):
            base_price = config.SELL_PRICES.get(rarity, 5.0)

        return cls(
            name=data.get("name", "Unknown") if isinstance(data, dict) else "Unknown",
            rarity=rarity,
            color=data.get("color", "white") if isinstance(data, dict) else "white",
            is_st=bool(data.get("is_st", False)) if isinstance(data, dict) else False,
            wear_float=wear_float,
            quality=quality,
            case_name=data.get("case_name", "") if isinstance(data, dict) else "",
            base_price=round(base_price, 2)
        )

@dataclass
class GameStats:
    cases_opened: int = 0
    money_spent: float = 0.0
    money_earned_from_selling: float = 0.0
    tradeups_done: int = 0
    stattrak_drops: int = 0
    drops_by_rarity: Dict[str, int] = field(default_factory=lambda: {r: 0 for r in config.RARITIES})