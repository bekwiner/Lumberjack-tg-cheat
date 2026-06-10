"""BotController — orkestratsiya va asosiy o'yin tsikli.

Ushbu modul barcha komponentlarni yagona o'yin oqimiga bog'laydigan
`BotController` sinfini belgilaydi. U boshqaruv/orkestratsiya qatlamiga
tegishli (dizayn hujjatining "BotController" bo'limi).

Umumiy oqim (Architecture flowchart):
    DependencyChecker -> ConfigValidator -> CalibrationModule -> GameStateMachine

Asosiy o'yin tsikli (sense-decide-act):
    piksel o'qish (ScreenCaptureModule.read_branch_points)
      -> BranchDetector.decide
      -> bosish (ClickSimulator)
      -> ScoreCounter.increment
      -> terminalga chop (Requirement 3.4)
      -> kechikish
      -> to'xtash shartini tekshirish (Requirement 3.5)

Xato/xavf boshqaruvi:
    - DANGER_STOP (ikki tomonda ham shox, Requirement 2.5) va
      PixelReadError (Requirement 2.6) holatlarida kesish XAVFSIZ
      to'xtatiladi: holat STOPPED ga o'tadi va `KeyboardListener.stop()`
      chaqiriladi (Requirement 6.5).

Arxitektura eslatmasi: barcha komponentlar konstruktor orqali (dependency
injection) kiritiladi, shuning uchun ular testlarda (12.2/12.3) osongina
mock qilinishi mumkin. `BotController` apparat I/O ni to'g'ridan-to'g'ri
bajarmaydi — u faqat injektsiya qilingan komponentlarni muvofiqlashtiradi.

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

import time
from typing import Callable, List, Optional

from .branch_detector import BranchDetector
from .calibration import CalibrationModule
from .click_simulator import ClickSimulator
from .config_validator import (
    validate_delay,
    validate_target_score,
    validate_tolerance,
)
from .delay_generator import DelayGenerator
from .dependency_checker import (
    MissingDependency,
    check_dependencies,
    report_missing_dependencies,
)
from .keyboard_listener import KeyboardListener
from .models import (
    BotConfig,
    CanvasCoords,
    Decision,
    ControlKey,
    PixelReadError,
    Side,
    State,
)
from .score_counter import ScoreCounter
from .screen_capture import ScreenCaptureModule
from .state_machine import GameStateMachine


def _opposite_side(side: Side) -> Side:
    """Berilgan tomonning qarama-qarshisini qaytaradi (LEFT <-> RIGHT)."""
    return Side.RIGHT if side is Side.LEFT else Side.LEFT


class BotController:
    """Komponentlarni bog'lab, o'yin tsiklini boshqaruvchi orkestrator.

    Barcha bog'liqliklar konstruktor orqali kiritiladi (dependency
    injection), shuning uchun har bir komponent testlarda mock qilinishi
    mumkin. `BotController` o'zi apparat I/O bajarmaydi.
    """

    def __init__(
        self,
        config: BotConfig,
        screen_capture: ScreenCaptureModule,
        branch_detector: BranchDetector,
        click_simulator: ClickSimulator,
        score_counter: ScoreCounter,
        state_machine: GameStateMachine,
        keyboard_listener: KeyboardListener,
        calibration: CalibrationModule,
        delay_generator: DelayGenerator,
        coords: Optional[CanvasCoords] = None,
        initial_hero_side: Side = Side.LEFT,
        # Quyidagilar test/maxsus muhit uchun almashtirilishi mumkin.
        dependency_check: Callable[[], List[MissingDependency]] = check_dependencies,
        dependency_report: Callable[[List[MissingDependency]], bool] = report_missing_dependencies,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        # Foydalanuvchi sozlamalari (target_score, tolerance, kechikish, rang).
        self.config = config
        # I/O qatlami komponentlari.
        self.screen_capture = screen_capture
        self.click_simulator = click_simulator
        self.keyboard_listener = keyboard_listener
        # Sof mantiqiy komponentlar.
        self.branch_detector = branch_detector
        self.score_counter = score_counter
        self.state_machine = state_machine
        self.delay_generator = delay_generator
        # Kalibrlash moduli (koordinatalarni sozlash/o'qish).
        self.calibration = calibration
        # Kalibrlangan koordinatalar; berilmasa run() ichida sozlanadi.
        self.coords = coords
        # Qahramon (Hero) joriy tomoni; MOVE_TO_SAFE da almashtiriladi.
        self.hero_side = initial_hero_side
        # Bog'liqlik tekshiruvi va hisobot funksiyalari (injektsiya qilinadi).
        self._dependency_check = dependency_check
        self._dependency_report = dependency_report
        # Kechikish uchun uxlash funksiyasi (test'da mock qilinadi).
        self._sleeper = sleeper

    # ------------------------------------------------------------------
    # Ishga tushishdan oldingi bosqichlar (fail-fast)
    # ------------------------------------------------------------------

    def check_environment(self) -> bool:
        """Kerakli kutubxonalar mavjudligini tekshiradi (Requirement 1.4–1.6).

        Yetishmayotgan kutubxonalar bo'lsa, ularning nomi va o'rnatish
        buyrug'i terminalga chop etiladi va hech qanday I/O amalisiz `False`
        qaytariladi (fail-fast). Hammasi mavjud bo'lsa `True`.
        """
        missing = self._dependency_check()
        # Hisobot funksiyasi yetishmayotganlar bo'lsa False qaytaradi
        # (Requirement 1.5, 1.6).
        return self._dependency_report(missing)

    def validate_config(self) -> bool:
        """Konfiguratsiyani validatsiya qiladi (target_score, tolerance, kechikish).

        Yaroqsiz qiymatda sabab terminalga chop etiladi va kesish
        boshlanmaydi (Requirement 3.2, 5.3, 2.4). Hammasi yaroqli bo'lsa
        `True` qaytadi.
        """
        # target_score (Requirement 3.1, 3.2)
        result = validate_target_score(self.config.target_score)
        if not result.ok:
            print(f"Konfiguratsiya xatosi: {result.reason}")
            return False

        # tolerance (Requirement 2.4)
        result = validate_tolerance(self.config.tolerance)
        if not result.ok:
            print(f"Konfiguratsiya xatosi: {result.reason}")
            return False

        # kechikish oralig'i (Requirement 5.2, 5.3)
        result = validate_delay(self.config.min_delay_ms, self.config.max_delay_ms)
        if not result.ok:
            print(f"Konfiguratsiya xatosi: {result.reason}")
            return False

        return True

    def calibrate(self) -> bool:
        """Koordinatalarni kalibrlash moduli orqali sozlaydi (Requirement 4).

        Agar koordinatalar konstruktorda berilgan bo'lsa, kalibrlash
        o'tkazib yuboriladi. Aks holda `CalibrationModule.run()` chaqiriladi.
        Koordinatalar muvaffaqiyatli olinsa `True`, aks holda `False`.
        """
        if self.coords is not None:
            return True

        coords = self.calibration.run()
        if coords is None:
            print("Kalibrlash bekor qilindi yoki muvaffaqiyatsiz tugadi.")
            return False

        self.coords = coords
        return True

    # ------------------------------------------------------------------
    # Boshqaruv tugmalari va holat (GameStateMachine + KeyboardListener)
    # ------------------------------------------------------------------

    def wait_for_start(self) -> bool:
        """'S' bosilishini kutadi (IDLE -> RUNNING, Requirement 6.1).

        'Q' bosilsa kutish bekor qilinadi va STOPPED ga o'tiladi. RUNNING
        holatiga o'tilganda `True`, STOPPED bo'lib qolsa `False` qaytadi.
        """
        print("Boshlash uchun 'S' tugmasini bosing (to'xtatish uchun 'Q').")
        # 'S' yoki 'Q' kelguncha klaviaturani kuzatamiz (~100 ms oralig'ida).
        while self.state_machine.state is State.IDLE:
            key = self.keyboard_listener.poll()
            if key is not None:
                self.state_machine.on_key(key)
            else:
                # Polling oralig'i (~100 ms, Requirement 6.3).
                self._sleeper(0.1)

        if self.state_machine.state is State.RUNNING:
            print("Kesish boshlandi.")
            return True

        # IDLE da 'Q' bosilgan bo'lsa STOPPED bo'ladi.
        self.stop_safely("Foydalanuvchi to'xtatdi.")
        return False

    # ------------------------------------------------------------------
    # Asosiy o'yin tsikli
    # ------------------------------------------------------------------

    def run_game_loop(self) -> None:
        """RUNNING holatida o'yin tsiklini bajaradi.

        Har bir iteratsiyada: 'Q' tekshiriladi, piksellar o'qiladi, qaror
        chiqariladi, bosish bajariladi, ball oshiriladi va chop etiladi,
        so'ng kechikish qo'shiladi va to'xtash sharti tekshiriladi.
        """
        while self.state_machine.state is State.RUNNING:
            # 'Q' bosilganini tekshiramiz (Requirement 6.2).
            key = self.keyboard_listener.poll()
            if key is ControlKey.STOP:
                self.stop_safely("Foydalanuvchi 'Q' tugmasini bosdi.")
                break

            # Bitta kesish tsiklini bajaramiz; muvaffaqiyatsiz bo'lsa to'xtaymiz.
            if not self._run_one_cycle():
                break

            # To'xtash sharti: maqsadli ballga yetildi (Requirement 3.5).
            if self.score_counter.target_reached():
                self.stop_safely(
                    f"Maqsadli ball ({self.config.target_score}) ga yetildi."
                )
                break

            # Inson tezligiga o'xshash kechikish (Requirement 5.1).
            self._apply_delay()

    def _run_one_cycle(self) -> bool:
        """Bitta sense-decide-act iteratsiyasini bajaradi.

        Tsikl davom etishi mumkin bo'lsa `True`, xavfsiz to'xtash kerak
        bo'lsa (DANGER_STOP yoki PixelReadError) `False` qaytaradi.
        """
        # 1) Piksellarni o'qish; o'qib bo'lmasa xavfsiz to'xtaymiz (Requirement 2.6).
        try:
            sample = self.screen_capture.read_branch_points(self.coords)
        except PixelReadError as exc:
            self.stop_safely(f"Piksel o'qish xatosi: {exc}")
            return False

        # 2) Qaror chiqarish (BranchDetector).
        decision = self.branch_detector.decide(sample, self.hero_side)

        # 3) Xavfli holat: ikki tomonda ham shox -> to'xtash (Requirement 2.5).
        if decision is Decision.DANGER_STOP:
            self.stop_safely(
                "XAVF: ikkala tomonda ham shox aniqlandi. Kesish to'xtatildi."
            )
            return False

        # 4) Harakatni bajarish (bosish).
        self._perform_action(decision)

        # 5) Ballni oshirish va terminalga chop etish (Requirement 3.3, 3.4).
        new_score = self.score_counter.increment()
        print(f"Ball: {new_score}")

        return True

    def _perform_action(self, decision: Decision) -> None:
        """Qarorga muvofiq sichqoncha bosishini bajaradi.

        - MOVE_TO_SAFE: qahramonni qarama-qarshi (xavfsiz) tomonga o'tkazadi
          va joriy tomonni yangilaydi (Requirement 2.2).
        - STAY_AND_CHOP: qahramonni joriy tomonda qoldirib kesadi (Requirement 2.3).
        """
        if decision is Decision.MOVE_TO_SAFE:
            # Qahramon tomonida shox bor -> xavfsiz (qarama-qarshi) tomonga o'tamiz.
            safe_side = _opposite_side(self.hero_side)
            self.click_simulator.move_then_chop(safe_side, self.coords)
            # Qahramon endi xavfsiz tomonda turibdi.
            self.hero_side = safe_side
        else:
            # STAY_AND_CHOP: joriy tomonda kesishni davom ettiramiz.
            self.click_simulator.chop(self.hero_side, self.coords)

    def _apply_delay(self) -> None:
        """Ketma-ket kesishlar orasiga tasodifiy kechikish qo'shadi (Requirement 5.1)."""
        delay_ms = self.delay_generator.next_delay_ms()
        # DelayGenerator millisekundda qaytaradi; sleeper soniyada kutadi.
        self._sleeper(delay_ms / 1000.0)

    # ------------------------------------------------------------------
    # Xavfsiz to'xtatish
    # ------------------------------------------------------------------

    def stop_safely(self, reason: str) -> None:
        """Kesishni xavfsiz to'xtatadi: STOPPED ga o'tadi va kuzatuvni to'xtatadi.

        DANGER_STOP, PixelReadError, maqsadli ballga yetish yoki 'Q' bosilishi
        holatlarida chaqiriladi. Holat STOPPED ga o'tkaziladi va
        `KeyboardListener.stop()` chaqiriladi (Requirement 6.5). Bir necha
        marta chaqirilsa ham xavfsiz (idempotent).
        """
        print(reason)
        # Holat mashinasini STOPPED ga o'tkazamiz (RUNNING/IDLE + 'Q' -> STOPPED).
        if self.state_machine.state is not State.STOPPED:
            self.state_machine.on_key(ControlKey.STOP)
        # Klaviatura kuzatuvini darhol to'xtatamiz (Requirement 6.5).
        self.keyboard_listener.stop()

    # ------------------------------------------------------------------
    # Yuqori darajadagi kirish nuqtasi
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """To'liq oqimni bajaradi: tekshiruv -> validatsiya -> kalibrlash -> tsikl.

        Oqim:
            1. check_environment()  — kutubxonalar (fail-fast)
            2. validate_config()    — sozlamalar (fail-fast)
            3. calibrate()          — koordinatalar
            4. wait_for_start()     — 'S' kutiladi (IDLE -> RUNNING)
            5. run_game_loop()      — asosiy tsikl

        Tsikl normal yakunlansa (maqsadga yetish yoki 'Q') `True`, ishga
        tushishdan oldingi biror bosqich muvaffaqiyatsiz bo'lsa `False`.
        """
        # 1) Bog'liqliklar (Requirement 1.4–1.6). Yetishmasa hech qanday I/O siz to'xtash.
        if not self.check_environment():
            return False

        # 2) Konfiguratsiya validatsiyasi (Requirement 3.2, 5.3, 2.4).
        if not self.validate_config():
            return False

        # 3) Koordinatalarni kalibrlash (Requirement 4).
        if not self.calibrate():
            return False

        # 4) 'S' kutiladi (Requirement 6.1).
        if not self.wait_for_start():
            return False

        # 5) Asosiy o'yin tsikli (Requirement 2, 3, 5).
        self.run_game_loop()
        return True
