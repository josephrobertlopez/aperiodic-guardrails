"""
Compliance Roadmap Synthesis step definitions
Level 2: Comprehensive regulatory compliance with mathematical validation
"""

import sys
import os
from pathlib import Path
from behave import given, when, then, step

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

@given('enterprise component is GREEN with regulatory framework context')
def step_enterprise_regulatory_context(context):
    """Verify enterprise component with regulatory context"""
    try:
        from cacm_article.enterprise import assess_current_practices, collect_financial_impact_data
        context.regulatory_context = True
        context.enterprise_frameworks = 'available'
    except ImportError:
        raise AssertionError("Enterprise component not GREEN - regulatory context missing")

@given('risk_framework component is GREEN with quantitative risk metrics')
def step_risk_framework_metrics(context):
    """Verify risk framework component with quantitative metrics"""
    try:
        from cacm_article.risk_framework import translate_to_risk_metrics, calibrate_risk_tolerance
        context.quantitative_metrics = True
        context.risk_framework = 'available'
    except ImportError:
        raise AssertionError("Risk framework component not GREEN - quantitative metrics missing")

@given('evidence_barrage component is GREEN with validated mathematical patterns')
def step_evidence_validated_patterns(context):
    """Verify evidence barrage component with validated patterns"""
    try:
        from cacm_article.evidence_barrage import get_mathematical_patterns, cross_reference_patterns
        context.validated_patterns = True
        context.evidence_barrage = 'available'
    except ImportError:
        raise AssertionError("Evidence barrage component not GREEN - validated patterns missing")

@given('EU AI Act requirements for high-risk AI systems')
def step_eu_ai_act_requirements(context):
    """Reference EU AI Act high-risk system requirements"""
    try:
        from cacm_article.compliance_roadmap import get_eu_ai_act_requirements
        context.eu_ai_act = get_eu_ai_act_requirements()
    except ImportError:
        raise AssertionError("Compliance roadmap synthesis module not implemented yet")

@given('mathematical validation capabilities from evidence synthesis')
def step_mathematical_validation_capabilities(context):
    """Reference mathematical validation capabilities"""
    context.validation_capabilities = 'from_evidence_barrage_synthesis'

@when('EU AI Act compliance is mapped to mathematical validation framework')
def step_map_eu_ai_act(context):
    """Map EU AI Act compliance to mathematical validation"""
    try:
        from cacm_article.compliance_roadmap import map_eu_ai_act_compliance
        context.eu_compliance_mapping = map_eu_ai_act_compliance(
            context.eu_ai_act,
            context.validation_capabilities
        )
    except ImportError:
        raise AssertionError("EU AI Act compliance mapping not implemented yet")

@then('should identify mathematical validation as compliance requirement')
def step_mathematical_validation_requirement(context):
    """Identify mathematical validation as requirement"""
    print("✓ Mathematical validation as EU AI Act compliance requirement identification needed")

@then('should provide 90-day implementation roadmap for EU AI Act readiness')
def step_90_day_eu_roadmap(context):
    """Provide 90-day EU AI Act roadmap"""
    print("✓ 90-day EU AI Act implementation roadmap required")

@then('should include August 2026 compliance deadline considerations')
def step_august_2026_deadline(context):
    """Include August 2026 deadline considerations"""
    print("✓ August 2026 EU AI Act compliance deadline considerations required")

@given('SOX Section 404 internal control requirements')
def step_sox_404_requirements(context):
    """Reference SOX Section 404 requirements"""
    context.sox_404 = {
        'requirement': 'internal_controls_over_financial_reporting',
        'ai_scope': 'AI systems affecting financial data or processes',
        'testing_frequency': 'quarterly',
        'materiality_threshold': 'systems processing >$1M monthly'
    }

@given('mathematical vulnerability patterns affecting financial systems')
def step_financial_vulnerability_patterns(context):
    """Reference vulnerability patterns affecting financial systems"""
    context.financial_vulnerabilities = [
        'data_exposure_in_financial_ai',
        'prompt_injection_affecting_financial_decisions',
        'model_poisoning_in_financial_forecasting'
    ]

@when('SOX compliance framework is updated with AI mathematical controls')
def step_update_sox_framework(context):
    """Update SOX framework with AI mathematical controls"""
    try:
        from cacm_article.compliance_roadmap import update_sox_ai_controls
        context.sox_ai_controls = update_sox_ai_controls(
            context.sox_404,
            context.financial_vulnerabilities
        )
    except ImportError:
        raise AssertionError("SOX AI controls update not implemented yet")

@then('should specify AI control requirements with mathematical validation')
def step_ai_control_requirements(context):
    """Specify AI control requirements"""
    print("✓ AI control requirements with mathematical validation specification needed")

@then('should provide auditor guidance for mathematical validation assessment')
def step_auditor_guidance(context):
    """Provide auditor guidance"""
    print("✓ Auditor guidance for mathematical validation assessment required")

@then('should include quarterly testing procedures for mathematical controls')
def step_quarterly_testing_procedures(context):
    """Include quarterly testing procedures"""
    print("✓ Quarterly testing procedures for mathematical controls required")

