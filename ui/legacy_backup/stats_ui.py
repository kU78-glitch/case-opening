import tkinter as tk
from tkinter import ttk, messagebox
import config
from game_logic import GameManager

class StatsWindow(tk.Toplevel):
    def __init__(self, parent, game: GameManager, on_update_callback):
        super().__init__(parent)
        self.title("Statistika & Prestige")
        self.geometry("620x520")
        self.game = game
        self.on_update = on_update_callback

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.setup_stats_tab()
        self.setup_prestige_tab()

    def setup_stats_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Statistika")

        stats = self.game.stats
        profit = stats.money_earned_from_selling - stats.money_spent
        profit_color = "green" if profit >= 0 else "red"

        container = ttk.Frame(tab)
        container.pack(fill="both", expand=True, padx=20, pady=15)

        info_lines = [
            ("Avatud kaste kokku:", f"{stats.cases_opened}"),
            ("Kulutatud raha (kastid + võtmed):", f"${stats.money_spent:.2f}"),
            ("Teenitud raha müügist:", f"${stats.money_earned_from_selling:.2f}"),
            ("Kasum / Kahjum (P/L):", f"${profit:+.2f}"),
            ("Tehtud Trade-Up lepinguid:", f"{stats.tradeups_done}"),
            ("StatTrak™ droppe:", f"{stats.stattrak_drops}")
        ]

        for idx, (label, val) in enumerate(info_lines):
            lbl_key = ttk.Label(container, text=label, font=("Arial", 11))
            lbl_key.grid(row=idx, column=0, sticky="w", pady=3)

            lbl_val = ttk.Label(container, text=val, font=("Arial", 11, "bold"))
            lbl_val.grid(row=idx, column=1, sticky="e", pady=3, padx=(20, 0))

        # Drops by rarity frame
        rarity_frame = ttk.LabelFrame(container, text="Dropid Harulduse Järgi")
        rarity_frame.grid(row=len(info_lines), column=0, columnspan=2, sticky="ew", pady=(15, 5))

        for r_idx, rarity in enumerate(config.RARITIES):
            count = stats.drops_by_rarity.get(rarity, 0)
            color = config.RARITY_COLORS.get(rarity, "#000000")
            r_label = tk.Label(rarity_frame, text=f"{rarity}: {count}", font=("Arial", 10, "bold"), fg=color)
            r_label.pack(side="left", padx=8, pady=8)

    def setup_prestige_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⭐ Prestige")

        lbl_title = ttk.Label(
            tab,
            text=f"Praegune Prestige Tase: P{self.game.prestige_level}",
            font=("Arial", 14, "bold")
        )
        lbl_title.pack(pady=15)

        bonus = int(self.game.prestige_level * 10)
        lbl_desc = ttk.Label(
            tab,
            text=(
                f"Prestige lävi: ${self.game.prestige_threshold:,.2f} kontojääki.\n"
                f"Praegune müügiboonus: +{bonus}%\n\n"
                "Prestige eelised:\n"
                "• Iga tase annab püsivalt +10% lisaväärtust kõigile müüdavatele esemetele.\n"
                "• Nullib konto jäägi $500 peale ja tühjendab inventari, säilitades sinu saavutused ja tõstes taset!"
            ),
            justify="center", font=("Arial", 10)
        )
        lbl_desc.pack(pady=10)

        btn_prestige = ttk.Button(tab, text="Tee Prestige Reset!", command=self.do_prestige)
        btn_prestige.pack(pady=20)

    def do_prestige(self):
        if self.game.balance < self.game.prestige_threshold:
            messagebox.showwarning(
                "Pole piisavalt raha",
                f"Vajad vähemalt ${self.game.prestige_threshold:,.2f} kontojääki prestige tegemiseks!\n"
                f"Praegune saldo: ${self.game.balance:.2f}"
            )
            return

        if messagebox.askyesno(
            "Kinnita Prestige",
            "Oled kindel?\n\n"
            "Sinu konto jääk viiakse tagasi $500 peale ning inventar nullitakse,\n"
            "kuid saad püsiva +10% lisaväärtuse boonuse igale esemele!"
        ):
            if self.game.prestige():
                messagebox.showinfo("Palju õnne!", f"Oled nüüd Prestige Level {self.game.prestige_level}!")
                self.on_update()
                self.destroy()