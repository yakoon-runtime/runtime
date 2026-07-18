"""Document schema — field names for child-bearing block types."""

CHILDREN_FIELDS = {
    "kv": "items",
    "list": "items",
    "list_item": "blocks",
    "section": "blocks",
    "stack": "blocks",
    "flow": "blocks",
    "collapsible": "blocks",
}
