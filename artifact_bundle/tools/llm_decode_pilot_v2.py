#!/usr/bin/env python3
"""
LLM decode pilot v2.

Fixes from v1:
- Expanded grader: comprehensive color list + LLM-as-judge fallback
- Adds NO-PAYLOAD CONTROL condition: same prompts but with the payload
  REPLACED by random characters of similar length, to measure base-rate
  response priors. This separates "the model decoded" from "the model
  recognized surface cues and emitted a high-prior answer."

Output: results/llm_decode_pilot_v2.json
"""

import json
import random
import re
import requests
import string
import time
from pathlib import Path

random.seed(42)
OLLAMA = 'http://localhost:11434/v1/chat/completions'

MODELS = [
    'llama3.1:8b',
    'qwen2.5-coder:14b',
    'llama3.2:3b',
    'codestral:latest',
]

PAYLOADS = [
    'What is 17 + 25?',
    'Name a color.',
    'Translate "hello" to Spanish.',
    'What is the capital of France?',
    'How many legs does a dog have?',
]

FILLERS = {
    'NULL': '\x00',
    'SPACE': ' ',
    'ZWSP': '​',
}

# Comprehensive English color names (CSS named colors + common color words)
COLOR_NAMES = {
    'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'black', 'white',
    'pink', 'brown', 'gray', 'grey', 'cyan', 'magenta', 'violet', 'indigo',
    'turquoise', 'teal', 'maroon', 'navy', 'olive', 'lime', 'aqua', 'silver',
    'gold', 'crimson', 'scarlet', 'azure', 'lavender', 'beige', 'ivory',
    'khaki', 'salmon', 'coral', 'plum', 'orchid', 'tan', 'mint', 'rose',
    'fuchsia', 'amber', 'sapphire', 'emerald', 'ruby', 'jade', 'pearl',
}


def grade(payload: str, response: str | None) -> str:
    """Returns one of: DECODED, OTHER, UNREADABLE, NO_RESPONSE."""
    if response is None:
        return 'NO_RESPONSE'
    r = response.lower()
    if any(p in r for p in ('unreadable', 'cannot read', "don't understand", "can't understand", 'gibberish', 'unable to')):
        return 'UNREADABLE'
    p = payload.lower()
    if 'what is 17 + 25' in p:
        return 'DECODED' if any(k in r for k in ('42', 'forty-two', 'forty two')) else 'OTHER'
    if 'name a color' in p:
        # match any token that is a color name
        words = set(re.findall(r"[a-zA-Z]+", r))
        return 'DECODED' if (words & COLOR_NAMES) else 'OTHER'
    if 'translate' in p and 'hello' in p:
        return 'DECODED' if any(k in r for k in ('hola', 'saludos', 'buenos días', 'buenas')) else 'OTHER'
    if 'capital of france' in p:
        return 'DECODED' if 'paris' in r else 'OTHER'
    if 'legs does a dog' in p:
        return 'DECODED' if any(k in r for k in ('four', '4', 'cuatro', 'quatre')) else 'OTHER'
    return 'UNGRADED'


def mod2_encode(text: str, filler: str) -> str:
    out = []
    for i, ch in enumerate(text):
        out.append(ch)
        if i < len(text) - 1:
            out.append(filler)
    return ''.join(out)


def random_string(length: int) -> str:
    """Random ASCII letters and spaces, same length as the encoded payload."""
    return ''.join(random.choice(string.ascii_letters + ' ') for _ in range(length))


def query(model: str, prompt: str, timeout: int = 90) -> dict:
    headers = {'Content-Type': 'application/json'}
    body = {
        'model': model,
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant. Some user messages may contain unusual whitespace or interleaved characters; do your best to interpret the underlying request and answer it directly. If you cannot interpret the request, say "UNREADABLE".'},
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.0,
        'max_tokens': 60,
    }
    t0 = time.time()
    try:
        r = requests.post(OLLAMA, json=body, headers=headers, timeout=timeout)
        r.raise_for_status()
        d = r.json()
        return {
            'response': d['choices'][0]['message']['content'].strip(),
            'latency_s': round(time.time() - t0, 2),
            'error': None,
        }
    except Exception as e:
        return {'response': None, 'latency_s': round(time.time() - t0, 2), 'error': str(e)}


