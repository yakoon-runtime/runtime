"""Runtime operations and node->bit mapping.

The engine knows only operations; the node maps an operation onto the
required permission bit via navigable (container vs leaf/command).
"""

from __future__ import annotations

import pytest
from y5n.runtime.api.permissions import Operation
from y5n.runtime.engine.nodes import Node


def test_operation_values():
    assert Operation.READ.value == "read"
    assert Operation.WRITE.value == "write"
    assert Operation.EXECUTE.value == "execute"


def test_container_maps_read_and_write():
    node = Node(key="opt", navigable=True)

    assert node.required_bit(Operation.READ) == "r"
    assert node.required_bit(Operation.WRITE) == "w"
    # execute on a container means entering/listing -> read
    assert node.required_bit(Operation.EXECUTE) == "r"


def test_leaf_command_maps_read_and_execute():
    node = Node(key="ls", navigable=False)

    assert node.required_bit(Operation.READ) == "r"
    assert node.required_bit(Operation.WRITE) == "w"
    assert node.required_bit(Operation.EXECUTE) == "x"


def test_unknown_operation_raises():
    node = Node(key="x", navigable=False)

    with pytest.raises(ValueError):
        node.required_bit("bogus")  # type: ignore[arg-type]
