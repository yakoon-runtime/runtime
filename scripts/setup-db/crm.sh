#!/usr/bin/env bash
set -euo pipefail

PSQL_OPTS="${PSQL_OPTS:--U postgres -h localhost}"

createdb $PSQL_OPTS yakoon_crm 2>/dev/null || echo "Database yakoon_crm already exists"

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

# Event-Store
EVENT_SQL="$REPO_DIR/stores/y5nstore-event/sql/postgres"
psql $PSQL_OPTS -d yakoon_crm -q -f "$EVENT_SQL/CREATE_TABLE.sql"
psql $PSQL_OPTS -d yakoon_crm -q -f "$EVENT_SQL/CREATE_INDEX.sql"

# Sequencer
createdb $PSQL_OPTS yakoon_crm_seq 2>/dev/null || echo "Database yakoon_crm_seq already exists"
SEQ_SQL="$REPO_DIR/stores/y5nstore-sequence/sql/postgres"
psql $PSQL_OPTS -d yakoon_crm_seq -q -f "$SEQ_SQL/CREATE_TABLE.sql"
