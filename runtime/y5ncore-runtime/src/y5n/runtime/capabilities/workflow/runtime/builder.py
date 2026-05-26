from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from y5n.base.capabilities.workflow.types import (
    InputBranchesDef,
    InputDef,
    InputFieldDef,
    RunDef,
    StepDef,
    SwitchDef,
)


class WorkflowFileNotFound(FileNotFoundError):
    pass


@dataclass(frozen=True, slots=True)
class StepContext:
    command_key: str
    step_id: str
    raw: dict[str, Any]

    def err(self, message: str) -> ValueError:
        # Consistent prefix for grep-ability: workflow:step
        return ValueError(f"{self.command_key}:{self.step_id}: {message}")

    def step_err(self, message: str) -> ValueError:
        # Alternative prefix used by some validations (kept readable)
        return ValueError(f"Step '{self.step_id}': {message}")


def _normalize_case_key(value: Any) -> str:
    return str(value).strip().lower()


# ----------------------------
# Step builders
# ----------------------------


class LegacyGuard:
    """Hard removal of old DSL keys."""

    def validate(self, ctx: StepContext) -> None:
        s = ctx.raw
        if s.get("prompt") is not None:
            raise ctx.err("'prompt' is no longer supported; use 'input'.")
        if s.get("branch") is not None:
            raise ctx.err("'branch' is replaced by 'input.branches'.")


class RunBuilder:
    """
    Parses:
      run: <command_key>
      args: [ ... ]  (optional)
    Enforces:
      - if 'args' is present, run must be set
      - if 'args' is present, run must be a single token (no whitespace)
      - args must be list[str], no empty strings
    """

    def build(self, ctx: StepContext) -> RunDef | None:
        s = ctx.raw
        run_key = s.get("run")

        has_args = "args" in s
        raw_args = s.get("args")

        if has_args:
            if raw_args is None:
                raw_args = []

            if not isinstance(raw_args, list) or not all(
                isinstance(x, str) for x in raw_args
            ):
                raise ctx.err("args must be a list of strings.")

            if any(not x.strip() for x in raw_args):
                raise ctx.err("args must not contain empty strings.")

            if not run_key or not isinstance(run_key, str):
                raise ctx.err("'args' requires 'run' to be set to a command key.")

            if any(ch.isspace() for ch in run_key):
                raise ctx.err(
                    "'run' must not contain whitespace when 'args' is present; "
                    "move parameters into 'args'."
                )
        else:
            raw_args = []

        if run_key is None:
            return None

        if not isinstance(run_key, str) or not run_key.strip():
            raise ctx.err("'run' must be a non-empty string when provided.")

        return RunDef(key=run_key, args=raw_args)


class SwitchBuilder:
    """
    Parses:
      switch:
        expr: <string>
        cases: { <key>: <step_id>, ... }
        default: <step_id> (optional)
    """

    def build(self, ctx: StepContext) -> SwitchDef | None:
        s = ctx.raw
        raw_switch = s.get("switch")
        if raw_switch is None:
            return None

        if not isinstance(raw_switch, dict):
            raise ctx.step_err("switch must be a mapping.")

        expr = raw_switch.get("expr")
        cases = raw_switch.get("cases")
        default = raw_switch.get("default")

        if not expr or not isinstance(expr, str):
            raise ctx.step_err("switch.expr must be a non-empty string.")

        if not isinstance(cases, dict) or not cases:
            raise ctx.step_err("switch.cases must be a non-empty mapping.")

        norm_cases = {_normalize_case_key(k): v for k, v in cases.items()}

        if default is not None and not isinstance(default, str):
            raise ctx.step_err("switch.default must be a string step id (or omitted).")

        return SwitchDef(expr=expr, cases=norm_cases, default=default)


