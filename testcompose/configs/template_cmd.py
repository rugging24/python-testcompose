from typing import Any, Dict, List, Optional
from click import command, option, echo
from pathlib import Path
import yaml
from testcompose.configs.generate_template_config import GenerateConfigTemplate


@command(name='generate-template')
@option(
    "--template-file",
    default="",
    show_default=True,
    help="Optional template file location otherwise stdout is used",
)
@option(
    "--components",
    multiple=True,
    help="Components for which config is to be generated [app, broker, db]",
)
def generate_template(template_file: str, components: List[str]):
    _components = [str(x).lower() for x in components]
    if not (set(_components) & set(['app', 'db', 'broker'])):
        raise AttributeError(
            f"Allowed component values are [app, broker, db], but {_components} was provided"
        )
    _components.sort()
    _filename: Optional[Path] = None
    if template_file:
        _filename = Path(template_file).absolute()
        if _filename.exists() or not _filename.parent.exists():
            raise FileExistsError(
                f"Config file {template_file} must not already exists or directory must exist"
            )

    _template_module = f"{'_'.join(_components)}_template"
    generated_template: Dict[str, Any] = getattr(GenerateConfigTemplate(), _template_module)()

    if _filename:
        with open(template_file, 'w') as fh:
            yaml.safe_dump(generated_template, fh, indent=3, sort_keys=False)
        echo(f"Config file {template_file} successfully written")
    else:
        echo(yaml.safe_dump(generated_template, indent=3, sort_keys=False))
