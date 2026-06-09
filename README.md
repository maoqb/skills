# maoqb-skills

A personal [Claude Code](https://claude.com/claude-code) skills marketplace.
Add it once and install any skill below on any device.

## Install

In Claude Code:

```
/plugin marketplace add maoqb/skills
/plugin install drawio-diagrams@maoqb-skills
/plugin install aosp-module-doc@maoqb-skills
```

The first command registers this repo as a marketplace; the second installs a
skill from it. Restart Claude Code (or run `/plugin`) if a newly installed skill
doesn't show up immediately.

To update later:

```
/plugin marketplace update maoqb-skills
```

## Skills

### drawio-diagrams

以程序化方式生成可编辑的 **draw.io**（`.drawio`，mxGraph XML）图，并可选导出为
PNG/SVG/PDF。覆盖三类：

- **流程图** —— start/process/decision/io/end 节点，自动网格布局
- **时序图** —— 参与者 + 有序消息，生命线自动对齐
- **框图/架构图** —— 带标签的方框、连线、分组分层

技能内置一个 Python 构建器（`scripts/drawio.py`）负责坐标计算，每类图各有参考文档，
另带一个导出脚本。让 Claude「画个流程图」「画一张架构框图」「draw a flowchart /
sequence diagram」等即可触发。

**可选依赖：** 导出图片需要 draw.io 桌面版 CLI（macOS 上 `brew install --cask drawio`）。
`.drawio` 文件本身用 draw.io 桌面版或 <https://app.diagrams.net> 即可打开，无需安装。

### aosp-module-doc

为**单个 AOSP 模块或工具**生成一篇完整的技术文档——编译系统、`release_config` /
`aconfig` / Soong 这类工具，或 `init` / binder / `system_server` 这类框架子系统。每一条
事实都对照**当前上游源码**核实（实时读取 `android.googlesource.com`），不凭训练记忆，
所以产出始终跟随最新 AOSP，而不会过时。

文章结构固定——概述 → 整体架构 → 数据/概念 → 各子模块 → 关键流程 → 配置与使用 →
调试工具 → 参考文档——标题带序号、附目录，并内嵌 draw.io 图（一张架构框图，外加每个子模块
各自的时序图/示意图，由 `drawio-diagrams` 技能生成）。它还会检索官方文档，吸收能提升质量的
内容。用「写/生成 AOSP XXX 模块/工具的文档」「讲清楚 AOSP 的 XXX 机制」等触发。

技能内置 `scripts/md2html.py`，一个零依赖的转换器，可把 Markdown 渲染成带可点击目录、
样式美观的独立 HTML。

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json     # marketplace + plugin definitions
└── skills/
    ├── drawio-diagrams/
    │   ├── SKILL.md
    │   ├── scripts/
    │   └── references/
    └── aosp-module-doc/
        ├── SKILL.md
        └── scripts/
```

## License

MIT
