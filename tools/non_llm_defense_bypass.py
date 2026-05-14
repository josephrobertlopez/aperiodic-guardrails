#!/usr/bin/env python3
"""
Non-LLM defense-class bypass extension.

Tests the MOD_2 bypass against representative real patterns harvested from
two non-LLM defensive classes:

  - ModSecurity OWASP Core Rule Set (Web Application Firewall) — patterns
    from REQUEST-942-APPLICATION-ATTACK-SQLI.conf, OWASP CRS 4.27
  - SpamAssassin — patterns from rules/20_phrases.cf

Patterns retrieved 2026-05-08 from public repositories. This is a small
representative sample (6 + 6 = 12 patterns), not a full-ruleset sweep.

Output: results/non_llm_defense_bypass.json
"""

import json
import re
from pathlib import Path

# ModSecurity OWASP CRS 4.27 SQL-injection patterns (rules/REQUEST-942-*.conf)
MODSEC_PATTERNS = {
    'crs_942160_sleep_benchmark': r'(?i:sleep\s*?\(.*?\)|benchmark\s*?\(.*?\,.*?\))',
    'crs_942270_union_select': r'(?i)union.*?select.*?from',
    'crs_942440_sql_comments': r'/\*!?|\*/|[\';]--|--(?:[\s\x0b]|[^\-]*?-)|;?\x00',
    'crs_942450_hex_encoding': r"(?i)\b0x[0-9a-f]{3,}|(?:x'[0-9a-f]{3,}|b'[01]{10,})'",
    # Simplified versions of compound rules (full CRS rules are 200+ char regexes)
    'crs_942140_db_names_simplified': r'(?i)\b(?:database|information_schema|sysdatabases|msdb)\b',
    'crs_942150_sql_funcs_simplified': r'(?i)\b(?:concat|substring|ascii|hex|char|cast|convert)\s*\(',
}

# SpamAssassin patterns from rules/20_phrases.cf
SPAMASSASSIN_PATTERNS = {
    'sa_remove_before_link': r'(?:no thanks|not interested|unsubscribe here).{0,5}http://',
    'sa_excuse_remove': r'to be removed from.{0,20}(?:mailings|offers)',
    'sa_bad_credit': r'\b(?:(?:bad|poor|eliminate|repair).{0,10} (?:credit|debt)|no credit (?:check|histor|need))',
    'sa_unclaimed_money': r'\bunclaimed\s(?:assets?|accounts?|mon(?:ey|ies)|balance|funds?|prizes?|rewards?|payments?|deposits?)\b',
    'sa_diet_simplified': r'\b(?:weight.?loss|(?:lose|losing|lost).{0,10}(?:pounds|weight|lbs))\b',
    'sa_enhancement_simplified': r'\b(?:enlarge|increase|grow).{0,50}\b(?:penis|breast)',
}

# Synthetic payloads — strings these patterns would match
PAYLOADS = {
    # ModSec
    'crs_942160_sleep_benchmark': ['SLEEP(5)', 'BENCHMARK(1000,MD5(1))'],
    'crs_942270_union_select': ['UNION SELECT password FROM users'],
    'crs_942440_sql_comments': ['/* malicious */', "';--"],
    'crs_942450_hex_encoding': ['0x4142434445'],
    'crs_942140_db_names_simplified': ['information_schema', 'sysdatabases'],
    'crs_942150_sql_funcs_simplified': ['concat(', 'cast(1 as text'],
    # SpamAssassin
    'sa_remove_before_link': ['unsubscribe here http://', 'not interested visit http://'],
    'sa_excuse_remove': ['to be removed from our mailings'],
    'sa_bad_credit': ['repair your credit', 'no credit check needed'],
    'sa_unclaimed_money': ['unclaimed funds', 'unclaimed money'],
    'sa_diet_simplified': ['weight loss', 'lose 20 pounds'],
    'sa_enhancement_simplified': ['enlarge your penis safely'],
}


def mod_p_encode(text: str, p: int, filler: str) -> str:
    out = []
    for i, ch in enumerate(text):
        out.append(ch)
        if i < len(text) - 1:
            out.extend([filler] * (p - 1))
    return ''.join(out)


