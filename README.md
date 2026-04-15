# SSA HDRify

> [!NOTE]
> **本项目已迁移至 Tauri 版本** — 新功能将在 [ssaHdrify-tauri](https://github.com/LtxPoi/ssaHdrify-tauri) 开发。此 Python 版本不再计划新功能，但仍接受 bug 反馈。
>
> **Development has moved to the Tauri version** — new features will be developed in [ssaHdrify-tauri](https://github.com/LtxPoi/ssaHdrify-tauri). This Python version is no longer actively developed, but bug reports are still welcome.

> **将 SSA/ASS 字幕颜色从 SDR 色彩空间转换到 HDR 色彩空间的小工具。**
>
> *A tool to convert SSA/ASS subtitle colors from SDR to HDR color space.*

Fork 自 [gky99/ssaHdrify](https://github.com/gky99/ssaHdrify)，包含多项 bug 修复与质量改进。

---

## 使用场景

播放 HDR 视频时，显示器会进入 HDR 模式。然而 SSA/ASS 字幕格式没有色彩空间元数据，字幕渲染器会将颜色当作 SDR 处理，导致字幕**过饱和、过亮**。

> 如果你的播放器已经能正确处理字幕亮度（例如 mpv 的 `blend-subtitles=video`，或 madVR 配合 xy-SubFilter 的字幕色彩管理），则不需要本工具。

相关讨论：[libass/libass#297](https://github.com/libass/libass/issues/297)

## Background

When playing HDR video, the display enters HDR mode. However, SSA/ASS subtitles lack color space metadata — the renderer treats them as SDR, causing subtitles to appear **oversaturated and overly bright**.

> If your player already handles subtitle brightness correctly (e.g. mpv with `blend-subtitles=video`, or madVR with xy-SubFilter color management), you don't need this tool.

Related discussion: [libass/libass#297](https://github.com/libass/libass/issues/297)

---

## 转换原理 | How It Works

```
SSA/ASS 字幕颜色 (sRGB)
  │
  ├─ 1. BT.709 OETF 线性化
  │     Linearize with BT.709 OETF
  │
  ├─ 2. sRGB → CIE xyY 色彩空间
  │     Map from sRGB to CIE xyY
  │
  ├─ 3. 调整亮度 Y（保持色度 xy 不变）
  │     Scale luminance Y, preserve chromaticity xy
  │     例 / e.g.: SDR 100nit, 显示器 10000nit → Y × 0.01
  │
  ├─ 4. CIE xyY → BT.2020 RGB
  │     Map from CIE xyY to BT.2020 RGB
  │
  ├─ 5. PQ (ST 2084) 或 HLG (ARIB STD-B67) OETF 编码
  │     Apply PQ or HLG OETF encoding
  │
  └─ 6. 输出 RGB
        Output RGB
```

### 精度说明 | Accuracy Note

理论上这个流程可以保证颜色准确。但由于字幕混合管线和 HDR 显示的不确定性（HDMI 元数据匹配、显示器 tone mapping 等），**实际效果只能保证"红是红、蓝是蓝"，不适用于对颜色精度有严格要求的场景**。

Theoretically this process preserves color accuracy. However, due to the complex subtitle blending pipeline and HDR display behavior (HDMI metadata matching, display-side tone mapping, etc.), **the result is only to the effect of "red is red and blue is blue" — not suitable for scenarios requiring strict color accuracy**.

---

## 使用方法 | How to Use

1. 运行程序 / Run the program
2. 选择 EOTF 曲线（PQ 或 HLG）/ Select EOTF curve (PQ or HLG)
3. 设置字幕目标亮度（默认 203 nits）/ Set target subtitle brightness (default: 203 nits)
4. 点击按钮选择字幕文件（支持多选）/ Click the button to select subtitle files (multi-select supported)
5. 输出文件扩展名为 `.hdr.ass` / Output files will have the `.hdr.ass` extension

> **参数说明 | Parameter Guide**
>
> | 参数 / Parameter | 默认值 / Default | 说明 / Description |
> |---|---|---|
> | EOTF curve | PQ | PQ (ST 2084) 用于 HDR10/杜比视界；HLG 用于广播 HDR。PQ for HDR10/Dolby Vision; HLG for broadcast HDR. |
> | Target brightness | 203 nits | SDR 字幕亮度峰值（BT.2408 标准值）。字幕太亮就调低，太暗就调高。Peak brightness per BT.2408. Decrease if too bright, increase if too dim. |
>
> 界面支持中英双语切换（左上角 Language 按钮）。
> UI supports English/Chinese switching (top-left Language button).

---

## 依赖 | Dependencies

| 包 / Package | 用途 / Purpose |
|---|---|
| [ass](https://pypi.org/project/ass/) | SSA/ASS 字幕解析 / Subtitle parsing |
| [colour-science](https://pypi.org/project/colour-science/) | 色彩空间转换 / Color space transformations |
| [numpy](https://pypi.org/project/numpy/) | 数值计算 / Numerical computation |
| [charset-normalizer](https://pypi.org/project/charset-normalizer/) | 文件编码检测 / File encoding detection |
| [Pillow](https://pypi.org/project/pillow/) | 窗口图标加载 / Window icon loading |

从源码运行时，先在项目根目录安装依赖：

When running from source, install dependencies in the project root:

```bash
cd path/to/ssaHdrify
pip install -r requirements.txt
python src/main.py
```

---

## 改进 | Improvements over upstream

相比原项目，本 fork 增加了以下改进：

Compared to the upstream project, this fork includes the following improvements:

- **输入验证 | Input validation**: 亮度输入框清空后阻止转换，防止静默使用旧值 / Prevents conversion with empty brightness field
- **CI 安全 | CI security**: VERSION 文件内容正则校验，防止命令注入 / Regex validation of VERSION file content
- **构建可靠性 | Build reliability**: PyInstaller 版本号改用环境变量传递，图标使用绝对路径 / ENV var for version, absolute icon paths
- **颜色正则 | Color regex**: 只匹配 6/8 位十六进制颜色，避免误匹配 / Only matches valid 6/8-digit hex colors
- **编码检测 | Encoding detection**: 低置信度时输出警告，提示可能乱码 / Warns when encoding detection confidence is low
- **安全关闭 | Safe shutdown**: 关闭窗口时主动取消工作线程，不留后台进程 / Cancels worker thread on window close
- **HLG 支持 | HLG support**: 新增 BT.2100 HLG 色彩空间，EOTF 下拉框可选 PQ/HLG / Added HLG color space, EOTF dropdown with PQ/HLG
- **中英双语 | i18n**: 界面支持中英文切换，首次跟随系统语言，选择自动保存 / UI language switching (EN/CN), persists to config
- **高 DPI 适配 | High DPI**: Windows Per-Monitor DPI Aware v2，文字清晰不模糊 / Crisp text on high-DPI displays
- **EOTF 说明 | EOTF description**: 下拉框下方动态显示选项释义 / Dynamic explanation below EOTF dropdown
- **亮度推荐 | Brightness recommendation**: 输入框下方显示推荐范围，随 EOTF 切换 / Dynamic recommendation follows EOTF
- **默认亮度 | Default brightness**: 从 100 改为 203 nits（BT.2408 标准）/ Changed from 100 to 203 nits per BT.2408
- **单文件打包 | One-file packaging**: Windows exe 从文件夹模式改为单文件 / Single exe instead of folder
- **BOM 编码检测 | BOM detection**: UTF-8/UTF-16 BOM 显式检测，优先于统计推断 / Explicit BOM detection before inference
- **CI 测试 | CI testing**: 13 个 pytest 回归测试（含 HLG），打包前必须通过 / 13 pytest tests (incl. HLG), must pass before packaging
- **CI 优化 | CI optimization**: path filter 避免非代码变更触发构建 / Path filter prevents builds on non-code changes
- **Python 3.14 兼容 | Python 3.14 support**: 放宽依赖版本约束 / Loosened dependency version constraints

---

## 致谢 | Credit

- 原项目 / Original project: [gky99/ssaHdrify](https://github.com/gky99/ssaHdrify)
- <a href="https://www.flaticon.com/free-icons/hdr" title="hdr icons">Hdr icons created by Freepik - Flaticon</a>
