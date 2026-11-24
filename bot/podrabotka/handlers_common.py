"""Базовые страницы бота: помощь, тарифы, привязка аккаунта, чаты, отзывы.

Здесь же — главный диспетчер текстовых сообщений (состояние FSM →
действие) и единый обработчик callback-запросов.
"""

import html
import re
from telebot import TeleBot

from . import format as fmt
from . import keyboards as kb
from .config import LANDING_URL, WEB_URL
from .constants import BOT_COMMANDS
from .db import BotDBError, Database
from .states import store
from . import states as S


def user_of(db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    return uid, (db.serialize_user(uid) if uid else None)


def send_main_menu(bot: TeleBot, db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    if uid:
        user = db.serialize_user(uid)
        role = user["role"] if user else None
        text = (
            f"С возвращением, <b>{fmt.esc(user['name'])}</b>! 👋\n"
            f"Роль: { {'worker': '👷 Исполнитель', 'employer': '🏢 Работодатель', 'admin': '🛡 Модератор'}.get(role, role) }\n"
            "Выбирайте раздел кнопками ниже 👇"
        )
    else:
        role = None
        text = (
            "Привет! Это <b>Подработка.МСК</b> — короткие смены в Москве и МО "
            "с оплатой сразу после смены.\n\n"
            "Можно просто смотреть каталог, а чтобы откликаться и общаться с работодателями — привяжите аккаунт."
        )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb.reply_keyboard(role))


def ensure_linked(bot: TeleBot, db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    if uid:
        return uid
    store.clear(chat_id)
    bot.send_message(
        chat_id,
        "🔗 Для этого действия нужен аккаунт Подработка.МСК.\n\n"
        "Привяжите существующий (тот же, что на сайте) или создайте новый — это займёт минуту.",
        parse_mode="HTML",
        reply_markup=kb.link_prompt_keyboard(),
    )
    return None


# ---------- статические страницы ----------
HELP_TEXT = (
    "❓ <b>Помощь — Подработка.МСК</b>\n\n"
    "<b>Исполнителю (в роли 👷):</b>\n"
    "🔍 Найти смену — каталог с фильтрами по категории, району и дате\n"
    "📅 Сегодня / Завтра — быстрые выборки\n"
    "⭐ Избранное — сохранённые смены\n"
    "📝 Мои отклики — статусы, отмена, чат, оценка смены\n"
    "💬 Чаты — переписка с работодателями по вашим откликам\n\n"
    "<b>Работодателю (в роли 🏢):</b>\n"
    "📦 Мои смены — управление, кандидаты, клонирование\n"
    "➕ Создать смену — публикация за пару минут\n"
    "👥 Кандидаты — отклики, принять / отклонить / закрыть смену\n\n"
    "<b>Общие:</b>\n"
    "/profile — профиль и статистика\n"
    "/tariffs — тарифы и лимиты\n"
    "/notifications — уведомления из платформы в Telegram: вкл/выкл\n"
    "/unlink — отвязать аккаунт от Telegram\n"
    "/web — открыть веб-версию\n\n"
    "Смена данных (роль, тариф, навыки) — в веб-версии, кнопка ниже."
)

FAQ_TEXT = (
    "❓ <b>Частые вопросы</b>\n\n"
    "<b>Как быстро получить деньги?</b>\n"
    "Сразу после того, как работодатель закроет смену: СБП — моментально, наличные — в конце смены, СМЗ — на карту с чеком.\n\n"
    "<b>Нужен ли опыт?</b>\n"
    "Нет: у многих смен пометка «Без опыта», всему научат за 10–15 минут на месте.\n\n"
    "<b>Нужна ли медкнижка?</b>\n"
    "Только там, где указано: еда, дарксторы, пекарни. Смотрите требования в карточке смены.\n\n"
    "<b>Что такое самозанятость?</b>\n"
    "Оформление в «Мой налог» за 5 минут. Работодатели с пометкой СМЗ компенсируют налог 6%.\n\n"
    "<b>Как работает «бригада N из M»?</b>\n"
    "Работодатель указывает число мест. Принятые кандидаты занимают места, остальные видят «набор завершён».\n\n"
    "<b>Почему отклик не отправился?</b>\n"
    "Возможно, исчерпан лимит 5 бесплатных откликов в день (тариф «Про» — безлимит). Либо вы уже откликались на эту смену.\n\n"
    "<b>Можно ли отменить отклик?</b>\n"
    "Да: «📝 Мои отклики» → открыть отклик → «🚫 Отменить»."
)

SUPPORT_TEXT = (
    "🛠 <b>Поддержка</b>\n\n"
    f"Веб-версия: {WEB_URL}\n"
    f"Демо-страница: {LANDING_URL}\n\n"
    "Опишите проблему: смена, дата, что ожидали и что получили. "
    "Отзывы проходят модерацию вручную — это защищает честный рейтинг."
)


def cmd_help(bot, db, msg):
    bot.send_message(msg.chat.id, HELP_TEXT, parse_mode="HTML", disable_web_page_preview=True)


def cmd_faq(bot, db, msg):
    bot.send_message(msg.chat.id, FAQ_TEXT, parse_mode="HTML", disable_web_page_preview=True)


def cmd_support(bot, db, msg):
    bot.send_message(msg.chat.id, SUPPORT_TEXT, parse_mode="HTML", disable_web_page_preview=True)


def cmd_web(bot, db, msg):
    bot.send_message(
        msg.chat.id,
        f"🌐 <b>Веб-версия «Подработка.МСК»</b>\n{WEB_URL}\n\n"
        "Каталог со всеми фильтрами, кабинет, мини-чат, оценки и тарифы — всё на одном экране.",
        parse_mode="HTML",
        disable_web_page_preview=False,
    )


def cmd_menu(bot, db, msg):
    store.clear(msg.chat.id)
    send_main_menu(bot, db, msg.chat.id)


def cmd_cancel(bot, db, msg):
    store.clear(msg.chat.id)
    send_main_menu(bot, db, msg.chat.id)


def show_tariffs(bot, db, msg_or_chat_id):
    chat_id = msg_or_chat_id if isinstance(msg_or_chat_id, int) else msg_or_chat_id.chat.id
    uid = db.linked_user_id(chat_id)
    user = db.serialize_user(uid) if uid else None
    tariffs = db.list_tariffs()
    bot.send_message(
        chat_id,
        fmt.tariffs_text(tariffs, user["tariff_slug"] if user else None),
        parse_mode="HTML",
    )


def show_profile(bot, db, msg_or_chat_id):
    chat_id = msg_or_chat_id if isinstance(msg_or_chat_id, int) else msg_or_chat_id.chat.id
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    user = db.serialize_user(uid)
    bot.send_message(chat_id, fmt.profile_text(user), parse_mode="HTML")


def show_unlink(bot, db, msg):
    uid = db.linked_user_id(msg.chat.id)
    if not uid:
        bot.send_message(msg.chat.id, "Аккаунт и так не привязан. /start — чтобы привязать.")
        return
    bot.send_message(
        msg.chat.id,
        "Отвязать аккаунт от Telegram?\n"
        "Данные на сайте останутся, отклики и история сохранятся. Обратно привязать можно в любой момент командой /start.",
        reply_markup=kb.confirm_unlink_keyboard(),
    )


def show_notifications_state(bot, db, msg):
    uid = ensure_linked(bot, db, msg.chat.id)
    if not uid:
        return
    on = db.get_notify(msg.chat.id)
    bot.send_message(
        msg.chat.id,
        f"🔔 Уведомления из платформы в Telegram сейчас: <b>{'включены' if on else 'выключены'}</b>\n\n"
        "Сюда приходят новые отклики на ваши смены, приглашения, сообщения и решения по отзывам.\n"
        "Команда /notifications переключает эту настройку.",
        parse_mode="HTML",
    )


def toggle_notifications(bot, db, msg):
    uid = ensure_linked(bot, db, msg.chat.id)
    if not uid:
        return
    try:
        on = db.toggle_notify(msg.chat.id)
    except BotDBError as e:
        bot.send_message(msg.chat.id, str(e))
        return
    bot.send_message(
        msg.chat.id,
        f"🔔 Уведомления в Telegram <b>{'включены' if on else 'выключены'}</b>.",
        parse_mode="HTML",
    )


# ---------- привязка аккаунта ----------
def start_link(bot, db, chat_id):
    store.set(chat_id, S.LINK_EMAIL)
    bot.send_message(
        chat_id,
        "🔗 <b>Привязка аккаунта</b>\n\nВведите email, которым вы регистрировались на сайте "
        "(например, onedopea@gmail.com).",
        parse_mode="HTML",
    )


def handle_link_email(bot, db, msg):
    email = (msg.text or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        bot.send_message(msg.chat.id, "Это не похоже на email. Введите, например: onedopea@gmail.com")
        return
    user = db.get_user_by_email(email)
    if not user:
        store.clear(msg.chat.id)
        bot.send_message(
            msg.chat.id,
            "Такого email нет в базе. Создадим новый аккаунт прямо здесь?",
            reply_markup=kb.link_prompt_keyboard(),
        )
        return
    db.link_telegram(msg.chat.id, user["id"])
    store.clear(msg.chat.id)
    role_label = {"worker": "👷 Исполнитель", "employer": "🏢 Работодатель", "admin": "🛡 Модератор"}.get(user["role"], user["role"])
    bot.send_message(
        msg.chat.id,
        f"✅ Аккаунт <b>{fmt.esc(user['name'])}</b> ({role_label}) привязан!\n"
        "Теперь вам доступны отклики, чаты и уведомления.",
        parse_mode="HTML",
    )
    send_main_menu(bot, db, msg.chat.id)


def start_register(bot, db, chat_id):
    store.set(chat_id, S.REG_ROLE)
    bot.send_message(
        chat_id,
        "📝 <b>Регистрация в Подработка.МСК</b>\n\nКем вы будете на платформе?",
        parse_mode="HTML",
        reply_markup=kb.role_choice_keyboard(),
    )


def handle_reg_name(bot, db, msg):
    name = (msg.text or "").strip()
    if len(name) < 2:
        bot.send_message(msg.chat.id, "Имя слишком короткое. Как к вам обращаться?")
        return
    if len(name) > 80:
        bot.send_message(msg.chat.id, "Имя длиннее 80 символов — сократите, пожалуйста.")
        return
    cur = store.get(msg.chat.id) or {}
    store.set(msg.chat.id, S.REG_EMAIL, name=name, role=cur.get("role"))
    bot.send_message(msg.chat.id, "Приятно познакомиться! Теперь введите email для входа на сайте и в боте.")


def handle_reg_email(bot, db, msg):
    email = (msg.text or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        bot.send_message(msg.chat.id, "Это не похоже на email. Попробуйте ещё раз.")
        return
    if db.email_exists(email):
        bot.send_message(
            msg.chat.id,
            "Этот email уже зарегистрирован. Привязать существующий аккаунт? Отправьте /start и выберите «Привязать аккаунт».",
        )
        store.clear(msg.chat.id)
        return
    cur = store.get(msg.chat.id) or {}
    store.set(msg.chat.id, S.REG_PASSWORD, email=email, name=cur.get("name"), role=cur.get("role"))
    bot.send_message(
        msg.chat.id,
        "Придумайте пароль (от 4 символов) — тот же пароль подойдёт для входа на сайте.\n"
        "Отправьте /skip — будет выдан демо-пароль demo1234.",
    )


def handle_reg_password(bot, db, msg):
    raw = (msg.text or "").strip()
    if (msg.text or "").startswith("/skip"):
        password = "demo1234"
    else:
        if len(raw) < 4:
            bot.send_message(msg.chat.id, "Пароль короче 4 символов. Придумайте подлиннее или отправьте /skip.")
            return
        password = raw
    cur = store.get(msg.chat.id) or {}
    role = cur.get("role") or "worker"
    name = cur.get("name") or "Гость"
    email = cur.get("email")
    try:
        user_id = db.create_user(name, email, password, role)
    except Exception as e:
        bot.send_message(msg.chat.id, f"Не удалось создать аккаунт: {e}")
        store.clear(msg.chat.id)
        return
    db.link_telegram(msg.chat.id, user_id)
    store.clear(msg.chat.id)
    role_label = {"worker": "👷 Исполнитель", "employer": "🏢 Работодатель"}.get(role, role)
    bot.send_message(
        msg.chat.id,
        f"🎉 Аккаунт создан и привязан!\n\n"
        f"👤 <b>{fmt.esc(name)}</b> · {role_label}\n"
        f"📧 {fmt.esc(email)}\n\n"
        "Теперь можно откликаться на смены, общаться в чатах и получать уведомления.",
        parse_mode="HTML",
    )
    send_main_menu(bot, db, msg.chat.id)


# ---------- отклики: просмотр / отмена ----------
def show_application_card(bot, db, chat_id, app_id: int):
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    app = db.get_application(app_id)
    if not app:
        bot.send_message(chat_id, "Отклик не найден (возможно, смена удалена).")
        return
    is_worker = app["worker_id"] == uid
    is_employer = app["employer_id"] == uid
    user = db.serialize_user(uid)
    is_admin = user and user["role"] == "admin"
    if not (is_worker or is_employer or is_admin):
        bot.send_message(chat_id, "Это не ваш отклик.")
        return
    perspective = "worker" if is_worker else "employer"
    lines = [
        f"<b>{'Ваш отклик' if is_worker else 'Отклик сотрудника' if is_employer else 'Отклик'} #{app['id']}</b>",
        fmt.application_line(app, perspective=perspective),
    ]
    if is_employer or is_admin:
        lines.append("")
        lines.append(fmt.application_detail_employer(app))
    bot.send_message(chat_id, "\n".join(lines), parse_mode="HTML",
                     reply_markup=kb.application_card_keyboard(app, perspective))


def render_applications(bot, db, chat_id, *, perspective: str, only_pending: bool = False, title: str = ""):
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    user = db.serialize_user(uid)
    apps = db.list_applications(uid, user["role"])
    if perspective == "employer":
        apps = [a for a in apps if a["employer_id"] == uid]
    else:
        apps = [a for a in apps if a["worker_id"] == uid]
    if only_pending:
        pending = [a for a in apps if a["status"] == "pending"]
        apps = pending if pending else apps[:5]
    apps = apps[:10]
    if not apps:
        hint = "Пока пусто. Откройте каталог — там смены на сегодня и завтра." if perspective == "worker" \
            else "Откликов пока нет. Скоро всё изменится — проверьте активные смены."
        bot.send_message(chat_id, f"{title or 'Пока пусто'}\n\n{hint}")
        return
    header = title or ("📝 <b>Мои отклики</b>" if perspective == "worker" else "👥 <b>Отклики на ваши смены</b>")
    ids = []
    lines = [header, ""]
    for a in apps:
        lines.append(fmt.application_line(a, perspective=perspective))
        lines.append("")
        ids.append(a["id"])
    bot.send_message(chat_id, "\n".join(lines)[:3900], parse_mode="HTML",
                     reply_markup=kb.applications_list_keyboard(ids))


def cancel_application(bot, db, chat_id, app_id: int):
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    res = db.set_application_status(app_id, uid, "cancelled")
    bot.send_message(chat_id, "🚫 Отклик отменён." if res.get("ok") else f"⚠️ {res.get('error', 'Не удалось отменить')}")


# ---------- мини-чат по отклику ----------
def show_chat(bot, db, chat_id, app_id: int):
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    app = db.get_application(app_id)
    if not app:
        bot.send_message(chat_id, "Диалог не найден.")
        return
    if uid not in (app["worker_id"], app["employer_id"]):
        bot.send_message(chat_id, "Вы не участник этого диалога.")
        return
    from .config import CHAT_HISTORY
    messages = db.list_messages(app_id, CHAT_HISTORY)
    text = (
        f"💬 <b>Чат по смене «{fmt.esc(app['job_title'])}»</b>\n"
        f"🗓 {fmt.shift_date(app['shift_date'])}, {fmt.esc(app['start_time'])}–{fmt.esc(app['end_time'])}\n\n"
        + fmt.chat_history_text(messages, uid)
    )
    bot.send_message(chat_id, text[:4000], parse_mode="HTML", reply_markup=kb.chat_actions_keyboard(app_id))


def start_chat_input(bot, db, chat_id, app_id: int):
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    app = db.get_application(app_id)
    if not app:
        bot.send_message(chat_id, "Диалог не найден.")
        return
    if uid not in (app["worker_id"], app["employer_id"]):
        bot.send_message(chat_id, "Вы не участник этого диалога.")
        return
    store.set(chat_id, S.CHAT_MESSAGE, app_id=app_id)
    bot.send_message(chat_id, "✍️ Введите сообщение. /menu — выйти из чата.")


def handle_chat_message(bot, db, msg):
    cur = store.get(msg.chat.id) or {}
    app_id = cur.get("app_id")
    body = (msg.text or "").strip()
    uid = db.linked_user_id(msg.chat.id)
    res = db.add_message(app_id, uid, body)
    if res.get("ok"):
        bot.send_message(msg.chat.id, "✅ Отправлено. Продолжайте писать или /menu — выйти.")
    else:
        store.clear(msg.chat.id)
        bot.send_message(msg.chat.id, f"⚠️ {res.get('error', 'Сообщение не отправлено')}")


# ---------- отзыв ----------
def start_review(bot, db, chat_id, app_id: int):
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    app = db.get_application(app_id)
    if not app or uid not in (app["worker_id"], app["employer_id"]):
        bot.send_message(chat_id, "Это не ваша смена.")
        return
    if db.has_my_review(app_id, uid):
        bot.send_message(chat_id, "Вы уже оценили эту смену. Спасибо! 🙏")
        return
    from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
    kbmark = InlineKeyboardMarkup()
    kbmark.row(*[InlineKeyboardButton("⭐" * n, callback_data=f"rate:{app_id}:{n}") for n in range(1, 6)])
    bot.send_message(chat_id, "Оцените смену от 1 до 5 звёзд:", reply_markup=kbmark)


def pick_rating(bot, db, call, app_id: int, rating: int):
    chat_id = call.message.chat.id
    store.set(chat_id, S.REVIEW_COMMENT, app_id=app_id, rating=rating)
    bot.edit_message_text(
        f"{'⭐' * rating}\n\nНапишите короткий отзыв (что понравилось / что улучшить). "
        "Отзыв уйдёт на модерацию перед публикацией.",
        chat_id,
        call.message.message_id,
    )


def handle_review_comment(bot, db, msg):
    cur = store.get(msg.chat.id) or {}
    comment = (msg.text or "").strip()
    if len(comment) < 4:
        bot.send_message(msg.chat.id, "Отзыв слишком короткий — добавьте пару слов.")
        return
    uid = db.linked_user_id(msg.chat.id)
    res = db.add_review(uid, cur.get("app_id"), cur.get("rating", 5), comment)
    store.clear(msg.chat.id)
    if res.get("ok"):
        bot.send_message(msg.chat.id, "🙏 Спасибо! Отзыв отправлен на модерацию — после проверки он появится в рейтинге.")
    else:
        bot.send_message(msg.chat.id, f"⚠️ {res.get('error', 'Не удалось сохранить отзыв')}")


# ---------- диспетчеры ----------
def handle_text(bot: TeleBot, db: Database, msg):
    chat_id = msg.chat.id
    text = (msg.text or "").strip()

    if text.startswith("/"):
        return  # команды обрабатываются своими обработчиками

    cur = store.get(chat_id)
    if cur:
        state = cur.get("state")
        state_handlers = {
            S.LINK_EMAIL: handle_link_email,
            S.REG_NAME: handle_reg_name,
            S.REG_EMAIL: handle_reg_email,
            S.REG_PASSWORD: handle_reg_password,
            S.APPLY_COVER: handle_apply_cover,
            S.CHAT_MESSAGE: handle_chat_message,
            S.REVIEW_COMMENT: handle_review_comment,
        }
        handler = state_handlers.get(state)
        if handler:
            handler(bot, db, msg)
            return
        # Остальные состояния (cj_*) — у работодателя
        from . import handlers_employer
        if state.startswith("cj_"):
            handlers_employer.handle_create_state(bot, db, msg, state)
            return
        store.clear(chat_id)

    # Кнопки главного меню
    mapping = {
        kb.BTN_JOBS: "jobs:filters",
        kb.BTN_TODAY: "jobs:quick:today",
        kb.BTN_TOMORROW: "jobs:quick:tomorrow",
        kb.BTN_FAVORITES: "favorites",
        kb.BTN_APPLICATIONS: "my_applications",
        kb.BTN_MY_JOBS: "my_jobs",
        kb.BTN_CREATE_JOB: "create_job",
        kb.BTN_CANDIDATES: "candidates_all",
        kb.BTN_CHATS: "chats",
        kb.BTN_CABINET: "cabinet",
        kb.BTN_PROFILE: "profile",
        kb.BTN_TARIFFS: "tariffs",
        kb.BTN_HELP: "help",
        kb.BTN_OVERVIEW: "admin_overview",
        kb.BTN_MODERATION: "admin_moderation",
        "🔗 Привязать аккаунт": "link",
        "📝 Регистрация": "register",
    }
    action = mapping.get(text)
    if action:
        store.clear(chat_id)
        run_action(bot, db, msg, action)
        return

    bot.send_message(
        chat_id,
        "Не совсем понял 🤔 Выберите кнопку в меню ниже или /help — там все возможности.",
        reply_markup=kb.reply_keyboard(_role_or_none(db, chat_id)),
    )


def _role_or_none(db, chat_id):
    uid = db.linked_user_id(chat_id)
    if not uid:
        return None
    user = db.serialize_user(uid)
    return user["role"] if user else None


def handle_apply_cover(bot, db, msg):
    cur = store.get(msg.chat.id) or {}
    job_id = cur.get("job_id")
    text = (msg.text or "").strip()
    cover = "" if text.startswith("/skip") else text
    uid = db.linked_user_id(msg.chat.id)
    res = db.apply_to_job(uid, job_id, cover)
    store.clear(msg.chat.id)
    if res.get("ok"):
        bot.send_message(
            msg.chat.id,
            "✅ Отклик отправлен! Работодатель увидит вас в списке кандидатов — ответ придёт сюда же.",
        )
    else:
        note = f"⚠️ {res.get('error')}"
        if res.get("code") == "TARIFF_LIMIT":
            note += "\n\n💡 Тариф «Про» (299 ₽/мес) снимает лимит на отклики. Смотрите /tariffs."
        bot.send_message(msg.chat.id, note)


def run_action(bot, db, msg, action: str):
    chat_id = msg.chat.id
    from . import handlers_admin, handlers_employer, handlers_worker

    if action == "jobs:filters":
        handlers_worker.show_jobs_filters(bot, db, chat_id)
    elif action == "jobs:quick:today":
        handlers_worker.show_jobs_quick(bot, db, chat_id, "today")
    elif action == "jobs:quick:tomorrow":
        handlers_worker.show_jobs_quick(bot, db, chat_id, "tomorrow")
    elif action == "favorites":
        handlers_worker.show_favorites(bot, db, chat_id)
    elif action == "my_applications":
        render_applications(bot, db, chat_id, perspective="worker", title="📝 <b>Мои отклики</b>")
    elif action == "my_jobs":
        handlers_employer.show_my_jobs(bot, db, chat_id)
    elif action == "create_job":
        handlers_employer.start_create_job(bot, db, chat_id)
    elif action == "candidates_all":
        render_applications(bot, db, chat_id, perspective="employer", only_pending=True,
                            title="👥 <b>Кандидаты</b> (сначала ожидающие)")
    elif action == "chats":
        render_applications(bot, db, chat_id, perspective="worker" if _role_or_none(db, chat_id) == "worker" else "employer",
                            title="💬 <b>Чаты по откликам</b> — выберите диалог")
    elif action == "cabinet":
        show_profile(bot, db, chat_id)
    elif action == "profile":
        show_profile(bot, db, chat_id)
    elif action == "tariffs":
        show_tariffs(bot, db, chat_id)
    elif action == "help":
        cmd_help(bot, db, msg)
    elif action == "admin_overview":
        handlers_admin.show_overview(bot, db, chat_id)
    elif action == "admin_moderation":
        handlers_admin.show_moderation(bot, db, chat_id)
    elif action == "link":
        start_link(bot, db, chat_id)
    elif action == "register":
        start_register(bot, db, chat_id)


def handle_callback(bot: TeleBot, db: Database, call):
    chat_id = call.message.chat.id
    data = call.data or ""
    answer = True

    if data == "noop":
        bot.answer_callback_query(call.id)
        return

    # Привязка / регистрация / отвязка
    if data == "link:start":
        start_link(bot, db, chat_id)
        bot.answer_callback_query(call.id)
        return
    if data == "register:start":
        start_register(bot, db, chat_id)
        bot.answer_callback_query(call.id)
        return
    if data.startswith("register:role:"):
        role = data.split(":")[-1]
        store.set(chat_id, S.REG_NAME, role=role)
        bot.edit_message_text(
            "Отлично! Как к вам обращаться? Введите имя.",
            chat_id, call.message.message_id,
        )
        bot.answer_callback_query(call.id)
        return
    if data == "unlink:confirm":
        db.unlink_telegram(chat_id)
        bot.edit_message_text("Аккаунт отвязан. Данные на сайте сохранены. /start — привязать снова.",
                              chat_id, call.message.message_id)
        bot.answer_callback_query(call.id, "Отвязано")
        send_main_menu(bot, db, chat_id)
        return
    if data == "unlink:cancel":
        bot.edit_message_text("Оставили как было — аккаунт привязан.", chat_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    # Приложения (обе роли)
    if data.startswith("myapp:"):
        app_id = int(data.split(":")[1])
        show_application_card(bot, db, chat_id, app_id)
        bot.answer_callback_query(call.id)
        return
    if data.startswith("cancel:"):
        app_id = int(data.split(":")[1])
        cancel_application(bot, db, chat_id, app_id)
        bot.answer_callback_query(call.id, "Отменено")
        return
    if data.startswith("chat:"):
        app_id = int(data.split(":")[1])
        show_chat(bot, db, chat_id, app_id)
        bot.answer_callback_query(call.id)
        return
    if data.startswith("sendmsg:"):
        app_id = int(data.split(":")[1])
        start_chat_input(bot, db, chat_id, app_id)
        bot.answer_callback_query(call.id)
        return
    if data.startswith("review:"):
        app_id = int(data.split(":")[1])
        start_review(bot, db, chat_id, app_id)
        bot.answer_callback_query(call.id)
        return
    if data.startswith("rate:"):
        _, app_id, rating = data.split(":")
        pick_rating(bot, db, call, int(app_id), int(rating))
        bot.answer_callback_query(call.id, "Отлично!")
        return

    # Остальное делегируем модулям
    from . import handlers_admin, handlers_employer, handlers_worker
    handled = (
        handlers_worker.handle_callback(bot, db, call)
        or handlers_employer.handle_callback(bot, db, call)
        or handlers_admin.handle_callback(bot, db, call)
    )
    if not handled:
        bot.answer_callback_query(call.id, "Неизвестное действие")
    _ = answer


def register(bot: TeleBot, db: Database):
    from . import handlers_admin, handlers_employer, handlers_worker  # локально, чтобы избежать циклов при импорте

    bot.register_message_handler(lambda m: cmd_menu(bot, db, m), commands=["menu", "start"])
    bot.register_message_handler(lambda m: cmd_help(bot, db, m), commands=["help"])
    bot.register_message_handler(lambda m: cmd_faq(bot, db, m), commands=["faq"])
    bot.register_message_handler(lambda m: cmd_support(bot, db, m), commands=["support"])
    bot.register_message_handler(lambda m: cmd_web(bot, db, m), commands=["web"])
    bot.register_message_handler(lambda m: cmd_cancel(bot, db, m), commands=["cancel", "done"])
    bot.register_message_handler(lambda m: show_tariffs(bot, db, m), commands=["tariffs"])
    bot.register_message_handler(lambda m: show_profile(bot, db, m), commands=["profile", "cabinet"])
    bot.register_message_handler(lambda m: show_unlink(bot, db, m), commands=["unlink"])
    bot.register_message_handler(lambda m: show_notifications_state(bot, db, m), commands=["notifications"])

    # Кнопки-ярлыки на команды
    bot.register_message_handler(lambda m: run_action(bot, db, m, "my_applications"), commands=["applications", "responses"])
    bot.register_message_handler(lambda m: run_action(bot, db, m, "favorites"), commands=["favorites"])
    bot.register_message_handler(lambda m: run_action(bot, db, m, "my_jobs"), commands=["myjobs"])
    bot.register_message_handler(lambda m: run_action(bot, db, m, "create_job"), commands=["create"])
    bot.register_message_handler(lambda m: run_action(bot, db, m, "chats"), commands=["chats"])
    bot.register_message_handler(lambda m: handlers_worker.show_jobs_filters(bot, db, m.chat.id), commands=["jobs", "search"])
    bot.register_message_handler(lambda m: handlers_worker.show_jobs_quick(bot, db, m.chat.id, "today"), commands=["today"])
    bot.register_message_handler(lambda m: handlers_worker.show_jobs_quick(bot, db, m.chat.id, "tomorrow"), commands=["tomorrow"])

    bot.register_message_handler(lambda m: handle_text(bot, db, m), func=lambda m: True, content_types=["text"])
    bot.register_callback_query_handler(lambda c: handle_callback(bot, db, c), func=lambda c: True)
