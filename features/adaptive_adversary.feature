Feature: Adaptive Adversary Tests
  Validates that inference-layer defenses fail against adaptive Class C attacks.
  Confirms execution-layer monitoring is the only complete defense.

  Scenario: Naive Class C caught by structural analysis
    Given 3 operational grammars with descriptive symbols
    And 2 academic grammars
    When I run structural anomaly detection
    Then all 3 operational grammars are flagged
    And both academic grammars pass

  Scenario: Adaptive Class C evades structural analysis
    Given 3 operational grammars with opaque symbols and fake recursion
    And 2 academic grammars
    When I run structural anomaly detection
    Then 0 of 3 operational grammars are flagged
    And this confirms Proposition 5.8 empirically

  Scenario: Adaptive adversary evades combined defense
    Given 3 operational grammars obfuscated with opaque symbols
    When I run combined structural plus reinterpretation defense
    Then evasion rate is 100%
    And execution-layer monitoring is the only remaining defense
