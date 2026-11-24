#!/usr/bin/env python3
"""Имитационный бот Подработка.МСК.

Работает БЕЗ базы данных — все смены, пользователи, отклики и статусы
хранятся в памяти и выдаются как демонстрационные данные. Подходит для
демонстрации работы сервиса в Bot-Control без настройки реального back-end.

Запуск:
    PODRABOTKA_BOT_TOKEN=123456:ABC-DEF... python bot/imitation_bot.py
"""

from __future__ import annotations

import os
from datetime import date, timedelta

import telebot
from telebot import types

BOT_TOKEN = os.environ.get("PODRABOTKA_BOT_TOKEN", "")
if not BOT_TOKEN:
    raise RuntimeError(
        "Задайте PODRABOTKA_BOT_TOKEN (токен от @BotFather), например:\n"
        "  PODRABOTKA_BOT_TOKEN=123456:ABC-DEF... python bot/imitation_bot.py"
    )

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ---------------------------------------------------------------------------
# Демо-данные (в памяти, имитация работы сервиса)
# ---------------------------------------------------------------------------

TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()
DAY_AFTER = (date.today() + timedelta(days=2)).isoformat()

DEMO_JOBS = [
    {
        "id": 101,
        "title": "Грузчик на склад Wildberries",
        "category": "Склад",
        "pay": 4500,
        "metro": "Автозаводская",
        "date": TOMORROW,
        "time": "09:00–18:00",
        "slots": "2 из 5",
        "status": "active",
        "employer": "ООО «Логистика-М»",
        "verified": True,
    },
    {
        "id": 102,
        "title": "Курьер доставки еды",
        "category": "Курьер",
        "pay": 3800,
        "metro": "Китай-город",
        "date": TODAY,
        "time": "12:00–21:00",
        "slots": "1 из 3",
        "status": "active",
        "employer": "ИП Смирнов А.В.",
        "verified": False,
    },
    {
        "id": 103,
        "title": "Официант в кафе",
        "category": "Официант",
        "pay": 3200,
        "metro": "Тверская",
        "date": DAY_AFTER,
        "time": "17:00–23:00",
        "slots": "4 из 6",
        "status": "active",
        "employer": "Кафе «Уют»",
        "verified": True,
    },
    {
        "id": 104,
        "title": "Промоутер в ТЦ",
        "category": "Промоутер",
        "pay": 2900,
        "metro": "ВДНХ",
        "date": TODAY,
        "time": "10:00–16:00",
        "slots": "0 из 2",
        "status": "active",
        "employer": "Агентство «Ярмарка»",
        "verified": False,
    },
    {
        "id": 105,
        "title": "Уборщик помещений",
        "category": "Уборка",
        "pay": 3400,
        "metro": "Парк Победы",
        "date": TOMORROW,
        "time": "08:00–12:00",
        "slots": "3 из 3",
        "status": "active",
        "employer": "ООО «Чистый дом»",
        "verified": True,
    },
]

DEMO_MY_JOBS = [
    {
        "id": 101,
        "title": "Грузчик на склад Wildberries",
        "pay": 4500,
        "metro": "Автозаводская",
        "date": TOMORROW,
        "status": "active",
        "applications": 2,
        "pending": 2,
    },
    {
        "id": 103,
        "title": "Официант в кафе",
        "pay": 3200,
        "metro": "Тверская",
        "date": DAY_AFTER,
        "status": "paused",
        "applications": 0,
        "pending": 0,
    },
]

DEMO_MY_APPLICATIONS = [
    {
        "id": 7,
        "job_title": "Курьер доставки еды",
        "job_pay": 3800,
        "job_date": TODAY,
        "job_time": "12:00–21:00",
        "status": "pending",
        "employer": "ИП Смирнов А.В.",
    },
    {
        "id": 5,
        "job_title": "Промоутер в ТЦ",
        "job_pay": 2900,
        "job_date": DAY_AFTER,
        "job_time": "10:00–16:00",
        "status": "accepted",
        "employer": "Агентство «Ярмарка»",
    },
]

STATUS_LABELS = {
    "pending": "⏳ Ожидает решения",
    "accepted": "✅ Принят",
    "completed": "🏁 Смена завершена",
    "rejected": "⛔ Отказ",
    "cancelled": "🚫 Отменён",
}

