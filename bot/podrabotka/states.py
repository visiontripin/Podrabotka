"""Простое in-memory хранилище состояний диалога (FSM)."""


class StateStore:
    def __init__(self):
        self._data: dict[int, dict] = {}

    def get(self, chat_id: int) -> dict | None:
        return self._data.get(chat_id)

    def set(self, chat_id: int, state: str, **data):
        self._data[chat_id] = {"state": state, **data}

    def update(self, chat_id: int, **data):
        cur = self._data.get(chat_id)
        if cur is None:
            self._data[chat_id] = dict(data)
        else:
            cur.update(data)

    def clear(self, chat_id: int):
        self._data.pop(chat_id, None)


store = StateStore()

# Имена состояний
LINK_EMAIL = "link_email"
REG_ROLE = "reg_role"       # выбираем роль (кнопками)
REG_NAME = "reg_name"
REG_EMAIL = "reg_email"
REG_PASSWORD = "reg_password"
APPLY_COVER = "apply_cover"     # ждём записку при отклике
CHAT_MESSAGE = "chat_message"   # ждём сообщение в мини-чате
REVIEW_COMMENT = "review_comment"
CJ_TITLE = "cj_title"
CJ_ADDRESS = "cj_address"
CJ_DATE_TEXT = "cj_date_text"
CJ_STATION_TEXT = "cj_station_text"
CJ_TIME = "cj_time"         # формат «09:00 18:00»
CJ_PAY = "cj_pay"
CJ_DESC = "cj_desc"
