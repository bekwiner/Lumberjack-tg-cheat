"""Ekran suratga olish moduli (I/O qatlami).

Ushbu modul ekran piksellarini o'qiydigan `ScreenCaptureModule` ni belgilaydi.
Birlamchi backend sifatida `PIL.ImageGrab`, muqobil sifatida `cv2` (OpenCV)
ishlatiladi. Backend kutubxonalari kechiktirilgan (lazy) tarzda import
qilinadi, shuning uchun ulardan biri o'rnatilmagan bo'lsa ham modul yuklanadi
(import vaqtida xato bermaydi). Backend faqat birinchi piksel o'qishda tanlanadi.

Dizayn hujjatining "ScreenCaptureModule" bo'limiga mos keladi.

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
Requirements: 2.1, 2.6
"""

from typing import Optional

from .models import BranchSample, CanvasCoords, PixelReadError, RGBColor


class ScreenCaptureModule:
    """Ekran piksellarini o'qiydigan apparatga bog'liq komponent.

    Backend tanlovi:
      - `pil`: `PIL.ImageGrab` orqali bitta pikselli surat olish.
      - `cv2`: butun ekranni suratga olib (mss/numpy emas, OpenCV orqali),
        kerakli pikselni indekslash.

    Backend birinchi `read_pixel` chaqiruvida aniqlanadi va keshlanadi.
    Hech qaysi backend mavjud bo'lmasa yoki o'qish amalga oshmasa,
    `PixelReadError` ko'tariladi (Requirement 2.6).
    """

    def __init__(self) -> None:
        # Tanlangan backend nomi ("pil" yoki "cv2"); hali aniqlanmagan bo'lsa None.
        self._backend: Optional[str] = None

    # -- Backend aniqlash -------------------------------------------------

    def _select_backend(self) -> str:
        """Mavjud backend'ni aniqlaydi va nomini qaytaradi.

        Avval `PIL.ImageGrab`, so'ng `cv2` sinab ko'riladi. Import lazy
        tarzda shu yerda bajariladi. Hech biri topilmasa `PixelReadError`.
        """
        if self._backend is not None:
            return self._backend

        # Birlamchi tanlov: PIL.ImageGrab
        try:
            from PIL import ImageGrab  # noqa: F401  (mavjudligini tekshirish)

            self._backend = "pil"
            return self._backend
        except Exception:
            # PIL mavjud emas yoki yuklab bo'lmadi -> muqobilga o'tamiz.
            pass

        # Muqobil tanlov: OpenCV
        try:
            import cv2  # noqa: F401  (mavjudligini tekshirish)

            self._backend = "cv2"
            return self._backend
        except Exception:
            pass

        # Hech qanday backend mavjud emas.
        raise PixelReadError(
            "Ekran suratga olish backend'i topilmadi: 'PIL' yoki 'cv2' "
            "kutubxonalaridan kamida bittasi o'rnatilgan bo'lishi kerak."
        )

    # -- Asosiy API -------------------------------------------------------

    def read_pixel(self, x: int, y: int) -> RGBColor:
        """Berilgan koordinatadagi piksel rangini `RGBColor` sifatida qaytaradi.

        O'qib bo'lmasa (backend yo'q, koordinata ekrandan tashqarida yoki
        surat olishda xato) `PixelReadError` ko'taradi (Requirement 2.6).
        """
        backend = self._select_backend()
        if backend == "pil":
            return self._read_pixel_pil(x, y)
        return self._read_pixel_cv2(x, y)

    def read_branch_points(self, coords: CanvasCoords) -> BranchSample:
        """Chap va o'ng tekshirish nuqtalaridagi ranglarni o'qiydi.

        Natijani `BranchSample` (left_color, right_color) sifatida qaytaradi
        (Requirement 2.1). Har qanday o'qish xatosi `PixelReadError` sifatida
        yuqoriga uzatiladi.
        """
        left_color = self.read_pixel(coords.left.x, coords.left.y)
        right_color = self.read_pixel(coords.right.x, coords.right.y)
        return BranchSample(left_color=left_color, right_color=right_color)

    # -- Backend amallari -------------------------------------------------

    def _read_pixel_pil(self, x: int, y: int) -> RGBColor:
        """`PIL.ImageGrab` orqali bitta pikselni o'qiydi.

        Faqat kerakli piksel atrofidagi 1x1 bbox suratga olinadi, bu tezroq
        va xotira tejamkor (Requirement 2.1 dagi vaqt chegarasiga yordam beradi).
        """
        try:
            from PIL import ImageGrab

            # bbox = (left, top, right, bottom); 1x1 sohani olamiz.
            image = ImageGrab.grab(bbox=(x, y, x + 1, y + 1))
            pixel = image.getpixel((0, 0))
        except Exception as exc:  # surat olish yoki kutubxona xatosi
            raise PixelReadError(
                f"PIL.ImageGrab orqali ({x}, {y}) pikselni o'qib bo'lmadi: {exc}"
            ) from exc

        return self._to_rgb(pixel, x, y)

    def _read_pixel_cv2(self, x: int, y: int) -> RGBColor:
        """OpenCV (cv2) orqali ekrandan pikselni o'qiydi.

        cv2 da to'g'ridan-to'g'ri ekran suratga olish yo'q, shuning uchun
        ekran surati `PIL.ImageGrab` mavjud bo'lmaganida `numpy`/`cv2` orqali
        olingan tasvirdan indekslanadi. Bu yerda ekran surati `cv2` bilan
        BGR formatida bo'lishi mumkinligini hisobga olamiz va RGB ga o'giramiz.
        """
        try:
            import numpy as np
            from PIL import ImageGrab  # cv2 backend ham surat manbasiga muhtoj

            frame = np.asarray(ImageGrab.grab())
            # frame[y, x] -> (R, G, B) PIL manbasida.
            pixel = frame[y, x]
        except Exception:
            # PIL yo'q bo'lsa, mss orqali sinab ko'ramiz (agar mavjud bo'lsa).
            try:
                import cv2
                import mss
                import numpy as np

                with mss.mss() as sct:
                    shot = sct.grab({"left": x, "top": y, "width": 1, "height": 1})
                    arr = np.asarray(shot)  # BGRA formatida
                bgr = arr[0, 0][:3]
                # BGR -> RGB
                pixel = (int(bgr[2]), int(bgr[1]), int(bgr[0]))
                # cv2 import qilingani backend mavjudligini tasdiqlaydi.
                _ = cv2
            except Exception as exc:
                raise PixelReadError(
                    f"OpenCV backend orqali ({x}, {y}) pikselni o'qib bo'lmadi: {exc}"
                ) from exc

        return self._to_rgb(pixel, x, y)

    # -- Yordamchi --------------------------------------------------------

    @staticmethod
    def _to_rgb(pixel, x: int, y: int) -> RGBColor:
        """Backend qaytargan piksel qiymatini `RGBColor` ga aylantiradi.

        Piksel RGB yoki RGBA (4 kanal) yoki kulrang (bitta son) bo'lishi
        mumkin. Mos kelmagan formatda `PixelReadError` ko'tariladi.
        """
        try:
            # Kulrang (grayscale) -> bir xil R=G=B.
            if isinstance(pixel, (int, float)):
                value = int(pixel)
                return RGBColor(value, value, value)

            # Ketma-ketlik (tuple/list/ndarray) -> kamida 3 kanal kerak.
            channels = list(pixel)
            if len(channels) < 3:
                raise ValueError(f"kutilmagan piksel formati: {pixel!r}")
            r, g, b = int(channels[0]), int(channels[1]), int(channels[2])
            return RGBColor(r, g, b)
        except PixelReadError:
            raise
        except Exception as exc:
            raise PixelReadError(
                f"({x}, {y}) piksel qiymatini RGB ga aylantirib bo'lmadi: {exc}"
            ) from exc
