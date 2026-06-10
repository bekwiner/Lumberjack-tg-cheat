"""Kerakli kutubxonalar importi uchun smoke testlar.

Task 13.3 / Requirements 1.1, 1.2, 1.3: botga kerakli runtime kutubxonalari
(ekranni suratga olish uchun ImageGrab/OpenCV, sichqoncha uchun pyautogui,
klaviatura uchun keyboard) import qilinishini tekshiradi.

Bu testlar SMOKE testlar (PBT emas). Maqsad — kutubxona MAVJUD bo'lganda
importi ishlashini tasdiqlash. Bu runtime kutubxonalar test muhitida
o'rnatilmagan bo'lishi mumkin (ayrimlari displey yoki admin huquqini talab
qiladi), shuning uchun testlar bardoshli (tolerant):

  - `importlib.util.find_spec` orqali mavjudlik tekshiriladi, qattiq import
    qilinmaydi (collection paytida crash bo'lmasligi uchun).
  - Kutubxona yo'q bo'lsa, test xato bermasdan `pytest.skip` orqali aniq xabar
    bilan o'tkazib yuboriladi.
"""

import importlib.util

import pytest


def _is_importable(module_name: str) -> bool:
    """Modul import qilinadigan bo'lsa True qaytaradi (crash bo'lmasdan)."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        # Ota-paket yo'q bo'lsa find_spec ModuleNotFoundError ko'tarishi mumkin.
        return False


def test_screen_capture_library_importable():
    """Requirement 1.1: ImageGrab (PIL) yoki OpenCV (cv2) dan kamida bittasi
    mavjud bo'lganda importi ishlashi kerak.

    Ikkalasi ham o'rnatilmagan bo'lsa, test fail emas, skip bo'ladi — maqsad
    kutubxona MAVJUD bo'lgandagi importni tekshirish.
    """
    has_pil = _is_importable("PIL")
    has_cv2 = _is_importable("cv2")

    if not (has_pil or has_cv2):
        pytest.skip(
            "Ekranni suratga olish kutubxonasi (Pillow/PIL yoki opencv-python/cv2) "
            "o'rnatilmagan; o'rnatish: 'pip install Pillow' yoki 'pip install opencv-python'"
        )

    # Mavjud bo'lganlardan kamida bittasi haqiqatan import qilinishi kerak.
    if has_pil:
        from PIL import ImageGrab  # noqa: F401

    if has_cv2:
        import cv2  # noqa: F401


def test_pyautogui_importable():
    """Requirement 1.2: pyautogui mavjud bo'lsa import qilinishi kerak.

    pyautogui importi displey muhitini talab qilishi mumkin, shuning uchun
    mavjud bo'lmasa yoki import muvaffaqiyatsiz bo'lsa skip bo'ladi.
    """
    pytest.importorskip(
        "pyautogui",
        reason="pyautogui o'rnatilmagan; o'rnatish: 'pip install pyautogui'",
    )


def test_keyboard_importable():
    """Requirement 1.3: keyboard kutubxonasi mavjud bo'lsa import qilinishi
    kerak.

    keyboard ba'zi platformalarda admin/root huquqini talab qilishi mumkin,
    mavjud bo'lmasa skip bo'ladi.
    """
    pytest.importorskip(
        "keyboard",
        reason="keyboard o'rnatilmagan; o'rnatish: 'pip install keyboard'",
    )


def test_check_dependencies_runs_and_returns_list():
    """check_dependencies() o'rnatilgan kutubxonalardan qat'i nazar ishlaydi
    va ro'yxat qaytaradi (sof mantiq, har doim ishlaydi)."""
    from lumberjack_bot.dependency_checker import (
        MissingDependency,
        check_dependencies,
    )

    result = check_dependencies()
    assert isinstance(result, list)
    # Ro'yxatdagi har bir element MissingDependency bo'lishi kerak.
    assert all(isinstance(item, MissingDependency) for item in result)
