from yakoon.base.runtime.sessions.flow import Flow, FlowKind
from yakoon.base.runtime.sessions.session import Session


def acquire_focus(session: Session, flow: Flow):
    if flow.kind != FlowKind.USER:
        return
    session.set_focus(flow.id)


def release_focus(session: Session, flow: Flow):
    if session.focused_flow == flow:
        session.set_focus(None)
