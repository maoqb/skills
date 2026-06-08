---
name: drawio-diagrams
description: >-
  Create editable draw.io (.drawio) diagrams — block/architecture diagrams (框图/架构图),
  sequence diagrams (时序图/序列图), and flowcharts (流程图) — by generating mxGraph XML
  programmatically, optionally exporting to PNG/SVG. Use this whenever the user wants to
  draw, diagram, or visualize a flow, process, algorithm, system architecture, component
  layout, module relationship, request/response interaction, or call sequence — including
  phrasings like "画个流程图", "画一个时序图", "框图", "画张架构图", "draw a flowchart/sequence/block
  diagram", "diagram this", "可视化这个流程", or asking for a .drawio/diagrams.net file. Prefer
  this over ASCII art or Mermaid when the user names drawio/diagrams.net or wants an
  editable diagram file they can open and tweak.
---

# drawio-diagrams

Generate editable `.drawio` files (mxGraph XML) for three diagram families:
**block/architecture (框图)**, **sequence (时序图)**, and **flowchart (流程图)**.
The output opens in draw.io desktop or <https://app.diagrams.net> for editing,
and can be exported to PNG/SVG.

## Why a builder instead of raw XML

The `.drawio` format places every shape at explicit pixel coordinates. Writing
that by hand is slow and error-prone — sequence diagrams especially, where each
message must align across vertical lifelines. `scripts/drawio.py` does the
geometry: you describe *what connects to what*, it computes *where things go*.
Reach for raw XML only for layouts the builders can't express.

## Workflow

1. **Identify the diagram type** from the request:
   - steps / decisions / "如果…则…" / an algorithm → **flowchart**
   - actors exchanging messages over time, request/response, call order → **sequence**
   - components / modules / services and how they connect → **block/architecture**
   - If genuinely ambiguous, ask; otherwise pick the best fit and proceed.

2. **Read the matching reference** for the API and a worked example:
   - `references/flowchart.md`
   - `references/sequence.md`
   - `references/block.md`
   - `references/format.md` — only when hand-writing custom XML.

3. **Build it** with `scripts/drawio.py`. Write a short Python script that
   imports the right builder, declares nodes/messages/blocks, and calls
   `.save("<name>.drawio")`. Keep `sys.path.insert(0, "<skill>/scripts")` at the
   top so the import resolves. Choose a descriptive output filename; default to
   the current working directory unless the user specifies a path.

4. **Validate** the file is well-formed:
   ```bash
   python3 -c "import xml.dom.minidom as m; m.parse('<name>.drawio'); print('OK')"
   ```

5. **Export only if asked** for an image (PNG/SVG/PDF). Run
   `scripts/export.sh <name>.drawio png`. This needs the drawio CLI; if it's not
   installed the script prints install instructions. The `.drawio` file is
   always the primary deliverable — never block on export tooling.

6. **Tell the user** the file path, that it's editable in draw.io /
   app.diagrams.net, and (if relevant) how to export an image.

## Quoting the skill path

Throughout, replace `<skill>` with this skill's directory (the folder
containing this SKILL.md). A robust pattern inside a generated script:

```python
import os, sys
SKILL = os.path.dirname(os.path.abspath(__file__))  # if script lives in <skill>
sys.path.insert(0, os.path.join(SKILL, "scripts"))
```

or just hard-code the absolute path to `scripts/` that you can see from the
skill location.

## Conventions that keep diagrams readable

- Short labels; let shape and colour carry the meaning. The builders use
  draw.io's native colour palette so results look hand-made, not generated.
- One concept per box; push detail to a second label line with `\n`.
- Label every decision branch ("是"/"否") and every sequence message.
- Match the user's language in labels (Chinese stays Chinese).

## Scope

Covers flowcharts, sequence diagrams, and block/architecture diagrams. For
other draw.io chart types (ER, mind maps, org charts, Gantt), the low-level
`Diagram` class plus `references/format.md` still apply — you supply the
coordinates and styles.
