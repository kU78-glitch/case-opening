import customtkinter as ctk
from ui.theme import PANEL_BG, TEXT_MAIN, TEXT_MUTED, GOLD_COLOR, SUCCESS_GREEN

class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, game):
        super().__init__(master, fg_color=PANEL_BG, corner_radius=12, height=60)
        self.game = game
        self.pack_propagate(False)

        # Left: Balance & Prestige
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.pack(side="left", padx=20, pady=10)

        self.balance_label = ctk.CTkLabel(
            left_frame,
            text=f"Balance: ${self.game.balance:,.2f}",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=SUCCESS_GREEN
        )
        self.balance_label.pack(side="left", padx=(0, 25))

        self.prestige_label = ctk.CTkLabel(
            left_frame,
            text=self._get_prestige_text(),
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=GOLD_COLOR if self.game.prestige_level > 0 else TEXT_MUTED
        )
        self.prestige_label.pack(side="left")

        # Right: Subtitle / branding
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", padx=20, pady=10)

        self.app_title_label = ctk.CTkLabel(
            right_frame,
            text="CASE SIMULATOR",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=TEXT_MUTED
        )
        self.app_title_label.pack(side="right")

    def _get_prestige_text(self) -> str:
        if self.game.prestige_level > 0:
            bonus = int(self.game.prestige_level * 10)
            return f"⭐ Prestige: P{self.game.prestige_level} (+{bonus}%)"
        return "⭐ Prestige: None"

    def refresh(self):
        self.balance_label.configure(text=f"Balance: ${self.game.balance:,.2f}")
        self.prestige_label.configure(
            text=self._get_prestige_text(),
            text_color=GOLD_COLOR if self.game.prestige_level > 0 else TEXT_MUTED
        )

