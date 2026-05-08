@foundation @tier-0
Feature: CFG Grammar Generator — Parametric (k,b,|M|) Generation and Parsing
  CFG-grammar-generator module produces valid context-free grammars with
  deterministic parametric generation and CYK parsing for membership testing.

  Scenario: Basic grammar generation with parameters
    Given parameters k=3, b=2, M_size=5
    When I generate grammar with seed=42
    Then grammar should have start symbol "A"
    And grammar should have nonterminals [A, B, C, ...]
    And grammar should have terminals [T0, T1, T2, T3, T4]
    And grammar should have production rules

  Scenario: Reproducibility with fixed seed
    Given parameters k=3, b=2, M_size=5
    When I generate grammar with seed=42
    And I generate the same grammar again with seed=42
    Then grammars should be identical
    And rules should match exactly
    And terminals should match exactly

  Scenario: Different seeds produce different grammars
    Given parameters k=3, b=2, M_size=5
    When I generate grammar with seed=42
    And I generate grammar with seed=123
    Then grammars should differ
    But both should be valid CFGs

  Scenario: Parameter space validation
    When I generate grammars with:
      | k | b | M_size |
      | 1 | 2 | 5      |
      | 5 | 3 | 10     |
      | 10| 5 | 20     |
      | 20| 10| 50     |
    Then all grammars should be valid
    And rule count should increase with k and b

  Scenario: CYK parsing of valid strings
    Given grammar with seed=42, k=3, b=2, M_size=5
    When I sample 10 strings from the grammar
    And I parse each string using CYK
    Then all 10 strings should parse successfully
    And parse should return True for each

  Scenario: CYK parsing of invalid strings
    Given grammar with seed=42, k=3, b=2, M_size=5
    When I generate 100 random strings not from grammar
    And I parse each using CYK
    Then at least 90 strings should fail parsing
    And failure rate should be > 90%

  Scenario: String sampling from grammar
    Given grammar with seed=42, k=3, b=2, M_size=5
    When I sample 5 strings from grammar
    And I parse each sampled string using CYK
    Then all 5 strings should parse successfully

  Scenario: String sampling without infinite loops
    Given grammar with k=5, b=3, M_size=10
    When I sample 100 strings from grammar
    Then all sampling should complete within 1000 ms
    And no sampling should hang or timeout
    And all 100 samples should be valid strings

  Scenario: Maximum sampling depth
    Given grammar with k=5, b=3, M_size=10
    When I sample strings with max_depth=10
    Then all strings should parse successfully
    And string depth should not exceed max_depth

  Scenario: CYK parsing complexity bounds
    Given grammar with k=10, b=5, M_size=20
    When I parse string of length 50
    Then parsing time should be less than 100 milliseconds

  Scenario: Grammar size scaling
    When I generate grammars with increasing k:
      | k | Expected rules (approx) |
      | 1 | < 10                   |
      | 3 | < 50                   |
      | 5 | < 200                  |
      | 10| < 1000                 |
    Then rule count should not exceed estimated bounds
    And grammar should remain valid and parseable

  Scenario: Grammar with minimal parameters
    When I generate grammar with k=1, b=2, M_size=5
    Then grammar should be valid
    And grammar should have at least one rule
    And sampling should work correctly

  Scenario: Grammar with maximum parameters
    When I generate grammar with k=20, b=10, M_size=50
    Then grammar should be valid
    And grammar should parse sampled strings
    And parsing should complete in < 100ms

  Scenario: Frozen CFGGrammar dataclass
    Given generated grammar
    When I access k, b, M_size, rules, terminals, start_symbol
    Then all fields should be readable
    And grammar object should be immutable
    And attempting to modify should raise error

  Scenario: Empty string parsing
    Given grammar with seed=42
    When I parse empty string ""
    Then parse result should be well-defined
    And result should be False (unless grammar generates epsilon)

  Scenario: Very long string parsing
    Given grammar with k=5, b=2, M_size=10
    When I parse string of length 200
    Then parsing should complete in reasonable time
    And should not exceed memory limits
    And result should be well-defined

  Scenario: Terminal-only productions
    Given grammar with terminals [T0, T1, ..., T9]
    When I verify all terminals in sampled strings
    Then all tokens should be from terminal set
    And no invalid terminals should appear

  Scenario: Nonterminal reachability
    Given grammar with k=3, b=2, M_size=5
    When I check reachability from start symbol
    Then all nonterminals should be reachable
    And all nonterminals should contribute to derivations
