Feature: Theorem 2 — Aperiodic guardrails are blind to MOD_p encodings
  Any payload encoded with MOD_p interleaving evades all aperiodic
  regex guardrails. This is provable, not empirical.

  Scenario Outline: MOD_2 bypass evades pattern <id>
    Given the regex pattern "<pattern>"
    And the blocked payload "<payload>"
    When I encode the payload with MOD_2 interleaving using filler "x"
    Then the regex should match the original payload
    But the regex should not match the encoded string
    And decoding the encoded string with s[0::2] should recover the payload

    Examples: Attack table from paper Section 6.5
      | id | pattern                    | payload  |
      | F1 | (bomb\|weapon\|explosive)  | bomb     |
      | F4 | AKIA[0-9A-Z]{16}           | AKIAIOSFODNN7EXAMPLE |
      | F5 | (eval\|exec)\s*\(          | exec(    |

  Scenario: MOD_3 bypass with p=3 interleaving
    Given the regex pattern "(bomb\|weapon\|explosive)"
    And the blocked payload "bomb"
    When I encode the payload with MOD_3 interleaving using filler "xy"
    Then the regex should not match the encoded string
    And decoding the encoded string with s[0::3] should recover the payload
