"""drawio.py — build draw.io (mxGraph) diagrams programmatically.

Why this exists: the .drawio file format is mxGraph XML where every shape needs
explicit x/y/width/height. Hand-writing that is tedious and easy to get wrong —
especially sequence diagrams, where lifeline geometry has to line up across many
messages. This module does the arithmetic so you describe *what* connects to what
and it computes *where* things go.

Three high-level builders cover the common cases:
    Flowchart      — start/process/decision/io/end nodes on an auto grid
    Sequence       — participants across the top, ordered messages down the page
    BlockDiagram   — labelled blocks on a grid with connections + optional groups

For anything the builders don't cover, use the low-level `Diagram` directly:
it exposes add_vertex / add_edge / add_edge_points and you supply coordinates.

Every builder has .to_xml() and .save(path). Save with a .drawio extension; open
the result in draw.io desktop or https://app.diagrams.net . To export to PNG/SVG
use scripts/export.sh (needs the drawio CLI — see that file's header).

Labels may contain Chinese (or any UTF-8) text freely. Use "\n" inside a label
for a line break.
"""
from __future__ import annotations
from typing import Optional, Sequence as Seq


# --------------------------------------------------------------------------- #
# XML helpers
# --------------------------------------------------------------------------- #
def _esc(s) -> str:
    """Escape a value for use inside an XML attribute. Newlines become <br>."""
    if s is None:
        return ""
    s = str(s)
    s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
          .replace('"', "&quot;").replace("\n", "&#10;"))
    return s


def _wrap(name: str, cells_xml: str, width: int, height: int) -> str:
    return (
        '<mxfile host="app.diagrams.net" type="device">\n'
        f'  <diagram name="{_esc(name)}" id="{_esc(name)}">\n'
        '    <mxGraphModel dx="900" dy="600" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        f'pageWidth="{width}" pageHeight="{height}" math="0" shadow="0">\n'
        '      <root>\n'
        '        <mxCell id="0" />\n'
        '        <mxCell id="1" parent="0" />\n'
        f'{cells_xml}\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>\n'
    )


# Sensible default edge routing: orthogonal elbows, looks tidy for most diagrams.
EDGE_DEFAULT = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;"


# --------------------------------------------------------------------------- #
# Low-level diagram: you supply coordinates
# --------------------------------------------------------------------------- #
class Diagram:
    def __init__(self, name: str = "Page-1", width: int = 850, height: int = 1100):
        self.name = name
        self.width = width
        self.height = height
        self.cells: list[str] = []
        self._auto = 0

    def _next_id(self, prefix: str = "c") -> str:
        self._auto += 1
        return f"{prefix}{self._auto}"

    def add_vertex(self, value, x, y, w, h, style, cid=None, parent="1") -> str:
        cid = cid or self._next_id("n")
        self.cells.append(
            f'        <mxCell id="{cid}" value="{_esc(value)}" style="{style}" '
            f'vertex="1" parent="{parent}">\n'
            f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
            f'as="geometry" />\n'
            f'        </mxCell>'
        )
        return cid

    def add_edge(self, source, target, value="", style=EDGE_DEFAULT,
                 cid=None, parent="1") -> str:
        cid = cid or self._next_id("e")
        self.cells.append(
            f'        <mxCell id="{cid}" value="{_esc(value)}" style="{style}" '
            f'edge="1" parent="{parent}" source="{source}" target="{target}">\n'
            f'          <mxGeometry relative="1" as="geometry" />\n'
            f'        </mxCell>'
        )
        return cid

    def add_edge_points(self, x1, y1, x2, y2, value="", style=EDGE_DEFAULT,
                        cid=None, parent="1", waypoints=None) -> str:
        """An edge between two absolute points (no source/target cells).

        Used for sequence-diagram messages, where the arrow sits at a precise y
        between two lifelines rather than connecting to a node's perimeter.
        `waypoints` is an optional list of (x, y) elbow points — used to draw
        the little loop of a self-message.
        """
        cid = cid or self._next_id("e")
        wp = ""
        if waypoints:
            pts = "".join(f'            <mxPoint x="{x}" y="{y}" />\n'
                          for x, y in waypoints)
            wp = ('          <Array as="points">\n' + pts + '          </Array>\n')
        self.cells.append(
            f'        <mxCell id="{cid}" value="{_esc(value)}" style="{style}" '
            f'edge="1" parent="{parent}">\n'
            f'          <mxGeometry relative="1" as="geometry">\n'
            f'            <mxPoint x="{x1}" y="{y1}" as="sourcePoint" />\n'
            f'            <mxPoint x="{x2}" y="{y2}" as="targetPoint" />\n'
            f'{wp}'
            f'          </mxGeometry>\n'
            f'        </mxCell>'
        )
        return cid

    def to_xml(self) -> str:
        return _wrap(self.name, "\n".join(self.cells), self.width, self.height)

    def save(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_xml())
        return path


