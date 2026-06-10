"""Ma'lumot modellari (data models).

Ushbu modul botning barcha komponentlari foydalanadigan enum'lar,
dataclass'lar va istisno (exception) sinflarini belgilaydi. Dizayn
hujjatining "Data Models" bo'limiga to'liq mos keladi.

Eslatma: kod identifikatorlari (sinf/maydon nomlari) inglizcha,
izohlar esa o'zbekcha.
"""

from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    """Qahramon (Hero) yoki shox tomonini bildiradi."""

    LEFT = "left"
    RIGHT = "right"


class Decision(Enum):
    """BranchDetector chiqaradigan qaror turlari."""

    MOVE_TO_SAFE = "move_to_safe"   # qahramon tomonida shox bor -> xavfsiz tomonga o'tish
    STAY_AND_CHOP = "stay_and_chop"  # qahramon tomonida shox yo'q -> joriy tomonda kesish
    DANGER_STOP = "danger_stop"      # ikki tomonda ham shox -> to'xtash


class ControlKey(Enum):
    """Foydalanuvchi boshqaruv tugmalari."""

    START = "S"  # kesishni boshlash
    STOP = "Q"   # kesishni to'xtatish


class State(Enum):
    """O'yin holat mashinasining holatlari."""

    IDLE = "idle"        # 'S' kutilmoqda
    RUNNING = "running"  # kesish jarayoni
    STOPPED = "stopped"  # yakunlangan


@dataclass(frozen=True)
class RGBColor:
    """RGB rang qiymati. Har bir kanal 0..255 oralig'ida."""

    r: int  # 0..255
    g: int  # 0..255
    b: int  # 0..255


@dataclass(frozen=True)
class Point:
    """Ekrandagi piksel koordinatasi."""

    x: int
    y: int


@dataclass(frozen=True)
class ScreenSize:
    """Ekran o'lchami (piksellarda)."""

    width: int
    height: int


@dataclass(frozen=True)
class CanvasCoords:
    """O'yin oynasi (Canvas) ning kalibrlangan koordinatalari."""

    left: Point    # chap shox tekshirish nuqtasi
    right: Point   # o'ng shox tekshirish nuqtasi
    top: Point     # yuqori nuqta (canvas chegarasi)


@dataclass(frozen=True)
class BranchSample:
    """Chap va o'ng nuqtalardan o'qilgan ranglar namunasi."""

    left_color: RGBColor
    right_color: RGBColor


@dataclass
class BotConfig:
    """Foydalanuvchi sozlay oladigan bot konfiguratsiyasi."""

    target_score: int                # 1..1_000_000 (Requirement 3.1)
    tolerance: int = 30              # 0..255 (Requirement 2.4)
    min_delay_ms: int = 100
    max_delay_ms: int = 400
    branch_color: RGBColor = RGBColor(139, 90, 43)  # jigarrang standart


class PixelReadError(Exception):
    """Piksel rang qiymatini o'qib bo'lmaganda ko'tariladigan istisno.

    Requirement 2.6 ga muvofiq, bu istisno ko'tarilganda bot kesishni
    to'xtatadi va xato indikatsiyasini ko'rsatadi.
    """
