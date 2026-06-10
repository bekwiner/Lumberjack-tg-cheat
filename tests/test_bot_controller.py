"""BotController uchun unit testlar (12.2 va 12.3 vazifalari).

Bu testlar orkestratsiya qatlamining ikki muhim xulqini qoplaydi:

  - 12.2: bitta kesish tsiklidan keyin (`increment()` chaqirilgach)
    yangilangan ballning terminalga chop etilishi (Requirement 3.4).
  - 12.3: xavfli holat va xato boshqaruvi:
      * `Decision.DANGER_STOP` da xavf indikatsiyasi ko'rsatilib, kesish
        xavfsiz to'xtatilishi (Requirement 2.5).
      * `PixelReadError` da xato indikatsiyasi ko'rsatilib, kesish xavfsiz
        to'xtatilishi (Requirement 2.6).

Test strategiyasi:
  - Holat o'tishlari haqiqiy `GameStateMachine` orqali tekshiriladi
    (RUNNING ga `on_key(START)` bilan o'tkaziladi), shunda STOPPED ga
    o'tish haqiqatan amalga oshganini ko'rish mumkin.
  - `ScoreCounter` haqiqiy obyekt — chop etilgan ball qiymatini ishonchli
    tekshirish uchun.
  - Apparat/I/O komponentlari (screen_capture, branch_detector,
    click_simulator, keyboard_listener, calibration, delay_generator)
    `unittest.mock` orqali mock qilinadi.

Eslatma: barcha holatlar mock qilinadi — testlar haqiqiy ekran/sichqoncha/
klaviaturadan mustaqil ishlaydi.
"""

from unittest.mock import MagicMock

from lumberjack_bot.bot_controller import BotController
from lumberjack_bot.models import (
    BotConfig,
    BranchSample,
    CanvasCoords,
    ControlKey,
    Decision,
    PixelReadError,
    Point,
    RGBColor,
    Side,
    State,
)
from lumberjack_bot.score_counter import ScoreCounter
from lumberjack_bot.state_machine import GameStateMachine


# Yaroqli kalibrlangan koordinatalar (chap/o'ng/yuqori nuqtalar).
_COORDS = CanvasCoords(left=Point(10, 20), right=Point(30, 40), top=Point(15, 5))

# Namuna piksel namunasi (qaror mock qilinadi, shuning uchun ranglar muhim emas).
_SAMPLE = BranchSample(
    left_color=RGBColor(139, 90, 43),
    right_color=RGBColor(0, 0, 0),
)


def _build_controller(target_score=10):
    """Mock komponentlar bilan RUNNING holatidagi BotController quradi.

    Haqiqiy `GameStateMachine` RUNNING ga o'tkaziladi va haqiqiy
    `ScoreCounter` ishlatiladi; qolgan barcha komponentlar mock qilinadi.
    `sleeper` ham mock — testlar real vaqt kutmaydi.
    """
    config = BotConfig(target_score=target_score)

    screen_capture = MagicMock()
    screen_capture.read_branch_points.return_value = _SAMPLE

    branch_detector = MagicMock()
    click_simulator = MagicMock()
    keyboard_listener = MagicMock()
    calibration = MagicMock()

    delay_generator = MagicMock()
    delay_generator.next_delay_ms.return_value = 0.0

    # Haqiqiy holat mashinasi: 'S' bilan RUNNING ga o'tkazamiz.
    state_machine = GameStateMachine()
    state_machine.on_key(ControlKey.START)
    assert state_machine.state is State.RUNNING

    # Haqiqiy ball sanagich.
    score_counter = ScoreCounter(target_score=target_score)

    controller = BotController(
        config=config,
        screen_capture=screen_capture,
        branch_detector=branch_detector,
        click_simulator=click_simulator,
        score_counter=score_counter,
        state_machine=state_machine,
        keyboard_listener=keyboard_listener,
        calibration=calibration,
        delay_generator=delay_generator,
        coords=_COORDS,
        initial_hero_side=Side.LEFT,
        sleeper=MagicMock(),  # real vaqt kutmaslik uchun
    )
    return controller


# ---------------------------------------------------------------------------
# 12.2 — Ball chop etilishi (Requirement 3.4)
# ---------------------------------------------------------------------------


