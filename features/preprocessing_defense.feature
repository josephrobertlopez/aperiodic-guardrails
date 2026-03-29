Feature: Preprocessing Pipeline Defense
  Validates invertibility-based defenses for Class A and B attacks.

  Scenario: ZWSP stripping recovers regex detection
    Given 20 payloads encoded with zero-width spaces
    And regex detection before stripping is 0%
    When I apply ZWSP stripping then regex
    Then detection rate exceeds 90%

  Scenario: Base64 decode recovers regex detection
    Given 20 payloads encoded with base64
    And regex detection before decoding is 0%
    When I try base64 decode then regex
    Then detection rate exceeds 90%

  Scenario: ROT13 decode recovers regex detection
    Given 20 payloads encoded with ROT13
    And regex detection before decoding is 0%
    When I try ROT13 decode then regex
    Then detection rate exceeds 90%

  Scenario: Confusable normalization recovers regex detection
    Given 20 payloads encoded with Cyrillic homoglyphs
    When I normalize confusables then regex
    Then detection rate exceeds 80%

  Scenario: Leetspeak reversal recovers regex detection
    Given 20 payloads encoded with leetspeak
    When I reverse leetspeak then regex
    Then detection rate exceeds 80%

  Scenario: Full pipeline composes all preprocessing
    Given 20 payloads encoded with various schemes
    When I run the full preprocessing pipeline then regex
    Then each encoding type has detection rate exceeding 80%
