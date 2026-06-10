"""GameStateMachine uchun xususiyat-asosli testlar.

Ushbu modul Property 8 ni amalga oshiradi: holat mashinasi o'tishlari
dizayn hujjatidagi jadvalga to'liq mos kelishini tekshiradi.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from lumberjack_bot.models import ControlKey, State
from lumberjack_bot.state_machine import GameStateMachine


# Dizayn hujjatidagi o'tish jadvalini takrorlovchi mustaqil "oracle".
# Bu funksiya implementatsiyadan alohida, jadval qoidalarini to'g'ridan-to'g'ri
# aks ettiradi va implementatsiya bilan solishtirish uchun ishlatiladi.
def reference_transition(state: State, key: ControlKey) -> State:
    """O'tish jadvalining mustaqil ma'lumotnoma (oracle) implementatsiyasi.

    | Joriy holat | Hodisa     | Yangi holat |
    |-------------|------------|-------------|
    | IDLE        | START('S') | RUNNING     |
    | IDLE        | STOP('Q')  | STOPPED     |
    | RUNNING     | STOP('Q')  | STOPPED     |
    | RUNNING     | START('S') | RUNNING     |
    | STOPPED     | har qanday | STOPPED     |
    """
    if state is State.IDLE:
        if key is ControlKey.START:
            return State.RUNNING
        return State.STOPPED  # ControlKey.STOP
    if state is State.RUNNING:
        if key is ControlKey.STOP:
            return State.STOPPED
        return State.RUNNING  # START e'tiborsiz qoldiriladi
    # STOPPED — yakuniy holat: har qanday tugma uchun o'zgarmaydi.
    return State.STOPPED


# Feature: lumberjack-bot, Property 8: Holat mashinasi o'tishlari to'g'ri
@settings(max_examples=100)
@given(keys=st.lists(st.sampled_from(list(ControlKey)), max_size=20))
def test_property_8_state_machine_transitions(keys):
    """Property 8: For any joriy holat va boshqaruv tugmasi uchun mashina
    jadvaldagi o'tishni bajaradi.

    Tasodifiy ControlKey ketma-ketliklari hosil qilinadi va har bir o'tish
    ma'lumotnoma (oracle) bilan solishtiriladi. STOPPED ning yakuniy
    (terminal) ekanligi ham tasdiqlanadi.

    **Validates: Requirements 6.1, 6.2, 6.4**
    """
    machine = GameStateMachine()
    # Boshlang'ich holat doimo IDLE bo'lishi kerak.
    assert machine.state is State.IDLE

    expected = State.IDLE
    for key in keys:
        # STOPPED yakuniy holat ekanini kuzatish uchun oldingi holatni saqlaymiz.
        was_stopped = expected is State.STOPPED

        actual = machine.on_key(key)
        expected = reference_transition(expected, key)

        # Har bir o'tish oracle bilan aynan mos kelishi kerak.
        assert actual is expected
        # on_key qaytargan qiymat .state xususiyati bilan ham mos bo'lishi kerak.
        assert machine.state is actual

        # STOPPED yakuniy holat: bir marta STOPPED ga kirgach, hech qanday
        # tugma uni boshqa holatga o'tkaza olmaydi.
        if was_stopped:
            assert actual is State.STOPPED
