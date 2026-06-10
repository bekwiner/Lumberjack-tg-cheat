"""Shox aniqlash mantiqi (BranchDetector).

Ushbu modul daraxt tanasining chap va o'ng nuqtalaridan o'qilgan ranglarni
shox rangiga solishtirib, qahramon (Hero) qaysi harakatni bajarishi kerakligi
haqida qaror chiqaradi. Bu sof mantiqiy (apparatdan mustaqil) komponent bo'lib,
hech qanday ekran/sichqoncha I/O amalini bajarmaydi.

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.

Dizayn manbasi: design.md "BranchDetector" bo'limi va Correctness Properties 2, 3.
Talablar: 2.2, 2.3, 2.4, 2.5.
"""

from .models import RGBColor, BranchSample, Side, Decision


class BranchDetector:
    """Rang tahliliga asoslangan shox aniqlash qaroriini chiqaruvchi komponent."""

    def __init__(self, branch_color: RGBColor, tolerance: int = 30):
        """BranchDetector ni shox rangi va rang chegarasi (tolerance) bilan yaratadi.

        Args:
            branch_color: Shoxning kutilayotgan RGB rangi.
            tolerance: Rang mosligi chegarasi, 0..255 oralig'ida (Requirement 2.4).
                Sozlanmagan holatda standart qiymat 30.

        Raises:
            ValueError: tolerance butun son bo'lmasa yoki 0..255 oralig'idan
                tashqarida bo'lsa.
        """
        # tolerance butun son va 0..255 oralig'ida bo'lishi shart (Requirement 2.4).
        # bool ni rad etamiz, chunki bool int ning kichik turi hisoblanadi.
        if isinstance(tolerance, bool) or not isinstance(tolerance, int):
            raise ValueError("tolerance butun son (int) bo'lishi kerak")
        if tolerance < 0 or tolerance > 255:
            raise ValueError("tolerance 0 dan 255 gacha bo'lishi kerak")

        self.branch_color = branch_color
        self.tolerance = tolerance

    def color_matches_branch(self, sample: RGBColor) -> bool:
        """Berilgan rang shox rangiga tolerance doirasida mos kelsa True qaytaradi.

        Har bir RGB kanali mustaqil ravishda chegara ichida bo'lishi kerak:
            matches = abs(r - br) <= tol AND abs(g - bg) <= tol AND abs(b - bb) <= tol

        Args:
            sample: Tekshiriladigan RGB rang.

        Returns:
            Rang shox rangiga mos kelsa True, aks holda False.
        """
        tol = self.tolerance
        br = self.branch_color
        return (
            abs(sample.r - br.r) <= tol
            and abs(sample.g - br.g) <= tol
            and abs(sample.b - br.b) <= tol
        )

    def decide(self, sample: BranchSample, hero_side: Side) -> Decision:
        """Chap/o'ng namunalar va qahramon tomoniga qarab qaror qaytaradi.

        Qaror mantiqi (Correctness Property 2):
            - ikkala tomon ham shox rangiga mos kelsa  -> DANGER_STOP (Requirement 2.5)
            - aks holda qahramon tomoni shox rangiga mos kelsa -> MOVE_TO_SAFE (Requirement 2.2)
            - aks holda -> STAY_AND_CHOP (Requirement 2.3)

        Args:
            sample: Chap va o'ng nuqtalardan o'qilgan ranglar.
            hero_side: Qahramon turgan tomon (LEFT yoki RIGHT).

        Returns:
            Decision enum qiymati.
        """
        left_has_branch = self.color_matches_branch(sample.left_color)
        right_has_branch = self.color_matches_branch(sample.right_color)

        # Ikki tomonda ham shox bo'lsa, xavfli holat -> to'xtash (Requirement 2.5).
        if left_has_branch and right_has_branch:
            return Decision.DANGER_STOP

        # Qahramon turgan tomonni tanlaymiz.
        hero_has_branch = left_has_branch if hero_side is Side.LEFT else right_has_branch

        # Qahramon tomonida shox bo'lsa, xavfsiz tomonga o'tish (Requirement 2.2).
        if hero_has_branch:
            return Decision.MOVE_TO_SAFE

        # Qahramon tomonida shox yo'q -> joriy tomonda kesishni davom ettirish (Requirement 2.3).
        return Decision.STAY_AND_CHOP
