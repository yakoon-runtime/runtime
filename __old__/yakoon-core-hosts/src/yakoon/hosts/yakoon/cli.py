import asyncio
from pathlib import Path

import typer
from y5n.apps.y5n.jobs.migrate import migrate_from_config
from y5n.apps.y5n.jobs.scaffold import scaffold_mesh_template

cli = typer.Typer()


@cli.command()
def testme(foo: str = typer.Option(...)):
    print(f"FOO is: {foo}")


@cli.command()
def migrate(config: str = typer.Option(..., help="Path to store config YAML")):
    """
    Run all registered domain migrations based on the given config.
    """
    asyncio.run(migrate_from_config(config))


@cli.command()
def scaffold(
    name: str = typer.Argument(..., help="Name of the new workspace project"),
    target: Path = typer.Option(Path.cwd(), help="Target directory"),  # noqa: B008
):
    """
    Scaffold a new mesh-based workspace with adjusted imports.
    """
    scaffold_mesh_template(name, target)
