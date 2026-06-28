#!/usr/bin/env bash
set -euo pipefail

for script in "$(dirname "$0")"/setup-db/*.sh; do
  echo "Running $script"
  bash "$script"
done
