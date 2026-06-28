#!/usr/bin/env bash
set -euo pipefail

createdb yakoon_crm 2>/dev/null || echo "Database yakoon_crm already exists"

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SQL_DIR="$REPO_DIR/stores/y5nstore-event/src/y5nstore/event/backends/postgres"
psql -d yakoon_crm -q -f "$SQL_DIR/CREATE_TABLE.sql"
psql -d yakoon_crm -q -f "$SQL_DIR/CREATE_INDEX.sql"
