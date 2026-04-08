# Codemap — SSA HDRify

> 生成时间：2026-04-08 | 文件数：25 | 目录数：7

```
CC_ssaHdrify/
├── .github/
│   └── workflows/
│       ├── add-tag.yml             — 根据 VERSION 文件自动创建 git tag
│       ├── build.yml               — CI 构建流水线（测试 + 双平台 PyInstaller 打包）
│       └── on-push.yml             — push 时触发 add-tag 工作流
├── src/
│   ├── asset/
│   │   └── hdr.png                 — 应用图标源文件
│   ├── ui/
│   │   ├── options/
│   │   │   ├── BrightnessOption.py — 目标亮度输入框组件（带输入验证）
│   │   │   ├── EotfOption.py       — EOTF 曲线选择下拉框（当前仅 PQ）
│   │   │   └── FileSelectionButton.py — 文件选择与转换触发按钮（含线程管理）
│   │   ├── MessageFrame.py         — 消息输出面板（线程安全队列轮询）
│   │   ├── OptionFrame.py          — 选项区域容器（组合各选项组件）
│   │   └── Root.py                 — 主窗口（布局 + 关闭逻辑）
│   ├── conversion_setting.py       — 全局转换参数单例
│   ├── hdrify.py                   — 核心转换逻辑（sRGB→HDR 色彩空间映射）
│   └── main.py                     — 程序入口（初始化 GUI + 输出重定向）
├── tests/
│   ├── conftest.py                 — pytest 配置（添加 src/ 到路径）
│   └── test_hdrify.py              — 回归测试（色彩转换 + 正则 + 端到端）
├── .gitattributes                  — Git 换行符规范化配置
├── .gitignore                      — Git 忽略规则
├── hdr.icns                        — macOS 应用图标
├── hdr.ico                         — Windows 应用图标
├── LICENSE                         — GPLv3 开源协议
├── README.md                       — 项目说明文档
├── requirements.txt                — Python 依赖清单
├── ssa_hdrify_macos.spec           — macOS PyInstaller 打包配置
├── ssa_hdrify_windows.spec         — Windows PyInstaller 打包配置
└── VERSION                         — 版本号文件（git tag 来源）
```
