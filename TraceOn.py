#!/usr/bin/env python3
"""TraceOn — Random background switcher for WezTerm

Run 'TraceOn' in any terminal to:
  1. Pick a random image from a configured directory
  2. Write it as WezTerm's background in wezterm.lua
  3. Open WezTerm in the current directory

On first run, a default config.json is generated next to the executable.
Edit it to change the image directory or toggle auto-launch.
"""

import json
import os
import random
import re
import struct
import subprocess
import sys
import platform


# ── Default config ────────────────────────────────────────

DEFAULT_CONFIG = {
    "image_directory": "E:/Picture/safe",
    "wezterm_config_path": "C:/Users/Dongcheng2/.config/wezterm/wezterm.lua",
    "wezterm_exe_path": "D:/app/WezTerm/WezTerm/wezterm-gui.exe",
    "launch_wezterm": True,
    "window_mode": "fit_image",
    "reference_cols": 60,
    "image_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
}


# ── Environment detection ─────────────────────────────────


def is_wsl():
    """Detect if running inside WSL"""
    release = platform.uname().release.lower()
    return 'microsoft' in release or 'wsl' in release


def get_app_dir():
    """Get the directory containing the executable or script"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))


# ── Path utilities ────────────────────────────────────────


def windows_to_wsl_path(win_path):
    """Convert a Windows path to a WSL path (/mnt/x/...)"""
    win_path = win_path.replace('\\', '/')
    if len(win_path) >= 2 and win_path[1] == ':':
        drive = win_path[0].lower()
        rest = win_path[2:]
        return f'/mnt/{drive}{rest}'
    return win_path


def wsl_to_windows_path(wsl_path):
    """Convert a WSL path (/mnt/x/...) back to a Windows path (X:/...)"""
    wsl_path = wsl_path.replace('\\', '/')
    match = re.match(r'^/mnt/([a-zA-Z])/', wsl_path)
    if match:
        drive = match.group(1).upper()
        rest = wsl_path[7:]  # skip /mnt/x/ prefix
        return f'{drive}:/{rest}'
    return wsl_path


def to_forward_slash(path):
    """Replace all backslashes with forward slashes"""
    return path.replace('\\', '/')


# ── Config management ─────────────────────────────────────


def load_config(config_path):
    """Load JSON config file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_path, config):
    """Save JSON config file"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def ensure_config(config_path):
    """Create default config.json if it doesn't exist yet"""
    if not os.path.exists(config_path):
        save_config(config_path, DEFAULT_CONFIG)
        print('[init] Default config created:')
        print(f'       {config_path}')
        print(f'  Edit "image_directory" to set your image folder.')
        print(f'  Current default: {DEFAULT_CONFIG["image_directory"]}')
        return False
    return True


# ── Core logic ────────────────────────────────────────────


