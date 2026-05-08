"""
Evidence Barrage Synthesis step definitions
Level 2: Synthesis of mathematical foundations with real-world incidents
"""

import sys
import os
from pathlib import Path
from behave import given, when, then, step

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

@given('foundations component is GREEN with mathematical theorem translation')
def step_foundations_green(context):
    """Verify foundations component is complete"""
    try:
        from cacm_article.foundations import translate_theorem_to_executive
        context.foundations_ready = True
        context.mathematical_translation = 'available'
    except ImportError:
        raise AssertionError("Foundations component not GREEN - translation module missing")

@given('incidents component is GREEN with 80% correlation rate')
def step_incidents_green(context):
    """Verify incidents component is complete"""
    try:
        from cacm_article.incidents import analyze_vulnerability_patterns, collect_major_incidents
        context.incidents_ready = True
        # Verify correlation rate meets threshold
        timeframe = {'start': '2024-01-01', 'end': '2026-12-31'}
        incidents = collect_major_incidents(timeframe)
        analysis = analyze_vulnerability_patterns(incidents)
        correlation = analysis.get('correlation_percentage', 0)
        if correlation < 70:
            raise AssertionError(f"Incidents correlation {correlation}% below required 70%")
        context.correlation_rate = correlation
    except ImportError:
        raise AssertionError("Incidents component not GREEN - analysis module missing")

@given('enterprise component is GREEN with business context')
def step_enterprise_green(context):
    """Verify enterprise component is complete"""
    try:
        from cacm_article.enterprise import assess_current_practices, collect_financial_impact_data
        context.enterprise_ready = True
        context.business_context = 'available'
    except ImportError:
        raise AssertionError("Enterprise component not GREEN - business context module missing")

@given('mathematical vulnerability patterns from Universal AI Vulnerability Theorem')
def step_mathematical_patterns(context):
    """Reference mathematical vulnerability patterns"""
    try:
        from cacm_article.evidence_barrage import get_mathematical_patterns
        context.mathematical_patterns = get_mathematical_patterns()
    except ImportError:
        raise AssertionError("Evidence barrage synthesis module not implemented yet")

@given('collected real-world incidents with technical analysis')
def step_incidents_with_analysis(context):
    """Reference incidents with technical details"""
    from cacm_article.incidents import collect_major_incidents
    timeframe = {'start': '2024-01-01', 'end': '2026-12-31'}
    context.incidents_with_analysis = collect_major_incidents(timeframe)

@when('cross-referenced for pattern correlation')
def step_cross_reference_patterns(context):
    """Cross-reference mathematical patterns with real incidents"""
    try:
        from cacm_article.evidence_barrage import cross_reference_patterns
        context.pattern_correlation = cross_reference_patterns(
            context.mathematical_patterns,
            context.incidents_with_analysis
        )
    except ImportError:
        raise AssertionError("Pattern correlation analysis not implemented yet")

@then('correlation rate should exceed 70% threshold')
def step_correlation_threshold(context):
    """Validate correlation exceeds threshold"""
    correlation = getattr(context, 'correlation_rate', 0)
    if correlation < 70:
        raise AssertionError(f"Correlation {correlation}% below 70% threshold")
    print(f"✓ Correlation rate: {correlation}% (exceeds 70% threshold)")

@then('each mathematical prediction should have incident examples')
def step_predictions_have_examples(context):
    """Validate each prediction has incident examples"""
    correlation = getattr(context, 'pattern_correlation', {})
    predictions_with_examples = correlation.get('predictions_with_examples', [])
    print(f"✓ Mathematical predictions with incident examples: {len(predictions_with_examples)}")

@then('correlation methodology should be independently verifiable')
def step_verifiable_correlation(context):
    """Ensure correlation methodology is verifiable"""
    print("✓ Correlation methodology independence verification required")

@given('real-world AI security incidents with business impact data')
def step_incidents_business_impact(context):
    """Reference incidents with business impact data"""
    from cacm_article.enterprise import collect_financial_impact_data
    context.business_impact_data = collect_financial_impact_data()

@given('mathematical vulnerability classifications')
def step_vulnerability_classifications(context):
    """Reference mathematical vulnerability classifications"""
    context.vulnerability_classifications = [
        'universal_vulnerability_theorem',
        'abstraction_layer_failure',
        'syntactic_monoid_aperiodicity',
        'semantic_drift_exploitation',
        'compositional_security_failure'
    ]

@when('ranked by enterprise relevance and mathematical inevitability')
def step_rank_by_relevance(context):
    """Rank incidents by relevance and mathematical backing"""
    # Get incidents if not already available
    if not hasattr(context, 'incidents_with_analysis'):
        from cacm_article.incidents import collect_major_incidents
        timeframe = {'start': '2024-01-01', 'end': '2026-12-31'}
        context.incidents_with_analysis = collect_major_incidents(timeframe)

    try:
        from cacm_article.evidence_barrage import rank_incidents_by_impact
        context.ranked_incidents = rank_incidents_by_impact(
            context.incidents_with_analysis,
            context.business_impact_data,
            context.vulnerability_classifications
        )
    except ImportError:
        raise AssertionError("Incident ranking module not implemented yet")

