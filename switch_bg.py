#!/usr/bin/env python3
"""WezTerm 背景图随机切换器

每次运行时，从指定目录随机选取一张图片，将其路径写入 wezterm.lua 的背景图配置中，
并可选择同时启动 WezTerm。

用法：
    python switch_bg.py                  # 随机切换背景并启动 WezTerm
    python switch_bg.py --no-launch      # 只切换背景，不启动 WezTerm
    python switch_bg.py --set-dir <DIR>  # 设置图片目录并保存到配置文件
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import platform


# ── 工具函数 ────────────────────────────────────────────


def is_wsl():
    """检测是否在 WSL 环境中运行"""
    release = platform.uname().release.lower()
    return 'microsoft' in release or 'wsl' in release


def windows_to_wsl_path(win_path):
    """将 Windows 路径转换为 WSL 路径（/mnt/x/...）

    Example:
        C:/Users/Dongcheng2/.config/wezterm/wezterm.lua
        → /mnt/c/Users/Dongcheng2/.config/wezterm/wezterm.lua
    """
    win_path = win_path.replace('\\', '/')
    if len(win_path) >= 2 and win_path[1] == ':':
        drive = win_path[0].lower()
        rest = win_path[2:]
        return f'/mnt/{drive}{rest}'
    return win_path


def wsl_to_windows_path(wsl_path):
    """将 WSL 路径（/mnt/x/...）转回 Windows 路径（X:/...）

    Example:
        /mnt/e/Picture/safe/img.jpg
        → E:/Picture/safe/img.jpg
    """
    wsl_path = wsl_path.replace('\\', '/')
    match = re.match(r'^/mnt/([a-zA-Z])/', wsl_path)
    if match:
        drive = match.group(1).upper()
        rest = wsl_path[7:]  # 去掉 /mnt/x/ 前缀（6 字符 + 1 斜杠）
        return f'{drive}:/{rest}'
    return wsl_path


def to_forward_slash(path):
    """将所有反斜杠替换为正斜杠"""
    return path.replace('\\', '/')


# ── 配置管理 ────────────────────────────────────────────


def load_config(config_path):
    """加载 JSON 配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_path, config):
    """保存 JSON 配置文件"""
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


# ── 核心逻辑 ────────────────────────────────────────────


def get_image_files(directory, extensions):
    """扫描目录下所有图片文件，返回完整路径列表"""
    image_files = []
    if not os.path.isdir(directory):
        print(f'[错误] 图片目录不存在: {directory}')
        return image_files

    for filename in sorted(os.listdir(directory)):
        ext = os.path.splitext(filename)[1].lower()
        if ext in extensions:
            full_path = os.path.join(directory, filename)
            image_files.append(full_path)

    return image_files


