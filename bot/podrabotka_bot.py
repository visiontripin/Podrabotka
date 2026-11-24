#!/usr/bin/env python3
"""Тонкий запуск полнофункционального бота Подработка.МСК.

Использование:
    PODRABOTKA_BOT_TOKEN=123456:ABC-DEF... python bot/podrabotka_bot.py

Бот открывает ту же SQLite-базу, что и веб-версия (через PODRABOTKA_DB_PATH,
по умолчанию data/podrabotka.sqlite в корне репозитория).
"""

from podrabotka.bot import main

if __name__ == "__main__":
    main()
