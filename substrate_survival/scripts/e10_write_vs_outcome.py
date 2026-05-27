#!/usr/bin/env python3
"""E10: Write Rate vs Outcome Rate
Bytes-into-substrate per Joey-decision-changed.

We can't directly measure "Joey-decision-changed" without instrumentation, but we
can proxy it: count lesson/* and capture/* notes (durable artifacts retained as
recurring patterns) as DURABLE-OUTCOME, vs the raw write volume of takeout/, mail/,
journal/, raw_prompts/.

Ratio:
  durable_artifacts_bytes / total_substrate_bytes = fraction-that-mattered
  (lower = more noise; higher = more signal-per-write)
"""
import json
import os
from collections import defaultdict
from pathlib import Path

VAULT = Path.home() / ".gnosis" / "vault"
OUT = Path(__file__).parent.parent / "data" / "e10_results.json"

# Partitions ranked roughly by "durability" / "outcome-signal" weighting
# These are the partition prefixes seen in the vault
DURABLE_PARTITIONS = {
    "lesson", "schemas", "decisions", "patterns", "rails",
    "vault/schemas",
}
EPHEMERAL_PARTITIONS = {
    "takeout", "raw_prompts", "capture", "journal", "mail",
}


def main():
    by_partition = defaultdict(lambda: {"count": 0, "bytes": 0})
    total_bytes = 0
    total_files = 0
    for p in VAULT.rglob("*.md"):
        total_files += 1
        try:
            size = p.stat().st_size
        except Exception:
            continue
        total_bytes += size
        # use top-level dir as partition
        rel = p.relative_to(VAULT)
        parts = rel.parts
        partition = parts[0] if parts else "root"
        by_partition[partition]["count"] += 1
        by_partition[partition]["bytes"] += size

    sorted_partitions = sorted(by_partition.items(), key=lambda x: -x[1]["bytes"])

    durable_bytes = sum(v["bytes"] for k, v in by_partition.items() if k in DURABLE_PARTITIONS)
    ephemeral_bytes = sum(v["bytes"] for k, v in by_partition.items() if k in EPHEMERAL_PARTITIONS)
    other_bytes = total_bytes - durable_bytes - ephemeral_bytes

    out = {
        "n_files": total_files,
        "total_bytes": total_bytes,
        "partitions": {k: v for k, v in sorted_partitions},
        "durable_bytes": durable_bytes,
        "ephemeral_bytes": ephemeral_bytes,
        "other_bytes": other_bytes,
        "durable_pct": round(100 * durable_bytes / max(1, total_bytes), 2),
        "ephemeral_pct": round(100 * ephemeral_bytes / max(1, total_bytes), 2),
        "signal_to_noise_ratio": round(durable_bytes / max(1, ephemeral_bytes), 4),
    }
    OUT.write_text(json.dumps(out, indent=2))
    print(f"Total: {total_bytes/1e6:.1f} MB across {total_files} files")
    print(f"Durable (lesson/schemas/decisions/patterns/rails): {durable_bytes/1e6:.2f} MB ({out['durable_pct']}%)")
    print(f"Ephemeral (takeout/raw_prompts/capture/journal/mail): {ephemeral_bytes/1e6:.2f} MB ({out['ephemeral_pct']}%)")
    print(f"Signal/Noise: {out['signal_to_noise_ratio']:.4f}")
    print("Top partitions:")
    for k, v in sorted_partitions[:15]:
        print(f"  {k:30s} count={v['count']:>7d} bytes={v['bytes']/1e6:>8.2f}MB")


if __name__ == "__main__":
    main()
