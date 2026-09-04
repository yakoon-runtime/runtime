"""Form elements mode — ordered mixture of YDS presentation blocks and
interactive Field elements.

Slice 1 of the Option-B evolution: the Form core projects an ordered
element list (presentation blocks break Field groups) while the
``fields=``/``title``/``intro`` compatibility mode projects byte-identical
to the previous single-fields-node shape.
"""

from y5n.runtime.api.flow.patterns.public import FormAction
from y5n.runtime.api.flow.patterns.public.form import Form
from y5n.runtime.api.flow.primitives import EmitView
from y5n.runtime.api.runtime import Event
from y5n.runtime.api.runtime.invocation import Param

# ----------------------------------------
# presentation stubs (wire-shaped dicts)
# ----------------------------------------


class Heading:
    type = "heading"

    def __init__(self, text: str):
        self.text = text

    def to_dict(self) -> dict:
        return {"type": "heading", "text": self.text}


class Rule:
    type = "rule"

    def to_dict(self) -> dict:
        return {"type": "rule"}


class Text:
    type = "text"

    def __init__(self, text: str):
        self.text = text

    def to_dict(self) -> dict:
        return {"type": "text", "text": self.text}


class FieldStub:
    """A non-Param interactive element (sdk Field is duck-compatible)."""

    def __init__(self, key: str, title: str | None = None, secret: bool = False):
        self.key = key
        self.title = title
        self.policy = None
        self.required = False
        self.secret = secret


class Required:
    def __init__(self, key: str, title: str | None = None):
        self.key = key
        self.title = title
        self.policy = None
        self.required = True
        self.secret = False


# ----------------------------------------
# driving helpers
# ----------------------------------------


def _views(pulses: list) -> list[dict]:
    return [
        effect.view
        for pulse in pulses
        for effect in pulse.effects
        if isinstance(effect, EmitView)
    ]


def _drive(form: Form, inputs: list) -> tuple[list, dict]:
    """Drive pulse_flow like the engine: raw input events on the
    USER_INPUT channel, None elsewhere. Returns (pulses, values)."""
    gen = form.pulse_flow()
    pulses: list = []
    try:
        pulse = gen.send(None)
        while True:
            pulses.append(pulse)
            control = getattr(pulse, "control", None)
            if control is not None and getattr(control, "channel", None) == "__user__":
                pulse = gen.send(Event(payload=inputs.pop(0)))
            else:
                pulse = gen.send(None)
    except StopIteration as stop:
        return pulses, stop.value


def _field_entries(view: dict) -> list[dict]:
    """All field entries of a view's fields nodes, in order."""
    entries = []
    for block in view["blocks"]:
        if block["type"] == "fields":
            entries.extend(block["fields"])
    return entries


def _block_types(view: dict) -> list[str]:
    return [block["type"] for block in view["blocks"]]


# ----------------------------------------
# compatibility mode: byte-identical projection
# ----------------------------------------


def test_fields_mode_projection_is_unchanged():
    form = Form(fields=[Param(key="user")], title="SIGN IN", intro="hello")
    gen = form.pulse_flow()
    pulse = gen.send(None)

    assert pulse.effects[1].view == {
        "kind": "document",
        "header": {"role": "info", "title": "SIGN IN"},
        "blocks": [
            {
                "type": "section",
                "blocks": [
                    {
                        "type": "fields",
                        "name": "SIGN IN",
                        "fields": [
                            {
                                "type": "field",
                                "policy": "string",
                                "title": "User",
                                "required": False,
                                "name": "user",
                                "value": None,
                                "state": "active",
                            }
                        ],
                        "intro": "hello",
                        "state": "active",
                    }
                ],
            }
        ],
    }


def test_empty_form_still_returns_empty_values():
    _pulses, values = _drive(Form(), inputs=[])
    assert values == {}


def test_empty_elements_form_returns_empty_values():
    _pulses, values = _drive(Form(elements=[]), inputs=[])
    assert values == {}


def test_fields_and_elements_are_mutually_exclusive():
    import pytest

    with pytest.raises(ValueError):
        Form(fields=[Param(key="a")], elements=[Rule()])


def test_title_and_intro_are_fields_mode_only():
    import pytest

    with pytest.raises(ValueError):
        Form(elements=[Rule()], title="T")
    with pytest.raises(ValueError):
        Form(elements=[Rule()], intro="I")


def test_fields_block_element_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        Form(elements=[{"type": "fields", "fields": []}])


def test_unsupported_element_is_rejected():
    import pytest

    with pytest.raises(ValueError):
        Form(elements=[42])


def test_presentation_dict_requires_type():
    import pytest

    with pytest.raises(ValueError):
        Form(elements=[{"text": "no type"}])


# ----------------------------------------
# elements mode: grouping and projection
# ----------------------------------------


def _sign_in_form(**kwargs) -> Form:
    return Form(
        elements=[
            Heading("SIGN IN"),
            Rule(),
            FieldStub("user", title="Username"),
            FieldStub("password", title="Password", secret=True),
            Text("note"),
            FieldStub("otp", title="OTP"),
            Rule(),
        ],
        **kwargs,
    )


