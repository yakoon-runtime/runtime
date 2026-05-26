from y5n.runtime.scaffold.workspace import scaffold_workspace


def scaffold_mesh_template(name: str, target):
    """
    Scaffold a new mesh-based workspace with adjusted imports.
    """
    project_dir = target / name
    scaffold_workspace(name, project_dir)
    print(f"✅ Scaffolded new workspace: {project_dir}")
