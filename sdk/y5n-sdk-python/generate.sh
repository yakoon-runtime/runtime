#!/usr/bin/env bash
# -----------------------------------------------------------------------------
#  generate.sh — Generate SDK model classes from yds-v1.yaml
#
#  Usage:
#    ./generate.sh [input_yaml] [output_py]
#
#  Defaults:
#    input   = sdk/spec/yds/yds-v1.yaml
#    output  = sdk/y5n-sdk-python/src/y5n/sdk/models.py
#
#  Uses the project venv python so the installed y5n-sdk-python generator is
#  the one in this repo (not a stale system copy), then formats the output.
# -----------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SDK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

INPUT="${1:-$SDK_ROOT/spec/yds/yds-v1.yaml}"
OUTPUT="${2:-$PROJECT_ROOT/sdk/y5n-sdk-python/src/y5n/sdk/models.py}"

# Resolve relative to project root
if [[ "$INPUT" != /* ]]; then
    INPUT="$PROJECT_ROOT/$INPUT"
fi
if [[ "$OUTPUT" != /* ]]; then
    OUTPUT="$PROJECT_ROOT/$OUTPUT"
fi

PYTHON="${YAKOON_PYTHON:-$PROJECT_ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
    PYTHON="python3"
fi

echo "Generating from: $INPUT"
echo "Writing to:      $OUTPUT"

"$PYTHON" -m y5n.sdk.gen \
    --input "$INPUT" \
    --output "$OUTPUT"

if "$PYTHON" -m black --version >/dev/null 2>&1; then
    "$PYTHON" -m black "$OUTPUT" -q
fi

echo "Done."
