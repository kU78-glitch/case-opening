import tkinter as tk
from tkinter import ttk, messagebox
import config
from game_logic import GameManager

class InventoryWindow(tk.Toplevel):
    def __init__(self, parent, game: GameManager, on_update_callback):
        super().__init__(parent)
        self.title("Inventar & Auto-Sell")
        self.geometry("800x550")
        self.game = game
        self.on_update = on_update_callback

        self.setup_ui()
        self.refresh_inventory()

    def setup_ui(self):
        # Auto-Sell seaded
        autosell_frame = ttk.LabelFrame(self, text="Auto-Sell Valikud (Automaatne müük kasti avamisel)")
        autosell_frame.pack(fill="x", padx=10, pady=5)

        self.autosell_vars = {}
        for rarity in config.RARITIES:
            var = tk.BooleanVar(value=self.game.auto_sell.get(rarity, False))
            self.autosell_vars[rarity] = var
            cb = ttk.Checkbutton(
                autosell_frame,
                text=rarity,
                variable=var,
                command=self.update_autosell
            )
            cb.pack(side="left", padx=8, pady=5)

        # Bulk sell nupud
        bulk_frame = ttk.LabelFrame(self, text="Massmüük Harulduse Järgi")
        bulk_frame.pack(fill="x", padx=10, pady=5)

        for rarity in config.RARITIES[:-1]:  # Mil-Spec kuni Covert
            btn = ttk.Button(
                bulk_frame,
                text=f"Müü kõik {rarity}",
                command=lambda r=rarity: self.sell_rarity(r)
            )
            btn.pack(side="left", padx=4, pady=4)

        # Inventari nimekiri
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("name", "rarity", "quality", "float", "st", "value")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Name")
        self.tree.heading("rarity", text="Rarity")
        self.tree.heading("quality", text="Quality")
        self.tree.heading("float", text="Float")
        self.tree.heading("st", text="StatTrak™")
        self.tree.heading("value", text="Value")

        self.tree.column("name", width=220, anchor="w")
        self.tree.column("rarity", width=100, anchor="center")
        self.tree.column("quality", width=110, anchor="center")
        self.tree.column("float", width=80, anchor="center")
        self.tree.column("st", width=80, anchor="center")
        self.tree.column("value", width=90, anchor="center")

        self.tree.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Alumine riba: Müü valitud ese ja väärtuse kokkuvõte
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=8)

        self.lbl_total_value = ttk.Label(bottom_frame, text="Koguväärtus: $0.00", font=("Arial", 11, "bold"))
        self.lbl_total_value.pack(side="left", padx=5)

        ttk.Button(bottom_frame, text="Müü valitud ese", command=self.sell_selected).pack(side="right", padx=5)

    def update_autosell(self):
        for rarity, var in self.autosell_vars.items():
            self.game.auto_sell[rarity] = var.get()

    def refresh_inventory(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_value = 0.0
        for idx, item in enumerate(self.game.inventory):
            val = item.get_value(self.game.prestige_level)
            total_value += val
            st_text = "StatTrak™" if item.is_st else "—"
            wear_str = f"{item.wear_float:.4f}"

            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    item.name,
                    item.rarity,
                    item.quality,
                    wear_str,
                    st_text,
                    f"${val:.2f}"
                )
            )

        self.lbl_total_value.config(text=f"Koguväärtus: ${total_value:.2f} ({len(self.game.inventory)} eset)")

    def sell_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        if self.game.sell_item(idx):
            self.refresh_inventory()
            self.on_update()

    def sell_rarity(self, rarity: str):
        gained = self.game.sell_all_of_rarity(rarity)
        if gained > 0:
            messagebox.showinfo("Müüdud", f"Müüdi maha kõik {rarity} esemed kokku ${gained:.2f} eest!")
        else:
            messagebox.showinfo("Teade", f"Inventaris pole ühtegi {rarity} eset.")
        self.refresh_inventory()
        self.on_update()