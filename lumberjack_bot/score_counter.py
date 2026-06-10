"""Ball sanagich (score counter) — sof mantiqiy komponent.

Ushbu modul muvaffaqiyatli kesishlar (Chop) sonini hisoblaydi va
maqsadli ballga (target_score) yetilganini aniqlaydi. Apparatdan
mustaqil, ya'ni I/O amallarisiz ishlaydi va mustaqil test qilinadi.

Dizayn hujjatining "ScoreCounter (sof mantiq)" bo'limiga mos keladi.

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""


class ScoreCounter:
    """Joriy ballni boshqaradi va to'xtash shartini hisoblaydi."""

    def __init__(self, target_score: int):
        # joriy ball noldan boshlanadi
        self.current = 0
        # maqsadli ball (target_score)
        self.target = target_score

    def increment(self) -> int:
        """Ballni 1 ga oshiradi va yangi qiymatni qaytaradi.

        Requirement 3.3 ga muvofiq, har bir muvaffaqiyatli kesishda
        joriy ball bir birlikka oshadi.
        """
        self.current += 1
        return self.current

    def target_reached(self) -> bool:
        """current >= target bo'lsa True qaytaradi.

        Requirement 3.5 ga muvofiq, joriy ball maqsadli ballga teng
        yoki undan katta bo'lganda to'xtash sharti bajariladi.
        """
        return self.current >= self.target
