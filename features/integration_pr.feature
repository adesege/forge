@integration
Feature: Pull request management with real Forgejo
  As a user of forge
  I want to manage pull requests on a real Forgejo instance
  So that I can create, view, and merge PRs

  Background:
    Given a running Forgejo instance
    And a repository named "test-prs" exists with a file

  Scenario: Create and view a pull request
    Given a branch "feature-branch" exists in "test-prs" with a commit
    When I create a pull request titled "Add feature" from "feature-branch" to "main" in "test-prs"
    Then the Forgejo API should show the pull request "Add feature" exists in "test-prs"

  Scenario: Create and merge a pull request
    Given a branch "merge-branch" exists in "test-prs" with a commit
    And a pull request titled "Merge me" exists from "merge-branch" to "main" in "test-prs"
    When I merge the pull request in "test-prs"
    Then the Forgejo API should show the pull request is merged in "test-prs"

  Scenario: Close a pull request
    Given a branch "close-branch" exists in "test-prs" with a commit
    And a pull request titled "Close me" exists from "close-branch" to "main" in "test-prs"
    When I close the pull request in "test-prs"
    Then the Forgejo API should show the pull request is "closed" in "test-prs"
