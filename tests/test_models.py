"""Ma'lumot modellari uchun smoke testlar.

Ushbu testlar enum'lar, dataclass'lar va istisno sinfining to'g'ri
import qilinishini va asosiy xususiyatlarini tekshiradi (Requirement 7.1
uchun poydevor).
"""

from lumberjack_bot.models import (
    BotConfig,
    BranchSample,
    CanvasCoords,
    ControlKey,
    Decision,
    PixelReadError,
    Point,
    RGBColor,
    ScreenSize,
    Side,
    State,
)


def test_enums_have_expected_values():
    assert Side.LEFT.value == "left"
    assert Side.RIGHT.value == "right"
    assert Decision.MOVE_TO_SAFE.value == "move_to_safe"
    assert Decision.STAY_AND_CHOP.value == "stay_and_chop"
    assert Decision.DANGER_STOP.value == "danger_stop"
    assert ControlKey.START.value == "S"
    assert ControlKey.STOP.value == "Q"
    assert State.IDLE.value == "idle"
    assert State.RUNNING.value == "running"
    assert State.STOPPED.value == "stopped"


def test_rgbcolor_is_frozen():
    color = RGBColor(10, 20, 30)
    assert (color.r, color.g, color.b) == (10, 20, 30)
    try:
        color.r = 99  # type: ignore[misc]
        assert False, "RGBColor o'zgarmas (frozen) bo'lishi kerak"
    except Exception:
        pass


def test_point_and_screensize():
    p = Point(5, 7)
    s = ScreenSize(1920, 1080)
    assert (p.x, p.y) == (5, 7)
    assert (s.width, s.height) == (1920, 1080)


def test_canvas_coords_and_branch_sample():
    coords = CanvasCoords(left=Point(1, 2), right=Point(3, 4), top=Point(5, 6))
    sample = BranchSample(left_color=RGBColor(0, 0, 0), right_color=RGBColor(255, 255, 255))
    assert coords.left == Point(1, 2)
    assert coords.right == Point(3, 4)
    assert coords.top == Point(5, 6)
    assert sample.left_color == RGBColor(0, 0, 0)
    assert sample.right_color == RGBColor(255, 255, 255)


def test_botconfig_defaults():
    cfg = BotConfig(target_score=269)
    assert cfg.target_score == 269
    assert cfg.tolerance == 30
    assert cfg.min_delay_ms == 100
    assert cfg.max_delay_ms == 400
    assert cfg.branch_color == RGBColor(139, 90, 43)


def test_pixel_read_error_is_exception():
    assert issubclass(PixelReadError, Exception)
    try:
        raise PixelReadError("o'qib bo'lmadi")
    except PixelReadError as e:
        assert str(e) == "o'qib bo'lmadi"
