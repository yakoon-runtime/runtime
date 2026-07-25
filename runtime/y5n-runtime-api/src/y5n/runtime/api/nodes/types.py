from enum import StrEnum


class NodeKind(StrEnum):
    """Classifies node execution semantics.

    USER — normal user-facing commands.
    BUILTIN — shell/core orchestration (use, man, wf.*).
    WORKFLOW — workflow entrypoints.
    """

    USER = "user"
    BUILTIN = "builtin"
    WORKFLOW = "workflow"


class NodeVisibility(StrEnum):
    """Controls listing visibility in man/help.

    NORMAL — standard in man.
    DEVELOPER — only in man --all / man workflows.
    INTERNAL — only in man --internal.
    """

    NORMAL = "normal"
    DEVELOPER = "dev"
    INTERNAL = "internal"
