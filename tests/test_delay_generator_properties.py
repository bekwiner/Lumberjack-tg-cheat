"""DelayGenerator uchun xususiyat-asosli testlar (hypothesis).

Ushbu modul dizayn hujjatidagi "Correctness Properties" bo'limining
Property 1 xususiyatini tekshiradi.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from lumberjack_bot.delay_generator import DelayGenerator


# Feature: lumberjack-bot, Property 1: Tasodifiy kechikish doimo oraliq ichida
# Validates: Requirements 5.1
@settings(max_examples=100)
@given(
    bounds=st.integers(min_value=10, max_value=5000).flatmap(
        lambda lo: st.tuples(
            st.just(lo),
            st.integers(min_value=lo, max_value=5000),
        )
    ),
    num_calls=st.integers(min_value=1, max_value=50),
)
def test_next_delay_always_within_range(bounds, num_calls):
    """For any yaroqli (min_ms, max_ms) juftligi (10 <= min <= max <= 5000)
    va istalgan sondagi chaqiruvlar uchun next_delay_ms() hosil qilgan
    har bir qiymat min_ms <= d <= max_ms shartini qondiradi."""
    min_ms, max_ms = bounds
    generator = DelayGenerator(min_ms, max_ms)

    for _ in range(num_calls):
        d = generator.next_delay_ms()
        assert min_ms <= d <= max_ms
