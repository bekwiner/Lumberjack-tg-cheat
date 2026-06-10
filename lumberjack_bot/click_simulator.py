"""Sichqoncha bosishini simulyatsiya qiluvchi I/O komponenti.

Ushbu modul daraxt kesuvchi qahramonni boshqarish uchun sichqoncha
bosishlarini `pyautogui` orqali simulyatsiya qiluvchi `ClickSimulator`
sinfini belgilaydi (Requirement 2.2). Ketma-ket ikki bosish orasiga
inson tezligiga o'xshash tasodifiy kechikish qo'shiladi (Requirement 5.1).

Eslatma:
- Bu komponent apparatga bog'liq (I/O qatlami), shuning uchun u sof
  mantiqdan ajratilgan.
- `pyautogui` dangasa (lazy) import qilinadi — modul `pyautogui`
  o'rnatilmagan muhitda ham import qilinishi (yuklanishi) mumkin;
  kutubxona faqat haqiqiy bosish bajarilganda talab qilinadi.
- Kechikishni hosil qilish `DelayGenerator` ga topshiriladi va u
  konstruktor orqali (dependency injection) beriladi.
"""

import time

from .delay_generator import DelayGenerator
from .models import CanvasCoords, Side


def _import_pyautogui():
    """`pyautogui` ni dangasa import qiladi.

    Import alohida funksiyaga ajratilgan, shunda modulning o'zi
    `pyautogui` o'rnatilmagan bo'lsa ham muammosiz yuklanadi. Kutubxona
    yetishmasa, tushunarli xato xabari bilan ko'tariladi.
    """
    try:
        import pyautogui  # type: ignore
    except ImportError as exc:  # pragma: no cover - muhitga bog'liq
        raise ImportError(
            "pyautogui o'rnatilmagan. O'rnatish uchun: pip install pyautogui"
        ) from exc
    return pyautogui


class ClickSimulator:
    """Sichqoncha bosishlarini simulyatsiya qiladi (pyautogui asosida)."""

    def __init__(self, delay_generator: DelayGenerator):
        # delay_generator: ketma-ket bosishlar orasidagi kechikishni
        # hosil qiluvchi sof mantiqiy komponent (Requirement 5.1).
        self.delay_generator = delay_generator
        # _last_click_done: kamida bitta bosish bajarilganini bildiradi.
        # Birinchi bosishdan oldin kechikish qo'shilmaydi; kechikish
        # faqat KETMA-KET ikki bosish ORASIGA qo'shiladi.
        self._last_click_done = False

    def chop(self, side: Side, coords: CanvasCoords) -> None:
        """Berilgan tomonda bitta kesish (sichqoncha bosishi) bajaradi.

        LEFT tomon `coords.left` nuqtasiga, RIGHT tomon esa
        `coords.right` nuqtasiga yaqin joyni bosadi (Requirement 2.3).
        Agar bu bosish oldingi bosishdan keyin kelsa, ular orasiga
        tasodifiy kechikish qo'shiladi (Requirement 5.1).
        """
        # Ketma-ket bosishlar orasiga inson tezligiga o'xshash kechikish.
        self._sleep_between_clicks()
        point = coords.left if side is Side.LEFT else coords.right
        self._click(point.x, point.y)

    def move_then_chop(self, side: Side, coords: CanvasCoords) -> None:
        """Qahramonni xavfsiz tomonga (Safe_Side) o'tkazib kesadi.

        `side` bu yerda qahramon o'tishi kerak bo'lgan XAVFSIZ tomon
        (Safe_Side) hisoblanadi: qahramon tomonida shox aniqlanganda
        `BranchDetector` `MOVE_TO_SAFE` qaytaradi va qahramon qarama-qarshi
        tomonga o'tkaziladi (Requirement 2.2). Sichqoncha bosishi
        qahramonni shu tomonga o'tkazadi va ayni vaqtda kesadi.
        """
        # Xavfsiz tomonga o'tish ham bitta sichqoncha bosishi bilan
        # amalga oshadi, shuning uchun `chop` mantig'idan foydalanamiz.
        self.chop(side, coords)

    def _sleep_between_clicks(self) -> None:
        """Oldingi bosish bo'lgan bo'lsa, navbatdagi bosishdan oldin kutadi."""
        if self._last_click_done:
            delay_ms = self.delay_generator.next_delay_ms()
            # DelayGenerator millisekundda qiymat qaytaradi; time.sleep
            # soniyada kutadi, shuning uchun 1000 ga bo'lamiz.
            time.sleep(delay_ms / 1000.0)

    def _click(self, x: int, y: int) -> None:
        """Berilgan ekran koordinatasida sichqoncha bosishini bajaradi."""
        pyautogui = _import_pyautogui()
        pyautogui.click(x=x, y=y)
        # Bosish bajarilganini belgilaymiz, shunda keyingi bosishdan
        # oldin kechikish qo'shiladi.
        self._last_click_done = True
