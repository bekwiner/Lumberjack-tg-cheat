"""lumberjack_auto.py — Telegram "Lumberjack" o'yini uchun TO'LIQ AVTOMATIK bot.

================================================================================
NIMA QILADI
================================================================================
Bu skript hech qanday qo'lda kalibrlash (sichqoncha bilan nuqta ko'rsatish)
talab qilmaydi. U:

  1. Butun ekranni rasmga oladi (Pillow.ImageGrab + numpy).
  2. Daraxt tanasining o'ziga xos JIGARRANG rangi bo'yicha o'yin maydonini va
     daraxt o'zagini AVTOMATIK topadi (eng katta vertikal jigarrang blok = tana).
  3. Tananing chap va o'ng chetidagi "xavfli zona" piksellarini doimiy
     tekshiradi: agar bir tomonda shox (jigarrang) aniqlansa, qarama-qarshi
     tomonga klik yuboradi; shox bo'lmasa joriy tomonda kesishda davom etadi.
  4. Har bir klikni sanaydi va TARGET_SCORE ga yetganda to'xtaydi.
  5. Kliklar orasida insoniy tasodifiy kechikish (0.13–0.17 s) qo'shadi.

Brauzer kodiga tegmaydi — faqat OS darajasida ekran piksellarini tahlil qiladi.

================================================================================
TALABLAR / O'RNATISH
================================================================================
    pip install Pillow numpy pyautogui keyboard

Eslatma: `keyboard` kutubxonasi global tugma kuzatuvi uchun ko'pincha
administrator/root huquqlarini talab qiladi (Windows: terminalni "Run as
administrator" bilan oching).

================================================================================
ISHLATISH
================================================================================
  1. Telegram'da "Lumberjack" o'yinini oching, o'yin oynasi to'liq ko'rinsin.
  2. Skriptni ishga tushiring:   python lumberjack_auto.py
  3. 'S' tugmasini bosing — bot ekranni skanерlaydi, daraxtni topadi va
     o'ynay boshlaydi.
  4. 'Q' tugmasini bosib istalgan vaqtda to'xtatish mumkin.
  5. Bot TARGET_SCORE ga yetganda avtomatik to'xtaydi.

XAVFSIZLIK: nazoratdan chiqsa, sichqonchani ekran burchagiga tez harakatlab
olib boring — pyautogui failsafe ishga tushib to'xtaydi. Bu loyiha faqat
ta'limiy maqsadlar uchun.
================================================================================
"""

import random
import sys
import time

# --- Tashqi kutubxonalar (dangasa importga emas, darhol tekshiramiz) ---------
try:
    import numpy as np
except ImportError:
    print("XATO: numpy o'rnatilmagan. O'rnatish: pip install numpy")
    sys.exit(1)

try:
    from PIL import ImageGrab, ImageDraw
except ImportError:
    print("XATO: Pillow o'rnatilmagan. O'rnatish: pip install Pillow")
    sys.exit(1)

try:
    import pyautogui
except ImportError:
    print("XATO: pyautogui o'rnatilmagan. O'rnatish: pip install pyautogui")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    print("XATO: keyboard o'rnatilmagan. O'rnatish: pip install keyboard")
    sys.exit(1)

# mss — ImageGrab dan ~5-10x tez ekran olish kutubxonasi (ixtiyoriy).
# O'rnatilmagan bo'lsa avtomatik ImageGrab ga qaytamiz.
try:
    import mss
    _MSS = mss.mss()
except Exception:
    _MSS = None


# ==============================================================================
# FOYDALANUVCHI SOZLAMALARI
# ==============================================================================

# Maqsadli ball: bot shu songa yetganda avtomatik to'xtaydi.
TARGET_SCORE = 902

# Daraxt shoxi/tanasining JIGARRANG rangi (siz aniqlagan qiymat).
# Auto-detection va shox aniqlash shu rangga tayanadi.
BRANCH_RGB = (161, 116, 56)

# Rang chegarasi (tolerance): piksel BRANCH_RGB ga shu chegara doirasida
# mos kelsa "jigarrang" deb hisoblanadi. Kattaroq = erkinroq moslik.
TOLERANCE = 45

