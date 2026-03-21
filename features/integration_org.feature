@integration
Feature: Organization management with real Forgejo
  As a user of forge
  I want to manage organizations on a real Forgejo instance
  So that I can create, view, and list organizations

  Background:
    Given a running Forgejo instance

  Scenario: List organizations
    Given an organization named "test-org" exists
    When I list organizations via the API
    Then the organization list should contain "test-org"

  Scenario: View organization details
    Given an organization named "view-org" exists with description "Test organization"
    When I view organization "view-org" via the API
    Then the organization details should show name "view-org"
