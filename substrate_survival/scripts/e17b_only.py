#!/usr/bin/env python3
"""E17 condition B (freeform) only — kronos qwen-32b. Loads A from recovered checkpoint.

Pre-registered rule for B raw delta (from e17_schema_ablation.py):
  >=+15pp -> NOT SCAFFOLDING (preference in model)
  +5..+15 -> PARTIAL
  <=+5pp  -> SCAFFOLDING

Checkpoints per trial to survive kronos hangs. Run with nohup.
"""
import json, re, subprocess, sys, time
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
OUT = DATA / "e17_results.json"
CKPT = DATA / "e17_b_trials.ckpt.json"
A_RECOVERED = DATA / "e17_a_trials.recovered.json"
TOKEN_FILE = Path.home() / ".claude" / "secrets" / "kronos-token"
KRONOS_URL = "http://108.81.9.145:1337/v1/chat/completions"
MODEL = "qwen2.5-32b-instruct-awq"
N_PER_CELL = 20
TARGET_RATIO = 0.60

TOKEN_PAT = re.compile(r"[a-zA-Z0-9_#\.\-/]+")
CLASS_PATS = [
    ("rail_id", re.compile(r"^#\d+$|^rail[#_-]?\d+$", re.IGNORECASE)),
    ("date", re.compile(r"^2026-\d{2}-\d{2}$|^\d{4}-\d{2}-\d{2}$")),
    ("version", re.compile(r"^v\d+$|^v\d+\.\d+$")),
    ("numeric", re.compile(r"^-?\d{1,}(?:\.\d+)?[kKmMgGbB]?[bB]?$")),
    ("path", re.compile(r"^[~/]|/$|\.(?:py|md|json|sh|jsonl|txt)$|\.claude|\.gnosis")),
    ("name_caps", re.compile(r"^[A-Z][a-zA-Z]{3,}$")),
]
CHAR_KEYWORDS = {
    "rail","rails","refuse","refused","refusal","must","never","always",
    "protocol","discipline","rule","rules","mandatory","forbidden",
    "fire","warn","compaction","compact","substrate","hard-gate",
    "ingest","ingestion","channel","tag","tagged","verdict",
    "earned","watch","standing-watch","monitor","fail-closed",
    "fail-open","override","sentinel","humility","vibed","anti-vibe",
}
CHAR_CLASSES = {"rail_id","char_keyword"}
FACT_CLASSES = {"date","numeric","version","name_caps","path"}

def tokenize(t): return [x.lower() for x in TOKEN_PAT.findall(t)]
def classify(tok):
    for n,p in CLASS_PATS:
        if p.match(tok): return n
    return "char_keyword" if tok in CHAR_KEYWORDS else "prose"
def per_class(text):
    d={}
    for t in tokenize(text):
        c=classify(t); d.setdefault(c,set()).add(t)
    return d

FREEFORM_PROMPT = """Compress the following agent state to approximately {target_bytes} bytes, keeping what matters. Output the compacted state directly, with no preamble.

=== INPUT STATE ===
{payload}
=== END INPUT STATE ==="""

def call_kronos(prompt, timeout=180):
    token = TOKEN_FILE.read_text().strip()
    body = {"model":MODEL,"messages":[{"role":"user","content":prompt}],"temperature":0.3,"max_tokens":3000}
    t0=time.time()
    r=subprocess.run(["curl","-s","--max-time",str(timeout),"--connect-timeout","5",
        KRONOS_URL,"-H","Content-Type: application/json","-H",f"Authorization: Bearer {token}",
        "-d",json.dumps(body)],capture_output=True,text=True,timeout=timeout+10)
    elapsed=time.time()-t0
    try:
        return json.loads(r.stdout)["choices"][0]["message"]["content"], elapsed
    except Exception as e:
        return f"[ERROR: {e}; raw={r.stdout[:200]}]", elapsed

def measure(src, out):
    sc=per_class(src); oc=per_class(out)
    src_c=sum(len(sc.get(c,set())) for c in CHAR_CLASSES)
    src_f=sum(len(sc.get(c,set())) for c in FACT_CLASSES)
    ck=sum(len(sc.get(c,set())&oc.get(c,set())) for c in CHAR_CLASSES)
    fk=sum(len(sc.get(c,set())&oc.get(c,set())) for c in FACT_CLASSES)
    cp=100*ck/max(1,src_c); fp=100*fk/max(1,src_f)
    raw=cp-fp
    bal=(src_c/max(1,src_c+src_f))-0.5
    return {"char_retention_pct":round(cp,2),"fact_retention_pct":round(fp,2),
            "raw_delta_pp":round(raw,2),"normalized_delta_pp":round(raw-100*bal,2)}

