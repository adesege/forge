Feature: Repo clone
  As a user of forge
  I want to clone a repository by name
  So that I can quickly get a local copy of a remote repo

  Scenario: Clone a named repository via CLI
    Given a mock Forgejo repo "alice/myrepo" with clone URL "https://git.example.com/alice/myrepo.git"
    When I run the CLI with "repo clone --name myrepo --owner alice"
    Then the CLI output should contain "Cloned alice/myrepo"

  Scenario: Clone with no repos shows message
    Given an empty Forgejo repo list
    When I run the CLI with "repo clone --owner empty-org"
    Then the CLI output should contain "No repositories found"