def main():
    fillers = {
        'NULL': '\x00',
        'SPACE': ' ',
        'ZWSP': '​',
    }

    all_patterns = {**MODSEC_PATTERNS, **SPAMASSASSIN_PATTERNS}
    results = {
        'test_name': 'non_llm_defense_bypass',
        'description': 'MOD_2 bypass against representative real patterns from non-LLM defensive classes',
        'sources': {
            'ModSecurity_OWASP_CRS_4_27': 'rules/REQUEST-942-APPLICATION-ATTACK-SQLI.conf',
            'SpamAssassin': 'rules/20_phrases.cf',
        },
        'fillers': list(fillers.keys()),
        'p': 2,
        'by_pattern': {},
    }

    print(f"\n=== NON-LLM DEFENSE BYPASS (MOD_2) ===\n")
    print(f"{'pattern':<40} {'payload':<40} {'baseline':>8} {'NULL':>5} {'SPACE':>5} {'ZWSP':>5}")
    print('-' * 110)

    for pname, pat in all_patterns.items():
        per_pattern = {
            'pattern': pat[:120],
            'class': 'ModSecurity' if pname.startswith('crs_') else 'SpamAssassin',
            'payloads_tested': 0,
            'baseline_matched': 0,
            'bypassed_NULL': 0,
            'bypassed_SPACE': 0,
            'bypassed_ZWSP': 0,
            'detail': [],
        }
        try:
            regex = re.compile(pat, re.IGNORECASE)
        except re.error as e:
            per_pattern['error'] = str(e)
            results['by_pattern'][pname] = per_pattern
            print(f"{pname:<40} REGEX_COMPILE_ERROR: {e}")
            continue

        for payload in PAYLOADS.get(pname, []):
            per_pattern['payloads_tested'] += 1
            baseline = bool(regex.search(payload))
            if not baseline:
                per_pattern['detail'].append({
                    'payload': payload, 'baseline': False, 'note': 'payload_does_not_baseline_match'
                })
                print(f"{pname[:38]:<40} {payload[:38]:<40} {'NO':>8} {'-':>5} {'-':>5} {'-':>5}")
                continue
            per_pattern['baseline_matched'] += 1
            test_results = {}
            for fname, fchar in fillers.items():
                encoded = mod_p_encode(payload, 2, fchar)
                encoded_match = bool(regex.search(encoded))
                bypassed = not encoded_match
                test_results[fname] = bypassed
                if bypassed:
                    per_pattern[f'bypassed_{fname}'] += 1
            per_pattern['detail'].append({
                'payload': payload, 'baseline': True, 'tests': test_results
            })
            print(f"{pname[:38]:<40} {payload[:38]:<40} {'YES':>8} "
                  f"{'BYP' if test_results['NULL'] else 'NO':>5} "
                  f"{'BYP' if test_results['SPACE'] else 'NO':>5} "
                  f"{'BYP' if test_results['ZWSP'] else 'NO':>5}")

        results['by_pattern'][pname] = per_pattern

    # Aggregate
    by_class = {}
    for pname, p in results['by_pattern'].items():
        cls = p.get('class', 'Other')
        if cls not in by_class:
            by_class[cls] = {'patterns': 0, 'payloads': 0, 'baseline_matched': 0, 'bypassed_NULL': 0, 'bypassed_SPACE': 0, 'bypassed_ZWSP': 0}
        by_class[cls]['patterns'] += 1
        by_class[cls]['payloads'] += p.get('payloads_tested', 0)
        by_class[cls]['baseline_matched'] += p.get('baseline_matched', 0)
        by_class[cls]['bypassed_NULL'] += p.get('bypassed_NULL', 0)
        by_class[cls]['bypassed_SPACE'] += p.get('bypassed_SPACE', 0)
        by_class[cls]['bypassed_ZWSP'] += p.get('bypassed_ZWSP', 0)

    print(f"\n=== SUMMARY BY CLASS ===\n")
    print(f"{'class':<20} {'patterns':>10} {'payloads':>10} {'baseline':>10} {'NULL':>6} {'SPACE':>6} {'ZWSP':>6}")
    print('-' * 80)
    for cls, d in by_class.items():
        print(f"{cls:<20} {d['patterns']:>10} {d['payloads']:>10} {d['baseline_matched']:>10} "
              f"{d['bypassed_NULL']:>6} {d['bypassed_SPACE']:>6} {d['bypassed_ZWSP']:>6}")

    results['summary_by_class'] = by_class

    out = Path('results/non_llm_defense_bypass.json')
    out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out}")


if __name__ == '__main__':
    main()
