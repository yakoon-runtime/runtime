"""CLI entry point for the YDS code generator.

Usage:
    python -m y5n.sdk.gen --input spec/yds/yds-v1.yaml --output models.py
    python -m y5n.sdk.gen --input spec/yds/yds-v1.yaml --output models.py \\
        --language python
"""

from __future__ import annotations

import argparse
import sys

from .emit.python import emit as emit_python
from .parser import parse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SDK model classes from yds-v1.yaml"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to yds-v1.yaml",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write generated output",
    )
    parser.add_argument(
        "--language",
        default="python",
        choices=["python"],
        help="Target language (default: python)",
    )
    args = parser.parse_args()

    schema = parse(args.input)

    if args.language == "python":
        source = emit_python(schema)
    else:
        print(f"Unsupported language: {args.language}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w") as f:
        f.write(source)

    print(f"Generated {args.output}")


if __name__ == "__main__":
    main()
