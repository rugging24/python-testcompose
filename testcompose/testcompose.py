from click import group
from testcompose.configs.template_cmd import generate_template


@group()
def config():
    pass


config.add_command(generate_template)