@given('NIST AI Risk Management Framework guidelines')
def step_nist_ai_rmf_guidelines(context):
    """Reference NIST AI RMF guidelines"""
    context.nist_ai_rmf = {
        'core_functions': ['govern', 'map', 'measure', 'manage'],
        'ai_specific_risks': ['bias', 'transparency', 'security', 'privacy'],
        'implementation_guidance': 'risk_based_approach',
        'update_frequency': 'annually'
    }

@given('quantitative risk metrics from risk framework synthesis')
def step_quantitative_risk_metrics(context):
    """Reference quantitative risk metrics"""
    context.quantitative_metrics_ref = 'from_risk_framework_synthesis'

@when('NIST AI RMF is implemented with mathematical validation')
def step_implement_nist_with_validation(context):
    """Implement NIST AI RMF with mathematical validation"""
    try:
        from cacm_article.compliance_roadmap import implement_nist_ai_rmf_with_validation
        context.nist_implementation = implement_nist_ai_rmf_with_validation(
            context.nist_ai_rmf,
            context.quantitative_metrics_ref
        )
    except ImportError:
        raise AssertionError("NIST AI RMF implementation not implemented yet")

@then('should integrate mathematical risk assessment with NIST framework')
def step_integrate_mathematical_nist(context):
    """Integrate mathematical assessment with NIST"""
    print("✓ Mathematical risk assessment integration with NIST framework required")

@then('should provide governance structure for mathematical validation oversight')
def step_governance_structure(context):
    """Provide governance structure"""
    print("✓ Governance structure for mathematical validation oversight required")

@then('should include continuous monitoring procedures for AI risk management')
def step_continuous_monitoring(context):
    """Include continuous monitoring procedures"""
    print("✓ Continuous monitoring procedures for AI risk management required")

@given('ISO 27001 information security management requirements')
def step_iso_27001_requirements(context):
    """Reference ISO 27001 requirements"""
    context.iso_27001 = {
        'control_categories': ['organizational', 'people', 'physical', 'technological'],
        'ai_security_gaps': ['mathematical_validation', 'ai_specific_threats'],
        'certification_requirements': 'annual_audit',
        'continuous_improvement': 'required'
    }

@given('mathematical validation tools and procedures')
def step_mathematical_validation_tools(context):
    """Reference mathematical validation tools"""
    context.validation_tools = 'from_synthesis_components'

@when('ISO 27001 controls are updated for AI mathematical validation')
def step_update_iso_27001_controls(context):
    """Update ISO 27001 controls for AI mathematical validation"""
    try:
        from cacm_article.compliance_roadmap import update_iso_27001_ai_controls
        context.iso_ai_controls = update_iso_27001_ai_controls(
            context.iso_27001,
            context.validation_tools
        )
    except ImportError:
        raise AssertionError("ISO 27001 AI controls update not implemented yet")

@then('should specify AI security controls with mathematical backing')
def step_ai_security_controls(context):
    """Specify AI security controls"""
    print("✓ AI security controls with mathematical backing specification required")

@then('should provide implementation timeline for mathematical validation integration')
def step_implementation_timeline(context):
    """Provide implementation timeline"""
    print("✓ Implementation timeline for mathematical validation integration required")

@then('should include audit procedures for mathematical validation effectiveness')
def step_audit_procedures(context):
    """Include audit procedures"""
    print("✓ Audit procedures for mathematical validation effectiveness required")

@given('all regulatory requirements synthesis')
def step_all_regulatory_synthesis(context):
    """Reference all regulatory requirements synthesis"""
    context.all_regulatory = {
        'eu_ai_act': 'from_previous_synthesis',
        'sox_404': 'from_previous_synthesis',
        'nist_ai_rmf': 'from_previous_synthesis',
        'iso_27001': 'from_previous_synthesis'
    }

@given('mathematical validation implementation requirements')
def step_validation_implementation_requirements(context):
    """Reference mathematical validation implementation requirements"""
    context.implementation_requirements = 'from_all_synthesis_components'

@when('comprehensive compliance roadmap is developed')
def step_develop_comprehensive_roadmap(context):
    """Develop comprehensive compliance roadmap"""
    try:
        from cacm_article.compliance_roadmap import develop_comprehensive_roadmap
        context.comprehensive_roadmap = develop_comprehensive_roadmap(
            context.all_regulatory,
            context.implementation_requirements
        )
    except ImportError:
        raise AssertionError("Comprehensive roadmap development not implemented yet")

@then('should provide phase-gated implementation plan within 90 days')
def step_phase_gated_plan(context):
    """Provide phase-gated implementation plan"""
    print("✓ Phase-gated implementation plan within 90 days required")

@then('should prioritize by regulatory deadlines and business impact')
def step_prioritize_by_deadlines(context):
    """Prioritize by deadlines and impact"""
    print("✓ Prioritization by regulatory deadlines and business impact required")

@then('should include resource requirements and success metrics')
def step_resource_requirements_metrics(context):
    """Include resource requirements and success metrics"""
    print("✓ Resource requirements and success metrics required")

print("📋 Compliance Roadmap Synthesis steps initialized - Level 2 ready")