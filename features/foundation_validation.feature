@foundation @tier-0
Feature: Cipher Validation — Bootstrap CI and Cross-Validation
  Cipher-validation module provides robust statistical confidence intervals,
  cross-validation, and quantitative metrics for encoding accuracy.

  Scenario: Bootstrap confidence interval with known distribution
    Given test data with 100 samples from N(μ=5.0, σ=1.0)
    When I compute 95% bootstrap CI with 1000 resamples
    Then lower bound should be within [4.5, 5.0]
    And upper bound should be within [5.0, 5.5]
    And CI width should be less than 1.0

  Scenario: Bootstrap CI on uniform distribution
    Given test data with 1000 samples from Uniform[0, 10]
    When I compute 95% bootstrap CI
    Then lower bound should be within [4.0, 5.5]
    And upper bound should be within [4.5, 6.0]
    And confidence interval should contain true mean

  Scenario: Bootstrap resampling size effect
    Given test data with 100 samples
    When I compute CI with 100 bootstrap resamples
    And I compute CI with 1000 bootstrap resamples
    And I compute CI with 5000 bootstrap resamples
    Then CI width should decrease with larger B
    And all CIs should contain true population mean

  Scenario: 90% vs 95% vs 99% confidence levels
    Given test data with 500 samples
    When I compute 90% bootstrap CI
    And I compute 95% bootstrap CI
    And I compute 99% bootstrap CI
    Then CI_90 width < CI_95 width < CI_99 width
    And all intervals should contain true mean
    And CI_99 should be widest

  Scenario: K-fold cross-validation with k=5
    Given encoder function and test set of 100 strings
    When I perform 5-fold cross-validation
    Then I should get exactly 5 fold results
    And training set size should be 80 samples per fold
    And validation set size should be 20 samples per fold
    And fold sizes should partition data exactly (no overlap/gaps)

  Scenario: Cross-validation fold stratification
    Given test set of 100 strings with 50 short + 50 long
    When I perform 5-fold cross-validation
    Then each fold should have ~10 short strings
    And each fold should have ~10 long strings
    And fold distributions should be balanced

  Scenario: Accuracy metric matches empirical rate
    Given encoder with known round-trip accuracy
    When I compute accuracy metric on 1000 test strings
    Then accuracy should match empirical (successes / total)
    And accuracy should be between 0.0 and 1.0

  Scenario: Precision and recall on error detection
    Given encoder and validation set with 100 strings
    When I compute precision metric
    And I compute recall metric
    Then precision + recall should be ≤ 1.5
    And both should be between 0.0 and 1.0

  Scenario: ValidationMetrics immutability
    Given computed ValidationMetrics object
    When I access accuracy, precision, recall, ci_lower, ci_upper
    Then all fields should be accessible
    And object should be frozen (no modifications allowed)

  Scenario: Metrics for 100% accurate encoder
    Given Caesar cipher encoder with shift=10
    When I validate on 1000 random strings
    Then accuracy should be 1.0
    And precision should be 1.0
    And recall should be 1.0
    And ci_lower should be very close to 1.0
    And ci_upper should be exactly 1.0

  Scenario: Metrics with partial encoder failure
    Given encoder that fails on 10% of inputs
    When I validate on 1000 strings
    Then accuracy should be approximately 0.90
    And confidence interval should be narrow (±0.05)

  Scenario: Bootstrap performance on large dataset
    Given test data with 10000 samples
    When I compute 95% bootstrap CI with 5000 resamples
    Then computation time should be less than 1000 milliseconds
    And result should be valid CI tuple (lower, upper)

  Scenario: Cross-validation with large test set
    Given test set of 5000 strings
    When I perform 5-fold cross-validation with k=5
    Then each fold has 4000 training samples
    And each fold has 1000 validation samples
    And computation time should be less than 5000 milliseconds

  Scenario: Reproducibility with fixed seed
    Given cross-validation with random seed=42
    When I run cross-validation twice
    Then fold assignments should be identical
    And metric results should be identical

  Scenario: Different bootstrap seeds produce different CIs
    Given test data with 100 samples
    When I compute CI with seed=42
    And I compute CI with seed=123
    Then CI bounds should differ
    But both should contain true mean