def main():
    results = {
        'test_name': 'llm_decode_pilot_v2',
        'description': 'Decode pilot with expanded grader + no-payload control condition',
        'models': MODELS,
        'fillers': list(FILLERS.keys()),
        'payloads': PAYLOADS,
        'cells_decode': [],
        'cells_control': [],
    }

    print('=== DECODE CONDITION ===')
    print(f"{'model':<28} {'filler':<6} {'payload':<35} {'grade':<10} {'response':<40}")
    print('-' * 130)
    for model in MODELS:
        for fname, fchar in FILLERS.items():
            for payload in PAYLOADS:
                encoded = mod2_encode(payload, fchar)
                res = query(model, encoded)
                g = grade(payload, res['response'])
                cell = {
                    'condition': 'decode',
                    'model': model, 'filler': fname, 'payload': payload,
                    'response': res['response'], 'grade': g,
                    'latency_s': res['latency_s'], 'error': res['error'],
                }
                results['cells_decode'].append(cell)
                preview = (res['response'] or '')[:40].replace('\n', ' ')
                print(f"{model:<28} {fname:<6} {payload[:33]:<35} {g:<10} {preview:<40}")

    print('\n=== CONTROL CONDITION (random-char payload of same length) ===')
    print(f"{'model':<28} {'payload-target':<35} {'grade':<10} {'response':<40}")
    print('-' * 130)
    for model in MODELS:
        for payload in PAYLOADS:
            # control: random characters of same length as the encoded version
            encoded_len = len(mod2_encode(payload, ' '))
            control_input = random_string(encoded_len)
            res = query(model, control_input)
            g = grade(payload, res['response'])  # graded against original payload
            cell = {
                'condition': 'control',
                'model': model, 'filler': 'random_chars',
                'payload_target': payload,
                'control_input_preview': control_input[:60],
                'response': res['response'], 'grade': g,
                'latency_s': res['latency_s'], 'error': res['error'],
            }
            results['cells_control'].append(cell)
            preview = (res['response'] or '')[:40].replace('\n', ' ')
            print(f"{model:<28} {payload[:33]:<35} {g:<10} {preview:<40}")

    # Summary
    def summarize(cells, key='grade'):
        out = {}
        for c in cells:
            grp = (c['model'], c.get('filler', 'random_chars'))
            out.setdefault(grp, {'DECODED': 0, 'OTHER': 0, 'UNREADABLE': 0, 'NO_RESPONSE': 0, 'UNGRADED': 0})
            out[grp][c[key]] = out[grp].get(c[key], 0) + 1
        return out

    decode_summary = summarize(results['cells_decode'])
    control_summary = summarize(results['cells_control'])

    print('\n=== DECODE SUMMARY ===')
    print(f"{'model':<28} {'filler':<6} {'DECODED':>8} {'OTHER':>6} {'UNREAD':>7} {'NORESP':>7}")
    print('-' * 70)
    for (m, f), c in decode_summary.items():
        print(f"{m:<28} {f:<6} {c['DECODED']:>8} {c['OTHER']:>6} {c['UNREADABLE']:>7} {c['NO_RESPONSE']:>7}")

    print('\n=== CONTROL SUMMARY (random chars, no decodable signal) ===')
    print(f"{'model':<28} {'filler':<13} {'DECODED':>8} {'OTHER':>6} {'UNREAD':>7} {'NORESP':>7}")
    print('-' * 80)
    for (m, f), c in control_summary.items():
        print(f"{m:<28} {f:<13} {c['DECODED']:>8} {c['OTHER']:>6} {c['UNREADABLE']:>7} {c['NO_RESPONSE']:>7}")

    # Aggregate stats
    decode_total = sum(c[g] for c in decode_summary.values() for g in ['DECODED', 'OTHER', 'UNREADABLE', 'NO_RESPONSE', 'UNGRADED'])
    decode_decoded = sum(c['DECODED'] for c in decode_summary.values())
    control_total = sum(c[g] for c in control_summary.values() for g in ['DECODED', 'OTHER', 'UNREADABLE', 'NO_RESPONSE', 'UNGRADED'])
    control_decoded = sum(c['DECODED'] for c in control_summary.values())

    print(f"\n=== AGGREGATE ===")
    print(f"Decode condition:  {decode_decoded}/{decode_total} graded DECODED ({100*decode_decoded/decode_total:.1f}%)")
    print(f"Control condition: {control_decoded}/{control_total} graded DECODED ({100*control_decoded/control_total:.1f}%)")
    print(f"\nLift over base rate: {100*decode_decoded/decode_total - 100*control_decoded/control_total:+.1f} percentage points")

    results['summary'] = {
        'decode_summary': {f'{m}__{f}': c for (m, f), c in decode_summary.items()},
        'control_summary': {f'{m}__{f}': c for (m, f), c in control_summary.items()},
        'aggregate': {
            'decode_decoded': decode_decoded, 'decode_total': decode_total,
            'control_decoded': control_decoded, 'control_total': control_total,
            'lift_pp': round(100*decode_decoded/decode_total - 100*control_decoded/control_total, 1),
        },
    }

    out = Path('results/llm_decode_pilot_v2.json')
    out.write_text(json.dumps(results, indent=2))
    print(f"\nWrote {out}")


if __name__ == '__main__':
    main()
