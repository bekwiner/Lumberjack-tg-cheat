"""CalibrationModule uchun unit testlar (misol va edge-case holatlar).

Ushbu modul ikkita unit testni amalga oshiradi:

- 10.4: kalibrlash rejimi ishga tushganda raqamlangan ko'rsatmalar chop
  etilishi (Requirements 4.1, 4.2). `pyautogui` va `keyboard`
  modullari mock qilinadi (sys.modules orqali).
- 10.5: saqlash amali muvaffaqiyatsiz bo'lganda (persist callback istisno
  ko'taradi) save_coords False qaytaradi, oldingi saqlangan qiymat
  o'zgarmaydi va xato indikatsiyasi ko'rsatiladi (Requirements 4.6).

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

import sys
import types
from unittest import mock

import pytest

from lumberjack_bot.calibration import CalibrationModule
from lumberjack_bot.models import CanvasCoords, Point, ScreenSize


# ----------------------------------------------------------------------
# 10.4: Kalibrlash boshlanishi va raqamlangan ko'rsatmalar (Requirements 4.1, 4.2)
# ----------------------------------------------------------------------


class _FakeMouse:
    """pyautogui.position() ni taqlid qiladi — ketma-ket koordinatalar qaytaradi.

    Har bir nuqta uchun bir nechta polling chaqiruvi bo'lishi mumkin, shu
    bois koordinatalar ro'yxatidan ketma-ket o'qiladi; ro'yxat tugasa,
    oxirgi qiymat takrorlanadi.
    """

    def __init__(self, positions):
        self._positions = list(positions)
        self._index = 0

    def position(self):
        if self._index < len(self._positions):
            pos = self._positions[self._index]
            self._index += 1
        else:
            pos = self._positions[-1]
        return pos


class _FakeKeyboard:
    """keyboard.is_pressed ni taqlid qiladi — har chaqiruvda True qaytaradi.

    Bu har bir nuqtaning birinchi polling iteratsiyasida darhol
    tasdiqlanishini ta'minlaydi, shunda run() bloklanmaydi.
    """

    def is_pressed(self, key):
        return True


def test_10_4_calibration_starts_and_prints_numbered_instructions(capsys):
    """run() kalibrlash rejimini boshlaydi va raqamlangan ko'rsatmalarni chop etadi.

    `pyautogui` va `keyboard` modullari sys.modules orqali mock qilinadi.
    Sichqoncha har doim ekran ichidagi yaroqli nuqtalarni qaytaradi va
    tasdiqlash tugmasi doimo bosilgan hisoblanadi, shunday qilib run()
    uchta nuqtani yig'adi va yakunlanadi.

    Stdout ichida "1.", "2.", "3." raqamlangan ko'rsatmalar bo'lishi kerak.

    **Requirements: 4.1, 4.2**
    """
    screen = ScreenSize(width=1920, height=1080)
    module = CalibrationModule(screen=screen)

    fake_mouse = _FakeMouse(
        positions=[(100, 200), (300, 400), (500, 600)]
    )
    fake_keyboard = _FakeKeyboard()

    fake_pyautogui = types.SimpleNamespace(position=fake_mouse.position)
    fake_keyboard_module = types.SimpleNamespace(
        is_pressed=fake_keyboard.is_pressed
    )

    with mock.patch.dict(
        sys.modules,
        {"pyautogui": fake_pyautogui, "keyboard": fake_keyboard_module},
    ):
        result = module.run()

    out = capsys.readouterr().out

    # Kalibrlash rejimi boshlanganini bildiruvchi sarlavha (Requirement 4.1).
    assert "Kalibrlash" in out

    # Uchta raqamlangan ko'rsatma mavjud bo'lishi kerak (Requirement 4.2).
    assert "1." in out
    assert "2." in out
    assert "3." in out

    # Uchta nuqta to'g'ri yig'ilib saqlangan bo'lishi kerak.
    assert result == CanvasCoords(
        left=Point(100, 200),
        right=Point(300, 400),
        top=Point(500, 600),
    )


# ----------------------------------------------------------------------
# 10.5: Saqlash xatosida koordinata saqlanishi (Requirements 4.6)
# ----------------------------------------------------------------------


def test_10_5_save_failure_keeps_previous_coords_unchanged():
    """persist callback istisno ko'tarsa, oldingi saqlangan qiymat o'zgarmaydi.

    Avval persist'siz modul orqali yaroqli koordinata saqlanadi (muvaffaqiyatli).
    So'ngra persist callback istisno ko'taradigan yangi modulga o'sha saqlangan
    qiymat o'rnatiladi va boshqa yaroqli koordinatani saqlashga urinilganda
    save_coords False qaytarishi hamda saqlangan qiymat o'zgarmasligi kerak.

    **Requirements: 4.6**
    """
    screen = ScreenSize(width=1920, height=1080)

    previous = CanvasCoords(
        left=Point(10, 20),
        right=Point(30, 40),
        top=Point(50, 60),
    )

    # persist callback har doim istisno ko'taradi (saqlash xatosini taqlid qiladi).
    def failing_persist(coords):
        raise IOError("saqlab bo'lmadi")

    module = CalibrationModule(screen=screen, persist=failing_persist)

    # Oldingi (muvaffaqiyatli saqlangan) holatni qo'lda o'rnatamiz.
    module._saved_coords = previous

    new_coords = CanvasCoords(
        left=Point(100, 200),
        right=Point(300, 400),
        top=Point(500, 600),
    )

    # Saqlash muvaffaqiyatsiz bo'lishi kerak (persist istisno ko'taradi).
    result = module.save_coords(new_coords)
    assert result is False

    # Oldingi koordinata o'zgarmasdan saqlanib qolishi kerak (Requirement 4.6).
    assert module.load_coords() == previous


def test_10_5_save_failure_prints_error_indication(capsys):
    """Saqlash muvaffaqiyatsiz bo'lganda run() xato indikatsiyasini ko'rsatadi.

    `pyautogui`/`keyboard` mock qilinadi; persist callback istisno ko'taradi.
    run() koordinatalarni yig'adi, save_coords muvaffaqiyatsiz bo'ladi va
    terminalda "Xato" so'zini o'z ichiga olgan xabar chop etiladi.

    **Requirements: 4.6**
    """
    screen = ScreenSize(width=1920, height=1080)

    def failing_persist(coords):
        raise IOError("saqlab bo'lmadi")

    module = CalibrationModule(screen=screen, persist=failing_persist)

    fake_mouse = _FakeMouse(positions=[(100, 200), (300, 400), (500, 600)])
    fake_keyboard = _FakeKeyboard()

    fake_pyautogui = types.SimpleNamespace(position=fake_mouse.position)
    fake_keyboard_module = types.SimpleNamespace(
        is_pressed=fake_keyboard.is_pressed
    )

    with mock.patch.dict(
        sys.modules,
        {"pyautogui": fake_pyautogui, "keyboard": fake_keyboard_module},
    ):
        result = module.run()

    out = capsys.readouterr().out

    # Saqlash xatosi indikatsiyasi ko'rsatilishi kerak (Requirement 4.6).
    assert "Xato" in out
    # Hech narsa muvaffaqiyatli saqlanmaganligi sababli load_coords None qaytaradi.
    assert result is None
