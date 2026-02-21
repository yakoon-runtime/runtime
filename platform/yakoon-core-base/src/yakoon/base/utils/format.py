from yakoon.base.runtime.session.session import Session


def format_ps1(
    session: Session, default_name="shell", active_controller="shell"
) -> str:
    """
    Formats the interactive prompt based on session state.

    Examples:
      - shell$
      - stefan@shell$
      - stefan@auth$
    """
    if not session:
        return default_name

    user = session.get_username()
    controller = session.get_active_controller(active_controller)

    if user:
        return f"{user}@{controller}$ "
    return f"{controller}$ "
