---
name: docforge
description: Create or substantially revise a traceable technical document from bounded source material such as code, docs, issues, commits, or notes. Use when the deliverable needs fact provenance, source-grounded diagrams, and a serial gather-author-verify quality gate; do not use for a small prose edit.
---

# DocForge

Use the DocForge engine in the current repository. It turns bounded source material into a
reader-facing technical document whose claims and diagram elements trace to source facts.

## Start a run

1. Confirm the repository has `AGENTS.md`, `scripts/docforge.py`, and `.claude/contracts/`.
   If it does not, explain that this skill needs the DocForge engine checkout; do not invent its
   contracts or workflow.
2. Read the repository `AGENTS.md` in full. It is the authoritative runtime instruction.
3. Initialize an isolated blackboard:

   ```sh
   python3 scripts/docforge.py init "<target>" --source-root <path> --lang <language>
   ```

   Use the emitted `.docforge/runs/<run-id>/` for every generated artifact. Do not write to
   `.claude/workspace/`, which only holds legacy examples.

## Run the gates serially

1. **GATHER** — Read `.claude/agents/miner.md`,
   `.claude/skills/fact-extract/SKILL.md`, and the relevant contracts. Write `boundary.json`
   and `facts.json`; do not proceed until both validate and every node/edge has provenance.
2. **AUTHOR** — Read `.claude/agents/writer.md`, its linked outline/diagram templates, and the
   diagram skills when a diagram is needed. Write `outline.md`, any diagrams and trace sidecars,
   and `draft.md`. Structural diagrams are hand-authored HTML/SVG; only sequence diagrams use
   Mermaid.
3. **VERIFY** — Read `.claude/agents/verifier.md` and `.claude/rubrics/doc.yaml`. Write
   `review.json`. On `BOUNCE`, return to the owning phase and rerun downstream gates; allow at
   most three bounce cycles.

Only promote `draft.md` to `document.md` when the verdict is `PASS`. Before publishing, run:

```sh
python3 scripts/docforge.py check <run-dir> --publishable
```

## Non-negotiable rules

- Ground every factual assertion and diagram element in a fact id with provenance.
- Label inference as `inference`, with `likely` or lower confidence and references to supporting
  fact ids.
- Keep reader-facing prose in the requested language; preserve source quotes, code, paths, IDs,
  and identifiers verbatim.
- Report missing source material or unresolved questions rather than fabricating facts.
