"""Document schema — field names for child-bearing block types.

Canonical definition: ``docs/yds/yds-v1.yaml`` → ``children_fields``.
This module is a thin runtime helper, not the source of truth.
"""

CHILDREN_FIELDS = {
    "kv": "items",
    "list": "items",
    "list_item": "blocks",
    "section": "blocks",
    "stack": "blocks",
    "flow": "blocks",
    "collapsible": "blocks",
}
