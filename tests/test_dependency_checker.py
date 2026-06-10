"""DependencyChecker uchun unit (misol va edge-case) testlar.

Task 8.4 / Requirement 1.6: yetishmayotgan kutubxona holatida bot hech
qanday ekranni suratga olish, sichqoncha bosish yoki klaviatura kuzatish
I/O amalini bajarmasdan ishni to'xtatadi (fail-fast).
"""

from unittest.mock import MagicMock

from lumberjack_bot.bot_controller import BotController
from lumberjack_bot.dependency_checker import (
    MissingDependency,
    report_missing_dependencies,
)
from lumberjack_bot.models import BotConfig


def test_report_returns_false_when_missing():
    """Yetishmayotganlar bo'lsa hisobot False qaytaradi (chaqiruvchi to'xtaydi)."""
    missing = [MissingDependency("pyautogui", "pip install pyautogui")]
    assert report_missing_dependencies(missing) is False


def test_report_returns_true_when_nothing_missing():
    """Hammasi mavjud bo'lsa hisobot True qaytaradi (davom etish mumkin)."""
    assert report_missing_dependencies([]) is True


def test_check_environment_halts_without_io_when_dependency_missing():
    """Bog'liqlik yetishmasa, hech qanday I/O chaqirilmasdan to'xtaydi (1.6).

    BotController.check_environment() yetishmayotgan bog'liqlikni aniqlasa
    `False` qaytarishi va shu paytgacha screen_capture / click_simulator /
    keyboard_listener komponentlarining birortasi ham chaqirilmagan bo'lishi
    kerak.
    """
    # I/O komponentlari to'liq mock — ularning birortasi chaqirilmasligi kerak.
    screen_capture = MagicMock(name="screen_capture")
    click_simulator = MagicMock(name="click_simulator")
    keyboard_listener = MagicMock(name="keyboard_listener")

    # Sof mantiqiy komponentlar ham mock (bu testda ishlatilmaydi).
    branch_detector = MagicMock(name="branch_detector")
    score_counter = MagicMock(name="score_counter")
    state_machine = MagicMock(name="state_machine")
    calibration = MagicMock(name="calibration")
    delay_generator = MagicMock(name="delay_generator")

    # Bog'liqlik tekshiruvi yetishmayotgan kutubxona qaytaradi.
    missing = [
        MissingDependency("pyautogui", "pip install pyautogui"),
        MissingDependency("keyboard", "pip install keyboard"),
    ]
    dependency_check = MagicMock(return_value=missing)

    controller = BotController(
        config=BotConfig(target_score=100),
        screen_capture=screen_capture,
        branch_detector=branch_detector,
        click_simulator=click_simulator,
        score_counter=score_counter,
        state_machine=state_machine,
        keyboard_listener=keyboard_listener,
        calibration=calibration,
        delay_generator=delay_generator,
        dependency_check=dependency_check,
        # report uchun haqiqiy funksiya ishlatiladi (False qaytaradi).
    )

    # Muhitni tekshirish yetishmayotgan bog'liqlik sababli False bo'lishi kerak.
    assert controller.check_environment() is False

    # Tekshiruv funksiyasi chaqirilgan bo'lishi kerak.
    dependency_check.assert_called_once()

    # HECH QANDAY I/O amali chaqirilmagan bo'lishi kerak (Requirement 1.6).
    assert screen_capture.mock_calls == []
    assert click_simulator.mock_calls == []
    assert keyboard_listener.mock_calls == []


def test_run_halts_before_io_when_dependency_missing():
    """To'liq run() oqimi ham yetishmayotgan bog'liqlikda I/O siz to'xtaydi.

    run() birinchi qadamda check_environment() ni chaqiradi; u False
    qaytarsa, kalibrlash, klaviatura kuzatuvi va o'yin tsikli boshlanmaydi.
    """
    screen_capture = MagicMock(name="screen_capture")
    click_simulator = MagicMock(name="click_simulator")
    keyboard_listener = MagicMock(name="keyboard_listener")
    calibration = MagicMock(name="calibration")

    branch_detector = MagicMock(name="branch_detector")
    score_counter = MagicMock(name="score_counter")
    state_machine = MagicMock(name="state_machine")
    delay_generator = MagicMock(name="delay_generator")

    missing = [MissingDependency("PIL yoki cv2", "pip install Pillow yoki pip install opencv-python")]
    dependency_check = MagicMock(return_value=missing)

    controller = BotController(
        config=BotConfig(target_score=100),
        screen_capture=screen_capture,
        branch_detector=branch_detector,
        click_simulator=click_simulator,
        score_counter=score_counter,
        state_machine=state_machine,
        keyboard_listener=keyboard_listener,
        calibration=calibration,
        delay_generator=delay_generator,
        dependency_check=dependency_check,
    )

    # run() fail-fast: False qaytaradi.
    assert controller.run() is False

    # Kalibrlash boshlanmagan va hech qanday I/O bajarilmagan.
    assert calibration.mock_calls == []
    assert screen_capture.mock_calls == []
    assert click_simulator.mock_calls == []
    assert keyboard_listener.mock_calls == []
