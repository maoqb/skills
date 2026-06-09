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
the result in draw.io desktop or https://app.diagrams.net .

SVG export (no external tools needed):
    builder.save_svg("diagram.svg")   # pure-Python, always works
    builder.to_svg()                  # returns SVG string

PNG/SVG via drawio CLI (higher fidelity, needs drawio desktop):
    scripts/export.sh diagram.drawio [png|svg]
    — export.sh falls back to Python SVG automatically when drawio is absent.

Labels may contain Chinese (or any UTF-8) text freely. Use "\\n" inside a label
for a line break.
"""
from __future__ import annotations
from typing import Optional, Sequence as Seq


# --------------------------------------------------------------------------- #
# XML helpers
# --------------------------------------------------------------------------- #
def _esc(s) -> str:
    """Escape a value for use inside an XML attribute. Newlines become &#10;."""
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
# SVG helpers (used by to_svg() methods)
# --------------------------------------------------------------------------- #
def _svg_esc(s: str) -> str:
    """Escape for SVG text content."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _svg_text(x, y, text, anchor="middle", fontsize=12, fill="#000000",
              bold=False, box_h=None, max_w=None) -> str:
    """Multi-line SVG text, vertically centered when box_h is given."""
    lines = str(text).split("\n")
    weight = "bold" if bold else "normal"
    line_h = fontsize + 4
    total_h = len(lines) * line_h
    if box_h is not None:
        start_y = y + (box_h - total_h) / 2 + fontsize
    else:
        start_y = y + fontsize
    parts = []
    for i, line in enumerate(lines):
        ty = start_y + i * line_h
        parts.append(
            f'<text x="{x}" y="{ty:.1f}" text-anchor="{anchor}" '
            f'font-family="Arial,Helvetica,sans-serif" font-size="{fontsize}" '
            f'font-weight="{weight}" fill="{fill}">{_svg_esc(line)}</text>'
        )
    return "\n".join(parts)


# Color fill/stroke pairs matching _FILL
_SVG_COLORS = {
    "blue":   ("#dae8fc", "#6c8ebf"),
    "green":  ("#d5e8d4", "#82b366"),
    "orange": ("#ffe6cc", "#d79b00"),
    "yellow": ("#fff2cc", "#d6b656"),
    "purple": ("#e1d5e7", "#9673a6"),
    "red":    ("#f8cecc", "#b85450"),
    "gray":   ("#f5f5f5", "#666666"),
}

_SVG_DEFS = """\
<defs>
  <marker id="arr-block" markerWidth="10" markerHeight="7"
          refX="9" refY="3.5" orient="auto">
    <polygon points="0 0,10 3.5,0 7" fill="#000000"/>
  </marker>
  <marker id="arr-open" markerWidth="12" markerHeight="8"
          refX="10" refY="4" orient="auto">
    <polyline points="0 1,10 4,0 7" fill="none" stroke="#000000" stroke-width="1.2"/>
  </marker>
  <marker id="arr-open-dash" markerWidth="12" markerHeight="8"
          refX="10" refY="4" orient="auto">
    <polyline points="0 1,10 4,0 7" fill="none" stroke="#000000" stroke-width="1.2"/>
  </marker>