class InputBuilder:
    """
    Parses:
      input:
        title: <string> (optional)
        fields: [ {var, policy?, title?, required?, default?, options?}, ... ]
        branches:
          on: <var key>
          cases: { <value>: <step_id>, ... }
    """

    def build(self, ctx: StepContext) -> InputDef | None:
        s = ctx.raw
        raw_in = s.get("input")
        if raw_in is None:
            return None

        if not isinstance(raw_in, dict):
            raise ctx.step_err("input must be a mapping.")

        title = raw_in.get("title") or ""
        if not isinstance(title, str):
            raise ctx.step_err("input.title must be a string.")

        raw_fields = raw_in.get("fields")
        if not isinstance(raw_fields, list) or not raw_fields:
            raise ctx.step_err("input.fields must be a non-empty list.")

        fields, field_vars = self._parse_fields(ctx, raw_fields)
        branches = self._parse_branches(ctx, raw_in.get("branches"), field_vars)

        return InputDef(title=title, fields=fields, branches=branches)

    def _parse_fields(
        self, ctx: StepContext, raw_fields: list[Any]
    ) -> tuple[list[InputFieldDef], list[str]]:
        fields: list[InputFieldDef] = []
        field_vars: list[str] = []

        for f in raw_fields:
            if not isinstance(f, dict):
                raise ctx.step_err("each input field must be a mapping.")

            var = f.get("var")
            if not var or not isinstance(var, str):
                raise ctx.step_err("each input field requires non-empty 'var'.")

            policy = f.get("policy", "system:string")
            if not isinstance(policy, str) or not policy:
                raise ctx.step_err(f"field '{var}': policy must be a non-empty string.")

            ftitle = f.get("title") or ""
            if not isinstance(ftitle, str):
                raise ctx.step_err(f"field '{var}': title must be a string.")

            required = f.get("required", True)
            if not isinstance(required, bool):
                raise ctx.step_err(f"field '{var}': required must be a boolean.")

            options = f.get("options") or []
            default = f.get("default")

            if options:
                self._validate_options(ctx, var, options, default)

            fields.append(
                InputFieldDef(
                    var=var,
                    policy=policy,
                    title=ftitle,
                    required=required,
                    options=options,
                    default=default,
                )
            )
            field_vars.append(var)

        return fields, field_vars

    def _validate_options(
        self, ctx: StepContext, var: str, options: Any, default: Any
    ) -> None:
        if not isinstance(options, list):
            raise ctx.step_err(f"field '{var}': options must be a list.")

        for opt in options:
            if not isinstance(opt, dict) or "label" not in opt or "value" not in opt:
                raise ctx.step_err(f"field '{var}': each option must have label/value.")

        values = [str(opt["value"]) for opt in options]
        if len(values) != len(set(values)):
            raise ctx.step_err(f"field '{var}': option values must be unique.")

        if default is not None and str(default) not in set(values):
            raise ctx.step_err(
                f"field '{var}': default '{default}' not in option values."
            )

    def _parse_branches(
        self, ctx: StepContext, raw_br: Any, field_vars: list[str]
    ) -> InputBranchesDef | None:
        if raw_br is None:
            return None

        if not isinstance(raw_br, dict):
            raise ctx.step_err("input.branches must be a mapping.")

        on = raw_br.get("on")
        if not on or not isinstance(on, str):
            raise ctx.step_err("input.branches.on must be a non-empty string.")

        if on not in set(field_vars):
            raise ctx.step_err(
                f"input.branches.on '{on}' must match one of input.fields.var."
            )

        cases = raw_br.get("cases")
        if not isinstance(cases, dict) or not cases:
            raise ctx.step_err("input.branches.cases must be a non-empty mapping.")

        norm_cases = {_normalize_case_key(k): v for k, v in cases.items()}
        return InputBranchesDef(on=on, cases=norm_cases)


class StepAssembler:
    """Builds a StepDef from raw dict and enforces 'exactly one action'."""

    def __init__(self) -> None:
        self._legacy = LegacyGuard()
        self._run = RunBuilder()
        self._switch = SwitchBuilder()
        self._input = InputBuilder()

    def build(self, command_key: str, sid: str, raw_step: dict[str, Any]) -> StepDef:
        ctx = StepContext(command_key=command_key, step_id=sid, raw=raw_step)

        self._legacy.validate(ctx)

        run_def = self._run.build(ctx)
        switch_def = self._switch.build(ctx)
        input_def = self._input.build(ctx)

        step = StepDef(
            id=sid,
            run=run_def,
            input=input_def,
            switch=switch_def,
            end=raw_step.get("end"),
            next=raw_step.get("next"),
        )

        actions = sum(
            [
                step.run is not None,
                step.input is not None,
                step.switch is not None,
                step.end is not None,
            ]
        )
        if actions != 1:
            raise ctx.err("define exactly one of [run, input, switch, end].")

        return step


class GraphValidator:
    def validate(self, command_key: str, steps: dict[str, StepDef], start: str) -> None:
        if start not in steps:
            raise ValueError(f"{command_key}: start step '{start}' not found.")

        step_ids = set(steps.keys())

        for step in steps.values():
            # next
            if step.next and step.next not in step_ids:
                raise ValueError(
                    f"{command_key}:{step.id}: next target '{step.next}' not found."
                )

            # input branches targets
            if step.input and step.input.branches:
                for _, target in step.input.branches.cases.items():
                    if target not in step_ids:
                        raise ValueError(
                            f"{command_key}:{step.id}: input branch target '{target}' not found."
                        )

            # switch targets
            if step.switch:
                for k, target in step.switch.cases.items():
                    if target not in step_ids:
                        raise ValueError(
                            f"{command_key}:{step.id}: switch case '{k}' target '{target}' not found."
                        )
                if step.switch.default and step.switch.default not in step_ids:
                    raise ValueError(
                        f"{command_key}:{step.id}: switch default target '{step.switch.default}' not found."
                    )
