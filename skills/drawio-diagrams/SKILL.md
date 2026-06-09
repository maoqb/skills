---
name: drawio-diagrams
description: >-
  以程序化方式生成可编辑的 draw.io（.drawio，mxGraph XML）图——框图/架构图、时序图/序列图、
  流程图，并可选导出为 PNG/SVG。当用户想绘制或可视化某个流程、过程、算法、系统架构、组件布局、
  模块关系、请求/响应交互或调用时序时使用——包括「画个流程图」「画一个时序图」「框图」「画张架构图」
  「draw a flowchart/sequence/block diagram」「diagram this」「可视化这个流程」或索要一个
  .drawio / diagrams.net 文件等说法。当用户点名 drawio / diagrams.net，或想要一个能打开再修改的
  可编辑图文件时，优先使用本技能，而不是 ASCII 字符画或 Mermaid。
---

# drawio-diagrams

为三类图生成可编辑的 `.drawio` 文件（mxGraph XML）：**框图/架构图（block/architecture）**、
**时序图（sequence）**、**流程图（flowchart）**。产物可在 draw.io 桌面版或
<https://app.diagrams.net> 中打开编辑，并可导出为 PNG/SVG。

## 为什么用构建器而非手写 XML

`.drawio` 格式把每个图形都放在明确的像素坐标上，手写既慢又易错——时序图尤甚，每条消息都要在
竖直生命线之间对齐。`scripts/drawio.py` 负责几何计算：你只描述*谁与谁相连*，它来算*东西摆在哪*。
只有当构建器表达不了某种布局时，才直接写 XML。

## 工作流

1. **从需求判断图的类型**：
   - 步骤 / 判断 / “如果…则…” / 某个算法 → **流程图（flowchart）**
   - 角色之间随时间交换消息、请求/响应、调用顺序 → **时序图（sequence）**
   - 组件 / 模块 / 服务以及它们如何相连 → **框图/架构图（block/architecture）**
   - 若确实含糊就发问；否则选最贴合的一种继续。

2. **读对应的参考文档**，了解 API 和一个完整示例：
   - `references/flowchart.md`
   - `references/sequence.md`
   - `references/block.md`
   - `references/format.md` —— 仅当需要手写自定义 XML 时。

3. **用 `scripts/drawio.py` 构建**。写一小段 Python 脚本：导入对应的构建器，声明
   节点/消息/方框，同时调用 `.save("<name>.drawio")` **和** `.save_svg("<name>.svg")`。开头保留
   `sys.path.insert(0, "<skill>/scripts")` 以便导入成功。输出文件名取得有辨识度；除非用户
   指定路径，否则默认放当前工作目录。

   ```python
   bd.save("architecture.drawio")      # 可编辑源文件
   bd.save_svg("architecture.svg")     # 可内嵌到 markdown 的图片（无需外部工具）
   ```

4. **校验文件格式正确**：
   ```bash
   python3 -c "import xml.dom.minidom as m; m.parse('<name>.drawio'); print('OK')"
   python3 -c "import xml.etree.ElementTree as ET; ET.parse('<name>.svg'); print('OK')"
   ```
   再渲染成图片自查质量（见下方“质量约束”）：
   ```bash
   rsvg-convert -w 1200 <name>.svg -o /tmp/preview.png   # 然后用 Read 查看
   ```

5. **SVG 是 markdown 内嵌的默认格式**。每张图都用 `save_svg()` 生成 `.svg`，在 markdown 里用
   `![标题](./name.svg)` 引用——这不需要 drawio CLI，纯 Python 即可，任何环境都能工作。
   若需要 PNG/PDF（更高保真度），运行 `scripts/export.sh <name>.drawio png`，它会在 drawio CLI
   可用时使用 CLI，否则自动降级为 SVG。`.drawio` 文件始终保留以便在 draw.io 中编辑。

6. **告诉用户**各文件路径：`.drawio` 可在 draw.io / app.diagrams.net 中编辑，`.svg` 已可在
   markdown/HTML 中直接显示。

## 关于 skill 路径的写法

全文中把 `<skill>` 替换为本技能所在目录（即包含这份 SKILL.md 的文件夹）。在生成的脚本里，一种
稳妥写法：

```python
import os, sys
SKILL = os.path.dirname(os.path.abspath(__file__))  # if script lives in <skill>
sys.path.insert(0, os.path.join(SKILL, "scripts"))
```

或者直接硬编码你从技能位置能看到的 `scripts/` 绝对路径。

## 让图保持易读的约定

- 标签简短；让形状和颜色承载含义。构建器用 draw.io 原生调色板，效果像手画而非生成的。
- 一个方框一个概念；细节用 `\n` 放到第二行标签。
- 给每个判断分支（“是”/“否”）和每条时序消息都打标签。
- 标签语言跟随用户（中文就保持中文）。

## 质量约束（生成后务必自查，尤其是框图/架构图）

1. **文字不能超出方框**：`BlockDiagram.block()` 会按标签行数自动算高度，但**宽度**仍需
   自己核对——超长的单行标识符（如 `inheritance_graph-<product>.dot`）要显式传 `w=`
   留够空间。
2. **同类元素用框中框**：一个方框如果概念上包含多个并列子项（例如某目录下的多种文件类型），
   不要塞进一个标签里——用 `BlockDiagram.child_block(parent_id, label, rel_x, rel_y, w, h,
   color=...)` 在父框内画出多个小方框，父框传 `title_top=True` 把标题置顶、给子框留空间。
3. **箭头可以是折线**：`connect()` 支持 `waypoints=[(x,y), ...]`，让连线绕开其他方框、
   避免多条箭头挤在一起重叠。多条折线如果同向绕路，分配不同的 x/y 通道（例如分别走
   `x=30` 和 `x=100`），不要共用同一条通道。
4. 上述三条的具体写法和示例见 `references/block.md`。流程图/时序图的构建器目前没有这些
   API，但同样的“不溢出、不重叠”原则适用——必要时手动调整标签长度或换行。

## 适用范围

覆盖流程图、时序图、框图/架构图。对于其它 draw.io 图类型（ER 图、思维导图、组织结构图、甘特图），
底层的 `Diagram` 类配合 `references/format.md` 仍然适用——由你自己提供坐标和样式。
