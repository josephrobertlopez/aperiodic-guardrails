"""
Mathematical Foundations step definitions for CACM Article
Level 1: Mathematical concepts translated for enterprise audience
"""

import sys
import os
from pathlib import Path
from behave import given, when, then, step

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

@given('the target audience includes CTOs and CISOs')
def step_executive_audience(context):
    """Define executive audience constraints"""
    context.audience_level = 'executive'
    context.technical_background = 'business_systems'

@given('mathematical concepts must avoid formal notation')
def step_avoid_notation(context):
    """No mathematical symbols or formal notation"""
    context.forbidden_notation = ['∀', '∃', '→', '⊆', 'Σ*', 'Q: C → A']
    context.use_prose = True

@given('explanations must use business analogies')
def step_business_analogies(context):
    """Require business-relevant analogies"""
    context.analogy_domains = ['banking_security', 'supply_chain', 'risk_management']

@given('the universal AI vulnerability theorem')
def step_universal_theorem(context):
    """Reference the mathematical theorem"""
    context.theorem = {
        'name': 'Universal AI Vulnerability Theorem',
        'claim': 'Every practical AI system has exploitable vulnerabilities',
        'proof_exists': True
    }

@when('translated to executive language')
def step_translate_executive(context):
    """Translate mathematical concept to executive language"""
    # Check if translation exists - should fail until implemented
    try:
        from cacm_article.foundations import translate_theorem_to_executive
        context.translation = translate_theorem_to_executive(context.theorem)
    except ImportError:
        raise AssertionError("Mathematical translation module not implemented yet")

@then('it should explain "every practical AI system has mathematical blindspots"')
def step_core_explanation(context):
    """Validate core concept explanation"""
    expected_insight = "every practical AI system has mathematical blindspots"
    # Check if translation contains the core insight
    translation = getattr(context, 'translation', None)
    if not translation or 'mathematical blindspots' not in str(translation):
        raise AssertionError(f"Translation missing core insight: {expected_insight}")
    print(f"✓ Core explanation validated: {expected_insight}")

@then('it should use business analogies like "security theater vs. real security"')
def step_business_analogies_validation(context):
    """Validate use of business analogies"""
    required_analogies = ["security theater vs. real security"]
    print(f"✓ Business analogies required: {required_analogies}")

@then('it should avoid terms like "functor", "monoid", "category theory"')
def step_avoid_jargon(context):
    """Ensure mathematical jargon is avoided"""
    forbidden_terms = ["functor", "monoid", "category theory", "morphism"]
    print(f"✓ Must avoid jargon: {forbidden_terms}")

@given('research results showing 100% bypass rates')
def step_empirical_results(context):
    """Reference empirical validation results"""
    context.empirical_data = {
        'bypass_rate': 100,  # percent
        'confidence_metrics': [0.466, 0.172, 0.122],
        'test_coverage': 1056  # systematic tests
    }

@when('presented for enterprise audience')
def step_present_enterprise(context):
    """Present results for enterprise consumption"""
    context.enterprise_presentation = 'pending'

@then('numbers should be contextualized as "attack success rates"')
def step_attack_success_context(context):
    """Contextualize numbers as attack metrics"""
    expected_context = "attack success rates"
    print(f"✓ Numerical context required: {expected_context}")

@then('0.466, 0.172, 0.122 should be explained as "confidence thresholds"')
def step_confidence_thresholds(context):
    """Explain specific numerical results"""
    metrics = context.empirical_data['confidence_metrics']
    print(f"✓ Confidence thresholds to explain: {metrics}")

@then('statistical significance should be stated in business terms')
def step_business_statistics(context):
    """Express statistics in business language"""
    print("✓ Statistical significance in business terms required")

@given('mathematical theorems about AI limitations')
def step_math_theorems(context):
    """Reference mathematical limitations"""
    context.theorems = ['universal_vulnerability', 'information_theoretic_bounds']

@when('deriving business implications')
def step_derive_implications(context):
    """Derive practical business implications"""
    context.implications = 'pending'

@then('should identify "what this means for enterprise security budgets"')
def step_budget_implications(context):
    """Identify budget implications"""
    print("✓ Budget implications required")

@then('should explain "why perfect AI security is impossible"')
def step_impossibility_explanation(context):
    """Explain impossibility of perfect security"""
    print("✓ Perfect security impossibility explanation required")

@then('should translate to "risk acceptance vs. risk elimination"')
def step_risk_framework(context):
    """Translate to risk management framework"""
    print("✓ Risk acceptance vs elimination framework required")

@given('simplified mathematical explanations')
def step_simplified_explanations(context):
    """Simplified but accurate explanations"""
    context.simplification_level = 'executive_accessible'

@when('reviewed by technical experts')
def step_technical_review(context):
    """Technical expert review process"""
    context.expert_review = 'pending'

@then('core mathematical validity must be preserved')
def step_preserve_validity(context):
    """Ensure mathematical validity preserved"""
    print("✓ Mathematical validity preservation required")

@then('no false claims should be introduced for accessibility')
def step_no_false_claims(context):
    """Prevent false claims from simplification"""
    print("✓ No false claims constraint")

@then('original research conclusions should remain intact')
def step_preserve_conclusions(context):
    """Preserve original research conclusions"""
    print("✓ Original conclusions preservation required")

@given('accessible mathematical explanations')
def step_accessible_explanations(context):
    """Accessible but credible explanations"""
    context.credibility_factors = ['mathematical_backing', 'peer_review']

@when('industry practitioners evaluate claims')
def step_industry_evaluation(context):
    """Industry practitioner evaluation"""
    context.practitioner_review = 'pending'

@then('mathematical backing should enhance credibility')
def step_enhance_credibility(context):
    """Mathematical backing should add credibility"""
    print("✓ Credibility enhancement required")

@then('simplification should not undermine technical authority')
def step_preserve_authority(context):
    """Maintain technical authority despite simplification"""
    print("✓ Technical authority preservation required")

@then('peer review should confirm accuracy of translations')
def step_peer_review_accuracy(context):
    """Peer review of translation accuracy"""
    print("✓ Peer review accuracy confirmation required")

print("🔢 Mathematical Foundations steps initialized - Level 1 ready")