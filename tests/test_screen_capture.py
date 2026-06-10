"""ScreenCaptureModule uchun integratsiya/unit testlar.

Bu testlar 9.2 va 9.3 vazifalarini qoplaydi:
  - 9.2: `read_branch_points` chap/o'ng ranglarni qaytaradi va ~100 ms
    vaqt chegarasi ichida bajariladi (manba mock qilinadi — haqiqiy ekran
    surati olinmaydi). _Requirements: 2.1_
  - 9.3: backend o'qishda xato bersa `PixelReadError` `read_branch_points`
    dan yuqoriga uzatiladi (xato indikatsiyasi). _Requirements: 2.6_

Eslatma: barcha holatlar mock qilinadi — testlar haqiqiy ekrandan
mustaqil ishlaydi.
"""

import time

import pytest

from lumberjack_bot.models import (
    CanvasCoords,
    PixelReadError,
    Point,
    RGBColor,
)
from lumberjack_bot.screen_capture import ScreenCaptureModule


# Ikkala tekshirish nuqtasi (chap/o'ng) uchun namuna koordinatalar.
_COORDS = CanvasCoords(left=Point(10, 20), right=Point(30, 40), top=Point(15, 5))


def test_read_branch_points_returns_both_colors_quickly():
    """9.2: read_branch_points chap va o'ng ranglarni qaytaradi (~100 ms).

    Backend (read_pixel) mock qilinadi, shuning uchun haqiqiy ekran surati
    olinmaydi. Chap nuqta uchun bitta rang, o'ng nuqta uchun boshqa rang
    qaytariladi va natija `BranchSample` da to'g'ri joylashishi tekshiriladi.
    Bajarilish vaqti generous chegara (< 0.1 s) ichida bo'lishi kerak.
    """
    module = ScreenCaptureModule()

    left = RGBColor(139, 90, 43)
    right = RGBColor(0, 0, 0)

    # read_pixel ni koordinataga qarab mos rang qaytaradigan qilib almashtiramiz.
    def fake_read_pixel(x, y):
        if (x, y) == (_COORDS.left.x, _COORDS.left.y):
            return left
        if (x, y) == (_COORDS.right.x, _COORDS.right.y):
            return right
        raise AssertionError(f"kutilmagan koordinata: ({x}, {y})")

    module.read_pixel = fake_read_pixel  # type: ignore[assignment]

    start = time.perf_counter()
    sample = module.read_branch_points(_COORDS)
    elapsed = time.perf_counter() - start

    # Ikkala rang ham to'g'ri qaytarilgan bo'lishi kerak (Requirement 2.1).
    assert sample.left_color == left
    assert sample.right_color == right
    # Vaqt chegarasi: ~100 ms generous bound (mock manba bilan juda tez).
    assert elapsed < 0.1


def test_read_branch_points_propagates_pixel_read_error():
    """9.3: backend o'qish xatosi PixelReadError sifatida uzatiladi.

    read_pixel `PixelReadError` ko'tarsa (backend xatosi mock qilingan),
    `read_branch_points` ham shu istisnoni yuqoriga uzatishi kerak
    (xato indikatsiyasi, Requirement 2.6).
    """
    module = ScreenCaptureModule()

    def failing_read_pixel(x, y):
        raise PixelReadError(f"backend xatosi: ({x}, {y})")

    module.read_pixel = failing_read_pixel  # type: ignore[assignment]

    with pytest.raises(PixelReadError):
        module.read_branch_points(_COORDS)


def test_read_pixel_raises_pixel_read_error_on_backend_failure():
    """9.3 (qo'shimcha): backend surat olishda xato bersa PixelReadError.

    PIL backend tanlangan, biroq `ImageGrab.grab` xato beradigan qilib
    almashtirilgan holatda `read_pixel` `PixelReadError` ko'tarishi kerak.
    """
    module = ScreenCaptureModule()
    # Backend'ni to'g'ridan-to'g'ri "pil" deb belgilaymiz (aniqlashni o'tkazib).
    module._backend = "pil"

    import sys
    import types

    # Soxta PIL.ImageGrab modulini sys.modules ga joylaymiz.
    fake_pil = types.ModuleType("PIL")
    fake_imagegrab = types.ModuleType("PIL.ImageGrab")

    def failing_grab(*args, **kwargs):
        raise OSError("ekran surati olinmadi")

    fake_imagegrab.grab = failing_grab
    fake_pil.ImageGrab = fake_imagegrab

    sys.modules["PIL"] = fake_pil
    sys.modules["PIL.ImageGrab"] = fake_imagegrab
    try:
        with pytest.raises(PixelReadError):
            module.read_pixel(5, 5)
    finally:
        # sys.modules ni tozalaymiz, boshqa testlarga ta'sir qilmasligi uchun.
        sys.modules.pop("PIL", None)
        sys.modules.pop("PIL.ImageGrab", None)