</defs>"""


def _border_pt(bx, by, bw, bh, tx, ty):
    """Point on box border in the direction of (tx, ty) from box centre."""
    cx, cy = bx + bw / 2, by + bh / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (bw / 2) / abs(dx) if dx != 0 else 1e9
    sy = (bh / 2) / abs(dy) if dy != 0 else 1e9
    t = min(sx, sy)
    return cx + dx * t, cy + dy * t


def _svg_header(width, height) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            f'style="background:white;font-family:Arial,Helvetica,sans-serif;">')


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
        self._nodes: dict[str, tuple] = {}   # cid -> (kind, label, x, y, w, h)
        self._flows: list[tuple] = []        # (src, dst, label)

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
        self._nodes[cid] = (kind, label, x, y, w, h)
        return cid

    def start(self, label, **kw):       return self._node("start", label, **kw)
    def end(self, label, **kw):         return self._node("end", label, **kw)
    def process(self, label, **kw):     return self._node("process", label, **kw)
    def decision(self, label, **kw):    return self._node("decision", label, **kw)
    def io(self, label, **kw):          return self._node("io", label, **kw)
    def subprocess(self, label, **kw):  return self._node("subprocess", label, **kw)

    def flow(self, src, dst, label="", style=None):
        style = style or EDGE_DEFAULT
        self._flows.append((src, dst, label))
        return self.d.add_edge(src, dst, label, style)

    @property
    def current_row(self) -> int:
        return self._row

    def to_xml(self):  return self.d.to_xml()
    def save(self, path): return self.d.save(path)

    def to_svg(self) -> str:
        _COLOR_MAP = {
            "start": "green", "end": "red", "process": "blue",
            "decision": "orange", "io": "yellow", "subprocess": "purple",
        }
        parts = []
        # compute canvas size
        max_x = max_y = 0
        for _, (kind, label, x, y, w, h) in self._nodes.items():
            max_x = max(max_x, x + w)
            max_y = max(max_y, y + h)
        width = max_x + self.MARGIN_X
        height = max_y + self.MARGIN_Y
        parts.append(_svg_header(width, height))
        parts.append(_SVG_DEFS)
        parts.append(f'<rect width="{width}" height="{height}" fill="white"/>')
        # draw edges first (behind nodes)
        for src, dst, label in self._flows:
            if src not in self._nodes or dst not in self._nodes:
                continue
            _, _, sx, sy, sw, sh = self._nodes[src]
            _, _, dx, dy, dw, dh = self._nodes[dst]
            scx, scy = sx + sw/2, sy + sh/2
            dcx, dcy = dx + dw/2, dy + dh/2
            x1, y1 = _border_pt(sx, sy, sw, sh, dcx, dcy)
            x2, y2 = _border_pt(dx, dy, dw, dh, scx, scy)
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#000" stroke-width="1.5" marker-end="url(#arr-block)"/>')
            if label:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                parts.append(
                    f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" '
                    f'font-size="11" fill="#333">{_svg_esc(label)}</text>')
        # draw nodes
        for cid, (kind, label, x, y, w, h) in self._nodes.items():
            fc, sc = _SVG_COLORS.get(_COLOR_MAP.get(kind, "blue"), ("#dae8fc", "#6c8ebf"))
            if kind == "decision":
                cx, cy = x + w/2, y + h/2
                pts = f"{cx},{y} {x+w},{cy} {cx},{y+h} {x},{cy}"
                parts.append(f'<polygon points="{pts}" fill="{fc}" stroke="{sc}" stroke-width="1.5"/>')
            elif kind in ("start", "end"):
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="30" ry="30" '
                    f'fill="{fc}" stroke="{sc}" stroke-width="1.5"/>')
            else:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                    f'fill="{fc}" stroke="{sc}" stroke-width="1.5"/>')
            cx = x + w/2
            parts.append(_svg_text(cx, y, label, anchor="middle", fontsize=12, box_h=h))
        parts.append('</svg>')
        return "\n".join(parts)

    def save_svg(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_svg())
        return path


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

    def to_svg(self) -> str:
        n_msg = len(self._messages)
        n_par = len(self._participants)
        width = max(900, self.MARGIN_X * 2 + n_par * self.GAP + self.HEAD_W // 2)
        bottom = self.FIRST_MSG_Y + max(n_msg, 1) * self.STEP_H + 60
        height = bottom + 20

        parts = [_svg_header(width, height), _SVG_DEFS,
                 f'<rect width="{width}" height="{height}" fill="white"/>']

        # ── headers + lifelines ──────────────────────────────────────────────
        for i, label in enumerate(self._participants):
            hx = self.MARGIN_X + i * self.GAP
            cx = self._cx(i)
            # header box
            parts.append(
                f'<rect x="{hx}" y="{self.HEAD_Y}" '
                f'width="{self.HEAD_W}" height="{self.HEAD_H}" '
                f'fill="#dae8fc" stroke="#6c8ebf" stroke-width="1.5" rx="2"/>')
            parts.append(_svg_text(cx, self.HEAD_Y, label, anchor="middle",
                                   fontsize=11, box_h=self.HEAD_H))
            # lifeline
            parts.append(
                f'<line x1="{cx}" y1="{self.HEAD_Y + self.HEAD_H}" '
                f'x2="{cx}" y2="{bottom}" '
                f'stroke="#888" stroke-dasharray="6,3" stroke-width="1.2"/>')

        # ── messages ─────────────────────────────────────────────────────────
        for k, (src, dst, label, kind) in enumerate(self._messages):
            y = self.FIRST_MSG_Y + k * self.STEP_H
            cx_src = self._cx(src)
            cx_dst = self._cx(dst)

            if kind == "self" or src == dst:
                lx = cx_src + 60
                parts.append(
                    f'<path d="M{cx_src},{y} L{lx},{y} L{lx},{y+30} L{cx_src},{y+30}" '
                    f'fill="none" stroke="#000" stroke-width="1.5" '
                    f'marker-end="url(#arr-block)"/>')
                if label:
                    parts.append(_svg_text(lx + 4, y - 2, label, anchor="start",
                                           fontsize=10))
                continue

            dash = 'stroke-dasharray="6,3"' if kind == "return" else ""
            marker = "arr-block" if kind == "call" else "arr-open"
            # shorten line so arrowhead sits at the lifeline, not past it
            gap = 8
            x1 = cx_src + (gap if cx_dst > cx_src else -gap)
            x2 = cx_dst + (-gap if cx_dst > cx_src else gap)
            parts.append(
                f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" '
                f'stroke="#000" stroke-width="1.5" {dash} '
                f'marker-end="url(#{marker})"/>')
            if label:
                mid_x = (cx_src + cx_dst) / 2
                # label above the arrow, truncated to avoid overflow
                parts.append(_svg_text(mid_x, y - 6, label, anchor="middle",
                                       fontsize=10))

        parts.append('</svg>')
        return "\n".join(parts)

    def save_svg(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_svg())
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
        self._pos: dict[str, tuple] = {}       # cid -> (x, y, w, h)
        self._labels: dict[str, str] = {}      # cid -> label
        self._colors: dict[str, str] = {}      # cid -> color name
        self._connections: list[tuple] = []    # (src, dst, label, directed, dashed)
        self._groups: list[tuple] = []         # (label, members, pad)
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
        self._labels[cid] = label
        self._colors[cid] = color
        return cid

    def connect(self, src, dst, label="", directed=True, dashed=False) -> str:
        style = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;"
        style += "endArrow=classic;" if directed else "endArrow=none;startArrow=none;"
        if dashed:
            style += "dashed=1;"
        self._connections.append((src, dst, label, directed, dashed))
        return self.d.add_edge(src, dst, label, style)

    def group(self, label, members: Seq[str], color="gray", pad=20) -> str:
        """Draw a dashed labelled container behind the given blocks."""
        self._groups.append((label, list(members), pad))
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

    def to_svg(self) -> str:
        # canvas size
        if self._pos:
            max_x = max(x + w for x, y, w, h in self._pos.values())
            max_y = max(y + h for x, y, w, h in self._pos.values())
        else:
            max_x = max_y = 400
        width = max_x + self.MARGIN
        height = max_y + self.MARGIN

        parts = [_svg_header(width, height), _SVG_DEFS,
                 f'<rect width="{width}" height="{height}" fill="white"/>']

        # ── groups (behind everything) ────────────────────────────────────────
        for g_label, members, pad in self._groups:
            xs = [self._pos[m] for m in members if m in self._pos]
            if not xs:
                continue
            gx = min(p[0] for p in xs) - pad
            gy = min(p[1] for p in xs) - pad - 12
            gx2 = max(p[0] + p[2] for p in xs) + pad
            gy2 = max(p[1] + p[3] for p in xs) + pad
            gw, gh = gx2 - gx, gy2 - gy
            parts.append(
                f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" '
                f'fill="none" stroke="#999" stroke-dasharray="6,3" '
                f'stroke-width="1.5" rx="4"/>')
            parts.append(
                f'<text x="{gx + 8}" y="{gy + 14}" '
                f'font-size="12" font-weight="bold" fill="#666">'
                f'{_svg_esc(g_label)}</text>')

        # ── connections ───────────────────────────────────────────────────────
        for src, dst, label, directed, dashed in self._connections:
            if src not in self._pos or dst not in self._pos:
                continue
            sx, sy, sw, sh = self._pos[src]
            dx, dy, dw, dh = self._pos[dst]
            scx, scy = sx + sw / 2, sy + sh / 2
            dcx, dcy = dx + dw / 2, dy + dh / 2
            x1, y1 = _border_pt(sx, sy, sw, sh, dcx, dcy)
            x2, y2 = _border_pt(dx, dy, dw, dh, scx, scy)
            dash_attr = 'stroke-dasharray="6,3"' if dashed else ""
            marker_attr = 'marker-end="url(#arr-block)"' if directed else ""
            parts.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" '
                f'x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="#555" stroke-width="1.5" {dash_attr} {marker_attr}/>')
            if label:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                # white background for readability
                parts.append(
                    f'<rect x="{mid_x - 30:.1f}" y="{mid_y - 9:.1f}" '
                    f'width="60" height="14" fill="white" opacity="0.8"/>')
                parts.append(
                    f'<text x="{mid_x:.1f}" y="{mid_y:.1f}" '
                    f'text-anchor="middle" font-size="10" fill="#333">'
                    f'{_svg_esc(label)}</text>')

        # ── blocks ────────────────────────────────────────────────────────────
        for cid, (x, y, w, h) in self._pos.items():
            color = self._colors.get(cid, "blue")
            fc, sc = _SVG_COLORS.get(color, _SVG_COLORS["blue"])
            label = self._labels.get(cid, "")
            parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'fill="{fc}" stroke="{sc}" stroke-width="1.5" rx="4"/>')
            parts.append(_svg_text(x + w / 2, y, label, anchor="middle",
                                   fontsize=11, box_h=h))

        parts.append('</svg>')
        return "\n".join(parts)

    def save_svg(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_svg())
        return path


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
    print(fc.save_svg("/tmp/_demo_flow.svg"))

    sq = Sequence()
    u = sq.participant("用户"); api = sq.participant("API"); db = sq.participant("DB")
    sq.message(u, api, "登录")
    sq.message(api, db, "查询")
    sq.message(db, api, "结果", kind="return")
    sq.message(api, u, "成功", kind="return")
    print(sq.save("/tmp/_demo_seq.drawio"))
    print(sq.save_svg("/tmp/_demo_seq.svg"))

    bd = BlockDiagram()
    w = bd.block("Web", col=0, row=0, color="blue")
    g = bd.block("网关", col=1, row=0, color="green")
    s = bd.block("服务", col=2, row=0)
    db2 = bd.block("数据库", col=2, row=1, color="gray")
    bd.connect(w, g, "HTTPS"); bd.connect(g, s); bd.connect(s, db2, "SQL")
    bd.group("后端", [s, db2])
    print(bd.save("/tmp/_demo_block.drawio"))
    print(bd.save_svg("/tmp/_demo_block.svg"))
