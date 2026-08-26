# maoqb-skills

个人 AI 编程技能仓库。所有技能以通用的 `SKILL.md` 形式维护，可供 **Claude Code** 与 **Codex** 使用；
`.claude-plugin/marketplace.json` 仅是 Claude Code 的 marketplace 安装清单，并不限定技能本身的运行环境。

## Install

在 Claude Code 中：

```
/plugin marketplace add maoqb/skills
/plugin install write-drawdoc@maoqb-skills
/plugin install gerrit-tool@maoqb-skills
/plugin install docforge@maoqb-skills
/plugin install aosp-solution-doc@maoqb-skills
```

第一条命令注册 marketplace，后续命令安装技能。新技能未显示时，重启 Claude Code 或运行 `/plugin`。

在 Codex 中：

```
codex plugin marketplace add maoqb/skills --ref main
codex plugin add docforge@maoqb-skills
```

将 `docforge` 替换为 `write-drawdoc`、`gerrit-tool` 或 `aosp-solution-doc` 即可安装对应 plugin。四个技能共享同一套
`SKILL.md` 格式，不依赖 Claude 专属的 slash command、Task 工具或项目配置。

To update later:

```
/plugin marketplace update maoqb-skills
```

## Skills

### write-drawdoc

撰写 **`.drawdoc`** 文档——[DrawDocs](https://drawdocs.vercel.app) 的原生格式，是
Markdown 的严格超集：普通 Markdown（标题/表格/列表/代码）照常有效，额外内嵌三种**可编辑**
的图——`drawio` 围栏（mxGraph XML）、`excalidraw` 围栏（场景 JSON）与 `mermaid` 围栏
（mermaid 文本，裸围栏在 GitHub 上原生渲染），外加带宽度的图片
（`![alt](src "w=420")`，可内联成 data URI）。

产物拖进 <https://drawdocs.vercel.app> 即可打开继续编辑（图块双击进对应编辑器改），也可用
DrawDocs 的本地文件夹 / GitHub 模式打开。技能内置 `scripts/drawdoc.py` 组装器（按顺序追加
正文 / 图 / 白板 / mermaid / 图片块并写出 `.drawdoc`）；drawio 围栏接受 `.drawio` 路径或原始 mxGraph XML。
用「写一篇 .drawdoc」「生成能在 DrawDocs 里改的图文文档」等触发。

### gerrit-tool

在 **AOSP / repo 管理的多仓库工作区**里，把 Gerrit 上同一个 **topic** 下的所有 change
按依赖顺序 cherry-pick 到各自对应的项目目录。核心是 `scripts/gerrit_topic_pick.py`
（纯 python3 标准库）：

- 通过 **ssh** 查询 topic（`ssh -p 29418 <host> gerrit query`），复用 `repo sync`
  的那把 key，无需额外认证配置；Gerrit 地址可从 manifest 的 `review=` 属性自动发现。
- `repo list` 自动把 project 映射到本地目录，逐个 `repo download --cherry-pick`。
- 同一 relation chain 内 parent 先应用；已应用的 change 按 Change-Id 自动跳过，
  冲突解决后重跑同一条命令即可续摘。
- 支持 `--dry-run` 先看计划、`--status` / `--branch` 过滤；`--verify` 用
  `git patch-id` 比对 diff 内容，检出本地摘的是旧 patchset 的 change（标 `OUTDATED`）。

用「cherry-pick 某个 topic」「把 gerrit 上 topic X 的 patch 都摘下来」等触发。

### docforge

从代码、文档、issue、commit 或笔记等**有界源材料**生成一篇可溯源的技术文档。它把事实提取、结构与
图表撰写、质量复核分为串行的 GATHER → AUTHOR → VERIFY 三道门：每一条事实性论断和每个图元素都必须
映射到带 provenance 的 fact id；**所有配图强制使用当前最强可用的 ChatGPT 图像生成模型**，不允许回退
到 Mermaid、手写 SVG/HTML 或其他模型。适合「根据这个仓库写一篇系统设计文档」「从这些变更整理技术说明」
等需要可靠取据和可审计图文的请求。

它是独立的技术写作 workflow：自行维护范围、事实账本、大纲、图稿溯源与审稿记录，不要求目标项目预置
任何 DocForge 文件或配置。

### aosp-solution-doc

在 **AOSP / Android platform 源码工作区**里完成系统或 Framework 需求，并把实现、实验和评审材料整理成
可复现交付。它覆盖源码改动、必要的 `development/samples/<DemoName>` demo APK、模块或整机编译、
模拟器验证，以及最终 HTML 方案文档。

文档侧重点是工程评审可用性：HTML-only 时不维护 Markdown；代码修改位置做成接近 Gerrit 的效果，
新增文件展示完整源码，修改文件展示左右双栏 before/after diff；流程图和时序图以说明关键逻辑为主，
时序图箭头优先写方法调用关系，并用颜色和图例区分新增类、修改类与未改动类。

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json     # marketplace + plugin definitions
├── .agents/plugins/marketplace.json  # Codex marketplace
├── .claude-plugin/marketplace.json   # Claude Code marketplace
└── plugins/
    ├── write-drawdoc/
    │   ├── .codex-plugin/plugin.json
    │   └── skills/write-drawdoc/      # SKILL.md、脚本与格式参考
    ├── gerrit-tool/
    │   ├── .codex-plugin/plugin.json
    │   └── skills/gerrit-tool/        # SKILL.md 与 topic 批量 cherry-pick 脚本
    ├── aosp-solution-doc/
    │   ├── .codex-plugin/plugin.json
    │   └── skills/aosp-solution-doc/  # AOSP 改动、验证与 HTML 方案文档工作流
    └── docforge/
        ├── .codex-plugin/plugin.json
        └── skills/docforge/SKILL.md
```

## License

MIT
