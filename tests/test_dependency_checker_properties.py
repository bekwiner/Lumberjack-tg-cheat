"""DependencyChecker uchun xususiyat-asosli testlar (hypothesis).

Dizayn hujjatining "Correctness Properties" bo'limidagi Property 9 va
Property 10 ni tekshiradi.
"""

import io
from contextlib import redirect_stdout
from typing import List, Set

from hypothesis import given, settings
from hypothesis import strategies as st

from lumberjack_bot.dependency_checker import (
    INSTALL_COMMANDS,
    MissingDependency,
    check_dependencies,
    report_missing_dependencies,
)


# Bog'liqlik tekshiruvi bilan bog'liq kutubxonalar to'plami.
RELEVANT_MODULES = ["PIL", "cv2", "pyautogui", "keyboard"]
# Tekshiruvga aloqasi bo'lmagan "shovqin" modullari (mavjud bo'lsa ham
# natijaga ta'sir qilmasligi kerak).
NOISE_MODULES = ["os", "sys", "json", "math", "collections"]


def _make_spec_finder(present: Set[str]):
    """`present` to'plamidagi modullar uchun spec qaytaruvchi soxta finder.

    `importlib.util.find_spec` imzosini taqlid qiladi: modul mavjud bo'lsa
    haqiqiy bo'lmagan obyekt, aks holda None qaytaradi.
    """

    def _finder(name: str):
        return object() if name in present else None

    return _finder


def _expected_missing(present: Set[str]) -> List[MissingDependency]:
    """Mustaqil mos'lash oracle'i: yetishmayotgan guruhlarni hisoblaydi.

    Implementatsiyadan mustaqil ravishda kutilgan natijani quradi:
      - "screen_capture" guruhi PIL yoki cv2 dan kamida bittasi mavjud
        bo'lsa qoniqtirilgan,
      - "pyautogui" va "keyboard" majburiy.
    """
    expected: List[MissingDependency] = []

    # screen_capture guruhi: PIL yoki cv2 dan kamida bittasi yetarli.
    if "PIL" not in present and "cv2" not in present:
        expected.append(
            MissingDependency(
                name="PIL yoki cv2",
                install_command=(
                    f"{INSTALL_COMMANDS['PIL']} yoki {INSTALL_COMMANDS['cv2']}"
                ),
            )
        )

    # pyautogui majburiy.
    if "pyautogui" not in present:
        expected.append(
            MissingDependency(
                name="pyautogui",
                install_command=INSTALL_COMMANDS["pyautogui"],
            )
        )

    # keyboard majburiy.
    if "keyboard" not in present:
        expected.append(
            MissingDependency(
                name="keyboard",
                install_command=INSTALL_COMMANDS["keyboard"],
            )
        )

    return expected


# Feature: lumberjack-bot, Property 9: Bog'liqlik tekshiruvi to'g'riligi
# For any mavjud/yetishmayotgan kutubxonalarning tasodifiy to'plami uchun,
# check_dependencies() aynan yetishmayotgan majburiy kutubxonalarni
# qaytaradi; "screen_capture" guruhi PIL yoki cv2 dan kamida bittasi
# mavjud bo'lganda qoniqtirilgan deb hisoblanadi.
# Validates: Requirements 1.4
@settings(max_examples=100)
@given(
    present=st.sets(st.sampled_from(RELEVANT_MODULES + NOISE_MODULES)),
)
def test_check_dependencies_correctness(present: Set[str]):
    spec_finder = _make_spec_finder(present)

    result = check_dependencies(spec_finder=spec_finder)
    expected = _expected_missing(present)

    # Tartibdan qat'i nazar aynan bir xil yetishmayotgan to'plam qaytishi kerak.
    assert set(result) == set(expected)
    # Dublikatsiz, har guruh uchun ko'pi bilan bitta yozuv.
    assert len(result) == len(expected)


# Yetishmayotgan kutubxona yozuvi uchun generator: nom va o'rnatish buyrug'i
# yangi qatorsiz, bo'sh bo'lmagan matnlar (chiqishda aniq qidirish uchun).
_safe_text = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\n\r"),
    min_size=1,
    max_size=40,
)

_missing_dependency = st.builds(
    MissingDependency,
    name=_safe_text,
    install_command=_safe_text,
)


# Feature: lumberjack-bot, Property 10: Yetishmayotgan kutubxonalar hisoboti to'liq
# For any yetishmayotgan kutubxonalar to'plami uchun, hosil qilingan terminal
# chiqishi har bir yetishmayotgan kutubxona nomini va unga mos o'rnatish
# buyrug'ini o'z ichiga oladi.
# Validates: Requirements 1.5
@settings(max_examples=100)
@given(missing=st.lists(_missing_dependency, min_size=1, max_size=8))
def test_report_missing_dependencies_complete(missing: List[MissingDependency]):
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        returned = report_missing_dependencies(missing)

    output = buffer.getvalue()

    # Yetishmayotganlar bo'lsa False qaytadi (chaqiruvchi to'xtaydi, 1.6).
    assert returned is False

    # Har bir yetishmayotgan kutubxona nomi va o'rnatish buyrug'i chiqishda bor.
    for dep in missing:
        assert dep.name in output
        assert dep.install_command in output