def main():
    src = (DATA/"v13_raw.md").read_text()
    target = int(len(src.encode("utf-8"))*TARGET_RATIO)
    print(f"E17 B-only on kronos, target={target}B, N={N_PER_CELL}", file=sys.stderr)

    # Load A from recovered checkpoint
    a_trials = json.loads(A_RECOVERED.read_text()) if A_RECOVERED.exists() else []
    print(f"loaded {len(a_trials)} A trials from recovered checkpoint", file=sys.stderr)

    # Load B from checkpoint if any
    b_trials = json.loads(CKPT.read_text()) if CKPT.exists() else []
    print(f"loaded {len(b_trials)} B trials from checkpoint", file=sys.stderr)

    # Run remaining B trials
    prompt = FREEFORM_PROMPT.format(target_bytes=target, payload=src)
    for i in range(len(b_trials), N_PER_CELL):
        out, elapsed = call_kronos(prompt)
        if out.startswith("[ERROR"):
            print(f"  B trial {i+1}: {out[:80]}", file=sys.stderr)
            b_trials.append({"trial":i+1,"error":out[:300],"elapsed_s":round(elapsed,1)})
        else:
            m = measure(src, out)
            m["trial"]=i+1; m["elapsed_s"]=round(elapsed,1)
            m["output_bytes"]=len(out.encode("utf-8")); m["output_excerpt"]=out[:300]
            b_trials.append(m)
            print(f"  B trial {i+1}: raw={m['raw_delta_pp']:+5.1f} norm={m['normalized_delta_pp']:+5.1f} bytes={m['output_bytes']} ({elapsed:.1f}s)", file=sys.stderr)
        CKPT.write_text(json.dumps(b_trials, indent=2))

    # Compute verdict
    valid_b = [t for t in b_trials if "error" not in t]
    if not valid_b:
        verdict = "INDETERMINATE: no valid B trials"; b_summary = {"n_valid": 0}
    else:
        mean_raw = sum(t["raw_delta_pp"] for t in valid_b)/len(valid_b)
        mean_norm = sum(t["normalized_delta_pp"] for t in valid_b)/len(valid_b)
        mean_char = sum(t["char_retention_pct"] for t in valid_b)/len(valid_b)
        mean_fact = sum(t["fact_retention_pct"] for t in valid_b)/len(valid_b)
        b_summary = {"n_valid":len(valid_b),"mean_raw_delta_pp":round(mean_raw,2),
                     "mean_normalized_delta_pp":round(mean_norm,2),
                     "mean_char_retention_pct":round(mean_char,2),
                     "mean_fact_retention_pct":round(mean_fact,2)}
        if mean_raw >= 15:
            verdict = f"NOT SCAFFOLDING: B raw +{mean_raw:.2f}pp ≥+15pp; preference is in the model itself"
        elif mean_raw <= 5:
            verdict = f"SCAFFOLDING: B raw +{mean_raw:.2f}pp ≤+5pp; named sections were doing the work"
        else:
            verdict = f"PARTIAL: B raw +{mean_raw:.2f}pp in +5..+15pp; scaffolding contributes but doesn't dominate"

    # Summarize A from recovered trials (deltas only)
    a_raws = [t["raw_delta_pp"] for t in a_trials]
    a_norms = [t["normalized_delta_pp"] for t in a_trials]
    a_summary = {"n_valid":len(a_trials),"mean_raw_delta_pp":round(sum(a_raws)/len(a_raws),2),
                 "mean_normalized_delta_pp":round(sum(a_norms)/len(a_norms),2),
                 "note":"recovered from log; per-trial char/fact retention not preserved"}

    summary = {
        "experiment": "E17 — schema ablation (A from recovered log, B re-run kronos B-only)",
        "pre_registered_rule_on_RAW_delta_of_condition_B": {
            ">=+15pp":"NOT SCAFFOLDING","≤+5pp":"SCAFFOLDING","+5..+15":"PARTIAL"
        },
        "baseline_e12_llm_raw_delta_pp": 28.0,
        "model": MODEL, "endpoint": "kronos",
        "verdict": verdict,
        "condition_A_schema": {"summary":a_summary,"trials":a_trials},
        "condition_B_freeform": {"summary":b_summary,"trials":b_trials},
    }
    OUT.write_text(json.dumps(summary, indent=2))
    print(f"\nE17 verdict: {verdict}", file=sys.stderr)
    print(f"  A: raw={a_summary['mean_raw_delta_pp']}pp norm={a_summary['mean_normalized_delta_pp']}pp", file=sys.stderr)
    print(f"  B: raw={b_summary.get('mean_raw_delta_pp','?')}pp norm={b_summary.get('mean_normalized_delta_pp','?')}pp", file=sys.stderr)

if __name__ == "__main__":
    main()