JOB_STATUS_LABELS = {
    "active": "🟢 Активна",
    "paused": "⏸ Пауза",
    "closed": "⛔ Закрыта",
}

CATEGORY_EMOJI = {
    "Склад": "🏬",
    "Курьер": "🚴",
    "Официант": "🍽",
    "Промоутер": "🎤",
    "Уборка": "🧹",
    "Стройка": "🏗",
    "Мероприятия": "🎪",
    "Грузчик": "📦",
}

# ---------------------------------------------------------------------------
# Сессии пользователей (в памяти)
# ---------------------------------------------------------------------------

sessions: dict[int, dict] = {}


def session(chat_id: int) -> dict:
    return sessions.setdefault(chat_id, {"role": None, "view": "start"})


# ---------------------------------------------------------------------------
# Клавиатуры
# ---------------------------------------------------------------------------

def kb_main(role: str | None = None) -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if role == "employer":
        kb.row("📦 Мои смены", "👥 Кандидаты")
        kb.row("💬 Чаты", "👤 Профиль")
        kb.row("💰 Тарифы", "❓ Помощь")
    elif role == "worker":
        kb.row("🔍 Найти смену", "📅 Сегодня", "📅 Завтра")
        kb.row("⭐ Избранное", "📝 Мои отклики")
        kb.row("💬 Чаты", "👤 Профиль")
        kb.row("💰 Тарифы", "❓ Помощь")
    else:
        kb.row("🔗 Привязать аккаунт", "📝 Регистрация")
        kb.row("🔍 Найти смену", "💰 Тарифы", "❓ Помощь")
    return kb


def kb_jobs_list() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    for j in DEMO_JOBS:
        emoji = CATEGORY_EMOJI.get(j["category"], "📋")
        kb.row(
            types.InlineKeyboardButton(
                f"{emoji} {j['title']} — {j['pay']} ₽", callback_data=f"job:{j['id']}"
            )
        )
    kb.row(types.InlineKeyboardButton("🔄 Обновить", callback_data="jobs:refresh"))
    kb.row(types.InlineKeyboardButton("🌐 Веб-версия", url="https://visiontripin.github.io/Podrabotka/"))
    return kb


def kb_job_detail(job_id: int, has_applied: bool = False) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if not has_applied:
        kb.row(types.InlineKeyboardButton("✋ Откликнуться", callback_data=f"apply:{job_id}"))
    else:
        kb.row(types.InlineKeyboardButton("⏳ Отклик отправлен", callback_data="noop"))
    kb.row(types.InlineKeyboardButton("🤍 В избранное", callback_data=f"fav:{job_id}"))
    kb.row(types.InlineKeyboardButton("◀ К списку", callback_data="jobs:list"))
    return kb


def kb_applications() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    for a in DEMO_MY_APPLICATIONS:
        label = f"Отклик #{a['id']} — {STATUS_LABELS[a['status']]}"
        kb.row(types.InlineKeyboardButton(label, callback_data=f"myapp:{a['id']}"))
    return kb


def kb_my_jobs() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    for j in DEMO_MY_JOBS:
        kb.row(types.InlineKeyboardButton(f"Смена #{j['id']} — {JOB_STATUS_LABELS[j['status']]}", callback_data=f"myjob:{j['id']}"))
    return kb


