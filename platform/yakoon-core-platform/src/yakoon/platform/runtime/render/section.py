class RenderSection:
    """
    Identifies a specific output block within a command template.

    The `key` selects the relevant section in the template (e.g. "success", "error"),
    while `data` provides optional values to be injected into that block.

    This allows command templates to render different outcomes
    (e.g. success/failure/info) from a shared file, depending on context.

    Attributes:
        key (str): Name of the section to render inside the template.
        data (dict): Optional context values available to the template.
    """

    def __init__(self, key, data=None):
        self.key = key
        self.data = data or {}