def test_score_is_printed_to_terminal_after_increment(capsys):
    """12.2: increment() dan keyin yangilangan ball terminalga chop etiladi.

    STAY_AND_CHOP qarorida bitta kesish tsikli bajariladi; ball 0 dan 1 ga
    oshadi va "Ball: 1" terminalga chop etilishi kerak (Requirement 3.4).
    """
    controller = _build_controller(target_score=10)
    controller.branch_detector.decide.return_value = Decision.STAY_AND_CHOP

    result = controller._run_one_cycle()

    # Tsikl davom etishi mumkin (xavfli holat/xato yo'q).
    assert result is True
    # Ball haqiqatan 1 ga oshgan bo'lishi kerak.
    assert controller.score_counter.current == 1
    # Joriy tomonda kesish bajarilgan (STAY_AND_CHOP).
    controller.click_simulator.chop.assert_called_once_with(Side.LEFT, _COORDS)

    # Terminal chiqishida yangilangan ball ko'rinishi kerak (Requirement 3.4).
    out = capsys.readouterr().out
    assert "Ball: 1" in out


def test_score_print_reflects_multiple_increments(capsys):
    """12.2 (qo'shimcha): ketma-ket tsikllarda har bir yangi ball chop etiladi."""
    controller = _build_controller(target_score=10)
    controller.branch_detector.decide.return_value = Decision.STAY_AND_CHOP

    controller._run_one_cycle()
    controller._run_one_cycle()
    controller._run_one_cycle()

    assert controller.score_counter.current == 3
    out = capsys.readouterr().out
    # Har bir oshirishdan keyin mos ball qiymati chop etilgan bo'lishi kerak.
    assert "Ball: 1" in out
    assert "Ball: 2" in out
    assert "Ball: 3" in out


# ---------------------------------------------------------------------------
# 12.3 — Xavfli holat va xato boshqaruvi (Requirement 2.5, 2.6)
# ---------------------------------------------------------------------------


def test_danger_stop_indicates_danger_and_stops_safely(capsys):
    """12.3: DANGER_STOP da xavf indikatsiyasi va xavfsiz to'xtash (Req 2.5).

    branch_detector.decide -> DANGER_STOP bo'lganda:
      - _run_one_cycle() False qaytaradi,
      - holat mashinasi STOPPED ga o'tadi,
      - keyboard_listener.stop() chaqiriladi (Req 6.5),
      - terminalga xavf indikatsiyasi chop etiladi.
    """
    controller = _build_controller(target_score=10)
    controller.branch_detector.decide.return_value = Decision.DANGER_STOP

    result = controller._run_one_cycle()

    # Tsikl xavfsiz to'xtash uchun False qaytarishi kerak.
    assert result is False
    # Holat STOPPED ga o'tgan bo'lishi kerak.
    assert controller.state_machine.state is State.STOPPED
    # Klaviatura kuzatuvi to'xtatilgan bo'lishi kerak (Req 6.5).
    controller.keyboard_listener.stop.assert_called_once()
    # Ball oshmasligi kerak (kesish bajarilmadi).
    assert controller.score_counter.current == 0
    # Hech qanday bosish bajarilmasligi kerak (xavfli holat).
    controller.click_simulator.chop.assert_not_called()
    controller.click_simulator.move_then_chop.assert_not_called()

    # Xavf indikatsiyasi terminalga chop etilishi kerak (Req 2.5).
    out = capsys.readouterr().out
    assert "XAVF" in out


def test_pixel_read_error_indicates_error_and_stops_safely(capsys):
    """12.3: PixelReadError da xato indikatsiyasi va xavfsiz to'xtash (Req 2.6).

    screen_capture.read_branch_points PixelReadError ko'targanda:
      - _run_one_cycle() False qaytaradi,
      - holat mashinasi STOPPED ga o'tadi,
      - keyboard_listener.stop() chaqiriladi (Req 6.5),
      - terminalga xato indikatsiyasi chop etiladi.
    """
    controller = _build_controller(target_score=10)
    controller.screen_capture.read_branch_points.side_effect = PixelReadError(
        "piksel o'qib bo'lmadi"
    )

    result = controller._run_one_cycle()

    # Tsikl xavfsiz to'xtash uchun False qaytarishi kerak.
    assert result is False
    # Holat STOPPED ga o'tgan bo'lishi kerak.
    assert controller.state_machine.state is State.STOPPED
    # Klaviatura kuzatuvi to'xtatilgan bo'lishi kerak (Req 6.5).
    controller.keyboard_listener.stop.assert_called_once()
    # Qaror chiqarilmasligi va bosish bajarilmasligi kerak.
    controller.branch_detector.decide.assert_not_called()
    controller.click_simulator.chop.assert_not_called()

    # Xato indikatsiyasi terminalga chop etilishi kerak (Req 2.6).
    out = capsys.readouterr().out
    assert "xato" in out.lower()
