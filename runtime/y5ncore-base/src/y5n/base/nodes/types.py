from enum import StrEnum


class NodeKind(StrEnum):
    USER = "user"  # normale, user-facing Commands
    BUILTIN = "builtin"  # shell/core orchestration (use, man, wf.*)
    WORKFLOW = "workflow"  # workflow entrypoints / workflow-only commands


class NodeVisibility(StrEnum):
    NORMAL = "normal"  # standard in `man`
    DEVELOPER = "dev"  # nur in `man --all` / `man workflows`
    INTERNAL = "internal"  # nur in `man --internal`


class NodeScope(StrEnum):
    NODE = "node"  # Only in active node
    ROOT = "root"  # In owner applcication and in root node
    GLOBAL = "global"  # global usage
