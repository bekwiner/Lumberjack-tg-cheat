# Implementation Plan: lumberjack-bot

## Overview

Ushbu reja `lumberjack-bot` skriptini bosqichma-bosqich, ortib boruvchi qadamlarda quradi. Avval apparatdan mustaqil **sof mantiqiy komponentlar** (ConfigValidator, DelayGenerator, BranchDetector, ScoreCounter, GameStateMachine, DependencyChecker, CalibrationModule validatsiyasi) `hypothesis` yordamida xususiyat-asosli testlar bilan amalga oshiriladi. Keyin **I/O qatlami** (ScreenCaptureModule, ClickSimulator, KeyboardListener) quriladi va integratsiya/unit testlari bilan qoplanadi. So'ngra `BotController` barcha komponentlarni yagona o'yin tsikliga bog'laydi. Nihoyat hammasi izohlangan, qo'shimcha tahrirsiz ishga tushiriladigan bitta Python skriptiga jamlanadi va ishga tushirish/kalibrlash yo'riqnomasi qo'shiladi (Requirement 7).

Til: **Python 3.8+**, test: **pytest + hypothesis**.

## Tasks

- [x] 1. Loyiha tuzilmasi, ma'lumot modellari va test muhiti
  - [x] 1.1 Tuzilma, ma'lumot modellari va test muhitini sozlash
    - `lumberjack_bot/` paketini va `tests/` papkasini yaratish
    - `models.py` da `Side`, `Decision`, `ControlKey`, `State` enumlari hamda `RGBColor`, `Point`, `ScreenSize`, `CanvasCoords`, `BranchSample`, `BotConfig` dataclass'larini yozish
    - `PixelReadError` istisno sinfini aniqlash
    - `pytest` va `hypothesis` ni `requirements-dev.txt` ga qo'shib test ramkasini sozlash
    - _Requirements: 7.1_

- [x] 2. ConfigValidator (sof mantiq) — target_score va kechikish validatsiyasi
  - [x] 2.1 ConfigValidator implementatsiyasi
    - `validate_target_score(value)`: butun son va `1 <= x <= 1_000_000` tekshiruvi (yaroqsizda kesish boshlanmaydi)
    - `validate_delay(min_ms, max_ms)`: `10 <= min <= max <= 5000` tekshiruvi; rad etishda sabab qaytariladi va oldingi sozlama o'zgarmaydi
    - `validate_tolerance(value)`: butun son, `0 <= x <= 255`
    - _Requirements: 3.1, 3.2, 5.2, 5.3, 2.4_

  - [x]* 2.2 target_score validatsiyasi uchun xususiyat testi
    - **Property 5: target_score validatsiyasi**
    - **Validates: Requirements 3.1, 3.2**

  - [x]* 2.3 kechikish oralig'i validatsiyasi uchun xususiyat testi
    - **Property 7: Kechikish oralig'i validatsiyasi**
    - **Validates: Requirements 5.2, 5.3**

- [x] 3. DelayGenerator (sof mantiq)
  - [x] 3.1 DelayGenerator implementatsiyasi
    - `__init__(min_ms, max_ms)` va `next_delay_ms()` — `random.uniform` orqali `[min_ms, max_ms]` oralig'ida bir tekis tasodifiy kechikish
    - _Requirements: 5.1_

  - [x]* 3.2 tasodifiy kechikish uchun xususiyat testi
    - **Property 1: Tasodifiy kechikish doimo oraliq ichida**
    - **Validates: Requirements 5.1**

