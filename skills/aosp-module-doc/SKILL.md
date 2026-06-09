---
name: aosp-module-doc
description: >-
  为单个 AOSP（Android 开源项目）模块或工具产出一篇完整的技术文档——可以是编译系统、某个工具
  （release_config、aconfig、soong、lunch），或某个框架子系统（init、SELinux、ART、binder、
  system_server、PackageManager 等）。产出一篇结构固定的文章：概述 → 整体架构(框图) →
  数据/概念 → 各子模块(每个配时序图/示意图) → 关键流程 → 配置与使用 → 调试工具 → 参考文档，
  全部基于当前上游源码核实，绝不凭训练记忆臆测。当用户要「写/生成/输出 一个 AOSP 模块或工具的
  文档/说明/分析」「讲清楚 AOSP 的 XXX 机制/模块/工具」「整理一份 XXX 的文档」「画 XXX 的
  架构图/时序图」时使用；也会被「AOSP 源码」「Android 编译系统」「最新版本的 XXX」触发。核心价值：
  AOSP 演进很快、训练知识容易过时（例如 release_config 已从 .scl 改为 .textproto），因此务必
  先对照实时源码核实。
---

# AOSP module / tool documentation

Produce **one technical article** about a single AOSP module or tool. The
deliverable reads like something a senior engineer wrote after reading the
source — concrete, specific, flowing prose — not like a generated template.
Diagrams are part of the article and carry a lot of the explanation.

Two things are non-negotiable: **the content is verified against current source**
(never written from memory), and **the article follows the structure below**.

There is **no local AOSP checkout** — read source online via gitiles (recipes at
the end). Default branch is `aosp main` (`refs/heads/main`) unless the user names
a specific branch/release tag. **The branch/version is stated once, in the
article header, and nowhere else** (see Source grounding).

## Source grounding

1. **Never describe a mechanism from memory.** Read the actual current source
   before writing any factual claim. If you can't fetch something, say so rather
   than filling the gap from memory.
2. **State the version once, in the header.** The article opens with a single
   line like `> 本文基于 Android <version>（aosp/<branch>）。`. Do **not** sprinkle
   `path @ branch` tags through the body — no per-claim citations, no repo paths
   in section text. Referring to a real file/type/function by name in prose
   (e.g. "在 `release_config.go` 的 `GenerateReleaseConfig()` 里") is normal and
   encouraged; pasting full gitiles paths is noise.
3. **Read before guessing paths.** Browse the directory listing first; a 404
   means the path differs from memory — re-check, don't guess again.
4. **Unverified content** is either left out or marked once with a short
   `（未核实）`. Don't ship memory-based guesses dressed as fact.
5. **Source is the truth; docs and blogs are supplements.** Besides reading the
   code, search the official docs (`source.android.com`) and reputable blogs /
   conference talks for the module, and absorb what genuinely improves the
   article — naming rules, usage patterns, rationale, history, gotchas. Verify
   anything you take against the source; if a blog contradicts the code, trust
   the code. Skip low-quality SEO/AI-spam pages — quality over quantity.
6. **End with a required `参考文档` section** (the last numbered section) listing
   each reference actually used, each with a one-line note on what it's good for.
   Include the authoritative source dirs and the useful official docs/blogs;
   omit anything you didn't actually draw on.

## Writing style — avoid the "AI 腔"

The user specifically dislikes generated-sounding docs. Apply these:

- **Prose first, lists second.** Explain in connected paragraphs. Use bullet
  lists only for genuinely enumerable things (flags, fields, file lists). Don't
  turn every explanation into a bullet shower.
- **No filler or hedging.** Cut "值得注意的是 / 总而言之 / 需要强调的是 / 总的来说",
  cut restating the section title in its first sentence, cut empty summary
  paragraphs.
- **Be concrete.** Real file names, type names, field names, numbers, defaults.
  Specifics replace adjectives — never "灵活强大的机制", say what it actually does.
- **No decoration.** No emoji, no bold-on-every-line, no "一句话：" labels. Bold
  sparingly for genuine key terms.
- **Section titles name real things,** not abstract buckets. Prefer
  "配置文件与 textproto schema" over "核心概念/数据模型"; prefer "Binder 事务的内核数据
  结构" over "数据模型".
- Match the user's language (Chinese stays Chinese) and write like internal
  engineering documentation.

## Article structure

Sections in this order. Adapt depth to the module; never drop 概述, 整体架构,
子模块, 关键流程, 调试工具.

### Numbering & table of contents (required)

- **Number every heading.** H2 uses Chinese ordinals `一、二、三、…`; H3 uses
  `<n>.<m>` where `<n>` is the parent's arabic number (e.g. under 「四、子模块详解」
  the subsections are `4.1`, `4.2`, …); H4 uses `<n>.<m>.<k>` (e.g. `4.2.1`).
