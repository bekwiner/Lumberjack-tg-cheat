"""CalibrationModule uchun xususiyat-asosli testlar (property-based tests).

Ushbu modul `hypothesis` yordamida `CalibrationModule` ning ikkita
to'g'rilik xususiyatini tekshiradi:

- Property 4: Koordinata saqlash round-trip (Requirements 4.4).
- Property 11: Koordinata validatsiyasi va o'zgarmaslik (Requirements 4.5).

Manba: design.md "Correctness Properties" va "CalibrationModule" bo'limlari.
Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from lumberjack_bot.calibration import CalibrationModule
from lumberjack_bot.models import CanvasCoords, Point, ScreenSize


# Ekran o'lchami generatori: kamida 1x1 (yaroqli koordinata bo'lishi uchun).
screen_sizes = st.builds(
    ScreenSize,
    width=st.integers(min_value=1, max_value=10_000),
    height=st.integers(min_value=1, max_value=10_000),
)


def valid_point_for(screen: ScreenSize):
    """Berilgan ekran ichidagi yaroqli nuqta generatori (0 <= x < w, 0 <= y < h)."""
    return st.builds(
        Point,
        x=st.integers(min_value=0, max_value=screen.width - 1),
        y=st.integers(min_value=0, max_value=screen.height - 1),
    )


@st.composite
def screen_and_valid_coords(draw):
    """Ekran o'lchami va o'sha ekran ichidagi yaroqli CanvasCoords juftligi."""
    screen = draw(screen_sizes)
    left = draw(valid_point_for(screen))
    right = draw(valid_point_for(screen))
    top = draw(valid_point_for(screen))
    return screen, CanvasCoords(left=left, right=right, top=top)


# Feature: lumberjack-bot, Property 4: Koordinata saqlash round-trip —
# For any yaroqli CanvasCoords qiymati uchun, uni CalibrationModule ga saqlab,
# keyin o'qib olinganda aynan o'sha qiymat qaytadi (ko'rsatish holatidan qat'i
# nazar).
@settings(max_examples=100)
@given(data=screen_and_valid_coords())
def test_property_4_save_load_round_trip(data):
    """Property 4: save_coords keyin load_coords aynan o'sha qiymatni qaytaradi.

    Yaroqli CanvasCoords tasodifiy hosil qilinadi, saqlanadi va o'qib olinadi.
    O'qilgan qiymat saqlangan qiymat bilan aynan teng bo'lishi kerak.

    **Validates: Requirements 4.4**
    """
    screen, coords = data
    module = CalibrationModule(screen=screen)

    assert module.save_coords(coords) is True

    loaded = module.load_coords()
    assert loaded == coords
    # Frozen dataclass tengligi maydonlar bo'yicha aniq mosligini ta'minlaydi.
    assert loaded.left == coords.left
    assert loaded.right == coords.right
    assert loaded.top == coords.top


def _reference_valid(point: Point, screen: ScreenSize) -> bool:
    """Mustaqil validatsiya oracle: 0 <= x < width va 0 <= y < height."""
    return 0 <= point.x < screen.width and 0 <= point.y < screen.height


# Feature: lumberjack-bot, Property 11: Koordinata validatsiyasi va o'zgarmaslik —
# For any koordinata va ekran o'lchami uchun, validate_coord() faqat
# 0 <= x < width va 0 <= y < height bo'lganda qabul qiladi; rad etilganda
# oldindan saqlangan koordinata o'zgartirilmaydi.
@settings(max_examples=100)
@given(
    screen=screen_sizes,
    px=st.integers(min_value=-10_000, max_value=20_000),
    py=st.integers(min_value=-10_000, max_value=20_000),
    base_dx=st.integers(min_value=0, max_value=9_999),
    base_dy=st.integers(min_value=0, max_value=9_999),
)
def test_property_11_validation_and_immutability(screen, px, py, base_dx, base_dy):
    """Property 11: validate_coord to'g'ri qabul/rad qiladi va rad etishda
    oldingi saqlangan koordinata o'zgarmaydi.

    Avval ekran ichidagi yaroqli "base" nuqta set_point orqali saqlanadi.
    So'ngra tasodifiy nuqta (ekrandan tashqarida ham bo'lishi mumkin)
    tekshiriladi: validate_coord natijasi oracle bilan mos kelishi kerak,
    va agar yangi nuqta rad etilsa, saqlangan nuqta o'zgarmasligi kerak.

    **Validates: Requirements 4.5**
    """
    module = CalibrationModule(screen=screen)

    # Ekran ichidagi yaroqli boshlang'ich nuqta (ekran kamida 1x1).
    base = Point(x=base_dx % screen.width, y=base_dy % screen.height)
    assert module.set_point("left", base) is True
    assert module.get_point("left") == base

    candidate = Point(x=px, y=py)

    expected = _reference_valid(candidate, screen)
    assert module.validate_coord(candidate, screen) is expected

    # set_point validatsiyaga asoslanadi: qabul/rad natijasi mos kelishi kerak.
    result = module.set_point("left", candidate)
    assert result is expected

    if not expected:
        # Rad etildi: oldingi saqlangan qiymat o'zgarmasligi kerak (Requirement 4.5).
        assert module.get_point("left") == base
    else:
        # Qabul qilindi: yangi qiymat saqlanadi.
        assert module.get_point("left") == candidate
