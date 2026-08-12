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
  doc.mermaid("graph TD\n A --> B", align="center")         # GitHub-native diagram
  doc.mindmap(mindmap_data("中心主题", "分支一", "分支二"))   # interactive mind map
  doc.toc()                                                  # live table of contents
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

  ```mermaid                              <- bare fence => GitHub renders it natively
  graph TD
    A --> B
  ```

  ```mindmap
  {"nodeData":{"id":"root","topic":"中心主题","children":[ … ]}}
  ```

  <!-- toc -->                            <- live TOC; DrawDocs regenerates from headings
  - [Title](#title)
  <!-- /toc -->

  ![Logo](data:image/png;base64,…  "w=420")  <- width lives in the title slot

Diagrams: `doc.drawio()` accepts a path to a saved `.drawio` file, a raw mxGraph
XML string, or any builder object exposing `.to_xml()` (called automatically).
A path drawn in draw.io desktop / https://app.diagrams.net is the safest source.
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
    # any builder object exposing .to_xml()
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
# mermaid source -> mermaid text
# --------------------------------------------------------------------------- #
def _mermaid_text(src: Any) -> str:
    if not isinstance(src, str):
        raise TypeError(f"unsupported mermaid source: {type(src).__name__}")
    # a path to a .mmd / .mermaid file, otherwise the mermaid text itself
    if os.path.exists(src) and len(src) < 4096 and "\n" not in src:
        with open(src, encoding="utf-8") as f:
            return f.read().strip()
    return src.strip()


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
# mindmap source -> mind-elixir data JSON string
#   DrawDocs stores mind-elixir getData() JSON: {"nodeData": <tree>, …}.
#   A node is {"id": <unique>, "topic": <text>, "children": [ … ]}.
# --------------------------------------------------------------------------- #
def mind_node(topic: str, *children: Any, node_id: str | None = None) -> dict:
    """Build one mind-map node. Children may be strings (leaf topics) or dicts
    produced by mind_node(); strings become leaf nodes automatically."""
    node: dict[str, Any] = {"id": node_id or f"m{_nonce()}", "topic": str(topic)}
    kids = [c if isinstance(c, dict) else mind_node(c) for c in children]
    if kids:
        node["children"] = kids
    return node


def mindmap_data(root: Any, *children: Any) -> dict:
    """Assemble a mind-elixir data dict ready for doc.mindmap().
    `root` is the centre topic (string) or a mind_node(); extra args are its
    children (strings or mind_node())."""
    node = root if isinstance(root, dict) else mind_node(root, *children)
    if not isinstance(root, dict) and not children:
        node.setdefault("children", [])
    return {"nodeData": node}


def _mind_json(src: Any) -> str:
    if isinstance(src, dict):
        data = src if "nodeData" in src else mindmap_data(src.get("topic", "中心主题"))
    elif isinstance(src, str):
        if os.path.exists(src):
            with open(src, encoding="utf-8") as f:
                src = f.read()
        data = json.loads(src) if src.strip() else mindmap_data("中心主题")
    else:
        raise TypeError(f"unsupported mindmap source: {type(src).__name__}")
    if "nodeData" not in data:
        raise ValueError('mindmap data must have a "nodeData" root node')
    return json.dumps(data, ensure_ascii=False)


# --------------------------------------------------------------------------- #
# Table-of-contents slugging — mirrors DrawDocs' GitHub-style anchor rules
# (lowercase, strip punctuation, spaces->hyphens, keep CJK/_; -1/-2 on dupes).
# --------------------------------------------------------------------------- #
def _base_slug(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^\w \-]", "", s, flags=re.UNICODE)  # \w keeps letters/digits/_/CJK
    return s.replace(" ", "-")


def _toc_from_headings(headings: list[tuple[int, str]]) -> str:
    if not headings:
        return ""
    min_level = min(lv for lv, _ in headings)
    seen: dict[str, int] = {}
    lines = []
    for level, text in headings:
        base = _base_slug(text)
        n = seen.get(base, 0)
        seen[base] = n + 1
        slug = base if n == 0 else f"{base}-{n}"
        indent = "  " * max(0, level - min_level)
        safe = text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
        lines.append(f"{indent}- [{safe}](#{slug})")
    return "\n".join(lines)


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
_TOC_SENTINEL = "\x00TOC\x00"  # placeholder; resolved against all headings at render
_ATX_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


class DrawDoc:
    def __init__(self) -> None:
        self._blocks: list[str] = []

    def _collect_headings(self) -> list[tuple[int, str]]:
        """ATX headings (`# … ######`) across all md blocks, skipping fenced code."""
        out: list[tuple[int, str]] = []
        for block in self._blocks:
            if block is _TOC_SENTINEL or block.lstrip().startswith("```"):
                continue
            in_fence = False
            for line in block.splitlines():
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                m = _ATX_RE.match(line)
                if m:
                    out.append((len(m.group(1)), m.group(2)))
        return out

    def _render_toc(self) -> str:
        body = _toc_from_headings(self._collect_headings())
        inner = f"\n\n{body}\n\n" if body else "\n\n"
        return f"<!-- toc -->{inner}<!-- /toc -->"

    def md(self, text: str) -> "DrawDoc":
        """Append a standard Markdown block (heading, prose, table, list, code…)."""
        self._blocks.append(text.strip("\n"))
        return self

    text = md  # alias

    def drawio(self, src: Any, width: int | None = None,
               align: str | None = None) -> "DrawDoc":
        """Embed a draw.io diagram. `src` may be a path to a .drawio file, a raw
        mxGraph XML string, or any builder object exposing .to_xml()."""
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

    def mermaid(self, src: str, width: int | None = None,
                align: str | None = None) -> "DrawDoc":
        """Embed a Mermaid diagram. `src` is mermaid text (e.g. "graph TD\\n A-->B",
        "sequenceDiagram …", "gantt …") or a path to a .mmd/.mermaid file. With no
        width/align the fence stays a bare ```mermaid, which GitHub renders
        natively; layout params turn it into a plain code block on GitHub but
        DrawDocs still renders/edits it."""
        text = _mermaid_text(src)
        if not text:
            raise ValueError("mermaid source is empty")
        if "```" in text:
            raise ValueError("mermaid text must not contain triple backticks")
        self._blocks.append(f"```{_fence_info('mermaid', width, align)}\n{text}\n```")
        return self

    def mindmap(self, src: Any, width: int | None = None,
                align: str | None = None) -> "DrawDoc":
        """Embed an interactive (mind-elixir) mind map. `src` may be a data dict
        from mindmap_data(), a JSON string, or a path to a saved mindmap JSON."""
        data = _mind_json(src)
        if "```" in data:
            raise ValueError("mindmap JSON must not contain triple backticks")
        self._blocks.append(f"```{_fence_info('mindmap', width, align)}\n{data}\n```")
        return self

    def toc(self) -> "DrawDoc":
        """Insert a live table of contents at this position. Stored as a doctoc
        ``<!-- toc --> … <!-- /toc -->`` block; DrawDocs regenerates the list from
        the document's headings on open (and keeps it live), while the precomputed
        anchor list below makes it render on GitHub immediately."""
        self._blocks.append(_TOC_SENTINEL)
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
        rendered = [self._render_toc() if b is _TOC_SENTINEL else b for b in self._blocks]
        return "\n\n".join(b for b in rendered if b.strip()) + "\n"

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
    doc.toc()
    doc.md("## Diagrams")
    doc.drawio(XML, width=520, align="center")
    doc.excalidraw(excalidraw_scene(
        ex_rect("r1", 80, 80, text="Box"),
        ex_text("t1", 80, 200, "label"),
    ))
    doc.mermaid("graph TD\n  A[开始] --> B[结束]", align="center")
    doc.mindmap(mindmap_data("中心主题", "分支一", mind_node("分支二", "子项")))
    out = doc.save("/tmp/drawdoc-selftest.drawdoc")

    body = open(out, encoding="utf-8").read()
    assert "```drawio width=520 align=center" in body
    assert "```excalidraw" in body
    assert "```mermaid align=center" in body
    assert "```mindmap" in body and '"nodeData"' in body
    assert "<!-- toc -->" in body and "<!-- /toc -->" in body
    assert "- [Self-test](#self-test)" in body  # toc anchors computed from headings
    drawio_fences = re.findall(r"^```drawio.*?^```", body, re.S | re.M)
    excal_fences = re.findall(r"^```excalidraw.*?^```", body, re.S | re.M)
    mermaid_fences = re.findall(r"^```mermaid.*?^```", body, re.S | re.M)
    mind_fences = re.findall(r"^```mindmap.*?^```", body, re.S | re.M)
    assert len(drawio_fences) == 1 and len(excal_fences) == 1
    assert len(mermaid_fences) == 1 and len(mind_fences) == 1
    # excalidraw + mindmap fence contents must be valid JSON
    json.loads(excal_fences[0].split("\n", 1)[1].rsplit("\n```", 1)[0])
    json.loads(mind_fences[0].split("\n", 1)[1].rsplit("\n```", 1)[0])
    print(f"OK  wrote {out}  ({len(body)} bytes)")