def get_image_files(directory, extensions):
    """Scan a directory for image files matching the given extensions"""
    image_files = []
    if not os.path.isdir(directory):
        print(f'[error] Image directory not found: {directory}')
        return image_files

    for filename in sorted(os.listdir(directory)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in extensions:
            full_path = os.path.join(directory, filename)
            image_files.append(full_path)

    return image_files


def get_image_size(filepath):
    """Read image dimensions (width, height) without external libraries.

    Supports: JPEG, PNG, GIF, BMP, WebP.
    Returns (width, height) or (0, 0) on failure.
    """
    try:
        with open(filepath, 'rb') as f:
            head = f.read(32)
            if len(head) < 2:
                return (0, 0)

            # JPEG: look for SOF0/SOF2 marker (0xFF 0xC0 ~ 0xFF 0xC2)
            if head[:2] == b'\xff\xd8':
                f.seek(2)
                while True:
                    chunk = f.read(4)
                    if len(chunk) < 4:
                        break
                    marker, length = struct.unpack('>HH', chunk)
                    if 0xFFC0 <= marker <= 0xFFC2:
                        data = f.read(6)
                        if len(data) >= 6:
                            _, h, w, _ = struct.unpack('>BHHB', data)
                            return (w, h)
                        f.seek(length - 8, 1)  # already consumed 6 extra bytes
                    else:
                        f.seek(length - 2, 1)
                return (0, 0)

            # PNG: IHDR chunk
            if head[:8] == b'\x89PNG\r\n\x1a\n':
                f.seek(16)
                data = f.read(8)
                w, h = struct.unpack('>II', data)
                return (w, h)

            # GIF: logical screen descriptor
            if head[:6] in (b'GIF87a', b'GIF89a'):
                w, h = struct.unpack('<HH', head[6:10])
                return (w, h)

            # BMP: DIB header
            if head[:2] == b'BM':
                f.seek(18)
                data = f.read(8)
                w, h = struct.unpack('<ii', data)
                return (abs(w), abs(h))

            # WebP: VP8 / VP8L / VP8X
            if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
                fmt = head[12:16]
                if fmt == b'VP8 ':  # lossy
                    data = f.read(10)[-4:]
                    w = struct.unpack('<H', data[0:2])[0] & 0x3FFF
                    h = struct.unpack('<H', data[2:4])[0] & 0x3FFF
                    return (w, h)
                elif fmt == b'VP8L':  # lossless
                    f.seek(21)
                    data = f.read(4)
                    bits = struct.unpack('<I', data)[0]
                    w = (bits & 0x3FFF) + 1
                    h = ((bits >> 14) & 0x3FFF) + 1
                    return (w, h)
                elif fmt == b'VP8X':  # extended
                    f.seek(24)
                    data = f.read(6)
                    w = struct.unpack('<I', data[:3] + b'\x00')[0] + 1
                    h = struct.unpack('<I', data[3:] + b'\x00')[0] + 1
                    return (w, h)

    except Exception:
        pass
    return (0, 0)


def update_wezterm_config(config_path, new_image_path, initial_cols=None, initial_rows=None):
    """Update bg_image_path (and inject/update cols/rows) in wezterm.lua"""
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # bg_image_path — always update
    content = re.sub(
        r'(local\s+bg_image_path\s*=\s*")[^"]*(")',
        f'\\g<1>{new_image_path}\\g<2>',
        content,
    )

    # Anchor: line after bg_image_path, for injecting missing vars
    anchor = f'local bg_image_path = "{new_image_path}"'
    anchor_idx = content.find(anchor)
    if anchor_idx != -1:
        anchor_eol = content.index('\n', anchor_idx)

        # bg_initial_cols — update existing, or inject
        if initial_cols is not None:
            if 'bg_initial_cols' in content:
                content = re.sub(
                    r'(local\s+bg_initial_cols\s*=\s*)[\d.]+',
                    f'\\g<1>{initial_cols}',
                    content,
                )
            else:
                content = (
                    content[:anchor_eol + 1]
                    + f'local bg_initial_cols = {initial_cols}\n'
                    + content[anchor_eol + 1:]
                )

        # bg_initial_rows — update existing, or inject
        if initial_rows is not None:
            if 'bg_initial_rows' in content:
                content = re.sub(
                    r'(local\s+bg_initial_rows\s*=\s*)[\d.]+',
                    f'\\g<1>{initial_rows}',
                    content,
                )
            else:
                content = (
                    content[:anchor_eol + 1]
                    + f'local bg_initial_rows = {initial_rows}\n'
                    + content[anchor_eol + 1:]
                )

    # Ensure config.initial_cols / config.initial_rows exist
    if 'config.initial_cols' not in content:
        content = content.replace(
            'return config',
            'config.initial_cols = bg_initial_cols\nconfig.initial_rows = bg_initial_rows\n\nreturn config',
        )
    if 'config.initial_rows' not in content:
        # initial_cols was injected but not rows
        content = content.replace(
            'config.initial_cols = bg_initial_cols\n',
            'config.initial_cols = bg_initial_cols\nconfig.initial_rows = bg_initial_rows\n',
        )

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return True



def launch_wezterm(exe_path, cwd):
    """Launch WezTerm in the given working directory"""
    try:
        subprocess.Popen(
            [exe_path, 'start', '--cwd', cwd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f'WezTerm started in: {cwd}')
        return True
    except FileNotFoundError:
        print(f'[error] WezTerm executable not found: {exe_path}')
        print(f'  Edit config.json "wezterm_exe_path" to fix.')
        return False
    except Exception as e:
        print(f'[error] Failed to launch WezTerm: {e}')
        return False


# ── Entry point ───────────────────────────────────────────


def main():
    app_dir = get_app_dir()
    config_path = os.path.join(app_dir, 'config.json')

    # First run: generate default config
    if not ensure_config(config_path):
        return

    # Load config
    config = load_config(config_path)

    image_dir = config.get('image_directory', '')
    if not image_dir:
        print(f'[error] image_directory is not set')
        print(f'  Edit {config_path} to set your image folder path.')
        return

    wezterm_config = config.get('wezterm_config_path', '')
    if not wezterm_config:
        print(f'[error] wezterm_config_path is not set')
        print(f'  Edit {config_path} to set your wezterm.lua path.')
        return

    exts = config.get('image_extensions', ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'])

    # Resolve image directory
    image_dir = to_forward_slash(image_dir)

    if is_wsl():
        scan_dir = windows_to_wsl_path(image_dir)
    else:
        scan_dir = image_dir

    # Scan for images
    image_files = get_image_files(scan_dir, exts)

    if not image_files:
        print(f'[error] No image files found in: {image_dir}')
        print(f'        Supported formats: {", ".join(exts)}')
        return

    # Pick a random image
    chosen = random.choice(image_files)
    print(f'Found {len(image_files)} images. Selected: {os.path.basename(chosen)}')

    # Build Windows-style path for wezterm.lua
    if is_wsl():
        bg_path = wsl_to_windows_path(chosen)
    else:
        bg_path = to_forward_slash(chosen)

    # Resolve wezterm.lua path and update
    wezterm_config = to_forward_slash(wezterm_config)
    if is_wsl():
        resolved_wezterm = windows_to_wsl_path(wezterm_config)
    else:
        resolved_wezterm = wezterm_config

    if not os.path.exists(resolved_wezterm):
        print(f'[error] wezterm.lua not found: {wezterm_config}')
        return

    # Calculate window cols/rows to match image aspect ratio
    cols, rows = None, None
    window_mode = config.get('window_mode', 'default')
    if window_mode == 'fit_image':
        ref_cols = config.get('reference_cols', 120)
        img_w, img_h = get_image_size(chosen)
        if img_w > 0 and img_h > 0:
            # char cell aspect: ~0.45 for JetBrains Mono at normal line height
            char_aspect = 0.45
            image_aspect = img_w / img_h
            cols = ref_cols
            rows = int(ref_cols / image_aspect * char_aspect)
            rows = max(10, min(rows, 200))  # clamp to reasonable range

    success = update_wezterm_config(resolved_wezterm, bg_path, cols, rows)
    if success:
        if cols and rows:
            print(f'Background updated -> {os.path.basename(chosen)}  '
                  f'({img_w}x{img_h} | cols={cols} rows={rows})')
        else:
            print(f'Background updated -> {os.path.basename(chosen)}')

    # Launch WezTerm
    launch = config.get('launch_wezterm', True)
    if launch:
        wezterm_exe = config.get('wezterm_exe_path', '')
        if not wezterm_exe:
            print('[info] wezterm_exe_path not set, skipping launch.')
        else:
            wezterm_exe = to_forward_slash(wezterm_exe)
            if is_wsl():
                exe_path = windows_to_wsl_path(wezterm_exe)
            else:
                exe_path = wezterm_exe
            cwd = os.getcwd()
            if is_wsl():
                cwd = wsl_to_windows_path(cwd)
            launch_wezterm(exe_path, cwd)


if __name__ == '__main__':
    main()