# Shox sezish chegarasi: zonaning shu ulushidan ko'pi jigarrang bo'lsa shox bor.
# Log'ga ko'ra shox bo'lgan tomonda ulush ~0.10–0.12, bo'lmaganda ~0.00,
# shuning uchun 0.06 ishonchli ajratadi.
BRANCH_FRACTION = 0.06

# Kliklar orasidagi qo'shimcha kechikish (soniyada). Aniq rejimda asosiy
# kutish SETTLE_S orqali bo'ladi, shuning uchun buni kichik qoldiramiz.
MIN_DELAY_S = 0.0
MAX_DELAY_S = 0.0

# DIAGNOSTIKA rejimi: hozir o'chirilgan (o'yinni o'ynaydi).
DIAGNOSE_MODE = False

# Pyautogui xavfsizlik: sichqonchani burchakka olib borsa to'xtaydi.
pyautogui.FAILSAFE = True
# Klik orasidagi pyautogui ichki pauzasini olib tashlaymiz (o'zimiz boshqaramiz).
pyautogui.PAUSE = 0


# ==============================================================================
# RANG YORDAMCHILARI
# ==============================================================================

def brown_mask(rgb_image):
    """RGB rasmdan jigarrang piksellarning boolean maskasini qaytaradi.

    Har bir kanal BRANCH_RGB dan TOLERANCE doirasida bo'lsa True.
    rgb_image: (H, W, 3) uint8 numpy massiv.
    """
    r, g, b = BRANCH_RGB
    # int16 ga o'tkazamiz, ayirma manfiy bo'lishi mumkin.
    img = rgb_image.astype(np.int16)
    mask = (
        (np.abs(img[:, :, 0] - r) <= TOLERANCE)
        & (np.abs(img[:, :, 1] - g) <= TOLERANCE)
        & (np.abs(img[:, :, 2] - b) <= TOLERANCE)
    )
    return mask


def grab_screen_rgb(bbox=None):
    """Ekran (yoki bbox sohasi) ni RGB numpy massiv sifatida qaytaradi.

    bbox = (left, top, right, bottom) yoki None (butun ekran).
    Iloji bo'lsa tez `mss` ishlatadi, aks holda `ImageGrab` ga qaytadi.
    """
    # TEZ yo'l: mss (BGRA qaytaradi -> RGB ga o'giramiz).
    if _MSS is not None:
        try:
            if bbox is None:
                mon = _MSS.monitors[0]  # butun virtual ekran
                region = {"left": mon["left"], "top": mon["top"],
                          "width": mon["width"], "height": mon["height"]}
            else:
                left, top, right, bottom = bbox
                region = {"left": int(left), "top": int(top),
                          "width": int(right - left), "height": int(bottom - top)}
            shot = _MSS.grab(region)
            arr = np.frombuffer(shot.rgb, dtype=np.uint8)
            arr = arr.reshape(shot.height, shot.width, 3)  # mss.rgb = RGB tartibda
            return arr
        except Exception:
            pass  # mss xato bersa, ImageGrab ga qaytamiz

    # Zaxira yo'l: ImageGrab.
    image = ImageGrab.grab(bbox=bbox)
    arr = np.asarray(image)
    if arr.ndim == 3 and arr.shape[2] >= 3:
        return arr[:, :, :3]
    raise RuntimeError("Ekranni o'qib bo'lmadi (kutilmagan format).")


# ==============================================================================
# AVTOMATIK ANIQLASH (AUTO-DETECTION)
# ==============================================================================

