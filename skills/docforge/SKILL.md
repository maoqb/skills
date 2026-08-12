---
name: docforge
description: 从代码、文档、issue、commit 或笔记等有界源材料创建或大幅修订一篇可溯源的技术文档。当交付物要求事实 provenance、由当前最强可用 ChatGPT 图像模型生成的配图，以及串行的取据-成文-核验质量门时使用；小幅文字润色不要使用。
---

# DocForge

在当前仓库的 DocForge 引擎上运行本技能。它把有界源材料整理为面向读者的技术文档；每个事实性论断与每张图
都必须能回溯到来源事实。

## 开始前

1. 确认当前仓库存在 `AGENTS.md`、`scripts/docforge.py` 与 `.claude/contracts/`。没有这些引擎资产时，
   说明无法运行；不得自行臆造契约或工作流。
2. 完整阅读仓库根目录的 `AGENTS.md`；它是运行时的最高优先级说明。
3. 创建隔离黑板：

   ```sh
   python3 scripts/docforge.py init "<目标>" --source-root <材料路径> --lang <语言代码>
   ```

   之后所有产物都写入命令输出的 `.docforge/runs/<run-id>/`。不要向 `.claude/workspace/` 写入生成内容；
   那里只保存旧样例。

## 串行质量门

1. **GATHER（界定与取据）**：阅读 `.claude/agents/miner.md`、
   `.claude/skills/fact-extract/SKILL.md` 及相关契约。产出 `boundary.json` 与 `facts.json`；每个节点和边
   都必须具有 provenance，二者验证通过后才可进入下一阶段。
2. **AUTHOR（组织、配图与写作）**：阅读 `.claude/agents/writer.md`、其引用的大纲/图表模板，及必要的
   图像生成说明。产出 `outline.md`、`diagrams/` 与 `draft.md`。严格遵守下方的图像生成政策。
3. **VERIFY（核验）**：阅读 `.claude/agents/verifier.md` 与 `.claude/rubrics/doc.yaml`，产出
   `review.json`。若 verdict 为 `BOUNCE`，回到 finding 所属阶段并重跑其后的所有阶段；最多回弹三次。

只有 verdict 为 `PASS` 时才可将 `draft.md` 晋升为 `document.md`。发布前必须运行：

```sh
python3 scripts/docforge.py check <run-dir> --publishable
```

## 图像生成政策（硬规则）

所有面向读者的图都必须通过 ChatGPT 的图像生成能力，以**当前环境可用的最新、最强图像生成模型**生成。
调用前先核对 OpenAI 官方文档或当前工具暴露的模型列表；工具允许选模型时，显式选择其中的旗舰图像模型，
工具不允许选模型时使用其默认图像生成模型。不得以 Mermaid、手写 HTML/SVG、Canvas、Graphviz、截图拼贴
或其他模型替代；也不得先画代码图再把它导出为位图。

- 在调用图像生成前，先由 `facts.json` 为每张图写出一份简短图稿：图的单一意图、要表达的关系、应出现的
  节点/连线/标签、对应 fact id，以及禁忌内容。提示词必须要求清晰的技术插图、足够留白、可读中文或目标语言
  标签，并禁止加入无来源的组件、数据流或结论。
- 生成后必须人工检查文字、箭头方向、分组和关系是否与图稿一致；不一致就重新生成或编辑，不能把模型臆造
  当成事实。将最终位图（推荐 PNG）写入 `diagrams/`，并保留每张图的 `.trace.json`，逐项映射图中的
  可见元素到真实 fact id。为通过既有预检，可额外提供同名 `.html` 包装页：它只嵌入生成的 PNG，并用
  带 `data-fact` 的可见图例列出对应事实；**包装页不得自行绘制、补画或改写图中的关系**。
- 若当前 ChatGPT/Codex 环境没有可用的图像生成能力，立即说明该阻塞，**不得降级**到任何代码图形媒介。
  没有合格图像时，不得声称已满足图表要求。

该规则优先于 DocForge 引擎资产中关于 Mermaid、HTML 或 SVG 作为图表介质的旧说明。

## 不可妥协的规则

- 每个事实性论断和每个图中的可见元素都要映射到带 provenance 的 fact id。
- 推断必须标为 `inference`，置信度只能为 `likely` 或更低，并引用支撑它的 fact id。
- 面向读者的正文使用指定语言；源引文、代码、路径、ID 和标识符必须保持原样。
- 源材料不足或问题未决时如实报告，绝不编造事实。
