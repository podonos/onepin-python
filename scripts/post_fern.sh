#!/usr/bin/env bash
# Restore py.typed PEP 561 markers after Fern overwrites src/onepin/.
# Run this after every `fern generate` invocation.
set -euo pipefail
touch src/onepin/py.typed
touch src/onepin/_cli/py.typed
echo "Restored py.typed markers after Fern regen."
