Feature: Proposition 4 — Fano bound on lifted guardrail error
  The binary entropy inverse gives an irreducible error floor
  for any lifted guardrail operating on abstracted content.

  Scenario: 30% mixed fiber mass gives ~5% error floor
    Given 30% of probability mass falls in mixed fibers
    And mixed fibers have 50/50 safe/unsafe split
    When I compute H(G(R) | U(R))
    Then the conditional entropy should be approximately 0.3 bits
    And h_inverse(0.3) should be approximately 0.048
    And the error floor should be approximately 5%

  Scenario: 50% mixed fiber mass gives ~11% error floor
    Given 50% of probability mass falls in mixed fibers
    And mixed fibers have 50/50 safe/unsafe split
    When I compute H(G(R) | U(R))
    Then the conditional entropy should be approximately 0.5 bits
    And h_inverse(0.5) should be approximately 0.110
