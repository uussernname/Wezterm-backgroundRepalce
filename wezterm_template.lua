-- ============================================================
-- TraceOn 所需的 wezterm.lua 模板片段
-- 复制以下内容到你的 wezterm.lua 中对应位置
-- ============================================================

-- 在文件顶部 require 之后、config.xxx 之前插入这三行变量：
-- ============================================================
-- 背景图路径 (由 TraceOn 自动更新，不要手动改)
-- ============================================================
local bg_image_path = ""
local bg_initial_cols = 120
local bg_initial_rows = 40


-- 在 config 区域插入以下背景图配置：
-- ============================================================
-- 背景图配置
-- ============================================================
config.background = {
    {
        source = { File = bg_image_path },

        -- 缩放模式 (可选值: "Cover" | "Contain" | "100%" )
        width = "Cover",
        height = "Cover",

        -- 对齐方式
        -- horizontal_align: "Left" | "Center" | "Right"
        -- vertical_align  : "Top"  | "Middle" | "Bottom"
        horizontal_align = "Center",
        vertical_align = "Middle",

        -- 亮度: 0.0=黑, 1.0=原图, >1.0=更亮
        hsb = { brightness = 0.3 },
    },
}


-- 窗口初始尺寸 (由 TraceOn 自动更新)
config.initial_cols = bg_initial_cols
config.initial_rows = bg_initial_rows


-- ============================================================
-- 完整 wezterm.lua 示例 (供参考)
-- ============================================================
--[[
local wezterm = require 'wezterm'
local config = wezterm.config_builder()

-- ★ TraceOn 变量 (必须保留)
local bg_image_path = ""
local bg_initial_cols = 120
local bg_initial_rows = 40

-- 你的其他配置
config.color_scheme = 'Tokyo Night Storm'
config.font = wezterm.font('JetBrains Mono')
config.font_size = 12.0

-- ★ TraceOn 背景图配置 (必须保留)
config.background = {
    {
        source = { File = bg_image_path },
        width = "Cover",
        height = "Cover",
        horizontal_align = "Center",
        vertical_align = "Middle",
        hsb = { brightness = 0.3 },
    },
}

config.colors = {
    background = '#1E1E2E',
    foreground = '#CDD6F4',
}

-- ★ TraceOn 窗口尺寸 (必须保留)
config.initial_cols = bg_initial_cols
config.initial_rows = bg_initial_rows

config.enable_tab_bar = true

return config
--]]
