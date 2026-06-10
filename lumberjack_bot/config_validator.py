"""ConfigValidator — konfiguratsiya validatsiyasi (sof mantiq).

Ushbu modul foydalanuvchi sozlay oladigan qiymatlarni (target_score,
kechikish oralig'i va tolerance) apparatdan mustaqil ravishda tekshiradi.
Validatsiya ishga tushishdan oldingi "fail-fast" yondashuvga mos keladi:
yaroqsiz qiymatda kesish boshlanmaydi va mavjud sozlama o'zgartirilmaydi.

Dizayn hujjatining "Validatsiya qoidalari" jadvaliga mos keladi:
    target_score : butun son, 1 <= x <= 1_000_000  (Requirement 3.1, 3.2)
    tolerance    : butun son, 0 <= x <= 255          (Requirement 2.4)
    delay        : 10 <= min <= max <= 5000          (Requirement 5.2, 5.3)

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

from dataclasses import dataclass
from typing import Optional


# target_score uchun ruxsat etilgan oraliq (Requirement 3.1)
TARGET_SCORE_MIN = 1
TARGET_SCORE_MAX = 1_000_000

# tolerance uchun ruxsat etilgan oraliq (Requirement 2.4)
TOLERANCE_MIN = 0
TOLERANCE_MAX = 255

# kechikish (millisekund) uchun ruxsat etilgan oraliq (Requirement 5.2)
DELAY_MIN_MS = 10
DELAY_MAX_MS = 5000


@dataclass(frozen=True)
class ValidationResult:
    """Validatsiya natijasi.

    ok        : qiymat qabul qilinganmi (True/False)
    reason    : rad etilganda sababni tushuntiruvchi xabar; qabul
                qilinganda None bo'ladi (Requirement 5.3 — rad etish sababi)
    """

    ok: bool
    reason: Optional[str] = None


def _is_int(value: object) -> bool:
    """Qiymat haqiqiy butun son ekanligini tekshiradi.

    bool turi Python'da int dan meros oladi, ammo biz uni butun son
    sifatida qabul qilmaymiz (masalan True 1 ga teng bo'lib qolmasligi
    uchun). float yoki boshqa turlar ham rad etiladi.
    """

    return isinstance(value, int) and not isinstance(value, bool)


def validate_target_score(value: object) -> ValidationResult:
    """target_score qiymatini tekshiradi (Requirement 3.1, 3.2).

    Qiymat faqat va faqat butun son hamda
    `1 <= value <= 1_000_000` bo'lganda qabul qilinadi. Aks holda rad
    etiladi va kesish boshlanmaydi (sabab qaytariladi).
    """

    if not _is_int(value):
        return ValidationResult(
            ok=False,
            reason="target_score butun son bo'lishi kerak",
        )

    if value < TARGET_SCORE_MIN or value > TARGET_SCORE_MAX:
        return ValidationResult(
            ok=False,
            reason=(
                f"target_score {TARGET_SCORE_MIN} dan {TARGET_SCORE_MAX} gacha "
                f"bo'lishi kerak, berilgan: {value}"
            ),
        )

    return ValidationResult(ok=True)


def validate_delay(min_ms: object, max_ms: object) -> ValidationResult:
    """Kechikish oralig'ini tekshiradi (Requirement 5.2, 5.3).

    Juftlik faqat va faqat `10 <= min_ms <= max_ms <= 5000` bo'lganda
    qabul qilinadi. Rad etilganda sabab qaytariladi; chaqiruvchi tomon
    oldingi amaldagi sozlamani o'zgarmagan holda saqlab qolishi kerak
    (bu funksiya hech qanday holatni o'zgartirmaydi — sof mantiq).
    """

    if not _is_int(min_ms) or not _is_int(max_ms):
        return ValidationResult(
            ok=False,
            reason="kechikish qiymatlari butun son bo'lishi kerak",
        )

    if min_ms < DELAY_MIN_MS or min_ms > DELAY_MAX_MS:
        return ValidationResult(
            ok=False,
            reason=(
                f"min_ms {DELAY_MIN_MS}–{DELAY_MAX_MS} ms oralig'ida bo'lishi "
                f"kerak, berilgan: {min_ms}"
            ),
        )

    if max_ms < DELAY_MIN_MS or max_ms > DELAY_MAX_MS:
        return ValidationResult(
            ok=False,
            reason=(
                f"max_ms {DELAY_MIN_MS}–{DELAY_MAX_MS} ms oralig'ida bo'lishi "
                f"kerak, berilgan: {max_ms}"
            ),
        )

    if min_ms > max_ms:
        return ValidationResult(
            ok=False,
            reason=(
                f"min_ms ({min_ms}) max_ms ({max_ms}) dan katta bo'lmasligi kerak"
            ),
        )

    return ValidationResult(ok=True)


def validate_tolerance(value: object) -> ValidationResult:
    """tolerance qiymatini tekshiradi (Requirement 2.4).

    Qiymat faqat va faqat butun son hamda `0 <= value <= 255`
    bo'lganda qabul qilinadi.
    """

    if not _is_int(value):
        return ValidationResult(
            ok=False,
            reason="tolerance butun son bo'lishi kerak",
        )

    if value < TOLERANCE_MIN or value > TOLERANCE_MAX:
        return ValidationResult(
            ok=False,
            reason=(
                f"tolerance {TOLERANCE_MIN} dan {TOLERANCE_MAX} gacha bo'lishi "
                f"kerak, berilgan: {value}"
            ),
        )

    return ValidationResult(ok=True)