# --------------------------------------------------------------------------- #
# Style palette — consistent draw.io colours per shape role
# --------------------------------------------------------------------------- #
_FILL = {
    "blue":   "fillColor=#dae8fc;strokeColor=#6c8ebf;",
    "green":  "fillColor=#d5e8d4;strokeColor=#82b366;",
    "orange": "fillColor=#ffe6cc;strokeColor=#d79b00;",
    "yellow": "fillColor=#fff2cc;strokeColor=#d6b656;",
    "purple": "fillColor=#e1d5e7;strokeColor=#9673a6;",
    "red":    "fillColor=#f8cecc;strokeColor=#b85450;",
    "gray":   "fillColor=#f5f5f5;strokeColor=#666666;",
}


# --------------------------------------------------------------------------- #
# Flowchart
# --------------------------------------------------------------------------- #
class Flowchart:
    """Flowchart on an auto grid.

    Each node gets a row (auto-incrementing) and a column (default 0). Put
    branch targets in a different column to fan out. Coordinates are computed
    from row/col so you only think about layout, not pixels.

        fc = Flowchart()
        a = fc.start("开始")
        b = fc.process("读取配置")
        c = fc.decision("配置有效?")
        d = fc.process("加载服务", col=0)
        e = fc.io("打印错误", col=1, row=c_row)   # side branch
        z = fc.end("结束")
        fc.flow(a, b); fc.flow(b, c)
        fc.flow(c, d, "是"); fc.flow(c, e, "否")
        fc.flow(d, z); fc.flow(e, z)
        fc.save("flow.drawio")
    """
    COL_W = 220
    ROW_H = 110
    MARGIN_X = 60
    MARGIN_Y = 40
    W = 160
    H = 60

    _STYLES = {
        "start":    "rounded=1;arcSize=50;whiteSpace=wrap;html=1;" + _FILL["green"],
        "end":      "rounded=1;arcSize=50;whiteSpace=wrap;html=1;" + _FILL["red"],
        "process":  "rounded=0;whiteSpace=wrap;html=1;" + _FILL["blue"],
        "decision": "rhombus;whiteSpace=wrap;html=1;" + _FILL["orange"],
        "io":       "shape=parallelogram;perimeter=parallelogramPerimeter;"
                    "whiteSpace=wrap;html=1;" + _FILL["yellow"],
        "subprocess": "shape=process;whiteSpace=wrap;html=1;" + _FILL["purple"],
    }

    def __init__(self, name="Flowchart"):
        self.d = Diagram(name)
        self._row = 0

    def _node(self, kind, label, col=0, row=None, w=None, h=None):
        if row is None:
            row = self._row
            self._row += 1
        else:
            self._row = max(self._row, row + 1)
        w = w or self.W
        h = h or (80 if kind == "decision" else self.H)
        x = self.MARGIN_X + col * self.COL_W
        y = self.MARGIN_Y + row * self.ROW_H
        cid = self.d.add_vertex(label, x, y, w, h, self._STYLES[kind])
        return cid

    def start(self, label, **kw):       return self._node("start", label, **kw)
    def end(self, label, **kw):         return self._node("end", label, **kw)
    def process(self, label, **kw):     return self._node("process", label, **kw)
    def decision(self, label, **kw):    return self._node("decision", label, **kw)
    def io(self, label, **kw):          return self._node("io", label, **kw)
    def subprocess(self, label, **kw):  return self._node("subprocess", label, **kw)

    def flow(self, src, dst, label="", style=None):
        style = style or EDGE_DEFAULT
        return self.d.add_edge(src, dst, label, style)

    @property
    def current_row(self) -> int:
        return self._row

    def to_xml(self):  return self.d.to_xml()
    def save(self, path): return self.d.save(path)


