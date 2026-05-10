from enum import StrEnum


class CommandKind(StrEnum):
    USER = "user"  # normale, user-facing Commands
    BUILTIN = "builtin"  # shell/core orchestration (use, man, wf.*)
    WORKFLOW = "workflow"  # workflow entrypoints / workflow-only commands


class CommandVisibility(StrEnum):
    NORMAL = "normal"  # standard in `man`
    DEVELOPER = "dev"  # nur in `man --all` / `man workflows`
    INTERNAL = "internal"  # nur in `man --internal`


class CommandScope(StrEnum):
    APP = "app"  # Only in active application
    SHELL = "shell"  # In owner applcication and in shell application
    GLOBAL = "global"  # global usage
