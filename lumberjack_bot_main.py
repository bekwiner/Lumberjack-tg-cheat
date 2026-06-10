"""lumberjack_bot_main.py — Telegram "Lumberjack" o'yini uchun yagona ishga
tushiriladigan bot skripti.

================================================================================
UMUMIY TAVSIF
================================================================================
Ushbu skript barcha komponentlarni (sof mantiq + I/O qatlami + orkestratsiya)
yagona kirish nuqtasiga (`main()` / `if __name__ == "__main__"`) jamlaydi.
Brauzer xavfsizlik cheklovlari (CORS/iframe) sababli bot brauzer kodiga
tegmaydi; uning o'rniga ekran piksellarini o'qiydi, daraxt tanasining chap va
o'ng nuqtalaridagi ranglarni tahlil qilib shoxlarni aniqlaydi, qahramonni
xavfsiz tomonga o'tkazish uchun sichqoncha bosishini simulyatsiya qiladi,
kesishlarni sanaydi va `TARGET_SCORE` ga yetganda avtomatik to'xtaydi
(Requirement 7.1).

Komponentlar `lumberjack_bot/` paketidan import qilinadi va shu yerda bog'lanadi.
Quyida har bir asosiy komponentning vazifasi izohlangan (Requirement 7.1):

  - ScreenCaptureModule : ekran piksellarini o'qiydi (PIL.ImageGrab yoki OpenCV).
  - BranchDetector      : chap/o'ng ranglarni shox rangiga solishtirib qaror
                          chiqaradi (sof mantiq).
  - ClickSimulator      : sichqoncha bosishini simulyatsiya qiladi (pyautogui).
  - ScoreCounter        : muvaffaqiyatli kesishlarni sanaydi (sof mantiq).
  - CalibrationModule   : Canvas koordinatalarini interaktiv sozlaydi.
  - KeyboardListener    : 'S'/'Q' boshqaruv tugmalarini kuzatadi (keyboard).
  - GameStateMachine    : IDLE/RUNNING/STOPPED holatlarini boshqaradi (sof mantiq).
  - DelayGenerator      : kesishlar orasiga tasodifiy kechikish hosil qiladi.
  - DependencyChecker   : kerakli kutubxonalar mavjudligini tekshiradi.
  - BotController       : barcha komponentlarni o'yin tsikliga bog'laydi.

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
================================================================================

ISHGA TUSHIRISH YO'RIQNOMASI: batafsil raqamlangan o'rnatish/ishga tushirish va
kalibrlash bosqichlari keyingi vazifada (13.2) hujjatlashtiriladi. Bu yerda
faqat kod va satr ichidagi izohlar joylashtirilgan.
"""

# Komponentlarni `lumberjack_bot` paketidan import qilamiz va shu skriptda
# bog'laymiz. Paket nomi (lumberjack_bot) va bu skript nomi (lumberjack_bot_main)
# ataylab farqli — bir xil bo'lsa import to'qnashuvi yuzaga kelardi.
from lumberjack_bot.models import BotConfig, CanvasCoords, Point, RGBColor, Side
from lumberjack_bot.screen_capture import ScreenCaptureModule
from lumberjack_bot.branch_detector import BranchDetector
from lumberjack_bot.click_simulator import ClickSimulator
from lumberjack_bot.score_counter import ScoreCounter
from lumberjack_bot.state_machine import GameStateMachine
from lumberjack_bot.keyboard_listener import KeyboardListener
from lumberjack_bot.calibration import CalibrationModule
from lumberjack_bot.delay_generator import DelayGenerator
from lumberjack_bot.bot_controller import BotController
from lumberjack_bot.dependency_checker import (
    check_dependencies,
    report_missing_dependencies,
)

# ==============================================================================
# FOYDALANUVCHI SOZLAY OLADIGAN O'ZGARUVCHILAR (Requirement 7.2)
# ------------------------------------------------------------------------------
# Quyidagi qiymatlarni o'z ekraningiz, o'yin oynasi joylashuvi va xohlagan
# tezligingizga moslab o'zgartiring. Boshqa joyni tahrir qilish shart emas.
# ==============================================================================

# Maqsadli ball: bot shu songa yetganda avtomatik to'xtaydi.
# Butun son bo'lishi va 1 dan 1 000 000 gacha bo'lishi kerak (Requirement 3.1).
TARGET_SCORE = 269

