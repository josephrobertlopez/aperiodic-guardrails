Feature: V1/V2 — Decomposition and zero-knowledge pipeline
  Known techniques reframed in the abstraction framework.
  The engine executes opaque configs without inspecting content.

  Scenario: Engine decodes base64 config without exposing content
    Given a config with medium "graph_solver" and target "N30"
    When I encode the config to base64
    And I decode the config with the engine
    Then the decoded config should have medium "graph_solver"
    And the decoded config should have target "N30"
    And no intermediate step should expose the target in plaintext logs

  Scenario: Graph solver finds path on abstract grammar
    Given a grammar with initial state ["N0", "N1"] and target "N30"
    And rules that form a valid path N0 -> N2 -> N3 -> N30
    When I run the graph solver
    Then the solver should find a path to N30
    And the path should have positive yield
