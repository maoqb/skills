# The `.drawdoc` format

`.drawdoc` is **DrawDocs' native document format — a strict superset of Markdown.**
Open one at <https://drawdocs.vercel.app>. Everything a normal Markdown renderer
understands stays valid; DrawDocs adds three fenced "macro" blocks and one image
convention on top.

A `.drawdoc` file that contains only standard Markdown is also a perfectly valid
`.md` file. The extra syntax below is what makes it a `.drawdoc`.

## 1. Standard Markdown (unchanged)

Headings, **bold**, *italic*, ~~strike~~, `inline code`, links, blockquotes,
ordered/unordered lists, tables (GFM pipe tables), fenced code blocks, horizontal
rules — all behave exactly as in Markdown and round-trip losslessly through the
DrawDocs editor.

## 2. drawio diagram macro

A fenced block whose language is **`drawio`**; its content is **mxGraph XML**
(`<mxfile>…</mxfile>`, the same XML draw.io / diagrams.net saves).

````text
```drawio
<mxfile><diagram name="Page-1"><mxGraphModel><root>
  <mxCell id="0"/><mxCell id="1" parent="0"/>
  <mxCell id="2" value="Box A" style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf"
          vertex="1" parent="1">
    <mxGeometry x="40" y="40" width="120" height="60" as="geometry"/>
  </mxCell>
</root></mxGraphModel></diagram></mxfile>
```
````

DrawDocs renders it inline as an SVG; double-clicking opens the full drawio editor.
The XML may be single- or multi-line; it must not contain a triple-backtick.

## 3. Excalidraw whiteboard macro

A fenced block whose language is **`excalidraw`**; its content is an Excalidraw
**scene JSON** (`{"type":"excalidraw","elements":[…],"appState":{…}}`).

````text
```excalidraw
{"type":"excalidraw","version":2,"elements":[
  {"id":"a1","type":"rectangle","x":80,"y":80,"width":160,"height":70, … }
],"appState":{"viewBackgroundColor":"#ffffff"},"files":{}}
```
````

An **empty** ` ```excalidraw ` block (no content) is valid — it shows a blank
whiteboard placeholder to draw on by hand inside DrawDocs.

Each element needs the full Excalidraw field set (`id, type, x, y, width, height,
angle, strokeColor, backgroundColor, fillStyle, strokeWidth, strokeStyle,
roughness, opacity, groupIds, seed, version, versionNonce, …`); text elements add
`text, originalText, fontSize, fontFamily, textAlign, verticalAlign, lineHeight`.
Use `scripts/drawdoc.py`'s `ex_rect / ex_text / ex_ellipse / ex_arrow /
excalidraw_scene` helpers, which fill every field — hand-writing these is the
usual source of "blank whiteboard" bugs.

## 4. Mermaid diagram macro

A fenced block whose language is **`mermaid`**; its content is **Mermaid text**
(flowchart / sequence / gantt / class …, the same syntax mermaid.js parses).

````text
```mermaid
graph TD
  A[Start] --> B{Choice}
  B -->|yes| C[Do]
  B -->|no|  D[End]
```
````

DrawDocs renders it inline as an SVG; double-clicking opens a source editor with a
live preview. The text must not contain a triple-backtick.

A **bare** ` ```mermaid ` fence (no layout params) is **GitHub-native**: GitHub
renders it as a diagram directly, so prefer mermaid for flowcharts/sequence
diagrams that should look good both in DrawDocs and on GitHub. (Adding `width=` /
`align=` makes GitHub fall back to showing it as a code block — see §5.)

## 5. Layout params on the fence info line

All three macro fences accept optional **width** (px) and **align** (`left`/
`center`/`right`) right after the language, space-separated, `key=value`:

````text
```drawio width=600 align=center
…XML…
```
```excalidraw width=400
…JSON…
```
````

- `width` is an integer; `align` is one of `left|center|right` (`left` is the
  default and is omitted).
- A standard Markdown renderer ignores anything after the language word, so these
  params survive `.drawdoc` ⇄ plain-Markdown round-trips. Note for **mermaid**:
  adding params keeps the diagram editable in DrawDocs but makes GitHub show it as
  a code block instead of rendering it — omit params if GitHub-native rendering
  matters.
- Order is always `width` then `align`. Illegal values are ignored by DrawDocs.

## 6. Image width convention

DrawDocs stores an image's display width in the Markdown **title slot** as
`w=<px>`:

```text
![Architecture](assets/arch.png "w=420")
![Logo](data:image/png;base64,iVBORw0KGgo… "w=120")
```

- A normal renderer shows the title as a harmless tooltip; DrawDocs reads `w=N`
  as the rendered width and lets the user drag-resize.
- `src` may be a relative path **or a `data:` URI**. Inlining as a data URI makes
  the `.drawdoc` a single self-contained file (drag-and-drop into DrawDocs works
  with no surrounding folder). Relative paths need DrawDocs' Local-folder mode so
  it can resolve them.
- HTML `<img src=… width=…>` is also accepted on load (DrawDocs converts it to
  this form), but emit the Markdown form above.

## 7. Opening a `.drawdoc` in DrawDocs

1. **Drag-and-drop** the `.drawdoc` (or `.md`) file onto
   <https://drawdocs.vercel.app> — it opens straight into the editor. Best paired
   with data-URI images so the single file is self-contained.
2. **Local-folder mode** — sidebar → *本地 / Local* tab → *打开本地文件夹*, pick the
   folder, click the file. Edits auto-save back to disk. Use this when images are
   separate relative files.
3. **GitHub mode** — commit the `.drawdoc` to a repo, then browse to it in the
   sidebar's GitHub tab and push edits back.

## Minimal valid example

````text
# 部署架构

服务整体如下图：

```drawio width=560 align=center
<mxfile><diagram name="Page-1"><mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="2" value="Client" style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf" vertex="1" parent="1"><mxGeometry x="40" y="40" width="120" height="50" as="geometry"/></mxCell>
<mxCell id="3" value="API" style="rounded=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1"><mxGeometry x="240" y="40" width="120" height="50" as="geometry"/></mxCell>
<mxCell id="4" style="edgeStyle=orthogonalEdgeStyle" edge="1" parent="1" source="2" target="3"><mxGeometry relative="1" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>
```

> 双击图块可在 DrawDocs 内打开 drawio 编辑器继续修改。
````