# Rang chegarasi (tolerance): o'qilgan rang shox rangiga qanchalik yaqin
# bo'lganda "shox" deb hisoblanishini belgilaydi. 0..255 oralig'ida; kichik
# qiymat qattiqroq moslik, katta qiymat erkinroq moslik beradi (Requirement 2.4).
TOLERANCE = 30

# Shoxning kutilayotgan RGB rangi. Standart — jigarrang (brown) shox.
# O'yiningiz shoxlari boshqa rangda bo'lsa (masalan barg-yashil), shu qiymatni
# kalibrlangan piksel rangiga moslang.
BRANCH_COLOR = RGBColor(r=161, g=116, b=56)

# Ketma-ket kesishlar orasidagi tasodifiy kechikish chegaralari (millisekundda).
# Inson tezligiga o'xshatish va tezkor signallar rad etilishining oldini olish
# uchun ishlatiladi. Har biri 10..5000 ms oralig'ida va MIN <= MAX bo'lishi
# kerak (Requirement 5.2, 5.3).
MIN_DELAY_MS = 100
MAX_DELAY_MS = 400

# Qahramon (Hero) boshlang'ich tomoni: o'yin boshlanishida qahramon daraxt
# tanasining qaysi tomonida turishini bildiradi (Side.LEFT yoki Side.RIGHT).
INITIAL_HERO_SIDE = Side.LEFT

# Daraxt tanasini tekshirish koordinatalari (ekran piksellarida).
#   - LEFT_POINT  : chap shoxni tekshirish nuqtasi
#   - RIGHT_POINT : o'ng shoxni tekshirish nuqtasi
#   - TOP_POINT   : yuqori nuqta (canvas chegarasi mo'ljali)
# Agar bu qiymatlarni oldindan aniq bilsangiz, ularni shu yerda kiriting va
# `USE_PRESET_COORDS = True` qiling — shunda kalibrlash o'tkazib yuboriladi.
# Aks holda `USE_PRESET_COORDS = False` qoldiring va skript ishga tushganda
# interaktiv kalibrlash rejimi orqali nuqtalarni sozlang.
USE_PRESET_COORDS = False
LEFT_POINT = Point(x=800, y=500)
RIGHT_POINT = Point(x=1120, y=500)
TOP_POINT = Point(x=960, y=200)

# ==============================================================================
# SOZLAMALAR TUGADI — quyida komponentlarni bog'lash mantig'i.
# ==============================================================================


def build_config() -> BotConfig:
    """Yuqoridagi foydalanuvchi o'zgaruvchilaridan `BotConfig` quradi.

    Validatsiya (qiymatlar yaroqliligini tekshirish) `BotController.run()`
    ichida fail-fast tarzda bajariladi (Requirement 3.2, 5.3, 2.4).
    """
    return BotConfig(
        target_score=TARGET_SCORE,
        tolerance=TOLERANCE,
        min_delay_ms=MIN_DELAY_MS,
        max_delay_ms=MAX_DELAY_MS,
        branch_color=BRANCH_COLOR,
    )


