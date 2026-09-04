import json
import os
import config
from models import Item, GameStats
from game_logic import GameManager

class StorageManager:
    @staticmethod
    def save_game(game: GameManager, filename: str = config.SAVE_FILE):
        data = {
            "balance": round(float(game.balance), 2),
            "prestige_level": int(game.prestige_level),
            "prestige_threshold": float(game.prestige_threshold),
            "achievements_unlocked": list(game.achievements_unlocked),
            "auto_sell": game.auto_sell,
            "inventory": [item.to_dict() for item in game.inventory],
            "stats": {
                "cases_opened": game.stats.cases_opened,
                "money_spent": round(float(game.stats.money_spent), 2),
                "money_earned_from_selling": round(float(game.stats.money_earned_from_selling), 2),
                "tradeups_done": game.stats.tradeups_done,
                "stattrak_drops": game.stats.stattrak_drops,
                "drops_by_rarity": game.stats.drops_by_rarity
            }
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    @staticmethod
    def load_game(game: GameManager, filename: str = config.SAVE_FILE) -> bool:
        if not os.path.exists(filename):
            return False

        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            game.balance = round(float(data.get("balance", 500.0)), 2)
            game.prestige_level = int(data.get("prestige_level", 0))
            game.prestige_threshold = float(data.get("prestige_threshold", 10000.0))
            game.achievements_unlocked = set(data.get("achievements_unlocked", []))
            game.auto_sell = data.get("auto_sell", {r: False for r in config.RARITIES})

            game.inventory = [Item.from_dict(item_dict) for item_dict in data.get("inventory", [])]

            stats_data = data.get("stats", {})
            game.stats = GameStats(
                cases_opened=stats_data.get("cases_opened", 0),
                money_spent=round(float(stats_data.get("money_spent", 0.0)), 2),
                money_earned_from_selling=round(float(stats_data.get("money_earned_from_selling", 0.0)), 2),
                tradeups_done=stats_data.get("tradeups_done", 0),
                stattrak_drops=stats_data.get("stattrak_drops", 0),
                drops_by_rarity=stats_data.get("drops_by_rarity", {r: 0 for r in config.RARITIES})
            )
            return True
        except Exception as e:
            print(f"Error loading save file: {e}")
            return False