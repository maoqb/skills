# mxGraph / .drawio 文件格式

当你需要手写 XML 时读这篇——即布局太特殊，`scripts/drawio.py` 里的 `Flowchart` /
`Sequence` / `BlockDiagram` 构建器表达不了。常见情况优先用构建器，它们会替你算坐标。

## 骨架

一个 `.drawio` 文件是一个 `<mxfile>`，内含一个或多个 `<diagram>` 页面。每个页面里是一个
`<mxGraphModel>`，其 `<root>` 以 `<mxCell>` 的形式持有每个图形和连线。

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

忘了就会出问题的规则：
- `id="0"` 和 `id="1"` 两个 cell 必须存在；其它一切的 `parent="1"`。
- 一个 vertex 需要 `vertex="1"` + 一个带 x/y/width/height 的 `<mxGeometry>`。
- 一个 edge 需要 `edge="1"` + `source`/`target`（cell id）**或**显式的
  `sourcePoint`/`targetPoint` 几何。它的几何是 `relative="1"`。
- `id` 值在文件内必须唯一。
- 坐标是绝对像素，原点在左上角，y 向下增长。

## 标签与文本

- `value` 属性即标签。style 里带 `html=1` 时它可以含 HTML；否则是纯文本。
- 把 `&` `<` `>` `"` 转义为 `&amp; &lt; &gt; &quot;`。
- 标签内的换行是 `&#10;`（`html=1` 时则用 `<br>`）。
- UTF-8 文本（中文、emoji 等）可直接写进文件。

## 样式串（Style strings）

样式是一个用分号分隔的 `key=value;` 列表。常用键：

| 键 | 效果 |
| --- | --- |
| `rounded=1` | 圆角矩形 |
| `whiteSpace=wrap;html=1` | 长标签自动换行（几乎总要带上） |
| `fillColor=#dae8fc;strokeColor=#6c8ebf` | 填充色 + 边框色 |
| `fontColor=#333333;fontSize=12;fontStyle=1` | 文本（fontStyle：1=粗体，2=斜体） |
| `dashed=1` | 虚线边框/线 |
| `shape=...` | 具名形状（parallelogram、process、cylinder、cloud 等） |
| `rhombus` | 菱形（判断） |
| `ellipse` | 椭圆 / 圆 |

仅用于 edge 的键：`edgeStyle=orthogonalEdgeStyle`（折线布线）、
`endArrow=classic|block|open|none`、`startArrow=...`、`dashed=1`、
`exitX/exitY/entryX/entryY`（0..1 的比例，用来固定连线从哪里接出/接入）。

## draw.io 的标准配色对

下面这些 填充/描边 配对正是 draw.io 自带调色板所用，看起来很原生：

| 名称 | fill | stroke |
| --- | --- | --- |
| blue | `#dae8fc` | `#6c8ebf` |
| green | `#d5e8d4` | `#82b366` |
| orange | `#ffe6cc` | `#d79b00` |
| yellow | `#fff2cc` | `#d6b656` |
| purple | `#e1d5e7` | `#9673a6` |
| red | `#f8cecc` | `#b85450` |
| gray | `#f5f5f5` | `#666666` |

## 容器 / 分组

一个带 `style="...;container=1;"` 的 cell，加上若干 `parent` 为该 cell id 的子 cell，就构成一个
分组；此时子 cell 的 x/y 相对于容器。而 `BlockDiagram.group()` 辅助方法则改为在方框*背后*画一个
普通虚线矩形，更简单，也避免了相对坐标带来的意外。

## 快速校验

写完文件后，做一次格式正确性检查：

```bash
python3 -c "import xml.dom.minidom as m; m.parse('out.drawio'); print('valid XML')"
```

这能抓出未转义的 `&`/`<` 和损坏的标签。它不会检查 edge 引用的 id 是否存在——那些用眼睛核对，
或者干脆用构建器。
