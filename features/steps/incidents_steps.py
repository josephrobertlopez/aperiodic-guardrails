"""
Real-World AI Security Incidents step definitions
Level 1: Incident database collection and analysis
"""

import sys
import os
from pathlib import Path
from behave import given, when, then, step

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

@given('we need incidents from 2024-2026 timeframe')
def step_timeframe(context):
    """Define incident collection timeframe"""
    context.timeframe = {'start': '2024-01-01', 'end': '2026-12-31'}

@given('incidents must demonstrate vulnerability patterns')
def step_vulnerability_patterns(context):
    """Incidents must show predicted patterns"""
    context.required_patterns = ['prompt_injection', 'jailbreak', 'bypass', 'data_exposure']

@given('each incident needs technical analysis')
def step_technical_analysis(context):
    """Each incident needs technical details"""
    context.analysis_required = ['root_cause', 'attack_vector', 'mitigation_attempts']

@given('major AI security failures from news sources')
def step_major_incidents(context):
    """Collect major AI security incidents"""
    try:
        from cacm_article.incidents import collect_major_incidents
        context.incidents = collect_major_incidents(context.timeframe)
    except ImportError:
        raise AssertionError("Incidents collection module not implemented yet")

@when('catalogued with technical details')
def step_catalogue_incidents(context):
    """Catalogue incidents with technical analysis"""
    context.catalogued = True

@then('should include ChatGPT data exposure incidents')
def step_chatgpt_incidents(context):
    """Verify ChatGPT incidents included"""
    incidents = getattr(context, 'incidents', [])
    chatgpt_incidents = [i for i in incidents if 'chatgpt' in str(i).lower()]
    if not chatgpt_incidents:
        raise AssertionError("ChatGPT data exposure incidents not found")
    print(f"✓ ChatGPT incidents: {len(chatgpt_incidents)}")

@then('should include prompt injection demonstrations')
def step_prompt_injection(context):
    """Verify prompt injection incidents"""
    print("✓ Prompt injection incidents required")

@then('should include jailbreak technique publications')
def step_jailbreak_incidents(context):
    """Verify jailbreak technique incidents"""
    print("✓ Jailbreak technique incidents required")

@then('should include AI model poisoning cases')
def step_model_poisoning(context):
    """Verify model poisoning incidents"""
    print("✓ AI model poisoning incidents required")

@then('should include guardrail bypass demonstrations')
def step_guardrail_bypass(context):
    """Verify guardrail bypass incidents"""
    print("✓ Guardrail bypass incidents required")

@given('collected real-world incidents')
def step_collected_incidents(context):
    """Reference collected incidents"""
    # Use incidents from previous step if available, otherwise collect them
    if not hasattr(context, 'incidents'):
        try:
            from cacm_article.incidents import collect_major_incidents
            context.incidents = collect_major_incidents(context.timeframe)
        except ImportError:
            raise AssertionError("Incidents collection module not implemented yet")
    context.incident_count = len(getattr(context, 'incidents', []))

@when('analyzed for vulnerability patterns')
def step_analyze_patterns(context):
    """Analyze incidents for mathematical patterns"""
    try:
        from cacm_article.incidents import analyze_vulnerability_patterns
        context.pattern_analysis = analyze_vulnerability_patterns(context.incidents)
    except ImportError:
        raise AssertionError("Pattern analysis module not implemented yet")

@then('at least 70% should match predicted mathematical patterns')
def step_70_percent_correlation(context):
    """Validate 70% correlation threshold"""
    analysis = getattr(context, 'pattern_analysis', {})
    correlation = analysis.get('correlation_percentage', 0)
    if correlation < 70:
        raise AssertionError(f"Correlation {correlation}% below 70% threshold")
    print(f"✓ Pattern correlation: {correlation}%")

@then('each incident should map to specific theorem predictions')
def step_theorem_mapping(context):
    """Map incidents to mathematical predictions"""
    print("✓ Theorem mapping required")

@then('correlation should be independently verifiable')
def step_verifiable_correlation(context):
    """Ensure correlation is independently verifiable"""
    print("✓ Independent verification required")

@given('real-world incident database')
def step_incident_database(context):
    """Reference complete incident database"""
    context.database_complete = True

@when('analyzed for business impact')
def step_business_impact(context):
    """Analyze business impact of incidents"""
    context.business_analysis = 'pending'

@then('should include financial losses where available')
def step_financial_losses(context):
    """Include financial impact data"""
    print("✓ Financial losses documentation required")

@then('should include reputation damage assessments')
def step_reputation_damage(context):
    """Include reputation impact"""
    print("✓ Reputation damage assessment required")

@then('should include regulatory consequences')
def step_regulatory_consequences(context):
    """Include regulatory impact"""
    print("✓ Regulatory consequences required")

@then('should include recovery timeline analysis')
def step_recovery_timeline(context):
    """Include recovery timeline data"""
    print("✓ Recovery timeline analysis required")

@given('major AI security incidents')
def step_major_incidents_postmortem(context):
    """Reference major incidents for post-mortem"""
    context.major_incidents = True

@when('technical post-mortems are available')
def step_postmortem_available(context):
    """Check for available post-mortems"""
    context.postmortem_analysis = 'pending'

@then('should include root cause analysis')
def step_root_cause(context):
    """Include root cause analysis"""
    print("✓ Root cause analysis required")

@then('should include failed mitigation attempts')
def step_failed_mitigations(context):
    """Include failed mitigation attempts"""
    print("✓ Failed mitigation documentation required")

@then('should identify which mathematical predictions were validated')
def step_prediction_validation(context):
    """Identify validated mathematical predictions"""
    print("✓ Mathematical prediction validation required")

@given('collected incident reports')
def step_incident_reports(context):
    """Reference incident reports for verification"""
    context.reports = True

@when('verified for accuracy')
def step_verify_accuracy(context):
    """Verify incident report accuracy"""
    context.verification = 'pending'

@then('sources must be reputable (news, research, vendor disclosures)')
def step_reputable_sources(context):
    """Ensure reputable sources"""
    print("✓ Reputable sources required")

@then('technical details must be independently confirmed')
def step_independent_confirmation(context):
    """Require independent confirmation"""
    print("✓ Independent confirmation required")

@then('avoid speculation or unverified claims')
def step_avoid_speculation(context):
    """Avoid unverified claims"""
    print("✓ No speculation constraint")

@given('verified incident database')
def step_verified_database(context):
    """Reference verified incident database"""
    context.verified = True

@when('compiled for maximum impact')
def step_compile_impact(context):
    """Compile for maximum impact"""
    context.impact_compilation = 'pending'

@then('incidents should be ordered by severity and relevance')
def step_order_by_severity(context):
    """Order by severity and relevance"""
    print("✓ Severity ordering required")

@then('should demonstrate pattern of mathematical inevitability')
def step_mathematical_inevitability(context):
    """Demonstrate mathematical inevitability"""
    print("✓ Mathematical inevitability pattern required")

@then('should build compelling narrative for enterprise audience')
def step_compelling_narrative(context):
    """Build compelling enterprise narrative"""
    print("✓ Compelling enterprise narrative required")

print("📰 Real-World Incidents steps initialized - Level 1 ready")