import customtkinter as ctk
import config
from ui.theme import (
    PANEL_BG, CARD_BG, ACCENT_BLUE, ACCENT_HOVER, SUCCESS_GREEN,
    DANGER_RED, TEXT_MAIN, TEXT_MUTED, RARITY_COLORS
)

class InventoryView(ctk.CTkFrame):
    def __init__(self, master, game, on_state_changed, on_open_tradeup):
        super().__init__(master, fg_color=PANEL_BG, corner_radius=12)
        self.game = game
        self.on_state_changed = on_state_changed
        self.on_open_tradeup = on_open_tradeup

        self.selected_item_index = None

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # Header Row
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        title = ctk.CTkLabel(
            header,
            text="Player Inventory",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_MAIN
        )
        title.pack(side="left")

        tradeup_btn = ctk.CTkButton(
            header,
            text="🔄 Trade-Up Contract",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=ACCENT_BLUE,
            hover_color=ACCENT_HOVER,
            corner_radius=6,
            command=self.on_open_tradeup
        )
        tradeup_btn.pack(side="right")

        # Filters & Sorting Card
        filter_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8)
        filter_card.pack(fill="x", pady=(0, 10), padx=2)

        f_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        f_row.pack(fill="x", padx=15, pady=10)

        # Rarity filter
        ctk.CTkLabel(f_row, text="Filter:", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
        self.filter_rarity_var = ctk.StringVar(value="All")
        rarity_options = ["All"] + config.RARITIES
        self.rarity_menu = ctk.CTkOptionMenu(
            f_row,
            variable=self.filter_rarity_var,
            values=rarity_options,
            width=130,
            command=lambda _: self.refresh_list()
        )
        self.rarity_menu.pack(side="left", padx=5)

        # StatTrak only checkbox
        self.filter_st_var = ctk.BooleanVar(value=False)
        self.st_checkbox = ctk.CTkCheckBox(
            f_row,
            text="StatTrak™ Only",
            variable=self.filter_st_var,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            command=self.refresh_list
        )
        self.st_checkbox.pack(side="left", padx=15)

        # Sort mode
        ctk.CTkLabel(f_row, text="Sort:", font=ctk.CTkFont(family="Segoe UI", size=13), text_color=TEXT_MUTED).pack(side="left", padx=(10, 5))
        self.sort_var = ctk.StringVar(value="Value: High to Low")
        sort_options = [
            "Value: High to Low",
            "Value: Low to High",
            "Rarity (Best First)",
            "Float: Low to High (Best)",
            "Name: A-Z"
        ]
        self.sort_menu = ctk.CTkOptionMenu(
            f_row,
            variable=self.sort_var,
            values=sort_options,
            width=180,
            command=lambda _: self.refresh_list()
        )
        self.sort_menu.pack(side="left", padx=5)

        # Scrollable Items Container
        self.items_scroll = ctk.CTkScrollableFrame(container, fg_color="#181a20", corner_radius=8, height=350)
        self.items_scroll.pack(fill="both", expand=True, pady=(0, 10))

        # Bottom Bar: Bulk Sell & Summary
        bottom_card = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8)
        bottom_card.pack(fill="x", pady=(5, 0))

        b_row = ctk.CTkFrame(bottom_card, fg_color="transparent")
        b_row.pack(fill="x", padx=15, pady=10)

        # Bulk sell
        ctk.CTkLabel(b_row, text="Bulk Sell:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(0, 5))
        self.bulk_rarity_var = ctk.StringVar(value="Mil-Spec")
        self.bulk_menu = ctk.CTkOptionMenu(
            b_row,
            variable=self.bulk_rarity_var,
            values=config.RARITIES,
            width=130
        )
        self.bulk_menu.pack(side="left", padx=5)

        self.bulk_sell_btn = ctk.CTkButton(
            b_row,
            text="Sell All of Tier",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=DANGER_RED,
            hover_color="#dc2626",
            width=110,
            command=self._bulk_sell
        )
        self.bulk_sell_btn.pack(side="left", padx=5)

        # Inventory Value Info on right
        self.summary_label = ctk.CTkLabel(
            b_row,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=SUCCESS_GREEN
        )
        self.summary_label.pack(side="right")

    def refresh_list(self):
        # Clear existing rows
        for child in self.items_scroll.winfo_children():
            child.destroy()

        filter_r = self.filter_rarity_var.get()
        filter_st = self.filter_st_var.get()
        sort_mode = self.sort_var.get()

        # Build list with original indices
        indexed_items = list(enumerate(self.game.inventory))

        # Filter
        filtered = []
        for idx, item in indexed_items:
            if filter_r != "All" and item.rarity != filter_r:
                continue
            if filter_st and not item.is_st:
                continue
            filtered.append((idx, item))

        # Sort
        rarity_ranks = {r: i for i, r in enumerate(config.RARITIES)}
        if sort_mode == "Value: High to Low":
            filtered.sort(key=lambda x: self.game.get_item_value(x[1]), reverse=True)
        elif sort_mode == "Value: Low to High":
            filtered.sort(key=lambda x: self.game.get_item_value(x[1]))
        elif sort_mode == "Rarity (Best First)":
            filtered.sort(key=lambda x: rarity_ranks.get(x[1].rarity, 0), reverse=True)
        elif sort_mode == "Float: Low to High (Best)":
            filtered.sort(key=lambda x: x[1].wear_float)
        elif sort_mode == "Name: A-Z":
            filtered.sort(key=lambda x: x[1].name)

        if not filtered:
            empty_lbl = ctk.CTkLabel(
                self.items_scroll,
                text="No items match your filter criteria.",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=TEXT_MUTED
            )
            empty_lbl.pack(pady=40)
        else:
            for orig_idx, item in filtered:
                self._create_item_row(orig_idx, item)

        # Update summary
        total_items = len(self.game.inventory)
        total_val = sum(self.game.get_item_value(it) for it in self.game.inventory)
        self.summary_label.configure(text=f"Total: {total_items} items  |  Value: ${total_val:,.2f}")

    def _create_item_row(self, orig_idx: int, item):
        val = self.game.get_item_value(item)
        r_color = RARITY_COLORS.get(item.rarity, TEXT_MAIN)

        row_card = ctk.CTkFrame(self.items_scroll, fg_color=CARD_BG, corner_radius=6, height=44)
        row_card.pack(fill="x", pady=2, padx=5)
        row_card.pack_propagate(False)

        # Rarity color strip on left
        strip = ctk.CTkFrame(row_card, fg_color=r_color, width=6, corner_radius=3)
        strip.pack(side="left", fill="y")

        # Item info text
        st_prefix = "★ " if item.is_st else ""
        name_label = ctk.CTkLabel(
            row_card,
            text=f"{st_prefix}{item.name}",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=r_color
        )
        name_label.pack(side="left", padx=(10, 10))

        details_label = ctk.CTkLabel(
            row_card,
            text=f"{item.rarity}  •  {item.quality} ({item.wear_float:.4f})  •  {item.case_name}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=TEXT_MUTED
        )
        details_label.pack(side="left", padx=5)

        # Sell button
        sell_btn = ctk.CTkButton(
            row_card,
            text=f"Sell ${val:,.2f}",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#374151",
            hover_color="#ef4444",
            width=90,
            height=28,
            corner_radius=4,
            command=lambda i=orig_idx: self._sell_single_item(i)
        )
        sell_btn.pack(side="right", padx=10)

    def _sell_single_item(self, index: int):
        val = self.game.sell_item(index)
        if val is not None:
            self.on_state_changed()
            self.game.save()
            self.refresh_list()

    def _bulk_sell(self):
        rarity = self.bulk_rarity_var.get()
        count, total = self.game.sell_all_of_rarity(rarity)
        if count > 0:
            self.on_state_changed()
            self.game.save()
            self.refresh_list()

