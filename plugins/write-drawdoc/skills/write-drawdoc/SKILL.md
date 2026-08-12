---
name: write-drawdoc
description: >-
  撰写 DrawDocs 原生 .drawdoc 文档（Markdown 超集：正文/表格/列表/代码 + 内嵌可编辑的
  drawio 图、Excalidraw 白板、Mermaid 图、思维导图、活目录 + 带宽度的图片），产物可在
  DrawDocs（drawdocs.vercel.app）里直接打开继续编辑。当用户想「写一篇 .drawdoc」「生成
  DrawDocs 文档」「写带图的文档并能在 DrawDocs 里改」「图文混排的技术文档/说明/方案，要
  可编辑的图/流程图/时序图/思维导图/目录」时使用；也会被「drawdoc」「DrawDocs」「写个能在
  drawdocs 打开的文档」触发。需要把图（流程图/架构图/时序图/思维导图）和正文排到一篇可编辑
  文档里时，优先用本技能，而不是只产出散落的 .drawio 或纯 Markdown。
---

# write-drawdoc

产出一个 **`.drawdoc`** 文件：DrawDocs 的原生文档格式，是 Markdown 的超集——普通
Markdown 全部有效，额外多了几种可被 DrawDocs 渲染成**可编辑内容**的围栏
（drawio / excalidraw / mermaid / mindmap）、一个**活目录**块和一个图片宽度约定。
产物在 <https://drawdocs.vercel.app> 里**拖进去即可打开编辑**。

先读 `references/format.md`（格式权威说明），再用 `scripts/drawdoc.py` 组装。

## 何时用

- 用户要一篇**图文混排、且图要能在 DrawDocs 里继续改**的文档 → 用本技能。
- 用户只要一张可编辑的图（不要承载文档）→ 直接产一个 `.drawio` 文件即可，不必用本技能。
- 用户只要纯文字 Markdown，不涉及内嵌图/DrawDocs → 直接写 `.md`，不必用本技能。

## 工作流

1. **规划文档结构**：标题层级、哪里需要图、每张图选哪种宏。正文语言跟随用户（中文就中文）。
   - **mermaid**：流程图/时序图/甘特图/类图等「文本能描述的图」——最省事，且裸围栏在
     GitHub 上原生渲染，**默认优先选它**。
   - **drawio**：需要精细排版/自定义样式的架构图、复杂示意图。
   - **excalidraw**：手绘风白板草图，或留空让用户手画。
   - **mindmap**：要点发散/层级大纲，可在 DrawDocs 里拖拽交互编辑。
   - **toc**：长文档导航——`doc.toc()` 按全文标题自动生成活目录。

2. **准备图的 XML（关键一步）**。`.drawdoc` 里的 drawio 围栏需要合法的 mxGraph
   XML（`<mxfile>…</mxfile>`）。`doc.drawio(src, …)` 接受三种 `src`：

   - 一个已保存的 `.drawio` 文件路径——用 draw.io 桌面版或 <https://app.diagrams.net>
     画好后传路径，最稳；
   - 原始 mxGraph XML 字符串（以 `<` 开头）；
   - 任意暴露 `.to_xml()` 方法的构建器对象（脚本会自动调用它）。

   手写 XML 极易错，优先传已画好的 `.drawio` 路径。