def test_elements_group_adjacent_fields_and_preserve_trailers():
    form = _sign_in_form()
    gen = form.pulse_flow()
    pulse = gen.send(None)
    view = pulse.effects[1].view

    assert _block_types(view) == ["heading", "rule", "fields", "text", "fields", "rule"]
    assert view["blocks"][0] == {"type": "heading", "text": "SIGN IN"}
    assert view["blocks"][1] == {"type": "rule"}

    first_group = view["blocks"][2]["fields"]
    assert [f["name"] for f in first_group] == ["user", "password"]
    assert first_group[0]["state"] == "active"
    assert first_group[0].get("secret") is not True  # ordinary username
    assert first_group[1]["state"] == "idle"
    assert first_group[1]["secret"] is True  # masked password

    assert view["blocks"][3] == {"type": "text", "text": "note"}
    assert [f["name"] for f in view["blocks"][4]["fields"]] == ["otp"]

    assert view["header"] == {"role": "info", "title": ""}


def test_elements_state_progression_and_values():
    form = _sign_in_form()
    pulses, values = _drive(form, inputs=["stefan", "pw123", "0000"])

    views = _views(pulses)
    # per field: prompt, receive, re-render — plus the next field's prompt
    assert len(views) == 6

    initial = _field_entries(views[0])
    assert [f["state"] for f in initial] == ["active", "idle", "idle"]

    after_user = _field_entries(views[1])
    assert [f["state"] for f in after_user] == ["done", "idle", "idle"]
    assert after_user[0]["value"] == "stefan"

    password_prompt = _field_entries(views[2])
    assert [f["state"] for f in password_prompt] == ["done", "active", "idle"]

    after_password = _field_entries(views[3])
    assert [f["state"] for f in after_password] == ["done", "done", "idle"]
    assert after_password[1]["value"] == "pw123"

    otp_prompt = _field_entries(views[4])
    assert [f["state"] for f in otp_prompt] == ["done", "done", "active"]

    final = _field_entries(views[5])
    assert [f["state"] for f in final] == ["done", "done", "done"]

    assert values == {"user": "stefan", "password": "pw123", "otp": "0000"}


def test_elements_mode_works_with_initial_and_focus():
    form = Form(
        elements=[FieldStub("user"), FieldStub("password", secret=True)],
        initial={"user": "stefan"},
        focus="password",
    )
    gen = form.pulse_flow()
    pulse = gen.send(None)

    entries = _field_entries(pulse.effects[1].view)
    assert [f["state"] for f in entries] == ["done", "active"]
    assert entries[0]["value"] == "stefan"


def test_elements_mode_navigation_skips_presentation_elements():
    form = _sign_in_form()
    pulses, values = _drive(form, inputs=[FormAction("next"), "pw123", "0000"])

    views = _views(pulses)
    # FormAction("next") moves the cursor straight to the password prompt
    # (no re-render in between); the user field was never acquired and
    # stays idle in every subsequent render
    assert len(views) == 5
    password_prompt = _field_entries(views[1])
    assert [f["state"] for f in password_prompt] == ["idle", "active", "idle"]
    assert values == {"password": "pw123", "otp": "0000"}


def test_elements_mode_required_field_reprompts():
    form = Form(elements=[Required("user"), Text("hint")])
    pulses, values = _drive(form, inputs=["", "stefan"])

    views = _views(pulses)
    # empty input on a required field re-prompts the same field
    assert len(_views(pulses)) >= 3
    assert _field_entries(views[0])[0]["state"] == "active"
    assert _field_entries(views[-1])[0]["state"] == "done"
    assert values == {"user": "stefan"}


def test_elements_mode_ask_registers_field_for_rendering():
    form = Form(elements=[Heading("DIALOG")])

    # ask() registers the field on the fly (async generator; the engine
    # drives it) — here we assert the registration/rendering contract
    form.ask("user", "Username")
    view = form._render("user")

    assert _block_types(view) == ["heading", "fields"]
    entries = _field_entries(view)
    assert entries[0]["name"] == "user"
    assert entries[0]["state"] == "active"


# ----------------------------------------
# required-field navigation invariant
# ----------------------------------------


def test_navigation_past_empty_required_field_returns_to_it():
    """Regression: navigating to a later required field and submitting it
    must NOT complete the form while an earlier required field is empty —
    the dialog returns to the first missing required field."""

    form = Form(elements=[Required("a"), Text("separator"), Required("b")])
    pulses, values = _drive(
        form, inputs=[FormAction("next"), "b-value", "a-value", "b-value"]
    )

    views = _views(pulses)
    # the form re-prompts "a" while "b" is already done — no completion
    returned = [
        view
        for view in views
        if [(f["name"], f["state"]) for f in _field_entries(view)]
        == [("a", "active"), ("b", "done")]
    ]
    assert returned, "form must return to the first missing required field"

    # only after both required fields are filled does the form complete
    assert values == {"a": "a-value", "b": "b-value"}


def test_both_required_fields_filled_sequentially_completes_normally():
    form = Form(elements=[Required("a"), Required("b")])
    _pulses, values = _drive(form, inputs=["a-value", "b-value"])

    assert values == {"a": "a-value", "b": "b-value"}


def test_navigation_return_then_completion():
    """navigate to B → fill B → return to A → fill A → completes."""
    form = Form(elements=[Required("a"), Required("b")])
    _pulses, values = _drive(
        form, inputs=[FormAction("next"), "b-value", "a-value", ""]
    )

    # the empty re-submit falls back to the stored value ("b-value")
    assert values == {"a": "a-value", "b": "b-value"}
