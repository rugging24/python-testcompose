from click.testing import CliRunner
from testcompose.testcompose import config
import yaml


def test_generate_template():
    runner = CliRunner()
    result = runner.invoke(
        config,
        [
            'generate-template',
            '--components',
            'app',
            '--components',
            'db',
            '--components',
            'broker',
        ],
    )
    output = result.output
    assert isinstance(yaml.safe_load(output), dict)
