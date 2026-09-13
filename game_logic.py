import random
from typing import Optional, List, Dict, Tuple
import config
from models import Item, GameStats, roll_float, float_to_quality
from cases import CASES, get_case
from item_prices import get_item_market_price
from storage import StorageManager

class GameManager:
    def __init__(self):
        self.balance: float = 500.0
        self.inventory: List[Item] = []
        self.prestige_level: int = 0
        self.stats = GameStats()
        self.auto_sell: Dict[str, bool] = {r: False for r in config.RARITIES}
        self.achievements_unlocked = set()

        # Permanent stackable Roguelike perks
        self.perks: Dict[str, float] = {
            "covert_luck": 0.0,
            "gold_luck": 0.0,
            "stattrak_bonus": 0.0,
            "sell_bonus": 0.0,
            "spin_speed": 0.0,
        }
        self.perk_history: List[str] = []

        # Achievements definition: (key, title, condition)
        self.achievements_def = [
            ("first_case", "First Case Opened", lambda s: s.stats.cases_opened >= 1),
            ("first_stattrak", "First StatTrak™ Drop", lambda s: s.stats.stattrak_drops >= 1),
            ("cases_100", "100 Cases Opened", lambda s: s.stats.cases_opened >= 100),
            ("first_covert", "First Covert Drop", lambda s: s.stats.drops_by_rarity.get("Covert", 0) >= 1),
            ("first_gold", "First Rare Special Drop", lambda s: s.stats.drops_by_rarity.get("Rare Special", 0) >= 1),
            ("profit_1k", "Earned $1000 from Selling", lambda s: s.stats.money_earned_from_selling >= 1000),
            ("first_tradeup", "First Trade-Up Completed", lambda s: s.stats.tradeups_done >= 1),
        ]

    def get_item_value(self, item: Item) -> float:
        """Calculates value including prestige level and permanent perk sell bonuses."""
        return item.get_value(self.prestige_level, self.perks.get("sell_bonus", 0.0))

    def roll_rarity(self, custom_odds: Optional[Dict[str, float]] = None) -> str:
        """Weighted probability drop roll based on CS2 odds (or scaled custom odds) plus permanent luck perks."""
        r = random.random()
        covert_luck = self.perks.get("covert_luck", 0.0)
        gold_luck = self.perks.get("gold_luck", 0.0)

        base_odds = custom_odds if custom_odds else config.RARITY_CHANCES
        # Dynamic chances adjusted for perks
        chances = {
            "Mil-Spec": max(0.01, base_odds["Mil-Spec"] - covert_luck - gold_luck),
            "Restricted": base_odds["Restricted"],
            "Classified": base_odds["Classified"],
            "Covert": base_odds["Covert"] + covert_luck,
            "Rare Special": base_odds["Rare Special"] + gold_luck
        }

        cum = 0.0
        for rarity in config.RARITIES:
            cum += chances[rarity]
            if r < cum:
                return rarity
        return "Mil-Spec"

    def open_case(self, case_name: str, skip_auto_sell: bool = False, delay_stats: bool = False) -> Optional[Item]:
        """
        Deducts Total Cost (Case Price + Key $2.49), generates item with float, quality,
        applies case-based price multiplier and individual item market valuation. If delay_stats=True,
        stats and auto-sell are deferred until animation completion via finalize_opened_item.
        """
        case_data = get_case(case_name)
        if not case_data:
            return None

        total_cost = round(float(case_data["price"]) + config.KEY_PRICE, 2)
        if self.balance < total_cost:
            return None

        self.balance -= total_cost
        self.balance = round(self.balance, 2)
        self.stats.money_spent += total_cost
        self.stats.money_spent = round(self.stats.money_spent, 2)

        custom_odds = case_data.get("odds")
        rarity = self.roll_rarity(custom_odds=custom_odds)
        pool = case_data["items"][rarity]
        name, color = random.choice(pool)

        # 10% base StatTrak chance + permanent perk bonus
        st_prob = min(0.75, config.STATTRAK_CHANCE + self.perks.get("stattrak_bonus", 0.0))
        is_st = random.random() < st_prob

        wear_float = roll_float()
        quality = float_to_quality(wear_float)

        # Kasti-põhine hinna kordaja ja individuaalne turuhind
        case_multiplier = float(case_data.get("multiplier", 1.0))
        item_market_price = get_item_market_price(name, rarity)
        base_price = round(item_market_price * case_multiplier, 2)

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

        if delay_stats:
            # Stats recording and inventory addition are delayed until spin animation ends
            return item

        self.stats.cases_opened += 1
        if is_st:
            self.stats.stattrak_drops += 1
        self.stats.drops_by_rarity[rarity] = self.stats.drops_by_rarity.get(rarity, 0) + 1

        if not skip_auto_sell and self.auto_sell.get(rarity, False):
            val = self.get_item_value(item)
            self.balance += val
            self.balance = round(self.balance, 2)
            self.stats.money_earned_from_selling += val
            self.stats.money_earned_from_selling = round(self.stats.money_earned_from_selling, 2)
        else:
            self.inventory.append(item)

        return item

    def finalize_opened_item(self, item: Item) -> Tuple[bool, float]:
        """
        Officially commits drop stats and evaluates auto-sell upon spin completion.
        Returns (auto_sold: bool, value: float).
        """
        self.stats.cases_opened += 1
        if item.is_st:
            self.stats.stattrak_drops += 1
        self.stats.drops_by_rarity[item.rarity] = self.stats.drops_by_rarity.get(item.rarity, 0) + 1

        val = self.get_item_value(item)
        if self.auto_sell.get(item.rarity, False):
            self.balance += val
            self.balance = round(self.balance, 2)
            self.stats.money_earned_from_selling += val
            self.stats.money_earned_from_selling = round(self.stats.money_earned_from_selling, 2)
            return True, val
        else:
            self.inventory.append(item)
            return False, val

    def open_multiple_cases(self, case_name: str, count: int) -> List[Item]:
        results = []
        for _ in range(count):
            item = self.open_case(case_name)
            if item is None:
                break
            results.append(item)
        return results

    def sell_item(self, index: int) -> Optional[float]:
        if 0 <= index < len(self.inventory):
            item = self.inventory.pop(index)
            val = self.get_item_value(item)
            self.balance += val
            self.balance = round(self.balance, 2)
            self.stats.money_earned_from_selling += val
            self.stats.money_earned_from_selling = round(self.stats.money_earned_from_selling, 2)
            return val
        return None

    def sell_all_of_rarity(self, rarity: str) -> Tuple[int, float]:
        to_remove = [i for i, item in enumerate(self.inventory) if item.rarity == rarity]
        total = 0.0
        count = len(to_remove)
        for i in reversed(to_remove):
            item = self.inventory.pop(i)
            val = self.get_item_value(item)
            total += val

        total = round(total, 2)
        self.balance += total
        self.balance = round(self.balance, 2)
        self.stats.money_earned_from_selling += total
        self.stats.money_earned_from_selling = round(self.stats.money_earned_from_selling, 2)
        return count, total

    def perform_tradeup(self, selected_indices: List[int]) -> Tuple[bool, str, Optional[Item]]:
        """
        Executes CS2 trade-up contract with selected 10 items.
        Returns: (success: bool, message: str, result_item: Optional[Item])
        """
        if len(selected_indices) != 10:
            return False, "You must select exactly 10 items.", None

        # Ensure all indices are distinct unique items
        unique_indices = sorted(list(set(selected_indices)), reverse=True)
        if len(unique_indices) != 10:
            return False, "All 10 trade-up items must be distinct unique selections.", None

        # Check bounds
        for idx in unique_indices:
            if idx < 0 or idx >= len(self.inventory):
                return False, "Invalid item selection.", None

        # Retrieve selected item objects
        items = [self.inventory[i] for i in unique_indices]
        rarity = items[0].rarity

        # Check all have same rarity
        if not all(it.rarity == rarity for it in items):
            return False, "All 10 items must have the same rarity.", None

        if rarity in ("Covert", "Rare Special"):
            return False, "Cannot trade up from Covert or Rare Special.", None

        try:
            r_idx = config.RARITIES.index(rarity)
            next_rarity = config.RARITIES[r_idx + 1]
        except (ValueError, IndexError):
            return False, "Cannot trade up from this rarity tier.", None

        # Determine output case weighted by input case origins
        case_weights = {}
        for it in items:
            c_name = it.case_name
            case_weights[c_name] = case_weights.get(c_name, 0) + 1

        eligible_cases = []
        for c_name, w in case_weights.items():
            c_items = CASES.get(c_name, {}).get("items", {})
            if next_rarity in c_items and c_items[next_rarity]:
                eligible_cases.append((c_name, w))

        if not eligible_cases:
            return False, f"No {next_rarity} items exist in source cases.", None

        total_w = sum(w for _, w in eligible_cases)
        r_val = random.uniform(0, total_w)
        cum = 0.0
        chosen_case = eligible_cases[-1][0]
        for c_name, w in eligible_cases:
            cum += w
            if r_val <= cum:
                chosen_case = c_name
                break

        pool = CASES[chosen_case]["items"][next_rarity]
        name, color = random.choice(pool)

        # All 10 StatTrak -> Guaranteed StatTrak outcome
        is_st = all(it.is_st for it in items)
        wear_float = roll_float()
        quality = float_to_quality(wear_float)
        case_multiplier = float(CASES.get(chosen_case, {}).get("multiplier", 1.0))
        item_market_price = get_item_market_price(name, next_rarity)
        base_price = round(item_market_price * case_multiplier, 2)

        new_item = Item(
            name=name,
            rarity=next_rarity,
            color=color,
            is_st=is_st,
            wear_float=wear_float,
            quality=quality,
            case_name=chosen_case,
            base_price=base_price
        )

        # Safe removal by object identity matching to prevent index shift corruption
        item_ids_to_remove = set(id(it) for it in items)
        self.inventory = [it for it in self.inventory if id(it) not in item_ids_to_remove]

        # Add new item
        self.inventory.append(new_item)
        self.stats.tradeups_done += 1
        self.stats.drops_by_rarity[next_rarity] = self.stats.drops_by_rarity.get(next_rarity, 0) + 1
        if is_st:
            self.stats.stattrak_drops += 1

        return True, "Trade-Up successful!", new_item

    def check_achievements(self) -> List[str]:
        """Checks for newly unlocked achievements. Returns list of unlocked titles."""
        unlocked_now = []
        for key, title, cond in self.achievements_def:
            if key not in self.achievements_unlocked and cond(self):
                self.achievements_unlocked.add(key)
                unlocked_now.append(title)
        return unlocked_now

    def reset_progress(self, clear_achievements: bool = False, hard_reset: bool = False):
        self.balance = 500.0
        self.inventory.clear()
        self.stats = GameStats()
        if clear_achievements:
            self.achievements_unlocked.clear()
        if hard_reset:
            self.prestige_level = 0
            self.perks = {
                "covert_luck": 0.0,
                "gold_luck": 0.0,
                "stattrak_bonus": 0.0,
                "sell_bonus": 0.0,
                "spin_speed": 0.0,
            }
            self.perk_history.clear()

    @property
    def prestige_threshold(self) -> float:
        """
        Dynamically scaling prestige requirement:
        - Prestige 0 -> 1: $10,000 (Unlocks 2x multi-case)
        - Prestige 1 -> 2: $25,000 (Unlocks 3x multi-case)
        - Prestige N -> N+1: $25,000 * (2 ** (N - 1)) ($50k, $100k, $200k...)
        """
        if self.prestige_level <= 0:
            return 10000.0
        elif self.prestige_level == 1:
            return 25000.0
        else:
            return float(25000.0 * (2 ** (self.prestige_level - 1)))

    @prestige_threshold.setter
    def prestige_threshold(self, value: float):
        # Allow assignment without error for backwards-compatibility with storage loader
        pass

    def generate_perk_choices(self) -> List[Dict]:
        """Generates 2 distinct random Roguelike perk choices upon Prestige."""
        perk_pool = [
            {
                "key": "covert_luck",
                "value": round(random.uniform(0.005, 0.015), 4),
                "title": "",
                "desc": "Permanently boosts unboxing odds for red Covert tier skins.",
                "icon": "🔴"
            },
            {
                "key": "gold_luck",
                "value": round(random.uniform(0.002, 0.005), 4),
                "title": "",
                "desc": "Permanently increases odds of unboxing Knives and Gloves.",
                "icon": "⭐"
            },
            {
                "key": "stattrak_bonus",
                "value": round(random.uniform(0.020, 0.040), 4),
                "title": "",
                "desc": "Permanently raises the probability of rolling a StatTrak™ skin.",
                "icon": "🟠"
            },
            {
                "key": "sell_bonus",
                "value": round(random.uniform(0.030, 0.060), 4),
                "title": "",
                "desc": "Permanently boosts cash payouts for all sold inventory skins.",
                "icon": "💰"
            },
            {
                "key": "spin_speed",
                "value": round(random.uniform(0.040, 0.070), 4),
                "title": "",
                "desc": "Permanently speeds up roulette carousel and deceleration time.",
                "icon": "⚡"
            }
        ]
        for p in perk_pool:
            if p["key"] == "covert_luck":
                p["title"] = f"+{p['value'] * 100:.1f}% Covert Drop Luck"
            elif p["key"] == "gold_luck":
                p["title"] = f"+{p['value'] * 100:.2f}% Rare Special Luck"
            elif p["key"] == "stattrak_bonus":
                p["title"] = f"+{p['value'] * 100:.1f}% StatTrak™ Chance"
            elif p["key"] == "sell_bonus":
                p["title"] = f"+{p['value'] * 100:.1f}% Global Sell Value"
            elif p["key"] == "spin_speed":
                p["title"] = f"+{int(round(p['value'] * 100))}% Faster Spin Speed"

        return random.sample(perk_pool, 2)

    def apply_perk(self, perk: Dict):
        """Permanently stacks a chosen Roguelike perk."""
        k = perk["key"]
        v = perk["value"]
        self.perks[k] = round(self.perks.get(k, 0.0) + v, 4)
        self.perk_history.append(perk["title"])
        self.save()

    def prestige(self) -> bool:
        if self.balance >= self.prestige_threshold:
            self.prestige_level += 1
            self.reset_progress(clear_achievements=False)
            return True
        return False

    def save(self, filename: str = config.SAVE_FILE):
        try:
            StorageManager.save_game(self, filename)
        except Exception as e:
            print(f"GameManager save error: {e}")

    def load(self, filename: str = config.SAVE_FILE) -> bool:
        return StorageManager.load_game(self, filename)