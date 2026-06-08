# mxGraph / .drawio file format

Read this when you need to hand-write XML — i.e. the layout is too custom for
the `Flowchart` / `Sequence` / `BlockDiagram` builders in `scripts/drawio.py`.
For the common cases, prefer the builders; they do the coordinate arithmetic.

## Skeleton

A `.drawio` file is one `<mxfile>` containing one or more `<diagram>` pages.
Inside each page is an `<mxGraphModel>` whose `<root>` holds every shape and
edge as an `<mxCell>`.

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Page-1" id="page1">
    <mxGraphModel dx="900" dy="600" grid="1" gridSize="10" page="1"
                  pageWidth="850" pageHeight="1100">
      <root>
        <mxCell id="0" />              <!-- root, required -->
        <mxCell id="1" parent="0" />   <!-- default layer, required -->

        <!-- a box (vertex) -->
        <mxCell id="n1" value="Hello" vertex="1" parent="1"
                style="rounded=0;whiteSpace=wrap;html=1;">
          <mxGeometry x="40" y="40" width="120" height="60" as="geometry" />
        </mxCell>

        <!-- a connector (edge) between two vertices -->
        <mxCell id="e1" value="" edge="1" parent="1" source="n1" target="n2"
                style="edgeStyle=orthogonalEdgeStyle;html=1;">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

Rules that bite if you forget them:
- Cells `id="0"` and `id="1"` must exist; everything else has `parent="1"`.
- A vertex needs `vertex="1"` + an `<mxGeometry>` with x/y/width/height.
- An edge needs `edge="1"` + `source`/`target` (cell ids) **or** explicit
  `sourcePoint`/`targetPoint` geometry. Its geometry is `relative="1"`.
- `id` values must be unique within the file.
- Coordinates are absolute pixels, origin top-left, y grows downward.

## Labels and text

- The `value` attribute is the label. With `html=1` in the style it may contain
  HTML; otherwise it's plain text.
- Escape `&` `<` `>` `"` as `&amp; &lt; &gt; &quot;`.
- A line break inside a label is `&#10;` (or `<br>` when `html=1`).
- UTF-8 text (Chinese, emoji, …) is fine directly in the file.

## Style strings

Style is a semicolon-separated `key=value;` list. Useful keys:

| Key | Effect |
| --- | --- |
| `rounded=1` | rounded rectangle corners |
| `whiteSpace=wrap;html=1` | wrap long labels (almost always include this) |
| `fillColor=#dae8fc;strokeColor=#6c8ebf` | fill + border colour |
| `fontColor=#333333;fontSize=12;fontStyle=1` | text (fontStyle: 1=bold,2=italic) |
| `dashed=1` | dashed border/line |
| `shape=...` | named shape (parallelogram, process, cylinder, cloud, …) |
| `rhombus` | diamond (decision) |
| `ellipse` | ellipse / circle |

Edge-only keys: `edgeStyle=orthogonalEdgeStyle` (elbow routing),
`endArrow=classic|block|open|none`, `startArrow=...`, `dashed=1`,
`exitX/exitY/entryX/entryY` (0..1 fractions to pin where an edge attaches).

## draw.io's standard colour pairs

These fill/stroke pairs are what draw.io's own palette uses — they look native:

| Name | fill | stroke |
| --- | --- | --- |
| blue | `#dae8fc` | `#6c8ebf` |
| green | `#d5e8d4` | `#82b366` |
| orange | `#ffe6cc` | `#d79b00` |
| yellow | `#fff2cc` | `#d6b656` |
| purple | `#e1d5e7` | `#9673a6` |
| red | `#f8cecc` | `#b85450` |
| gray | `#f5f5f5` | `#666666` |

## Containers / grouping

A cell with `style="...;container=1;"` and child cells whose `parent` is that
cell's id forms a group; child x/y are then relative to the container. The
`BlockDiagram.group()` helper instead draws a plain dashed rectangle *behind*
the blocks, which is simpler and avoids relative-coordinate surprises.

## Quick validation

After writing a file, well-formedness check:

```bash
python3 -c "import xml.dom.minidom as m; m.parse('out.drawio'); print('valid XML')"
```

This catches unescaped `&`/`<` and broken tags. It does not check that ids
referenced by edges exist — eyeball those, or just use the builders.
