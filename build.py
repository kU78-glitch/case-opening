"""
build.py - Standalone Windows Executable (.exe) Packager for Case Opening Simulator
Packages the application into a standalone distribution with all assets, sound effects, and custom case templates.
"""
import os
import sys
import subprocess
import shutil

def build_executable():
    print("=" * 65)
    print("  Case Opening Simulator - Windows Executable (.exe) Build  ")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.dirname(__file__))
    os.chdir(base_dir)

    # 1. Ensure required tools are available
    try:
        import PyInstaller
    except ImportError:
        print("[!] PyInstaller not found. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Ensure assets and sounds folders exist and are synced
    assets_dir = os.path.join(base_dir, "assets")
    sounds_dir = os.path.join(base_dir, "sounds")
    assets_sounds_dir = os.path.join(assets_dir, "sounds")

    os.makedirs(assets_sounds_dir, exist_ok=True)
    if os.path.exists(sounds_dir):
        for fname in os.listdir(sounds_dir):
            src = os.path.join(sounds_dir, fname)
            dst = os.path.join(assets_sounds_dir, fname)
            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)

    # 3. Ensure custom_cases.json exists
    custom_cases_file = os.path.join(base_dir, "custom_cases.json")
    if not os.path.exists(custom_cases_file):
        print("[*] Generating default custom_cases.json template...")
        import cases
        cases.load_custom_cases()

    # 4. Detect CustomTkinter path for packaging assets
    ctk_args = ["--collect-all", "customtkinter"]
    try:
        import customtkinter
        ctk_path = os.path.dirname(customtkinter.__file__)
        if os.path.exists(ctk_path):
            ctk_args.extend(["--add-data", f"{ctk_path};customtkinter"])
    except Exception as e:
        print(f"[!] Warning: Could not detect customtkinter path: {e}")

    # 5. Assemble PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "Case_Opening_Simulator",
        "--contents-directory", "_internal",
        "--add-data", "assets;assets",
    ]
    cmd.extend(ctk_args)
    cmd.append("main.py")

    print("\n[+] Running command:")
    print(" ".join(cmd))
    print("\n[+] Compiling application binary... (this may take 1-2 minutes)")

    result = subprocess.run(cmd)

    if result.returncode == 0:
        dist_dir = os.path.join(base_dir, "dist")
        dist_folder = os.path.join(dist_dir, "Case_Opening_Simulator")
        exe_path = os.path.join(dist_folder, "Case_Opening_Simulator.exe")
        zip_path = os.path.join(dist_dir, "Case_Opening_Simulator.zip")

        # Ensure secure custom_cases.dat is present in distribution root
        custom_cases_dat = os.path.join(base_dir, "custom_cases.dat")
        root_custom_cases_dat = os.path.join(dist_folder, "custom_cases.dat")
        if os.path.exists(custom_cases_dat) and not os.path.exists(root_custom_cases_dat):
            shutil.copy2(custom_cases_dat, root_custom_cases_dat)

        # Remove any legacy unencrypted custom_cases.json if present
        legacy_json = os.path.join(dist_folder, "custom_cases.json")
        if os.path.exists(legacy_json):
            os.remove(legacy_json)

        print("\n" + "=" * 65)
        print("  BUILD SUCCESSFUL!  ")
        print("=" * 65)
        print(f"[OK] Output directory : {dist_folder}")
        print(f"[OK] Executable binary: {exe_path}")

        # 6. Create clean ZIP archive of the distribution
        print("\n[+] Creating ZIP archive: Case_Opening_Simulator.zip...")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        shutil.make_archive(
            base_name=os.path.join(dist_dir, "Case_Opening_Simulator"),
            format="zip",
            root_dir=dist_folder
        )
        print(f"[OK] ZIP archive generated: {zip_path}")
        print("=" * 65)
    else:
        print(f"\n[X] Build failed with exit code: {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build_executable()

