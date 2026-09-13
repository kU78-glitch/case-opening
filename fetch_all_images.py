"""
fetch_all_images.py - Bulk downloader for all weapon skins in Case Opening Simulator.
Iterates over all official and custom cases and downloads required skin PNGs from Valve CDN.
"""
import os
import re
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from cases import get_all_known_items
import image_loader

def normalize(name: str) -> str:
    return re.sub(r'^[★\s]+', '', name).strip().lower()

def main():
    print("=" * 65)
    print("  CS2 Weapon Skin Artwork Pre-Fetcher & Downloader  ")
    print("=" * 65)

    skins_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "assets", "skins")
    os.makedirs(skins_dir, exist_ok=True)

    # 1. Load CDN index
    print("[+] Fetching skin CDN database index...")
    url = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        skins_data = json.loads(resp.read().decode())

    cdn_map = {}
    for s in skins_data:
        norm = normalize(s.get("name", ""))
        img_url = s.get("image")
        if norm and img_url:
            cdn_map[norm] = img_url

    print(f"[OK] Loaded {len(cdn_map)} skins from CDN index.")

    # 2. Collect all known game skins
    known = get_all_known_items()
    unique_skins = set()
    for rarity, items in known.items():
        for item in items:
            unique_skins.add(item[0])

    print(f"[+] Found {len(unique_skins)} unique skin models across all cases.")

    # 3. Download concurrently
    tasks = []
    already_present = 0

    for skin_name in unique_skins:
        fname = image_loader.sanitize_filename(skin_name)
        target = os.path.join(skins_dir, fname)
        if os.path.exists(target) and os.path.getsize(target) > 500:
            already_present += 1
            continue

        norm = normalize(skin_name)
        img_url = cdn_map.get(norm)
        if not img_url:
            for k, u in cdn_map.items():
                if norm in k or k in norm:
                    img_url = u
                    break

        if img_url:
            tasks.append((skin_name, img_url, target))

    print(f"[*] Already cached: {already_present} | To download: {len(tasks)}")

    def download_one(task):
        name, img_url, path = task
        try:
            r = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(r, timeout=15) as res:
                data = res.read()
            with open(f"{path}.tmp", "wb") as f:
                f.write(data)
            os.replace(f"{path}.tmp", path)
            return True, name
        except Exception as e:
            return False, f"{name}: {e}"

    success_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        for ok, msg in executor.map(download_one, tasks):
            if ok:
                success_count += 1
                if success_count % 10 == 0 or success_count == len(tasks):
                    print(f"  Downloaded [{success_count}/{len(tasks)}] images...")
            else:
                print(f"  [!] Failed to download: {msg}")

    print("=" * 65)
    print(f"[OK] Finished! Total skins cached: {already_present + success_count} / {len(unique_skins)}")
    print("=" * 65)

if __name__ == "__main__":
    main()

