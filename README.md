# maoqb-skills

A personal [Claude Code](https://claude.com/claude-code) skills marketplace.
Add it once and install any skill below on any device.

## Install

In Claude Code:

```
/plugin marketplace add maoqb/skills
/plugin install write-drawdoc@maoqb-skills
/plugin install gerrit-tool@maoqb-skills
/plugin install docforge@maoqb-skills
```

The first command registers this repo as a marketplace; the second installs a
skill from it. Restart Claude Code (or run `/plugin`) if a newly installed skill
doesn't show up immediately.

To update later:

```
/plugin marketplace update maoqb-skills
```

## Skills

### write-drawdoc

撰写 **`.drawdoc`** 文档——[DrawDocs](https://drawdocs.vercel.app) 的原生格式，是
Markdown 的严格超集：普通 Markdown（标题/表格/列表/代码）照常有效，额外内嵌三种**可编辑**
的图——`drawio` 围栏（mxGraph XML）、`excalidraw` 围栏（场景 JSON）与 `mermaid` 围栏
（mermaid 文本，裸围栏在 GitHub 上原生渲染），外加带宽度的图片
（`![alt](src "w=420")`，可内联成 data URI）。

产物拖进 <https://drawdocs.vercel.app> 即可打开继续编辑（图块双击进对应编辑器改），也可用
DrawDocs 的本地文件夹 / GitHub 模式打开。技能内置 `scripts/drawdoc.py` 组装器（按顺序追加
正文 / 图 / 白板 / mermaid / 图片块并写出 `.drawdoc`）；drawio 围栏接受 `.drawio` 路径或原始 mxGraph XML。
用「写一篇 .drawdoc」「生成能在 DrawDocs 里改的图文文档」等触发。

### gerrit-tool

在 **AOSP / repo 管理的多仓库工作区**里，把 Gerrit 上同一个 **topic** 下的所有 change
按依赖顺序 cherry-pick 到各自对应的项目目录。核心是 `scripts/gerrit_topic_pick.py`
（纯 python3 标准库）：

- 通过 **ssh** 查询 topic（`ssh -p 29418 <host> gerrit query`），复用 `repo sync`
  的那把 key，无需额外认证配置；Gerrit 地址可从 manifest 的 `review=` 属性自动发现。
- `repo list` 自动把 project 映射到本地目录，逐个 `repo download --cherry-pick`。
- 同一 relation chain 内 parent 先应用；已应用的 change 按 Change-Id 自动跳过，
  冲突解决后重跑同一条命令即可续摘。
- 支持 `--dry-run` 先看计划、`--status` / `--branch` 过滤；`--verify` 用
  `git patch-id` 比对 diff 内容，检出本地摘的是旧 patchset 的 change（标 `OUTDATED`）。

用「cherry-pick 某个 topic」「把 gerrit 上 topic X 的 patch 都摘下来」等触发。

### docforge

从代码、文档、issue、commit 或笔记等**有界源材料**生成一篇可溯源的技术文档。它把事实提取、结构与
图表撰写、质量复核分为串行的 GATHER → AUTHOR → VERIFY 三道门：每一条事实性论断和每个图元素都必须
映射到带 provenance 的 fact id；结构图使用手写 HTML/SVG，时序图才使用 Mermaid。适合「根据这个仓库
写一篇系统设计文档」「从这些变更整理技术说明」等需要可靠取据和可审计图文的请求。

该 skill 要求当前项目已经包含 DocForge 引擎（`AGENTS.md`、`scripts/docforge.py` 和
`.claude/contracts/`）。它不会猜造缺失的契约或来源。

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json     # marketplace + plugin definitions
└── skills/
    ├── write-drawdoc/
    │   ├── SKILL.md
    │   ├── scripts/        # drawdoc.py — .drawdoc 组装器
    │   └── references/     # format.md — .drawdoc 格式规范
    └── gerrit-tool/
        ├── SKILL.md
        └── scripts/        # gerrit_topic_pick.py — topic 批量 cherry-pick
    └── docforge/
        └── SKILL.md
```

## License

MIT
