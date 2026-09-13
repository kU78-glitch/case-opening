import json
import os
import config
from typing import TYPE_CHECKING
from models import Item, GameStats
from security import save_encrypted_file, load_encrypted_file

if TYPE_CHECKING:
    from game_logic import GameManager

class StorageManager:
    @staticmethod
    def save_game(game: "GameManager", filename: str = config.SAVE_FILE):
        data = {
            "balance": round(float(game.balance), 2),
            "prestige_level": int(game.prestige_level),
            "prestige_threshold": float(game.prestige_threshold),
            "achievements_unlocked": list(game.achievements_unlocked),
            "auto_sell": game.auto_sell,
            "perks": game.perks,
            "perk_history": game.perk_history,
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
        # 1. Save encrypted binary save (.dat)
        success = save_encrypted_file(filename, data)
        if not success:
            print(f"Warning: Failed to save game state to '{filename}'")

        # 2. Always sync save.json for user inspection and testing
        legacy_file = getattr(config, "LEGACY_SAVE_FILE", None)
        if legacy_file:
            try:
                with open(legacy_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Warning: Failed to sync save.json: {e}")

    @staticmethod
    def load_game(game: "GameManager", filename: str = config.SAVE_FILE) -> bool:
        data = None
        is_tampered = False
        legacy_file = getattr(config, "LEGACY_SAVE_FILE", None)

        # 1. Check if user edited save.json more recently than save.dat
        if legacy_file and os.path.exists(legacy_file):
            dat_exists = os.path.exists(filename)
            if not dat_exists or (os.path.getmtime(legacy_file) > os.path.getmtime(filename)):
                try:
                    with open(legacy_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    print(f"[*] Loaded user-edited '{legacy_file}', updating encrypted '{filename}'")
                    save_encrypted_file(filename, data)
                except Exception as e:
                    print(f"Warning: Could not read user save.json: {e}")
                    data = None

        # 2. Otherwise load encrypted binary save (.dat)
        if data is None and os.path.exists(filename):
            data, is_tampered = load_encrypted_file(filename)
            if is_tampered:
                print(f"[SECURITY ALERT] Save file '{filename}' failed tamper/HMAC verification! Resetting to safe defaults.")
                return False

        # 3. Fallback to save.json if dat was not found
        if data is None and legacy_file and os.path.exists(legacy_file):
            try:
                with open(legacy_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                save_encrypted_file(filename, data)
            except Exception as e:
                print(f"Warning: Could not read legacy save file: {e}")

        if data is None:
            return False

        try:
            game.balance = round(float(data.get("balance", 500.0)), 2)
            game.prestige_level = int(data.get("prestige_level", 0))
            game.prestige_threshold = float(data.get("prestige_threshold", 10000.0))
            game.achievements_unlocked = set(data.get("achievements_unlocked", []))
            game.auto_sell = data.get("auto_sell", {r: False for r in config.RARITIES})

            default_perks = {
                "covert_luck": 0.0,
                "gold_luck": 0.0,
                "stattrak_bonus": 0.0,
                "sell_bonus": 0.0,
                "spin_speed": 0.0,
            }
            loaded_perks = data.get("perks", {})
            for k in default_perks:
                game.perks[k] = float(loaded_perks.get(k, default_perks[k]))
            game.perk_history = list(data.get("perk_history", []))

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
            print(f"Error parsing save file: {e}")
            return False