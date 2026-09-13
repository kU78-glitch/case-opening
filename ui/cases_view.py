import random
import time
import tkinter as tk
import customtkinter as ctk
from typing import Optional, List, Dict

from cases import (
    CASES, CUSTOM_CASES, load_custom_cases, save_custom_cases,
    delete_custom_case, get_case, get_all_known_items, calculate_custom_case_ev
)
from item_prices import get_item_market_price, BENCHMARK_TIER_PRICES
import config
from models import roll_float, float_to_quality, Item
import image_loader
from ui.theme import (
    PANEL_BG, CARD_BG, ACCENT_BLUE, ACCENT_HOVER, SUCCESS_GREEN,
    TEXT_MAIN, TEXT_MUTED, GOLD_COLOR, RARITY_COLORS
)

class CasesView(ctk.CTkFrame):
    # --- Animation constants ---
    ITEM_WIDTH = 110          # pixel width per item card (CS2-style compact square)
    VISIBLE_RADIUS = 3        # items visible each side of center (3 fits in 680px at 110px each)
    SPIN_ITEM_COUNT = 55      # total fake items in the strip
    ANIM_FPS = 60             # target frames per second
    FRAME_MS = 16             # ms per frame (~60 FPS)


    def __init__(self, master, game, sound_manager, on_state_changed, on_open_inventory=None):
        super().__init__(master, fg_color=PANEL_BG, corner_radius=12)
        self.game = game
        self.sound = sound_manager
        self.on_state_changed = on_state_changed

        # Multi-case selection (1, 2, or 3)
        self.case_count = 1

        # Fast Open / Skip animation flag
        self.skip_animation_var = ctk.BooleanVar(value=False)

        # Continuous pixel-scroll spin state
        self.spin_running = False
        self.spin_sequences: List[List[Dict]] = []
        self.winning_items: List[Item] = []
        self.spin_canvases: List[tk.Canvas] = []

        # Gold bonus re-spin sequential queue for multi-case drops
        self.pending_gold_respins: List[Item] = []

        # Easing animation state (set per spin)
        self._anim_start_time: float = 0.0
        self._anim_duration: float = 0.0
        self._anim_total_px: float = 0.0
        self._anim_scroll_px: float = 0.0
        self._last_tick_item: int = -1   # last item index that crossed center (for tick sync)
        self._anim_target_item: int = 0  # the item index the spin must land on
        self._toast_timer = None
        self._photo_refs: list = []   # prevents GC from dropping canvas PhotoImage objects between frames

        self._build_ui()
        self._setup_spinner_rows(1)
        self.refresh_controls()
        self.update_case_price()

    def _show_toast(self, message: str, color: str = SUCCESS_GREEN, duration_ms: int = 4000):
        """Displays a temporary lightweight toast banner below the control panel."""
        if hasattr(self, "_toast_timer") and self._toast_timer is not None:
            try:
                self.after_cancel(self._toast_timer)
            except Exception:
                pass
        self.rolling_label.configure(text=message, text_color=color, height=26)
        self._toast_timer = self.after(duration_ms, lambda: self.rolling_label.configure(text="", height=0))

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

        # Category Switcher: Official CS2 Cases | Custom Cases | + Create New Case
        cat_frame = ctk.CTkFrame(container, fg_color="transparent")
        cat_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.current_category_var = ctk.StringVar(value="official")

        self.cat_official_btn = ctk.CTkButton(
            cat_frame,
            text="📦 Official Cases",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=ACCENT_BLUE,
            hover_color=ACCENT_HOVER,
            height=32,
            width=150,
            command=lambda: self._set_category("official")
        )
        self.cat_official_btn.pack(side="left", padx=(0, 8))

        self.cat_custom_btn = ctk.CTkButton(
            cat_frame,
            text="🛠️ Custom Cases",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#1e222d",
            hover_color="#2d3342",
            height=32,
            width=150,
            command=lambda: self._set_category("custom")
        )
        self.cat_custom_btn.pack(side="left", padx=(0, 8))

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
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#1e222d",
            button_color=ACCENT_BLUE,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color="#1e222d",
            dropdown_hover_color=ACCENT_HOVER,
            dropdown_text_color=TEXT_MAIN,
            command=lambda _: self.update_case_price()
        )
        self.case_menu.pack(side="left", padx=(0, 10))

        # View Case Drops Preview Pop-up Button
        self.preview_btn = ctk.CTkButton(
            selector_row,
            text="👁️ View Case Drops",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#1e222d",
            hover_color="#2d3342",
            border_width=1,
            border_color="#374151",
            height=34,
            command=self._open_case_drops_modal
        )
        self.preview_btn.pack(side="left", padx=(0, 10))

        # Actions Dropdown Button for Custom Cases (Rename, Edit, Delete)
        self.actions_btn = ctk.CTkButton(
            selector_row,
            text="⚙️ Case Options ▼",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#1e222d",
            hover_color="#2d3342",
            border_width=1,
            border_color="#374151",
            height=34,
            command=self._toggle_actions_menu
        )
        self.actions_btn.pack(side="left", padx=(0, 10))

        self.price_label = ctk.CTkLabel(
            case_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_MUTED
        )
        self.price_label.pack(pady=(0, 8))

        # Action Controls: OPEN CASE + Multi-Count SegmentedButton
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(pady=(4, 8))

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

        # Fast Open / Skip Animation Toggle (only box clickable)
        fast_item = ctk.CTkFrame(btn_row, fg_color="transparent")
        fast_item.pack(side="left", padx=10)

        self.skip_cb = ctk.CTkCheckBox(
            fast_item,
            text="",
            variable=self.skip_animation_var,
            checkmark_color="#000000",
            fg_color="#f59e0b",
            hover_color="#d97706",
            width=22,
            height=22,
            checkbox_width=22,
            checkbox_height=22
        )
        self.skip_cb.pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            fast_item,
            text="⚡ Fast Open",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(side="left")

        # Auto-Sell Rarity Filter Checkboxes Row
        auto_sell_row = ctk.CTkFrame(container, fg_color="transparent")
        auto_sell_row.pack(pady=(0, 6))

        ctk.CTkLabel(
            auto_sell_row,
            text="Auto-Sell:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_MUTED
        ).pack(side="left", padx=(0, 8))

        self.auto_sell_vars = {}
        auto_sell_tiers = [
            ("Mil-Spec", "Mil-Spec", "#4b69ff"),
            ("Restricted", "Restricted", "#8847ff"),
            ("Classified", "Classified", "#d32ce6"),
            ("Covert", "Covert", "#eb4b4b"),
        ]

        for rarity, label, color in auto_sell_tiers:
            var = ctk.BooleanVar(value=bool(self.game.auto_sell.get(rarity, False)))
            self.auto_sell_vars[rarity] = var

            def make_toggle(r_name=rarity, r_var=var):
                def toggle():
                    self.game.auto_sell[r_name] = r_var.get()
                    self.game.save()
                return toggle

            tier_item = ctk.CTkFrame(auto_sell_row, fg_color="transparent")
            tier_item.pack(side="left", padx=8)

            cb = ctk.CTkCheckBox(
                tier_item,
                text="",
                variable=var,
                command=make_toggle(rarity, var),
                fg_color=color,
                hover_color=color,
                border_color=color,
                checkmark_color="#ffffff",
                width=22,
                height=22,
                checkbox_width=22,
                checkbox_height=22
            )
            cb.pack(side="left", padx=(0, 5))

            ctk.CTkLabel(
                tier_item,
                text=f"Auto-Sell {label}",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=color
            ).pack(side="left")

        # Lightweight Status Notification / Toast Label
        self.rolling_label = ctk.CTkLabel(
            container,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=SUCCESS_GREEN,
            height=0
        )
        self.rolling_label.pack(pady=(0, 4))

        # Dynamic Stacked Spinners Container
        self.spinner_card = ctk.CTkFrame(container, fg_color="#0b0d11", corner_radius=10)
        self.spinner_card.pack(fill="x", padx=10, pady=6)

        self.canvases_frame = ctk.CTkFrame(self.spinner_card, fg_color="transparent")
        self.canvases_frame.pack(fill="both", expand=True, padx=8, pady=8)

    def _open_case_drops_modal(self):
        """Displays a dedicated pop-up modal showing all items and odds in the current case."""
        case_name = self.selected_case_var.get()
        case_data = get_case(case_name)
        if not case_data or "items" not in case_data:
            return

        if hasattr(self, "_drops_modal") and self._drops_modal is not None and self._drops_modal.winfo_exists():
            self._drops_modal.destroy()

        self._drops_modal = ctk.CTkFrame(
            self,
            fg_color="#0d0f17",
            border_width=2,
            border_color=ACCENT_BLUE,
            corner_radius=14
        )
        self._drops_modal.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.82, relheight=0.84)
        self._drops_modal.lift()

        # Modal Header
        m_top = ctk.CTkFrame(self._drops_modal, fg_color="transparent")
        m_top.pack(fill="x", padx=18, pady=(14, 8))

        ctk.CTkLabel(
            m_top,
            text=f"🔍 Drops Preview: {case_name}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(side="left")

        close_m_btn = ctk.CTkButton(
            m_top,
            text="✕ Close",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            width=80,
            height=28,
            corner_radius=6,
            command=self._drops_modal.destroy
        )
        close_m_btn.pack(side="right")

        # Scrollable container for item cards
        scroll_container = ctk.CTkScrollableFrame(
            self._drops_modal,
            fg_color="transparent"
        )
        scroll_container.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        # Flatten items grouped from highest rarity to lowest
        items_by_rarity = case_data.get("items", {})
        display_items = []
        for rarity in reversed(config.RARITIES):
            pool = items_by_rarity.get(rarity, [])
            for entry in pool:
                name = entry[0] if isinstance(entry, (list, tuple)) else entry
                color = entry[1] if isinstance(entry, (list, tuple)) and len(entry) > 1 else "blue"
                display_items.append((name, rarity, color))

        num_cols = 5
        for col_idx in range(num_cols):
            scroll_container.grid_columnconfigure(col_idx, weight=1, uniform="modal_prev_col")

        for idx, (name, rarity, color) in enumerate(display_items):
            r_border_color = RARITY_COLORS.get(rarity, "#4b69ff")
            price = get_item_market_price(name, rarity)

            card = ctk.CTkFrame(
                scroll_container,
                fg_color="#181c26",
                border_width=2,
                border_color=r_border_color,
                corner_radius=8
            )
            row = idx // num_cols
            col = idx % num_cols
            card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

            img = image_loader.get_skin_image(name, rarity=rarity, size=(90, 68))
            img_lbl = ctk.CTkLabel(card, text="", image=img)
            img_lbl.pack(pady=(4, 2))

            clean_name = name.split("|")[-1].strip() if "|" in name else name
            clean_name = clean_name[:16]
            ctk.CTkLabel(
                card,
                text=clean_name,
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color=TEXT_MAIN
            ).pack(padx=2)

            ctk.CTkLabel(
                card,
                text=f"${price:,.2f}",
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color=r_border_color
            ).pack(pady=(0, 4))

    def _update_case_preview(self, case_name: str):
        """No-op or updates active preview modal if currently visible."""
        if hasattr(self, "_drops_modal") and self._drops_modal is not None and self._drops_modal.winfo_exists():
            self._open_case_drops_modal()

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

        if hasattr(self, "auto_sell_vars"):
            for rarity, var in self.auto_sell_vars.items():
                var.set(bool(self.game.auto_sell.get(rarity, False)))

    def _on_count_selected(self, value: str):
        target_count = int(value.replace("x", ""))
        max_allowed = self._get_max_unlocked_cases()

        if target_count > max_allowed:
            req_prestige = 1 if target_count == 2 else 2
            self._show_toast(
                f"🔒 {target_count}x Multi-Case unlocks at Prestige {req_prestige}!",
                GOLD_COLOR
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

        # Canvas heights based on count — match ITEM_WIDTH for square CS2-style cards
        if count == 1:
            row_height = 110
            pady = 2
        elif count == 2:
            row_height = 100
            pady = 2
        else:
            row_height = 90
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

    def _set_category(self, category: str):
        """Switches between Official CS2 Cases and Custom Cases without affecting state."""
        self._close_actions_menu()
        self.current_category_var.set(category)
        if category == "official":
            self.cat_official_btn.configure(fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER)
            self.cat_custom_btn.configure(fg_color="#1e222d", hover_color="#2d3342")
            case_list = list(CASES.keys())
        else:
            self.cat_official_btn.configure(fg_color="#1e222d", hover_color="#2d3342")
            self.cat_custom_btn.configure(fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER)
            custom_dict = load_custom_cases()
            case_list = list(custom_dict.keys())
            if not case_list:
                case_list = ["(No Custom Cases)"]

        self.case_menu.configure(values=case_list)
        if case_list:
            self.selected_case_var.set(case_list[0])
        self.update_case_price()

    def _open_case_creator_studio(self):
        """Opens the in-window Custom Case Creator Studio overlay."""
        if hasattr(self, "creator_modal") and self.creator_modal is not None and self.creator_modal.winfo_exists():
            self.creator_modal.destroy()

        known_items = get_all_known_items()

        # In-window overlay modal
        self.creator_modal = ctk.CTkFrame(
            self,
            fg_color="#11131a",
            border_width=2,
            border_color=ACCENT_BLUE,
            corner_radius=14
        )
        self.creator_modal.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.90)

        # Header
        top_bar = ctk.CTkFrame(self.creator_modal, fg_color="transparent")
        top_bar.pack(fill="x", padx=20, pady=(14, 8))

        ctk.CTkLabel(
            top_bar,
            text="🛠️ Custom Case Creator Studio",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_MAIN
        ).pack(side="left")

        close_btn = ctk.CTkButton(
            top_bar,
            text="✕ Close",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            width=70,
            height=28,
            command=self.creator_modal.destroy
        )
        close_btn.pack(side="right")

        # Config Inputs & Summary Row
        top_container = ctk.CTkFrame(self.creator_modal, fg_color="transparent")
        top_container.pack(fill="x", padx=20, pady=(0, 10))

        # Left Card: Case Name + House Margin Selector
        left_card = ctk.CTkFrame(top_container, fg_color=CARD_BG, corner_radius=8)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        name_row = ctk.CTkFrame(left_card, fg_color="transparent")
        name_row.pack(fill="x", padx=15, pady=(10, 6))
        ctk.CTkLabel(name_row, text="Case Name:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        case_name_entry = ctk.CTkEntry(name_row, width=180, font=ctk.CTkFont(family="Segoe UI", size=12), placeholder_text="e.g. Cyberpunk Case")
        case_name_entry.pack(side="left")

        # House Margin Selector Row
        margin_row = ctk.CTkFrame(left_card, fg_color="transparent")
        margin_row.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(margin_row, text="House Margin:", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))

        self.margin_val_var = ctk.StringVar(value="10% (Standard)")
        margin_dropdown = ctk.CTkOptionMenu(
            margin_row,
            variable=self.margin_val_var,
            values=["0% (Fair/Zero-Edge)", "5% (Low Edge)", "10% (Standard)", "15% (High Edge)", "20% (Casino Degen)"],
            width=180,
            height=28,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            command=lambda _: update_live_ev()
        )
        margin_dropdown.set("10% (Standard)")
        margin_dropdown.pack(side="left")

        # Right Card: Expanded Price Breakdown Panel
        breakdown_card = ctk.CTkFrame(top_container, fg_color="#141721", corner_radius=8, border_width=1, border_color="#2b3245")
        breakdown_card.pack(side="right", fill="both", expand=True)

        bd_top = ctk.CTkFrame(breakdown_card, fg_color="transparent")
        bd_top.pack(fill="x", padx=12, pady=(8, 2))

        case_price_label = ctk.CTkLabel(
            bd_top,
            text="💰 Calculated Case Price: $0.00",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=GOLD_COLOR
        )
        case_price_label.pack(side="left")

        volatility_label = ctk.CTkLabel(
            bd_top,
            text="🛡️ Safe / Low Risk",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#38bdf8"
        )
        volatility_label.pack(side="right")

        calc_summary_label = ctk.CTkLabel(
            breakdown_card,
            text="Base EV: $0.00 + 10% House Margin = $0.00 Final Price",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#93c5fd"
        )
        calc_summary_label.pack(fill="x", padx=12, pady=(0, 2), anchor="w")

        tier_breakdown_label = ctk.CTkLabel(
            breakdown_card,
            text="Tier Breakdown: Loading...",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=TEXT_MUTED
        )
        tier_breakdown_label.pack(fill="x", padx=12, pady=(0, 6), anchor="w")

        # Static Item Selection Container (No scrollable canvas, completely eliminating ghosting)
        items_container = ctk.CTkFrame(self.creator_modal, fg_color="#0e1017", corner_radius=8)
        items_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Tier Tab Switcher: Mil-Spec, Restricted, Classified, Covert, Rare Special
        tab_nav_frame = ctk.CTkFrame(items_container, fg_color="#141721", corner_radius=6)
        tab_nav_frame.pack(fill="x", padx=10, pady=(10, 8))

        active_tab_var = ctk.StringVar(value="Mil-Spec")
        tier_frames = {}
        tab_buttons = {}

        selected_items_by_rarity = {r: set() for r in config.RARITIES}
        current_case_price = [0.0]
        current_scaled_odds = [dict(config.RARITY_CHANCES)]

        # Bottom Bar: Status + Save Case Button
        bot_bar = ctk.CTkFrame(self.creator_modal, fg_color="transparent")
        bot_bar.pack(fill="x", padx=20, pady=(0, 14))

        status_lbl = ctk.CTkLabel(
            bot_bar,
            text="Select at least 1 item for each rarity tier to create your custom case.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED
        )
        status_lbl.pack(side="left")

        def save_new_case():
            name = case_name_entry.get().strip()
            if not name:
                status_lbl.configure(text="Please enter a case name!", text_color="#ef4444")
                return

            if name in CASES:
                status_lbl.configure(text="Cannot overwrite official CS2 cases!", text_color="#ef4444")
                return

            price = current_case_price[0]
            if price <= 0.0:
                status_lbl.configure(text="Cannot save a free/zero-value case!", text_color="#ef4444")
                return

            all_tiers_filled = all(len(selected_items_by_rarity[r]) > 0 for r in config.RARITIES)
            if not all_tiers_filled:
                status_lbl.configure(text="Please select at least one item for all rarity tiers!", text_color="#ef4444")
                return

            custom_dict = load_custom_cases()
            custom_dict[name] = {
                "price": price,
                "multiplier": 1.2,
                "odds": current_scaled_odds[0],
                "items": {r: list(selected_items_by_rarity[r]) for r in config.RARITIES}
            }
            save_custom_cases(custom_dict)

            # Switch category to custom and select the new case
            self.creator_modal.destroy()
            self._set_category("custom")
            self.selected_case_var.set(name)
            self.update_case_price()
            self.rolling_label.configure(
                text=f"🎉 Custom Case '{name}' created with EV-balanced price (${price:.2f})!",
                text_color=SUCCESS_GREEN
            )

        save_btn = ctk.CTkButton(
            bot_bar,
            text="💾 SAVE & CREATE CASE",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=SUCCESS_GREEN,
            hover_color="#059669",
            height=36,
            command=save_new_case
        )
        save_btn.pack(side="right")

        def get_current_margin_multiplier() -> tuple[float, int]:
            val_str = self.margin_val_var.get()
            if "0%" in val_str:
                return 1.00, 0
            elif "5%" in val_str:
                return 1.05, 5
            elif "15%" in val_str:
                return 1.15, 15
            elif "20%" in val_str:
                return 1.20, 20
            return 1.10, 10

        def update_live_ev():
            """Recalculates EV dynamically based on individual item valuations and scaled drop odds."""
            margin_mult, margin_pct = get_current_margin_multiplier()
            case_items_dict = {r: list(selected_items_by_rarity[r]) for r in config.RARITIES}
            base_ev, final_price, contributions, risk_str, scaled_odds = calculate_custom_case_ev(case_items_dict, margin_multiplier=margin_mult)
            current_case_price[0] = final_price
            current_scaled_odds[0] = scaled_odds

            case_price_label.configure(text=f"💰 Case Price: ${final_price:.2f}")
            volatility_label.configure(text=risk_str)
            calc_summary_label.configure(
                text=f"Base EV: ${base_ev:.2f} + {margin_pct}% House Margin = ${final_price:.2f} Final Price"
            )

            # Update tab badge labels with selection counts
            for r in config.RARITIES:
                cnt = len(selected_items_by_rarity[r])
                btn = tab_buttons.get(r)
                if btn:
                    short = r.replace("Rare Special", "★ Gold")
                    if cnt > 0:
                        btn.configure(text=f"{short} ({cnt})")
                    else:
                        btn.configure(text=f"{short} (0)")

            # Build readable tier contributions string with dynamically scaled odds percentages
            bd_parts = []
            for r in config.RARITIES:
                c_val = contributions.get(r, 0.0)
                odds_pct = scaled_odds.get(r, 0.0) * 100.0
                short_name = r.replace("Rare Special", "Gold").replace("Mil-Spec", "Blue")
                if odds_pct < 0.01:
                    odds_fmt = f"{odds_pct:.4f}%"
                elif odds_pct < 0.1:
                    odds_fmt = f"{odds_pct:.3f}%"
                else:
                    odds_fmt = f"{odds_pct:.2f}%"
                bd_parts.append(f"{short_name} ({odds_fmt}): +${c_val:.2f}")
            tier_breakdown_label.configure(text="  |  ".join(bd_parts))

            # Check if all rarities have at least 1 item selected
            all_tiers_filled = all(len(selected_items_by_rarity[r]) > 0 for r in config.RARITIES)
            if final_price > 0.0 and all_tiers_filled:
                save_btn.configure(state="normal", fg_color=SUCCESS_GREEN)
                status_lbl.configure(
                    text=f"All tiers configured. Automated Case Price is set to ${final_price:.2f}.",
                    text_color=SUCCESS_GREEN
                )
            else:
                save_btn.configure(state="disabled", fg_color="#374151")
                missing = [r for r in config.RARITIES if len(selected_items_by_rarity[r]) == 0]
                if missing:
                    status_lbl.configure(
                        text=f"Pick at least 1 item for: {', '.join(missing)}",
                        text_color=TEXT_MUTED
                    )
                else:
                    status_lbl.configure(
                        text="Pick items to calculate case price.",
                        text_color=TEXT_MUTED
                    )

        # Tab content container (grid stacking)
        content_host = ctk.CTkFrame(items_container, fg_color="transparent")
        content_host.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        content_host.grid_rowconfigure(0, weight=1)
        content_host.grid_columnconfigure(0, weight=1)

        def switch_tab(target_rarity: str):
            active_tab_var.set(target_rarity)
            for r, frame in tier_frames.items():
                if r == target_rarity:
                    frame.grid(row=0, column=0, sticky="nsew")
                else:
                    frame.grid_remove()
            for r, btn in tab_buttons.items():
                if r == target_rarity:
                    r_color = RARITY_COLORS.get(r, ACCENT_BLUE)
                    btn.configure(fg_color=r_color, text_color="#ffffff" if r != "Mil-Spec" else "#111827")
                else:
                    btn.configure(fg_color="#1a1d27", text_color="#9ca3af")

        # Build each tier tab statically
        for rarity in config.RARITIES:
            r_color = RARITY_COLORS.get(rarity, TEXT_MAIN)
            tier_benchmark = BENCHMARK_TIER_PRICES.get(rarity, 5.0)

            # Tab button
            tab_btn = ctk.CTkButton(
                tab_nav_frame,
                text=rarity.replace("Rare Special", "★ Gold"),
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="#1a1d27",
                hover_color="#262b3a",
                height=30,
                corner_radius=6,
                command=lambda r=rarity: switch_tab(r)
            )
            tab_btn.pack(side="left", padx=4, pady=4, expand=True, fill="x")
            tab_buttons[rarity] = tab_btn

            # Tab Content Frame
            tf = ctk.CTkFrame(content_host, fg_color="#12151c", corner_radius=8)
            tier_frames[rarity] = tf

            # Tier info banner
            info_bar = ctk.CTkFrame(tf, fg_color="#181c26", corner_radius=6, height=32)
            info_bar.pack(fill="x", padx=10, pady=(10, 8))
            info_bar.pack_propagate(False)

            ctk.CTkLabel(
                info_bar,
                text=f"● {rarity} Drop Pool",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=r_color
            ).pack(side="left", padx=12)

            ctk.CTkLabel(
                info_bar,
                text=f"Tier Market Baseline: ${tier_benchmark:.2f}  |  Select skins to include in this tier's drop table",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=TEXT_MUTED
            ).pack(side="right", padx=12)

            # Static Grid of Item Checkboxes (3 columns x 4 rows = 12 items fits without scrolling)
            grid_frame = ctk.CTkFrame(tf, fg_color="transparent")
            grid_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            for c in range(3):
                grid_frame.grid_columnconfigure(c, weight=1, uniform="tier_col")

            pool = known_items.get(rarity, [])
            for idx, (skin_name, color) in enumerate(pool[:15]):
                skin_price = get_item_market_price(skin_name, rarity)
                cb_var = ctk.BooleanVar(value=(idx < 2))
                if cb_var.get():
                    selected_items_by_rarity[rarity].add((skin_name, color))

                def make_toggle(r, s, c, v):
                    def toggle():
                        if v.get():
                            selected_items_by_rarity[r].add((s, c))
                        else:
                            selected_items_by_rarity[r].discard((s, c))
                        update_live_ev()
                    return toggle

                price_tag = f"(${skin_price:.2f})"
                full_display_text = f"{skin_name} {price_tag}"

                if skin_price >= 200.0:
                    badge_color = "#f59e0b"
                elif skin_price >= 50.0:
                    badge_color = "#38bdf8"
                elif skin_price >= 10.0:
                    badge_color = "#10b981"
                else:
                    badge_color = "#d1d5db"

                # Solid background cell
                row = idx // 3
                col = idx % 3
                cell = ctk.CTkFrame(grid_frame, fg_color="#181c26", corner_radius=6, height=36)
                cell.grid(row=row, column=col, sticky="ew", padx=5, pady=4)
                cell.pack_propagate(False)

                cb = ctk.CTkCheckBox(
                    cell,
                    text=full_display_text,
                    variable=cb_var,
                    font=ctk.CTkFont(family="Segoe UI", size=11),
                    text_color=badge_color,
                    fg_color="#3b82f6",
                    hover_color="#2563eb",
                    checkbox_height=16,
                    checkbox_width=16,
                    corner_radius=3,
                    command=make_toggle(rarity, skin_name, color, cb_var)
                )
                cb.pack(side="left", padx=8, pady=4, fill="x", expand=True)

        # Show initial tab
        switch_tab("Mil-Spec")

        # Initialize dynamic calculation
        update_live_ev()

    def _on_auto_sell_toggle(self, rarity: str, var: ctk.BooleanVar):
        self.game.auto_sell[rarity] = var.get()
        self.game.save()

    def update_case_price(self):
        self._close_actions_menu()
        case_name = self.selected_case_var.get()
        case_data = get_case(case_name)
        if not case_data:
            if hasattr(self, "current_category_var") and self.current_category_var.get() == "custom":
                self.price_label.configure(text="No custom cases available. Click '⋮' to create one!")
            else:
                self.price_label.configure(text="")
            if hasattr(self, "open_btn"):
                self.open_btn.configure(state="disabled")
            return

        if hasattr(self, "open_btn"):
            self.open_btn.configure(state="normal")

        case_price = round(float(case_data["price"]), 2)
        key_price = config.KEY_PRICE
        single_cost = round(case_price + key_price, 2)
        total_cost = round(single_cost * self.case_count, 2)

        if self.case_count == 1:
            self.price_label.configure(
                text=f"Case: ${case_price:.2f} + Key: ${key_price:.2f}  |  Total: ${single_cost:.2f}"
            )
        else:
            self.price_label.configure(
                text=f"Case: ${case_price:.2f} + Key: ${key_price:.2f} (${single_cost:.2f}/ea)  |  Total ({self.case_count}x): ${total_cost:.2f}"
            )

        # Refresh the Case Drops Preview Grid
        if hasattr(self, "preview_grid_frame"):
            self._update_case_preview(case_name)

    def _toggle_actions_menu(self):
        """Opens or closes the compact context menu for case actions (⋮)."""
        if hasattr(self, "_actions_menu_frame") and self._actions_menu_frame is not None and self._actions_menu_frame.winfo_exists():
            if self._actions_menu_frame.winfo_ismapped():
                self._close_actions_menu()
                return
        self._open_actions_menu()

    def _open_actions_menu(self):
        """Builds and displays the context menu dropdown beneath the ⋮ button."""
        if not hasattr(self, "_actions_menu_frame") or self._actions_menu_frame is None or not self._actions_menu_frame.winfo_exists():
            self._actions_menu_frame = ctk.CTkFrame(
                self,
                fg_color="#181b24",
                border_width=1,
                border_color="#2d3342",
                corner_radius=8
            )
            # Bind global click listener to dismiss menu when clicking outside
            try:
                self.winfo_toplevel().bind("<Button-1>", self._on_root_click_actions, add="+")
            except Exception:
                pass

        # Clear existing menu items
        for child in self._actions_menu_frame.winfo_children():
            child.destroy()

        case_name = self.selected_case_var.get()
        is_custom = (
            hasattr(self, "current_category_var")
            and self.current_category_var.get() == "custom"
            and bool(case_name)
            and case_name != "(No Custom Cases)"
            and case_name not in CASES
        )

        # 1. ➕ Create New Case (Always visible)
        create_btn = ctk.CTkButton(
            self._actions_menu_frame,
            text="➕  Create New Case",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="transparent",
            hover_color="#252a37",
            text_color="#f3f4f6",
            anchor="w",
            height=30,
            width=164,
            corner_radius=6,
            command=self._on_action_create_case
        )
        create_btn.pack(fill="x", padx=6, pady=(6, 4) if is_custom else (6, 6))

        # 2. 🗑️ Delete Case (ONLY visible for Custom Cases)
        if is_custom:
            sep = ctk.CTkFrame(self._actions_menu_frame, height=1, fg_color="#2d3342")
            sep.pack(fill="x", padx=6, pady=2)

            del_btn = ctk.CTkButton(
                self._actions_menu_frame,
                text="🗑️  Delete Case",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                fg_color="transparent",
                hover_color="#3b1114",
                text_color="#ef4444",
                anchor="w",
                height=30,
                width=164,
                corner_radius=6,
                command=self._on_action_delete_case
            )
            del_btn.pack(fill="x", padx=6, pady=(2, 6))

        # Calculate position relative to self (CasesView)
        self.update_idletasks()
        bx = self.actions_btn.winfo_rootx() - self.winfo_rootx()
        by = self.actions_btn.winfo_rooty() - self.winfo_rooty() + self.actions_btn.winfo_height() + 4

        menu_w = 176
        if bx + menu_w > self.winfo_width() - 10:
            bx = max(10, (self.actions_btn.winfo_rootx() - self.winfo_rootx() + self.actions_btn.winfo_width()) - menu_w)

        self._actions_menu_frame.place(x=bx, y=by)
        self._actions_menu_frame.lift()

    def _on_action_create_case(self):
        self._close_actions_menu()
        self._open_case_creator_studio()

    def _on_action_delete_case(self):
        self._close_actions_menu()
        self._confirm_delete_custom_case()

    def _close_actions_menu(self):
        if hasattr(self, "_actions_menu_frame") and self._actions_menu_frame is not None and self._actions_menu_frame.winfo_exists():
            if self._actions_menu_frame.winfo_ismapped():
                self._actions_menu_frame.place_forget()

    def _on_root_click_actions(self, event):
        if not hasattr(self, "_actions_menu_frame") or self._actions_menu_frame is None or not self._actions_menu_frame.winfo_exists():
            return
        if not self._actions_menu_frame.winfo_ismapped():
            return
        try:
            x, y = event.x_root, event.y_root
            bx1 = self.actions_btn.winfo_rootx()
            by1 = self.actions_btn.winfo_rooty()
            bx2 = bx1 + self.actions_btn.winfo_width()
            by2 = by1 + self.actions_btn.winfo_height()
            if bx1 <= x <= bx2 and by1 <= y <= by2:
                return

            mx1 = self._actions_menu_frame.winfo_rootx()
            my1 = self._actions_menu_frame.winfo_rooty()
            mx2 = mx1 + self._actions_menu_frame.winfo_width()
            my2 = my1 + self._actions_menu_frame.winfo_height()
            if not (mx1 <= x <= mx2 and my1 <= y <= my2):
                self._close_actions_menu()
        except Exception:
            pass

    def _confirm_delete_custom_case(self):
        """Displays a confirmation modal before deleting a custom case."""
        case_name = self.selected_case_var.get()
        if not case_name or case_name in CASES or case_name == "(No Custom Cases)":
            return

        if hasattr(self, "_delete_modal") and self._delete_modal is not None and self._delete_modal.winfo_exists():
            self._delete_modal.destroy()

        self._delete_modal = ctk.CTkFrame(
            self,
            fg_color="#11131a",
            border_width=2,
            border_color="#ef4444",
            corner_radius=14
        )
        self._delete_modal.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.52, relheight=0.32)

        ctk.CTkLabel(
            self._delete_modal,
            text="⚠️ Confirm Delete Case",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color="#ef4444"
        ).pack(pady=(18, 8))

        ctk.CTkLabel(
            self._delete_modal,
            text=f"Are you sure you want to delete '{case_name}'?\nThis action cannot be undone.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=TEXT_MAIN,
            justify="center"
        ).pack(pady=(0, 16), padx=20)

        btn_box = ctk.CTkFrame(self._delete_modal, fg_color="transparent")
        btn_box.pack(pady=(0, 12))

        cancel_btn = ctk.CTkButton(
            btn_box,
            text="Cancel",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#374151",
            hover_color="#4b5563",
            width=100,
            height=32,
            command=self._delete_modal.destroy
        )
        cancel_btn.pack(side="left", padx=8)

        delete_btn = ctk.CTkButton(
            btn_box,
            text="Delete Case",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            width=110,
            height=32,
            command=lambda: self._do_delete_custom_case(case_name)
        )
        delete_btn.pack(side="left", padx=8)

    def _do_delete_custom_case(self, case_name: str):
        """Executes deletion of the custom case and refreshes the CasesView dynamically."""
        if hasattr(self, "_delete_modal") and self._delete_modal is not None and self._delete_modal.winfo_exists():
            self._delete_modal.destroy()

        success = delete_custom_case(case_name)
        if success:
            custom_dict = load_custom_cases()
            case_list = list(custom_dict.keys())
            if not case_list:
                case_list = ["(No Custom Cases)"]
            self.case_menu.configure(values=case_list)
            self.selected_case_var.set(case_list[0])
            self.update_case_price()
            self.rolling_label.configure(
                text=f"🗑️ Custom Case '{case_name}' was permanently deleted.",
                text_color="#ef4444"
            )
        else:
            self.rolling_label.configure(
                text=f"Error: Could not delete '{case_name}'.",
                text_color="#ef4444"
            )

    def start_cases(self):
        if self.spin_running:
            return

        case_name = self.selected_case_var.get()
        case_data = get_case(case_name)
        if not case_data:
            return

        single_cost = round(float(case_data["price"]) + config.KEY_PRICE, 2)
        total_cost = round(single_cost * self.case_count, 2)

        if self.game.balance < total_cost:
            self._show_toast(
                f"⚠️ Insufficient balance! Need ${total_cost:.2f} to open {self.case_count} cases.",
                "#ef4444"
            )
            return

        # Open items with delayed stats (so achievements and inventory commits wait for spin reveal)
        self.winning_items = []
        for _ in range(self.case_count):
            item = self.game.open_case(case_name, delay_stats=True)
            if item:
                self.winning_items.append(item)

        if len(self.winning_items) != self.case_count:
            self._show_toast("Error generating drops!", "#ef4444")
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
        self.rolling_label.configure(text="", height=0)

        case_data = get_case(case_name)
        if not case_data:
            self.open_btn.configure(state="normal")
            self.seg_button.configure(state="normal")
            self.case_menu.configure(state="normal")
            self.spin_running = False
            return

        items = case_data["items"]
        case_multiplier = float(case_data.get("multiplier", 1.0))

        fake_count = self.SPIN_ITEM_COUNT
        self.spin_sequences = []

        # Realistic CS2 visual filler weights (heavily blue-dominated)
        _FILLER_WEIGHTS = {
            "Mil-Spec": 80.0,
            "Restricted": 15.0,
            "Classified": 4.0,
            "Covert": 0.8,
            "Rare Special": 0.2,
        }
        # Build weighted pool from rarities that exist in this case
        available_rarities = [r for r in _FILLER_WEIGHTS if r in items and items[r]]
        filler_weights = [_FILLER_WEIGHTS[r] for r in available_rarities]

        for row_idx, winning_item in enumerate(self.winning_items):
            row_seq = []
            for _ in range(fake_count):
                rf = random.choices(available_rarities, weights=filler_weights, k=1)[0]
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

            win_idx = fake_count - self.VISIBLE_RADIUS - 1
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

        # Target: scroll so that win_idx is centered, plus a random inner offset
        # for CS2-style "near-miss" suspense landing
        self._anim_target_item = fake_count - self.VISIBLE_RADIUS - 1
        # Random offset within the winning item's card bounds (card is ±38px from center)
        card_half_w = 38
        margin = 8  # safety margin from card edge
        max_shift = card_half_w - margin  # 30px max shift in either direction
        landing_offset = random.uniform(-max_shift, max_shift)
        # Total pixel distance: item center + random offset within card
        self._anim_total_px = float(self._anim_target_item * self.ITEM_WIDTH) + landing_offset
        self._anim_scroll_px = 0.0
        self._last_tick_item = -1

        # Animation duration: ~4 seconds base, or ~1.6s if Fast Open is enabled (2.5x faster), reduced by spin_speed perk
        is_fast_open = self.skip_animation_var.get()
        base_duration = 1.6 if is_fast_open else 4.0
        speed_mult = 1.0 + self.game.perks.get("spin_speed", 0.0)
        self._anim_duration = max(0.5, base_duration / speed_mult)
        self._anim_start_time = time.monotonic()

        self._spin_step()

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Cubic ease-out: fast start, smooth deceleration."""
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out for smooth snap-back recoil."""
        if t < 0.5:
            return 2.0 * t * t
        return 1.0 - (-2.0 * t + 2.0) ** 2 / 2.0

    def _render_at_scroll(self, scroll_px: float):
        """Render all spinner row canvases at the given pixel scroll position."""
        current_center_item = int(scroll_px / self.ITEM_WIDTH)
        sub_pixel_offset = scroll_px - (current_center_item * self.ITEM_WIDTH)

        canvas_center_x = 340
        item_w = self.ITEM_WIDTH
        vis_r = self.VISIBLE_RADIUS

        # Reset per-frame photo refs to prevent GC from dropping canvas images
        self._photo_refs = []

        for row_idx, canvas in enumerate(self.spin_canvases):
            if row_idx >= len(self.spin_sequences):
                continue

            seq = self.spin_sequences[row_idx]
            canvas.delete("all")
            h = int(canvas.cget("height"))
            center_y = h // 2
            # Square card: use (h//2 - 4) so card height = h - 8 (fills canvas)
            card_half_h = h // 2 - 4

            # Draw items from (center - radius - 1) to (center + radius + 1) for smooth edges
            for offset in range(-vis_r - 1, vis_r + 2):
                idx = current_center_item + offset
                if 0 <= idx < len(seq):
                    item = seq[idx]
                    x = canvas_center_x + offset * item_w - sub_pixel_offset

                    if x < -item_w or x > 680 + item_w:
                        continue

                    y = center_y
                    is_gold = item.get("rarity") == "Rare Special"
                    rarity_color = RARITY_COLORS.get(item["rarity"], "#444444")

                    is_center = abs(x - canvas_center_x) < item_w * 0.5

                    # Card half-width: leave 3px gap between cards (item_w=110, card 104px wide)
                    card_w = item_w // 2 - 3
                    card_top = y - card_half_h
                    card_bot = y + card_half_h

                    if is_gold:
                        outline = "#ffe566" if is_center else "#d4af37"
                        bdr_w   = 3 if is_center else 2
                        # Dark gold fill with inner shimmer
                        canvas.create_rectangle(x - card_w, card_top, x + card_w, card_bot,
                                                fill="#2e1c00", outline=outline, width=bdr_w)
                        canvas.create_rectangle(x - card_w + 3, card_top + 3,
                                                x + card_w - 3, card_bot - 3,
                                                fill="#4a2e00", outline="")
                        # Gold shimmer strip at top
                        canvas.create_rectangle(x - card_w + 3, card_top + 3,
                                                x + card_w - 3, card_top + 8,
                                                fill="#b8860b", outline="")
                    else:
                        outline = "#fbbf24" if is_center else "#1e2433"
                        bdr_w   = 3 if is_center else 1
                        # Dark card body
                        canvas.create_rectangle(x - card_w, card_top, x + card_w, card_bot,
                                                fill="#12151e", outline=outline, width=bdr_w)
                        # Bottom rarity accent bar (6px tall)
                        canvas.create_rectangle(x - card_w, card_bot - 6, x + card_w, card_bot,
                                                fill=rarity_color, outline="")

                    # --- Image (fills upper ~75% of card, leaves ~25% for label) ---
                    # Card inner height = 2*(card_half_h) px.  Image takes (h-8 - label_h) of that.
                    label_h = 18   # pixels reserved for text at the bottom
                    img_h = max(30, card_half_h * 2 - label_h - 4)
                    img_w = max(50, card_w * 2 - 8)
                    img_size = (img_w, img_h)

                    # Image center: (card_top + 4 + img_h/2) → shifted so image + label fit inside card
                    img_cy = card_top + 4 + img_h // 2

                    if is_gold:
                        photo = image_loader.get_gold_special_tk_photo(size=img_size)
                        label_text = "* GOLD *"
                        text_fill  = "#ffd700"
                    else:
                        skin_part  = item['name'].split("|")[-1].strip() if "|" in item['name'] else item['name']
                        st_mark    = "[ST] " if item.get("is_st") else ""
                        label_text = f"{st_mark}{skin_part[:14]}"
                        photo = image_loader.get_tk_photo_image(item['name'], rarity=item['rarity'], size=img_size)
                        text_fill  = "#e8eaf0"

                    if photo:
                        self._photo_refs.append(photo)   # keep alive — prevents GC
                        canvas.create_image(x, img_cy, image=photo)

                    # Label at the bottom of card (inside the accent bar area for non-gold)
                    canvas.create_text(
                        x, card_bot - label_h // 2 - 2,
                        text=label_text, fill=text_fill,
                        font=("Segoe UI", 8, "bold"), width=card_w * 2 - 6
                    )

            # Center indicator line (golden ticker)
            canvas.create_line(canvas_center_x, 0, canvas_center_x, h, fill="#fbbf24", width=2)



    def _spin_step(self):
        now = time.monotonic()
        elapsed = now - self._anim_start_time
        t = min(elapsed / self._anim_duration, 1.0)

        # Apply ease-out curve to get scroll progress 0..1
        progress = self._ease_out_cubic(t)
        self._anim_scroll_px = progress * self._anim_total_px

        # Play tick sound when a new item boundary crosses the center
        current_center_item = int(self._anim_scroll_px / self.ITEM_WIDTH)
        if current_center_item != self._last_tick_item and t < 1.0:
            self.sound.play_tick()
            self._last_tick_item = current_center_item

        # Render
        self._render_at_scroll(self._anim_scroll_px)

        # Continue main spin or start snap-back sequence
        if t < 1.0:
            self.after(self.FRAME_MS, self._spin_step)
        else:
            # Main spin done — render final offset position, then start snap-back after suspense pause
            self._anim_scroll_px = self._anim_total_px
            self._render_at_scroll(self._anim_scroll_px)

            # Snap-back: recoil from the random landing offset to exact item center
            is_fast_open = self.skip_animation_var.get()
            self._snap_from_px = self._anim_total_px
            self._snap_to_px = float(self._anim_target_item * self.ITEM_WIDTH)
            self._snap_duration = 0.10 if is_fast_open else 0.25
            # Suspense pause before snap-back begins
            pause_ms = 80 if is_fast_open else 200
            self.after(pause_ms, self._start_snap_back)

    def _start_snap_back(self):
        """Begin the snap-back recoil animation to center the winning item."""
        self._snap_start_time = time.monotonic()
        self._snap_back_step()

    def _snap_back_step(self):
        now = time.monotonic()
        elapsed = now - self._snap_start_time
        t = min(elapsed / self._snap_duration, 1.0)

        # Ease-in-out interpolation from landing offset to exact center
        progress = self._ease_in_out_quad(t)
        current_px = self._snap_from_px + (self._snap_to_px - self._snap_from_px) * progress

        self._render_at_scroll(current_px)

        if t < 1.0:
            self.after(self.FRAME_MS, self._snap_back_step)
        else:
            # Snap-back complete — check if any rows dropped Gold
            self._render_at_scroll(self._snap_to_px)
            self.spin_running = False

            def check_finalize():
                # Check for any Gold drops in active winning items
                gold_row_indices = [
                    idx for idx, it in enumerate(self.winning_items)
                    if it.rarity == "Rare Special"
                ]
                if gold_row_indices:
                    self._start_inline_gold_respin(gold_row_indices)
                else:
                    self.open_btn.configure(state="normal")
                    self.seg_button.configure(state="normal")
                    self.case_menu.configure(state="normal")
                    self.finalize_multi_spin()

            finalize_delay = 180 if self.skip_animation_var.get() else 500
            self.after(finalize_delay, check_finalize)

    def _start_inline_gold_respin(self, gold_row_indices: List[int]):
        """
        Converts winning Gold rows in-place into Upgrade Strips (UPGRADE vs BASE).
        All gold rows spin their bonus wheel simultaneously on the active canvas.
        """
        self.sound.play_gold()
        self.rolling_label.configure(
            text="★ GOLD ITEM UPGRADE RE-SPIN ★",
            text_color=GOLD_COLOR
        )

        bonus_item_w = 210
        win_slot_idx = 26
        self._inline_respin_win_idx = win_slot_idx
        self._inline_respin_item_w = bonus_item_w
        self._inline_respin_gold_rows = gold_row_indices

        # Prepare upgrade sequences and determine true outcomes for each gold row
        self._inline_bonus_sequences = {}
        self._inline_bonus_outcomes = {}
        self._inline_bonus_upgraded_names = {}

        finishes = ["Doppler Phase 4", "Fade (99%)", "Lore", "Marble Fade Fire & Ice", "Gamma Doppler Emerald"]

        for row_idx in gold_row_indices:
            gold_item = self.winning_items[row_idx]
            knife_base = gold_item.name.split("|")[0].strip()
            chosen_finish = random.choice(finishes)
            upgraded_name = f"{knife_base} | {chosen_finish}"
            self._inline_bonus_upgraded_names[row_idx] = upgraded_name

            # 50% chance of upgraded knife
            is_upgrade = random.random() < 0.50
            self._inline_bonus_outcomes[row_idx] = is_upgrade

            # Strip leading ★ so we never get "★ BASE: ★ Kukri..."
            clean_base = gold_item.name.lstrip("★ ").strip()
            clean_upgrade = upgraded_name.lstrip("★ ").strip()

            bonus_tile_types = [
                {"type": "UPGRADE", "name": upgraded_name,      "title": f"⬆ {clean_upgrade[:26]}", "color": "#10ffaa", "bg": "#003320"},
                {"type": "BASE",    "name": gold_item.name,     "title": f"★ {clean_base[:26]}",     "color": "#ffd700", "bg": "#3d2800"}
            ]

            seq = []
            for i in range(35):
                if i == win_slot_idx:
                    tile = bonus_tile_types[0] if is_upgrade else bonus_tile_types[1]
                else:
                    tile = bonus_tile_types[i % 2]
                seq.append(tile)

            self._inline_bonus_sequences[row_idx] = seq

        # Random landing shift within the center indicator
        landing_shift = random.uniform(-35, 35)
        self._inline_respin_total_px = float(win_slot_idx * bonus_item_w) + landing_shift
        is_fast_open = self.skip_animation_var.get()
        self._inline_respin_duration = 1.2 if is_fast_open else 3.0
        self._inline_respin_start_time = time.monotonic()
        self._inline_respin_last_tick = -1

        self._step_inline_gold_respin()

    def _render_inline_bonus_row(self, row_idx: int, scroll_px: float):
        """Draws the upgrade strip on a specific row canvas."""
        canvas = self.spin_canvases[row_idx]
        seq = self._inline_bonus_sequences.get(row_idx, [])
        if not seq:
            return

        canvas.delete("all")
        canvas_center_x = 340
        h = int(canvas.cget("height"))
        center_y = h // 2
        card_half_h = min(26, h // 2 - 4)

        item_w = self._inline_respin_item_w
        cur_item = int(scroll_px / item_w)
        sub_px = scroll_px - (cur_item * item_w)

        for offset in range(-2, 3):
            idx = cur_item + offset
            if 0 <= idx < len(seq):
                tile = seq[idx]
                x = canvas_center_x + offset * item_w - sub_px
                y = center_y

                is_center = abs(x - canvas_center_x) < item_w * 0.45
                outline = "#fbbf24" if is_center else "#1e293b"
                width = 2 if is_center else 1

                canvas.create_rectangle(
                    x - 98, y - card_half_h, x + 98, y + card_half_h,
                    fill=tile["bg"], outline=outline, width=width
                )

                # Image: 80×(card_height-22) to leave room for text label
                tile_img_h = max(32, card_half_h * 2 - 22)
                tile_img_size = (80, tile_img_h)
                tile_name = tile.get("name", "")
                img_cy = y - card_half_h + 4 + tile_img_h // 2   # top-aligned inside card

                if tile["type"] == "UPGRADE" and tile_name:
                    tile_photo = image_loader.get_tk_photo_image(tile_name, rarity="Rare Special", size=tile_img_size)
                else:
                    tile_photo = image_loader.get_gold_special_tk_photo(size=tile_img_size)

                if tile_photo:
                    self._photo_refs.append(tile_photo)   # GC-safe
                    canvas.create_image(x, img_cy, image=tile_photo)

                # Label below image
                canvas.create_text(
                    x, y + card_half_h - 10,
                    text=tile["title"],
                    fill=tile["color"],
                    font=("Segoe UI", 9, "bold"),
                    width=188
                )

        # Golden center line
        canvas.create_line(canvas_center_x, 0, canvas_center_x, h, fill="#fbbf24", width=3)

    def _step_inline_gold_respin(self):
        now = time.monotonic()
        elapsed = now - self._inline_respin_start_time
        t = min(elapsed / self._inline_respin_duration, 1.0)
        progress = self._ease_out_cubic(t)
        current_scroll = progress * self._inline_respin_total_px

        # Play tick sound using consolidated audio loop with debounce
        current_tick = int(current_scroll / self._inline_respin_item_w)
        if current_tick != self._inline_respin_last_tick and t < 1.0:
            self.sound.play_tick()
            self._inline_respin_last_tick = current_tick

        # Render all gold rows simultaneously in-place
        for row_idx in self._inline_respin_gold_rows:
            self._render_inline_bonus_row(row_idx, current_scroll)

        if t < 1.0:
            self.after(self.FRAME_MS, self._step_inline_gold_respin)
        else:
            # Inline re-spin complete — apply upgrades
            upgraded_any = False

            for row_idx in self._inline_respin_gold_rows:
                is_upgrade = self._inline_bonus_outcomes.get(row_idx, False)
                item = self.winning_items[row_idx]
                if is_upgrade:
                    upgraded_any = True
                    item.name = self._inline_bonus_upgraded_names[row_idx]
                    item.base_price = round(item.base_price * 1.50, 2)

            if upgraded_any:
                self.sound.play_gold()
            else:
                self.sound.play_win()

            def finish_inline():
                self.open_btn.configure(state="normal")
                self.seg_button.configure(state="normal")
                self.case_menu.configure(state="normal")
                self.finalize_multi_spin()

            # Short pause to let player see the landed outcome before final reveal text
            self.after(600, finish_inline)

    def finalize_multi_spin(self):
        has_gold = any(it.rarity == "Rare Special" for it in self.winning_items)
        has_covert = any(it.rarity == "Covert" for it in self.winning_items)

        # Audio reveal
        if has_gold or has_covert:
            self.sound.play_gold()
        else:
            self.sound.play_win()

        auto_sold_count = 0
        auto_sold_total = 0.0

        opened_results = []
        for item in self.winning_items:
            auto_sold, val = self.game.finalize_opened_item(item)
            opened_results.append((item, auto_sold, val))
            if auto_sold:
                auto_sold_count += 1
                auto_sold_total += val

        self.on_state_changed()
        self.game.save()

        # Show toast notification for every drop — no modal ever
        auto_sold_results = [res for res in opened_results if res[1]]
        kept_results     = [res for res in opened_results if not res[1]]

        if len(opened_results) == 1:
            it, auto_sold, val = opened_results[0]
            st = "★ " if it.is_st else ""
            r_color = RARITY_COLORS.get(it.rarity, SUCCESS_GREEN)
            if auto_sold:
                self.sound.play_sell()
                self._show_toast(
                    f"⚡ Auto-sold {st}{it.name} [{it.quality}] for +${val:,.2f}!",
                    SUCCESS_GREEN,
                    5000
                )
            else:
                self._show_toast(
                    f"🎁 Got: {st}{it.name} [{it.quality} • {it.wear_float:.4f}] (${val:,.2f})",
                    r_color,
                    5000
                )
        else:
            total_val = sum(res[2] for res in opened_results)
            sold_count = len(auto_sold_results)
            kept_count = len(kept_results)
            if sold_count and not kept_count:
                self.sound.play_sell()
                self._show_toast(
                    f"⚡ Auto-sold {sold_count} item(s) for +${total_val:,.2f} directly to Balance!",
                    SUCCESS_GREEN,
                    5000
                )
            elif sold_count:
                self.sound.play_sell()
                kept_val = sum(res[2] for res in kept_results)
                self._show_toast(
                    f"🎁 Unboxed {len(opened_results)} items — {kept_count} kept (${kept_val:,.2f}), {sold_count} auto-sold (${sum(r[2] for r in auto_sold_results):,.2f})",
                    SUCCESS_GREEN,
                    6000
                )
            else:
                self._show_toast(
                    f"🎁 Unboxed {len(opened_results)} items! Total value: ${total_val:,.2f}",
                    SUCCESS_GREEN,
                    5000
                )

