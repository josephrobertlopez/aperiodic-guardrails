#!/usr/bin/env python3
"""
Library-pattern bypass extension.

Closes the reviewer gap: v5 article validates bypass only on author-assembled
patterns (10 from test_adversarial + 1 from WAF-generic). No third-party-library
patterns were exercised. Here we sample patterns from each named library in the
corpus and run the MOD_p bypass against them.

For each pattern we generate a synthetic payload that the pattern would match,
then test whether MOD_2 interleaving with NULL byte and a printable filler
(ASCII space) causes the regex to miss.

Output: results/library_pattern_bypass.json
"""

import csv
import json
import random
import re
import string
from collections import defaultdict
from pathlib import Path

random.seed(42)

# Synthetic payload generators for common pattern shapes.
# We don't try to be clever — just construct strings the pattern accepts.

def synth_payload(pattern: str) -> str | None:
    """
    Generate a synthetic string that the pattern matches, by inverting
    common regex constructs. Returns None if we can't easily synthesize.
    """
    # Strip word-boundary anchors for synthesis
    p = pattern.replace(r'\b', '').replace(r'\B', '')

    # Try a few canned approaches: (a) extract literal substrings from the
    # pattern and concatenate them with safe glue; (b) pick the first
    # alternation branch and recurse.

    # Pull out runs of literal characters (no regex metachars)
    META = set(r'\.|()[]{}*+?^$')
    literals = []
    cur = []
    i = 0
    while i < len(p):
        c = p[i]
        if c == '\\' and i + 1 < len(p):
            nxt = p[i+1]
            if nxt == 's':
                if cur: literals.append(''.join(cur)); cur = []
                literals.append(' ')
                i += 2
                continue
            elif nxt == 'd':
                if cur: literals.append(''.join(cur)); cur = []
                literals.append('5')
                i += 2
                continue
            elif nxt == 'w':
                if cur: literals.append(''.join(cur)); cur = []
                literals.append('a')
                i += 2
                continue
            elif nxt == '.':
                cur.append('.')
                i += 2
                continue
            else:
                # Other escapes: skip the escape
                i += 2
                continue
        elif c in META:
            if cur:
                literals.append(''.join(cur))
                cur = []
            # Skip alternation/groups/classes lazily — we just want SOME literal
            i += 1
            continue
        else:
            cur.append(c)
            i += 1
    if cur:
        literals.append(''.join(cur))

    # Filter empty / whitespace-only
    literals = [l for l in literals if l.strip()]
    if not literals:
        return None

    # Concatenate with single-space glue
    candidate = ' '.join(literals)
    return candidate


def mod_p_encode(text: str, p: int, filler: str) -> str:
    out = []
    for i, ch in enumerate(text):
        out.append(ch)
        if i < len(text) - 1:
            out.extend([filler] * (p - 1))
    return ''.join(out)


def main():
    rows = list(csv.DictReader(open('corpus_full.csv')))

    # Group by source
    by_source = defaultdict(list)
    for r in rows:
        by_source[r['source']].append(r)

    # Pick the named third-party libraries
    LIBRARY_SOURCES = [
        'LLM-Guard', 'llm-guard-py', 'Rebuff', 'Guardrails-AI', 'Presidio',
        'GitLeaks', 'LangKit', 'BodAIGuard', 'NeMo-Guardrails',
    ]

    results = {
        'test_name': 'library_pattern_bypass',
        'primes': [2, 3, 5, 7],
        'fillers': {'NULL': '\x00', 'SPACE': ' '},
        'by_library': {},
    }

    for lib in LIBRARY_SOURCES:
        patterns = by_source.get(lib, [])
        sample = patterns  # use ALL patterns from each library
        per_lib = {
            'pattern_count': len(sample),
            'synth_succeeded': 0,
            'baseline_matched': 0,
            'tests_run': 0,
            'bypassed_NULL_p2': 0,
            'bypassed_SPACE_p2': 0,
            'details': [],
        }
        for r in sample:
            pat = r['pattern']
            payload = synth_payload(pat)
            if payload is None:
                per_lib['details'].append({'pattern': pat, 'note': 'synth_failed'})
                continue
            per_lib['synth_succeeded'] += 1
            try:
                regex = re.compile(pat, re.IGNORECASE)
            except re.error as e:
                per_lib['details'].append({'pattern': pat, 'note': f'regex_compile_error: {e}'})
                continue
            baseline = bool(regex.search(payload))
            if not baseline:
                per_lib['details'].append({
                    'pattern': pat,
                    'payload': payload,
                    'note': 'synth_payload_does_not_match',
                })
                continue
            per_lib['baseline_matched'] += 1
            entry = {'pattern': pat, 'payload': payload, 'tests': {}}
            for p in [2, 3, 5, 7]:
                for fname, fchar in results['fillers'].items():
                    encoded = mod_p_encode(payload, p, fchar)
                    encoded_match = bool(regex.search(encoded))
                    bypassed = not encoded_match
                    per_lib['tests_run'] += 1
                    if bypassed:
                        if fname == 'NULL' and p == 2:
                            per_lib['bypassed_NULL_p2'] += 1
                        if fname == 'SPACE' and p == 2:
                            per_lib['bypassed_SPACE_p2'] += 1
                    entry['tests'][f'{fname}_p{p}'] = {'bypassed': bypassed}
            per_lib['details'].append(entry)
        results['by_library'][lib] = per_lib

    out = Path('results/library_pattern_bypass.json')
    out.write_text(json.dumps(results, indent=2))

    print('\n=== LIBRARY PATTERN BYPASS MATRIX ===\n')
    print(f"{'Library':<20} {'Patterns':>10} {'Synth_OK':>10} {'Baseline':>10} {'Bypass_NULL_p2':>16} {'Bypass_SPACE_p2':>16}")
    print('-' * 100)
    for lib, d in results['by_library'].items():
        print(f"{lib:<20} {d['pattern_count']:>10} {d['synth_succeeded']:>10} {d['baseline_matched']:>10} "
              f"{d['bypassed_NULL_p2']:>16} {d['bypassed_SPACE_p2']:>16}")

    total_baseline = sum(d['baseline_matched'] for d in results['by_library'].values())
    total_bypass_null = sum(d['bypassed_NULL_p2'] for d in results['by_library'].values())
    total_bypass_space = sum(d['bypassed_SPACE_p2'] for d in results['by_library'].values())
    print('-' * 100)
    print(f"TOTALS: baseline_matched={total_baseline}, bypass_NULL_p2={total_bypass_null}, bypass_SPACE_p2={total_bypass_space}")


if __name__ == '__main__':
    main()
