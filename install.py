#!/usr/bin/env python3
"""TraceOn — One-time setup / install script

Detects WezTerm paths, asks for image directory, generates config.json,
and optionally adds TraceOn to the system PATH so "TraceOn" works
from any terminal.

Run this once after extracting TraceOn to your desired folder.
"""

import json
import os
import shutil
import subprocess
import sys


# ── Default / fallback paths ──────────────────────────────

DEFAULT_SEARCH_PATHS = {
    "wezterm_config": [
        r"%USERPROFILE%\.config\wezterm\wezterm.lua",
        r"%APPDATA%\wezterm\wezterm.lua",
        r"%USERPROFILE%\wezterm.lua",
    ],
    "wezterm_exe": [
        r"C:\Program Files\WezTerm\wezterm-gui.exe",
        r"D:\app\WezTerm\wezterm-gui.exe",
        r"%LOCALAPPDATA%\Programs\WezTerm\wezterm-gui.exe",
        r"%LOCALAPPDATA%\Microsoft\WindowsApps\wezterm-gui.exe",
    ],
}

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]


# ── Helpers ───────────────────────────────────────────────


def expand(path: str) -> str:
    """Expand %VAR% environment variables in a Windows path."""
    return os.path.expandvars(path)


def to_forward_slash(path: str) -> str:
    """Replace all backslashes with forward slashes."""
    return path.replace("\\", "/")


def ask(prompt: str, default: str = "") -> str:
    """Prompt the user for input with an optional default value."""
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def ask_yn(prompt: str, default: bool = True) -> bool:
    """Ask a yes/no question."""
    hint = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {hint}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def find_file(search_paths, description):
    """Try each search path; return the first one that exists, or None."""
    for raw in search_paths:
        p = expand(raw)
        if os.path.isfile(p):
            return p
    return None


def find_exe_in_path(name):
    """Search for an executable on the system PATH."""
    result = shutil.which(name)
    if result:
        return result
    # Also try common names
    for variant in (name, name.replace("-gui", ""), name + ".exe"):
        result = shutil.which(variant)
        if result:
            return result
    return None


# ── PATH management (Windows registry) ────────────────────


def add_to_user_path(dir_path):
    """Add *dir_path* to the user-level PATH environment variable.

    Uses the Windows registry so the change persists.  Requires a log-off /
    log-on (or new terminal) to take effect for already-open shells.
    """
    if sys.platform != "win32":
        print("  (skipping PATH update — not on Windows)")
        return False

    try:
        import winreg
    except ImportError:
        print("  (skipping PATH update — winreg not available)")
        return False

    dir_path = os.path.abspath(dir_path)

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Environment",
        0,
        winreg.KEY_READ | winreg.KEY_SET_VALUE,
    )
    try:
        path, _ = winreg.QueryValueEx(key, "PATH")
    except (FileNotFoundError, OSError):
        path = ""

    # Normalise: split, strip, dedupe
    entries = [p.strip().rstrip("\\") for p in path.split(";") if p.strip()]
    norm = os.path.normpath(dir_path).lower().rstrip("\\")

    if any(os.path.normpath(e).lower().rstrip("\\") == norm for e in entries):
        winreg.CloseKey(key)
        return False  # already present

    entries.append(dir_path)
    new_path = ";".join(entries)
    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
    winreg.CloseKey(key)

    # Notify other applications of the change
    try:
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0, 5000, None
        )
    except Exception:
        pass

    print(f"\n  Added to PATH: {dir_path}")
    print("  (Open a new terminal for the change to take effect.)")
    return True


# ── Main setup flow ───────────────────────────────────────


