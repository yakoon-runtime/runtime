from yakoon.base.capabilities.workflow import WorkflowService
from yakoon.base.commands import (
    Command,
    CommandKind,
    CommandScope,
    CommandVisibility,
    Request,
)


class CmdWfInput(Command):

    key = "wf.input"

    kind = CommandKind.WORKFLOW
    scope = CommandScope.GLOBAL
    visibility = CommandVisibility.INTERNAL
    requires_workflow = True

    async def run(self, request: Request) -> None:  # noqa: ARG002
        batch_id = request.arg(0)
        step_id = request.arg(1)

        wfsvc = self.container.get(WorkflowService)

        step = wfsvc.get_step(session, batch_id=batch_id, step_id=step_id)
        s = step.input
        if not s:
            raise RuntimeError(f"{batch_id}:{step_id}: step has no input")

        # Build View for the host (fields keyed by var)
        fields: dict[str, dict] = {}
        order: list[str] = []

        for f in s.fields:
            var = f.var
            order.append(var)

            fd = {
                "var": var,  # required everywhere now
                "policy": f.policy or "system:string",
                "title": f.title or var,
                "required": bool(f.required),
            }
            if f.default is not None:
                fd["default"] = f.default
            if f.options:
                fd["options"] = f.options

            # Modell A: UI hints derived from policy
            fd["ui"] = _ui_from_policy(fd["policy"])

            fields[var] = fd

        view = {
            "kind": "view",
            "mode": "replace",
            "id": f"{batch_id}:{step_id}",
            "input": {
                "kind": "form",
                "form_id": f"{batch_id}.{step_id}",
                "title": s.title or None,
                "fields": fields,
                "meta": {
                    "order": order,
                    "aliases": {},  # workflow uses var directly; keep empty for consistency
                    "batch_id": batch_id,
                    "step_key": step_id,
                },
            },
        }

        result = await inputs.ask_view(session, view)

        # if ask_view already returns PromptResult: values = result.dict()
        values = result.dict() if hasattr(result, "dict") else result

        wfsvc.complete_input_step(
            session,
            batch_id=batch_id,
            step_id=step_id,
            values=values,
        )


def _ui_from_policy(policy_key: str) -> dict:
    # Minimal start: keep host dumb (ui only), policy remains truth
    if policy_key.endswith(":masked") or policy_key in {"system:masked"}:
        return {"secret": True}
    return {}
