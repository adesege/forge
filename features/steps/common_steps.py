"""Common step definitions shared across features."""

from behave import then, when
from click.testing import CliRunner

from forge.cli import main


@when('I run the CLI with "{args}"')
def step_run_cli(context, args):
    runner = CliRunner()
    result = runner.invoke(main, args.split())
    context.cli_result = result


@then('the CLI output should contain "{text}"')
def step_cli_output_contains(context, text):
    assert text in context.cli_result.output, \
        f"Expected '{text}' in output: {context.cli_result.output}"
