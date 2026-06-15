# maoqb-skills

A personal [Claude Code](https://claude.com/claude-code) skills marketplace.
Add it once and install any skill below on any device.

## Install

In Claude Code:

```
/plugin marketplace add maoqb/skills
/plugin install write-drawdoc@maoqb-skills
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
Markdown 的严格超集：普通 Markdown（标题/表格/列表/代码）照常有效，额外内嵌两种**可编辑**
的图——`drawio` 围栏（mxGraph XML）与 `excalidraw` 围栏（场景 JSON），外加带宽度的图片
（`![alt](src "w=420")`，可内联成 data URI）。

产物拖进 <https://drawdocs.vercel.app> 即可打开继续编辑（图块双击进对应编辑器改），也可用
DrawDocs 的本地文件夹 / GitHub 模式打开。技能内置 `scripts/drawdoc.py` 组装器（按顺序追加
正文 / 图 / 白板 / 图片块并写出 `.drawdoc`）；drawio 围栏接受 `.drawio` 路径或原始 mxGraph XML。
用「写一篇 .drawdoc」「生成能在 DrawDocs 里改的图文文档」等触发。

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json     # marketplace + plugin definitions
└── skills/
    └── write-drawdoc/
        ├── SKILL.md
        ├── scripts/        # drawdoc.py — .drawdoc 组装器
        └── references/     # format.md — .drawdoc 格式规范
```

## License

MIT
