#!/usr/bin/env bash
# Post-process Fern output after it overwrites src/onepin/:
#   1. Restore py.typed PEP 561 markers.
#   2. Rebrand the generated SDK README ("Podonos" -> "OnePin").
# Run this after every `fern generate` invocation.
set -euo pipefail
touch src/onepin/py.typed
touch src/onepin/_cli/py.typed
echo "Restored py.typed markers after Fern regen."

# Brand name only: case-sensitive so the lowercase "podonos" org slug in URLs is preserved.
if [ -f src/onepin/README.md ]; then
  sed -i.bak 's/Podonos/OnePin/g' src/onepin/README.md && rm -f src/onepin/README.md.bak
  echo "Rebranded src/onepin/README.md (Podonos -> OnePin)."
fi

# Scrub an internal backend symbol path Fern copies verbatim from the spec docstring.
if [ -f src/onepin/types/triggered_by_out.py ]; then
  sed -i.bak 's/donut\.utils\.user\.user_display_name/the user display name/g' src/onepin/types/triggered_by_out.py && rm -f src/onepin/types/triggered_by_out.py.bak
  echo "Scrubbed internal symbol path in triggered_by_out.py."
fi
