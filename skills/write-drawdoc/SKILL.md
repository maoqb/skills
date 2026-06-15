---
name: write-drawdoc
description: >-
  撰写 DrawDocs 原生 .drawdoc 文档（Markdown 超集：正文/表格/列表/代码 + 内嵌可编辑的
  drawio 图与 Excalidraw 白板 + 带宽度的图片），产物可在 DrawDocs（drawdocs.vercel.app）
  里直接打开继续编辑。当用户想「写一篇 .drawdoc」「生成 DrawDocs 文档」「写带图的文档并能在
  DrawDocs 里改」「图文混排的技术文档/说明/方案，要可编辑的图」时使用；也会被「drawdoc」
  「DrawDocs」「写个能在 drawdocs 打开的文档」触发。需要把图（流程图/架构图/时序图）和正文
  排到一篇可编辑文档里时，优先用本技能，而不是只产出散落的 .drawio 或纯 Markdown。
---

# write-drawdoc

产出一个 **`.drawdoc`** 文件：DrawDocs 的原生文档格式，是 Markdown 的严格超集——普通
Markdown 全部有效，额外多了两种可被 DrawDocs 渲染成**可编辑图**的围栏（drawio / excalidraw）
和一个图片宽度约定。产物在 <https://drawdocs.vercel.app> 里**拖进去即可打开编辑**。

先读 `references/format.md`（格式权威说明），再用 `scripts/drawdoc.py` 组装。

## 何时用

- 用户要一篇**图文混排、且图要能在 DrawDocs 里继续改**的文档 → 用本技能。
- 用户只要一张可编辑的图（不要承载文档）→ 用 `drawio-diagrams` 技能产 `.drawio` 即可。
- 用户只要纯文字 Markdown，不涉及内嵌图/DrawDocs → 直接写 `.md`，不必用本技能。

## 工作流

1. **规划文档结构**：标题层级、哪里需要图、每张图是流程图/架构图/时序图还是手绘白板。
   正文语言跟随用户（中文就中文）。

2. **生成图的 XML（关键一步）**。`.drawdoc` 里的 drawio 围栏需要合法的 mxGraph XML，
   手写极易错——**用同一 marketplace 的 `drawio-diagrams` 技能**构建 Flowchart /
   Sequence / BlockDiagram，然后把构建器对象**直接传给** `doc.drawio(builder)`
   （本脚本会调用它的 `.to_xml()`）。也可以传一个已保存的 `.drawio` 文件路径或原始 XML。

   ```python
   import sys
   sys.path.insert(0, "<drawio-diagrams skill>/scripts")  # 若已装 drawio-diagrams
   from drawio import BlockDiagram
   bd = BlockDiagram("架构")
   a = bd.block("Client", col=0, color="blue")
   b = bd.block("API",    col=1, color="green")
   bd.connect(a, b, "HTTP")
   ```

3. **组装 `.drawdoc`**。用 `scripts/drawdoc.py` 的 `DrawDoc` 按顺序追加块：

   ```python
   import sys
   sys.path.insert(0, "<write-drawdoc skill>/scripts")
   from drawdoc import DrawDoc, excalidraw_scene, ex_rect, ex_text

   doc = DrawDoc()
   doc.md("# 部署架构\n\n服务整体如下图，**双击图可在 DrawDocs 内编辑**：")
   doc.drawio(bd, width=600, align="center")          # 传 drawio-diagrams 构建器
   doc.md("## 数据流\n\n| 阶段 | 说明 |\n|---|---|\n| 入站 | … |")
   doc.excalidraw(excalidraw_scene(                    # 可选：手绘风白板
       ex_rect("r1", 80, 80, text="想法"),
       ex_text("t1", 80, 200, "备注"),
   ), align="center")
   doc.image("logo.png", alt="Logo", width=160)        # 默认内联为 data URI
   path = doc.save("部署架构.drawdoc")
   print(path)
   ```

   - 图片默认**内联成 data URI**，使 `.drawdoc` 成为单文件、可直接拖进 DrawDocs；
     若用相对路径（`embed=False`），需让用户用「本地文件夹」模式打开以解析图片。
   - 想留一块空白白板让用户手画：`doc.excalidraw()`（不传参）。

4. **自检产物**：
   ```bash
   python3 - <<'PY'
   import re, json
   body = open("部署架构.drawdoc", encoding="utf-8").read()
   for m in re.findall(r"^```excalidraw.*?\n(.*?)\n```", body, re.S | re.M):
       json.loads(m)                      # excalidraw 围栏必须是合法 JSON
   assert "```drawio" in body
   print("OK", len(body), "bytes")
   PY
   ```
   `scripts/drawdoc.py` 直接运行（`python3 drawdoc.py`）会跑一个内置自检并写出
   `/tmp/drawdoc-selftest.drawdoc` 作为参考样例。

5. **告诉用户如何在 DrawDocs 打开**（三选一，见 `references/format.md` §6）：
   - **拖进去**：把 `.drawdoc` 拖到 <https://drawdocs.vercel.app> 窗口即开（配合内联图片最顺）。
   - **本地文件夹**：侧栏「本地」标签 →「打开本地文件夹」选所在目录 → 点文件；编辑自动保存回磁盘。
   - **GitHub**：把文件提交到仓库，在侧栏 GitHub 标签里浏览并推送修改。

## 让文档好用的约定

- 一张图配一句引导（「下图为…」「双击可编辑」），不要图突兀地插在段落中间。
- 图用 `width` + `align=center` 居中、控制大小；正文宽图用 `width=600~760`。
- 标签短、跟随用户语言；复杂图的质量约束沿用 `drawio-diagrams` 技能的指引
  （文字不溢出方框、并列子项用框中框等）。
- 凡是「可编辑的图」一律走 drawio / excalidraw 围栏，**不要**把图导成 PNG 再 `![]()`——
  那样在 DrawDocs 里就只是张死图、不能改了。

## 关于 skill 路径

把 `<write-drawdoc skill>` 替换为本 SKILL.md 所在目录；`<drawio-diagrams skill>` 替换为
已安装的 drawio-diagrams 技能目录。脚本里稳妥的写法：

```python
import os, sys
SKILL = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
```