def main():
    print("=" * 50)
    print("  TraceOn — First-time Setup")
    print("=" * 50)
    print()
    print("This script will detect WezTerm paths and ask for your")
    print("image folder, then generate config.json.  Run it once")
    print("after extracting TraceOn to its permanent folder.\n")

    app_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(app_dir, "config.json")

    config = {}

    # ── 1. Detect wezterm.lua ──────────────────────────────
    print("─" * 50)
    print(" [1/4] Locating wezterm.lua …")
    found = find_file(
        DEFAULT_SEARCH_PATHS["wezterm_config"],
        "wezterm.lua",
    )
    if found:
        print(f"  Found: {found}")
        if ask_yn("  Use this path?", default=True):
            config["wezterm_config_path"] = to_forward_slash(found)
    if "wezterm_config_path" not in config:
        print()
        print("  WezTerm config file not found automatically.")
        print("  Common locations:")
        print("    %USERPROFILE%\\.config\\wezterm\\wezterm.lua")
        print("    %APPDATA%\\wezterm\\wezterm.lua")
        manual = ask("  Please enter the full path to wezterm.lua")
        config["wezterm_config_path"] = to_forward_slash(manual)

    # ── 2. Detect wezterm-gui.exe ──────────────────────────
    print()
    print("─" * 50)
    print(" [2/4] Locating wezterm-gui.exe …")
    found = find_exe_in_path("wezterm-gui.exe")
    if not found:
        found = find_file(
            DEFAULT_SEARCH_PATHS["wezterm_exe"],
            "wezterm-gui.exe",
        )
    if found:
        print(f"  Found: {found}")
        if ask_yn("  Use this path?", default=True):
            config["wezterm_exe_path"] = to_forward_slash(found)
    if "wezterm_exe_path" not in config:
        print("  WezTerm executable not found automatically.")
        print("  Common locations:")
        print("    C:\\Program Files\\WezTerm\\wezterm-gui.exe")
        print("    %LOCALAPPDATA%\\Programs\\WezTerm\\wezterm-gui.exe")
        manual = ask("  Please enter the full path to wezterm-gui.exe")
        config["wezterm_exe_path"] = to_forward_slash(manual)

    # ── 3. Image directory ─────────────────────────────────
    print()
    print("─" * 50)
    print(" [3/4] Image folder …")
    print("  This is the folder containing images you want to")
    print("  use as WezTerm backgrounds.  Example: E:/Pictures/Wallpapers")
    while True:
        img_dir = ask("  Enter the full path to your image folder")
        img_dir = to_forward_slash(img_dir)
        if os.path.isdir(expand(img_dir)):
            config["image_directory"] = img_dir
            break
        # Maybe the user entered a Windows path with forward slashes —
        # try to check existence via expand
        expanded = expand(img_dir)
        if os.path.isdir(expanded):
            config["image_directory"] = img_dir
            break
        print(f"  Directory not found: {img_dir}")
        if not ask_yn("  Try again?", default=True):
            print("  Setup cancelled.")
            return

    # ── 4. Save config ─────────────────────────────────────
    print()
    print("─" * 50)
    print(" [4/4] Saving configuration …")

    config["launch_wezterm"] = True
    config["image_extensions"] = IMAGE_EXTENSIONS

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    print(f"  Config saved: {config_path}")

    # Show summary
    print()
    print("=" * 50)
    print("  Configuration Summary")
    print("=" * 50)
    print(f"  wezterm.lua : {config['wezterm_config_path']}")
    print(f"  wezterm.exe : {config['wezterm_exe_path']}")
    print(f"  Image dir   : {config['image_directory']}")
    print(f"  Launch      : {config['launch_wezterm']}")

    # ── 5. PATH (optional) ─────────────────────────────────
    print()
    print("─" * 50)
    print(" [Optional] Add to PATH")
    print(f"  Add this folder to your user PATH so you can type")
    print(f"  'TraceOn' from any terminal?")
    print(f"  Folder: {app_dir}")
    if ask_yn("  Add to PATH?", default=True):
        added = add_to_user_path(app_dir)
        if not added:
            print("  Already in PATH — nothing to do.")

    print()
    print("=" * 50)
    print("  Setup complete!")
    print("=" * 50)
    print()
    print("  Next steps:")
    print("    1. Make sure the TraceOn folder is in PATH (handled above)")
    print("    2. Open a new terminal")
    print("    3. Type 'TraceOn' to randomise your WezTerm background")
    print()
    print("  To change the image folder later, just re-run this script")
    print("  or edit config.json directly.\n")


if __name__ == "__main__":
    main()
