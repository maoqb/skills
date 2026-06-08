# maoqb-skills

A personal [Claude Code](https://claude.com/claude-code) skills marketplace.
Add it once and install any skill below on any device.

## Install

In Claude Code:

```
/plugin marketplace add maoqb/skills
/plugin install drawio-diagrams@maoqb-skills
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

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json     # marketplace + plugin definitions
└── skills/
    └── drawio-diagrams/
        ├── SKILL.md
        ├── scripts/
        └── references/
```

## License

MIT
