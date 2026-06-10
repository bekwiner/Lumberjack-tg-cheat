"""KeyboardListener uchun integratsiya/unit testlar.

Bu testlar 9.6 va 9.7 vazifalarini qoplaydi:
  - 9.6: `keyboard` kutubxonasi mock qilinib, 's'/'q' bosilganda `poll()`
    mos `ControlKey` ni qaytarishi tekshiriladi. ~100 ms polling oralig'ida
    takroriy chaqirilishi ham tasdiqlanadi. _Requirements: 6.3_
  - 9.7: STOPPED ga o'tishda `BotController.stop_safely` orqali
    `KeyboardListener.stop()` chaqirilishi tekshiriladi (mock). _Requirements: 6.5_

Eslatma: barcha holatlar mock qilinadi — testlar haqiqiy klaviaturadan
mustaqil ishlaydi.
"""

import sys
import types
from unittest.mock import Mock

import pytest

from lumberjack_bot.keyboard_listener import KeyboardListener
from lumberjack_bot.models import ControlKey, State


@pytest.fixture
def fake_keyboard():
    """Soxta `keyboard` modulini sys.modules ga joylaydi va olib tashlaydi.

    `is_pressed(name)` ni testlar boshqaradigan funksiya bilan ta'minlaydi.
    """
    module = types.ModuleType("keyboard")
    # Standart: hech qaysi tugma bosilmagan.
    module.is_pressed = lambda name: False
    module.unhook_all = lambda: None

    sys.modules["keyboard"] = module
    try:
        yield module
    finally:
        sys.modules.pop("keyboard", None)


def test_poll_returns_start_then_stop(fake_keyboard):
    """9.6: 's' bosilsa START, 'q' bosilsa STOP qaytadi (~100 ms polling).

    `keyboard.is_pressed` ketma-ket chaqiruvlarda avval 's', so'ng 'q'
    bosilgan deb qaytaradi. Har bir poll() ~100 ms oralig'ida chaqirilishini
    simulyatsiya qilamiz (lekin haqiqiy kutishsiz).
    """
    # Birinchi polling tsiklida faqat 's' bosilgan.
    pressed = {"s": False, "q": False}
    fake_keyboard.is_pressed = lambda name: pressed.get(name, False)

    listener = KeyboardListener()

    # Hech narsa bosilmaganda None.
    assert listener.poll() is None

    # 's' bosilsa START.
    pressed["s"] = True
    assert listener.poll() is ControlKey.START

    # 's' qo'yib yuborilib 'q' bosilsa STOP.
    pressed["s"] = False
    pressed["q"] = True
    assert listener.poll() is ControlKey.STOP


def test_poll_repeated_polling_is_consistent(fake_keyboard):
    """9.6: takroriy polling izchil ishlaydi (~100 ms oraliqda chaqiriladi).

    Bir nechta ketma-ket poll() chaqiruvi kutilgan ControlKey larni
    qaytarishini tasdiqlaydi.
    """
    sequence = iter([
        None,                 # 1-tsikl: hech narsa
        ControlKey.START,     # 2-tsikl: 's'
        None,                 # 3-tsikl: hech narsa
        ControlKey.STOP,      # 4-tsikl: 'q'
    ])

    # Har poll() da navbatdagi natijani beradigan is_pressed quramiz.
    state = {"current": None}

    def is_pressed(name):
        cur = state["current"]
        if cur is ControlKey.START:
            return name == "s"
        if cur is ControlKey.STOP:
            return name == "q"
        return False

    fake_keyboard.is_pressed = is_pressed

    listener = KeyboardListener()
    results = []
    for expected in sequence:
        state["current"] = expected
        results.append(listener.poll())

    assert results == [None, ControlKey.START, None, ControlKey.STOP]


def test_stop_disables_polling(fake_keyboard):
    """9.6/6.5: stop() chaqirilgach poll() doimo None qaytaradi."""
    fake_keyboard.is_pressed = lambda name: True  # hamma tugma bosilgan deylik

    listener = KeyboardListener()
    listener._get_keyboard()  # kutubxonani yuklatamiz
    listener.stop()

    assert listener.poll() is None


def _build_controller(keyboard_listener):
    """Mock komponentlar bilan minimal BotController quradi (9.7 uchun).

    Faqat `stop_safely` uchun zarur bo'lgan komponentlar haqiqiy yoki mock:
    state_machine haqiqiy GameStateMachine, keyboard_listener mock.
    """
    from lumberjack_bot.bot_controller import BotController
    from lumberjack_bot.models import BotConfig
    from lumberjack_bot.state_machine import GameStateMachine

    return BotController(
        config=BotConfig(target_score=10),
        screen_capture=Mock(),
        branch_detector=Mock(),
        click_simulator=Mock(),
        score_counter=Mock(),
        state_machine=GameStateMachine(),
        keyboard_listener=keyboard_listener,
        calibration=Mock(),
        delay_generator=Mock(),
    )


def test_stop_safely_calls_keyboard_stop_and_transitions_to_stopped():
    """9.7: STOPPED ga o'tishda KeyboardListener.stop() chaqiriladi (mock).

    `stop_safely` chaqirilganda holat mashinasi STOPPED ga o'tishi va
    injektsiya qilingan keyboard_listener.stop() chaqirilishi kerak
    (Requirement 6.5).
    """
    mock_listener = Mock()
    controller = _build_controller(mock_listener)

    # Boshlanishi IDLE; RUNNING ga o'tkazamiz, keyin xavfsiz to'xtatamiz.
    controller.state_machine.on_key(ControlKey.START)
    assert controller.state_machine.state is State.RUNNING

    controller.stop_safely("test sababi")

    # Holat STOPPED ga o'tgan bo'lishi kerak.
    assert controller.state_machine.state is State.STOPPED
    # KeyboardListener.stop() aniq bir marta chaqirilgan bo'lishi kerak.
    mock_listener.stop.assert_called_once()


def test_stop_safely_is_idempotent():
    """9.7 (qo'shimcha): stop_safely takroran chaqirilsa ham xavfsiz.

    Holat allaqachon STOPPED bo'lsa ham keyboard_listener.stop() chaqiriladi
    va istisno ko'tarilmaydi.
    """
    mock_listener = Mock()
    controller = _build_controller(mock_listener)

    controller.stop_safely("birinchi")
    controller.stop_safely("ikkinchi")

    assert controller.state_machine.state is State.STOPPED
    # Har chaqiruvda stop() chaqiriladi (idempotent to'xtatish).
    assert mock_listener.stop.call_count == 2
