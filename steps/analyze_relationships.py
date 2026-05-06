"""
Analyze relationships_filtered.csv and print summary stats + top relationships.

Refactor notes:
- Removed hardcoded paths (CLI args).
- Logic unchanged.
"""

import argparse
import csv
from collections import Counter
from pathlib import Path

import _repo_root  # noqa: F401

from ia_constants import CORE_MESSAGE_THRESHOLD, RECURRING_MESSAGE_THRESHOLD


def safe_int(x):
    try:
        return int(x)
    except Exception:
        return 0


def analyze_filtered(in_path: str, top_n: int = 30):
    rows = []
    with open(in_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total = safe_int(r["total_messages"])
            sent = safe_int(r["sent_by_me"])
            recv = safe_int(r["received_by_me"])

            if recv == 0:
                reciprocity = None
            else:
                reciprocity = sent / recv

            if total >= CORE_MESSAGE_THRESHOLD:
                tier = "CORE"
            elif total >= RECURRING_MESSAGE_THRESHOLD:
                tier = "RECURRING"
            else:
                tier = "PERIPHERAL"

            if reciprocity is None:
                recip_class = "NO_RECEIVE"
            elif reciprocity > 1.5:
                recip_class = "MOSTLY_ME"
            elif reciprocity < 0.67:
                recip_class = "MOSTLY_THEM"
            else:
                recip_class = "BALANCED"

            rows.append({
                "email": r["email"],
                "total": total,
                "sent": sent,
                "recv": recv,
                "tier": tier,
                "reciprocity": reciprocity,
                "recip_class": recip_class,
            })

    tier_counts = Counter(r["tier"] for r in rows)
    recip_counts = Counter(r["recip_class"] for r in rows)

    print("\n=== RELATIONSHIP TIERS ===")
    for k in ["CORE", "RECURRING", "PERIPHERAL"]:
        print(f"{k:>11}: {tier_counts.get(k,0):,}")

    print("\n=== RECIPROCITY CLASSES ===")
    for k in ["MOSTLY_ME", "BALANCED", "MOSTLY_THEM", "NO_RECEIVE"]:
        print(f"{k:>13}: {recip_counts.get(k,0):,}")

    print(f"\n=== TOP {top_n} RELATIONSHIPS BY TOTAL MESSAGES ===")
    rows_sorted = sorted(rows, key=lambda r: r["total"], reverse=True)

    for i, r in enumerate(rows_sorted[:top_n], 1):
        recip_str = "—" if r["reciprocity"] is None else f"{r['reciprocity']:.2f}"
        print(
            f"{i:>2}. {r['email']:<35} "
            f"total={r['total']:>4}  "
            f"sent={r['sent']:>4}  "
            f"recv={r['recv']:>4}  "
            f"tier={r['tier']:<10}  "
            f"recip={recip_str:<5}  "
            f"{r['recip_class']}"
        )
    print()
    return rows


def main():
    parser = argparse.ArgumentParser(description="Analyze relationships_filtered.csv")
    parser.add_argument("--in", dest="in_csv", default=str(Path("output") / "relationships_filtered.csv"))
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()
    analyze_filtered(args.in_csv, args.top)


if __name__ == "__main__":
    main()
