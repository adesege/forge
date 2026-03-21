@integration
Feature: Issue management with real Forgejo
  As a user of forge
  I want to manage issues on a real Forgejo instance
  So that I can create, view, close, and comment on issues

  Background:
    Given a running Forgejo instance
    And a repository named "test-issues" exists

  Scenario: Create and view an issue
    When I create an issue titled "Bug report" with body "Something is broken" in "test-issues"
    Then the Forgejo API should show the issue "Bug report" exists in "test-issues"
    And the issue should have body "Something is broken"

  Scenario: Close and reopen an issue
    Given an issue titled "To be closed" exists in "test-issues"
    When I close the issue in "test-issues"
    Then the Forgejo API should show the issue is "closed" in "test-issues"
    When I reopen the issue in "test-issues"
    Then the Forgejo API should show the issue is "open" in "test-issues"

  Scenario: Comment on an issue
    Given an issue titled "Needs comment" exists in "test-issues"
    When I add a comment "Working on this" to the issue in "test-issues"
    Then the Forgejo API should show the comment "Working on this" on the issue in "test-issues"

  Scenario: Edit an issue
    Given an issue titled "Original title" exists in "test-issues"
    When I edit the issue title to "Updated title" in "test-issues"
    Then the Forgejo API should show the issue "Updated title" exists in "test-issues"
