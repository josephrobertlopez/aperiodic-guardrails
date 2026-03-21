@nondeterministic @requires-ollama
Feature: ToT Benchmark — LLM-guided reasoning outperforms uninformed search
  Tree-of-Thought with LLM evaluation achieves higher yield than
  BFS and random-beam on abstract grammars. Results are stochastic.

  Scenario: Grammar generation produces valid solvable instances
    Given I generate 5 randomized grammars with seeds 1000-1004
    Then each grammar should have a valid path from initial state to target
    And each grammar should have at least 10 rules
    And each grammar should have at least 2 constraints

  @slow
  Scenario: BFS finds paths on all generated grammars
    Given I generate 5 randomized grammars with seeds 1000-1004
    When I run BFS on each grammar with depth limit 12
    Then BFS should find a path on at least 4 of 5 grammars
    And BFS mean yield should be between 0.05 and 0.30

  @slow @requires-ollama
  Scenario: ToT+LLM outperforms random-beam
    Given I generate 5 randomized grammars with seeds 1000-1004
    When I run random-beam on each grammar with beam width 5
    And I run ToT+LLM on each grammar with beam width 5 and model "qwen2.5-coder:7b"
    Then ToT mean yield should be greater than random-beam mean yield
