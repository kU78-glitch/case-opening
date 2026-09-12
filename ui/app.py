import os
import sys
import customtkinter as ctk

from game_logic import GameManager
from ui.sound_manager import SoundManager
from ui.header import HeaderBar
from ui.sidebar import Sidebar
from ui.cases_view import CasesView
from ui.inventory_view import InventoryView
from ui.tradeup_view import TradeUpView
from ui.stats_view import StatsView
from ui.theme import DARK_BG, GOLD_COLOR, SUCCESS_GREEN

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Setup Theme & Appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Case Opening Simulator")
        self.geometry("1120x740")
        self.minsize(980, 680)
        self.configure(fg_color=DARK_BG)

        # Game State & Audio
        self.game = GameManager()
        self.game.load()
        self.sound = SoundManager()

        self._build_layout()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_layout(self):
        # 1. Top Header Bar
        self.header = HeaderBar(self, self.game)
        self.header.pack(fill="x", padx=15, pady=(15, 10))

        # 2. Main Body (Sidebar on left, Content on right)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Sidebar
        self.sidebar = Sidebar(body, on_navigate=self.show_view)
        self.sidebar.pack(side="left", fill="y", padx=(0, 12))

        # Content Frame
        self.content_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # 3. Instantiate Views
        self.views = {
            "cases": CasesView(
                self.content_frame,
                self.game,
                self.sound,
                on_state_changed=self.on_state_changed,
                on_open_inventory=lambda: self.navigate_to("inventory")
            ),
            "inventory": InventoryView(
                self.content_frame,
                self.game,
                on_state_changed=self.on_state_changed,
                on_open_tradeup=lambda: self.navigate_to("tradeup")
            ),
            "tradeup": TradeUpView(
                self.content_frame,
                self.game,
                self.sound,
                on_state_changed=self.on_state_changed
            ),
            "stats": StatsView(
                self.content_frame,
                self.game,
                self.sound,
                on_state_changed=self.on_state_changed
            )
        }

        self.current_view_key = None
        self.show_view("cases")

    def navigate_to(self, key: str):
        self.sidebar.set_active(key)
        self.show_view(key)

    def show_view(self, key: str):
        if key not in self.views:
            return

        # Hide old view
        if self.current_view_key and self.current_view_key in self.views:
            self.views[self.current_view_key].pack_forget()

        # Show new view
        view = self.views[key]
        view.pack(fill="both", expand=True)
        self.current_view_key = key

        # View specific refresh hooks
        if key == "cases":
            view.refresh_controls()
        elif key == "inventory":
            view.refresh_list()
        elif key == "tradeup":
            view.refresh_candidates()
        elif key == "stats":
            view.refresh()

    def on_state_changed(self, check_achievements: bool = True):
        # Refresh header balances
        self.header.refresh()
        if "cases" in self.views:
            self.views["cases"].refresh_controls()

        if check_achievements:
            # Check for newly unlocked achievements only when explicitly requested
            new_achs = self.game.check_achievements()
            if new_achs:
                self.sound.play_gold()
                for title in new_achs:
                    self.show_toast(f"🏆 Achievement Unlocked!\n{title}")

    def show_toast(self, message: str):
        toast = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=8, border_width=1, border_color=GOLD_COLOR)
        toast.place(relx=0.98, rely=0.05, anchor="ne")

        lbl = ctk.CTkLabel(
            toast,
            text=message,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#ffffff",
            justify="center"
        )
        lbl.pack(padx=15, pady=10)

        # Auto dismiss after 3 seconds
        self.after(3000, toast.destroy)

    def on_close(self):
        self.game.save()
        self.destroy()

