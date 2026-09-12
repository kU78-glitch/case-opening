import tkinter.messagebox as msgbox
import customtkinter as ctk
import config
from ui.theme import (
    PANEL_BG, CARD_BG, ACCENT_BLUE, ACCENT_HOVER, SUCCESS_GREEN,
    DANGER_RED, GOLD_COLOR, TEXT_MAIN, TEXT_MUTED, RARITY_COLORS
)

class StatsView(ctk.CTkFrame):
    def __init__(self, master, game, sound_manager, on_state_changed):
        super().__init__(master, fg_color=PANEL_BG, corner_radius=12)
        self.game = game
        self.sound = sound_manager
        self.on_state_changed = on_state_changed
        self.perk_modal = None

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=15)

        # Title
        title = ctk.CTkLabel(
            container,
            text="Game Statistics & Prestige Perks",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_MAIN
        )
        title.pack(pady=(0, 6))

        # Main scrollable area
        self.scroll = ctk.CTkScrollableFrame(container, fg_color="transparent", height=480)
        self.scroll.pack(fill="both", expand=True)

        # 1. Economy & Opening Stats Card
        stats_card = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=8)
        stats_card.pack(fill="x", pady=4)

        ctk.CTkLabel(
            stats_card,
            text="📊 Financial & Opening Overview",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=15, pady=(8, 4))

        grid = ctk.CTkFrame(stats_card, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=(0, 8))

        self.lbl_cases = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUTED)
        self.lbl_cases.grid(row=0, column=0, sticky="w", padx=10, pady=2)

        self.lbl_spent = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUTED)
        self.lbl_spent.grid(row=0, column=1, sticky="w", padx=10, pady=2)

        self.lbl_earned = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUTED)
        self.lbl_earned.grid(row=1, column=0, sticky="w", padx=10, pady=2)

        self.lbl_pnl = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_pnl.grid(row=1, column=1, sticky="w", padx=10, pady=2)

        self.lbl_tradeups = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUTED)
        self.lbl_tradeups.grid(row=2, column=0, sticky="w", padx=10, pady=2)

        self.lbl_st = ctk.CTkLabel(grid, text="", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUTED)
        self.lbl_st.grid(row=2, column=1, sticky="w", padx=10, pady=2)

        # 2. Drops by Rarity Card
        drops_card = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=8)
        drops_card.pack(fill="x", pady=4)

        ctk.CTkLabel(
            drops_card,
            text="🎯 Drops by Rarity Tier",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=15, pady=(8, 4))

        self.rarity_labels_frame = ctk.CTkFrame(drops_card, fg_color="transparent")
        self.rarity_labels_frame.pack(fill="x", padx=15, pady=(0, 8))

        self.rarity_labels = {}
        for r in config.RARITIES:
            lbl = ctk.CTkLabel(
                self.rarity_labels_frame,
                text="",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=RARITY_COLORS.get(r, TEXT_MAIN)
            )
            lbl.pack(side="left", expand=True, padx=4)
            self.rarity_labels[r] = lbl

        # 3. Permanent Stackable Perks Card
        self.perks_card = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=8)
        self.perks_card.pack(fill="x", pady=4)

        ctk.CTkLabel(
            self.perks_card,
            text="🌟 Permanent Stackable Roguelike Perks",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=GOLD_COLOR
        ).pack(anchor="w", padx=15, pady=(8, 4))

        self.perks_summary_label = ctk.CTkLabel(
            self.perks_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_MAIN,
            justify="left"
        )
        self.perks_summary_label.pack(anchor="w", padx=15, pady=(0, 4))

        self.perks_history_label = ctk.CTkLabel(
            self.perks_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED,
            justify="left",
            wraplength=700
        )
        self.perks_history_label.pack(anchor="w", padx=15, pady=(0, 8))

        # 4. Achievements Card
        ach_card = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=8)
        ach_card.pack(fill="x", pady=4)

        ctk.CTkLabel(
            ach_card,
            text="🏆 Achievements",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(anchor="w", padx=15, pady=(8, 4))

        self.ach_frame = ctk.CTkFrame(ach_card, fg_color="transparent")
        self.ach_frame.pack(fill="x", padx=15, pady=(0, 8))

        # 5. Prestige & Reset Card
        prestige_card = ctk.CTkFrame(self.scroll, fg_color=CARD_BG, corner_radius=8)
        prestige_card.pack(fill="x", pady=4)

        ctk.CTkLabel(
            prestige_card,
            text="⭐ Prestige Progression & Reset",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=GOLD_COLOR
        ).pack(anchor="w", padx=15, pady=(8, 4))

        self.prestige_info = ctk.CTkLabel(
            prestige_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_MAIN,
            justify="left"
        )
        self.prestige_info.pack(anchor="w", padx=15, pady=2)

        act_row = ctk.CTkFrame(prestige_card, fg_color="transparent")
        act_row.pack(fill="x", padx=15, pady=(8, 12))

        self.prestige_btn = ctk.CTkButton(
            act_row,
            text="⭐ PRESTIGE (Req. $10,000)",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=GOLD_COLOR,
            hover_color="#d97706",
            text_color="#000000",
            text_color_disabled="#ffffff",
            command=self._do_prestige
        )
        self.prestige_btn.pack(side="left", padx=(0, 15))

        self.reset_btn = ctk.CTkButton(
            act_row,
            text="Reset Progress",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=DANGER_RED,
            hover_color="#dc2626",
            command=self._do_reset
        )
        self.reset_btn.pack(side="left")

    def refresh(self):
        s = self.game.stats
        pnl = s.money_earned_from_selling - s.money_spent

        self.lbl_cases.configure(text=f"📦 Cases Opened: {s.cases_opened:,}")
        self.lbl_spent.configure(text=f"💸 Money Spent: ${s.money_spent:,.2f}")
        self.lbl_earned.configure(text=f"💰 Earned from Sales: ${s.money_earned_from_selling:,.2f}")

        pnl_text = f"📈 Net P/L: {'+' if pnl >= 0 else ''}${pnl:,.2f}"
        pnl_color = SUCCESS_GREEN if pnl >= 0 else DANGER_RED
        self.lbl_pnl.configure(text=pnl_text, text_color=pnl_color)

        self.lbl_tradeups.configure(text=f"🔄 Trade-Ups Done: {s.tradeups_done}")
        self.lbl_st.configure(text=f"★ StatTrak™ Drops: {s.stattrak_drops}")

        for r, lbl in self.rarity_labels.items():
            count = s.drops_by_rarity.get(r, 0)
            lbl.configure(text=f"{r}: {count}")

        # Perks summary
        p = self.game.perks
        has_any_perks = bool(self.game.perk_history) or any(v > 0 for v in p.values())

        if has_any_perks:
            covert_pct = p.get("covert_luck", 0.0) * 100
            gold_pct = p.get("gold_luck", 0.0) * 100
            st_pct = p.get("stattrak_bonus", 0.0) * 100
            sell_pct = p.get("sell_bonus", 0.0) * 100
            speed_pct = int(p.get("spin_speed", 0.0) * 100)

            perks_summary = (
                f"🔴 Covert Luck: +{covert_pct:.1f}%    "
                f"⭐ Gold Luck: +{gold_pct:.2f}%    "
                f"🟠 StatTrak™: +{st_pct:.1f}%\n"
                f"💰 Extra Sell Payout: +{sell_pct:.1f}%    "
                f"⚡ Spin Speed: +{speed_pct}%"
            )
            self.perks_summary_label.configure(text=perks_summary)
            history_str = "Selected History: " + "  •  ".join(self.game.perk_history)
            self.perks_history_label.configure(text=history_str)
        else:
            self.perks_summary_label.configure(text="No active perks. Prestige to earn permanent perks!")
            self.perks_history_label.configure(text="")

        # Achievements
        for child in self.ach_frame.winfo_children():
            child.destroy()

        for key, name, _ in self.game.achievements_def:
            unlocked = key in self.game.achievements_unlocked
            status_icon = "✅" if unlocked else "⬜"
            status_color = SUCCESS_GREEN if unlocked else TEXT_MUTED

            row = ctk.CTkFrame(self.ach_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=f"{status_icon} {name}",
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold" if unlocked else "normal"),
                text_color=status_color
            ).pack(side="left")

        # Prestige
        lvl = self.game.prestige_level
        bonus = int(lvl * 10)
        req = self.game.prestige_threshold
        next_lvl = lvl + 1

        if lvl == 0:
            reward_note = "Next Perks: Unlocks 2x Multi-Case Unboxing + 10% Sell Bonus + 1 Roguelike Perk"
        elif lvl == 1:
            reward_note = "Next Perks: Unlocks 3x Multi-Case Unboxing (Max) + 10% Sell Bonus + 1 Roguelike Perk"
        else:
            reward_note = "Next Perks: +10% Permanent Sell Value + 1 Roguelike Perk Choice"

        self.prestige_info.configure(
            text=f"Current Prestige: Level {lvl} (+{bonus}% Base Sell Bonus)\n"
                 f"Next Level Target ({lvl} -> {next_lvl}): Reach ${req:,.0f} balance.\n"
                 f"⭐ {reward_note}"
        )

        if self.game.balance >= req:
            self.prestige_btn.configure(state="normal", text=f"⭐ PRESTIGE TO LEVEL {next_lvl} NOW!")
        else:
            self.prestige_btn.configure(state="disabled", text=f"⭐ Prestige (Need ${req - self.game.balance:,.2f} more)")

    def _do_prestige(self):
        if self.game.balance < self.game.prestige_threshold:
            return

        confirm = msgbox.askyesno(
            "Prestige Confirmation",
            "Prestiging will reset your balance to $500 and clear your inventory,\n"
            "but permanently grant you +10% sell value AND let you choose\n"
            "1 PERMANENT ROGUELIKE PERK!\n\n"
            "Do you want to prestige?"
        )
        if confirm:
            self.game.prestige()
            self.sound.play_gold()
            self.on_state_changed()
            self.game.save()
            self.refresh()
            # Show in-window perk selection modal!
            self._show_perk_modal()

    def _show_perk_modal(self):
        if self.perk_modal is not None and self.perk_modal.winfo_exists():
            self.perk_modal.destroy()

        choices = self.game.generate_perk_choices()

        # In-window overlay modal
        self.perk_modal = ctk.CTkFrame(
            self,
            fg_color="#181a22",
            border_width=2,
            border_color=GOLD_COLOR,
            corner_radius=14
        )
        self.perk_modal.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.88, relheight=0.75)

        title = ctk.CTkLabel(
            self.perk_modal,
            text=f"⭐ PRESTIGE LEVEL {self.game.prestige_level} UNLOCKED! ⭐",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=GOLD_COLOR
        )
        title.pack(pady=(16, 4))

        subtitle = ctk.CTkLabel(
            self.perk_modal,
            text="Choose 1 Permanent Roguelike Perk to stack onto your profile:",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=TEXT_MAIN
        )
        subtitle.pack(pady=(0, 16))

        cards_row = ctk.CTkFrame(self.perk_modal, fg_color="transparent")
        cards_row.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for choice in choices:
            card = ctk.CTkFrame(cards_row, fg_color="#222530", corner_radius=10, border_width=1, border_color="#374151")
            card.pack(side="left", fill="both", expand=True, padx=12, pady=5)

            # Icon
            ctk.CTkLabel(
                card,
                text=choice["icon"],
                font=ctk.CTkFont(family="Segoe UI", size=36)
            ).pack(pady=(16, 6))

            # Title
            ctk.CTkLabel(
                card,
                text=choice["title"],
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                text_color=SUCCESS_GREEN
            ).pack(pady=4)

            # Description
            ctk.CTkLabel(
                card,
                text=choice["desc"],
                font=ctk.CTkFont(family="Segoe UI", size=13),
                text_color=TEXT_MUTED,
                wraplength=220,
                justify="center"
            ).pack(pady=8, padx=10, expand=True)

            # Choose button
            btn = ctk.CTkButton(
                card,
                text="SELECT PERK",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                fg_color=GOLD_COLOR,
                hover_color="#d97706",
                text_color="#000000",
                height=40,
                command=lambda p=choice: self._on_perk_chosen(p)
            )
            btn.pack(fill="x", padx=20, pady=(10, 16))

    def _on_perk_chosen(self, perk: dict):
        self.game.apply_perk(perk)
        self.sound.play_gold()
        if self.perk_modal is not None and self.perk_modal.winfo_exists():
            self.perk_modal.destroy()
            self.perk_modal = None
        self.on_state_changed()
        self.refresh()

    def _do_reset(self):
        confirm = msgbox.askyesno(
            "Hard Reset Progress",
            "Are you sure you want to perform a complete HARD RESET?\n\n"
            "This will permanently wipe:\n"
            "• Balance back to $500.00\n"
            "• All inventory items\n"
            "• Lifetime stats and achievements\n"
            "• Prestige level back to 0\n"
            "• ALL active Roguelike perks and perk history\n\n"
            "This action cannot be undone."
        )
        if confirm:
            self.game.reset_progress(clear_achievements=True, hard_reset=True)
            self.on_state_changed()
            self.game.save()
            self.refresh()
