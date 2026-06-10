"""Klaviatura tugmalarini kuzatuvchi komponent (I/O qatlami).

Ushbu modul 'S' (boshlash) va 'Q' (to'xtatish) boshqaruv tugmalarini
kuzatuvchi `KeyboardListener` sinfini belgilaydi. Komponent `keyboard`
kutubxonasiga tayanadi (Requirement 1.3, 6.3, 6.5).

Eslatma: bu apparatga bog'liq I/O qatlami. `keyboard` kutubxonasi
dangasa (lazy) import qilinadi, shunda kutubxona o'rnatilmagan bo'lsa
ham modul yuklanaveradi va sof mantiqiy qismlar test qilinishi mumkin.
Kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

from typing import Optional

from .models import ControlKey


# 'S'/'Q' tugmalarini ControlKey ga moslashtiruvchi xarita (Requirement 6.3).
# Kalitlar kichik harfda — `keyboard` kutubxonasi tugma nomlarini kichik
# harfda qaytaradi.
_KEY_MAP = {
    "s": ControlKey.START,
    "q": ControlKey.STOP,
}


class KeyboardListener:
    """'S'/'Q' tugmalarini kuzatadi va ControlKey sifatida qaytaradi.

    Bot ishlash davomida `poll()` kamida har 100 millisekundda chaqirilib,
    bosilgan tugmani qaytaradi (Requirement 6.3). Dastur yakunlanishida
    `stop()` kuzatishni darhol to'xtatadi (Requirement 6.5).
    """

    def __init__(self) -> None:
        # _active: kuzatuv faolligini bildiradi. stop() chaqirilgach False
        # bo'lib qoladi va poll() darhol None qaytaradi (Requirement 6.5).
        self._active = True
        # _keyboard: dangasa import qilingan `keyboard` moduli kefshi (cache).
        # Birinchi poll() chaqiruvida yuklanadi.
        self._keyboard = None

    def _get_keyboard(self):
        """`keyboard` kutubxonasini dangasa (lazy) import qiladi va kefshlaydi.

        Import faqat kerak bo'lganda bajariladi, shunda modul yuklanishi
        kutubxona mavjudligiga bog'liq bo'lmaydi.
        """
        if self._keyboard is None:
            import keyboard  # dangasa import — yuqoridagi izohga qarang

            self._keyboard = keyboard
        return self._keyboard

    def poll(self) -> Optional[ControlKey]:
        """Bosilgan 'S' yoki 'Q' tugmasini ControlKey sifatida qaytaradi.

        'S' bosilsa `ControlKey.START`, 'Q' bosilsa `ControlKey.STOP`
        qaytadi. Hech qaysi tugma bosilmagan bo'lsa yoki kuzatuv to'xtatilgan
        bo'lsa `None` qaytadi. Bu metod kamida har 100 ms da chaqirilishi
        kutiladi (Requirement 6.3).
        """
        # Kuzatuv to'xtatilgan bo'lsa hech narsa qaytarmaymiz (Requirement 6.5).
        if not self._active:
            return None

        keyboard = self._get_keyboard()

        # Har bir tugmani tekshiramiz; START STOP dan oldin tekshiriladi.
        for key_name, control_key in _KEY_MAP.items():
            if keyboard.is_pressed(key_name):
                return control_key

        return None

    def stop(self) -> None:
        """Tugma kuzatishni darhol to'xtatadi (Requirement 6.5).

        Chaqirilgandan so'ng `poll()` doimo `None` qaytaradi va, agar
        `keyboard` kutubxonasi yuklangan bo'lsa, barcha ro'yxatdan o'tgan
        hotkey/hook'lar tozalanadi.
        """
        self._active = False

        # Kutubxona allaqachon yuklangan bo'lsagina tozalashga harakat qilamiz.
        if self._keyboard is not None:
            try:
                self._keyboard.unhook_all()
            except Exception:
                # Tozalash xatosi to'xtatish jarayonini to'sib qo'ymasligi kerak.
                pass
