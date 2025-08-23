# This script cleans up cache directories for Whisper and Argos Translate.

import os
import shutil
from pathlib import Path

def get_cache_dirs():
    home = Path.home()
    huggingface_cache = home / ".cache" / "huggingface" / "hub"
    argos_cache1 = home / ".local" / "share" / "argos-translate"
    argos_cache2 = home / ".local" / "cache" / "argos-translate"
    return {
        "whisper": [huggingface_cache],
        "argos": [argos_cache1, argos_cache2],
    }

def remove_dir(path: Path):
    if path.exists():
        try:
            shutil.rmtree(path)
            print(f"Successfully removed {path}")
        except OSError as e:
            print(f"Error removing {path}: {e}")
    else:
        print(f"Directory not found: {path}")

def main():
    cache_dirs = get_cache_dirs()

    print("Select a cleanup option:")
    print("1. Clean Whisper cache")
    print("2. Clean Argos Translate cache")
    print("3. Clean everything")
    print("4. Cancel")

    try:
        choice = int(input("Enter your choice (1-4): "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        return

    if choice == 1:
        print("\nCleaning Whisper cache...")
        for path in cache_dirs["whisper"]:
            remove_dir(path)
    elif choice == 2:
        print("\nCleaning Argos Translate cache...")
        for path in cache_dirs["argos"]:
            remove_dir(path)
    elif choice == 3:
        print("\nCleaning everything...")
        for cache_type in cache_dirs.values():
            for path in cache_type:
                remove_dir(path)
    elif choice == 4:
        print("Operation cancelled.")
    else:
        print("Invalid choice. Please select a number between 1 and 4.")

if __name__ == "__main__":
    main()
