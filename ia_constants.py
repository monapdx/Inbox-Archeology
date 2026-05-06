"""
Shared thresholds for relationship tiers and CORE timeline filtering.

Keep these in sync everywhere tiers are computed or summarized.
"""

from __future__ import annotations

CORE_MESSAGE_THRESHOLD = 100
RECURRING_MESSAGE_THRESHOLD = 25


def tier_from_total(total: int) -> str:
    if total >= CORE_MESSAGE_THRESHOLD:
        return "CORE"
    if total >= RECURRING_MESSAGE_THRESHOLD:
        return "RECURRING"
    return "PERIPHERAL"