- **Include a `## 目录` section** right after the header/version line, before
  「一、概述」. Write it as a nested list of the numbered section + subsection
  titles. (When exported to HTML it becomes a clickable TOC automatically.) The
  `目录` heading itself is not numbered.

### Heading wording (required)

- **Headings are declarative noun phrases.** No question form — never
  「它解决什么问题」「数据怎么流动」「如何…」「为什么…」. Use a noun phrase instead:
  「解决的问题」「数据流向」「取值合并规则」.
- **No parentheses in headings** — neither `（…）` nor `(…)`. A heading states the
  topic; any aside, qualifier, or "纠偏" note belongs in the body, not the title.
  E.g. not 「1.2 编写格式（一个重要纠偏）」, but 「1.2 编写格式从 scl 迁移到 textproto」.

### Anti–wall-of-text (required)

A reader should be able to scan the article by its headings. Do not pile
paragraphs under one heading.

- **Every 一级标题 (H2) must contain at least one 二级标题 (H3).** No H2 may hold a
  long body passage directly. An H2 may open with a 1–2 sentence lead, but its
  substance lives in its 二级标题 subsections — this applies to *every* top-level
  section, including short ones like 概述 / 整体架构 / 关键流程 (split them, e.g.
  概述 → "解决什么问题" + "重要纠偏/版本变化" + "代码与数据在哪"). The structural
  sections `目录` and `参考文档` are exempt — they are plain annotated lists.
- **Heading depth is capped at 四级标题** (markdown H5, the `x.y.z.w` form). Don't
  nest deeper; if you need more, the structure is wrong — flatten or regroup.
- A subsection (H3) opens with a 1–2 sentence lead, then breaks its content into
  **H4 sub-headings**, a short list, or a table — whenever it covers more than
  one distinct point or would run past ~3 paragraphs.
- **The core-logic submodule and the 调试工具 section are the usual offenders —
  they must be decomposed.** E.g. split a core library into "职责与关键文件" +
  "关键算法/流程(配图)"; split 调试工具 into one H3 per tool or per task
  (查取值 / 看生效值 / 读产物 / …), not one long blob.
- Prefer several short, titled chunks over one dense passage. Each chunk earns
  its heading; if a chunk has nothing distinct to say, merge it.

1. **头部** — title + one line stating the Android version/branch. Nothing else.

2. **概述** — the module/tool's overall function: what it is, what problem it
   solves, where it sits in Android. Flowing prose. If a mechanism changed across
   versions or is commonly misunderstood (e.g. scl→textproto), weave that into
   the prose naturally — don't bolt on a labeled "纠偏" block.

3. **整体架构** — the spine of the whole article. **Embed an architecture block
   diagram (框图)** and walk the reader through how data/control flows across the
   components. The diagram is 提纲挈领:
   - **Each box = one component that gets its own 子模块 subsection later**, and
     the box label should match (or clearly map to) that subsection's title.
   - **Box text is concise but informative** — name the component AND hint its
     responsibility (a short second line), not a single bare word, not a sentence.
   - The set of boxes should preview the article's structure, so a reader who
     only looks at this diagram understands the module's decomposition.

4. **<concrete data/concept section>** — the core data the module operates on:
   schemas, config formats, key structs/protos/enums, state. **Title it after the
   real thing** (e.g. "配置文件与 textproto schema", "核心数据结构与状态"), not the
   generic words "核心概念/数据模型". Quote real definitions from source.

5. **子模块详解** — one subsection per architecture box, titled to match. Go as
   deep as the source allows: responsibility, the key files/functions/interfaces,
   how it talks to the other submodules, important edge cases. **Each submodule
   should carry its own 时序图 or 示意图** (its internal call sequence, state
   transitions, or data shape) — the more detailed, the better. This is where the
   article earns its value; don't keep it shallow.

6. **关键流程** — the main end-to-end flow(s). **Embed a sequence diagram (时序图)
   or flowchart (流程图)** for at least the primary flow.

7. **配置与使用** — how to invoke/configure: CLI flags, env vars, build vars,
   file layout, entry points (how `lunch`/`m`/a syscall triggers it).

8. **调试工具** — concrete: real CLIs, dump/print commands, artifacts to inspect,
   logs, build vars to query, test dirs. Must be runnable, not hand-wavy. Always
   include.

9. **参考文档** — the last section. An annotated list of the references actually
   used: authoritative source dirs, useful official docs (`source.android.com`),
   and quality blogs/talks. One short line per entry saying what it offers. No
   subsections (exempt from the H3 rule).

(Author's pre-delivery self-check stays out of the article — see the checklist
at the end of this skill. The 参考文档 section, by contrast, is part of the
article and required.)

## Diagrams

Diagrams come from the verified source and do real explanatory work. Generate
them with the **`drawio-diagrams`** skill (editable `.drawio` + exported
`png`/`svg`), save next to the article, embed with `![标题](./xxx.png)`, and put a
one-line caption noting it's based on the same version as the header.

