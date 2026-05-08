"""
Enterprise Context Framework step definitions
Level 1: Enterprise guidance and business translation
"""

import sys
import os
from pathlib import Path
from behave import given, when, then, step

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

@given('the target audience includes CTOs, CISOs, and AI governance leaders')
def step_executive_audience(context):
    """Define enterprise executive audience"""
    context.target_audience = {
        'primary': ['CTO', 'CISO', 'AI_governance_leader'],
        'secondary': ['board_members', 'risk_officers', 'compliance_teams']
    }
    context.audience_constraints = ['90_day_actionability', 'budget_implications', 'regulatory_alignment']

@given('guidance must integrate with existing enterprise frameworks')
def step_enterprise_frameworks(context):
    """Reference existing enterprise frameworks"""
    context.enterprise_frameworks = ['SOX', 'SOC2', 'ISO_27001', 'NIST_AI_RMF', 'EU_AI_Act']

@given('recommendations must be actionable within 90 days')
def step_90_day_constraint(context):
    """90-day implementation timeline constraint"""
    context.implementation_timeline = '90_days'
    context.actionable_constraint = True

@given('typical enterprise AI deployment patterns')
def step_enterprise_patterns(context):
    """Reference typical enterprise AI deployments"""
    try:
        from cacm_article.enterprise import assess_current_practices
        context.current_practices = assess_current_practices()
    except ImportError:
        raise AssertionError("Enterprise assessment module not implemented yet")

@when('analyzed for security vulnerabilities')
def step_analyze_vulnerabilities(context):
    """Analyze current practices for vulnerabilities"""
    context.vulnerability_analysis = 'pending'

@then('should identify common guardrail tools (LLM Guard, content filters)')
def step_common_guardrails(context):
    """Identify current guardrail tools"""
    expected_tools = ['LLM_Guard', 'content_filters', 'prompt_validators']
    print(f"✓ Common guardrail tools to assess: {expected_tools}")

@then('should assess current risk management frameworks')
def step_assess_risk_frameworks(context):
    """Assess current enterprise risk frameworks"""
    print("✓ Risk management framework assessment required")

@then('should identify gaps in mathematical validation')
def step_mathematical_gaps(context):
    """Identify gaps in mathematical validation"""
    print("✓ Mathematical validation gaps identification required")

@given('regulatory frameworks for enterprise compliance')
def step_regulatory_frameworks(context):
    """Reference regulatory frameworks"""
    context.regulatory_frameworks = {
        'EU_AI_Act': {'status': 'active', 'compliance_deadline': '2026-08-02'},
        'NIST_AI_RMF': {'status': 'guideline', 'adoption_rate': '65%'},
        'ISO_27001_AI': {'status': 'draft', 'expected': '2026-12-01'}
    }

@when('mathematical constraints are considered')
def step_mathematical_constraints(context):
    """Consider mathematical impossibility constraints"""
    context.mathematical_constraints = ['universal_vulnerability_theorem', 'information_theoretic_bounds']

@then('should identify gaps in current compliance frameworks')
def step_compliance_gaps(context):
    """Identify compliance framework gaps"""
    print("✓ Compliance framework gaps identification required")

@then('should translate mathematical limits to policy recommendations')
def step_policy_translation(context):
    """Translate mathematical limits to policy"""
    print("✓ Mathematical limits to policy translation required")

@then('should provide compliance roadmap for 90-day implementation')
def step_compliance_roadmap(context):
    """Provide 90-day compliance roadmap"""
    print("✓ 90-day compliance roadmap required")

@given('mathematical impossibility of perfect AI security')
def step_mathematical_impossibility(context):
    """Reference mathematical impossibility result"""
    context.impossibility_theorem = {
        'claim': 'Perfect AI security is mathematically impossible',
        'proof_exists': True,
        'business_implication': 'risk_acceptance_framework_required'
    }

@when('translated to enterprise risk management')
def step_risk_translation(context):
    """Translate to enterprise risk management"""
    context.risk_translation = 'pending'

@then('should shift from "risk elimination" to "risk acceptance" framework')
def step_risk_acceptance(context):
    """Shift to risk acceptance framework"""
    expected_shift = "risk_elimination → risk_acceptance_with_quantification"
    print(f"✓ Risk framework shift required: {expected_shift}")

