import sys
import subprocess


def auto_install_dependencies():
    required_packages = ["customtkinter", "pygame"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Package '{package}' missing. Installing automatically...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


auto_install_dependencies()

from ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()