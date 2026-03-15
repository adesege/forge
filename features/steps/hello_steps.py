"""Step definitions for the hello feature."""

from behave import then, when
from click.testing import CliRunner
from click_clop.service import ServiceRegistry

from forge.cli import main

# Import to trigger registration
from forge.services import hello  # noqa: F401


@when('I call the greet service')
def step_call_greet(context):
    svc = ServiceRegistry.get().get_service("hello")
    greet = next(m for m in svc.methods() if m.name == "greet")
    context.result = greet.func()


@when('I call the greet service with name "{name}"')
def step_call_greet_with_name(context, name):
    svc = ServiceRegistry.get().get_service("hello")
    greet = next(m for m in svc.methods() if m.name == "greet")
    context.result = greet.func(name=name)


@when('I call the farewell service with name "{name}"')
def step_call_farewell_with_name(context, name):
    svc = ServiceRegistry.get().get_service("hello")
    farewell = next(m for m in svc.methods() if m.name == "farewell")
    context.result = farewell.func(name=name)


@then('the result should be "{expected}"')
def step_result_should_be(context, expected):
    assert context.result == expected, f"Expected '{expected}', got '{context.result}'"


@when('I run the CLI with "{args}"')
def step_run_cli(context, args):
    runner = CliRunner()
    result = runner.invoke(main, args.split())
    context.cli_result = result


@then('the CLI output should contain "{text}"')
def step_cli_output_contains(context, text):
    assert text in context.cli_result.output, \
        f"Expected '{text}' in output: {context.cli_result.output}"
