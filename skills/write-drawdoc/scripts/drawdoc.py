#!/usr/bin/env python3
"""
drawdoc.py — assemble a `.drawdoc` document, DrawDocs' native format.

`.drawdoc` is a **Markdown superset**: everything is standard Markdown, plus two
fenced "macro" blocks that DrawDocs renders as *editable* diagrams, and an image
width convention. Open the result in DrawDocs (https://drawdocs.vercel.app):
drag the `.drawdoc` file onto the window, or use the Local-folder mode and pick
the folder that contains it.

Building blocks
---------------
  doc = DrawDoc()
  doc.md("# Title\n\nProse with **bold**, tables, lists, `code` …")
  doc.drawio(xml_or_path_or_builder, width=600, align="center")
  doc.excalidraw(scene_or_path_or_dict, align="center")     # whiteboard
  doc.image("logo.png", alt="Logo", width=420)              # inlined by default
  doc.save("my-doc.drawdoc")

On-disk format produced
-----------------------
  ```drawio width=600 align=center        <- fence info line carries layout
  <mxfile> … mxGraph XML … </mxfile>
  ```

  ```excalidraw
  {"type":"excalidraw","elements":[ … ]}
  ```

  ![Logo](data:image/png;base64,…  "w=420")  <- width lives in the title slot

Diagrams: the cleanest way to get valid mxGraph XML is the sibling
`drawio-diagrams` skill — build a Flowchart/Sequence/BlockDiagram and pass the
builder straight to `doc.drawio(builder)` (this script calls `.to_xml()`), or
pass a path to a saved `.drawio` file, or raw XML.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import random
import re
from typing import Any

ALIGNS = ("left", "center", "right")


# --------------------------------------------------------------------------- #
# Fence info line  ->  mirrors DrawDocs' fenceInfo(): "drawio width=N align=X"
# --------------------------------------------------------------------------- #
def _fence_info(lang: str, width: int | None, align: str | None) -> str:
    info = lang
    if width:
        info += f" width={int(width)}"
    if align in ("center", "right"):  # "left" is the default, so omit it
        info += f" align={align}"
    elif align not in (None, "left"):
        raise ValueError(f"align must be one of {ALIGNS}, got {align!r}")
    return info


# --------------------------------------------------------------------------- #
# drawio source -> mxGraph XML string
# --------------------------------------------------------------------------- #
def _diagram_xml(src: Any) -> str:
    # drawio-diagrams builders (Flowchart/Sequence/BlockDiagram/Diagram)
    if hasattr(src, "to_xml"):
        return src.to_xml().strip()
    if hasattr(src, "d") and hasattr(src.d, "to_xml"):
        return src.d.to_xml().strip()
    if isinstance(src, str):
        if src.lstrip().startswith("<"):
            return src.strip()
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                return f.read().strip()
        raise ValueError(
            "drawio source string is neither XML (starts with '<') nor an "
            f"existing file path: {src[:60]!r}"
        )
    raise TypeError(f"unsupported drawio source: {type(src).__name__}")


# --------------------------------------------------------------------------- #
# excalidraw source -> scene JSON string
# --------------------------------------------------------------------------- #
def _scene_json(src: Any) -> str:
    if isinstance(src, dict):
        scene = dict(src)
    elif isinstance(src, str):
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                src = f.read()
        if not src.strip():
            scene = {}
        else:
            scene = json.loads(src)
    else:
        raise TypeError(f"unsupported excalidraw source: {type(src).__name__}")
    scene.setdefault("type", "excalidraw")
    scene.setdefault("version", 2)
    scene.setdefault("source", "drawdocs")
    scene.setdefault("elements", [])
    scene.setdefault("appState", {})
    scene.setdefault("files", {})
    return json.dumps(scene, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Excalidraw element helpers — full default fields so exportToSvg renders them
# --------------------------------------------------------------------------- #
def _nonce() -> int:
    return random.randint(1, 2**31 - 1)


def _ex_base(eid: str, x: float, y: float, w: float, h: float, **over) -> dict:
    el = {
        "id": eid,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": _nonce(),
        "version": 1,
        "versionNonce": _nonce(),
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }
    el.update(over)
    return el


def ex_rect(eid, x, y, w=160, h=70, color="#1e1e1e", fill="#a5d8ff", text=None):
    """A rounded rectangle, optionally with centered label text element(s)."""
    rect = _ex_base(eid, x, y, w, h, type="rectangle",
                    strokeColor=color, backgroundColor=fill,
                    roundness={"type": 3})
    out = [rect]
    if text:
        out.append(ex_text(f"{eid}-t", x + 10, y + h / 2 - 12, text, w=w - 20))
    return out


def ex_ellipse(eid, x, y, w=140, h=80, color="#1e1e1e", fill="#b2f2bb"):
    return [_ex_base(eid, x, y, w, h, type="ellipse",
                     strokeColor=color, backgroundColor=fill)]


def ex_text(eid, x, y, text, size=20, color="#1e1e1e", w=None):
    w = w if w is not None else max(20, len(text) * size * 0.55)
    h = size * 1.25
    return _ex_base(
        eid, x, y, w, h, type="text", text=text, originalText=text,
        strokeColor=color, fontSize=size, fontFamily=1,
        textAlign="left", verticalAlign="top",
        containerId=None, lineHeight=1.25, baseline=int(size * 0.9),
    )


def ex_arrow(eid, x1, y1, x2, y2, color="#1e1e1e"):
    return [_ex_base(
        eid, x1, y1, abs(x2 - x1), abs(y2 - y1), type="arrow",
        strokeColor=color,
        points=[[0, 0], [x2 - x1, y2 - y1]],
        lastCommittedPoint=None, startBinding=None, endBinding=None,
        startArrowhead=None, endArrowhead="arrow",
    )]


def excalidraw_scene(*element_groups) -> dict:
    """Flatten element helpers into a scene dict ready for doc.excalidraw()."""
    elements: list[dict] = []
    for g in element_groups:
        elements.extend(g if isinstance(g, list) else [g])
    return {"type": "excalidraw", "version": 2, "source": "drawdocs",
            "elements": elements, "appState": {"viewBackgroundColor": "#ffffff"},
            "files": {}}


# --------------------------------------------------------------------------- #
# Image -> Markdown image, inlined as a data URI by default (self-contained)
# --------------------------------------------------------------------------- #
def _data_uri(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        mime = "image/png" if path.lower().endswith(".png") else "application/octet-stream"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


# --------------------------------------------------------------------------- #
# Document builder
# --------------------------------------------------------------------------- #
class DrawDoc:
    def __init__(self) -> None:
        self._blocks: list[str] = []

    def md(self, text: str) -> "DrawDoc":
        """Append a standard Markdown block (heading, prose, table, list, code…)."""
        self._blocks.append(text.strip("\n"))
        return self

    text = md  # alias

    def drawio(self, src: Any, width: int | None = None,
               align: str | None = None) -> "DrawDoc":
        """Embed a draw.io diagram. `src` may be a drawio-diagrams builder, a
        path to a .drawio file, or a raw mxGraph XML string."""
        xml = _diagram_xml(src)
        if "```" in xml:
            raise ValueError("drawio XML must not contain triple backticks")
        self._blocks.append(f"```{_fence_info('drawio', width, align)}\n{xml}\n```")
        return self

    def excalidraw(self, src: Any = "", width: int | None = None,
                   align: str | None = None) -> "DrawDoc":
        """Embed an Excalidraw whiteboard. `src` may be a scene dict (see
        excalidraw_scene()), a JSON string, a path to a .excalidraw file, or ""
        for an empty block to draw by hand in DrawDocs."""
        data = _scene_json(src)
        if "```" in data:
            raise ValueError("excalidraw JSON must not contain triple backticks")
        self._blocks.append(f"```{_fence_info('excalidraw', width, align)}\n{data}\n```")
        return self

    def image(self, src: str, alt: str = "", width: int | None = None,
              embed: bool = True) -> "DrawDoc":
        """Add an image. By default a local file is inlined as a data URI so the
        `.drawdoc` is a single self-contained file (drag-and-drop friendly).
        Pass embed=False to keep `src` as a relative link (use Local-folder mode
        so DrawDocs can resolve it)."""
        alt = re.sub(r"[\[\]]", "", alt)
        link = _data_uri(src) if (embed and os.path.exists(src)) else src
        title = f' "w={int(width)}"' if width else ""
        self._blocks.append(f"![{alt}]({link}{title})")
        return self

    def to_text(self) -> str:
        return "\n\n".join(b for b in self._blocks if b.strip()) + "\n"

    def save(self, path: str) -> str:
        if not path.endswith(".drawdoc"):
            path += ".drawdoc"
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_text())
        return path


# --------------------------------------------------------------------------- #
# Self-test: build a tiny doc and re-parse its fences to confirm validity.
#   python3 drawdoc.py            -> writes /tmp/drawdoc-selftest.drawdoc
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    XML = ('<mxfile><diagram id="d" name="P"><mxGraphModel><root>'
           '<mxCell id="0"/><mxCell id="1" parent="0"/>'
           '<mxCell id="2" value="Hello" style="rounded=1;fillColor=#dae8fc" '
           'vertex="1" parent="1"><mxGeometry x="40" y="40" width="120" '
           'height="50" as="geometry"/></mxCell>'
           '</root></mxGraphModel></diagram></mxfile>')
    doc = DrawDoc()
    doc.md("# Self-test\n\nProse with **bold** and a table:\n\n"
           "| A | B |\n|---|---|\n| 1 | 2 |")
    doc.drawio(XML, width=520, align="center")
    doc.excalidraw(excalidraw_scene(
        ex_rect("r1", 80, 80, text="Box"),
        ex_text("t1", 80, 200, "label"),
    ))
    out = doc.save("/tmp/drawdoc-selftest.drawdoc")

    body = open(out, encoding="utf-8").read()
    assert "```drawio width=520 align=center" in body
    assert "```excalidraw" in body
    drawio_fences = re.findall(r"^```drawio.*?^```", body, re.S | re.M)
    excal_fences = re.findall(r"^```excalidraw.*?^```", body, re.S | re.M)
    assert len(drawio_fences) == 1 and len(excal_fences) == 1
    # excalidraw fence content must be valid JSON
    json.loads(excal_fences[0].split("\n", 1)[1].rsplit("\n```", 1)[0])
    print(f"OK  wrote {out}  ({len(body)} bytes)")
