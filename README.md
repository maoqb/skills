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

Generate editable **draw.io** (`.drawio`, mxGraph XML) diagrams programmatically
and optionally export them to PNG/SVG/PDF. Covers three families:

- **Flowcharts (流程图)** — start/process/decision/io/end nodes on an auto grid
- **Sequence diagrams (时序图)** — participants + ordered messages, lifelines auto-aligned
- **Block / architecture diagrams (框图)** — labelled blocks, connections, grouped layers

The skill bundles a Python builder (`scripts/drawio.py`) that does the coordinate
math, reference docs per diagram type, and an export script. Trigger it by asking
Claude to "draw a flowchart / sequence diagram / architecture diagram", "画个流程图",
"画一张架构框图", etc.

**Optional dependency:** image export needs the draw.io desktop CLI
(`brew install --cask drawio` on macOS). The `.drawio` file itself opens in
draw.io desktop or <https://app.diagrams.net> with no install.

### aosp-module-doc

Generate a complete technical document for **one AOSP module or tool** — the
build system, a tool like `release_config` / `aconfig` / Soong, or a framework
subsystem like `init` / binder / `system_server`. Every factual claim is verified
against **current upstream source** (read live from `android.googlesource.com`),
not training memory, so the output tracks the latest AOSP instead of going stale.

The article follows a fixed structure — 概述 → 整体架构 → 数据/概念 → 各子模块 →
关键流程 → 配置与使用 → 调试工具 → 参考文档 — with numbered headings, a table of
contents, and embedded draw.io diagrams (an architecture 框图 plus per-submodule
时序图/示意图, produced via the `drawio-diagrams` skill). It also searches the
official docs and absorbs what improves the article. Trigger it with "写/生成 AOSP
XXX 模块/工具的文档", "讲清楚 AOSP 的 XXX 机制", etc.

The skill bundles `scripts/md2html.py`, a zero-dependency converter that renders
the Markdown to a styled standalone HTML with a clickable, auto-generated TOC.

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