- [x] 4. BranchDetector (sof mantiq)
  - [x] 4.1 BranchDetector implementatsiyasi
    - `color_matches_branch(sample)`: har bir RGB kanal mustaqil ravishda `tolerance` chegarasida bo'lishini tekshirish
    - `decide(sample, hero_side)`: `DANGER_STOP` (ikki tomonda ham shox) / `MOVE_TO_SAFE` (qahramon tomonida shox) / `STAY_AND_CHOP` (shox yo'q) qaytarish
    - `tolerance` standart qiymati 30, oralig'i 0..255
    - _Requirements: 2.2, 2.3, 2.4, 2.5_

  - [x]* 4.2 shox aniqlash qarori uchun xususiyat testi
    - **Property 2: Shox aniqlash qarori to'g'ri**
    - **Validates: Requirements 2.2, 2.3, 2.5**

  - [x]* 4.3 tolerance monotonligi uchun xususiyat testi
    - **Property 3: Tolerance monotonligi**
    - **Validates: Requirements 2.4**

- [x] 5. ScoreCounter (sof mantiq)
  - [x] 5.1 ScoreCounter implementatsiyasi
    - `increment()`: joriy ballni 1 ga oshirib yangi qiymatni qaytaradi
    - `target_reached()`: `current >= target` bo'lganda `True`
    - _Requirements: 3.3, 3.5_

  - [x]* 5.2 ball sanagich uchun xususiyat testi
    - **Property 6: Ball sanagich to'g'riligi**
    - **Validates: Requirements 3.3, 3.5**

- [x] 6. GameStateMachine (sof mantiq)
  - [x] 6.1 GameStateMachine implementatsiyasi
    - `on_key(key)`: IDLE+'S'→RUNNING, IDLE/RUNNING+'Q'→STOPPED, RUNNING+'S'→RUNNING (e'tiborsiz), STOPPED+har qanday→STOPPED
    - _Requirements: 6.1, 6.2, 6.4_

  - [x]* 6.2 holat o'tishlari uchun xususiyat testi
    - **Property 8: Holat mashinasi o'tishlari to'g'ri**
    - **Validates: Requirements 6.1, 6.2, 6.4**

- [x] 7. Checkpoint — sof o'yin mantig'i testlari o'tishini tekshirish
  - Barcha testlar o'tishini ta'minlang, savol tug'ilsa foydalanuvchidan so'rang.

- [x] 8. DependencyChecker (sof mantiq)
  - [x] 8.1 DependencyChecker implementatsiyasi
    - `MissingDependency` dataclass (`name`, `install_command`)
    - `check_dependencies()`: `importlib.util.find_spec` orqali tekshirish; "screen_capture" guruhi `PIL` yoki `cv2` dan kamida bittasi bilan qoniqtiriladi; `pyautogui` va `keyboard` majburiy
    - Yetishmayotgan kutubxonalar nomi va o'rnatish buyrug'ini terminalga chop etuvchi hisobot funksiyasi; yetishmasa hech qanday I/O amalisiz to'xtash
    - _Requirements: 1.4, 1.5, 1.6_

  - [x]* 8.2 bog'liqlik tekshiruvi uchun xususiyat testi
    - **Property 9: Bog'liqlik tekshiruvi to'g'riligi**
    - **Validates: Requirements 1.4**

  - [x]* 8.3 yetishmayotgan kutubxonalar hisoboti uchun xususiyat testi
    - **Property 10: Yetishmayotgan kutubxonalar hisoboti to'liq**
    - **Validates: Requirements 1.5**

  - [x]* 8.4 yetishmayotgan kutubxonada I/O bajarilmasligi uchun unit test
    - Mock orqali capture/click/keyboard chaqirilmasligini tekshirish (fail-fast)
    - _Requirements: 1.6_

- [x] 9. I/O qatlami — ScreenCaptureModule, ClickSimulator, KeyboardListener
  - [x] 9.1 ScreenCaptureModule implementatsiyasi
    - `read_pixel(x, y)`: ImageGrab yoki OpenCV orqali piksel rangi; o'qib bo'lmasa `PixelReadError`
    - `read_branch_points(coords)`: chap va o'ng nuqtalardagi ranglarni `BranchSample` sifatida qaytarish
    - _Requirements: 2.1, 2.6_

  - [x]* 9.2 read_branch_points uchun integratsiya testi
    - Ikkala rangni qaytarishi va ~100 ms vaqt chegarasi ichida bajarilishi (mock manba)
    - _Requirements: 2.1_

  - [x]* 9.3 piksel o'qish xatosi uchun unit test
    - `PixelReadError` da xato indikatsiyasi ko'rsatilishi (mock)
    - _Requirements: 2.6_

  - [x] 9.4 ClickSimulator implementatsiyasi
    - `chop(side, coords)` va `move_then_chop(side, coords)` — pyautogui orqali sichqoncha bosishi
    - DelayGenerator bilan ketma-ket bosishlar orasiga kechikish qo'shish
    - _Requirements: 2.2, 5.1_

  - [x] 9.5 KeyboardListener implementatsiyasi
    - `poll()`: 'S'/'Q' bosilishini qaytarish; `stop()`: kuzatishni darhol to'xtatish
    - _Requirements: 6.3, 6.5_

  - [x]* 9.6 klaviatura polling uchun integratsiya testi
    - 'S'/'Q' tugmalarining ~100 ms polling oralig'ida kuzatilishi (mock)
    - _Requirements: 6.3_

  - [x]* 9.7 STOPPED holatida stop() chaqirilishi uchun unit test
    - STOPPED ga o'tishda `KeyboardListener.stop()` chaqirilishini tekshirish (mock)
    - _Requirements: 6.5_

- [x] 10. CalibrationModule — koordinata sozlash va validatsiya
  - [x] 10.1 CalibrationModule implementatsiyasi
    - `run()`: chap, o'ng, yuqori nuqtalarni raqamlangan ko'rsatmalar bilan sozlash; joriy sichqoncha koordinatasini har ~100 ms da ko'rsatish
    - `validate_coord(point, screen)`: `0 <= x < width` va `0 <= y < height`; rad etilganda oldingi koordinata o'zgarmaydi
    - Sozlangan koordinatalarni saqlash/o'qish (round-trip); saqlash xatosida oldingi qiymatni saqlab qolish
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x]* 10.2 koordinata saqlash round-trip uchun xususiyat testi
    - **Property 4: Koordinata saqlash round-trip**
    - **Validates: Requirements 4.4**

  - [x]* 10.3 koordinata validatsiyasi va o'zgarmaslik uchun xususiyat testi
    - **Property 11: Koordinata validatsiyasi va o'zgarmaslik**
    - **Validates: Requirements 4.5**

  - [x]* 10.4 kalibrlash boshlanishi va ko'rsatmalar uchun unit test
    - Ishga tushishda kalibrlash rejimi boshlanishi va raqamlangan ko'rsatmalar mavjudligi (mock)
    - _Requirements: 4.1, 4.2_

  - [x]* 10.5 saqlash xatosida koordinata saqlanishi uchun unit test
    - Saqlash muvaffaqiyatsiz bo'lganda oldingi koordinata o'zgarmasligi va xato indikatsiyasi (mock)
    - _Requirements: 4.6_

- [x] 11. Checkpoint — I/O va kalibrlash testlari o'tishini tekshirish
  - Barcha testlar o'tishini ta'minlang, savol tug'ilsa foydalanuvchidan so'rang.

- [x] 12. BotController — orkestratsiya va o'yin tsikli
  - [x] 12.1 BotController implementatsiyasi
    - DependencyChecker → ConfigValidator → CalibrationModule → GameStateMachine oqimini bog'lash
    - O'yin tsikli: piksel o'qish → `BranchDetector.decide` → bosish → `ScoreCounter.increment` → terminalga chop → kechikish → to'xtash shartini tekshirish
    - `DANGER_STOP` va `PixelReadError` holatlarida kesishni xavfsiz to'xtatish, STOPPED ga o'tish va `KeyboardListener.stop()` chaqirish
    - _Requirements: 2.5, 2.6, 3.4, 3.5, 6.1, 6.2_

  - [x]* 12.2 ball chop etilishi uchun unit test
    - `increment()` dan keyin yangilangan ballning terminalga chop etilishi (mock)
    - _Requirements: 3.4_

  - [x]* 12.3 xavfli holat va xato boshqaruvi uchun unit test
    - `DANGER_STOP` da xavf indikatsiyasi va to'xtash; `PixelReadError` da xato indikatsiyasi va to'xtash (mock)
    - _Requirements: 2.5, 2.6_

- [x] 13. Yagona ishga tushiriladigan skript va yo'riqnoma (Requirement 7)
  - [x] 13.1 Komponentlarni bitta ishga tushiriladigan skriptga jamlash
    - Barcha komponentlarni `lumberjack_bot.py` yagona skriptiga birlashtirish (`if __name__ == "__main__"` kirish nuqtasi bilan)
    - Fayl boshida foydalanuvchi sozlay oladigan o'zgaruvchilar (`target_score`, koordinatalar, `tolerance`, `min/max` kechikish) izohlovchi sharhlar bilan
    - Har bir asosiy komponentni izohlovchi sharhlar
    - _Requirements: 7.1, 7.2_

  - [x] 13.2 Ishga tushirish va kalibrlash yo'riqnomasini yozish
    - O'rnatish, ishga tushirish va boshlash bo'yicha tartiblangan, raqamlangan bosqichlar
    - Koordinatalarni kalibrlash (chap, o'ng, yuqori nuqtalarni belgilash va saqlash) bo'yicha raqamlangan bosqichlar
    - Skript ichidagi docstring/sharhlarda yoki `README` da joylashtirish
    - _Requirements: 7.3, 7.4_

  - [x]* 13.3 kerakli kutubxonalar importi uchun smoke testlar
    - ImageGrab/OpenCV, pyautogui va keyboard import qilinishini tekshirish
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 14. Yakuniy checkpoint — barcha testlar o'tishini tekshirish
  - Barcha testlar o'tishini ta'minlang, savol tug'ilsa foydalanuvchidan so'rang.

## Notes

- `*` bilan belgilangan vazifalar ixtiyoriy bo'lib, tezroq MVP uchun o'tkazib yuborilishi mumkin (lekin tavsiya etiladi).
- Har bir vazifa kuzatuvchanlik uchun aniq talab(lar)ga havola qiladi.
- Checkpoint'lar ortib boruvchi validatsiyani ta'minlaydi.
- Xususiyat testlari (Property 1–11) `hypothesis` bilan, har biri kamida 100 iteratsiya (`@settings(max_examples=100)`) ishlaydi va dizayndagi mos xususiyatga izoh bilan bog'lanadi.
- Unit testlar misol va edge-case holatlarni, integratsiya testlari vaqtga bog'liq I/O xulqini qoplaydi.
- Har bir vazifa avvalgi vazifalar ustiga quriladi va oxirida hamma narsa yagona ishga tushiriladigan skriptga bog'lanadi — osilib qolgan kod qoldirilmaydi.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "4.1", "5.1", "6.1", "8.1", "9.1", "9.4", "9.5", "10.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.2", "4.2", "4.3", "5.2", "6.2", "8.2", "8.3", "8.4", "9.2", "9.3", "9.6", "9.7", "10.2", "10.3", "10.4", "10.5", "12.1"] },
    { "id": 3, "tasks": ["12.2", "12.3", "13.1"] },
    { "id": 4, "tasks": ["13.2", "13.3"] }
  ]
}
```
