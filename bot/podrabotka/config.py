"""Конфигурация бота: переменные окружения с разумными значениями по умолчанию."""

import os
from pathlib import Path

# Корень репозитория: bot/podrabotka/config.py -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

# Токен бота от @BotFather. Обязателен для запуска.
BOT_TOKEN = os.environ.get("PODRABOTKA_BOT_TOKEN", "").strip()

# Путь к SQLite-базе веб-версии. По умолчанию — <repo>/data/podrabotka.sqlite
# Если базы ещё нет, запустите веб-сервер один раз (npm run dev) — он создаст и наполнит её.
_DB_PATH = os.environ.get("PODRABOTKA_DB_PATH", "").strip()
if _DB_PATH:
    DB_PATH = Path(_DB_PATH).expanduser().resolve()
else:
    _DATA_DIR = os.environ.get("PODRABOTKA_DATA_DIR", "").strip()
    DB_PATH = Path(_DATA_DIR).expanduser().resolve() / "podrabotka.sqlite" if _DATA_DIR else REPO_ROOT / "data" / "podrabotka.sqlite"

# Публичный URL веб-версии (кнопки «🌐 Веб-версия»)
WEB_URL = os.environ.get("PODRABOTKA_WEB_URL", "https://visiontripin.github.io/Podrabotka/app.html").strip()

# URL демо-страницы
LANDING_URL = os.environ.get("PODRABOTKA_LANDING_URL", "https://visiontripin.github.io/Podrabotka/").strip()

# Как часто (сек) бот проверяет уведомления для привязанных аккаунтов
NOTIFY_INTERVAL = int(os.environ.get("PODRABOTKA_NOTIFY_INTERVAL", "15"))

# Сколько смен показывать на одной странице списка
JOBS_PAGE_SIZE = 5

# Сколько последних сообщений показывать в чате по отклику
CHAT_HISTORY = 8
