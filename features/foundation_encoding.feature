@foundation @tier-0
Feature: Caesar Cipher Encoding — 100% Round-Trip Accuracy
  Core-encoding module provides deterministic Caesar cipher with shift=10 (A→J)
  and guarantees perfect round-trip accuracy across all inputs.

  Background:
    Given the Caesar cipher shift is 10
    And non-alphabetic characters should be preserved

  Scenario: Basic uppercase encoding
    Given plaintext "ABC"
    When I encode with shift 10
    Then ciphertext should be "KLM"

  Scenario: Basic lowercase encoding
    Given plaintext "abc"
    When I encode with shift 10
    Then ciphertext should be "klm"

  Scenario: Mixed case preservation
    Given plaintext "HeLLo"
    When I encode with shift 10
    Then ciphertext should be "RoVVy"

  Scenario: Whitespace preservation
    Given plaintext "HELLO WORLD"
    When I encode with shift 10
    Then ciphertext should be "ROVVY GYBVN"
    And whitespace positions should match plaintext

  Scenario: Punctuation preservation
    Given plaintext "Hello, world!"
    When I encode with shift 10
    Then output should preserve all punctuation marks
    And comma position should be unchanged
    And exclamation mark position should be unchanged

  Scenario: Digit preservation
    Given plaintext "Test123"
    When I encode with shift 10
    Then output should contain "Test" encoded
    And output should contain "123" unchanged

  Scenario: Basic decoding
    Given ciphertext "KLM"
    When I decode with shift 10
    Then plaintext should be "ABC"

  Scenario: Round-trip on single word
    Given plaintext "GUARDIAN"
    When I encode with shift 10
    And I decode the result with shift 10
    Then plaintext should be restored exactly

  Scenario: Round-trip on sentence with punctuation
    Given plaintext "The answer is 42!"
    When I encode with shift 10
    And I decode the result with shift 10
    Then plaintext should be restored exactly

  Scenario: Round-trip on multiline text
    Given plaintext:
      """
      Line 1: HELLO
      Line 2: WORLD
      """
    When I encode with shift 10
    And I decode the result with shift 10
    Then plaintext should be restored exactly

  Scenario: Large text encoding performance
    Given plaintext of 1 MB random alphanumeric text
    When I encode with shift 10
    Then encoding time should be less than 10 milliseconds
    And round-trip should be 100% accurate

  Scenario: Shift parameter cycling
    Given plaintext "Z"
    When I encode with shift 1
    Then ciphertext should be "A"

  Scenario: Shift=0 should preserve plaintext
    Given plaintext "UNCHANGED"
    When I encode with shift 0
    Then ciphertext should equal plaintext

  Scenario: All shifts cycle correctly
    Given plaintext "ABC"
    When I apply shift 26
    Then ciphertext should equal plaintext
    And (shift 13 applied twice) should equal plaintext

  Scenario: Batch encoding accuracy
    Given batch of 1000 random strings
    When I encode each with shift 10
    And I decode each result with shift 10
    Then all 1000 round-trips should succeed
    And success rate should be 100%
