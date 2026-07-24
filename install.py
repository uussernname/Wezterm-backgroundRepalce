#!/usr/bin/env python3
"""TraceOn — All-in-one installer

Run once. This script will:
  1. Auto-detect WezTerm paths (fall back to manual input)
  2. Ask for your image folder
  3. Generate config.json
  4. Create venv + install PyInstaller
  5. Build TraceOn.exe
  6. Add dist/TraceOn/ to PATH
  7. Remind you to update wezterm.lua
"""

import json
import os
import shutil
import subprocess
import sys


# ── Search paths ──────────────────────────────────────────

DEFAULT_SEARCH_PATHS = {
    "wezterm_config": [
        r"%USERPROFILE%\.config\wezterm\wezterm.lua",
        r"%APPDATA%\wezterm\wezterm.lua",
        r"%USERPROFILE%\wezterm.lua",
    ],
    "wezterm_exe": [
        r"C:\Program Files\WezTerm\wezterm-gui.exe",
        r"D:\app\WezTerm\WezTerm\wezterm-gui.exe",
        r"D:\app\WezTerm\wezterm-gui.exe",
        r"%LOCALAPPDATA%\Programs\WezTerm\wezterm-gui.exe",
        r"%LOCALAPPDATA%\Microsoft\WindowsApps\wezterm-gui.exe",
    ],
}

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]


# ── Helpers ───────────────────────────────────────────────


def expand(path: str) -> str:
    return os.path.expandvars(path)


def to_forward_slash(path: str) -> str:
    return path.replace("\\", "/")


def ask(prompt: str, default: str = "") -> str:
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


def ask_yn(prompt: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    answer = input(f"{prompt} {hint}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def find_file(search_paths):
    for raw in search_paths:
        p = expand(raw)
        if os.path.isfile(p):
            return p
    return None


def find_exe_in_path(name):
    result = shutil.which(name)
    if result:
        return result
    for variant in (name, name.replace("-gui", ""), name + ".exe"):
        result = shutil.which(variant)
        if result:
            return result
    return None


def run(cmd, desc="", check=True):
    """Run a command; print progress; return True on success."""
    label = f"  {desc} ..." if desc else ""
    print(label)
    try:
        subprocess.run(cmd, check=check, shell=isinstance(cmd, str),
                       stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        print(f"  [FAILED] {desc}")
        return False


# ── PATH management ───────────────────────────────────────


def add_to_user_path(dir_path):
    """Add dir_path to user PATH via Windows registry."""
    if sys.platform != "win32":
        print("  (skip — not on Windows)")
        return False
    try:
        import winreg
    except ImportError:
        print("  (skip — winreg not available)")
        return False

    dir_path = os.path.abspath(dir_path)
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, r"Environment", 0,
        winreg.KEY_READ | winreg.KEY_SET_VALUE,
    )
    try:
        path, _ = winreg.QueryValueEx(key, "PATH")
    except (FileNotFoundError, OSError):
        path = ""

    entries = [p.strip().rstrip("\\") for p in path.split(";") if p.strip()]
    norm = os.path.normpath(dir_path).lower().rstrip("\\")

    if any(os.path.normpath(e).lower().rstrip("\\") == norm for e in entries):
        winreg.CloseKey(key)
        return False

    entries.append(dir_path)
    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, ";".join(entries))
    winreg.CloseKey(key)

    try:
        import ctypes
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 0, 5000, None,
        )
    except Exception:
        pass

    return True


# ── Main ──────────────────────────────────────────────────