# --------------------------------------------------------------------------- #
# Sequence diagram
# --------------------------------------------------------------------------- #
class Sequence:
    """UML-style sequence diagram.

    Declare participants left-to-right, then add messages top-to-bottom. The
    builder draws each participant's header box and dashed lifeline, and places
    every message arrow at the right y. Lifelines automatically extend to cover
    all messages.

        sq = Sequence()
        u  = sq.participant("用户")
        api = sq.participant("API 服务")
        db = sq.participant("数据库")
        sq.message(u, api, "登录(账号, 密码)")
        sq.message(api, db, "查询用户")
        sq.message(db, api, "用户记录", kind="return")
        sq.message(api, api, "校验密码", kind="self")
        sq.message(api, u, "登录成功", kind="return")
        sq.save("seq.drawio")

    message kind:
        "call"   solid arrow  (default; synchronous call)
        "async"  open arrow   (asynchronous / signal)
        "return" dashed arrow (reply)
        "self"   loop back to the same lifeline
    """
    GAP = 200          # horizontal distance between lifelines
    MARGIN_X = 80
    HEAD_Y = 40
    HEAD_W = 140
    HEAD_H = 40
    FIRST_MSG_Y = 140
    STEP_H = 50

    _HEAD_STYLE = ("rounded=0;whiteSpace=wrap;html=1;"
                   "fillColor=#dae8fc;strokeColor=#6c8ebf;")
    _LIFELINE_STYLE = ("html=1;endArrow=none;dashed=1;strokeColor=#666666;"
                       "rounded=0;")
    _MSG = {
        "call":   "html=1;endArrow=block;rounded=0;",
        "async":  "html=1;endArrow=open;rounded=0;",
        "return": "html=1;endArrow=open;dashed=1;rounded=0;",
    }

    def __init__(self, name="Sequence"):
        self.name = name
        self._participants: list[str] = []
        self._messages: list[tuple] = []  # (src_idx, dst_idx, label, kind)

    def participant(self, label) -> int:
        self._participants.append(label)
        return len(self._participants) - 1

    def message(self, src: int, dst: int, label="", kind="call") -> None:
        self._messages.append((src, dst, label, kind))

    def _cx(self, idx: int) -> int:
        return self.MARGIN_X + idx * self.GAP + self.HEAD_W // 2

    def to_xml(self) -> str:
        d = Diagram(self.name)
        n_msg = len(self._messages)
        bottom = self.FIRST_MSG_Y + max(n_msg, 1) * self.STEP_H + 40
        # headers + lifelines
        for i, label in enumerate(self._participants):
            x = self.MARGIN_X + i * self.GAP
            d.add_vertex(label, x, self.HEAD_Y, self.HEAD_W, self.HEAD_H,
                         self._HEAD_STYLE)
            cx = self._cx(i)
            d.add_edge_points(cx, self.HEAD_Y + self.HEAD_H, cx, bottom,
                              "", self._LIFELINE_STYLE)
        # messages
        for k, (src, dst, label, kind) in enumerate(self._messages):
            y = self.FIRST_MSG_Y + k * self.STEP_H
            if kind == "self" or src == dst:
                cx = self._cx(src)
                # a small loop to the right of the lifeline: out, down, back
                d.add_edge_points(
                    cx, y, cx, y + 30, label,
                    "html=1;endArrow=block;rounded=0;"
                    "verticalAlign=bottom;align=left;spacingLeft=8;",
                    waypoints=[(cx + 60, y), (cx + 60, y + 30)])
                continue
            style = self._MSG.get(kind, self._MSG["call"])
            d.add_edge_points(self._cx(src), y, self._cx(dst), y, label, style)
        # widen page if many participants
        d.width = max(850, self.MARGIN_X * 2 + len(self._participants) * self.GAP)
        d.height = max(1100, bottom + 40)
        return d.to_xml()

    def save(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_xml())
        return path


