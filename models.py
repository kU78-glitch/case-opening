import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import config

def roll_float() -> float:
    """Generates a random float value bounded between 0.0000 and 1.0000."""
    return round(random.uniform(0.0000, 1.0000), 4)

def float_to_quality(wear_float: float) -> str:
    """
    Wear Conversion:
    0.0000 - 0.0699: Factory New (FN)
    0.0700 - 0.1499: Minimal Wear (MW)
    0.1500 - 0.3799: Field-Tested (FT)
    0.3800 - 0.4499: Well-Worn (WW)
    0.4500 - 1.0000: Battle-Scarred (BS)
    """
    if wear_float < 0.0700:
        return "Factory New"
    elif wear_float < 0.1500:
        return "Minimal Wear"
    elif wear_float < 0.3800:
        return "Field-Tested"
    elif wear_float < 0.4500:
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

    def get_value(self, prestige_level: int = 0) -> float:
        """
        Dynamic Price Calculation:
        Final Price = Base Price * Float Multiplier * StatTrak Multiplier * Prestige Multiplier
        Float Multipliers: FN = 1.5x (or 1.8x if float < 0.02), MW = 1.1x, FT = 0.8x, WW = 0.65x, BS = 0.5x.
        StatTrak™ Multiplier: 2.5x if is_st is True, else 1.0x.
        Prestige Bonus: +10% per prestige level (1.0 + (level * 0.10)).
        """
        # Float multiplier
        if self.wear_float < 0.0200:
            float_mult = 1.8
        elif self.wear_float < 0.0700:
            float_mult = 1.5
        elif self.wear_float < 0.1500:
            float_mult = 1.1
        elif self.wear_float < 0.3800:
            float_mult = 0.8
        elif self.wear_float < 0.4500:
            float_mult = 0.65
        else:
            float_mult = 0.5

        st_mult = 2.5 if self.is_st else 1.0
        prestige_mult = 1.0 + (prestige_level * 0.10)

        final_price = self.base_price * float_mult * st_mult * prestige_mult
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
        wear_float = data.get("wear_float")
        if wear_float is None:
            wear_float = roll_float()

        quality = data.get("quality")
        if not quality:
            quality = float_to_quality(wear_float)

        rarity = data.get("rarity", "Mil-Spec")
        base_price = data.get("base_price", config.SELL_PRICES.get(rarity, 5.0))

        return cls(
            name=data.get("name", "Unknown"),
            rarity=rarity,
            color=data.get("color", "white"),
            is_st=bool(data.get("is_st", False)),
            wear_float=float(wear_float),
            quality=quality,
            case_name=data.get("case_name", ""),
            base_price=float(base_price)
        )

@dataclass
class GameStats:
    cases_opened: int = 0
    money_spent: float = 0.0
    money_earned_from_selling: float = 0.0
    tradeups_done: int = 0
    stattrak_drops: int = 0
    drops_by_rarity: Dict[str, int] = field(default_factory=lambda: {r: 0 for r in config.RARITIES})