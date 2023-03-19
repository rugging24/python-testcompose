from typing import Any, Dict, List, Optional
from click import command, option, echo
from pathlib import Path
import click
import yaml
from testcompose.configs.generate_template_config import GenerateConfigTemplate
import sys


@command(name='generate-template')
@option(
    "--template-file",
    default="",
    show_default=True,
    help="Optional template file location otherwise stdout is used",
)
@option(
    "--component",
    multiple=True,
    help="Components for which config is to be generated [app, broker, db].\
            This argument can be provided multiple times",
)
def generate_template(template_file: str, component: List[str]):
    _components = [str(x).lower() for x in component]
    if not (set(_components) & set(['app', 'db', 'broker'])):
        _missing_attr_error_reporting()
    _components.sort()
    _filename: Optional[Path] = None
    if template_file:
        _filename = Path(template_file).absolute()
        if _filename.exists() or not _filename.parent.exists():
            click.echo(f"Config file {template_file} must not already exists or directory must exist")
            click.echo()
            sys.exit(0)

    _template_module = f"{'_'.join(_components)}_template"
    if not hasattr(GenerateConfigTemplate(), _template_module):
        _missing_attr_error_reporting()
    generated_template: Dict[str, Any] = getattr(GenerateConfigTemplate(), _template_module)()

    if _filename:
        with open(template_file, 'w') as fh:
            yaml.safe_dump(generated_template, fh, indent=3, sort_keys=False)
        echo(f"Config file {template_file} successfully written")
    else:
        echo(yaml.safe_dump(generated_template, indent=3, sort_keys=False))


def _missing_attr_error_reporting():
    click.echo()
    click.echo("Allowed component values are [app, broker, db]")
    click.echo()
    click.echo("Run testcompose generate-template --help for more info")
    sys.exit(0)
