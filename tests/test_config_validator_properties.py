"""ConfigValidator uchun xususiyat-asosli testlar (hypothesis).

Ushbu fayl dizayn hujjatidagi quyidagi xususiyatlarni amalga oshiradi:
    - Property 5: target_score validatsiyasi (Requirements 3.1, 3.2)
    - Property 7: Kechikish oralig'i validatsiyasi (Requirements 5.2, 5.3)

Har bir xususiyat testi kamida 100 iteratsiya ishlaydi
(@settings(max_examples=100)). Generatorlar chegara holatlarini
(boundary) maxsus qamrab oladi.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from lumberjack_bot.config_validator import (
    DELAY_MAX_MS,
    DELAY_MIN_MS,
    TARGET_SCORE_MAX,
    TARGET_SCORE_MIN,
    validate_delay,
    validate_target_score,
)


# ---------------------------------------------------------------------------
# Property 5: target_score validatsiyasi
# ---------------------------------------------------------------------------

# target_score uchun har xil turdagi qiymatlarni qamraydigan strategiya:
#   - oraliq ichidagi butun sonlar (1..1_000_000)
#   - oraliq tashqarisidagi butun sonlar (manfiy, 0, juda katta)
#   - chegara qiymatlari (1, 1_000_000, 0)
#   - butun bo'lmagan turlar (float, str, None, bool)
_target_score_strategy = st.one_of(
    st.integers(min_value=TARGET_SCORE_MIN, max_value=TARGET_SCORE_MAX),
    st.integers(),  # diapazon tashqarisidagilarni ham qamraydi
    st.sampled_from([TARGET_SCORE_MIN, TARGET_SCORE_MAX, 0, -1,
                     TARGET_SCORE_MAX + 1, TARGET_SCORE_MIN - 1]),
    st.floats(),
    st.text(),
    st.none(),
    st.booleans(),
)


# Feature: lumberjack-bot, Property 5: target_score validatsiyasi —
# For any qiymat uchun, ConfigValidator uni faqat va faqat u butun son
# hamda 1 <= target_score <= 1_000_000 bo'lganda qabul qiladi; aks holda
# rad etadi va kesish boshlanmaydi. (Validates: Requirements 3.1, 3.2)
@settings(max_examples=100)
@given(value=_target_score_strategy)
def test_property_5_target_score_validation(value):
    result = validate_target_score(value)

    # Kutilgan natija: faqat haqiqiy int (bool emas) va oraliq ichida
    is_real_int = isinstance(value, int) and not isinstance(value, bool)
    expected_ok = is_real_int and TARGET_SCORE_MIN <= value <= TARGET_SCORE_MAX

    assert result.ok == expected_ok, (
        f"value={value!r} uchun ok={result.ok}, kutilgan={expected_ok}"
    )

    # Rad etilganda sabab bo'lishi, qabul qilinganda sabab bo'lmasligi kerak
    if expected_ok:
        assert result.reason is None
    else:
        assert result.reason is not None


# Feature: lumberjack-bot, Property 5: target_score validatsiyasi — chegara
# qiymatlarining aniq xulqi (1 va 1_000_000 qabul, 0 rad).
@settings(max_examples=100)
@given(value=st.sampled_from([TARGET_SCORE_MIN, TARGET_SCORE_MAX, 0]))
def test_property_5_target_score_boundaries(value):
    result = validate_target_score(value)
    if value in (TARGET_SCORE_MIN, TARGET_SCORE_MAX):
        assert result.ok is True
    else:  # 0 — oraliqdan tashqarida
        assert result.ok is False


# ---------------------------------------------------------------------------
# Property 7: Kechikish oralig'i validatsiyasi
# ---------------------------------------------------------------------------

# Kechikish juftligi uchun strategiya: chegara atrofini va min>max
# holatlarini ataylab qamrab oladi.
_delay_value_strategy = st.one_of(
    st.integers(min_value=DELAY_MIN_MS, max_value=DELAY_MAX_MS),
    st.integers(),  # oraliq tashqarisi (manfiy, juda katta)
    st.sampled_from([DELAY_MIN_MS, DELAY_MAX_MS, DELAY_MIN_MS - 1,
                     DELAY_MAX_MS + 1, 0]),
)


# Feature: lumberjack-bot, Property 7: Kechikish oralig'i validatsiyasi —
# For any (min_ms, max_ms) juftligi uchun, ConfigValidator uni faqat va
# faqat 10 <= min_ms <= max_ms <= 5000 bo'lganda qabul qiladi; aks holda
# rad etadi va oldingi sozlama o'zgarmaydi. (Validates: Requirements 5.2, 5.3)
@settings(max_examples=100)
@given(min_ms=_delay_value_strategy, max_ms=_delay_value_strategy)
def test_property_7_delay_range_validation(min_ms, max_ms):
    result = validate_delay(min_ms, max_ms)

    expected_ok = (
        DELAY_MIN_MS <= min_ms <= DELAY_MAX_MS
        and DELAY_MIN_MS <= max_ms <= DELAY_MAX_MS
        and min_ms <= max_ms
    )

    assert result.ok == expected_ok, (
        f"min_ms={min_ms!r}, max_ms={max_ms!r} uchun ok={result.ok}, "
        f"kutilgan={expected_ok}"
    )

    if expected_ok:
        assert result.reason is None
    else:
        assert result.reason is not None


# Feature: lumberjack-bot, Property 7: Kechikish oralig'i validatsiyasi —
# chegara qiymatlari (10, 5000) qabul qilinishi va min>max rad etilishi.
@settings(max_examples=100)
@given(
    a=st.sampled_from([DELAY_MIN_MS, DELAY_MAX_MS, 100, 400]),
    b=st.sampled_from([DELAY_MIN_MS, DELAY_MAX_MS, 100, 400]),
)
def test_property_7_delay_boundaries_and_order(a, b):
    min_ms, max_ms = min(a, b), max(a, b)

    # min <= max va ikkalasi ham oraliq ichida -> qabul
    ok_result = validate_delay(min_ms, max_ms)
    assert ok_result.ok is True

    # min > max -> rad (agar a != b bo'lsa)
    if a != b:
        bad_result = validate_delay(max_ms, min_ms)
        assert bad_result.ok is False
        assert bad_result.reason is not None
