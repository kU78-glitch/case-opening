import os
import sys
import json
import random
import tkinter as tk
from tkinter import messagebox

# Lisame projekti juurkausta otsinguteele
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from cases import CASES
import config
from models import roll_float, float_to_quality

# -------------------------------------------------
# CONSTANTS & CONFIG
# -------------------------------------------------

SAVE_FILE = config.SAVE_FILE
KEY_PRICE = config.KEY_PRICE
RARITY_CHANCES = config.RARITY_CHANCES
SELL_PRICES = config.SELL_PRICES

# -------------------------------------------------
# MAIN GAME CLASS
# -------------------------------------------------

class CaseGame:
    def __init__(self, root):
        self.root = root
        self.root.title("CS2 Case Opening Simulator")
        self.balance = 500.0

        # inventory entry: (name, rarity, color, is_st, quality, case_name, wear_float, base_price)
        self.inventory = []

        self.rarities = ["Mil-Spec", "Restricted", "Classified", "Covert", "Rare Special"]

        self.rarity_colors = {
            "Mil-Spec": "#4b69ff",
            "Restricted": "#8847ff",
            "Classified": "#d32ce6",
            "Covert": "#eb4b4b",
            "Rare Special": "#ffd700"
        }

        # --- Dark mode (algselt hele nagu pildil) ---
        self.dark_mode = False
        self.dark_mode_var = tk.BooleanVar(value=False)

        # theme colors
        self.bg_color = None
        self.panel_color = None
        self.text_color = None
        self.list_bg = None
        self.list_fg = None
        self.button_bg = None
        self.button_fg = None
        self.entry_bg = None
        self.accent_color = None

        # --- Prestige ---
        self.prestige_level = 0
        self.prestige_threshold = 10000.0

        # --- Stats ---
        self.cases_opened = 0
        self.money_spent = 0.0
        self.money_earned_from_selling = 0.0
        self.tradeups_done = 0
        self.stattrak_drops = 0
        self.drops_by_rarity = {r: 0 for r in self.rarities}

        # achievements definition: (key, title, condition)
        self.achievements_def = [
            ("first_case", "First Case Opened", lambda s: s.cases_opened >= 1),
            ("first_stattrak", "First StatTrak\u2122 Drop", lambda s: s.stattrak_drops >= 1),
            ("cases_100", "100 Cases Opened", lambda s: s.cases_opened >= 100),
            ("first_covert", "First Covert Drop", lambda s: s.drops_by_rarity.get("Covert", 0) >= 1),
            ("first_gold", "First Rare Special Drop", lambda s: s.drops_by_rarity.get("Rare Special", 0) >= 1),
            ("profit_1k", "Earned $1000 from selling", lambda s: s.money_earned_from_selling >= 1000),
            ("first_tradeup", "First Trade-Up Completed", lambda s: s.tradeups_done >= 1),
        ]
        self.achievements_unlocked = set()

        # INVENTORY WINDOW & WIDGETS
        self.inventory_window = None
        self.inventory_box = None
        self.sell_button = None
        self.inventory_value_label = None
        self.sell_rarity_var = tk.StringVar(value="Mil-Spec")
        self.selected_index = None
        self.filter_rarity_var = tk.StringVar(value="All")
        self.filter_stattrak_var = tk.BooleanVar(value=False)
        self.sort_mode_var = tk.StringVar(value="Default")
        self.inventory_view_indices = []

        # TRADE-UP WINDOW & STATE
        self.tradeup_window = None
        self.tradeup_listbox = None
        self.tradeup_rarity_var = tk.StringVar(value="Mil-Spec")
        self.tradeup_info_label = None
        self.tradeup_status_label = None
        self.tradeup_candidates = []

        # SPIN STATE
        self.spin_canvas = None
        self.spin_running = False
        self.spin_sequence = []
        self.spin_frame = 0
        self.spin_visible_radius = 4
        self.spin_win_index = 0
        self.spin_result = None

        # STATS WINDOW
        self.stats_window = None
        self.stats_cases_label = None
        self.stats_spent_label = None
        self.stats_earned_label = None
        self.stats_tradeups_label = None
        self.stats_st_label = None
        self.stats_drops_label = None
        self.stats_prestige_label = None
        self.achievements_box = None

        self.prestige_label = None

        # -----------------------------
        # MAIN UI (TÄPSELT NAGU PILDIL)
        # -----------------------------

        top = tk.Frame(root)
        top.pack(pady=10, fill="x")

        mid = tk.Frame(root)
        mid.pack(pady=10)

        bot = tk.Frame(root)
        bot.pack(pady=10)

        # BALANCE LABEL (vasakule)
        self.balance_label = tk.Label(top, text=f"Balance: ${self.balance:.2f}", font=("Arial", 18))
        self.balance_label.pack(side="left", padx=10)

        # Prestige badge
        self.prestige_label = tk.Label(top, text="Prestige: None", font=("Arial", 12))
        self.prestige_label.pack(side="left", padx=10)

        # STATS BUTTON (paremale)
        self.stats_button = tk.Button(
            top,
            text="🏆 Stats",
            font=("Arial", 12),
            command=self.open_stats_window
        )
        self.stats_button.pack(side="right", padx=10)

        # Dark mode toggle (paremal, Stats kõrval)
        self.dark_toggle = tk.Checkbutton(
            top,
            text="Dark",
            variable=self.dark_mode_var,
            font=("Arial", 10),
            command=self.toggle_dark_mode
        )
        self.dark_toggle.pack(side="right")

        # CASE OPENING FRAME
        case_frame = tk.LabelFrame(mid, text="Case Opening", font=("Arial", 12))
        case_frame.pack(padx=10, pady=5)

        # CASE SELECTOR (OptionMenu)
        self.selected_case = tk.StringVar(value=list(CASES.keys())[0])

        self.case_menu = tk.OptionMenu(
            case_frame, self.selected_case, *CASES.keys(),
            command=lambda _: self.update_case_price()
        )
        self.case_menu.config(font=("Arial", 14))
        self.case_menu.pack(pady=5)

        # PRICE LABEL
        self.case_price_label = tk.Label(case_frame, text="", font=("Arial", 14))
        self.case_price_label.pack()
        self.update_case_price()

        # OPEN BUTTON
        self.open_button = tk.Button(
            case_frame,
            text="Open Case",
            font=("Arial", 16),
            command=self.start_case
        )
        self.open_button.pack(pady=5)

        # MULTI-CASE OPEN BUTTON
        self.multi_case_frame = tk.Frame(case_frame)
        self.multi_case_frame.pack(pady=5)

        tk.Label(self.multi_case_frame, text="Multi-Case Count:", font=("Arial", 12)).pack(side="left")
        self.multi_case_count = tk.IntVar(value=5)
        tk.Entry(
            self.multi_case_frame,
            textvariable=self.multi_case_count,
            width=5,
            font=("Arial", 12)
        ).pack(side="left", padx=5)
        self.multi_open_button = tk.Button(
            self.multi_case_frame,
            text="Open Multiple Cases",
            font=("Arial", 12),
            command=self.start_multi_case
        )
        self.multi_open_button.pack(side="left", padx=5)

        # SPIN RESULT LABEL (tekst)
        self.rolling_label = tk.Label(
            case_frame,
            text="",
            font=("Arial", 20, "bold"),
            width=45,
            height=2
        )
        self.rolling_label.pack(pady=10)

        # ROULETTE SPIN CANVAS (560x80)
        self.spin_canvas = tk.Canvas(
            case_frame,
            width=560,
            height=80,
            bg="#111111",
            highlightthickness=0
        )
        self.spin_canvas.pack(pady=5)

        # AUTO-SELL OPTIONS
        self.auto_sell_frame = tk.LabelFrame(bot, text="Auto-Sell Options", font=("Arial", 12))
        self.auto_sell_frame.pack(pady=5)

        self.auto_sell_vars = {}
        for rarity in self.rarities:
            var = tk.BooleanVar(value=False)
            chk = tk.Checkbutton(self.auto_sell_frame, text=rarity, variable=var, font=("Arial", 12))
            chk.pack(side="left", padx=5)
            self.auto_sell_vars[rarity] = var

        # INVENTORY OPEN BUTTON
        self.inventory_button = tk.Button(
            bot,
            text="Open Inventory",
            font=("Arial", 12),
            command=self.open_inventory_window
        )
        self.inventory_button.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.set_theme_colors()
        self.apply_theme()
        self.update_prestige_label()

        self.load_game()

    # -------------------------------------------------
    # SAVE / LOAD
    # -------------------------------------------------

    def save_game(self):
        try:
            data = {
                "balance": round(float(self.balance), 2),
                "inventory": [
                    {
                        "name": item[0],
                        "rarity": item[1],
                        "color": item[2],
                        "is_st": bool(item[3]),
                        "quality": item[4],
                        "case_name": item[5],
                        "wear_float": round(float(item[6]), 4),
                        "base_price": float(item[7])
                    }
                    for item in self.inventory
                ],
                "auto_sell": {
                    rarity: var.get() for rarity, var in self.auto_sell_vars.items()
                },
                "stats": {
                    "cases_opened": self.cases_opened,
                    "money_spent": round(float(self.money_spent), 2),
                    "money_earned_from_selling": round(float(self.money_earned_from_selling), 2),
                    "tradeups_done": self.tradeups_done,
                    "stattrak_drops": self.stattrak_drops,
                    "drops_by_rarity": self.drops_by_rarity,
                },
                "achievements_unlocked": list(self.achievements_unlocked),
                "prestige_level": self.prestige_level,
            }
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving game:", e)

    def load_game(self):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            return
        except Exception as e:
            print("Error loading game:", e)
            return

        self.balance = float(data.get("balance", self.balance))
        self.update_balance()

        self.inventory.clear()
        for item in data.get("inventory", []):
            name = item.get("name", "Unknown")
            rarity = item.get("rarity", "Mil-Spec")
            color = item.get("color", "white")
            is_st = bool(item.get("is_st", False))
            wear_float = float(item.get("wear_float", roll_float()))
            quality = item.get("quality", float_to_quality(wear_float))
            case_name = item.get("case_name", list(CASES.keys())[0])
            case_multiplier = CASES.get(case_name, {}).get("multiplier", 1.0)
            default_price = SELL_PRICES.get(rarity, 5.0) * case_multiplier
            base_price = float(item.get("base_price", default_price))
            self.inventory.append((name, rarity, color, is_st, quality, case_name, wear_float, base_price))

        auto_sell_data = data.get("auto_sell", {})
        for rarity, var in self.auto_sell_vars.items():
            var.set(bool(auto_sell_data.get(rarity, False)))

        stats = data.get("stats", {})
        self.cases_opened = int(stats.get("cases_opened", 0))
        self.money_spent = float(stats.get("money_spent", 0.0))
        self.money_earned_from_selling = float(stats.get("money_earned_from_selling", 0.0))
        self.tradeups_done = int(stats.get("tradeups_done", 0))
        self.stattrak_drops = int(stats.get("stattrak_drops", 0))
        drops = stats.get("drops_by_rarity", {})
        for r in self.rarities:
            self.drops_by_rarity[r] = int(drops.get(r, 0))

        ach_unl = data.get("achievements_unlocked", [])
        valid_keys = {key for key, _, _ in self.achievements_def}
        self.achievements_unlocked = {k for k in ach_unl if k in valid_keys}

        self.prestige_level = int(data.get("prestige_level", 0))
        self.update_prestige_label()

        if self.inventory_box is not None:
            self.refresh_inventory_view()

        self.update_inventory_value()
        self.update_stats_window()
        self.apply_theme()

    def on_close(self):
        self.save_game()
        self.root.destroy()

    # -------------------------------------------------
    # INVENTORY WINDOW
    # -------------------------------------------------

    def open_inventory_window(self):
        if self.inventory_window is not None and tk.Toplevel.winfo_exists(self.inventory_window):
            self.inventory_window.lift()
            return

        self.inventory_window = tk.Toplevel(self.root)
        self.inventory_window.title("Inventory")
        self.inventory_window.protocol("WM_DELETE_WINDOW", self.close_inventory_window)

        self.inventory_box = tk.Listbox(self.inventory_window, width=76, height=15,
                                        font=("Arial", 12), selectmode="browse")
        self.inventory_box.pack(padx=10, pady=10)
        self.inventory_box.bind("<<ListboxSelect>>", self.on_select)

        filter_frame = tk.Frame(self.inventory_window)
        filter_frame.pack(pady=2)

        tk.Label(filter_frame, text="Filter rarity:", font=("Arial", 10)).pack(side="left", padx=3)
        rarity_options = ["All"] + self.rarities
        rarity_menu = tk.OptionMenu(
            filter_frame,
            self.filter_rarity_var,
            *rarity_options,
            command=lambda _: self.refresh_inventory_view()
        )
        rarity_menu.config(font=("Arial", 10))
        rarity_menu.pack(side="left", padx=3)

        st_chk = tk.Checkbutton(
            filter_frame,
            text="Only StatTrak\u2122",
            variable=self.filter_stattrak_var,
            font=("Arial", 10),
            command=self.refresh_inventory_view
        )
        st_chk.pack(side="left", padx=8)

        sort_frame = tk.Frame(self.inventory_window)
        sort_frame.pack(pady=2)

        tk.Label(sort_frame, text="Sort by:", font=("Arial", 10)).pack(side="left", padx=3)
        sort_options = [
            "Default",
            "Rarity \u2191",
            "Rarity \u2193",
            "Name A\u2192Z",
            "Name Z\u2192A",
            "Quality \u2191",
            "Quality \u2193",
        ]
        sort_menu = tk.OptionMenu(
            sort_frame,
            self.sort_mode_var,
            *sort_options,
            command=lambda _: self.refresh_inventory_view()
        )
        sort_menu.config(font=("Arial", 10))
        sort_menu.pack(side="left", padx=3)

        self.sell_button = tk.Button(self.inventory_window, text="Sell Selected Item",
                                     font=("Arial", 14), state="disabled",
                                     command=self.sell_item)
        self.sell_button.pack(pady=5)

        self.inventory_value_label = tk.Label(self.inventory_window, text="Inventory Value: $0.00",
                                              font=("Arial", 14))
        self.inventory_value_label.pack(pady=5)

        sell_all_frame = tk.Frame(self.inventory_window)
        sell_all_frame.pack(pady=5)

        tk.Label(sell_all_frame, text="Sell all of rarity:", font=("Arial", 12)).pack(side="left", padx=5)
        sell_all_menu = tk.OptionMenu(sell_all_frame, self.sell_rarity_var, *self.rarities)
        sell_all_menu.config(font=("Arial", 12))
        sell_all_menu.pack(side="left", padx=5)

        sell_all_button = tk.Button(
            sell_all_frame,
            text="Sell All",
            font=("Arial", 12),
            command=self.sell_all_rarity
        )
        sell_all_button.pack(side="left", padx=5)

        tradeup_btn = tk.Button(
            self.inventory_window,
            text="Open Trade-Up Contract",
            font=("Arial", 12),
            command=self.open_tradeup_window
        )
        tradeup_btn.pack(pady=10)

        self.refresh_inventory_view()
        self.update_inventory_value()
        self.apply_theme()

    def close_inventory_window(self):
        if self.inventory_window is not None:
            self.inventory_window.destroy()
        self.inventory_window = None
        self.inventory_box = None
        self.sell_button = None
        self.inventory_value_label = None
        self.selected_index = None
        self.inventory_view_indices = []

    def refresh_inventory_view(self):
        if self.inventory_box is None:
            return

        rarity_filter = self.filter_rarity_var.get()
        only_st = self.filter_stattrak_var.get()
        sort_mode = self.sort_mode_var.get()

        items = []
        for inv_idx, item in enumerate(self.inventory):
            name, rarity, color, is_st, quality, case_name, wear_float, base_price = item
            if rarity_filter != "All" and rarity != rarity_filter:
                continue
            if only_st and not is_st:
                continue
            items.append((inv_idx, name, rarity, color, is_st, quality, case_name, wear_float, base_price))

        rarity_order = {r: i for i, r in enumerate(self.rarities)}
        quality_order = {
            "Factory New": 0,
            "Minimal Wear": 1,
            "Field-Tested": 2,
            "Well-Worn": 3,
            "Battle-Scarred": 4
        }

        reverse = False

        if sort_mode == "Default":
            key_func = lambda it: it[0]
        elif sort_mode == "Rarity \u2191":
            key_func = lambda it: (rarity_order.get(it[2], 999), it[1].lower())
        elif sort_mode == "Rarity \u2193":
            key_func = lambda it: (rarity_order.get(it[2], 999), it[1].lower())
            reverse = True
        elif sort_mode == "Name A\u2192Z":
            key_func = lambda it: it[1].lower()
        elif sort_mode == "Name Z\u2192A":
            key_func = lambda it: it[1].lower()
            reverse = True
        elif sort_mode == "Quality \u2191":
            key_func = lambda it: (quality_order.get(it[5], 999), it[1].lower())
        elif sort_mode == "Quality \u2193":
            key_func = lambda it: (quality_order.get(it[5], 999), it[1].lower())
            reverse = True
        else:
            key_func = lambda it: it[0]

        items.sort(key=key_func, reverse=reverse)

        self.inventory_box.delete(0, tk.END)
        self.inventory_view_indices = []

        for inv_idx, name, rarity, color, is_st, quality, case_name, wear_float, base_price in items:
            val = self.get_item_value(rarity, is_st, wear_float, base_price)
            st_prefix = "StatTrak\u2122 " if is_st else ""
            display_str = f"{st_prefix}{name} [{quality} ({wear_float:.4f})] - ${val:.2f} ({rarity})"

            row = self.inventory_box.size()
            self.inventory_box.insert(row, display_str)
            fg_color = self.rarity_colors.get(rarity, "black")
            self.inventory_box.itemconfig(row, fg=fg_color)
            self.inventory_view_indices.append(inv_idx)

        self.selected_index = None
        if self.sell_button is not None:
            self.sell_button.config(state="disabled")

    # -------------------------------------------------
    # STATS & ACHIEVEMENTS WINDOW
    # -------------------------------------------------

    def open_stats_window(self):
        if self.stats_window is not None and tk.Toplevel.winfo_exists(self.stats_window):
            self.stats_window.lift()
            self.update_stats_window()
            self.apply_theme()
            return

        self.stats_window = tk.Toplevel(self.root)
        self.stats_window.title("Stats & Achievements")
        self.stats_window.protocol("WM_DELETE_WINDOW", self.close_stats_window)

        stats_frame = tk.LabelFrame(self.stats_window, text="Stats", font=("Arial", 12))
        stats_frame.pack(padx=10, pady=8, fill="x")

        self.stats_cases_label = tk.Label(stats_frame, text="", font=("Arial", 11), anchor="w")
        self.stats_cases_label.pack(fill="x")
        self.stats_spent_label = tk.Label(stats_frame, text="", font=("Arial", 11), anchor="w")
        self.stats_spent_label.pack(fill="x")
        self.stats_earned_label = tk.Label(stats_frame, text="", font=("Arial", 11), anchor="w")
        self.stats_earned_label.pack(fill="x")
        self.stats_tradeups_label = tk.Label(stats_frame, text="", font=("Arial", 11), anchor="w")
        self.stats_tradeups_label.pack(fill="x")
        self.stats_prestige_label = tk.Label(stats_frame, text="", font=("Arial", 11), anchor="w")
        self.stats_prestige_label.pack(fill="x")
        self.stats_st_label = tk.Label(stats_frame, text="", font=("Arial", 11), anchor="w")
        self.stats_st_label.pack(fill="x")
        self.stats_drops_label = tk.Label(stats_frame, text="", font=("Arial", 11), anchor="w", justify="left")
        self.stats_drops_label.pack(fill="x", pady=(4, 0))

        ach_frame = tk.LabelFrame(self.stats_window, text="Achievements", font=("Arial", 12))
        ach_frame.pack(padx=10, pady=8, fill="both", expand=True)

        self.achievements_box = tk.Listbox(ach_frame, width=40, height=8, font=("Arial", 11))
        self.achievements_box.pack(padx=5, pady=5, fill="both", expand=True)

        btn_frame = tk.Frame(self.stats_window)
        btn_frame.pack(pady=(0, 10))

        reset_btn = tk.Button(
            btn_frame,
            text="Reset Progress",
            font=("Arial", 11),
            command=self.reset_progress
        )
        reset_btn.pack(side="left", padx=5)

        prestige_btn = tk.Button(
            btn_frame,
            text="Prestige",
            font=("Arial", 11),
            command=self.prestige
        )
        prestige_btn.pack(side="left", padx=5)

        self.update_stats_window()
        self.apply_theme()

    def close_stats_window(self):
        if self.stats_window is not None:
            self.stats_window.destroy()
        self.stats_window = None
        self.stats_cases_label = None
        self.stats_spent_label = None
        self.stats_earned_label = None
        self.stats_tradeups_label = None
        self.stats_st_label = None
        self.stats_drops_label = None
        self.stats_prestige_label = None
        self.achievements_box = None

    def update_stats_window(self):
        if self.stats_window is None:
            return

        if self.stats_cases_label is not None:
            self.stats_cases_label.config(text=f"Cases opened: {self.cases_opened}")
        if self.stats_spent_label is not None:
            self.stats_spent_label.config(text=f"Money spent: ${self.money_spent:.2f}")
        if self.stats_earned_label is not None:
            self.stats_earned_label.config(text=f"Money earned from selling: ${self.money_earned_from_selling:.2f}")
        if self.stats_tradeups_label is not None:
            self.stats_tradeups_label.config(text=f"Trade-Ups completed: {self.tradeups_done}")
        if self.stats_prestige_label is not None:
            bonus = int(self.prestige_level * 10)
            self.stats_prestige_label.config(
                text=f"Prestige level: {self.prestige_level} (Sell bonus: +{bonus}% per item)"
            )
        if self.stats_st_label is not None:
            self.stats_st_label.config(text=f"StatTrak drops: {self.stattrak_drops}")
        if self.stats_drops_label is not None:
            drops_text = "Drops by rarity: " + ", ".join(
                f"{r}: {self.drops_by_rarity.get(r, 0)}" for r in self.rarities
            )
            self.stats_drops_label.config(text=drops_text)

        if self.achievements_box is not None:
            self.achievements_box.delete(0, tk.END)
            for key, title, cond in self.achievements_def:
                unlocked = cond(self)
                prefix = "✅ " if unlocked else "⬜ "
                self.achievements_box.insert(tk.END, prefix + title)

    # -------------------------------------------------
    # TRADE-UP WINDOW
    # -------------------------------------------------

    def open_tradeup_window(self):
        if self.tradeup_window is not None and tk.Toplevel.winfo_exists(self.tradeup_window):
            self.tradeup_window.lift()
            self.refresh_tradeup_candidates()
            self.apply_theme()
            return

        self.tradeup_window = tk.Toplevel(self.root)
        self.tradeup_window.title("Trade-Up Contract")
        self.tradeup_window.protocol("WM_DELETE_WINDOW", self.close_tradeup_window)

        rarity_frame = tk.Frame(self.tradeup_window)
        rarity_frame.pack(pady=5)

        tk.Label(rarity_frame, text="Trade up from rarity:", font=("Arial", 12)).pack(side="left", padx=5)
        rarity_menu = tk.OptionMenu(rarity_frame, self.tradeup_rarity_var, *self.rarities[:-1],
                                    command=lambda _: self.refresh_tradeup_candidates())
        rarity_menu.config(font=("Arial", 12))
        rarity_menu.pack(side="left", padx=5)

        self.tradeup_info_label = tk.Label(self.tradeup_window, text="", font=("Arial", 11))
        self.tradeup_info_label.pack(pady=5)

        self.tradeup_listbox = tk.Listbox(self.tradeup_window, width=70, height=10,
                                          font=("Arial", 11), selectmode="multiple")
        self.tradeup_listbox.pack(padx=10, pady=5)

        btn_frame = tk.Frame(self.tradeup_window)
        btn_frame.pack(pady=5)

        autofill_btn = tk.Button(btn_frame, text="Auto-fill 10", font=("Arial", 11),
                                 command=self.tradeup_autofill)
        autofill_btn.pack(side="left", padx=5)

        confirm_btn = tk.Button(btn_frame, text="Confirm Trade-Up", font=("Arial", 11),
                                command=self.perform_tradeup)
        confirm_btn.pack(side="left", padx=5)

        self.tradeup_status_label = tk.Label(self.tradeup_window, text="", font=("Arial", 11))
        self.tradeup_status_label.pack(pady=5)

        self.refresh_tradeup_candidates()
        self.apply_theme()

    def close_tradeup_window(self):
        if self.tradeup_window is not None:
            self.tradeup_window.destroy()
        self.tradeup_window = None
        self.tradeup_listbox = None
        self.tradeup_info_label = None
        self.tradeup_status_label = None
        self.tradeup_candidates = []

    def refresh_tradeup_candidates(self):
        if self.tradeup_listbox is None:
            return

        rarity = self.tradeup_rarity_var.get()
        self.tradeup_listbox.delete(0, tk.END)
        self.tradeup_candidates = []

        for idx, item in enumerate(self.inventory):
            name, r, color, is_st, quality, case_name, wear_float, base_price = item
            if r == rarity:
                st_prefix = "StatTrak\u2122 " if is_st else ""
                display = f"{st_prefix}{name} [{quality} ({wear_float:.4f})] ({case_name})"
                self.tradeup_listbox.insert(tk.END, display)
                self.tradeup_candidates.append(idx)

        count = len(self.tradeup_candidates)
        if self.tradeup_info_label is not None:
            self.tradeup_info_label.config(
                text=f"You have {count} items of rarity {rarity}. "
                     f"You need 10 to perform a trade-up."
            )

        if self.tradeup_status_label is not None:
            self.tradeup_status_label.config(text="")

    def tradeup_autofill(self):
        if self.tradeup_listbox is None:
            return
        self.tradeup_listbox.selection_clear(0, tk.END)
        max_fill = min(10, self.tradeup_listbox.size())
        for i in range(max_fill):
            self.tradeup_listbox.selection_set(i)

    def perform_tradeup(self):
        rarity = self.tradeup_rarity_var.get()

        if rarity in ("Covert", "Rare Special"):
            if self.tradeup_status_label is not None:
                self.tradeup_status_label.config(text="Cannot trade up from highest rarity.", fg="red")
            return

        if self.tradeup_listbox is None:
            return

        selected = list(self.tradeup_listbox.curselection())
        if len(selected) != 10:
            if self.tradeup_status_label is not None:
                self.tradeup_status_label.config(text="You must select exactly 10 items.", fg="red")
            return

        inv_indices = [self.tradeup_candidates[i] for i in selected]
        items = [self.inventory[i] for i in inv_indices]

        all_st = all(item[3] for item in items)

        try:
            idx = self.rarities.index(rarity)
            next_rarity = self.rarities[idx + 1]
        except (ValueError, IndexError):
            if self.tradeup_status_label is not None:
                self.tradeup_status_label.config(text="Invalid rarity for trade-up.", fg="red")
            return

        weights = {}
        for item in items:
            case_name = item[5]
            weights[case_name] = weights.get(case_name, 0) + 1

        cases_with_next = []
        for case_name, w in weights.items():
            case_items = CASES.get(case_name, {}).get("items", {})
            if next_rarity in case_items and case_items[next_rarity]:
                cases_with_next.append((case_name, w))

        if not cases_with_next:
            if self.tradeup_status_label is not None:
                self.tradeup_status_label.config(
                    text=f"No {next_rarity} items available in the source cases.", fg="red"
                )
            return

        total_w = sum(w for _, w in cases_with_next)
        r_val = random.uniform(0, total_w)
        cum = 0
        chosen_case = cases_with_next[-1][0]
        for case_name, w in cases_with_next:
            cum += w
            if r_val <= cum:
                chosen_case = case_name
                break

        pool = CASES[chosen_case]["items"][next_rarity]
        name, color = random.choice(pool)

        wear_float = roll_float()
        quality = float_to_quality(wear_float)
        case_multiplier = CASES.get(chosen_case, {}).get("multiplier", 1.0)
        base_price = SELL_PRICES.get(next_rarity, 5.0) * case_multiplier
        is_st = all_st

        st_prefix = "StatTrak\u2122 " if is_st else ""
        display = f"{st_prefix}{name} [{quality} ({wear_float:.4f})]"

        if is_st:
            self.stattrak_drops += 1

        for i in sorted(inv_indices, reverse=True):
            del self.inventory[i]

        self.inventory.append((name, next_rarity, color, is_st, quality, chosen_case, wear_float, base_price))
        self.tradeups_done += 1
        self.drops_by_rarity[next_rarity] = self.drops_by_rarity.get(next_rarity, 0) + 1

        if self.inventory_box is not None:
            self.refresh_inventory_view()

        self.update_inventory_value()

        if self.tradeup_status_label is not None:
            self.tradeup_status_label.config(
                text=f"Trade-Up success! You got {display} ({next_rarity})",
                fg="green"
            )

        self.refresh_tradeup_candidates()
        self.update_stats_window()
        self.check_achievements()
        self.save_game()

    # -------------------------------------------------
    # CASE PRICE / BALANCE
    # -------------------------------------------------

    def update_case_price(self):
        case_name = self.selected_case.get()
        case_data = CASES[case_name]
        case_price = case_data["price"]
        multiplier = case_data.get("multiplier", 1.0)
        total_cost = case_price + KEY_PRICE
        
        mult_str = f"  |  Kordaja: {multiplier:.1f}x" if multiplier != 1.0 else ""
        self.case_price_label.config(
            text=f"Case Price: ${case_price:.2f}  |  Key: ${KEY_PRICE:.2f}  |  Total: ${total_cost:.2f}{mult_str}"
        )

    def update_balance(self):
        if self.balance < 0:
            self.balance = 0.0
        self.balance = round(self.balance, 2)
        self.balance_label.config(text=f"Balance: ${self.balance:.2f}")

    # -------------------------------------------------
    # CASE OPENING + SPIN
    # -------------------------------------------------

    def start_case(self):
        if self.spin_running:
            return
        self.open_single_case(use_animation=True)

    def start_multi_case(self):
        if self.spin_running:
            self.set_label("Wait for spin to finish!", "red")
            return

        count = self.multi_case_count.get()
        if count <= 0:
            self.set_label("Enter a valid number of cases!", "red")
            return

        opened = 0
        for _ in range(count):
            res = self.open_single_case(use_animation=False)
            if res is None:
                break
            opened += 1

        if opened > 0:
            self.set_label(f"Opened {opened} cases.", "white" if self.dark_mode else "black")

    def open_single_case(self, use_animation=True):
        case_name = self.selected_case.get()
        case_data = CASES[case_name]
        case_price = case_data["price"]
        total_cost = case_price + KEY_PRICE

        if self.balance < total_cost:
            self.set_label("Not enough money!", "red")
            return None

        self.cases_opened += 1
        self.money_spent += total_cost
        self.balance -= total_cost
        self.update_balance()

        items = case_data["items"]
        rarity = self.roll_rarity()
        name, color = random.choice(items[rarity])

        # 10% StatTrak chance
        is_st = random.random() < config.STATTRAK_CHANCE

        wear_float = roll_float()
        quality = float_to_quality(wear_float)
        
        # Kasti-põhine hinna kordaja
        case_multiplier = float(case_data.get("multiplier", 1.0))
        base_price = round(SELL_PRICES.get(rarity, 5.0) * case_multiplier, 2)

        result = {
            "case_name": case_name,
            "rarity": rarity,
            "name": name,
            "color": color,
            "is_st": is_st,
            "quality": quality,
            "wear_float": wear_float,
            "base_price": base_price
        }

        if use_animation:
            self.start_spin_animation(result)
        else:
            self.finalize_result(result)

        self.update_stats_window()
        self.check_achievements()
        self.save_game()
        return result

    def start_spin_animation(self, result):
        if self.spin_running:
            return

        self.spin_running = True
        self.open_button.config(state="disabled")
        self.multi_open_button.config(state="disabled")
        self.spin_canvas.delete("all")
        self.set_label("Spinning...", "white" if self.dark_mode else "black")

        case_name = result["case_name"]
        case_data = CASES[case_name]
        items = case_data["items"]
        case_multiplier = float(case_data.get("multiplier", 1.0))

        self.spin_sequence = []
        fake_count = 40

        for _ in range(fake_count):
            rf = random.choice(list(items.keys()))
            n_fake, c_fake = random.choice(items[rf])
            f_fake = roll_float()
            self.spin_sequence.append({
                "case_name": case_name,
                "rarity": rf,
                "name": n_fake,
                "color": c_fake,
                "is_st": False,
                "quality": float_to_quality(f_fake),
                "wear_float": f_fake,
                "base_price": round(SELL_PRICES.get(rf, 5.0) * case_multiplier, 2)
            })

        win_index = fake_count - self.spin_visible_radius - 1
        if win_index < 0:
            win_index = max(0, fake_count - 1)

        self.spin_win_index = win_index
        self.spin_result = result
        self.spin_sequence[win_index] = result

        self.spin_frame = 0
        self._spin_step()

    def _spin_step(self):
        seq = self.spin_sequence
        frame = self.spin_frame

        if frame > self.spin_win_index:
            self.spin_running = False

            def enable_buttons_and_finalize():
                self.open_button.config(state="normal")
                self.multi_open_button.config(state="normal")
                if self.spin_result is not None:
                    self.finalize_result(self.spin_result)

            self.root.after(600, enable_buttons_and_finalize)
            return

        center_index = frame
        self.spin_canvas.delete("all")

        visible_radius = self.spin_visible_radius
        item_width = 80
        center_x = 280
        center_y = 40

        for offset in range(-visible_radius, visible_radius + 1):
            idx = center_index + offset
            if 0 <= idx < len(seq):
                item = seq[idx]
                x = center_x + offset * item_width
                y = center_y

                bg = self.get_rarity_color(item["rarity"])
                outline = "#f1c40f" if offset == 0 else "#333333"
                width = 3 if offset == 0 else 1

                self.spin_canvas.create_rectangle(
                    x - 35, y - 25, x + 35, y + 25,
                    fill=bg, outline=outline, width=width
                )

                st_pref = "★ " if item.get("is_st") else ""
                display = f"{st_pref}{item['name']}"
                self.spin_canvas.create_text(
                    x, y, text=display, fill="white",
                    font=("Arial", 9), width=70
                )

        if 0 <= center_index < len(seq):
            center_item = seq[center_index]
            display_center = ("StatTrak\u2122 " if center_item.get("is_st") else "") + center_item["name"]
            self.set_label(display_center, self.get_rarity_color(center_item["rarity"]))

        t = frame / max(1, self.spin_win_index)
        delay = int(30 + 220 * (t ** 2))

        self.spin_frame += 1
        self.root.after(delay, self._spin_step)

    def finalize_result(self, result):
        rarity = result["rarity"]
        name = result["name"]
        color = result["color"]
        is_st = result["is_st"]
        quality = result["quality"]
        wear_float = result["wear_float"]
        case_name = result["case_name"]
        base_price = result["base_price"]

        if is_st:
            self.stattrak_drops += 1

        display = ("StatTrak\u2122 " if is_st else "") + name
        display_with_quality = f"{display} [{quality} ({wear_float:.4f})]"

        self.drops_by_rarity[rarity] = self.drops_by_rarity.get(rarity, 0) + 1

        if self.auto_sell_vars.get(rarity, tk.BooleanVar()).get():
            value = self.get_item_value(rarity, is_st, wear_float, base_price)
            self.balance += value
            self.money_earned_from_selling += value
            self.update_balance()
            self.set_label(f"Auto-sold {display_with_quality} for ${value:.2f}", "green")
        else:
            self.inventory.append((name, rarity, color, is_st, quality, case_name, wear_float, base_price))
            if self.inventory_box is not None:
                self.refresh_inventory_view()
            self.set_label(display_with_quality, self.get_rarity_color(rarity))

        self.update_inventory_value()
        self.update_stats_window()
        self.check_achievements()
        self.save_game()

    def roll_rarity(self):
        r = random.random()
        cum = 0.0
        for rarity, prob in RARITY_CHANCES.items():
            cum += prob
            if r < cum:
                return rarity
        return "Mil-Spec"

    def get_rarity_color(self, rarity):
        return self.rarity_colors.get(rarity, "#555555")

    def get_item_value(self, rarity, is_st, wear_float=0.15, base_price=None) -> float:
        """
        Arvutab müügiväärtuse: Base Price * Float Multiplier * StatTrak Multiplier * Prestige Multiplier.
        """
        if base_price is None:
            base = SELL_PRICES.get(rarity, 5.0)
        else:
            base = base_price

        if wear_float < 0.0200:
            float_mult = 1.8
        elif wear_float < 0.0700:
            float_mult = 1.5
        elif wear_float < 0.1500:
            float_mult = 1.1
        elif wear_float < 0.3800:
            float_mult = 0.8
        elif wear_float < 0.4500:
            float_mult = 0.65
        else:
            float_mult = 0.5

        st_mult = 2.5 if is_st else 1.0
        prestige_mult = 1.0 + 0.10 * self.prestige_level
        return round(base * float_mult * st_mult * prestige_mult, 2)

    # -------------------------------------------------
    # SELLING
    # -------------------------------------------------

    def on_select(self, event):
        if self.inventory_box is None:
            return
        sel = self.inventory_box.curselection()
        if sel:
            row = sel[0]
            if 0 <= row < len(self.inventory_view_indices):
                self.selected_index = self.inventory_view_indices[row]
                if self.sell_button is not None:
                    self.sell_button.config(state="normal")
        else:
            self.selected_index = None
            if self.sell_button is not None:
                self.sell_button.config(state="disabled")

    def sell_item(self):
        if self.selected_index is None:
            return
        if self.selected_index < 0 or self.selected_index >= len(self.inventory):
            return

        item = self.inventory[self.selected_index]
        name, rarity, color, is_st, quality, case_name, wear_float, base_price = item
        value = self.get_item_value(rarity, is_st, wear_float, base_price)

        self.balance += value
        self.money_earned_from_selling += value
        self.update_balance()

        del self.inventory[self.selected_index]

        if self.inventory_box is not None:
            self.refresh_inventory_view()

        self.update_inventory_value()
        self.selected_index = None
        if self.sell_button is not None:
            self.sell_button.config(state="disabled")

        self.update_stats_window()
        self.check_achievements()
        self.save_game()

    def sell_all_rarity(self):
        rarity_to_sell = self.sell_rarity_var.get()
        total = 0.0
        indexes_to_remove = []

        for i, item in enumerate(self.inventory):
            name, rarity, color, is_st, quality, case_name, wear_float, base_price = item
            if rarity == rarity_to_sell:
                total += self.get_item_value(rarity, is_st, wear_float, base_price)
                indexes_to_remove.append(i)

        if not indexes_to_remove:
            self.rolling_label.config(text=f"No {rarity_to_sell} items to sell!", fg="red")
            return

        self.balance += total
        self.money_earned_from_selling += total
        self.update_balance()

        for i in reversed(indexes_to_remove):
            del self.inventory[i]

        if self.inventory_box is not None:
            self.refresh_inventory_view()

        self.update_inventory_value()
        self.rolling_label.config(text=f"Sold all {rarity_to_sell} items for ${total:.2f}", fg="green")

        self.update_stats_window()
        self.check_achievements()
        self.save_game()

    # -------------------------------------------------
    # RESET & PRESTIGE
    # -------------------------------------------------

    def _soft_reset(self, clear_achievements: bool):
        self.balance = 500.0
        self.update_balance()

        self.inventory.clear()
        if self.inventory_box is not None:
            self.refresh_inventory_view()
        self.update_inventory_value()

        self.cases_opened = 0
        self.money_spent = 0.0
        self.money_earned_from_selling = 0.0
        self.tradeups_done = 0
        self.stattrak_drops = 0
        self.drops_by_rarity = {r: 0 for r in self.rarities}

        if clear_achievements:
            self.achievements_unlocked.clear()

        for var in self.auto_sell_vars.values():
            var.set(False)

        self.update_stats_window()
        self.check_achievements()
        self.save_game()

    def reset_progress(self):
        confirm = messagebox.askyesno(
            "Reset Progress",
            "Are you sure you want to reset all progress?\n"
            "This will clear your balance, inventory, stats and achievements.\n"
            "Prestige level will stay."
        )
        if not confirm:
            return

        self._soft_reset(clear_achievements=True)
        self.set_label("Progress reset!", "white" if self.dark_mode else "black")

    def prestige(self):
        if self.balance < self.prestige_threshold:
            messagebox.showinfo(
                "Prestige",
                f"You need at least ${self.prestige_threshold:.0f} balance to prestige.\n"
                f"Current balance: ${self.balance:.2f}"
            )
            return

        confirm = messagebox.askyesno(
            "Prestige",
            "Prestiging will:\n"
            "- Reset your balance to $500\n"
            "- Clear your inventory and stats\n"
            "- KEEP your achievements\n\n"
            "In return you gain +10% sell value per prestige.\n\n"
            "Do you want to prestige?"
        )
        if not confirm:
            return

        self.prestige_level += 1
        self.update_prestige_label()
        self._soft_reset(clear_achievements=False)
        self.show_prestige_popup(self.prestige_level)
        self.set_label(f"Prestiged to level {self.prestige_level}!", "white" if self.dark_mode else "black")

    # -------------------------------------------------
    # THEME / DARK MODE
    # -------------------------------------------------

    def set_theme_colors(self):
        if self.dark_mode:
            self.bg_color = "#121212"
            self.panel_color = "#1e1e1e"
            self.text_color = "#f5f5f5"
            self.list_bg = "#181818"
            self.list_fg = "#f5f5f5"
            self.button_bg = "#2a2a2a"
            self.button_fg = "#f5f5f5"
            self.entry_bg = "#181818"
            self.accent_color = "#3a7afe"
        else:
            self.bg_color = "#f0f0f0"
            self.panel_color = "#ffffff"
            self.text_color = "#000000"
            self.list_bg = "#ffffff"
            self.list_fg = "#000000"
            self.button_bg = "#e0e0e0"
            self.button_fg = "#000000"
            self.entry_bg = "#ffffff"
            self.accent_color = "#3a7afe"

    def apply_theme(self):
        self.set_theme_colors()
        try:
            self.root.configure(bg=self.bg_color)
        except tk.TclError:
            pass
        self._themify(self.root)

        if self.inventory_box is not None:
            for row, inv_idx in enumerate(self.inventory_view_indices):
                if 0 <= inv_idx < len(self.inventory):
                    rarity = self.inventory[inv_idx][1]
                    color = self.rarity_colors.get(rarity, self.list_fg)
                    try:
                        self.inventory_box.itemconfig(row, fg=color)
                    except tk.TclError:
                        pass

    def _themify(self, widget):
        cls = widget.winfo_class()

        try:
            if cls in ("Toplevel", "Frame", "Labelframe"):
                widget.configure(bg=self.bg_color)
            elif cls == "Label":
                widget.configure(bg=self.bg_color, fg=self.text_color)
            elif cls == "Button":
                widget.configure(
                    bg=self.button_bg,
                    fg=self.button_fg,
                    activebackground=self.accent_color,
                    activeforeground=self.text_color,
                    bd=1,
                    highlightthickness=0,
                )
            elif cls == "Checkbutton":
                widget.configure(
                    bg=self.bg_color,
                    fg=self.text_color,
                    activebackground=self.bg_color,
                    activeforeground=self.text_color,
                    selectcolor=self.bg_color,
                    bd=0,
                    highlightthickness=0,
                )
            elif cls == "Entry":
                widget.configure(
                    bg=self.entry_bg,
                    fg=self.text_color,
                    insertbackground=self.text_color,
                    bd=1,
                    highlightthickness=1,
                    highlightbackground=self.panel_color,
                )
            elif cls == "Listbox":
                widget.configure(
                    bg=self.list_bg,
                    fg=self.list_fg,
                    selectbackground=self.accent_color,
                    selectforeground=self.text_color,
                    bd=0,
                    highlightthickness=1,
                    highlightbackground=self.panel_color,
                )
            elif cls == "Canvas":
                pass
            elif cls == "Menubutton":
                widget.configure(
                    bg=self.button_bg,
                    fg=self.button_fg,
                    activebackground=self.accent_color,
                    activeforeground=self.text_color,
                    bd=1,
                    highlightthickness=0,
                )
                try:
                    menu = widget["menu"]
                    menu.configure(
                        bg=self.list_bg,
                        fg=self.list_fg,
                        activebackground=self.accent_color,
                        activeforeground=self.text_color,
                    )
                except Exception:
                    pass
        except tk.TclError:
            pass

        for child in widget.winfo_children():
            self._themify(child)

    def toggle_dark_mode(self):
        self.dark_mode = self.dark_mode_var.get()
        self.apply_theme()

    # -------------------------------------------------
    # ACHIEVEMENTS & PRESTIGE POPUPS
    # -------------------------------------------------

    def check_achievements(self):
        newly = []
        for key, title, cond in self.achievements_def:
            if cond(self) and key not in self.achievements_unlocked:
                self.achievements_unlocked.add(key)
                newly.append(title)

        if newly:
            for title in newly:
                self.show_achievement_popup(title)
            self.update_stats_window()
            self.save_game()

    def show_achievement_popup(self, title):
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        self.root.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()

        width = 260
        height = 70
        x = rx + rw - width - 20
        y = ry + 40

        popup.geometry(f"{width}x{height}+{x}+{y}")

        bg = "#1e272e" if self.dark_mode else "#ffffff"
        fg = "#f5f5f5" if self.dark_mode else "#000000"

        popup.configure(bg=bg)

        title_label = tk.Label(
            popup,
            text="Achievement Unlocked!",
            font=("Arial", 11, "bold"),
            bg=bg,
            fg=self.accent_color
        )
        title_label.pack(pady=(8, 0))

        text_label = tk.Label(
            popup,
            text=title,
            font=("Arial", 10),
            bg=bg,
            fg=fg,
            wraplength=240,
            justify="center"
        )
        text_label.pack(pady=(2, 8))

        popup.after(2500, popup.destroy)

    def show_prestige_popup(self, level):
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        self.root.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()

        width = 260
        height = 70
        x = rx + rw - width - 20
        y = ry + 120

        popup.geometry(f"{width}x{height}+{x}+{y}")

        bg = "#1e272e" if self.dark_mode else "#ffffff"
        fg = "#f5f5f5" if self.dark_mode else "#000000"

        popup.configure(bg=bg)

        title_label = tk.Label(
            popup,
            text="Prestige Up!",
            font=("Arial", 11, "bold"),
            bg=bg,
            fg="#ffd700"
        )
        title_label.pack(pady=(8, 0))

        bonus = int(level * 10)
        text_label = tk.Label(
            popup,
            text=f"You reached Prestige {level}.\nSell bonus: +{bonus}% value.",
            font=("Arial", 10),
            bg=bg,
            fg=fg,
            wraplength=240,
            justify="center"
        )
        text_label.pack(pady=(2, 8))

        popup.after(2500, popup.destroy)

    # -------------------------------------------------
    # UI HELPERS
    # -------------------------------------------------

    def update_inventory_value(self):
        total = 0.0
        for item in self.inventory:
            name, rarity, color, is_st, quality, case_name, wear_float, base_price = item
            total += self.get_item_value(rarity, is_st, wear_float, base_price)
        if self.inventory_value_label is not None:
            self.inventory_value_label.config(text=f"Inventory Value: ${total:.2f}")

    def set_label(self, text, color):
        self.rolling_label.config(text=text, fg=color)

    def update_prestige_label(self):
        if self.prestige_label is not None:
            if self.prestige_level > 0:
                self.prestige_label.config(text=f"Prestige: P{self.prestige_level}")
            else:
                self.prestige_label.config(text="Prestige: None")

# -------------------------------------------------
# TKINTER ROOT ADAPTER
# -------------------------------------------------

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.game = CaseGame(self)

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()