def update_wezterm_config(config_path, new_image_path):
    """更新 wezterm.lua 中 bg_image_path 变量的值

    使用正则匹配模式: local bg_image_path = "旧路径"
    替换为:             local bg_image_path = "新路径"
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(local\s+bg_image_path\s*=\s*")[^"]*(")'
    replacement = f'\\g<1>{new_image_path}\\g<2>'
    new_content = re.sub(pattern, replacement, content)

    if new_content == content:
        print('[警告] 未找到 bg_image_path 变量，请检查 wezterm.lua 格式')
        print(f'       期望格式: local bg_image_path = "路径"')
        return False

    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def launch_wezterm(exe_path):
    """在后台启动 WezTerm"""
    try:
        subprocess.Popen(
            [exe_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f'[信息] WezTerm 已启动')
        return True
    except FileNotFoundError:
        print(f'[错误] 找不到 WezTerm 可执行文件: {exe_path}')
        return False
    except Exception as e:
        print(f'[错误] 无法启动 WezTerm: {e}')
        return False


# ── 主入口 ──────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description='WezTerm 背景图随机切换器 — 从指定目录随机选取图片设为 WezTerm 背景'
    )
    parser.add_argument(
        '-c', '--config', default=None,
        help='配置文件路径（默认: 脚本同目录下的 config.json）',
    )
    parser.add_argument(
        '--no-launch', action='store_true',
        help='只切换背景图，不启动 WezTerm',
    )
    parser.add_argument(
        '--set-dir', default=None, metavar='DIR',
        help='设置图片目录路径并保存到配置文件',
    )
    parser.add_argument(
        '--set-wezterm-config', default=None, metavar='PATH',
        help='设置 wezterm.lua 路径并保存到配置文件',
    )
    parser.add_argument(
        '--set-wezterm-exe', default=None, metavar='PATH',
        help='设置 wezterm-gui.exe 路径并保存到配置文件',
    )
    args = parser.parse_args()

    # ── 确定配置文件路径 ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = args.config or os.path.join(script_dir, 'config.json')

    if not os.path.exists(config_path):
        print(f'[错误] 配置文件不存在: {config_path}')
        print('请先创建 config.json，或使用 --set-dir 指定图片目录')
        sys.exit(1)

    config = load_config(config_path)

    # ── 处理设置参数 ──
    need_save = False

    if args.set_dir:
        config['image_directory'] = args.set_dir
        need_save = True
        print(f'[信息] 图片目录已设置为: {args.set_dir}')

    if args.set_wezterm_config:
        config['wezterm_config_path'] = args.set_wezterm_config
        need_save = True
        print(f'[信息] wezterm.lua 路径已设置为: {args.set_wezterm_config}')

    if args.set_wezterm_exe:
        config['wezterm_exe_path'] = args.set_wezterm_exe
        need_save = True
        print(f'[信息] wezterm-gui.exe 路径已设置为: {args.set_wezterm_exe}')

    if need_save:
        save_config(config_path, config)

    # ── 如果只是设置路径（没有图片目录配置），则退出 ──
    if not config.get('image_directory'):
        print('[错误] 未配置图片目录，请使用 --set-dir <目录路径> 进行设置')
        sys.exit(1)

    # ── 解析图片目录为实际可访问的路径 ──
    image_dir = config['image_directory']

    # 总是先确保使用正斜杠
    image_dir = to_forward_slash(image_dir)
    config['image_directory'] = image_dir

    if is_wsl():
        scan_dir = windows_to_wsl_path(image_dir)
    else:
        scan_dir = image_dir

    # ── 扫描图片文件 ──
    exts = config.get('image_extensions', ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'])
    image_files = get_image_files(scan_dir, exts)

    if not image_files:
        print(f'[错误] 在目录 "{image_dir}" 中未找到任何图片文件')
        print(f'       支持的格式: {", ".join(exts)}')
        sys.exit(1)

    # ── 随机选一张 ──
    chosen = random.choice(image_files)
    print(f'[信息] 找到 {len(image_files)} 张图片，本次随机选中: {os.path.basename(chosen)}')

    # ── 构建写入 wezterm.lua 的路径（Windows 格式 + 正斜杠） ──
    if is_wsl():
        # chosen 是 /mnt/e/Picture/safe/img.jpg 格式，转回 E:/Picture/safe/img.jpg
        bg_path = wsl_to_windows_path(chosen)
    else:
        bg_path = to_forward_slash(chosen)

    print(f'[信息] 背景图路径: {bg_path}')

    # ── 解析 wezterm.lua 路径并更新 ──
    wezterm_config = to_forward_slash(config['wezterm_config_path'])
    if is_wsl():
        resolved_wezterm = windows_to_wsl_path(wezterm_config)
    else:
        resolved_wezterm = wezterm_config

    if not os.path.exists(resolved_wezterm):
        print(f'[错误] wezterm.lua 不存在: {wezterm_config}')
        print(f'       已尝试访问: {resolved_wezterm}')
        sys.exit(1)

    success = update_wezterm_config(resolved_wezterm, bg_path)
    if success:
        print(f'[成功] 已更新 wezterm.lua 背景图 → {os.path.basename(chosen)}')
    else:
        print(f'[失败] wezterm.lua 更新失败，未做任何更改')
        sys.exit(1)

    # ── 启动 WezTerm ──
    launch = config.get('launch_wezterm', True) and not args.no_launch
    if launch:
        wezterm_exe = config.get('wezterm_exe_path', '')
        if not wezterm_exe:
            print('[信息] 未配置 wezterm_exe_path，跳过启动 WezTerm')
        else:
            wezterm_exe = to_forward_slash(wezterm_exe)
            if is_wsl():
                exe_path = windows_to_wsl_path(wezterm_exe)
            else:
                exe_path = wezterm_exe
            launch_wezterm(exe_path)


if __name__ == '__main__':
    main()
