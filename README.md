# SSA HDRify

> **将 SSA/ASS 字幕颜色从 SDR 色彩空间转换到 HDR 色彩空间的小工具。**
>
> *A tool to convert SSA/ASS subtitle colors from SDR to HDR color space.*

Fork 自 [gky99/ssaHdrify](https://github.com/gky99/ssaHdrify)，修复了若干 bug。

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
  ├─ 5. PQ (ST 2084) OETF 编码
  │     Apply PQ OETF encoding
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
2. 设置字幕目标亮度（默认 100 nits）/ Set target subtitle brightness (default: 100 nits)
3. 点击按钮选择字幕文件（支持多选）/ Click the button to select subtitle files (multi-select supported)
4. 输出文件扩展名为 `.hdr.ass` / Output files will have the `.hdr.ass` extension

> **参数说明 | Parameter Guide**
>
> | 参数 / Parameter | 默认值 / Default | 说明 / Description |
> |---|---|---|
> | Target brightness | 100 nits | SDR 字幕亮度峰值。字幕太亮就调低，太暗就调高。Peak brightness for SDR subtitles. Decrease if too bright, increase if too dim. |

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

## 致谢 | Credit

- 原项目 / Original project: [gky99/ssaHdrify](https://github.com/gky99/ssaHdrify)
- <a href="https://www.flaticon.com/free-icons/hdr" title="hdr icons">Hdr icons created by Freepik - Flaticon</a>
