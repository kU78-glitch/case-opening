import random
from typing import Optional, List, Dict
import config
from models import Item, GameStats, roll_float, float_to_quality
from cases import CASES

class GameManager:
    def __init__(self):
        self.balance: float = 500.0
        self.inventory: List[Item] = []
        self.prestige_level: int = 0
        self.prestige_threshold: float = 10000.0
        self.stats = GameStats()
        self.auto_sell: Dict[str, bool] = {r: False for r in config.RARITIES}
        self.achievements_unlocked = set()

    def roll_rarity(self) -> str:
        """Weighted probability drop roll based on official CS2 odds."""
        r = random.random()
        cum = 0.0
        for rarity, prob in config.RARITY_CHANCES.items():
            cum += prob
            if r < cum:
                return rarity
        return "Mil-Spec"

    def open_case(self, case_name: str) -> Optional[Item]:
        """
        Deducts Case Price + Key Price ($2.49), generates item with float, quality,
        applies case-based price multiplier, evaluates auto-sell or appends to inventory.
        """
        case_data = CASES.get(case_name)
        if not case_data:
            return None

        total_cost = case_data["price"] + config.KEY_PRICE
        if self.balance < total_cost:
            return None

        self.balance -= total_cost
        self.balance = round(self.balance, 2)
        self.stats.cases_opened += 1
        self.stats.money_spent += total_cost
        self.stats.money_spent = round(self.stats.money_spent, 2)

        rarity = self.roll_rarity()
        pool = case_data["items"][rarity]
        name, color = random.choice(pool)

        is_st = random.random() < config.STATTRAK_CHANCE

        wear_float = roll_float()
        quality = float_to_quality(wear_float)

        # Kasti-põhine hinna kordaja
        case_multiplier = float(case_data.get("multiplier", 1.0))
        base_price = round(config.SELL_PRICES.get(rarity, 5.0) * case_multiplier, 2)

        item = Item(
            name=name,
            rarity=rarity,
            color=color,
            is_st=is_st,
            wear_float=wear_float,
            quality=quality,
            case_name=case_name,
            base_price=base_price
        )

        if is_st:
            self.stats.stattrak_drops += 1
        self.stats.drops_by_rarity[rarity] = self.stats.drops_by_rarity.get(rarity, 0) + 1

        if self.auto_sell.get(rarity, False):
            val = item.get_value(self.prestige_level)
            self.balance += val
            self.balance = round(self.balance, 2)
            self.stats.money_earned_from_selling += val
            self.stats.money_earned_from_selling = round(self.stats.money_earned_from_selling, 2)
        else:
            self.inventory.append(item)

        return item

    def open_multiple_cases(self, case_name: str, count: int) -> List[Item]:
        results = []
        for _ in range(count):
            item = self.open_case(case_name)
            if item is None:
                break
            results.append(item)
        return results

    def sell_item(self, index: int) -> bool:
        if 0 <= index < len(self.inventory):
            item = self.inventory.pop(index)
            val = item.get_value(self.prestige_level)
            self.balance += val
            self.balance = round(self.balance, 2)
            self.stats.money_earned_from_selling += val
            self.stats.money_earned_from_selling = round(self.stats.money_earned_from_selling, 2)
            return True
        return False

    def sell_all_of_rarity(self, rarity: str) -> float:
        to_remove = [i for i, item in enumerate(self.inventory) if item.rarity == rarity]
        total = 0.0
        for i in reversed(to_remove):
            item = self.inventory.pop(i)
            val = item.get_value(self.prestige_level)
            total += val

        total = round(total, 2)
        self.balance += total
        self.balance = round(self.balance, 2)
        self.stats.money_earned_from_selling += total
        self.stats.money_earned_from_selling = round(self.stats.money_earned_from_selling, 2)
        return total

    def reset_progress(self, clear_achievements: bool = True):
        self.balance = 500.0
        self.inventory.clear()
        self.stats = GameStats()
        if clear_achievements:
            self.achievements_unlocked.clear()

    def prestige(self) -> bool:
        if self.balance >= self.prestige_threshold:
            self.prestige_level += 1
            self.reset_progress(clear_achievements=False)
            return True
        return False