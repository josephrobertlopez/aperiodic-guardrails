Feature: Theorem 1 — Substring-matching regex guardrails are aperiodic
  All substring-matching regex patterns used in guardrails have
  aperiodic syntactic monoids, placing them in AC^0.

  Scenario Outline: Guardrail pattern <id> has aperiodic syntactic monoid
    Given the regex pattern "<pattern>"
    When I compute the syntactic monoid via DFA minimization
    Then the monoid should be aperiodic
    And the monoid size should be <monoid_size>

    Examples: Representative guardrail patterns from 5 tools
      | id | pattern                          | monoid_size |
      | F1 | (bomb\|weapon\|explosive)        | 70          |
      | F2 | b[i1][t+]ch                      | 17          |
      | F3 | ignore\s+(all\s+)?(previous\|prior)\s+instructions? | 562 |
      | F4 | AKIA[0-9A-Z]{16}                 | 91          |
      | F5 | (eval\|exec)\s*\(               | 26          |

  Scenario: Non-aperiodic pattern (aa)* has cyclic group Z/2Z
    Given the regex pattern "(aa)*"
    When I compute the syntactic monoid via DFA minimization
    Then the monoid should not be aperiodic
    And the monoid should contain group Z/2Z