class TreeLayout:
    """Aniqlangan daraxt joylashuvi va klik/tekshirish nuqtalari."""

    def __init__(self, trunk_cx, trunk_left, trunk_right, top_y, bottom_y):
        self.trunk_cx = trunk_cx        # tana markazi X (ekran koordinatasi)
        self.trunk_left = trunk_left    # tananing chap cheti X
        self.trunk_right = trunk_right  # tananing o'ng cheti X
        self.top_y = top_y              # jigarrang sohaning yuqori Y
        self.bottom_y = bottom_y        # jigarrang sohaning pastki Y

        trunk_w = max(8, trunk_right - trunk_left)
        self.trunk_w = trunk_w

        # "Xavfli zona" balandligi: shoxlar personaj boshi ustida paydo bo'ladi.
        # Tananing yuqori-o'rta qismida tekshiramiz (yangi shoxlar shu yerda
        # ko'rinadi). Bottom dan emas, balki span ning ~35% balandligida.
        span = bottom_y - top_y
        self.span = span
        self.check_y = int(top_y + span * 0.45)

        # Shox tekshirish ZONALARI: tana chetidan tashqarida, shox cho'ziladigan
        # gorizontal yo'lak. Tanadan biroz uzoqlashamiz (tana o'zi jigarrang
        # bo'lgani uchun unga tegmaslik kerak), lekin shox uzunligini qamrab
        # olamiz. Zona = (x1, x2) gorizontal oraliq.
        gap = max(4, int(trunk_w * 0.25))   # tanadan kichik bo'shliq
        reach = max(trunk_w * 3, 60)         # shox qancha uzoqqa cho'ziladi
        self.left_zone = (trunk_left - gap - reach, trunk_left - gap)
        self.right_zone = (trunk_right + gap, trunk_right + gap + reach)

        # Klik nuqtalari: pastdagi ikkita dumaloq tan-rangli tugma.
        # Bular detect_tree() da avtomatik aniqlanadi va shu yerga beriladi.
        # Agar berilmagan bo'lsa, taxminiy joy (tana markazidan chap/o'ng).
        click_y = int(bottom_y + span * 0.55)
        self.left_click = (trunk_cx - trunk_w * 2, click_y)
        self.right_click = (trunk_cx + trunk_w * 2, click_y)

        # Eski yagona-nuqta atributlari (debug rasmi uchun markaz nuqtalari).
        self.left_check = ((self.left_zone[0] + self.left_zone[1]) // 2, self.check_y)
        self.right_check = ((self.right_zone[0] + self.right_zone[1]) // 2, self.check_y)

    def __repr__(self):
        return (
            f"TreeLayout(cx={self.trunk_cx}, left={self.trunk_left}, "
            f"right={self.trunk_right}, top={self.top_y}, bottom={self.bottom_y}, "
            f"check_y={self.check_y})"
        )


def detect_tree():
    """Ekranni skanеrlab daraxt o'zagini avtomatik topadi.

    Strategiya:
      1. Butun ekrandan jigarrang maska olamiz.
      2. Har bir ustundagi jigarrang piksellar sonini hisoblaymiz.
      3. Eng ko'p jigarrang to'plangan ustunlar bandi = daraxt tanasi.
      4. Tananing chap/o'ng chetlari va vertikal chegaralarini aniqlaymiz.

    Topilmasa None qaytaradi.
    """
    screen = grab_screen_rgb()
    h, w = screen.shape[:2]
    mask = brown_mask(screen)

    # Har bir ustundagi jigarrang piksellar soni.
    col_counts = mask.sum(axis=0)

    if col_counts.max() == 0:
        return None  # jigarrang topilmadi

    # Tana — eng baland (ko'p jigarrangli) ustunlar atrofida. Eng zich ustunni
    # topamiz va undan chap/o'ngga "yetarlicha jigarrang" ustunlarni kengaytiramiz.
    peak_x = int(np.argmax(col_counts))
    threshold = max(10, col_counts[peak_x] * 0.35)

    left = peak_x
    while left > 0 and col_counts[left - 1] >= threshold:
        left -= 1
    right = peak_x
    while right < w - 1 and col_counts[right + 1] >= threshold:
        right += 1

    # Juda keng band tana emas (balki fon) — qo'pol filtr.
    trunk_width = right - left
    if trunk_width > w * 0.5 or trunk_width < 3:
        return None

    # Tana ustunidagi jigarrang piksellarning vertikal chegarasi.
    # MUHIM: shunchaki min..max emas, eng uzun UZLUKSIZ jigarrang bandni
    # olamiz — aks holda ekran tepasi/pastidagi boshqa jigarrang narsalar
    # (shovqin) tana balandligini noto'g'ri cho'zib yuboradi.
    band = mask[:, left:right + 1]
    row_has = band.any(axis=1)
    if not row_has.any():
        return None

    gap_allow = max(10, h // 60)  # kichik uzilishlarga yo'l qo'yamiz
    best_start, best_len = 0, 0
    cur_start, cur_len, gap = None, 0, 0
    for y in range(h):
        if row_has[y]:
            if cur_start is None:
                cur_start = y
            cur_len = y - cur_start + 1
            gap = 0
            if cur_len > best_len:
                best_len, best_start = cur_len, cur_start
        else:
            gap += 1
            if gap > gap_allow:
                cur_start, cur_len = None, 0

    top_y = int(best_start)
    bottom_y = int(best_start + best_len)

    trunk_cx = (left + right) // 2
    layout = TreeLayout(trunk_cx, left, right, top_y, bottom_y)

    # Pastdagi ikkita dumaloq tan-rangli tugmani avtomatik topamiz va klik
    # nuqtalarini ularning markaziga moslaymiz.
    buttons = detect_buttons(screen, trunk_cx)
    if buttons is not None:
        layout.left_click, layout.right_click = buttons

    return layout


# Dumaloq strelka tugmalarining och-jigarrang (tan) rangi.
BUTTON_RGB = (232, 184, 120)
BUTTON_TOL = 40


def detect_buttons(screen, trunk_cx):
    """Pastdagi ikkita dumaloq tan-rangli tugmaning markazini topadi.

    screen: butun ekran RGB massiv.
    trunk_cx: tana markazi X (chap/o'ngga ajratish uchun).
    Topilsa ((lx, ly), (rx, ry)) qaytaradi, aks holda None.
    """
    h, w = screen.shape[:2]
    img = screen.astype(np.int16)
    br, bg, bb = BUTTON_RGB
    mask = (
        (np.abs(img[:, :, 0] - br) <= BUTTON_TOL)
        & (np.abs(img[:, :, 1] - bg) <= BUTTON_TOL)
        & (np.abs(img[:, :, 2] - bb) <= BUTTON_TOL)
    )
    # Faqat ekranning pastki yarmida qidiramiz (tugmalar pastda).
    mask[: int(h * 0.55), :] = False

    if mask.sum() == 0:
        return None

    # Eng zich gorizontal band (tugmalar shu yerda to'plangan).
    row_counts = mask.sum(axis=1)
    win = max(30, h // 25)
    best_y, best = int(h * 0.55), 0
    for y in range(int(h * 0.55), h - win):
        s = int(row_counts[y:y + win].sum())
        if s > best:
            best, best_y = s, y
    band_top, band_bot = best_y, best_y + win

    sub = mask[band_top:band_bot, :]
    ys, xs = np.where(sub)
    if xs.size == 0:
        return None

    cy = band_top + win // 2
    left_xs = xs[xs < trunk_cx]
    right_xs = xs[xs >= trunk_cx]
    if left_xs.size == 0 or right_xs.size == 0:
        return None

    left_click = (int(np.median(left_xs)), int(cy))
    right_click = (int(np.median(right_xs)), int(cy))
    return left_click, right_click


def save_debug_image(layout, filename="debug_detect.png"):
    """Topilgan tana va tekshirish/klik nuqtalarini rasm ustiga chizib saqlaydi.

    Bu nuqtalar QAYERGA tushayotganini ko'rish uchun. Yashil = tana chegarasi,
    qizil = shox tekshirish nuqtalari, ko'k = klik nuqtalari.
    """
    image = ImageGrab.grab().convert("RGB")
    draw = ImageDraw.Draw(image)

    # Tana chegarasi (yashil to'rtburchak).
    draw.rectangle(
        [layout.trunk_left, layout.top_y, layout.trunk_right, layout.bottom_y],
        outline=(0, 255, 0), width=3,
    )

    # Shox tekshirish ZONALARI (qizil to'rtburchaklar).
    band = max(6, layout.span // 12)
    lz = layout.left_zone
    rz = layout.right_zone
    draw.rectangle(
        [lz[0], layout.check_y - band, lz[1], layout.check_y + band],
        outline=(255, 0, 0), width=3,
    )
    draw.rectangle(
        [rz[0], layout.check_y - band, rz[1], layout.check_y + band],
        outline=(255, 0, 0), width=3,
    )

    def marker(point, color):
        x, y = point
        r = 8
        draw.ellipse([x - r, y - r, x + r, y + r], outline=color, width=3)

    # Klik nuqtalari (ko'k).
    marker(layout.left_click, (0, 100, 255))
    marker(layout.right_click, (0, 100, 255))

    image.save(filename)
    print(f"Diagnostika rasmi saqlandi: {filename}")


# ==============================================================================
# SHOX ANIQLASH (real vaqt)
# ==============================================================================

def detect_threat_side(layout):
    """Eng pastdagi (personajga eng yaqin) shox qaysi tomonda ekanini aniqlaydi.

    Tana balandligi bo'ylab pastdan yuqoriga skanеrlaydi. Birinchi (eng past)
    shox topilgan darajada qaysi tomon jigarrang ko'proq bo'lsa, o'sha tomon
    XAVFLI deb qaytariladi:
      'left'  -> chapda shox (o'ngga o'tish kerak)
      'right' -> o'ngda shox (chapga o'tish kerak)
      None    -> shox yo'q (joriy tomonda kesishda davom etish)
    """
    top_y = layout.top_y
    bottom_y = layout.bottom_y
    lx1, lx2 = layout.left_zone
    rx1, rx2 = layout.right_zone
    if lx1 < 0:
        lx1 = 0

    # TEZLIK: butun chap+o'ng zonani BITTA rasmga olamiz (ImageGrab sekin,
    # 20 ta alohida grab o'rniga 1 ta), so'ng numpy bilan darajalarni tahlil.
    x_min = min(lx1, rx1)
    x_max = max(lx2, rx2)
    try:
        full = grab_screen_rgb(bbox=(x_min, top_y, x_max, bottom_y))
    except Exception:
        return None

    mask = brown_mask(full)
    fh = bottom_y - top_y
    l_a, l_b = lx1 - x_min, lx2 - x_min
    r_a, r_b = rx1 - x_min, rx2 - x_min

    levels = 10
    band = max(4, fh // (levels * 2))
    for k in range(levels - 1, -1, -1):  # pastdan yuqoriga
        cy = int(fh * (k + 0.5) / levels)
        ya, yb = max(0, cy - band), min(fh, cy + band)
        left_region = mask[ya:yb, l_a:l_b]
        right_region = mask[ya:yb, r_a:r_b]
        lf = float(left_region.mean()) if left_region.size else 0.0
        rf = float(right_region.mean()) if right_region.size else 0.0
        if lf >= BRANCH_FRACTION or rf >= BRANCH_FRACTION:
            return "left" if lf >= rf else "right"
    return None


def detect_branch_sequence(layout):
    """Tanani BIR MARTA o'qib, pastdan yuqoriga har segmentdagi shox tomonini
    ro'yxat sifatida qaytaradi.

    Qaytariladi: ["right", None, "left", ...] — pastdan (personajga yaqin)
    yuqoriga. Har element o'sha segmentda QAYSI tomonda shox borligini bildiradi
    ('left'/'right'), shox bo'lmasa None. Bu ro'yxat orqali bir nechta klikni
    qayta ekran o'qimasdan rejalashtirish mumkin (tezlik uchun).
    """
    top_y = layout.top_y
    bottom_y = layout.bottom_y
    lx1, lx2 = layout.left_zone
    rx1, rx2 = layout.right_zone
    if lx1 < 0:
        lx1 = 0

    x_min = min(lx1, rx1)
    x_max = max(lx2, rx2)
    try:
        full = grab_screen_rgb(bbox=(x_min, top_y, x_max, bottom_y))
    except Exception:
        return []

    mask = brown_mask(full)
    fh = bottom_y - top_y
    l_a, l_b = lx1 - x_min, lx2 - x_min
    r_a, r_b = rx1 - x_min, rx2 - x_min

    levels = 10
    band = max(4, fh // (levels * 2))
    seq = []
    for k in range(levels - 1, -1, -1):  # pastdan yuqoriga
        cy = int(fh * (k + 0.5) / levels)
        ya, yb = max(0, cy - band), min(fh, cy + band)
        lf = float(mask[ya:yb, l_a:l_b].mean()) if mask[ya:yb, l_a:l_b].size else 0.0
        rf = float(mask[ya:yb, r_a:r_b].mean()) if mask[ya:yb, r_a:r_b].size else 0.0
        if lf >= BRANCH_FRACTION and lf >= rf:
            seq.append("left")
        elif rf >= BRANCH_FRACTION:
            seq.append("right")
        else:
            seq.append(None)
    return seq

# Klikdan keyin ekran (daraxt surilishi animatsiyasi) joylashishi uchun
# kutiladigan vaqt (soniyada). Bu aniq rejimda asosiy tezlik sozlamasi.
# Kichraytiring = tezroq, lekin juda kichik bo'lsa animatsiya tugamasdan o'qib
# xato qiladi. 0.03 dan boshlab sinab ko'ring; xato qilsa 0.05–0.06 ga oshiring.
SETTLE_S = 0.10

# BURST rejimi: True bo'lsa, bot tanani bir marta o'qib, ko'rinib turgan bir
# nechta shoxni qayta o'qimasdan ketma-ket bosadi (tezroq). Xato qilsa False
# qiling (har klikda qayta o'qiydi — sekinroq, lekin ishonchliroq).
# ANIQ ishlashi uchun False (har klikda qayta o'qiydi).
BURST_MODE = False
# Burst ichida nechta klikni qayta o'qimasdan yuborish (eng past segmentlar).
# Kichikroq = ishonchliroq (bashorat xatosi kamroq to'planadi), kattaroq = tezroq.
BURST_SIZE = 2
# Burst ichidagi kliklar orasidagi kichik pauza (animatsiya uchun).
BURST_GAP_S = 0.05


# ==============================================================================
# ASOSIY BOT MANTIG'I
# ==============================================================================

def human_delay():
    """(Eski) — endi play() ichida to'g'ridan-to'g'ri sleep ishlatiladi."""
    time.sleep(random.uniform(MIN_DELAY_S, MAX_DELAY_S))


def fast_click(x, y):
    """Tez sichqoncha bosishi (pyautogui.click dan kamroq qo'shimcha yuk).

    Sichqonchani joyiga qo'yib, mouseDown+mouseUp bajaradi. pyautogui.click
    ichida qo'shimcha tekshiruvlar bor; bu yo'l biroz tezroq.
    """
    pyautogui.moveTo(x, y)
    pyautogui.mouseDown()
    pyautogui.mouseUp()


def play(layout):
    """Aniqlangan daraxt joylashuvi bo'yicha o'yinni avtomatik o'ynaydi.

    'Q' bosilmaguncha yoki TARGET_SCORE ga yetmaguncha davom etadi.

    Ikki rejim:
      - BURST_MODE: tanani bir marta o'qib, ko'rinib turgan bir nechta shoxni
        ketma-ket bosadi (tezroq).
      - Oddiy: har klikda qayta o'qiydi (sekinroq, ishonchliroq).
    """
    score = 0
    current_side = "left"  # joriy xavfsiz tomon
    lx, ly = layout.left_click
    rx, ry = layout.right_click

    def do_click(side):
        if side == "left":
            fast_click(lx, ly)
        else:
            fast_click(rx, ry)

    print(f"O'yin boshlandi! Maqsad: {TARGET_SCORE} ball. To'xtatish: 'Q'.")

    while score < TARGET_SCORE:
        if keyboard.is_pressed("q"):
            print("\n'Q' bosildi — to'xtatildi.")
            return score

        if BURST_MODE:
            # Tanani BIR MARTA o'qib, pastdan yuqoriga shoxlar ketma-ketligini
            # olamiz va bir nechta klikni qayta o'qimasdan yuboramiz.
            seq = detect_branch_sequence(layout)  # ["right", None, "left", ...]
            clicks = 0
            for branch in seq:
                if branch == "left":
                    current_side = "right"   # chapda shox -> o'ngga
                elif branch == "right":
                    current_side = "left"    # o'ngda shox -> chapga
                # branch None -> joriy tomonda davom

                do_click(current_side)
                score += 1
                clicks += 1
                if score >= TARGET_SCORE:
                    break
                time.sleep(BURST_GAP_S)
                if clicks >= BURST_SIZE:
                    break

            if score % 10 < BURST_SIZE or score >= TARGET_SCORE:
                print(f"\rBall: {score}", end="", flush=True)

            # Burstdan keyin ekran joylashishini kutamiz, so'ng qayta o'qiymiz.
            time.sleep(SETTLE_S)
        else:
            # Oddiy rejim: har klikda qayta o'qiydi.
            threat = detect_threat_side(layout)
            if threat == "left":
                current_side = "right"
            elif threat == "right":
                current_side = "left"
            do_click(current_side)
            score += 1
            if score % 10 == 0 or score == TARGET_SCORE:
                print(f"\rBall: {score}", end="", flush=True)
            time.sleep(SETTLE_S)
            if MAX_DELAY_S > 0:
                time.sleep(random.uniform(MIN_DELAY_S, MAX_DELAY_S))

    print(f"\nMaqsadli ball ({TARGET_SCORE}) ga yetildi! To'xtatildi.")
    return score


def main():
    print("=" * 60)
    print("  LUMBERJACK AVTOMATIK BOT")
    print("=" * 60)
    print("1. Telegram'da 'Lumberjack' o'yinini oching (oyna to'liq ko'rinsin).")
    print("2. Boshlash uchun 'S' tugmasini bosing.")
    print("3. Istalgan vaqtda to'xtatish uchun 'Q' bosing.")
    print("-" * 60)

    # 'S' yoki 'Q' kutamiz.
    print("'S' kutilmoqda...")
    while True:
        if keyboard.is_pressed("s"):
            break
        if keyboard.is_pressed("q"):
            print("To'xtatildi.")
            return 0
        time.sleep(0.05)

    # 'S' qo'yib yuborilishini kutamiz (takroriy ishga tushmasligi uchun).
    while keyboard.is_pressed("s"):
        time.sleep(0.05)

    print("\nEkran skanерlanmoqda, daraxt qidirilmoqda...")
    layout = detect_tree()

    if layout is None:
        print(
            "XATO: daraxt topilmadi. Ehtimollar:\n"
            "  - O'yin oynasi ekranda ko'rinmayapti.\n"
            "  - Shox rangi BRANCH_RGB ga mos emas — sample_colors.py bilan\n"
            "    tananing rangini aniqlab, yuqoridagi BRANCH_RGB ni yangilang.\n"
            "  - TOLERANCE ni oshirib ko'ring."
        )
        return 1

    print(f"Daraxt topildi: {layout}")
    print(
        f"  Chap tekshiruv: {layout.left_check}   "
        f"O'ng tekshiruv: {layout.right_check}"
    )
    print(
        f"  Chap klik: {layout.left_click}   "
        f"O'ng klik: {layout.right_click}"
    )
    # Topilgan natijani rasmga chizib saqlaymiz — nuqtalar qayerga
    # tushayotganini ko'rish uchun (debug_detect.png faylini oching).
    try:
        save_debug_image(layout)
    except Exception as exc:
        print(f"Diagnostika rasmini saqlab bo'lmadi: {exc}")
    # Topilgan natijani ko'rish uchun qisqa pauza.
    time.sleep(1.0)

    # DIAGNOSTIKA rejimi: kliklamasdan zonalarni kuzatamiz.
    if DIAGNOSE_MODE:
        print("\nDiagnostika rejimi yoqilgan, lekin o'chirilgan funksiya. "
              "DIAGNOSE_MODE = False qiling.")
        return 0

    score = play(layout)
    print(f"Yakuniy ball: {score}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except pyautogui.FailSafeException:
        print("\nFailsafe ishga tushdi (sichqoncha burchakka olib borildi). To'xtatildi.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCtrl+C — to'xtatildi.")
        sys.exit(1)
