"""DependencyChecker (sof mantiq).

Ishga tushishdan oldin botga kerakli kutubxonalar mavjudligini tekshiradi
(Requirement 1.4–1.6). Komponent apparatdan mustaqil va sof mantiqiy:
kutubxonalarni qidiruvchi funksiya (`spec_finder`) tashqaridan kiritilishi
mumkin, shuning uchun xususiyat-asosli testlar ixtiyoriy mavjud/yetishmayotgan
to'plamlarni simulyatsiya qila oladi.

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


# Har bir kutubxona uchun import nomi -> o'rnatish buyrug'i.
# Import nomi (find_spec ga beriladigan nom) PyPI paket nomidan farq qilishi
# mumkin (masalan, "PIL" -> "Pillow", "cv2" -> "opencv-python").
INSTALL_COMMANDS: Dict[str, str] = {
    "PIL": "pip install Pillow",
    "cv2": "pip install opencv-python",
    "pyautogui": "pip install pyautogui",
    "keyboard": "pip install keyboard",
}

# Talab qilinadigan kutubxona guruhlari. Har bir guruh bir yoki bir nechta
# muqobil kutubxonadan iborat:
#   - "screen_capture" guruhi `PIL` YOKI `cv2` dan kamida bittasi bilan
#     qoniqtiriladi (Requirement 1.1).
#   - "pyautogui" va "keyboard" majburiy, bitta a'zoli guruhlar (1.2, 1.3).
REQUIRED: Dict[str, List[str]] = {
    "screen_capture": ["PIL", "cv2"],
    "pyautogui": ["pyautogui"],
    "keyboard": ["keyboard"],
}


@dataclass(frozen=True)
class MissingDependency:
    """Yetishmayotgan kutubxona (yoki guruh) haqidagi ma'lumot.

    `name` — guruh nomi yoki kutubxona nomi (foydalanuvchiga ko'rsatiladi).
    `install_command` — uni o'rnatish uchun terminal buyrug'i.
    """

    name: str
    install_command: str


# spec_finder funksiyasi `importlib.util.find_spec` bilan bir xil imzoga ega:
# berilgan modul nomi bo'yicha spec qaytaradi yoki topilmasa None.
SpecFinder = Callable[[str], Optional[object]]


def _is_available(module_name: str, spec_finder: SpecFinder) -> bool:
    """Berilgan modul mavjud bo'lsa True qaytaradi.

    `find_spec` ba'zi muhitlarda modul topilmaganda `ModuleNotFoundError`
    ko'tarishi mumkin (masalan, ota-paket yo'q bo'lsa); bunday holatni ham
    "mavjud emas" deb hisoblaymiz.
    """
    try:
        return spec_finder(module_name) is not None
    except (ImportError, ValueError):
        # ModuleNotFoundError ImportError dan meros oladi.
        return False


def _install_command_for(module_name: str) -> str:
    """Modul uchun o'rnatish buyrug'ini qaytaradi (noma'lum bo'lsa umumiy)."""
    return INSTALL_COMMANDS.get(module_name, f"pip install {module_name}")


def check_dependencies(spec_finder: SpecFinder = importlib.util.find_spec) -> List[MissingDependency]:
    """Yetishmayotgan kutubxonalar ro'yxatini qaytaradi.

    Bo'sh ro'yxat = barcha kerakli kutubxonalar mavjud (Requirement 1.4).
    Guruhdagi a'zolardan kamida bittasi mavjud bo'lsa, guruh qoniqtirilgan
    hisoblanadi (masalan, "screen_capture" uchun `PIL` yoki `cv2`).

    `spec_finder` test qilish uchun tashqaridan kiritilishi mumkin; standart
    holatda `importlib.util.find_spec` ishlatiladi.
    """
    missing: List[MissingDependency] = []

    for group_name, members in REQUIRED.items():
        # Guruhdagi a'zolardan birortasi mavjudmi?
        if any(_is_available(member, spec_finder) for member in members):
            continue

        # Guruh qoniqtirilmadi -> yetishmayotgan deb belgilaymiz.
        if len(members) == 1:
            # Bitta a'zoli majburiy guruh: kutubxona nomini to'g'ridan-to'g'ri
            # ishlatamiz.
            member = members[0]
            missing.append(
                MissingDependency(
                    name=member,
                    install_command=_install_command_for(member),
                )
            )
        else:
            # Ko'p muqobilli guruh (masalan, screen_capture): barcha
            # muqobillarni nom va buyruqlarda ko'rsatamiz.
            display_name = " yoki ".join(members)
            commands = " yoki ".join(
                _install_command_for(member) for member in members
            )
            missing.append(
                MissingDependency(
                    name=display_name,
                    install_command=commands,
                )
            )

    return missing


def report_missing_dependencies(missing: List[MissingDependency]) -> bool:
    """Yetishmayotgan kutubxonalarni terminalga chop etadi.

    Har bir yetishmayotgan kutubxona nomini va uni o'rnatish buyrug'ini
    chop etadi (Requirement 1.5). Agar ro'yxat bo'sh bo'lmasa, `False`
    qaytaradi — bu chaqiruvchiga hech qanday ekran/sichqoncha/klaviatura I/O
    amalini bajarmasdan to'xtash kerakligini bildiradi (Requirement 1.6).

    Hammasi mavjud bo'lsa (`missing` bo'sh), `True` qaytaradi.
    """
    if not missing:
        return True

    print("Quyidagi kerakli kutubxonalar yetishmayapti:")
    for dep in missing:
        print(f"  - {dep.name}: {dep.install_command}")
    print("Iltimos yuqoridagi kutubxonalarni o'rnatib, qaytadan ishga tushiring.")
    return False