def build_controller(config: BotConfig) -> BotController:
    """Barcha komponentlarni yaratib, ularni `BotController` ga bog'laydi.

    Har bir komponent dependency injection orqali kiritiladi, shuning uchun
    `BotController` apparat I/O ni o'zi bajarmaydi — u faqat komponentlarni
    muvofiqlashtiradi.
    """
    # --- Sof mantiqiy komponentlar (apparatdan mustaqil) ---------------------
    # Shox aniqlash: rang tahliliga asoslangan qaror chiqaruvchi.
    branch_detector = BranchDetector(
        branch_color=config.branch_color,
        tolerance=config.tolerance,
    )
    # Ball sanagich: muvaffaqiyatli kesishlarni hisoblaydi.
    score_counter = ScoreCounter(target_score=config.target_score)
    # Holat mashinasi: IDLE/RUNNING/STOPPED o'tishlarini boshqaradi.
    state_machine = GameStateMachine()
    # Kechikish generatori: kesishlar orasiga tasodifiy pauza beradi.
    delay_generator = DelayGenerator(
        min_ms=config.min_delay_ms,
        max_ms=config.max_delay_ms,
    )

    # --- I/O qatlami komponentlari (apparatga bog'liq) -----------------------
    # Ekran suratga olish: piksel ranglarini o'qiydi.
    screen_capture = ScreenCaptureModule()
    # Sichqoncha bosish simulyatori; kechikishni delay_generator boshqaradi.
    click_simulator = ClickSimulator(delay_generator=delay_generator)
    # Klaviatura kuzatuvchisi: 'S'/'Q' tugmalarini kuzatadi.
    keyboard_listener = KeyboardListener()

    # --- Kalibrlash moduli ---------------------------------------------------
    # Ekran o'lchamini aniqlaymiz; iloji bo'lsa pyautogui'dan olamiz, aks holda
    # xavfsiz standart qiymatga qaytamiz. Bu CalibrationModule ning koordinata
    # validatsiyasi (Requirement 4.5) uchun chegara sifatida ishlatiladi.
    screen_size = _detect_screen_size()
    calibration = CalibrationModule(screen=screen_size)

    # Oldindan belgilangan koordinatalar bo'lsa, kalibrlashni o'tkazib yuboramiz
    # (USE_PRESET_COORDS = True). Aks holda BotController kalibrlash rejimini
    # ishga tushiradi (coords=None).
    coords = None
    if USE_PRESET_COORDS:
        coords = CanvasCoords(left=LEFT_POINT, right=RIGHT_POINT, top=TOP_POINT)

    # --- Orkestrator ---------------------------------------------------------
    return BotController(
        config=config,
        screen_capture=screen_capture,
        branch_detector=branch_detector,
        click_simulator=click_simulator,
        score_counter=score_counter,
        state_machine=state_machine,
        keyboard_listener=keyboard_listener,
        calibration=calibration,
        delay_generator=delay_generator,
        coords=coords,
        initial_hero_side=INITIAL_HERO_SIDE,
    )


def _detect_screen_size():
    """Ekran o'lchamini aniqlaydi (kalibrlash chegaralari uchun).

    `pyautogui` mavjud bo'lsa undan haqiqiy ekran o'lchamini olamiz; aks holda
    keng tarqalgan standart o'lchamga (1920x1080) qaytamiz. Import dangasa —
    bu funksiya faqat `main()` ichidan, bog'liqlik tekshiruvidan keyin
    chaqiriladi.
    """
    from lumberjack_bot.models import ScreenSize

    try:
        import pyautogui

        width, height = pyautogui.size()
        return ScreenSize(width=int(width), height=int(height))
    except Exception:
        # pyautogui mavjud emas yoki o'lchamni olib bo'lmadi -> standart.
        return ScreenSize(width=1920, height=1080)


def main() -> int:
    """Botning asosiy kirish nuqtasi.

    Oqim:
        1) Bog'liqlik tekshiruvi (fail-fast) — kerakli kutubxonalar yo'q bo'lsa
           hech qanday I/O amalisiz to'xtaymiz (Requirement 1.4–1.6).
        2) Foydalanuvchi o'zgaruvchilaridan BotConfig quramiz.
        3) Barcha komponentlarni yaratib BotController ga bog'laymiz.
        4) controller.run() — validatsiya, kalibrlash va o'yin tsiklini bajaradi.

    Qaytaradi: jarayon chiqish kodi (0 — muvaffaqiyat, 1 — xatolik/to'xtatish).
    """
    # 1) Bog'liqliklarni eng avval tekshiramiz (fail-fast). Yetishmasa
    #    foydalanuvchiga nom va o'rnatish buyrug'i ko'rsatiladi va to'xtaymiz.
    missing = check_dependencies()
    if not report_missing_dependencies(missing):
        return 1

    # 2) Foydalanuvchi sozlamalaridan konfiguratsiya quramiz.
    config = build_config()

    # 3) Komponentlarni yaratib bog'laymiz.
    controller = build_controller(config)

    # 4) To'liq oqimni ishga tushiramiz. run() ichki validatsiyani ham
    #    bajaradi, shuning uchun yaroqsiz sozlamada xavfsiz to'xtaydi.
    success = controller.run()
    return 0 if success else 1


# Skript to'g'ridan-to'g'ri ishga tushirilgandagina main() chaqiriladi.
# `import lumberjack_bot_main` qilinganda hech qanday bot harakati boshlanmaydi —
# barcha I/O main() ichida himoyalangan.
if __name__ == "__main__":
    import sys

    sys.exit(main())
