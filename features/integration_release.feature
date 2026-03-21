@integration
Feature: Release management with real Forgejo
  As a user of forge
  I want to manage releases on a real Forgejo instance
  So that I can create, view, edit, and delete releases

  Background:
    Given a running Forgejo instance
    And a repository named "test-releases" exists

  Scenario: Create and view a release
    When I create a release with tag "v1.0.0" and title "First Release" in "test-releases"
    Then the Forgejo API should show the release "v1.0.0" exists in "test-releases"
    And the release should have title "First Release"

  Scenario: Edit a release
    Given a release with tag "v2.0.0" exists in "test-releases"
    When I edit the release "v2.0.0" title to "Updated Release" in "test-releases"
    Then the Forgejo API should show the release "v2.0.0" has title "Updated Release" in "test-releases"

  Scenario: Delete a release
    Given a release with tag "v3.0.0" exists in "test-releases"
    When I delete the release "v3.0.0" in "test-releases"
    Then the Forgejo API should show the release "v3.0.0" does not exist in "test-releases"
