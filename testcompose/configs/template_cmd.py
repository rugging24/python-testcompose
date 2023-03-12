from typing import List
from click import command, option
from pathlib import Path


@command()
@option("--template-file", default="bootstrap.yaml", show_default=True, help="Template file location")
@option(
    "--components",
    multiple=True,
    help="Components for which config is to be generated [app, broker, db]",
)
def generate(template_file: str, components: List[str]):
    if Path(template_file).absolute().exists():
        raise FileExistsError(f"Config file {template_file} exists!")

    if not Path(Path(template_file).absolute().stem).absolute().exists():
        raise FileNotFoundError(
            f"Invalid config location directory provided {Path(template_file).absolute().stem}"
        )

    _components = [str(x).lower() for x in components]
    if list(set(_components) ^ set(['app', 'db', 'broker'])):
        raise AttributeError("Allowed component values are [app, broker, db]")