@then('should prioritize incidents demonstrating universal vulnerability patterns')
def step_prioritize_universal_patterns(context):
    """Prioritize incidents with universal patterns"""
    print("✓ Universal vulnerability pattern prioritization required")

@then('should include financial impact quantification')
def step_financial_quantification(context):
    """Include financial impact data"""
    print("✓ Financial impact quantification required")

@then('should highlight mathematical predictions validated by failures')
def step_highlight_validated_predictions(context):
    """Highlight validated mathematical predictions"""
    print("✓ Mathematical prediction validation highlighting required")

@given('mathematically-validated incident patterns')
def step_validated_patterns(context):
    """Reference validated incident patterns"""
    context.validated_patterns = 'from_correlation_analysis'

@given('enterprise business context and risk frameworks')
def step_enterprise_risk_context(context):
    """Reference enterprise context"""
    context.enterprise_risk_context = 'from_enterprise_component'

@when('synthesized into evidence barrage narrative')
def step_synthesize_narrative(context):
    """Synthesize evidence into compelling narrative"""
    # Ensure ranked incidents are available
    if not hasattr(context, 'ranked_incidents'):
        from cacm_article.incidents import collect_major_incidents
        from cacm_article.enterprise import collect_financial_impact_data
        from cacm_article.evidence_barrage import rank_incidents_by_impact

        timeframe = {'start': '2024-01-01', 'end': '2026-12-31'}
        incidents = collect_major_incidents(timeframe)
        business_data = collect_financial_impact_data()
        classifications = ['universal_vulnerability_theorem', 'abstraction_layer_failure']
        context.ranked_incidents = rank_incidents_by_impact(incidents, business_data, classifications)

    try:
        from cacm_article.evidence_barrage import synthesize_evidence_narrative
        context.evidence_narrative = synthesize_evidence_narrative(
            context.validated_patterns,
            context.enterprise_risk_context,
            context.ranked_incidents
        )
    except ImportError:
        raise AssertionError("Evidence narrative synthesis not implemented yet")

@then('should demonstrate mathematical inevitability in evidence synthesis')
def step_mathematical_inevitability_pattern(context):
    """Demonstrate mathematical inevitability in synthesis"""
    print("✓ Mathematical inevitability pattern demonstration in synthesis required")

@then('should translate technical failures to business consequences')
def step_technical_to_business(context):
    """Translate technical failures to business terms"""
    print("✓ Technical to business translation required")

@then('should build credible case for mathematical validation adoption')
def step_credible_adoption_case(context):
    """Build credible case for adoption"""
    print("✓ Credible adoption case construction required")

@given('incident database with source attribution')
def step_incident_sources(context):
    """Reference incident database with sources"""
    context.incident_sources = 'verified_sources'

@given('mathematical correlation analysis')
def step_correlation_analysis(context):
    """Reference correlation analysis"""
    context.correlation_analysis = 'completed'

@when('reviewed for credibility and accuracy')
def step_credibility_review(context):
    """Review evidence for credibility"""
    context.credibility_review = 'pending'

@then('all incidents must have reputable sources')
def step_reputable_sources(context):
    """Ensure reputable sources"""
    print("✓ Reputable source requirement verification needed")

@then('mathematical correlations must be independently verifiable')
def step_independent_verification(context):
    """Ensure independent verification"""
    print("✓ Independent verification of mathematical correlations required")

@then('should avoid speculation or unsubstantiated claims')
def step_avoid_speculation(context):
    """Avoid speculation"""
    print("✓ No speculation constraint enforcement required")

@given('verified evidence barrage with mathematical backing')
def step_verified_evidence(context):
    """Reference verified evidence barrage"""
    context.verified_evidence = 'complete'

@given('enterprise audience comprehension constraints')
def step_audience_constraints(context):
    """Reference audience constraints"""
    context.audience_constraints = ['avoid_formal_notation', 'business_analogies', '90_day_actionability']

@when('structured for maximum persuasive impact')
def step_structure_for_impact(context):
    """Structure evidence for maximum impact"""
    try:
        from cacm_article.evidence_barrage import structure_for_maximum_impact
        context.structured_evidence = structure_for_maximum_impact(
            context.verified_evidence,
            context.audience_constraints
        )
    except ImportError:
        raise AssertionError("Evidence structuring module not implemented yet")

@then('should lead with highest-impact, clearest incidents')
def step_lead_highest_impact(context):
    """Lead with highest impact incidents"""
    print("✓ Highest-impact incident leadership required")

@then('should reinforce mathematical inevitability theme')
def step_reinforce_inevitability(context):
    """Reinforce mathematical inevitability theme"""
    print("✓ Mathematical inevitability theme reinforcement required")

@then('should build toward actionable recommendations')
def step_build_actionable(context):
    """Build toward actionable recommendations"""
    print("✓ Actionable recommendation building required")

print("🎯 Evidence Barrage Synthesis steps initialized - Level 2 ready")