"""The PostgreSQL schema of the runtime store as package resources.

Three idempotent DDL scripts (see ADR-19; bootstrap / schema setup is
the next lifecycle decision). The destructive ``EMPTY.sql`` maintenance
script is deliberately not part of the schema resources.
"""
