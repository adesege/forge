Feature: Hello service
  As a user of forge
  I want to greet and farewell people
  So that I can verify the service layer works end-to-end

  Scenario: Greet with default name
    When I call the greet service
    Then the result should be "Hello, world!"

  Scenario: Greet with custom name
    When I call the greet service with name "Claude"
    Then the result should be "Hello, Claude!"

  Scenario: Farewell with custom name
    When I call the farewell service with name "Claude"
    Then the result should be "Goodbye, Claude!"

  Scenario: Greet via CLI
    When I run the CLI with "hello greet --name World"
    Then the CLI output should contain "Hello, World!"

  Scenario: Farewell via CLI
    When I run the CLI with "hello farewell --name World"
    Then the CLI output should contain "Goodbye, World!"
