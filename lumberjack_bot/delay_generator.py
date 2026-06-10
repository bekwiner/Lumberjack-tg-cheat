"""Tasodifiy kechikish generatori (sof mantiq).

Ushbu modul kesishlar orasiga inson tezligiga o'xshash, belgilangan
oraliqda bir tekis taqsimlangan tasodifiy kechikishni hosil qiluvchi
`DelayGenerator` sinfini belgilaydi (Requirement 5.1).

Eslatma: bu komponent apparatdan mustaqil — u faqat `random.uniform`
dan foydalanadi, shuning uchun mustaqil ravishda test qilinadi.
"""

import random


class DelayGenerator:
    """[min_ms, max_ms] oralig'ida bir tekis tasodifiy kechikish hosil qiladi."""

    def __init__(self, min_ms: int, max_ms: int):
        # min_ms: minimal kechikish (millisekund)
        # max_ms: maksimal kechikish (millisekund)
        # Eslatma: oraliq validatsiyasi ConfigValidator zimmasida
        # (Requirement 5.2, 5.3); bu yerda faqat sof generatsiya mantig'i.
        self.min_ms = min_ms
        self.max_ms = max_ms

    def next_delay_ms(self) -> float:
        """[min_ms, max_ms] oralig'ida bir tekis tasodifiy kechikish qaytaradi.

        `random.uniform` ikkala chegarani ham qamrab oluvchi bir tekis
        taqsimotdan qiymat qaytaradi (Requirement 5.1).
        """
        return random.uniform(self.min_ms, self.max_ms)
