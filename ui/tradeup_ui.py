import random
import tkinter as tk
from tkinter import ttk, messagebox
import config
from models import Item, roll_float, float_to_quality
from game_logic import GameManager
from cases import CASES

class TradeUpWindow(tk.Toplevel):
    def __init__(self, parent, game: GameManager, on_update_callback):
        super().__init__(parent)
        self.title("Trade-Up Leping (10 relva -> 1 kõrgem tase)")
        self.geometry("700x500")
        self.game = game
        self.on_update = on_update_callback

        self.setup_ui()
        self.refresh_inventory_list()

    def setup_ui(self):
        ttk.Label(
            self,
            text="Vali inventarist täpselt 10 sama haruldusega relva:",
            font=("Arial", 11, "bold")
        ).pack(pady=8)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("name", "rarity", "quality", "float", "st")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("name", text="Name")
        self.tree.heading("rarity", text="Rarity")
        self.tree.heading("quality", text="Quality")
        self.tree.heading("float", text="Float")
        self.tree.heading("st", text="StatTrak™")

        self.tree.column("name", width=240, anchor="w")
        self.tree.column("rarity", width=110, anchor="center")
        self.tree.column("quality", width=120, anchor="center")
        self.tree.column("float", width=80, anchor="center")
        self.tree.column("st", width=90, anchor="center")

        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Automaatne 10 valik", command=self.autofill_ten).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Kinnita Trade-Up", command=self.process_tradeup).pack(side="left", padx=5)

    def refresh_inventory_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, item in enumerate(self.game.inventory):
            # Trade-Up lepingusse sobivad esemed (kuni Classified)
            if item.rarity not in ("Covert", "Rare Special"):
                st_text = "StatTrak™" if item.is_st else "—"
                self.tree.insert(
                    "",
                    "end",
                    iid=str(idx),
                    values=(
                        item.name,
                        item.rarity,
                        item.quality,
                        f"{item.wear_float:.4f}",
                        st_text
                    )
                )

    def autofill_ten(self):
        """Valib esimesed 10 sama haruldusega eset."""
        rarities_in_inv = {}
        for idx, item in enumerate(self.game.inventory):
            if item.rarity not in ("Covert", "Rare Special"):
                rarities_in_inv.setdefault(item.rarity, []).append(idx)

        for rarity, indices in rarities_in_inv.items():
            if len(indices) >= 10:
                self.tree.selection_set([str(i) for i in indices[:10]])
                return

        messagebox.showinfo("Teade", "Inventaris ei leidu 10 sama haruldusega eset trade-up jaoks.")

    def process_tradeup(self):
        selected_iids = self.tree.selection()
        if len(selected_iids) != 10:
            messagebox.showwarning("Vale kogus", "Trade-Up lepingu jaoks pead valima täpselt 10 eset!")
            return

        indices = [int(iid) for iid in selected_iids]
        selected_items = [self.game.inventory[i] for i in indices]

        first_rarity = selected_items[0].rarity
        if not all(item.rarity == first_rarity for item in selected_items):
            messagebox.showerror("Viga", "Kõik 10 eset peavad olema samast haruldusastmest!")
            return

        rarity_order = config.RARITIES
        try:
            curr_idx = rarity_order.index(first_rarity)
            if curr_idx + 1 >= len(rarity_order):
                raise ValueError
            next_rarity = rarity_order[curr_idx + 1]
        except (ValueError, IndexError):
            messagebox.showerror("Viga", "Selle haruldusega ei saa Trade-Up lepingut teha!")
            return

        # StatTrak staatus: kui kõik 10 olid StatTrak, on tulemus StatTrak
        all_st = all(item.is_st for item in selected_items)

        # Lähtekastide kaalutud valik
        weights = {}
        for item in selected_items:
            weights[item.case_name] = weights.get(item.case_name, 0) + 1

        eligible_cases = []
        for case_name, w in weights.items():
            case_items = CASES.get(case_name, {}).get("items", {})
            if next_rarity in case_items and case_items[next_rarity]:
                eligible_cases.append((case_name, w))

        if not eligible_cases:
            # Fallback kasti leidmine
            for c_name, c_data in CASES.items():
                if next_rarity in c_data.get("items", {}):
                    eligible_cases.append((c_name, 1))
                    break

        total_weight = sum(w for _, w in eligible_cases)
        r_val = random.uniform(0, total_weight)
        cum = 0
        chosen_case = eligible_cases[-1][0]
        for c_name, w in eligible_cases:
            cum += w
            if r_val <= cum:
                chosen_case = c_name
                break

        # Eemaldame valitud 10 eset inventarist tagurpidi
        for i in sorted(indices, reverse=True):
            self.game.inventory.pop(i)

        case_data = CASES[chosen_case]
        pool = case_data["items"][next_rarity]
        name, color = random.choice(pool)

        wear_float = roll_float()
        quality = float_to_quality(wear_float)
        base_price = config.SELL_PRICES.get(next_rarity, 5.0)

        new_item = Item(
            name=name,
            rarity=next_rarity,
            color=color,
            is_st=all_st,
            wear_float=wear_float,
            quality=quality,
            case_name=chosen_case,
            base_price=base_price
        )

        self.game.inventory.append(new_item)
        self.game.stats.tradeups_done += 1
        if all_st:
            self.game.stats.stattrak_drops += 1
        self.game.stats.drops_by_rarity[next_rarity] = self.game.stats.drops_by_rarity.get(next_rarity, 0) + 1

        st_prefix = "StatTrak™ " if all_st else ""
        messagebox.showinfo(
            "Trade-Up Õnnestus!",
            f"Said uue eseme:\n\n{st_prefix}{new_item.name}\n"
            f"Kvaliteet: {new_item.quality} (Float: {new_item.wear_float:.4f})\n"
            f"Haruldus: {new_item.rarity}\n"
            f"Väärtus: ${new_item.get_value(self.game.prestige_level):.2f}"
        )

        self.refresh_inventory_list()
        self.on_update()