def main():
    print("=" * 56)
    print("  TraceOn — All-in-one Installer")
    print("=" * 56)
    print()

    app_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(app_dir, "config.json")
    dist_dir = os.path.join(app_dir, "dist", "TraceOn")
    config = {}

    # ── Step 1: Detect wezterm.lua ───────────────────────────
    print("─" * 56)
    print(" [1/5] Locating wezterm.lua ...")
    print()
    found = find_file(DEFAULT_SEARCH_PATHS["wezterm_config"])
    if found:
        print(f"  Auto-detected: {found}")
        if ask_yn("  Use this path?", default=True):
            config["wezterm_config_path"] = to_forward_slash(found)
    if "wezterm_config_path" not in config:
        print()
        print("  Could not auto-detect wezterm.lua.")
        print("  Common locations:")
        print("    %USERPROFILE%\\.config\\wezterm\\wezterm.lua")
        print("    %APPDATA%\\wezterm\\wezterm.lua")
        print()
        manual = ask("  Enter the full path to your wezterm.lua")
        config["wezterm_config_path"] = to_forward_slash(manual)

    # ── Step 2: Detect wezterm-gui.exe ───────────────────────
    print()
    print("─" * 56)
    print(" [2/5] Locating wezterm-gui.exe ...")
    print()
    found = find_exe_in_path("wezterm-gui.exe")
    if not found:
        found = find_file(DEFAULT_SEARCH_PATHS["wezterm_exe"])
    if found:
        print(f"  Auto-detected: {found}")
        if ask_yn("  Use this path?", default=True):
            config["wezterm_exe_path"] = to_forward_slash(found)
    if "wezterm_exe_path" not in config:
        print("  Could not auto-detect wezterm-gui.exe.")
        print("  Common locations:")
        print("    C:\\Program Files\\WezTerm\\wezterm-gui.exe")
        print("    %LOCALAPPDATA%\\Programs\\WezTerm\\wezterm-gui.exe")
        print()
        manual = ask("  Enter the full path to wezterm-gui.exe")
        config["wezterm_exe_path"] = to_forward_slash(manual)

    # ── Step 3: Image directory ──────────────────────────────
    print()
    print("─" * 56)
    print(" [3/5] Image folder ...")
    print()
    print("  This is the folder where your background images live.")
    print("  Example: E:/Pictures/Wallpapers")
    print()
    while True:
        img_dir = ask("  Enter the full path to your image folder")
        img_dir = to_forward_slash(img_dir)
        expanded = expand(img_dir)
        if os.path.isdir(expanded):
            config["image_directory"] = img_dir
            break
        print(f"  Directory not found: {img_dir}")
        if not ask_yn("  Try again?", default=True):
            print("  Setup cancelled.")
            return

    # ── Step 4: Save config ──────────────────────────────────
    print()
    print("─" * 56)
    print(" [4/5] Saving config + Building exe ...")
    print()

    config["launch_wezterm"] = True
    config["window_mode"] = "fit_image"
    config["reference_cols"] = 60
    config["image_extensions"] = IMAGE_EXTENSIONS

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"  config.json saved")

    # ── Step 4b: Venv + PyInstaller ──────────────────────────
    venv_python = os.path.join(app_dir, "venv", "Scripts", "python.exe")
    if not os.path.isfile(venv_python):
        print("  Creating virtual environment ...")
        r = subprocess.run([sys.executable, "-m", "venv", "venv"],
                           cwd=app_dir, capture_output=True)
        if r.returncode != 0:
            print("  [FAILED] venv creation failed.  Is Python installed?")
            return
    subprocess.run([venv_python, "-m", "pip", "install", "--quiet",
                    "--disable-pip-version-check", "pyinstaller"],
                   cwd=app_dir, capture_output=True)
    print("  PyInstaller ready")

    # ── Step 4c: Build exe ───────────────────────────────────
    spec = os.path.join(app_dir, "TraceOn.spec")
    if os.path.isfile(spec):
        os.remove(spec)
    r = subprocess.run(
        [venv_python, "-m", "PyInstaller", "--onedir", "--name", "TraceOn",
         "--clean", "TraceOn.py"],
        cwd=app_dir, capture_output=True,
    )
    if r.returncode != 0:
        print("  [FAILED] Build failed.  Check console for errors.")
        return
    print("  TraceOn.exe built -> dist\\TraceOn\\")

    # ── Step 5: Add to PATH ──────────────────────────────────
    print()
    print("─" * 56)
    print(" [5/5] Adding to PATH ...")
    print()
    print(f"  Folder: {dist_dir}")
    print(f"  This allows you to type 'TraceOn' from any terminal.")
    print()
    if ask_yn("  Add to PATH?", default=True):
        if add_to_user_path(dist_dir):
            print(f"  Added to PATH.")
            print(f"  (Open a NEW terminal for it to take effect.)")
        else:
            print("  Already in PATH — nothing to do.")

    # ── Done ─────────────────────────────────────────────────
    print()
    print("=" * 56)
    print("  Install Complete!")
    print("=" * 56)
    print()
    print("  BEFORE YOU RUN TRACEON:")
    print()
    print("  1. Open your wezterm.lua:")
    print(f"     {config['wezterm_config_path']}")
    print()
    print("  2. Copy the TraceOn template from wezterm_template.lua")
    print("     into your wezterm.lua.  (Required — TraceOn needs")
    print("     specific variables to work.)")
    print()
    print("  3. Open a NEW terminal and run:")
    print("     TraceOn")
    print()
    print("  You're done!")
    print()


if __name__ == "__main__":
    main()