3. **组装 `.drawdoc`**。用 `scripts/drawdoc.py` 的 `DrawDoc` 按顺序追加块：

   ```python
   import sys
   sys.path.insert(0, "<write-drawdoc skill>/scripts")
   from drawdoc import (DrawDoc, excalidraw_scene, ex_rect, ex_text,
                        mindmap_data, mind_node)

   doc = DrawDoc()
   doc.md("# 部署架构\n\n服务整体如下图，**双击图可在 DrawDocs 内编辑**：")
   doc.toc()                                            # 活目录（按标题实时生成）
   doc.drawio("架构.drawio", width=600, align="center")  # .drawio 路径 / 原始 XML
   doc.md("## 数据流\n\n| 阶段 | 说明 |\n|---|---|\n| 入站 | … |")
   doc.mermaid("sequenceDiagram\n  C->>A: 请求\n  A-->>C: 响应")  # GitHub 原生图
   doc.excalidraw(excalidraw_scene(                    # 可选：手绘风白板
       ex_rect("r1", 80, 80, text="想法"),
       ex_text("t1", 80, 200, "备注"),
   ), align="center")
   doc.mindmap(mindmap_data("中心主题", "分支一",       # 交互式思维导图
       mind_node("分支二", "子项 A", "子项 B")))
   doc.image("logo.png", alt="Logo", width=160)        # 默认内联为 data URI
   path = doc.save("部署架构.drawdoc")
   print(path)
   ```

   - **选对宏**：流程/架构/时序图能在 GitHub 也渲染又想精简 → `doc.mermaid()`（裸围栏
     GitHub 原生）；需要像素级摆放/复杂样式、要在 draw.io 里精修 → `doc.drawio()`；
     手绘草图风白板 → `doc.excalidraw()`；要点发散/层级大纲、可交互拖拽 → `doc.mindmap()`；
     长文导航 → `doc.toc()`（放在首个标题之后，自动按全文标题生成锚点）。
   - 图片默认**内联成 data URI**，使 `.drawdoc` 成为单文件、可直接拖进 DrawDocs；
     若用相对路径（`embed=False`），需让用户用「本地文件夹」模式打开以解析图片。
   - 想留一块空白白板让用户手画：`doc.excalidraw()`（不传参）。
   - `doc.mermaid(src)` 的 `src` 是 mermaid 文本，或 `.mmd/.mermaid` 文件路径；**不带
     width/align** 时输出裸 ` ```mermaid ` 围栏，GitHub 上也原生渲染（设了布局参数则
     GitHub 退化成代码块，但 DrawDocs 仍可渲染/编辑）。

4. **自检产物**：
   ```bash
   python3 - <<'PY'
   import re, json
   body = open("部署架构.drawdoc", encoding="utf-8").read()
   for lang in ("excalidraw", "mindmap"):       # 这两种围栏内容必须是合法 JSON
       for m in re.findall(rf"^```{lang}.*?\n(.*?)\n```", body, re.S | re.M):
           json.loads(m)
   # 目录块若存在必须闭合
   assert body.count("<!-- toc -->") == body.count("<!-- /toc -->")
   print("OK", len(body), "bytes")
   PY
   ```
   `scripts/drawdoc.py` 直接运行（`python3 drawdoc.py`）会跑一个内置自检并写出
   `/tmp/drawdoc-selftest.drawdoc` 作为参考样例。

5. **告诉用户如何在 DrawDocs 打开**（三选一，见 `references/format.md` §9）：
   - **拖进去**：把 `.drawdoc` 拖到 <https://drawdocs.vercel.app> 窗口即开（配合内联图片最顺）。
   - **本地文件夹**：侧栏「本地」标签 →「打开本地文件夹」选所在目录 → 点文件；编辑自动保存回磁盘。
   - **GitHub**：把文件提交到仓库，在侧栏 GitHub 标签里浏览并推送修改。

## 让文档好用的约定

- 一张图配一句引导（「下图为…」「双击可编辑」），不要图突兀地插在段落中间。
- 图用 `width` + `align=center` 居中、控制大小；正文宽图用 `width=600~760`。
  注意：mermaid 一旦设 `width/align` 就在 GitHub 上退化为代码块，纯展示优先留裸围栏。
- 标签短、跟随用户语言；复杂图注意质量（文字不溢出方框、并列子项用框中框、连线尽量不交叉等）。
- 凡是「可编辑的图」一律走 drawio / excalidraw / mermaid / mindmap 围栏，**不要**把图导成
  PNG 再 `![]()`——那样在 DrawDocs 里就只是张死图、不能改了。
- 能用文字描述清楚的流程图/时序图，**优先用 mermaid**：源码可读可 diff，GitHub 原生渲染，
  比手搓 drawio XML 稳得多。
- 思维导图节点 id 必须唯一（用 `mind_node()` / `mindmap_data()` 自动分配，别手填重复 id）。

## 关于 skill 路径

把 `<write-drawdoc skill>` 替换为本 SKILL.md 所在目录。脚本里稳妥的写法：

```python
import os, sys
SKILL = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SKILL, "scripts"))
```
