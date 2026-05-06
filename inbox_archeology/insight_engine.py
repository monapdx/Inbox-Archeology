"""
Deterministic insight generation from relationships_clean.csv and optional core_timeline.csv.

Uses the same reciprocity and tier thresholds as the dashboard (via ia_constants / mirrored logic).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ia_constants import CORE_MESSAGE_THRESHOLD, tier_from_total

# --- Mirrors dashboard.recip_class (avoid importing Streamlit in subprocess steps) ---


def recip_class(sent: int, recv: int) -> str:
    if recv == 0:
        return "NO_RECEIVE"
    r = sent / recv
    if r > 1.5:
        return "MOSTLY_ME"
    if r < 0.67:
        return "MOSTLY_THEM"
    return "BALANCED"


IMPORTANCE_RANK = {"high": 3, "medium": 2, "low": 1}

MIN_MESSAGES_ONE_SIDED = 10
MIN_MESSAGES_FADED = 10
MIN_MESSAGES_OUTLIER = 15
FADE_GAP_DAYS = 730  # ~2 years before dataset max(last_contact)
OUTLIER_RATIO_HIGH = 5.0
OUTLIER_RATIO_LOW = 0.2
MAX_INSIGHTS = 20

_LIMITS = {
    "core": 1,
    "reciprocity": 4,
    "lifecycle": 3,
    "volume": 1,
    "temporal": 1,
    "outliers": 2,
}


def _json_safe(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.bool_):
        return bool(obj)
    if pd.isna(obj):
        return None
    return obj


def _norm_rel_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["total_messages"] = pd.to_numeric(out["total_messages"], errors="coerce").fillna(0).astype(int)
    out["sent_by_me"] = pd.to_numeric(out["sent_by_me"], errors="coerce").fillna(0).astype(int)
    out["received_by_me"] = pd.to_numeric(out["received_by_me"], errors="coerce").fillna(0).astype(int)
    out["first_contact"] = pd.to_datetime(out["first_contact"], errors="coerce", utc=True)
    out["last_contact"] = pd.to_datetime(out["last_contact"], errors="coerce", utc=True)
    out["tier"] = out["total_messages"].apply(tier_from_total)
    out["recip_ratio"] = np.where(
        out["received_by_me"] == 0,
        np.nan,
        out["sent_by_me"] / out["received_by_me"].replace(0, np.nan),
    )
    out["recip_class"] = [
        recip_class(int(s), int(r)) for s, r in zip(out["sent_by_me"], out["received_by_me"])
    ]
    out["duration_days"] = (out["last_contact"] - out["first_contact"]).dt.days
    out["duration_years"] = pd.to_numeric(out["duration_days"], errors="coerce") / 365.25
    return out


def _overlap_peak_year(timeline_df: pd.DataFrame) -> tuple[int, int, dict[int, int]] | None:
    """Return (peak_year, peak_count, full_counts) from CORE timeline rows."""
    if timeline_df.empty:
        return None
    tl = timeline_df.copy()
    tl["start"] = pd.to_datetime(tl["start"], errors="coerce", utc=True)
    tl["end"] = pd.to_datetime(tl["end"], errors="coerce", utc=True)
    tl = tl.dropna(subset=["start", "end"])
    if tl.empty:
        return None
    counts: Counter[int] = Counter()
    for _, row in tl.iterrows():
        sy = int(row["start"].year)
        ey = int(row["end"].year)
        if sy > ey:
            sy, ey = ey, sy
        for y in range(sy, ey + 1):
            counts[y] += 1
    if not counts:
        return None
    peak_year = max(counts, key=lambda y: (counts[y], y))
    return peak_year, counts[peak_year], dict(sorted(counts.items()))


def generate_insights(relationships_csv: str, timeline_csv: str | None, out_path: str) -> dict:
    """
    Load CSVs, build deterministic insights, write JSON to out_path, return parsed dict.

    Structure returned and written:
        {"insights": [ {...}, ... ]}
    """
    rel_path = Path(relationships_csv)
    if not rel_path.is_file():
        payload = {"insights": []}
        outp = Path(out_path)
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload

    df = pd.read_csv(rel_path)
    df = _norm_rel_df(df)

    timeline_df: pd.DataFrame | None = None
    if timeline_csv:
        tp = Path(timeline_csv)
        if tp.is_file():
            timeline_df = pd.read_csv(tp)

    insights: list[dict[str, Any]] = []
    per_cat: Counter[str] = Counter()

    def add(ins: dict[str, Any]) -> None:
        cat = ins.get("category", "")
        if per_cat[cat] >= _LIMITS.get(cat, 99):
            return
        per_cat[cat] += 1
        insights.append(ins)

    # --- 1) Core relationships (top 5 CORE by volume, single aggregate insight) ---
    core_rows = df[df["tier"] == "CORE"].sort_values("total_messages", ascending=False).head(5)
    if not core_rows.empty:
        contacts = []
        for _, row in core_rows.iterrows():
            contacts.append(
                {
                    "email": row["email"] if isinstance(row["email"], str) else str(row["email"]),
                    "total_messages": int(row["total_messages"]),
                }
            )
        add(
            {
                "title": "Core relationships",
                "category": "core",
                "importance": "high",
                "email": None,
                "evidence": {
                    "threshold_messages_for_core": CORE_MESSAGE_THRESHOLD,
                    "top_contacts": contacts,
                    "count_shown": len(contacts),
                },
                "interpretation": "These people were central to your communication history.",
            }
        )

    # --- 2) One-sided (mostly me) ---
    mostly_me = df[
        (df["recip_class"] == "MOSTLY_ME")
        & (df["total_messages"] >= MIN_MESSAGES_ONE_SIDED)
        & (df["received_by_me"] > 0)
    ].sort_values("recip_ratio", ascending=False)
    for _, row in mostly_me.head(2).iterrows():
        email_s = row["email"] if isinstance(row["email"], str) else str(row["email"])
        rr = float(row["recip_ratio"]) if pd.notna(row["recip_ratio"]) else None
        if per_cat["reciprocity"] >= _LIMITS["reciprocity"]:
            break
        add(
            {
                "title": "Mostly your outreach",
                "category": "reciprocity",
                "importance": "medium",
                "email": email_s,
                "evidence": _json_safe(
                    {
                        "sent_by_me": int(row["sent_by_me"]),
                        "received_by_me": int(row["received_by_me"]),
                        "total_messages": int(row["total_messages"]),
                        "sent_per_received_ratio": rr,
                    }
                ),
                "interpretation": "You were doing most of the reaching out.",
            }
        )

    # --- 3) One-sided (mostly them) ---
    mostly_them = df[
        (df["recip_class"] == "MOSTLY_THEM")
        & (df["total_messages"] >= MIN_MESSAGES_ONE_SIDED)
        & (df["received_by_me"] > 0)
    ].sort_values("recip_ratio", ascending=True)
    for _, row in mostly_them.head(2).iterrows():
        email_s = row["email"] if isinstance(row["email"], str) else str(row["email"])
        rr = float(row["recip_ratio"]) if pd.notna(row["recip_ratio"]) else None
        if per_cat["reciprocity"] >= _LIMITS["reciprocity"]:
            break
        add(
            {
                "title": "Mostly their outreach",
                "category": "reciprocity",
                "importance": "medium",
                "email": email_s,
                "evidence": _json_safe(
                    {
                        "sent_by_me": int(row["sent_by_me"]),
                        "received_by_me": int(row["received_by_me"]),
                        "total_messages": int(row["total_messages"]),
                        "sent_per_received_ratio": rr,
                    }
                ),
                "interpretation": "This person initiated most conversations.",
            }
        )

    # --- 4) Long-running ---
    dur_df = df.dropna(subset=["duration_years", "first_contact", "last_contact"]).copy()
    dur_df = dur_df[dur_df["duration_years"] > 0]
    if not dur_df.empty:
        idx = dur_df["duration_years"].idxmax()
        row = dur_df.loc[idx]
        email_s = row["email"] if isinstance(row["email"], str) else str(row["email"])
        add(
            {
                "title": "Longest-running relationship",
                "category": "lifecycle",
                "importance": "high",
                "email": email_s,
                "evidence": _json_safe(
                    {
                        "duration_years": round(float(row["duration_years"]), 2),
                        "duration_days": int(row["duration_days"]) if pd.notna(row["duration_days"]) else None,
                        "first_contact": row["first_contact"].isoformat()
                        if pd.notna(row["first_contact"])
                        else None,
                        "last_contact": row["last_contact"].isoformat()
                        if pd.notna(row["last_contact"])
                        else None,
                        "total_messages": int(row["total_messages"]),
                    }
                ),
                "interpretation": "This relationship persisted over a long period.",
            }
        )

    # --- 5) High intensity ---
    if not df.empty:
        idx = df["total_messages"].idxmax()
        row = df.loc[idx]
        email_s = row["email"] if isinstance(row["email"], str) else str(row["email"])
        add(
            {
                "title": "Highest message volume",
                "category": "volume",
                "importance": "high",
                "email": email_s,
                "evidence": _json_safe(
                    {
                        "total_messages": int(row["total_messages"]),
                        "sent_by_me": int(row["sent_by_me"]),
                        "received_by_me": int(row["received_by_me"]),
                        "tier": str(row["tier"]),
                    }
                ),
                "interpretation": "This was one of your most active conversations.",
            }
        )

    # --- 6) Faded ---
    valid_last = df["last_contact"].dropna()
    if not valid_last.empty:
        max_last = valid_last.max()
        cutoff = max_last - pd.Timedelta(days=FADE_GAP_DAYS)
        faded = df[
            (df["last_contact"].notna())
            & (df["last_contact"] < cutoff)
            & (df["total_messages"] >= MIN_MESSAGES_FADED)
        ].sort_values("last_contact", ascending=True)
        for _, row in faded.head(2).iterrows():
            email_s = row["email"] if isinstance(row["email"], str) else str(row["email"])
            gap_days = (max_last - row["last_contact"]).days if pd.notna(row["last_contact"]) else None
            add(
                {
                    "title": "Relationship appears faded",
                    "category": "lifecycle",
                    "importance": "low",
                    "email": email_s,
                    "evidence": _json_safe(
                        {
                            "last_contact": row["last_contact"].isoformat()
                            if pd.notna(row["last_contact"])
                            else None,
                            "dataset_latest_contact": max_last.isoformat(),
                            "gap_days_before_latest": gap_days,
                            "total_messages": int(row["total_messages"]),
                        }
                    ),
                    "interpretation": "This relationship appears to have faded.",
                }
            )

    # --- 7) Dense social year (timeline) ---
    if timeline_df is not None and not timeline_df.empty:
        peak = _overlap_peak_year(timeline_df)
        if peak:
            peak_year, peak_count, all_counts = peak
            add(
                {
                    "title": f"Peak CORE overlap in {peak_year}",
                    "category": "temporal",
                    "importance": "high",
                    "email": None,
                    "evidence": {
                        "peak_year": peak_year,
                        "overlap_count_core_relationships": peak_count,
                        "overlap_by_year": all_counts,
                    },
                    "interpretation": f"Your communication activity peaked around {peak_year}.",
                }
            )

    # --- 8) Unbalanced outliers ---
    bal = df[(df["received_by_me"] > 0) & (df["total_messages"] >= MIN_MESSAGES_OUTLIER)].copy()
    bal = bal[bal["recip_ratio"].notna()]
    if not bal.empty:
        bal["imbalance"] = np.where(
            bal["recip_ratio"] > 1,
            bal["recip_ratio"],
            1.0 / bal["recip_ratio"].replace(0, np.nan),
        )
        extreme = bal[
            (bal["recip_ratio"] >= OUTLIER_RATIO_HIGH) | (bal["recip_ratio"] <= OUTLIER_RATIO_LOW)
        ].sort_values("imbalance", ascending=False)
        for _, row in extreme.head(2).iterrows():
            if per_cat["outliers"] >= _LIMITS["outliers"]:
                break
            email_s = row["email"] if isinstance(row["email"], str) else str(row["email"])
            rr = float(row["recip_ratio"])
            add(
                {
                    "title": "Unusually unbalanced reciprocity",
                    "category": "outliers",
                    "importance": "medium",
                    "email": email_s,
                    "evidence": _json_safe(
                        {
                            "sent_by_me": int(row["sent_by_me"]),
                            "received_by_me": int(row["received_by_me"]),
                            "sent_per_received_ratio": rr,
                            "total_messages": int(row["total_messages"]),
                        }
                    ),
                    "interpretation": "This relationship was unusually unbalanced.",
                }
            )

    insights.sort(
        key=lambda x: (
            -IMPORTANCE_RANK.get(str(x.get("importance", "low")), 1),
            str(x.get("category", "")),
            str(x.get("title", "")),
        )
    )

    insights = insights[:MAX_INSIGHTS]

    payload = {"insights": [_json_safe(i) for i in insights]}
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload
