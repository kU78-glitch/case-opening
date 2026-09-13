"""
decrypt_tool.py - Standalone Developer Utility for Secure Save and Custom Cases Data.
Allows developers to inspect and edit encrypted .dat game state files.

Usage:
  python decrypt_tool.py decrypt [input_file] [output_json]
  python decrypt_tool.py encrypt [input_json] [output_file]

Defaults:
  decrypt: reads 'save.dat' (or 'custom_cases.dat') and writes 'debug_save.json'
  encrypt: reads 'debug_save.json' and writes 'save.dat'
"""
import sys
import os
import json
from security import save_encrypted_file, load_encrypted_file, encrypt_data, decrypt_data

def print_help():
    print("=" * 65)
    print("  Save & Custom Cases Developer Decryption/Encryption Utility  ")
    print("=" * 65)
    print("Usage:")
    print("  python decrypt_tool.py decrypt [input.dat] [output.json]")
    print("  python decrypt_tool.py encrypt [input.json] [output.dat]")
    print("\nExamples:")
    print("  python decrypt_tool.py decrypt save.dat debug_save.json")
    print("  python decrypt_tool.py encrypt debug_save.json save.dat")
    print("  python decrypt_tool.py decrypt custom_cases.dat debug_custom_cases.json")
    print("  python decrypt_tool.py encrypt debug_custom_cases.json custom_cases.dat")
    print("=" * 65)

def do_decrypt(input_file: str, output_file: str):
    if not os.path.exists(input_file):
        print(f"[!] Error: Target file '{input_file}' does not exist.")
        return False

    print(f"[*] Reading and decrypting '{input_file}'...")
    data, is_tampered = load_encrypted_file(input_file)
    if is_tampered:
        print(f"[!] WARNING: '{input_file}' failed HMAC anti-tamper signature or decryption verification!")

    if data is None:
        # Check if it was plain JSON
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[*] Note: '{input_file}' was unencrypted plain JSON.")
        except Exception:
            print(f"[X] Failed to decrypt '{input_file}'.")
            return False

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"[OK] Decrypted JSON saved to: {os.path.abspath(output_file)}")
    return True

def do_encrypt(input_file: str, output_file: str):
    if not os.path.exists(input_file):
        print(f"[!] Error: JSON file '{input_file}' does not exist.")
        return False

    print(f"[*] Reading '{input_file}'...")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[X] Error parsing JSON in '{input_file}': {e}")
        return False

    print(f"[*] Encrypting and signing HMAC for '{output_file}'...")
    if save_encrypted_file(output_file, data):
        print(f"[OK] Encrypted binary successfully saved to: {os.path.abspath(output_file)}")
        return True
    else:
        print(f"[X] Failed to save encrypted file '{output_file}'.")
        return False

def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() in ("-h", "--help", "help"):
        print_help()
        sys.exit(0)

    action = sys.argv[1].lower()

    if action == "decrypt":
        input_file = sys.argv[2] if len(sys.argv) > 2 else "save.dat"
        if not os.path.exists(input_file) and os.path.exists("custom_cases.dat") and input_file == "save.dat":
            # If save.dat not found, check custom_cases.dat
            pass
        output_file = sys.argv[3] if len(sys.argv) > 3 else "debug_save.json"
        success = do_decrypt(input_file, output_file)
        sys.exit(0 if success else 1)

    elif action == "encrypt":
        input_file = sys.argv[2] if len(sys.argv) > 2 else "debug_save.json"
        output_file = sys.argv[3] if len(sys.argv) > 3 else "save.dat"
        success = do_encrypt(input_file, output_file)
        sys.exit(0 if success else 1)

    else:
        print(f"[!] Unknown action: {action}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

