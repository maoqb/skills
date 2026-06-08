#!/usr/bin/env bash
# export.sh — render a .drawio file to PNG / SVG / PDF using the drawio CLI.
#
# The .drawio file itself is always the source of truth (open it in draw.io to
# edit). This script just produces a flat image for embedding in notes/docs.
#
# Requirements: the drawio desktop app provides the CLI. If it's missing:
#   macOS:  brew install --cask drawio
#           # CLI then lives at /Applications/draw.io.app/Contents/MacOS/draw.io
#   Linux:  download the AppImage / .deb from github.com/jgraph/drawio-desktop
#   npm:    not available — drawio-desktop is an Electron app, not an npm pkg.
#
# Usage:
#   ./export.sh diagram.drawio                 # -> diagram.png (default)
#   ./export.sh diagram.drawio svg             # -> diagram.svg
#   ./export.sh diagram.drawio pdf out.pdf     # explicit output path
#
# Headless note: exporting needs a display. On a headless Linux box wrap the
# command with `xvfb-run -a ...`.

set -euo pipefail

SRC="${1:?usage: export.sh <file.drawio> [png|svg|pdf] [output]}"
FMT="${2:-png}"
OUT="${3:-${SRC%.*}.$FMT}"

# locate the drawio binary
if command -v drawio >/dev/null 2>&1; then
  DRAWIO="drawio"
elif [ -x "/Applications/draw.io.app/Contents/MacOS/draw.io" ]; then
  DRAWIO="/Applications/draw.io.app/Contents/MacOS/draw.io"
else
  echo "ERROR: drawio CLI not found." >&2
  echo "Install it (macOS): brew install --cask drawio" >&2
  echo "The .drawio file is still valid — open it at https://app.diagrams.net" >&2
  exit 1
fi

# --crop trims whitespace; --scale 2 gives a crisp PNG. Adjust as needed.
EXTRA=()
if [ "$FMT" = "png" ]; then EXTRA=(--scale 2); fi

"$DRAWIO" --export --format "$FMT" --crop "${EXTRA[@]}" --output "$OUT" "$SRC"
echo "wrote $OUT"
