@integration
Feature: Repository management with real Forgejo
  As a user of forge
  I want to manage repositories on a real Forgejo instance
  So that I can create, view, search, and delete repos

  Scenario: Create and view a repository
    Given a running Forgejo instance
    When I create a repository named "test-repo-create" with description "Integration test repo"
    Then the Forgejo API should show repository "test-repo-create" exists
    And the repository "test-repo-create" should have description "Integration test repo"

  Scenario: Create and delete a repository
    Given a running Forgejo instance
    When I create a repository named "test-repo-delete"
    And I delete the repository "test-repo-delete"
    Then the Forgejo API should show repository "test-repo-delete" does not exist

  Scenario: List repositories
    Given a running Forgejo instance
    And a repository named "test-repo-list" exists
    When I list repositories for the admin user
    Then the repository list should contain "test-repo-list"

  Scenario: Search repositories
    Given a running Forgejo instance
    And a repository named "searchable-project" exists
    When I search for repositories with query "searchable"
    Then the search results should contain "searchable-project"