def kb_candidates(job_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.row(types.InlineKeyboardButton("✅ Принять кандидата #7", callback_data=f"accept:7:{job_id}"))
    kb.row(types.InlineKeyboardButton("❌ Отклонить кандидата #7", callback_data=f"reject:7:{job_id}"))
    kb.row(types.InlineKeyboardButton("◀ К сменам", callback_data="employer:myjobs"))
    return kb


def kb_app_detail(app_id: int, status: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if status == "pending":
        kb.row(types.InlineKeyboardButton("🚫 Отменить отклик", callback_data=f"cancel:{app_id}"))
    kb.row(types.InlineKeyboardButton("💬 Написать работодателю", callback_data=f"chat:{app_id}"))
    kb.row(types.InlineKeyboardButton("◀ К откликам", callback_data="worker:applications"))
    return kb


def kb_my_job_detail(job_id: int, status: str) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    if status == "active":
        kb.row(types.InlineKeyboardButton("⏸ Приостановить", callback_data=f"pausejob:{job_id}"))
    elif status == "paused":
        kb.row(types.InlineKeyboardButton("▶️ Возобновить", callback_data=f"resumejob:{job_id}"))
    kb.row(types.InlineKeyboardButton("👥 Кандидаты", callback_data=f"candidates:{job_id}"))
    kb.row(types.InlineKeyboardButton("⛔ Закрыть смену", callback_data=f"closejob:{job_id}"))
    kb.row(types.InlineKeyboardButton("◀ Мои смены", callback_data="employer:myjobs"))
    return kb


# ---------------------------------------------------------------------------
# Вспомогательные форматеры
# ---------------------------------------------------------------------------

def money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₽"


def job_text(j: dict) -> str:
    verified = " ✅" if j.get("verified") else ""
    return (
        f"{CATEGORY_EMOJI.get(j['category'], '📋')} <b>{j['title']}</b>{verified}\n"
        f"💰 <b>{money(j['pay'])}</b> за смену\n"
        f"📍 {j['metro']} · {j['date']} · {j['time']}\n"
        f"👥 Мест: {j['slots']}\n"
        f"🏢 {j['employer']}\n"
    )


# ---------------------------------------------------------------------------
# Хендлеры
# ---------------------------------------------------------------------------

@bot.message_handler(commands=["start", "menu"])
def cmd_start(message: types.Message):
    chat_id = message.chat.id
    s = session(chat_id)
    s["view"] = "start"
    bot.send_message(
        chat_id,
        "Привет! Это демо-бот <b>Подработка.МСК</b>.\n\n"
        "Здесь всё работает в режиме имитации: смены, отклики и статусы — "
        "демонстрационные данные без реальной базы.\n\n"
        "Выберите, кем вы заходите:",
        reply_markup=kb_main(),
    )


# Явные command-хендлеры, чтобы Bot-Control видел прикрепление клавиатур
@bot.message_handler(commands=["jobs"])
def cmd_jobs(message: types.Message):
    bot.send_message(
        message.chat.id,
        "🔍 <b>Доступные смены (демо)</b>\nВыберите смену для подробностей:",
        reply_markup=kb_jobs_list(),
    )


@bot.message_handler(commands=["applications"])
def cmd_applications(message: types.Message):
    text_out = "📝 <b>Мои отклики (демо)</b>\n\n"
    for a in DEMO_MY_APPLICATIONS:
        text_out += (
            f"#{a['id']} {STATUS_LABELS[a['status']]} — {a['job_title']}\n"
            f"  🗓 {a['job_date']}, {a['job_time']} · {money(a['job_pay'])}\n"
            f"  🏢 {a['employer']}\n\n"
        )
    bot.send_message(message.chat.id, text_out, reply_markup=kb_applications())


@bot.message_handler(commands=["myjobs"])
def cmd_myjobs(message: types.Message):
    text_out = "📦 <b>Мои смены (демо)</b>\n\n"
    for j in DEMO_MY_JOBS:
        text_out += (
            f"• #{j['id']} {j['title']} — {money(j['pay'])} · {j['date']}\n"
            f"  {JOB_STATUS_LABELS[j['status']]} · откликов: {j['applications']} (в ожидании: {j['pending']})\n\n"
        )
    bot.send_message(message.chat.id, text_out, reply_markup=kb_my_jobs())


@bot.message_handler(commands=["candidates"])
def cmd_candidates(message: types.Message):
    bot.send_message(
        message.chat.id,
        "👥 <b>Кандидаты (демо)</b>\n\n"
        "На смену «Грузчик на склад Wildberries» откликнулся:\n"
        "• #7 — Алексей Demo — ⏳ Ожидает решения\n\n"
        "Выберите действие:",
        reply_markup=kb_candidates(101),
    )


@bot.message_handler(commands=["jobdetail"])
def cmd_jobdetail(message: types.Message):
    j = DEMO_JOBS[0]
    bot.send_message(
        message.chat.id,
        job_text(j) + "\nНажмите «Откликнуться», чтобы оставить заявку (имитация).",
        reply_markup=kb_job_detail(j["id"], has_applied=False),
    )


@bot.message_handler(commands=["appdetail"])
def cmd_appdetail(message: types.Message):
    a = DEMO_MY_APPLICATIONS[0]
    bot.send_message(
        message.chat.id,
        f"<b>Отклик #{a['id']}</b> — {STATUS_LABELS[a['status']]}\n\n"
        f"💼 {a['job_title']}\n"
        f"🗓 {a['job_date']}, {a['job_time']} · {money(a['job_pay'])}\n"
        f"🏢 {a['employer']}\n\n"
        f"(в демо-режиме статус не меняется)",
        reply_markup=kb_app_detail(a["id"], a["status"]),
    )


@bot.message_handler(commands=["примеры"])
def cmd_examples(message: types.Message):
    """Показывает примеры работы каждой кнопки (демо-гид)."""
    examples = (
        "📖 <b>Примеры работы кнопок (демо-гид)</b>\n\n"
        "<b>🔍 Найти смену</b> → открывает список доступных смен с категориями, оплатой, метро.\n"
        "Нажмите на смену → откроется карточка с подробностями и кнопкой «Откликнуться».\n\n"
        "<b>📅 Сегодня / 📅 Завтра</b> → показывает только смены на выбранную дату.\n\n"
        "<b>⭐ Избранное</b> → сохранённые смены (в демо пусто).\n\n"
        "<b>📝 Мои отклики</b> → список ваших откликов со статусами:\n"
        "• #7 — Курьер доставки еды — ⏳ Ожидает решения\n"
        "• #5 — Промоутер в ТЦ — ✅ Принят\n\n"
        "<b>📦 Мои смены</b> (работодателю) → ваши смены со статусом:\n"
        "• #101 — Грузчик на склад — 🟢 Активна · откликов: 2\n"
        "• #103 — Официант в кафе — ⏸ Пауза\n\n"
        "<b>👥 Кандидаты</b> → откликнувшиеся на вашу смену с кнопками ✅ Принять / ❌ Отклонить.\n\n"
        "<b>💬 Чаты</b> → демо-диалог с работодателем (отправка имитируется).\n\n"
        "<b>👤 Профиль</b> → ваши данные, рейтинг, закрытые смены, заработок.\n\n"
        "<b>💰 Тарифы</b> → тарифы исполнителя и работодателя.\n\n"
        "<b>❓ Помощь</b> → общая справка по боту.\n\n"
        "<b>🔗 Привязать аккаунт / 📝 Регистрация</b> → в демо уже активен аккаунт Алексей Demo.\n"
    )
    bot.send_message(message.chat.id, examples, reply_markup=kb_main(session(message.chat.id).get("role")))


@bot.message_handler(commands=["myjobdetail"])
def cmd_myjobdetail(message: types.Message):
    j = DEMO_MY_JOBS[0]
    bot.send_message(
        message.chat.id,
        f"<b>Смена #{j['id']}</b> — {j['title']}\n"
        f"💰 {money(j['pay'])} · 📍 {j['metro']} · 🗓 {j['date']}\n"
        f"Статус: {JOB_STATUS_LABELS[j['status']]}\n"
        f"Откликов: {j['applications']} (в ожидании: {j['pending']})\n",
        reply_markup=kb_my_job_detail(j["id"], j["status"]),
    )


@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message):
    bot.send_message(
        message.chat.id,
        "❓ <b>Помощь (демо-режим)</b>\n\n"
        "🔍 Найти смену — просмотр демонстрационных смен\n"
        "📝 Мои отклики — имитация откликов\n"
        "📦 Мои смены (работодателю) — управление сменами и кандидатами\n"
        "👤 Профиль — демо-профиль\n"
        "\nВсе данные выдуманы, никакие реальные действия не выполняются.",
    )


@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(message: types.Message):
    chat_id = message.chat.id
    text = (message.text or "").strip()
    s = session(chat_id)

    # Выбор роли при старте
    if s["view"] == "start":
        if text in ("👷 Исполнитель", "Я ищу подработку", "worker", "исполнитель"):
            s["role"] = "worker"
            s["view"] = "menu"
            bot.send_message(
                chat_id,
                "Режим: <b>👷 Исполнитель</b>\nВыберите действие:",
                reply_markup=kb_main("worker"),
            )
            return
        if text in ("🏢 Работодатель", "Я нанимаю", "employer", "работодатель"):
            s["role"] = "employer"
            s["view"] = "menu"
            bot.send_message(
                chat_id,
                "Режим: <b>🏢 Работодатель</b>\nВыберите действие:",
                reply_markup=kb_main("employer"),
            )
            return
        # Покажем выбор roli кнопками
        role_kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        role_kb.row("👷 Я ищу подработку (исполнитель)")
        role_kb.row("🏢 Я нанимаю (работодатель)")
        bot.send_message(
            chat_id,
            "Кем вы будете на платформе?",
            reply_markup=role_kb,
        )
        return

    role = s.get("role")

    if text == "🔍 Найти смену":
        bot.send_message(
            chat_id,
            "🔍 <b>Доступные смены (демо)</b>\nВыберите смену для подробностей:",
            reply_markup=kb_jobs_list(),
        )
        return

    if text == "📅 Сегодня":
        todays = [j for j in DEMO_JOBS if j["date"] == TODAY]
        if not todays:
            bot.send_message(chat_id, "На сегодня смен не найдено (демо).")
            return
        text_out = "📅 <b>Смены на сегодня</b>\n\n"
        for j in todays:
            text_out += job_text(j) + "\n"
        bot.send_message(chat_id, text_out, reply_markup=kb_jobs_list())
        return

    if text == "📅 Завтра":
        tomorrows = [j for j in DEMO_JOBS if j["date"] == TOMORROW]
        text_out = "📅 <b>Смены на завтра</b>\n\n"
        for j in tomorrows:
            text_out += job_text(j) + "\n"
        bot.send_message(chat_id, text_out, reply_markup=kb_jobs_list())
        return

    if text == "⭐ Избранное":
        bot.send_message(
            chat_id,
            "⭐ <b>Избранное (демо)</b>\n\n"
            "Пока пусто. В реальном боте здесь сохраняются понравившиеся смены.",
            reply_markup=kb_main(role),
        )
        return

    if text == "📝 Мои отклики":
        s["view"] = "applications"
        text_out = "📝 <b>Мои отклики (демо)</b>\n\n"
        for a in DEMO_MY_APPLICATIONS:
            text_out += (
                f"#{a['id']} {STATUS_LABELS[a['status']]} — {a['job_title']}\n"
                f"  🗓 {a['job_date']}, {a['job_time']} · {money(a['job_pay'])}\n"
                f"  🏢 {a['employer']}\n\n"
            )
        bot.send_message(chat_id, text_out, reply_markup=kb_applications())
        return

    if text == "📦 Мои смены":
        if role != "employer":
            bot.send_message(chat_id, "Этот раздел для работодателей. Смените роль через /start.")
            return
        s["view"] = "myjobs"
        text_out = "📦 <b>Мои смены (демо)</b>\n\n"
        for j in DEMO_MY_JOBS:
            text_out += (
                f"• #{j['id']} {j['title']} — {money(j['pay'])} · {j['date']}\n"
                f"  {JOB_STATUS_LABELS[j['status']]} · откликов: {j['applications']} (в ожидании: {j['pending']})\n\n"
            )
        bot.send_message(chat_id, text_out, reply_markup=kb_my_jobs())
        return

    if text == "👥 Кандидаты":
        if role != "employer":
            bot.send_message(chat_id, "Этот раздел для работодателей.")
            return
        bot.send_message(
            chat_id,
            "👥 <b>Кандидаты (демо)</b>\n\n"
            "На смену «Грузчик на склад Wildberries» откликнулся:\n"
            "• #7 — Алексей Demo — ⏳ Ожидает решения\n\n"
            "Выберите действие:",
            reply_markup=kb_candidates(101),
        )
        return

    if text == "💬 Чаты":
        bot.send_message(
            chat_id,
            "💬 <b>Чаты (демо)</b>\n\n"
            "Диалог с ИП Смирнов А.В. по смене «Курьер доставки еды»:\n"
            "Вы: Добрый день, я готов выйти на смену!\n"
            "Работодатель: Отлично, ждём вас в 12:00.\n"
            "(в демо-режиме отправка сообщений имитируется)",
            reply_markup=kb_main(role),
        )
        return

    if text == "👤 Профиль":
        role_label = {"worker": "👷 Исполнитель", "employer": "🏢 Работодатель"}.get(role, "—")
        bot.send_message(
            chat_id,
            "👤 <b>Профиль (демо)</b>\n\n"
            f"Имя: Алексей Demo\n"
            f"Роль: {role_label or 'не выбрана'}\n"
            f"Email: alexey.demo@example.com\n"
            f"Рейтинг: 4.9 ★ (12 отзывов)\n"
            f"Закрытых смен: 8\n"
            f"Заработано: 28 500 ₽\n"
            "\n(все данные выдуманы)",
            reply_markup=kb_main(role),
        )
        return

    if text == "💰 Тарифы":
        bot.send_message(
            chat_id,
            "💰 <b>Тарифы (демо)</b>\n\n"
            "👷 Исполнителю:\n"
            "• Бесплатный — до 5 откликов/день\n"
            "• Про (299 ₽/мес) — безлимит откликов\n"
            "\n🏢 Работодателю:\n"
            "• Старт — до 5 активных смен\n"
            "• Бизнес — без лимита\n"
            "\n(демо-данные, оплата не привязана)",
            reply_markup=kb_main(role),
        )
        return

    if text == "❓ Помощь":
        cmd_help(message)
        return

    if text == "🔗 Привязать аккаунт":
        bot.send_message(
            chat_id,
            "🔗 <b>Привязка (демо)</b>\n\n"
            "В реальном боте здесь привязывается Telegram к аккаунту на сайте. "
            "В демо-режиме это имитируется — вы уже вошли как Алексей Demo.",
            reply_markup=kb_main(role),
        )
        return

    if text == "📝 Регистрация":
        bot.send_message(
            chat_id,
            "📝 <b>Регистрация (демо)</b>\n\n"
            "Демо-аккаунт уже активен: Алексей Demo (a­lexey.demo@example.com). "
            "Реальная регистрация не требуется.",
            reply_markup=kb_main(role),
        )
        return

    bot.send_message(
        chat_id,
        "Выберите кнопку в меню ниже или /start — перезапустить демо.",
        reply_markup=kb_main(role),
    )


# ---------------------------------------------------------------------------
# Callback-запросы (inline-кнопки)
# ---------------------------------------------------------------------------

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    data = call.data or ""
    s = session(chat_id)
    role = s.get("role")

    bot.answer_callback_query(call.id)

    if data == "noop":
        return

    if data == "jobs:refresh":
        bot.edit_message_text(
            "🔍 <b>Доступные смены (демо)</b>\nВыберите смену для подробностей:",
            chat_id,
            call.message.message_id,
            reply_markup=kb_jobs_list(),
        )
        return

    if data == "jobs:list":
        bot.edit_message_text(
            "🔍 <b>Доступные смены (демо)</b>\nВыберите смену для подробностей:",
            chat_id,
            call.message.message_id,
            reply_markup=kb_jobs_list(),
        )
        return

    if data.startswith("job:"):
        job_id = int(data.split(":")[1])
        job = next((j for j in DEMO_JOBS if j["id"] == job_id), None)
        if not job:
            bot.send_message(chat_id, "Смена не найдена (демо).")
            return
        bot.edit_message_text(
            job_text(job) + "\nНажмите «Откликнуться», чтобы оставить заявку (имитация).",
            chat_id,
            call.message.message_id,
            reply_markup=kb_job_detail(job_id, has_applied=False),
        )
        return

    if data.startswith("apply:"):
        job_id = int(data.split(":")[1])
        job = next((j for j in DEMO_JOBS if j["id"] == job_id), None)
        bot.edit_message_text(
            f"✅ <b>Отклик отправлен (имитация)</b>\n\n"
            f"Вы откликнулись на «{job['title'] if job else 'смену'}» "
            f"({money(job['pay']) if job else ''}).\n"
            f"Работодатель получит уведомление и примет решение.\n\n"
            f"Статус отклика: ⏳ Ожидает решения",
            chat_id,
            call.message.message_id,
            reply_markup=kb_job_detail(job_id, has_applied=True),
        )
        return

    if data.startswith("fav:"):
        job_id = int(data.split(":")[1])
        bot.answer_callback_query(call.id, "Добавлено в избранное (демо) ⭐", show_alert=False)
        return

    if data == "worker:applications":
        text_out = "📝 <b>Мои отклики (демо)</b>\n\n"
        for a in DEMO_MY_APPLICATIONS:
            text_out += (
                f"#{a['id']} {STATUS_LABELS[a['status']]} — {a['job_title']}\n"
                f"  🗓 {a['job_date']}, {a['job_time']} · {money(a['job_pay'])}\n"
                f"  🏢 {a['employer']}\n\n"
            )
        bot.edit_message_text(text_out, chat_id, call.message.message_id, reply_markup=kb_applications())
        return

    if data.startswith("myapp:"):
        app_id = int(data.split(":")[1])
        app = next((a for a in DEMO_MY_APPLICATIONS if a["id"] == app_id), None)
        if not app:
            bot.send_message(chat_id, "Отклик не найден (демо).")
            return
        bot.edit_message_text(
            f"<b>Отклик #{app['id']}</b> — {STATUS_LABELS[app['status']]}\n\n"
            f"💼 {app['job_title']}\n"
            f"🗓 {app['job_date']}, {app['job_time']} · {money(app['job_pay'])}\n"
            f"🏢 {app['employer']}\n\n"
            f"(в демо-режиме статус не меняется)",
            chat_id,
            call.message.message_id,
            reply_markup=kb_app_detail(app_id, app["status"]),
        )
        return

    if data == "employer:myjobs":
        text_out = "📦 <b>Мои смены (демо)</b>\n\n"
        for j in DEMO_MY_JOBS:
            text_out += (
                f"• #{j['id']} {j['title']} — {money(j['pay'])} · {j['date']}\n"
                f"  {JOB_STATUS_LABELS[j['status']]} · откликов: {j['applications']} (в ожидании: {j['pending']})\n\n"
            )
        bot.edit_message_text(text_out, chat_id, call.message.message_id, reply_markup=kb_my_jobs())
        return

    if data.startswith("myjob:"):
        job_id = int(data.split(":")[1])
        job = next((j for j in DEMO_MY_JOBS if j["id"] == job_id), None)
        if not job:
            bot.send_message(chat_id, "Смена не найдена (демо).")
            return
        bot.edit_message_text(
            f"<b>Смена #{job['id']}</b> — {job['title']}\n"
            f"💰 {money(job['pay'])} · 📍 {job['metro']} · 🗓 {job['date']}\n"
            f"Статус: {JOB_STATUS_LABELS[job['status']]}\n"
            f"Откликов: {job['applications']} (в ожидании: {job['pending']})\n",
            chat_id,
            call.message.message_id,
            reply_markup=kb_my_job_detail(job_id, job["status"]),
        )
        return

    if data.startswith("pausejob:"):
        job_id = int(data.split(":")[1])
        bot.answer_callback_query(call.id, "Набор приостановлен (демо) ⏸")
        return

    if data.startswith("resumejob:"):
        job_id = int(data.split(":")[1])
        bot.answer_callback_query(call.id, "Набор возобновлён (демо) ▶️")
        return

    if data.startswith("closejob:"):
        job_id = int(data.split(":")[1])
        bot.answer_callback_query(call.id, "Смена закрыта (демо) ⛔")
        return

    if data.startswith("candidates:"):
        job_id = int(data.split(":")[1])
        bot.edit_message_text(
            "👥 <b>Кандидаты (демо)</b>\n\n"
            "На смену «Грузчик на склад Wildberries» откликнулся:\n"
            "• #7 — Алексей Demo — ⏳ Ожидает решения\n\n"
            "Выберите действие:",
            chat_id,
            call.message.message_id,
            reply_markup=kb_candidates(job_id),
        )
        return

    if data.startswith("accept:"):
        parts = data.split(":")
        app_id = int(parts[1])
        bot.answer_callback_query(call.id, f"Кандидат #{app_id} принят (демо) ✅")
        return

    if data.startswith("reject:"):
        parts = data.split(":")
        app_id = int(parts[1])
        bot.answer_callback_query(call.id, f"Кандидат #{app_id} отклонён (демо) ❌")
        return

    if data.startswith("cancel:"):
        app_id = int(data.split(":")[1])
        bot.answer_callback_query(call.id, f"Отклик #{app_id} отменён (демо) 🚫")
        return

    if data.startswith("chat:"):
        app_id = int(data.split(":")[1])
        bot.send_message(
            chat_id,
            f"💬 <b>Чат по отклику #{app_id} (демо)</b>\n\n"
            "Вы: Добрый день, я готов выйти на смену!\n"
            "Работодатель: Отлично, ждём вас.\n"
            "(отправка сообщений имитируется)",
        )
        return


def main():
    print("Имитационный бот Подработка.МСК запущен.")
    print("Режим: только демонстрация, без базы данных.")
    bot.infinity_polling(timeout=30, long_polling_timeout=25)


if __name__ == "__main__":
    main()
