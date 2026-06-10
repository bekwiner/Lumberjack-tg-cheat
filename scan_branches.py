"""scan_branches.py — o'yin paytida shoxlar QAYERDA ekanini skanerlaydi.

Daraxt tanasini topadi, so'ng tananing chap va o'ng tomonida HAR XIL
balandliklarda jigarrang (shox) bor-yo'qligini tekshiradi va eng yaqin
shox qaysi balandlik/tomonda ekanini ko'rsatadi.

ISHLATISH:
  1. O'yinni oching (shoxlar ko'rinib tursin).
  2. python scan_branches.py
  3. 'S' bosing — skanеr boshlanadi. 'Q' to'xtatadi.
"""
import time
import numpy as np
from PIL import ImageGrab
import keyboard

BRANCH_RGB = (161, 116, 56)
TOL = 45


def grab():
    arr = np.asarray(ImageGrab.grab())
    return arr[:, :, :3]


def brown_mask(img):
    r, g, b = BRANCH_RGB
    i = img.astype(np.int16)
    return ((np.abs(i[:, :, 0] - r) <= TOL)
            & (np.abs(i[:, :, 1] - g) <= TOL)
            & (np.abs(i[:, :, 2] - b) <= TOL))


def detect_trunk(mask):
    h, w = mask.shape
    col = mask.sum(axis=0)
    if col.max() == 0:
        return None
    peak = int(np.argmax(col))
    thr = max(10, col[peak] * 0.35)
    left = peak
    while left > 0 and col[left - 1] >= thr:
        left -= 1
    right = peak
    while right < w - 1 and col[right + 1] >= thr:
        right += 1
    band = mask[:, left:right + 1]
    rh = band.any(axis=1)
    gap_allow = max(10, h // 60)
    bs, bl, cs, cl, gap = 0, 0, None, 0, 0
    for y in range(h):
        if rh[y]:
            if cs is None:
                cs = y
            cl = y - cs + 1
            gap = 0
            if cl > bl:
                bl, bs = cl, cs
        else:
            gap += 1
            if gap > gap_allow:
                cs, cl = None, 0
    return left, right, bs, bs + bl


def main():
    print("Skanеr 3 soniyadan keyin boshlanadi — o'yin oynasini ochib qo'ying!")
    print("(To'xtatish uchun 'Q' bosing. Natijalar scan_log.txt ga yoziladi.)")
    for i in (3, 2, 1):
        print(f"  {i}...")
        time.sleep(1)

    print("Skanеr ishlamoqda... (natijalar scan_log.txt fayliga yoziladi)\n")
    log = open("scan_log.txt", "w", encoding="utf-8")
    log.write("=== Shox skaneri jurnali ===\n")

    def out(line):
        """Bir vaqtda terminalga ham, log faylga ham yozadi."""
        print(line)
        log.write(line + "\n")
        log.flush()

    try:
        end_time = time.time() + 12.0  # 12 soniya skanерlab, avtomatik to'xtaydi
        while time.time() < end_time:
            if keyboard.is_pressed("q"):
                break
            screen = grab()
            mask = brown_mask(screen)
            trunk = detect_trunk(mask)
            if trunk is None:
                out("Tana topilmadi...")
                time.sleep(0.3)
                continue
            left, right, top_y, bottom_y = trunk
            tw = max(8, right - left)
            gap = max(4, int(tw * 0.25))
            reach = max(tw * 3, 60)

            # Tana balandligini 6 ta darajaga bo'lamiz va har birida chap/o'ng
            # zonada jigarrang ulushini o'lchaymiz.
            levels = 6
            stamp = time.strftime("%H:%M:%S")
            out(f"\n[{stamp}] Tana X:{left}..{right} Y:{top_y}..{bottom_y} (kenglik {tw})")
            for k in range(levels):
                y = int(top_y + (bottom_y - top_y) * (k + 0.5) / levels)
                band = max(4, (bottom_y - top_y) // (levels * 2))
                ya, yb = y - band, y + band
                lz = mask[ya:yb, max(0, left - gap - reach):max(1, left - gap)]
                rz = mask[ya:yb, right + gap:right + gap + reach]
                lf = lz.mean() if lz.size else 0
                rf = rz.mean() if rz.size else 0
                lflag = "SHOX" if lf > 0.10 else "    "
                rflag = "SHOX" if rf > 0.10 else "    "
                out(f"  Y={y:>4} | CHAP={lf:.2f} {lflag}  O'NG={rf:.2f} {rflag}")
            time.sleep(0.6)
    finally:
        log.close()
        print("\nJurnal saqlandi: scan_log.txt")


if __name__ == "__main__":
    main()
