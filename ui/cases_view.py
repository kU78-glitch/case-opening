import random
import tkinter as tk
import customtkinter as ctk
from typing import Optional, List, Dict

from cases import CASES
import config
from models import roll_float, float_to_quality, Item
from ui.theme import (
    PANEL_BG, CARD_BG, ACCENT_BLUE, ACCENT_HOVER, SUCCESS_GREEN,
    TEXT_MAIN, TEXT_MUTED, GOLD_COLOR, RARITY_COLORS
)

class CasesView(ctk.CTkFrame):
    def __init__(self, master, game, sound_manager, on_state_changed, on_open_inventory=None):
        super().__init__(master, fg_color=PANEL_BG, corner_radius=12)
        self.game = game
        self.sound = sound_manager
        self.on_state_changed = on_state_changed

        # Multi-case selection (1, 2, or 3)
        self.case_count = 1

        # Multi-spin state
        self.spin_running = False
        self.spin_sequences: List[List[Dict]] = []
        self.spin_frame = 0
        self.spin_visible_radius = 4
        self.spin_win_index = 35
        self.winning_items: List[Item] = []
        self.spin_canvases: List[tk.Canvas] = []

        self._build_ui()
        self._setup_spinner_rows(1)
        self.refresh_controls()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=15)

        # Title
        title = ctk.CTkLabel(
            container,
            text="Case Opening Simulator",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_MAIN
        )
        title.pack(pady=(0, 6))

        # Case Selector & Price Card
        case_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=10)
        case_card.pack(fill="x", padx=10, pady=(0, 8))

        selector_row = ctk.CTkFrame(case_card, fg_color="transparent")
        selector_row.pack(pady=(8, 4))

        case_names = list(CASES.keys())
        self.selected_case_var = ctk.StringVar(value=case_names[0] if case_names else "")
        self.case_menu = ctk.CTkOptionMenu(
            selector_row,
            variable=self.selected_case_var,
            values=case_names,
            width=260,
            height=36,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=lambda _: self.update_case_price()
        )
        self.case_menu.pack(side="left", padx=10)

        self.price_label = ctk.CTkLabel(
            case_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_MUTED
        )
        self.price_label.pack(pady=(0, 8))
        self.update_case_price()

        # Action Controls: OPEN CASE + Multi-Count SegmentedButton
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(pady=4)

        self.open_btn = ctk.CTkButton(
            btn_row,
            text="OPEN 1 CASE",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            width=180,
            height=42,
            fg_color=SUCCESS_GREEN,
            hover_color="#059669",
            corner_radius=8,
            command=self.start_cases
        )
        self.open_btn.pack(side="left", padx=8)

        # Multi-Count Segmented Button
        seg_frame = ctk.CTkFrame(btn_row, fg_color=CARD_BG, corner_radius=8)
        seg_frame.pack(side="left", padx=8)

        ctk.CTkLabel(
            seg_frame,
            text="Unbox Count:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_MUTED
        ).pack(side="left", padx=(10, 6), pady=6)

        self.seg_button = ctk.CTkSegmentedButton(
            seg_frame,
            values=["1x", "2x", "3x"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=32,
            selected_color=ACCENT_BLUE,
            selected_hover_color=ACCENT_HOVER,
            command=self._on_count_selected
        )
        self.seg_button.set("1x")
        self.seg_button.pack(side="left", padx=(0, 10), pady=6)

        # Result Announcement Label
        self.rolling_label = ctk.CTkLabel(
            container,
            text="Select case and click OPEN to spin!",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=TEXT_MAIN,
            height=32
        )
        self.rolling_label.pack(pady=4)

        # Dynamic Stacked Spinners Container
        self.spinner_card = ctk.CTkFrame(container, fg_color="#0b0d11", corner_radius=10)
        self.spinner_card.pack(fill="x", padx=10, pady=4)

        self.canvases_frame = ctk.CTkFrame(self.spinner_card, fg_color="transparent")
        self.canvases_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Auto-Sell Options
        auto_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=10)
        auto_card.pack(fill="x", padx=10, pady=(6, 0))

        auto_title = ctk.CTkLabel(
            auto_card,
            text="Auto-Sell Dropped Items By Rarity:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_MUTED
        )
        auto_title.pack(anchor="w", padx=15, pady=(6, 2))

        cb_row = ctk.CTkFrame(auto_card, fg_color="transparent")
        cb_row.pack(fill="x", padx=15, pady=(0, 8))

        self.auto_sell_vars = {}
        for rarity in config.RARITIES:
            var = ctk.BooleanVar(value=self.game.auto_sell.get(rarity, False))
            self.auto_sell_vars[rarity] = var
            color = RARITY_COLORS.get(rarity, TEXT_MAIN)
            cb = ctk.CTkCheckBox(
                cb_row,
                text=rarity,
                variable=var,
                text_color=color,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                checkbox_height=18,
                checkbox_width=18,
                corner_radius=4,
                command=lambda r=rarity, v=var: self._on_auto_sell_toggle(r, v)
            )
            cb.pack(side="left", padx=10, expand=True)

    def _get_max_unlocked_cases(self) -> int:
        if self.game.prestige_level >= 2:
            return 3
        elif self.game.prestige_level == 1:
            return 2
        return 1

    def refresh_controls(self):
        """Called when view opens or prestige changes to enforce limits."""
        max_allowed = self._get_max_unlocked_cases()
        if self.case_count > max_allowed:
            self.case_count = max_allowed
            self.seg_button.set(f"{self.case_count}x")
            self._setup_spinner_rows(self.case_count)
            self.update_case_price()

    def _on_count_selected(self, value: str):
        target_count = int(value.replace("x", ""))
        max_allowed = self._get_max_unlocked_cases()

        if target_count > max_allowed:
            req_prestige = 1 if target_count == 2 else 2
            self.rolling_label.configure(
                text=f"🔒 {target_count}x Multi-Case unlocks at Prestige {req_prestige}!",
                text_color=GOLD_COLOR
            )
            # Revert selection
            self.seg_button.set(f"{self.case_count}x")
            return

        self.case_count = target_count
        self.open_btn.configure(text=f"OPEN {self.case_count} {'CASES' if self.case_count > 1 else 'CASE'}")
        self._setup_spinner_rows(self.case_count)
        self.update_case_price()

    def _setup_spinner_rows(self, count: int):
        """Clears and instantiates count stacked roulette canvases."""
        for child in self.canvases_frame.winfo_children():
            child.destroy()

        self.spin_canvases.clear()

        # Canvas heights based on count
        if count == 1:
            row_height = 80
            pady = 2
        elif count == 2:
            row_height = 68
            pady = 3
        else:
            row_height = 58
            pady = 2

        for row_idx in range(count):
            canvas = tk.Canvas(
                self.canvases_frame,
                width=680,
                height=row_height,
                bg="#0b0d11",
                highlightthickness=1,
                highlightbackground="#1e222d"
            )
            canvas.pack(pady=pady)
            self.spin_canvases.append(canvas)
            self._draw_placeholder(canvas, row_idx + 1)

    def _draw_placeholder(self, canvas: tk.Canvas, row_number: int):
        w = int(canvas.cget("width"))
        h = int(canvas.cget("height"))
        canvas.delete("all")
        # Center line marker
        canvas.create_line(w // 2, 0, w // 2, h, fill="#fbbf24", width=2)
        canvas.create_text(
            w // 2, h // 2,
            text=f"Slot #{row_number} - Ready to spin",
            fill="#4b5563",
            font=("Segoe UI", 11, "bold")
        )

    def _on_auto_sell_toggle(self, rarity: str, var: ctk.BooleanVar):
        self.game.auto_sell[rarity] = var.get()
        self.game.save()

    def update_case_price(self):
        case_name = self.selected_case_var.get()
        case_data = CASES.get(case_name)
        if not case_data:
            return

        case_price = case_data["price"]
        key_price = config.KEY_PRICE
        single_cost = case_price + key_price
        total_cost = single_cost * self.case_count

        if self.case_count == 1:
            self.price_label.configure(
                text=f"Case: ${case_price:.2f}  |  Key: ${key_price:.2f}  |  Total: ${total_cost:.2f}"
            )
        else:
            self.price_label.configure(
                text=f"Case: ${case_price:.2f}  |  Key: ${key_price:.2f}  |  Per Case: ${single_cost:.2f}  |  Total ({self.case_count}x): ${total_cost:.2f}"
            )

    def start_cases(self):
        if self.spin_running:
            return

        case_name = self.selected_case_var.get()
        case_data = CASES.get(case_name)
        if not case_data:
            return

        single_cost = case_data["price"] + config.KEY_PRICE
        total_cost = single_cost * self.case_count

        if self.game.balance < total_cost:
            self.rolling_label.configure(
                text=f"Insufficient balance! Need ${total_cost:.2f} to open {self.case_count} cases.",
                text_color="#ef4444"
            )
            return

        # Open items with delayed stats (so achievements and inventory commits wait for spin reveal)
        self.winning_items = []
        for _ in range(self.case_count):
            item = self.game.open_case(case_name, delay_stats=True)
            if item:
                self.winning_items.append(item)

        if len(self.winning_items) != self.case_count:
            self.rolling_label.configure(text="Error generating drops!", text_color="#ef4444")
            return

        # Immediately update header balance without triggering achievements prematurely
        self.on_state_changed(check_achievements=False)
        self.game.save()

        self.start_multi_spin(case_name)

    def start_multi_spin(self, case_name: str):
        self.spin_running = True
        self.open_btn.configure(state="disabled")
        self.seg_button.configure(state="disabled")
        self.case_menu.configure(state="disabled")
        self.rolling_label.configure(text="Spinning...", text_color=TEXT_MAIN)

        case_data = CASES[case_name]
        items = case_data["items"]
        case_multiplier = float(case_data.get("multiplier", 1.0))

        fake_count = 40
        self.spin_sequences = []

        for row_idx, winning_item in enumerate(self.winning_items):
            row_seq = []
            for _ in range(fake_count):
                rf = random.choice(list(items.keys()))
                n_fake, _ = random.choice(items[rf])
                f_fake = roll_float()
                row_seq.append({
                    "case_name": case_name,
                    "rarity": rf,
                    "name": n_fake,
                    "is_st": False,
                    "quality": float_to_quality(f_fake),
                    "wear_float": f_fake,
                    "base_price": round(config.SELL_PRICES.get(rf, 5.0) * case_multiplier, 2)
                })

            win_idx = fake_count - self.spin_visible_radius - 1
            row_seq[win_idx] = {
                "case_name": winning_item.case_name,
                "rarity": winning_item.rarity,
                "name": winning_item.name,
                "is_st": winning_item.is_st,
                "quality": winning_item.quality,
                "wear_float": winning_item.wear_float,
                "base_price": winning_item.base_price
            }
            self.spin_sequences.append(row_seq)

        self.spin_win_index = fake_count - self.spin_visible_radius - 1
        self.spin_frame = 0
        self._spin_step()

    def _spin_step(self):
        frame = self.spin_frame

        if frame > self.spin_win_index:
            self.spin_running = False

            def finalize():
                self.open_btn.configure(state="normal")
                self.seg_button.configure(state="normal")
                self.case_menu.configure(state="normal")
                self.finalize_multi_spin()

            self.after(500, finalize)
            return

        # Sound tick
        self.sound.play_tick()

        center_index = frame
        visible_radius = self.spin_visible_radius
        item_width = 85
        center_x = 340

        # Animate each row canvas simultaneously
        for row_idx, canvas in enumerate(self.spin_canvases):
            if row_idx >= len(self.spin_sequences):
                continue

            seq = self.spin_sequences[row_idx]
            canvas.delete("all")
            h = int(canvas.cget("height"))
            center_y = h // 2
            card_half_h = min(26, h // 2 - 4)

            for offset in range(-visible_radius, visible_radius + 1):
                idx = center_index + offset
                if 0 <= idx < len(seq):
                    item = seq[idx]
                    x = center_x + offset * item_width
                    y = center_y

                    bg = RARITY_COLORS.get(item["rarity"], "#444444")
                    outline = "#fbbf24" if offset == 0 else "#252833"
                    width = 3 if offset == 0 else 1

                    canvas.create_rectangle(
                        x - 38, y - card_half_h, x + 38, y + card_half_h,
                        fill=bg, outline=outline, width=width
                    )

                    st_pref = "★ " if item.get("is_st") else ""
                    display = f"{st_pref}{item['name']}"
                    canvas.create_text(
                        x, y, text=display, fill="#ffffff",
                        font=("Segoe UI", 9, "bold"), width=72
                    )

            # Center indicator line on each canvas
            canvas.create_line(center_x, 0, center_x, h, fill="#fbbf24", width=2)

        # Quadratic easing delay adjusted by permanent spin_speed perk
        t = frame / max(1, self.spin_win_index)
        base_delay = int(30 + 220 * (t ** 2))
        speed_mult = 1.0 + self.game.perks.get("spin_speed", 0.0)
        delay = max(10, int(base_delay / speed_mult))

        self.spin_frame += 1
        self.after(delay, self._spin_step)

    def finalize_multi_spin(self):
        has_gold = any(it.rarity == "Rare Special" for it in self.winning_items)
        has_covert = any(it.rarity == "Covert" for it in self.winning_items)

        # Audio reveal
        if has_gold:
            self.sound.play_gold()
        elif has_covert:
            self.sound.play_gold()
        else:
            self.sound.play_win()

        result_texts = []
        auto_sold_count = 0
        auto_sold_total = 0.0

        for item in self.winning_items:
            auto_sold, val = self.game.finalize_opened_item(item)
            st_prefix = "★ " if item.is_st else ""
            item_display = f"{st_prefix}{item.name} [{item.quality}]"

            if auto_sold:
                auto_sold_count += 1
                auto_sold_total += val
                result_texts.append(f"{item_display} (Auto-sold ${val:,.2f})")
            else:
                result_texts.append(f"{item_display} (${val:,.2f})")

        # Update announcement text
        if self.case_count == 1:
            it = self.winning_items[0]
            st = "★ " if it.is_st else ""
            val = self.game.get_item_value(it)
            r_color = RARITY_COLORS.get(it.rarity, TEXT_MAIN)
            if self.game.auto_sell.get(it.rarity, False):
                self.rolling_label.configure(
                    text=f"Auto-sold {st}{it.name} [{it.quality} ({it.wear_float:.4f})] for ${val:,.2f}!",
                    text_color=SUCCESS_GREEN
                )
            else:
                self.rolling_label.configure(
                    text=f"You got: {st}{it.name} [{it.quality} ({it.wear_float:.4f})] (${val:,.2f})",
                    text_color=r_color
                )
        else:
            summary = "  |  ".join(result_texts)
            if auto_sold_count > 0:
                summary += f"  (Auto-sold {auto_sold_count} items for +${auto_sold_total:,.2f})"
            self.rolling_label.configure(
                text=summary,
                text_color=GOLD_COLOR if has_gold else SUCCESS_GREEN
            )

        self.on_state_changed()
        self.game.save()