@then('should provide quantitative risk assessment methods')
def step_quantitative_risk(context):
    """Provide quantitative risk assessment"""
    print("✓ Quantitative risk assessment methods required")

@then('should integrate with existing SOX, SOC2, ISO 27001 frameworks')
def step_integrate_frameworks(context):
    """Integration with existing frameworks"""
    frameworks = context.enterprise_frameworks
    print(f"✓ Framework integration required: {frameworks}")

@given('real-world AI security incidents with financial data')
def step_financial_incidents(context):
    """Reference incidents with financial impact"""
    try:
        from cacm_article.enterprise import collect_financial_impact_data
        context.financial_impacts = collect_financial_impact_data()
    except ImportError:
        raise AssertionError("Financial impact analysis module not implemented yet")

@when('analyzed for enterprise budget implications')
def step_budget_analysis(context):
    """Analyze budget implications"""
    context.budget_analysis = 'pending'

@then('should provide cost-benefit analysis of security approaches')
def step_cost_benefit(context):
    """Provide cost-benefit analysis"""
    print("✓ Cost-benefit analysis of security approaches required")

@then('should quantify ROI of mathematical validation vs security theater')
def step_roi_quantification(context):
    """Quantify ROI of mathematical validation"""
    print("✓ ROI quantification: mathematical validation vs security theater")

@then('should include implementation timeline and resource requirements')
def step_resource_requirements(context):
    """Include resource requirements"""
    print("✓ Implementation timeline and resource requirements needed")

@given('UW-Whitewater NSA-designated cybersecurity center')
def step_balaji_credibility(context):
    """Reference Balaji's institutional backing"""
    context.institutional_backing = {
        'institution': 'UW-Whitewater',
        'designation': 'NSA_cybersecurity_center',
        'credibility_factor': 'government_backing'
    }

@when('leveraged for enterprise credibility')
def step_leverage_credibility(context):
    """Leverage institutional credibility"""
    context.credibility_strategy = 'pending'

@then('should establish institutional authority for recommendations')
def step_institutional_authority(context):
    """Establish institutional authority"""
    print("✓ Institutional authority establishment required")

@then('should provide third-party validation of mathematical approaches')
def step_third_party_validation(context):
    """Third-party validation"""
    print("✓ Third-party validation of mathematical approaches required")

@then('should connect to broader cybersecurity community expertise')
def step_community_expertise(context):
    """Connect to cybersecurity community"""
    print("✓ Broader cybersecurity community connection required")

@given('diverse enterprise technology environments')
def step_diverse_environments(context):
    """Reference diverse enterprise environments"""
    context.tech_environments = ['cloud_native', 'hybrid', 'on_premise', 'multi_cloud']

@when('mathematical validation tools are deployed')
def step_deploy_validation_tools(context):
    """Deploy mathematical validation tools"""
    context.deployment_context = 'enterprise_integration'

@then('should integrate with existing security operations centers')
def step_soc_integration(context):
    """Integration with SOCs"""
    print("✓ Security Operations Center integration required")

@then('should work with current threat detection platforms')
def step_threat_platform_integration(context):
    """Integration with threat detection"""
    print("✓ Threat detection platform integration required")

@then('should provide APIs for enterprise security orchestration')
def step_api_orchestration(context):
    """Provide orchestration APIs"""
    print("✓ Enterprise security orchestration APIs required")

@given('need to communicate mathematical limits to board level')
def step_board_communication(context):
    """Board-level communication requirement"""
    context.board_communication = {
        'audience': 'board_of_directors',
        'format': 'executive_summary',
        'time_constraint': '15_minutes_max'
    }

@when('preparing executive presentations')
def step_executive_presentations(context):
    """Prepare executive presentations"""
    context.presentation_prep = 'pending'

@then('should provide board-ready risk assessment summaries')
def step_board_summaries(context):
    """Board-ready summaries"""
    print("✓ Board-ready risk assessment summaries required")

@then('should translate technical findings to business language')
def step_business_language(context):
    """Translate to business language"""
    print("✓ Technical findings to business language translation required")

@then('should include actionable recommendations for governance committees')
def step_governance_recommendations(context):
    """Actionable governance recommendations"""
    print("✓ Actionable governance committee recommendations required")

print("🏢 Enterprise Context Framework steps initialized - Level 1 ready")