- **整体架构 → 框图 (block):** boxes map 1:1 to 子模块 subsections (see §3). Make
  labels meaningful; this diagram is the outline.
- **每个子模块 → 时序图/示意图:** prefer a sequence diagram for call/interaction
  order, a flowchart for step/decision logic, a block/schematic for data shape or
  state. Detailed beats pretty.
- **关键流程 → 时序图 or 流程图.**

Plan the architecture diagram and the submodule breakdown *together* so the boxes
and the later subsections line up.

## Workflow

1. **Pin the version.** Default `aosp main`. State it in the header only.
2. **Locate & read the real source.** Map topic → git project(s)+path(s); don't
   trust memory for paths. `WebSearch` `android.googlesource.com <module>` or use
   the project index, then browse directory listings and read the files behind
   every section: schemas/protos, entry points, the core library, Android.bp,
   READMEs. Decide the component decomposition from what you read — this drives
   both the architecture diagram and the 子模块 sections.
   Then **search supporting material** — official docs on `source.android.com`
   and reputable blogs/talks — and pull in what improves the article (naming
   rules, how to consume the thing, rationale, history), verifying each point
   against the source. Note which references you actually used for `参考文档`.
   > Path-mapping gotcha: gitiles project `platform/build` → tree `build/make/`;
   > `platform/build/release` → `build/release/`; `platform/build/soong` →
   > `build/soong/`. A 404 usually means wrong project/path — re-check the listing.
3. **Plan structure + diagrams together,** then write the article in flowing prose
   per the style rules.
4. **Generate the diagrams** (architecture, per-submodule, key-flow) via
   `drawio-diagrams`; embed and caption them.
5. **Save & report.** Keep the article and all its diagrams **together in one
   folder** so the relative `![](./...)` image links resolve. The skill does
   **not** mandate a location — save wherever fits the current context (the
   working directory, or wherever the user keeps such docs); let Claude Code
   decide from where it was invoked. Illustrative layout (one folder per module):
   ```
   <module>/
     <module>.md
     <module>.html                (optional, see below)
     <module>_architecture.drawio (+ .png/.svg)
     <module>_<submodule>.drawio  (+ .png/.svg)
     <module>_<flow>.drawio       (+ .png/.svg)
   ```
   Report the paths; note diagrams are editable in draw.io.

### Optional: HTML export

The markdown is the single source. To also produce a styled, standalone HTML
(clickable auto-generated TOC, styled code/tables, figures), run the bundled
converter — no dependencies needed:
```
python3 <skill>/scripts/md2html.py <module>.md <module>.html
```
It reads the `## 目录` section and replaces it with a clickable TOC built from the
numbered H2/H3 headings, and gives every heading an anchor id. Images are
referenced relatively, so keep the `.html` next to the `.png` files.

## Retrieval recipes (verified working)

Use gitiles = `android.googlesource.com` (server-rendered HTML, WebFetch reads it
reliably):

- **Directory listing:** `.../platform/<project>/+/refs/heads/main/<subdir>/`
- **File content:** `.../platform/<project>/+/refs/heads/main/<path>`
- **Raw bytes (base64 — decode):** append `?format=TEXT`.
- **File history (when did X change):** `.../platform/<project>/+log/refs/heads/main/<path>`
- **Project index:** `https://android.googlesource.com/`

Common projects: `platform/build` (→`build/make/`), `platform/build/release`,
`platform/build/soong`, `platform/frameworks/base`, `platform/system/core`.

**Do NOT fetch `cs.android.com`** — JS SPA, WebFetch gets an empty shell. Read via
gitiles. The WebFetch summarizer may truncate long files — fetch in parts or use
`?format=TEXT`.

## Author's pre-delivery self-check (not part of the article)
- [ ] Version stated once in the header; no `path @ branch` tags in the body.
- [ ] `## 目录` present after the header; every H2/H3/H4 is numbered
      (一、二 / 4.1 / 4.2.1).
- [ ] Every 一级标题 (H2) has ≥1 二级标题 (H3) — no H2 holds a long passage
      directly. Depth never exceeds 四级标题 (H5).
- [ ] No heading is a question; no heading contains `（…）` / `(…)`.
- [ ] Official docs / quality blogs searched; valuable points absorbed (verified
      against source). Final `参考文档` section lists each reference used, annotated.
- [ ] No wall of text — dense topics (core logic, 调试工具) split into titled
      chunks / lists / tables; the article scans by its headings.
- [ ] Reads like human engineering prose — no AI filler, no bullet-shower, no
      abstract section titles.
- [ ] Architecture 框图 boxes map 1:1 to 子模块 subsections, labels informative.
- [ ] Every 子模块 has a detailed 时序图/示意图; key flow has its diagram.
- [ ] 调试工具 section is concrete and runnable.
- [ ] No `.scl`-era / `Android.mk`-era (or other stale) assumption survived; every
      mechanism was read from current source. Unverified bits left out or marked
      once with `（未核实）`.