# --------------------------------------------------------------------------- #
# Block / architecture diagram
# --------------------------------------------------------------------------- #
class BlockDiagram:
    """Boxes on a grid with connections — for architecture / block diagrams.

        bd = BlockDiagram()
        web = bd.block("Web 前端", col=0, row=0, color="blue")
        api = bd.block("API 网关", col=1, row=0, color="green")
        svc = bd.block("订单服务", col=2, row=0)
        db  = bd.block("PostgreSQL", col=2, row=1, color="gray")
        bd.connect(web, api, "HTTPS")
        bd.connect(api, svc, "gRPC")
        bd.connect(svc, db, "SQL")
        bd.group("后端", [svc, db])         # optional dashed container behind
        bd.save("arch.drawio")

    Use col/row for grid placement, or pass explicit x=/y= for free positioning.
    connect(directed=False) draws a line with no arrowhead (e.g. a data bus).
    """
    COL_W = 220
    ROW_H = 140
    MARGIN = 60
    W = 160
    H = 70

    def __init__(self, name="Block Diagram"):
        self.d = Diagram(name)
        self._pos: dict[str, tuple] = {}  # cid -> (x, y, w, h)
        self._pending_groups: list[tuple] = []

    def block(self, label, col=0, row=0, x=None, y=None, w=None, h=None,
              color="blue", rounded=True) -> str:
        w = w or self.W
        h = h or self.H
        if x is None:
            x = self.MARGIN + col * self.COL_W
        if y is None:
            y = self.MARGIN + row * self.ROW_H
        style = (f"rounded={1 if rounded else 0};whiteSpace=wrap;html=1;"
                 + _FILL.get(color, _FILL["blue"]))
        cid = self.d.add_vertex(label, x, y, w, h, style)
        self._pos[cid] = (x, y, w, h)
        return cid

    def connect(self, src, dst, label="", directed=True, dashed=False) -> str:
        style = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;"
        style += "endArrow=classic;" if directed else "endArrow=none;startArrow=none;"
        if dashed:
            style += "dashed=1;"
        return self.d.add_edge(src, dst, label, style)

    def group(self, label, members: Seq[str], color="gray", pad=20) -> str:
        """Draw a dashed labelled container behind the given blocks."""
        xs = [self._pos[m] for m in members if m in self._pos]
        if not xs:
            return ""
        minx = min(p[0] for p in xs) - pad
        miny = min(p[1] for p in xs) - pad - 10
        maxx = max(p[0] + p[2] for p in xs) + pad
        maxy = max(p[1] + p[3] for p in xs) + pad
        style = ("rounded=1;whiteSpace=wrap;html=1;dashed=1;"
                 "verticalAlign=top;fontStyle=1;fillColor=none;"
                 f"strokeColor=#999999;")
        cid = self.d._next_id("g")
        # insert the group cell at the FRONT so it renders behind the blocks
        cell = (
            f'        <mxCell id="{cid}" value="{_esc(label)}" style="{style}" '
            f'vertex="1" parent="1">\n'
            f'          <mxGeometry x="{minx}" y="{miny}" '
            f'width="{maxx-minx}" height="{maxy-miny}" as="geometry" />\n'
            f'        </mxCell>'
        )
        self.d.cells.insert(0, cell)
        return cid

    def to_xml(self):  return self.d.to_xml()
    def save(self, path): return self.d.save(path)


# --------------------------------------------------------------------------- #
# Smoke test: `python drawio.py` writes one of each into /tmp
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    fc = Flowchart()
    a = fc.start("开始")
    b = fc.process("读取输入")
    c = fc.decision("有效?")
    err = fc.io("报错", col=1, row=2)
    d = fc.process("处理")
    z = fc.end("结束")
    fc.flow(a, b); fc.flow(b, c)
    fc.flow(c, d, "是"); fc.flow(c, err, "否")
    fc.flow(d, z); fc.flow(err, z)
    print(fc.save("/tmp/_demo_flow.drawio"))

    sq = Sequence()
    u = sq.participant("用户"); api = sq.participant("API"); db = sq.participant("DB")
    sq.message(u, api, "登录")
    sq.message(api, db, "查询")
    sq.message(db, api, "结果", kind="return")
    sq.message(api, u, "成功", kind="return")
    print(sq.save("/tmp/_demo_seq.drawio"))

    bd = BlockDiagram()
    w = bd.block("Web", col=0, row=0, color="blue")
    g = bd.block("网关", col=1, row=0, color="green")
    s = bd.block("服务", col=2, row=0)
    db2 = bd.block("数据库", col=2, row=1, color="gray")
    bd.connect(w, g, "HTTPS"); bd.connect(g, s); bd.connect(s, db2, "SQL")
    bd.group("后端", [s, db2])
    print(bd.save("/tmp/_demo_block.drawio"))
