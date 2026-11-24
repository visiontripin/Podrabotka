"""Точка входа Telegram-бота Подработка.МСК (полнофункциональный,data-backed).

Общается с той же SQLite-базой, что и веб-версия (server/index.ts), через
stdlib sqlite3. Запускается приложением ++Bot-Control++ или напрямую:
    python bot/podrabotka_bot.py   (переменная PODRABOTKA_BOT_TOKEN обязательна)
"""

from __future__ import annotations

import html
import threading
import time
from pathlib import Path

import telebot
from telebot.types import BotCommand

from .config import BOT_TOKEN, DB_PATH, NOTIFY_INTERVAL
from .constants import BOT_COMMANDS
from .db import Database
from . import format as fmt
from . import handlers_common as hc

WEB_TARGET_HINT = {
    "cabinet": "\n👤 Перейти в «Мой кабинет» на сайте.",
    "jobs": "\n🔍 Открыть каталог смен на сайте.",
    "profile": "\n👤 Открыть профиль на сайте.",
    "admin": "\n🛡 Перейти в панель модератора на сайте.",
}


class PodrabotkaBot:
    def __init__(self, token: str | None = None, db_path=None):
        self.token = token or BOT_TOKEN
        if not self.token:
            raise RuntimeError(
                "PODRABOTKA_BOT_TOKEN не задан. Получите токен у @BotFather и передайте "
                "через переменную окружения PODRABOTKA_BOT_TOKEN."
            )
        db_path = db_path or str(DB_PATH)
        self.db_path = db_path
        self.db = Database(Path(db_path))
        self.bot = telebot.TeleBot(self.token, parse_mode="HTML")
        self._notifier_thread: threading.Thread | None = None
        self._notifier_stop = threading.Event()
        self._cursor_lock = threading.Lock()

    # ---------- публичные ----------

    def setup(self):
        """Регистрирует все обработчики и команды бота."""
        hc.register(self.bot, self.db)
        self._set_commands()
        # Инициализируем курсор уведомлений, если ещё нет.
        if self.db.get_meta("notification_cursor") is None:
            self.db.set_meta("notification_cursor", str(self.db.max_notification_id()))

    def _set_commands(self):
        try:
            self.bot.set_my_commands([BotCommand(cmd, desc) for cmd, desc in BOT_COMMANDS])
        except Exception as exc:  # сеть/токен — не должны убивать запуск
            print(f"[bot] set_my_commands предупреждение: {exc}")

    def start_notifier(self):
        """Фоновый поток: опрашивает новые уведомления и шлёт в Telegram."""
        if self._notifier_thread and self._notifier_thread.is_alive():
            return
        self._notifier_stop.clear()
        self._notifier_thread = threading.Thread(target=self._notifier_loop, name="notifier", daemon=True)
        self._notifier_thread.start()
        print(f"[bot] notifier запущен (интервал {NOTIFY_INTERVAL} с)")

    def stop_notifier(self):
        self._notifier_stop.set()
        if self._notifier_thread:
            self._notifier_thread.join(timeout=5)

    def run(self):
        self.setup()
        self.start_notifier()
        print("[bot] polling запущен")
        try:
            self.bot.infinity_polling(timeout=30, long_polling_timeout=25)
        finally:
            self.stop_notifier()

    # ---------- нотификатор ----------

    def _notifier_loop(self):
        while not self._notifier_stop.wait(NOTIFY_INTERVAL):
            try:
                self._tick()
            except Exception as exc:  # не убиваем поток одной ошибкой
                print(f"[notifier] ошибка: {exc}")

    def _tick(self):
        with self._cursor_lock:
            cursor = int(self.db.get_meta("notification_cursor") or "0")
            rows = self.db.poll_unsent_notifications(cursor)
        if not rows:
            return
        for n in rows:
            try:
                self._deliver(n)
            except Exception as exc:
                print(f"[notifier] не удалось доставить уведомление id={n['id']}: {exc}")
            cursor = max(cursor, int(n["id"]))
        with self._cursor_lock:
            self.db.set_meta("notification_cursor", str(cursor))

    def _deliver(self, n: dict):
        telegram_id = int(n["telegram_id"])
        title = n.get("title") or "Уведомление от Подработка.МСК"
        body = n.get("body") or ""
        hint = WEB_TARGET_HINT.get(n.get("target_tab"), "")
        text = f"📬 <b>{fmt.esc(title)}</b>\n\n{fmt.esc(body)}{hint}"
        self.bot.send_message(telegram_id, text, parse_mode="HTML", disable_web_page_preview=True)


def main():
    PodrabotkaBot().run()


if __name__ == "__main__":
    main()
