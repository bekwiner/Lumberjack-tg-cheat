"""ScoreCounter uchun xususiyat-asosli testlar (hypothesis).

Dizayn hujjatining "Correctness Properties" bo'limidagi Property 6 ni
tekshiradi.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from lumberjack_bot.score_counter import ScoreCounter


# Feature: lumberjack-bot, Property 6: Ball sanagich to'g'riligi
# For any boshlang'ich target va istalgan N >= 0 sondagi muvaffaqiyatli
# kesish uchun, N marta increment() dan keyin joriy ball aynan N ga teng
# bo'ladi va target_reached() faqat current >= target bo'lganda True
# qaytaradi.
# Validates: Requirements 3.3, 3.5
@settings(max_examples=100)
@given(
    target=st.integers(min_value=1, max_value=1_000_000),
    n=st.integers(min_value=0, max_value=2000),
)
def test_score_counter_correctness(target: int, n: int):
    counter = ScoreCounter(target)

    # boshlang'ich holatda joriy ball 0 bo'lishi kerak
    assert counter.current == 0

    for _ in range(n):
        counter.increment()

    # N marta increment() dan keyin joriy ball aynan N ga teng
    assert counter.current == n

    # target_reached() faqat va faqat current >= target bo'lganda True
    assert counter.target_reached() == (counter.current >= target)
