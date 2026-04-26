from typing import Any


class Request:
    """Parse and query a single command-line style input.

    Tokenization is expected to be done before (e.g. via InputEvent).

    Conventions:
        - Command is provided separately.
        - Tokens represent all arguments.
        - Options follow `--name value`.
        - Flags are options without a value.
        - Positional arguments exclude option keys and option values.

    This class intentionally represents exactly one command.
    """

    def __init__(self, command: str, tokens: list[str], payload) -> None:
        """Create a Request from normalized input.

        Args:
            command: The command name (already extracted).
            tokens: Tokenized arguments (order preserved).

        Notes:
            Tokens must already be split (e.g. via shlex).
        """
        self._command: str = command
        self._args: list[str] = tokens or []
        self.payload = payload

    @property
    def command(self) -> str:
        """The command name (first token), lowercased."""
        return self._command

    def args(self) -> list[str]:
        """All argument tokens (everything after the command token)."""
        return self._args

    def token(self, index: int, default: Any = None) -> Any:
        """Return the Nth argument token (0-based) or a default.

        Args:
            index: Index into `args` (0-based).
            default: Returned if the index is out of bounds.

        Returns:
            The token string or `default`.
        """
        try:
            return self._args[index]
        except IndexError:
            return default

    def arg(self, index: int, default: Any = None) -> Any:
        """Return the Nth positional argument (0-based) or a default.

        Positional arguments exclude:
            - option keys: `--name`
            - option values: the value following an option key (if any)

        Args:
            index: Index into the positional arguments (0-based).
            default: Returned if the index is out of bounds.

        Returns:
            The positional argument string or `default`.
        """
        pos = self._pos_args()
        try:
            return pos[index]
        except IndexError:
            return default

    def has_args(self) -> bool:
        """Whether there are any argument tokens."""
        return bool(self._args)

    def arg_count(self) -> int:
        """Number of argument tokens."""
        return len(self._args)

    def has_option(self, name: str) -> bool:
        """Check whether an option key `--name` is present (flag or key-value)."""
        return f"--{name}" in self._args

    def option(self, name: str, default: Any = None) -> Any:
        """Return the value for an option of the form `--name value`.

        Args:
            name: Option name without leading dashes.
            default: Returned if the option is missing or has no value.

        Returns:
            The option value token, or `default`.

        Examples:
            Input:  "cmd --user alice --dry-run"
            option("user") -> "alice"
            has_option("dry-run") -> True
            option("dry-run") -> default (no value by design)
        """
        key = f"--{name}"
        try:
            idx = self._args.index(key)
        except ValueError:
            return default

        # Missing value or followed by another option -> treat as no-value (flag)
        if idx + 1 >= len(self._args):
            return default

        value = self._args[idx + 1]
        if value.startswith("--"):
            return default

        return value

    def _pos_args(self) -> list[str]:
        """Compute positional arguments by skipping options and option values.

        Rules:
            - Any token starting with `--` is an option key.
            - If the following token exists and does not start with `--`,
              it is treated as the option's value and skipped as well.

        Returns:
            A list of positional argument tokens.
        """
        out: list[str] = []
        i = 0
        while i < len(self._args):
            tok = self._args[i]

            if tok.startswith("--"):
                i += 1
                if i < len(self._args) and not self._args[i].startswith("--"):
                    i += 1
                continue

            out.append(tok)
            i += 1

        return out
