"""BranchDetector uchun xususiyat-asosli testlar (property-based tests).

Ushbu modul `hypothesis` yordamida `BranchDetector` ning ikkita to'g'rilik
xususiyatini tekshiradi:

- Property 2: Shox aniqlash qarori to'g'ri (Requirements 2.2, 2.3, 2.5).
- Property 3: Tolerance monotonligi (Requirements 2.4).

Manba: design.md "Correctness Properties" va "BranchDetector" bo'limlari.
Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from lumberjack_bot.branch_detector import BranchDetector
from lumberjack_bot.models import BranchSample, Decision, RGBColor, Side


# RGB kanal generatori: 0..255, chegaralar (0, 255) bilan birga.
channels = st.integers(min_value=0, max_value=255)


def rgb_strategy():
    """0..255 oralig'ida RGB rang generatori (chegaralarni qamrab oladi)."""
    return st.builds(RGBColor, r=channels, g=channels, b=channels)


def _reference_matches(branch_color: RGBColor, tolerance: int, sample: RGBColor) -> bool:
    """Mustaqil mos kelish oracle: har bir kanal chegara ichida bo'lishi kerak."""
    return (
        abs(sample.r - branch_color.r) <= tolerance
        and abs(sample.g - branch_color.g) <= tolerance
        and abs(sample.b - branch_color.b) <= tolerance
    )


# Feature: lumberjack-bot, Property 2: Shox aniqlash qarori to'g'ri —
# For any BranchSample (chap va o'ng ranglar), qahramon tomoni va tolerance uchun
# decide() ikkala tomon mos kelsa DANGER_STOP, aks holda qahramon tomoni mos kelsa
# MOVE_TO_SAFE, aks holda STAY_AND_CHOP qaytaradi.
# Validates: Requirements 2.2, 2.3, 2.5
@settings(max_examples=200)
@given(
    branch_color=rgb_strategy(),
    left_color=rgb_strategy(),
    right_color=rgb_strategy(),
    hero_side=st.sampled_from(list(Side)),
    tolerance=channels,
)
def test_decide_matches_reference_oracle(
    branch_color, left_color, right_color, hero_side, tolerance
):
    detector = BranchDetector(branch_color=branch_color, tolerance=tolerance)
    sample = BranchSample(left_color=left_color, right_color=right_color)

    # Test ichida `color_matches_branch` dan mustaqil oracle quramiz.
    left_match = _reference_matches(branch_color, tolerance, left_color)
    right_match = _reference_matches(branch_color, tolerance, right_color)
    hero_match = left_match if hero_side is Side.LEFT else right_match

    if left_match and right_match:
        expected = Decision.DANGER_STOP
    elif hero_match:
        expected = Decision.MOVE_TO_SAFE
    else:
        expected = Decision.STAY_AND_CHOP

    assert detector.decide(sample, hero_side) == expected


# Feature: lumberjack-bot, Property 3: Tolerance monotonligi —
# For any ikkita rang va ikkita tolerance t1 <= t2 uchun, agar rang t1 chegarasida
# mos kelsa, u t2 chegarasida ham mos keladi (moslik to'plami kamaymaydi);
# tolerance = 0 da faqat aniq teng ranglar mos keladi.
# Validates: Requirements 2.4
@settings(max_examples=200)
@given(
    branch_color=rgb_strategy(),
    sample_color=rgb_strategy(),
    t_a=channels,
    t_b=channels,
)
def test_tolerance_monotonicity(branch_color, sample_color, t_a, t_b):
    t1, t2 = sorted((t_a, t_b))  # t1 <= t2 ni kafolatlaymiz

    detector_t1 = BranchDetector(branch_color=branch_color, tolerance=t1)
    detector_t2 = BranchDetector(branch_color=branch_color, tolerance=t2)

    matches_t1 = detector_t1.color_matches_branch(sample_color)
    matches_t2 = detector_t2.color_matches_branch(sample_color)

    # Monotonlik: t1 da mos kelsa, t2 (>= t1) da ham mos kelishi shart.
    if matches_t1:
        assert matches_t2

    # tolerance = 0 da faqat aniq teng ranglar mos keladi.
    detector_zero = BranchDetector(branch_color=branch_color, tolerance=0)
    exact_equal = sample_color == branch_color
    assert detector_zero.color_matches_branch(sample_color) == exact_equal
