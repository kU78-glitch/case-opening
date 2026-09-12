import customtkinter as ctk
import config
from ui.theme import (
    PANEL_BG, CARD_BG, ACCENT_BLUE, ACCENT_HOVER, SUCCESS_GREEN,
    DANGER_RED, TEXT_MAIN, TEXT_MUTED, RARITY_COLORS
)

class TradeUpView(ctk.CTkFrame):
    def __init__(self, master, game, sound_manager, on_state_changed):
        super().__init__(master, fg_color=PANEL_BG, corner_radius=12)
        self.game = game
        self.sound = sound_manager
        self.on_state_changed = on_state_changed

        self.eligible_rarities = ["Mil-Spec", "Restricted", "Classified"]
        self.selected_indices = set()
        self.candidate_items = []  # List of (orig_inventory_idx, item)

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # Header
        title = ctk.CTkLabel(
            container,
            text="Trade-Up Contract (10 Items ➔ 1 Higher Tier)",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_MAIN
        )
        title.pack(pady=(0, 10))

        # Controls row (Rarity selector + Auto-fill + Status)
        ctrl_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8)
        ctrl_card.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(ctrl_card, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(row, text="Source Rarity:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
        self.rarity_var = ctk.StringVar(value=self.eligible_rarities[0])
        self.rarity_menu = ctk.CTkOptionMenu(
            row,
            variable=self.rarity_var,
            values=self.eligible_rarities,
            width=140,
            command=lambda _: self.refresh_candidates()
        )
        self.rarity_menu.pack(side="left", padx=5)

        self.autofill_btn = ctk.CTkButton(
            row,
            text="⚡ Auto-fill 10",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            width=120,
            command=self._autofill
        )
        self.autofill_btn.pack(side="left", padx=15)

        self.counter_label = ctk.CTkLabel(
            row,
            text="0 / 10 Selected",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=ACCENT_BLUE
        )
        self.counter_label.pack(side="right", padx=10)

        # Scrollable candidates list
        self.scroll_frame = ctk.CTkScrollableFrame(container, fg_color="#181a20", corner_radius=8, height=330)
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Action & Result Bottom Bar
        bottom_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8)
        bottom_card.pack(fill="x", pady=(5, 0))

        b_row = ctk.CTkFrame(bottom_card, fg_color="transparent")
        b_row.pack(fill="x", padx=15, pady=12)

        self.tradeup_btn = ctk.CTkButton(
            b_row,
            text="CONFIRM TRADE-UP",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=SUCCESS_GREEN,
            hover_color="#059669",
            height=40,
            width=200,
            state="disabled",
            command=self._do_tradeup
        )
        self.tradeup_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            b_row,
            text="Select 10 items of identical rarity to proceed.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_MUTED
        )
        self.status_label.pack(side="left", padx=20)

    def refresh_candidates(self, clear_selection: bool = True):
        if clear_selection:
            self.selected_indices.clear()

        target_rarity = self.rarity_var.get()
        self.candidate_items = [
            (idx, item) for idx, item in enumerate(self.game.inventory)
            if item.rarity == target_rarity
        ]

        self._render_rows()
        self._update_counter()

    def _render_rows(self):
        for child in self.scroll_frame.winfo_children():
            child.destroy()

        target_rarity = self.rarity_var.get()
        if not self.candidate_items:
            empty = ctk.CTkLabel(
                self.scroll_frame,
                text=f"No {target_rarity} items in inventory for trade-up.",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=TEXT_MUTED
            )
            empty.pack(pady=40)
            return

        for orig_idx, item in self.candidate_items:
            self._create_candidate_row(orig_idx, item)

    def _create_candidate_row(self, orig_idx: int, item):
        val = self.game.get_item_value(item)
        r_color = RARITY_COLORS.get(item.rarity, TEXT_MAIN)

        row_card = ctk.CTkFrame(self.scroll_frame, fg_color=CARD_BG, corner_radius=6, height=40)
        row_card.pack(fill="x", pady=2, padx=5)
        row_card.pack_propagate(False)

        # Checkbox
        cb_var = ctk.BooleanVar(value=orig_idx in self.selected_indices)
        cb = ctk.CTkCheckBox(
            row_card,
            text="",
            variable=cb_var,
            width=20,
            checkbox_height=20,
            checkbox_width=20,
            command=lambda i=orig_idx, v=cb_var: self._toggle_selection(i, v)
        )
        cb.pack(side="left", padx=(10, 5))

        st_prefix = "★ " if item.is_st else ""
        name_lbl = ctk.CTkLabel(
            row_card,
            text=f"{st_prefix}{item.name}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=r_color
        )
        name_lbl.pack(side="left", padx=5)

        info_lbl = ctk.CTkLabel(
            row_card,
            text=f"{item.quality} ({item.wear_float:.4f})  •  {item.case_name}  •  ${val:,.2f}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        )
        info_lbl.pack(side="left", padx=10)

    def _toggle_selection(self, orig_idx: int, cb_var: ctk.BooleanVar):
        if cb_var.get():
            if len(self.selected_indices) >= 10:
                cb_var.set(False)
                return
            self.selected_indices.add(orig_idx)
        else:
            self.selected_indices.discard(orig_idx)
        self._update_counter()

    def _autofill(self):
        # Check current rarity first
        current_candidates = [
            (idx, item) for idx, item in enumerate(self.game.inventory)
            if item.rarity == self.rarity_var.get()
        ]

        # If current rarity has less than 10, see if another eligible rarity has >= 10
        if len(current_candidates) < 10:
            for r in self.eligible_rarities:
                matching = [
                    (idx, item) for idx, item in enumerate(self.game.inventory)
                    if item.rarity == r
                ]
                if len(matching) >= 10:
                    self.rarity_var.set(r)
                    self.candidate_items = matching
                    break
            else:
                self.candidate_items = current_candidates
        else:
            self.candidate_items = current_candidates

        self.selected_indices.clear()
        for orig_idx, _ in self.candidate_items[:10]:
            self.selected_indices.add(orig_idx)

        self._render_rows()
        self._update_counter()

    def _update_counter(self):
        count = len(self.selected_indices)
        self.counter_label.configure(text=f"{count} / 10 Selected")
        if count == 10:
            self.tradeup_btn.configure(state="normal", fg_color=SUCCESS_GREEN)
            self.status_label.configure(text="Ready! Click confirm to sign contract.", text_color=SUCCESS_GREEN)
        else:
            self.tradeup_btn.configure(state="disabled", fg_color="#374151")
            self.status_label.configure(text=f"Select {10 - count} more items.", text_color=TEXT_MUTED)

    def _do_tradeup(self):
        if len(self.selected_indices) != 10:
            return

        success, msg, new_item = self.game.perform_tradeup(list(self.selected_indices))
        if success and new_item:
            self.sound.play_win()
            st_text = "StatTrak™ " if new_item.is_st else ""
            r_color = RARITY_COLORS.get(new_item.rarity, SUCCESS_GREEN)
            self.status_label.configure(
                text=f"Contract Signed! You got: {st_text}{new_item.name} [{new_item.quality}] ({new_item.rarity})",
                text_color=r_color
            )
            self.selected_indices.clear()
            self.on_state_changed()
            self.game.save()
            self.refresh_candidates()
        else:
            self.status_label.configure(text=msg, text_color=DANGER_RED)

