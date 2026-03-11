Feature: Shell completion
  As a user of forge
  I want to generate shell completion scripts
  So that I get tab-completion in my terminal

  Scenario: Generate bash completion script
    When I run the CLI with "completion bash"
    Then the CLI output should contain "_forge_completion()"
    And the CLI output should contain "_FORGE_COMPLETE=bash_complete"

  Scenario: Generate zsh completion script
    When I run the CLI with "completion zsh"
    Then the CLI output should contain "_forge_completion()"
    And the CLI output should contain "compdef"

  Scenario: Generate fish completion script
    When I run the CLI with "completion fish"
    Then the CLI output should contain "_forge_completion"
    And the CLI output should contain "_FORGE_COMPLETE=fish_complete"
