# TraceOn — WezTerm 背景图随机切换器

每次在终端输入 `TraceOn`，从预设图片目录随机抽取一张设为 WezTerm 背景，
窗口尺寸自动匹配图片宽高比。

---

## 首次安装（拉取项目后只需 3 步）

### 前提

- Windows 10 / 11
- 已安装 [WezTerm](https://wezterm.org/)
- 已安装 [Python 3.8+](https://www.python.org/downloads/)（安装时勾选 "Add Python to PATH"）

### 第 1 步：配置 wezterm.lua（一次性）

打开你的 `wezterm.lua`（通常在 `C:\Users\你的用户名\.config\wezterm\wezterm.lua`），
参照 `wezterm_template.lua` 中的模板，加入 TraceOn 需要的三段代码。

也可直接把 `wezterm_template.lua` 中注释掉的完整示例复制过去作为起点。

### 第 2 步：双击运行安装程序

```
双击 install.bat
```

或：

```powershell
python install.py
```

**这一步会自动完成：**
- 检测 WezTerm 路径（找不到会提示你手动输入）
- 询问图片文件夹
- 生成 config.json
- 创建虚拟环境 + 安装 PyInstaller
- 打包 TraceOn.exe
- 将 `dist\TraceOn\` 加入 PATH

### 第 3 步：打开新终端，验证

```powershell
TraceOn
```

```
Found 274 images. Selected: example.jpg  (1920x1080 | cols=60 rows=15)
Background updated.
WezTerm started in: D:\Projects
```

---

## 日常使用

```powershell
# 任意目录下
TraceOn
```

---

## 项目文件

```
backgroudSwitcher/
├── TraceOn.py              # 主程序
├── install.py              # 首次配置向导
├── config.json             # 用户配置（install.py 生成）
├── wezterm_template.lua    # wezterm.lua 模板（复制到你的 wezterm.lua）
├── setup.bat               # 创建 venv + 安装 PyInstaller
├── build_exe.bat           # 打包为 dist\TraceOn\（--onedir 模式）
├── README.md               # 本文件
└── dist/
    └── TraceOn/
        ├── TraceOn.exe
        └── _internal/
```

---

## 配置项说明 (config.json)

| 字段 | 类型 | 说明 |
|------|------|------|
| `image_directory` | string | 存放背景图片的目录，**必须用正斜杠 `/`** |
| `wezterm_config_path` | string | `wezterm.lua` 的完整路径 |
| `wezterm_exe_path` | string | `wezterm-gui.exe` 的完整路径 |
| `launch_wezterm` | bool | 是否启动 WezTerm，默认 `true` |
| `window_mode` | string | `"fit_image"` = 窗口按图片比例 / `"default"` = 不调整 |
| `reference_cols` | int | fit_image 模式下的参考列宽，默认 60 |
| `image_extensions` | list | 支持的图片格式 |

```json
{
    "image_directory": "E:/Pictures/Wallpapers",
    "wezterm_config_path": "C:/Users/xxx/.config/wezterm/wezterm.lua",
    "wezterm_exe_path": "C:/Program Files/WezTerm/wezterm-gui.exe",
    "launch_wezterm": true,
    "window_mode": "fit_image",
    "reference_cols": 60,
    "image_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
}
```

---

## 工作原理

1. 读取同目录下的 `config.json`
2. 扫描 `image_directory` 中所有图片文件
3. 随机选取一张
4. 用纯 Python 读取图片尺寸（无需 Pillow），计算窗口行列数
5. 正则替换 `wezterm.lua` 中 `bg_image_path`、`bg_initial_cols`、`bg_initial_rows`
6. 在当前目录启动 WezTerm

---

## 常见问题

### Q: `TraceOn` 在终端中找不到？

A: PATH 里加的是**目录**（如 `D:\Tools\TraceOn`），不是 `.exe` 文件。加完后需新开终端。

### Q: Windows 阻止运行 / SmartScreen 弹窗？

A: exe 没有数字签名。右键 `TraceOn.exe` → 属性 → 勾选「解除锁定」→ 确定。
或在 PowerShell 中运行：`Get-ChildItem -Recurse | Unblock-File`

### Q: 运行后 WezTerm 报错？

A: 确认 `wezterm.lua` 中有 TraceOn 需要的模板变量。参考 `wezterm_template.lua`。

### Q: 只想换背景，不想打开新窗口？

A: `config.json` 中设 `"launch_wezterm": false`。

### Q: 怎么改窗口大小？

A: 调 `reference_cols`。当前 60，改大窗口更宽，改小更窄。
