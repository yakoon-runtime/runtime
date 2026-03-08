from __future__ import annotations

import json
import re
from typing import Any

import yaml

from yakoon.base.capabilities.workflow.types import (
    StepDef,
    WorkflowDef,
)

from ..runtime.builder import (
    GraphValidator,
    StepAssembler,
)


class DefaultWorkflowCompileService:

    def compile(self, command_key: str, raw_text: str) -> WorkflowDef:
        raw = self._parse(command_key, raw_text)
        return self._build_workflow_def(command_key, raw)

    def _parse(self, command_key: str, raw: str) -> dict[str, Any]:
        try:
            # try YAML first
            return _yaml12_safe_load(raw)
        except Exception:
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError(
                        f"{command_key}: workflow must contain mapping at root."
                    )
                return data
            except Exception as e:
                raise ValueError(f"{command_key}: invalid workflow format") from e

    def _build_workflow_def(self, command_key: str, raw: dict[str, Any]) -> WorkflowDef:
        start = raw.get("start")
        if not start or not isinstance(start, str):
            raise ValueError(f"{command_key}: missing 'start'.")

        raw_steps = raw.get("steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ValueError(f"{command_key}: 'steps' must be a non-empty list.")

        assembler = StepAssembler()
        validator = GraphValidator()

        steps: dict[str, StepDef] = {}
        for s in raw_steps:
            if not isinstance(s, dict):
                raise ValueError(f"{command_key}: each step must be a mapping.")

            sid = s.get("id")
            if not sid or not isinstance(sid, str):
                raise ValueError(f"{command_key}: step without id.")

            if sid in steps:
                raise ValueError(f"{command_key}: duplicate step id '{sid}'.")

            steps[sid] = assembler.build(command_key, sid, s)

        validator.validate(command_key, steps, start)
        return WorkflowDef(id=command_key, start=start, steps=steps)


class Yaml12SafeLoader(yaml.SafeLoader):
    """SafeLoader with YAML 1.2 bool behavior: only true/false are booleans."""


def _yaml12_safe_load(raw: str) -> dict[str, Any]:
    # Remove YAML 1.1 bool resolver (on/off/yes/no, etc.)
    for first_char, mappings in list(Yaml12SafeLoader.yaml_implicit_resolvers.items()):
        Yaml12SafeLoader.yaml_implicit_resolvers[first_char] = [
            (tag, regexp)
            for (tag, regexp) in mappings
            if tag != "tag:yaml.org,2002:bool"
        ]

    # Add YAML 1.2 bool resolver: only true/false (case-insensitive)
    yaml12_bool = re.compile(r"^(?:true|false)$", re.IGNORECASE)
    Yaml12SafeLoader.add_implicit_resolver(
        "tag:yaml.org,2002:bool",
        yaml12_bool,
        list("tTfF"),
    )

    data = yaml.load(raw, Loader=Yaml12SafeLoader)
    if data is None:
        raise ValueError("Workflow YAML is empty.")
    if not isinstance(data, dict):
        raise ValueError("Workflow YAML must contain a mapping at root.")
    return data
