"""Kalibrlash moduli (CalibrationModule).

Ushbu modul o'yin oynasi (Canvas) koordinatalarini interaktiv sozlash
imkonini beruvchi `CalibrationModule` sinfini belgilaydi. Dizayn
hujjatining "CalibrationModule" bo'limiga hamda Requirement 4 ga mos
keladi.

Arxitektura: apparatga bog'liq interaktiv I/O (`run()` — `pyautogui`
va `keyboard` dan foydalanadi) sof mantiqiy qismlardan (`validate_coord`,
`set_point`, `save_coords`, `load_coords` — xotiradagi saqlash) ataylab
ajratilgan. Bu sof qismlarni apparatdan mustaqil ravishda test qilish
imkonini beradi (Property 4 va Property 11).

Eslatma: `pyautogui` va `keyboard` import qilinishi dangasa (lazy) —
faqat `run()` chaqirilganda amalga oshiriladi, shunda sof mantiqni
test qilishda bu kutubxonalar talab qilinmaydi.

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

import time
from typing import Callable, Dict, Optional

from .models import CanvasCoords, Point, ScreenSize

# Joriy sichqoncha koordinatasini ko'rsatish oralig'i (~100 ms, Requirement 4.3)
_POLL_INTERVAL_S = 0.1

# Foydalanuvchi nuqtani tasdiqlash uchun bosadigan tugma
_CONFIRM_KEY = "space"

# Kalibrlanadigan nuqtalar tartibi va ularning raqamlangan ko'rsatmalari
# (Requirement 4.1, 4.2). Tartib muhim: chap -> o'ng -> yuqori.
_POINT_PROMPTS = (
    ("left", "Chap shox tekshirish nuqtasi"),
    ("right", "O'ng shox tekshirish nuqtasi"),
    ("top", "Yuqori nuqta (canvas chegarasi)"),
)


class CalibrationModule:
    """Canvas koordinatalarini sozlaydi, validatsiya qiladi va saqlaydi.

    Sof mantiqiy interfeys (test qilinadigan):
      - `validate_coord(point, screen)` — koordinata yaroqliligini tekshiradi
      - `set_point(name, point)` — bitta nuqtani saqlaydi (yaroqsizda eski qoladi)
      - `save_coords(coords)` — to'liq CanvasCoords ni saqlaydi (round-trip)
      - `load_coords()` — saqlangan CanvasCoords ni qaytaradi

    Interaktiv interfeys (apparatga bog'liq):
      - `run()` — `pyautogui`/`keyboard` orqali koordinatalarni sozlaydi
    """

    def __init__(
        self,
        screen: ScreenSize,
        persist: Optional[Callable[[CanvasCoords], None]] = None,
    ):
        # ekran o'lchami — validatsiya chegaralari uchun ishlatiladi
        self.screen = screen
        # alohida sozlangan nuqtalarning xotiradagi ombori (name -> Point)
        self._points: Dict[str, Point] = {}
        # eng oxirgi muvaffaqiyatli saqlangan to'liq koordinatalar
        self._saved_coords: Optional[CanvasCoords] = None
        # ixtiyoriy doimiy saqlash (persistence) funksiyasi; agar berilsa,
        # u xato yuzaga kelganda istisno ko'tarishi mumkin (Requirement 4.6).
        # Standart holatda saqlash faqat xotirada amalga oshadi.
        self._persist = persist

    # ------------------------------------------------------------------
    # Sof mantiq (apparatdan mustaqil, test qilinadigan)
    # ------------------------------------------------------------------

    def validate_coord(self, point: Point, screen: ScreenSize) -> bool:
        """Koordinata ekran chegaralari ichida ekanini tekshiradi.

        Requirement 4.5 ga muvofiq, koordinata faqat va faqat
        `0 <= x < width` va `0 <= y < height` bo'lganda yaroqli.
        """
        return (
            0 <= point.x < screen.width
            and 0 <= point.y < screen.height
        )

    def set_point(self, name: str, point: Point) -> bool:
        """Bitta nomli nuqtani (left/right/top) validatsiya qilib saqlaydi.

        Yaroqli bo'lsa saqlaydi va `True` qaytaradi. Yaroqsiz bo'lsa
        rad etadi, oldingi saqlangan qiymatni o'zgartirmaydi va `False`
        qaytaradi (Requirement 4.5).
        """
        if not self.validate_coord(point, self.screen):
            # rad etish: oldingi qiymat (agar bo'lsa) o'zgarmaydi
            return False
        self._points[name] = point
        return True

    def get_point(self, name: str) -> Optional[Point]:
        """Saqlangan nomli nuqtani qaytaradi (yo'q bo'lsa None)."""
        return self._points.get(name)

    def save_coords(self, coords: CanvasCoords) -> bool:
        """To'liq CanvasCoords ni validatsiya qilib saqlaydi.

        Barcha uchta nuqta yaroqli bo'lishi va saqlash amali muvaffaqiyatli
        yakunlanishi kerak. Aks holda oldingi saqlangan qiymat o'zgarmasdan
        qoladi va `False` qaytariladi (Requirement 4.4, 4.5, 4.6).

        Muvaffaqiyatda saqlangan qiymat keyin `load_coords()` orqali aynan
        o'sha holatda o'qib olinadi (Property 4: round-trip).
        """
        # Avval barcha nuqtalarni validatsiya qilamiz (Requirement 4.5)
        for point in (coords.left, coords.right, coords.top):
            if not self.validate_coord(point, self.screen):
                # yaroqsiz koordinata: oldingi saqlangan qiymat o'zgarmaydi
                return False

        # Ixtiyoriy doimiy saqlash; xato bo'lsa oldingi qiymatni saqlab qolamiz
        # (Requirement 4.6).
        if self._persist is not None:
            try:
                self._persist(coords)
            except Exception:
                # saqlash xatosi: _saved_coords o'zgarmaydi
                return False

        # Muvaffaqiyat: yangi qiymatni xotirada saqlaymiz
        self._saved_coords = coords
        return True

    def load_coords(self) -> Optional[CanvasCoords]:
        """Eng oxirgi muvaffaqiyatli saqlangan CanvasCoords ni qaytaradi.

        Hech narsa saqlanmagan bo'lsa `None` qaytaradi. Saqlangan qiymat
        ko'rsatish holatidan qat'i nazar o'zgarmas qoladi (Requirement 4.4).
        """
        return self._saved_coords

    # ------------------------------------------------------------------
    # Interaktiv I/O (apparatga bog'liq) — pyautogui va keyboard
    # ------------------------------------------------------------------

    def run(self) -> Optional[CanvasCoords]:
        """Koordinatalarni interaktiv ravishda sozlaydi va saqlaydi.

        Requirement 4.1, 4.2, 4.3 ga muvofiq:
          - har bir nuqta uchun raqamlangan yozma ko'rsatma chop etadi,
          - joriy sichqoncha koordinatasini ~100 ms da yangilab ko'rsatadi,
          - foydalanuvchi tasdiqlaganda nuqtani qabul qiladi.

        Muvaffaqiyatda saqlangan `CanvasCoords` ni qaytaradi; foydalanuvchi
        bekor qilsa `None` qaytaradi.

        Eslatma: `pyautogui` va `keyboard` shu yerda dangasa import qilinadi.
        """
        # Dangasa (lazy) import — sof mantiqni test qilishda talab qilinmaydi
        import pyautogui
        import keyboard

        print("=== Kalibrlash rejimi ===")
        print(
            "Har bir nuqta uchun sichqonchani kerakli joyga olib boring "
            f"va '{_CONFIRM_KEY}' tugmasini bosing."
        )

        collected: Dict[str, Point] = {}

        # Nuqtalarni tartiblangan, raqamlangan ko'rsatmalar bilan to'playmiz
        for index, (name, description) in enumerate(_POINT_PROMPTS, start=1):
            while True:
                # Raqamlangan ko'rsatma (Requirement 4.2)
                print(f"\n{index}. {description} ni belgilang:")

                # Joriy nuqta tasdiqlanguncha koordinatani ~100 ms da ko'rsatamiz
                point = self._capture_point(pyautogui, keyboard)

                # Validatsiya (Requirement 4.5)
                if self.validate_coord(point, self.screen):
                    collected[name] = point
                    print(f"   Saqlandi: X={point.x}, Y={point.y}")
                    break

                # Yaroqsiz: xato xabar va qayta urinish (eski qiymat o'zgarmaydi)
                print(
                    f"   Xato: koordinata ({point.x}, {point.y}) ekran "
                    f"chegarasidan ({self.screen.width}x{self.screen.height}) "
                    "tashqarida. Qayta urinib ko'ring."
                )

        coords = CanvasCoords(
            left=collected["left"],
            right=collected["right"],
            top=collected["top"],
        )

        # Saqlash; xato bo'lsa oldingi qiymat saqlanadi (Requirement 4.6)
        if self.save_coords(coords):
            print("\nKoordinatalar muvaffaqiyatli saqlandi.")
            return self.load_coords()

        # Saqlash muvaffaqiyatsiz: xato indikatsiyasi, oldingi qiymat o'zgarmaydi
        print(
            "\nXato: koordinatalarni saqlab bo'lmadi. Oldingi koordinatalar "
            "o'zgarmasdan saqlanib qoldi."
        )
        return self.load_coords()

    def _capture_point(self, pyautogui, keyboard) -> Point:
        """Foydalanuvchi tasdiqlaguncha joriy sichqoncha nuqtasini ko'rsatadi.

        Har ~100 ms da joriy koordinatani terminalda yangilab turadi
        (Requirement 4.3) va tasdiqlash tugmasi bosilganda o'sha ondagi
        koordinatani `Point` sifatida qaytaradi.

        Muhim: avval tasdiqlash tugmasi QO'YIB YUBORILISHINI kutadi, shunda
        oldingi nuqtadan qolgan bosish keyingi nuqtani noto'g'ri tasdiqlamaydi
        (tugma "debounce"). So'ng yangi bosishni kutadi.
        """
        # 1) Oldingi nuqtadan qolgan bosishni tozalaymiz: tugma qo'yib
        #    yuborilmaguncha kutamiz. Bu uchala nuqtaning bir xil koordinatani
        #    olishining oldini oladi.
        while keyboard.is_pressed(_CONFIRM_KEY):
            time.sleep(_POLL_INTERVAL_S)

        # 2) Endi yangi bosishni kutamiz.
        while True:
            pos = pyautogui.position()
            x, y = int(pos[0]), int(pos[1])
            # Joriy koordinatani bir qatorda yangilab ko'rsatamiz
            print(f"\r   Joriy sichqoncha: X={x}, Y={y}   ", end="", flush=True)

            # Tasdiqlash tugmasi bosilganda joriy nuqtani qabul qilamiz
            if keyboard.is_pressed(_CONFIRM_KEY):
                print()  # yangi qatorga o'tish
                # Tugma qo'yib yuborilishini kutamiz, shunda bu bosish
                # keyingi bosqichga ham o'tib ketmaydi.
                while keyboard.is_pressed(_CONFIRM_KEY):
                    time.sleep(_POLL_INTERVAL_S)
                return Point(x=x, y=y)

            time.sleep(_POLL_INTERVAL_S)
