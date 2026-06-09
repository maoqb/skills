#!/usr/bin/env bash
# export.sh — render a .drawio file to SVG / PNG / PDF.
#
# Two export paths:
#   1. Python SVG (always works, no install needed):
#      Calls save_svg() on the builder that generated the diagram.
#      Default format; SVG embeds cleanly in markdown with ![](./x.svg).
#   2. drawio CLI (higher fidelity, needed for PNG/PDF):
#      Uses the drawio desktop app. Install instructions below.
#      On headless Linux: xvfb-run -a ./export.sh diagram.drawio png
#
# Installing the drawio CLI:
#   macOS:  brew install --cask drawio
#   Linux:  download .deb / AppImage from github.com/jgraph/drawio-desktop
#
# Usage:
#   ./export.sh diagram.drawio            # -> diagram.svg  (Python, always works)
#   ./export.sh diagram.drawio svg        # -> diagram.svg
#   ./export.sh diagram.drawio png        # -> diagram.png  (needs drawio CLI)
#   ./export.sh diagram.drawio pdf out.pdf

set -euo pipefail

SRC="${1:?usage: export.sh <file.drawio> [svg|png|pdf] [output]}"
FMT="${2:-svg}"
OUT="${3:-${SRC%.*}.$FMT}"
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── Try the drawio CLI for png/pdf ──────────────────────────────────────────
DRAWIO_CLI=""
if command -v drawio >/dev/null 2>&1; then
  DRAWIO_CLI="drawio"
elif [ -x "/Applications/draw.io.app/Contents/MacOS/draw.io" ]; then
  DRAWIO_CLI="/Applications/draw.io.app/Contents/MacOS/draw.io"
fi

if [ -n "$DRAWIO_CLI" ] && [ "$FMT" != "svg" ]; then
  EXTRA=()
  if [ "$FMT" = "png" ]; then EXTRA=(--scale 2); fi
  "$DRAWIO_CLI" --export --format "$FMT" --crop "${EXTRA[@]}" --output "$OUT" "$SRC"
  echo "wrote $OUT  (drawio CLI)"
  exit 0
fi

# ── Python SVG export (no external tools needed) ────────────────────────────
if [ "$FMT" = "png" ] || [ "$FMT" = "pdf" ]; then
  echo "NOTE: drawio CLI not found — exporting SVG instead of $FMT." >&2
  FMT="svg"; OUT="${SRC%.*}.svg"
fi

# Find the companion Python generation script (same stem, same or parent dir).
GEN_PY="${SRC%.*}.py"
[ -f "$GEN_PY" ] || GEN_PY="$(dirname "$SRC")/$(basename "${SRC%.*}").py"

if [ -f "$GEN_PY" ]; then
  python3 - "$GEN_PY" "$OUT" "$SKILL_DIR/scripts" <<'PYEOF'
import sys, importlib.util

gen_script, out_path, scripts_dir = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, scripts_dir)
import drawio as _dmod

_last = [None]
for _cls in (_dmod.Sequence, _dmod.BlockDiagram, _dmod.Flowchart):
    _orig = _cls.save
    def _wrap(self, p, _o=_orig):
        _last[0] = self
        return _o(self, p)
    _cls.save = _wrap

spec = importlib.util.spec_from_file_location("_gen", gen_script)
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if _last[0] is not None:
    _last[0].save_svg(out_path)
    print(f"wrote {out_path}  (Python SVG)")
else:
    print("WARNING: no builder found in generation script", file=sys.stderr)
    sys.exit(1)
PYEOF
else
  echo "ERROR: no generation script found for $SRC" >&2
  echo "To generate SVG, call builder.save_svg('${SRC%.*}.svg') in your script." >&2
  exit 1
fi
