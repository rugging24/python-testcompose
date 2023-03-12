from click import group
from testcompose.configs.template_cmd import generate


@group()
def config():
    pass


config.add_command(generate)
