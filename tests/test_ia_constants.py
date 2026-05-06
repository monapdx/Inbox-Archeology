from ia_constants import (
    CORE_MESSAGE_THRESHOLD,
    RECURRING_MESSAGE_THRESHOLD,
    tier_from_total,
)


def test_tier_boundaries() -> None:
    assert tier_from_total(CORE_MESSAGE_THRESHOLD + 5) == "CORE"
    assert tier_from_total(CORE_MESSAGE_THRESHOLD) == "CORE"
    assert tier_from_total(CORE_MESSAGE_THRESHOLD - 1) == "RECURRING"
    assert tier_from_total(RECURRING_MESSAGE_THRESHOLD) == "RECURRING"
    assert tier_from_total(RECURRING_MESSAGE_THRESHOLD - 1) == "PERIPHERAL"
