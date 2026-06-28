#!/usr/bin/env bash
set -euo pipefail

createdb yakoon_crm 2>/dev/null || echo "Database yakoon_crm already exists"
