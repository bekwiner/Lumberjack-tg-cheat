"""sample_colors.py — piksel rangini aniqlash vositasi (diagnostika).

Maqsad: bot kalibrlangan nuqtalarda QAYSI rangni o'qiyotganini bilish.
Shu orqali `lumberjack_bot_main.py` dagi BRANCH_COLOR va TOLERANCE
qiymatlarini to'g'ri sozlash mumkin.

ISHLATISH:
  1. Telegram'da "Lumberjack" o'yinini oching.
  2. Bu skriptni ishga tushiring:  python sample_colors.py
  3. Sichqonchani SHOX (jigarrang/yashil novda) ustiga olib boring va
     terminalda chiqayotgan RGB qiymatini yozib oling.
  4. So'ng sichqonchani SHOX YO'Q joyga (bo'sh tana yoki fon) olib boring
     va o'sha yerdagi RGB ni ham yozib oling.
  5. To'xtatish uchun Ctrl+C bosing.

Terminal har ~0.3 soniyada joriy sichqoncha koordinatasi va o'sha
pikseldagi RGB rangini ko'rsatib turadi.
"""

import time

from lumberjack_bot.screen_capture import ScreenCaptureModule


def main() -> None:
    import pyautogui

    capture = ScreenCaptureModule()
    print("=== Piksel rangini aniqlash vositasi ===")
    print("Sichqonchani kerakli joyga olib boring; RGB qiymati ko'rsatiladi.")
    print("To'xtatish uchun Ctrl+C bosing.\n")

    try:
        while True:
            x, y = pyautogui.position()
            try:
                color = capture.read_pixel(int(x), int(y))
                print(
                    f"\rX={int(x):>5}  Y={int(y):>5}   "
                    f"RGB=({color.r:>3}, {color.g:>3}, {color.b:>3})        ",
                    end="",
                    flush=True,
                )
            except Exception as exc:
                print(f"\rX={int(x)} Y={int(y)}  o'qish xatosi: {exc}",
                      end="", flush=True)
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")


if __name__ == "__main__":
    main()
