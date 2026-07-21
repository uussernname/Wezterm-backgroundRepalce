# TraceOn — WezTerm 背景图随机切换器

每次在终端输入 `TraceOn`，从预设图片目录随机抽取一张设为 WezTerm 背景。

---

## 快速开始（三选一）

### 方式一：从源码运行

```powershell
# 1. 进入项目目录
cd D:\UselessFile\backgroudSwitcher

# 2. 一键安装配置（自动检测 WezTerm 路径，询问图片目录）
python install.py

# 3. 日常使用
python TraceOn.py
```

### 方式二：打包为 exe 后运行

```powershell
# 1. 创建虚拟环境并安装 PyInstaller
.\setup.bat

# 2. 运行配置脚本
python install.py

# 3. 打包
.\build_exe.bat

# 4. 把 dist\TraceOn\ 文件夹复制到固定位置（如 D:\Tools\TraceOn\）
# 5. 将该目录加入系统 PATH
# 6. 在任意终端输入 TraceOn
```

### 方式三：直接使用已打包的 exe

```powershell
# 1. 将 dist\TraceOn\ 整个文件夹复制到 D:\Tools\TraceOn\
# 2. 在 D:\Tools\TraceOn\ 下运行配置
cd D:\Tools\TraceOn
python install.py

# 3. 在任意终端输入 TraceOn
```

---

## 项目文件说明

```
backgroudSwitcher/
├── TraceOn.py          # 主程序 — 随机选图、更新 wezterm.lua、启动 WezTerm
├── install.py          # 安装脚本 — 首次配置向导（检测路径 + 生成 config.json）
├── config.json         # 配置文件（由 install.py 生成，也可手动编辑）
├── setup.bat           # 一键创建 venv + 安装 PyInstaller
├── build_exe.bat       # 一键打包为 dist\TraceOn\TraceOn.exe（--onedir 模式）
└── README.md           # 本文件
```

---

## install.py 配置向导说明

运行 `python install.py` 后会依次执行：

| 步骤 | 内容 | 自动检测 | 手动输入 |
|------|------|----------|----------|
| 1 | 定位 `wezterm.lua` | `%USERPROFILE%\.config\wezterm\` / `%APPDATA%\wezterm\` | 提供完整路径 |
| 2 | 定位 `wezterm-gui.exe` | 系统 PATH / `Program Files\WezTerm\` / LocalAppData | 提供完整路径 |
| 3 | 设置图片目录 | — | 提供目录路径 |
| 4 | 保存 config.json | — | — |
| 可选 | 添加到用户 PATH | 通过注册表修改 | — |

### config.json 示例

```json
{
    "image_directory": "E:/Pictures/Wallpapers",
    "wezterm_config_path": "C:/Users/YourName/.config/wezterm/wezterm.lua",
    "wezterm_exe_path": "C:/Program Files/WezTerm/wezterm-gui.exe",
    "launch_wezterm": true,
    "image_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
}
```

> **注意**：所有路径使用正斜杠 `/`，不要用反斜杠。

---

## 配置项说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image_directory` | string | 是 | 存放背景图片的目录，支持中文路径 |
| `wezterm_config_path` | string | 是 | `wezterm.lua` 文件的完整路径 |
| `wezterm_exe_path` | string | 是 | `wezterm-gui.exe` 的完整路径 |
| `launch_wezterm` | bool | 否 | 是否自动启动 WezTerm，默认 `true` |
| `image_extensions` | list | 否 | 支持的图片格式，默认 `.jpg .jpeg .png .gif .bmp .webp` |

---

## 工作原理

1. `TraceOn` 被调用
2. 读取同目录下的 `config.json`
3. 扫描 `image_directory` 中所有支持的图片文件
4. 随机选取一张
5. 用正则替换 `wezterm.lua` 中 `bg_image_path` 的值（路径自动转正斜杠）
6. 在**当前目录**启动 WezTerm（`wezterm-gui.exe start --cwd`）

### wezterm.lua 要求

你的 `wezterm.lua` 中需要有以下格式的背景图配置：

```lua
local bg_image_path = "E:/Pictures/wallpaper.jpg"

config.background = {
    {
        source = { File = bg_image_path },
        hsb = { brightness = 0.3 },
    },
}
```

> `TraceOn` 只替换 `bg_image_path` 变量的值，其余配置原封不动。

---

## 从源码构建 exe

```powershell
# 1. 首次需要创建 venv（仅一次）
.\setup.bat

# 2. 打包（每次修改 TraceOn.py 后执行）
.\build_exe.bat

# 输出在 dist\TraceOn\ 目录
```

打包使用 `--onedir` 模式，避免 `--onefile` 向 `%TEMP%` 解压时被安全软件拦截。

---

## 要求

- **操作系统**：Windows 10 / 11
- **Python**：3.8+（仅在从源码运行时需要）
- **WezTerm**：已安装并配置好 `wezterm.lua`

---

## 常见问题

### Q: `TraceOn` 在终端中找不到？

A: 检查 PATH 环境变量：
- 确保添加的是 **目录**（如 `D:\Tools\TraceOn`），不是 `.exe` 文件路径
- 添加后需要**新开一个终端**窗口才能生效

### Q: 运行后 WezTerm 没有变化？

A: WezTerm 需要刷新才能加载新背景配置。按 `Ctrl+Shift+R` 或在 WezTerm 中执行 `wezterm restart`。

### Q: 只想更新背景，不想打开新的 WezTerm 窗口？

A: 编辑 `config.json`，将 `"launch_wezterm"` 设为 `false`。

### Q: 修改图片目录后如何更新配置？

A: 两种方法：
- 重新运行 `python install.py`
- 直接编辑 `config.json` 中的 `image_directory`
