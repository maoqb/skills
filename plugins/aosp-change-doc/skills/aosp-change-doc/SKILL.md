---
name: aosp-change-doc
description: >-
  在 AOSP / Android platform 源码中完成系统或 Framework 需求，并交付实验验证与
  HTML 方案文档。当用户要求修改 AOSP、编译整机或模块、跑模拟器验证、补 demo APK、
  输出方案文档、代码修改位置或 Gerrit 风格 diff 时使用；普通 Android App 开发不要使用。
---

# AOSP Change Doc

用于把一次 AOSP 需求做成可复现、可验证、可评审的交付：源码改动、必要的实验 APK、
编译/模拟器验证，以及一份空间利用充分的 HTML 方案文档。

## 工作方式

- 先读现有代码和本地构建状态，再决定修改点。AOSP 往往是 `repo` 管理的多仓库工作区，
  顶层不一定是普通 git 仓库；需要 diff 时进入具体项目目录或使用 `repo diff` / `repo status`。
- 改动要贴近现有 framework/server/app 模式，避免为了实验需求新增公开 API 或跨层大改。
  临时实验开关优先放在便于 `adb shell settings put` 调整的位置，除非用户要求产品化接口。
- 对窗口、启动、显示、输入、多用户等系统行为，优先找统一调度点，避免只覆盖某个入口。
  同时检查后续校验路径，确认不会被 resizeability、display area、windowing mode 或权限校验回退。
- demo APK 只在它能显著提升验证效率时添加，通常放在 `development/samples/<DemoName>`，
  保持自包含，并展示能证明行为的观测数据，如 bounds、WindowMetrics、configuration、density、
  decor size/location、当前 activity/component。
- 编译优先复用用户已配置好的 lunch target。常用形式是
  `source build/envsetup.sh && lunch <target> && m <module...>`；只有用户要求或效果验证必须时，
  才重新编译整机、重启模拟器或刷入镜像。
- 模拟器验证要记录精确命令和观察结果，例如 `adb shell settings put ...`、
  `adb shell am start -W ...`、`dumpsys window containers`、`logcat`。不要凭记忆猜设置项名称，
  先在源码里确认当前分支实际使用的 key。

## HTML 方案文档

当用户要求方案文档，尤其要求 HTML 时，维护 HTML 作为最终产物；用户明确说不要 Markdown 时，
删除或忽略同名 `.md`，不要再把 Markdown 当源文件。

文档应默认包含：

- 背景与目标：说明需求边界、实验性质、非目标。
- 使用方式：配置格式、adb 命令、demo APK 启动方式、预期观测结果。
- 实现方案：关键类、关键入口、为什么选择这些修改点。
- 编译与验证：模块/整机构建命令、输出 APK/JAR/镜像路径、模拟器验证证据。
- 风险与回退：resizeability、freeform 支持、display bounds、稳定区裁剪、兼容性影响。
- 代码修改位置：按文件展示真实改动，而不是只列路径。

HTML 版式要高密度、宽屏友好。使用宽 `main` 容器、紧凑目录、表格和横向滚动代码区，
避免大片空白和低信息密度卡片。最终用浏览器渲染检查 Mermaid、表格和代码块没有明显错位。

## Gerrit 风格代码展示

“代码修改位置”应做成接近 Gerrit 的 review 效果：

- 新增文件：直接展示完整源码；太长时用 `<details>` 折叠，默认可展开阅读。
- 修改文件：使用左右双栏 diff，左侧是修改前，右侧是修改后，带行号和变更高亮。
- 大文件或长 diff：按文件或 hunk 折叠，摘要里写清职责和本次变化。
- 代码内容必须来自真实文件和真实 diff；如果本地没有可靠 before 版本，先说明来源限制，
  再用可验证的方式生成对比，不要手工编造旧代码。
- 文件标题要包含状态，如 `NEW FILE`、`MODIFIED`、`DELETED`，并保留完整路径，方便以后评审定位。

## 图表规范

图表服务逻辑说明，不堆实现细节。每张图只表达一个关键问题，例如启动决策、配置解析、
校验放行或回退路径。

- 流程图/框图：保留关键判断和结果，不把所有类、字段、异常分支都塞进一张图。
- 时序图：箭头文字尽量体现方法调用关系，例如 `startActivity()`、
  `calculate(..., PHASE_BOUNDS)`、`onCalculate(...)`、`getBoundsForActivity()`、
  `setBounds(mBounds)`；不要让箭头全是中文解释。
- 如果要区分新增类、修改类、未改动类，使用颜色和图例表达。participant 标签只写类名或角色名，
  不要在 participant 文本或分组标题里重复写“新增类”“涉及修改的类”“未改动类”。
- Mermaid `box rgba(...)` 可以只写颜色、不写描述；分类文字放在图例里即可。

## 交付收尾

最终回复要说明：

- 改了哪些源码模块和 demo；
- HTML 文档路径；
- 已执行的构建/验证命令和关键观察结果；
- 哪些事没有做，例如未重新编译整机、未重启模拟器或某项验证受阻。

如果工作区有用户已有改动，不要回滚。只提交或描述本次任务相关文件。
