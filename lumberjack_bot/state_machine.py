"""O'yin holat mashinasi (game state machine) — sof mantiq.

Ushbu modul `GameStateMachine` sinfini taqdim etadi. U botning
IDLE / RUNNING / STOPPED holatlari va ular orasidagi o'tishlarni
boshqaradi. Apparatdan mustaqil (sof mantiq), shu sababli xususiyat
asosli test qilinishi mumkin (Property 8).

Holat o'tishlari jadvali (dizayn hujjatiga muvofiq):

| Joriy holat | Hodisa     | Yangi holat | Izoh                     |
|-------------|------------|-------------|--------------------------|
| IDLE        | 'S'        | RUNNING     | Kesishni boshlash (6.1)  |
| IDLE        | 'Q'        | STOPPED     | To'xtatish               |
| RUNNING     | 'Q'        | STOPPED     | Kesishni to'xtatish (6.2)|
| RUNNING     | 'S'        | RUNNING     | E'tiborsiz (6.4)         |
| STOPPED     | har qanday | STOPPED     | Yakuniy holat            |

Eslatma: kod identifikatorlari inglizcha, izohlar o'zbekcha.
"""

from .models import ControlKey, State


class GameStateMachine:
    """IDLE/RUNNING/STOPPED holatlari va o'tishlarni boshqaradi.

    Requirement 6.1, 6.2, 6.4 ga muvofiq holat o'tishlarini amalga oshiradi.
    """

    def __init__(self) -> None:
        # Boshlang'ich holat doimo IDLE ('S' kutilmoqda).
        self._state: State = State.IDLE

    @property
    def state(self) -> State:
        """Joriy holatni qaytaradi."""
        return self._state

    def on_key(self, key: ControlKey) -> State:
        """Boshqaruv tugmasiga qarab holatni yangilaydi va yangi holatni qaytaradi.

        O'tish qoidalari:
        - IDLE + START('S')  -> RUNNING  (kesishni boshlash, 6.1)
        - IDLE + STOP('Q')   -> STOPPED  (to'xtatish)
        - RUNNING + STOP('Q')-> STOPPED  (kesishni to'xtatish, 6.2)
        - RUNNING + START('S')-> RUNNING (e'tiborsiz qoldiriladi, 6.4)
        - STOPPED + har qanday-> STOPPED (yakuniy holat, o'zgarmaydi)
        """
        if self._state is State.IDLE:
            if key is ControlKey.START:
                # IDLE holatida 'S' kesishni boshlaydi (6.1).
                self._state = State.RUNNING
            elif key is ControlKey.STOP:
                # IDLE holatida 'Q' to'xtatadi.
                self._state = State.STOPPED
        elif self._state is State.RUNNING:
            if key is ControlKey.STOP:
                # RUNNING holatida 'Q' kesishni to'xtatadi (6.2).
                self._state = State.STOPPED
            # RUNNING holatida 'S' e'tiborsiz qoldiriladi (6.4): holat o'zgarmaydi.
        # STOPPED — yakuniy holat: hech qanday tugma holatni o'zgartirmaydi.

        return self._state
