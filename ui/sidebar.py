import customtkinter as ctk
from ui.theme import SIDEBAR_BG, ACCENT_BLUE, TEXT_MAIN, TEXT_MUTED

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate):
        super().__init__(master, fg_color=SIDEBAR_BG, corner_radius=12, width=220)
        self.on_navigate = on_navigate
        self.pack_propagate(False)

        # Brand / Logo Header
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=(20, 30))

        title = ctk.CTkLabel(
            title_frame,
            text="CASE OPENER",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=TEXT_MAIN
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Simulator & Trade-Up",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_MUTED
        )
        subtitle.pack(anchor="w")

        # Navigation Buttons
        self.buttons = {}
        nav_items = [
            ("cases", "📦  Cases / Open"),
            ("inventory", "🎒  Inventory"),
            ("tradeup", "🔄  Trade-Up"),
            ("stats", "📊  Statistics"),
        ]

        for key, text in nav_items:
            btn = ctk.CTkButton(
                self,
                text=text,
                font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                height=46,
                corner_radius=8,
                anchor="w",
                fg_color="transparent",
                text_color=TEXT_MUTED,
                hover_color="#272b36",
                command=lambda k=key: self._on_btn_click(k)
            )
            btn.pack(fill="x", padx=12, pady=5)
            self.buttons[key] = btn

        # Default selection
        self.set_active("cases")

    def _on_btn_click(self, key: str):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, active_key: str):
        for key, btn in self.buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=ACCENT_BLUE,
                    text_color="#ffffff",
                    hover_color=ACCENT_BLUE
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_MUTED,
                    hover_color="#272b36"
                )

