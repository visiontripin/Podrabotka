"""Сценарии исполнителя: каталог смен, отклик, избранное."""

import math

from telebot import TeleBot

from . import format as fmt
from . import keyboards as kb
from .config import JOBS_PAGE_SIZE
from .db import Database
from .states import store
from . import states as S
from .constants import CATEGORIES

# Быстрые фильтры каталога по чату (in-memory, не критично терять при перезапуске)
_filters: dict[int, dict] = {}


def get_filter(chat_id: int) -> dict:
    return _filters.get(chat_id, {})


def set_filter(chat_id: int, **kwargs):
    cur = _filters.get(chat_id, {})
    cur.update(kwargs)
    _filters[chat_id] = cur
    return cur


def show_jobs_filters(bot: TeleBot, db: Database, chat_id: int):
    f = get_filter(chat_id)
    bot.send_message(
        chat_id,
        "🎛 <b>Фильтры каталога</b>\n\n"
        "Выберите категорию, район и дату — и нажмите «🔍 Показать результаты».\n"
        "Точный поиск по названию — на сайте кнопкой «🌐 Веб-версия».",
        parse_mode="HTML",
        reply_markup=kb.jobs_filter_keyboard(f.get("category"), f.get("area_type"), f.get("date_preset")),
    )


def show_jobs_quick(bot: TeleBot, db: Database, chat_id: int, date_preset: str):
    set_filter(chat_id, date_preset=date_preset)
    send_jobs_page(bot, db, chat_id, 1)


def send_jobs_page(bot: TeleBot, db: Database, chat_id: int, page: int):
    uid = db.linked_user_id(chat_id) or 0  # 0 — анонимная подборка, избранное не отметится
    f = get_filter(chat_id)
    jobs, total, pages, page = db.list_jobs(
        uid,
        category=f.get("category"),
        area_type=f.get("area_type"),
        date_preset=f.get("date_preset"),
        page=page,
        page_size=JOBS_PAGE_SIZE,
    )
    active = []
    if f.get("category"):
        active.append(f.get("category"))
    if f.get("area_type") and f.get("area_type") != "all":
        active.append("Москва" if f["area_type"] == "moscow" else "МО")
    if f.get("date_preset") and f.get("date_preset") != "all":
        active.append({"today": "сегодня", "tomorrow": "завтра"}.get(f["date_preset"], ""))
    header = "🔍 <b>Смены" + (f" · {' · '.join(a for a in active if a)}" if active else "") + f"</b> ({total})"
    if not jobs:
        bot.send_message(
            chat_id,
            header + "\n\nПо этим фильтрам ничего нет. Сбросьте фильтры или посмотрите завтрашние смены.",
            parse_mode="HTML",
            reply_markup=kb.jobs_filter_keyboard(f.get("category"), f.get("area_type"), f.get("date_preset")),
        )
        return
    lines = [header, ""]
    for j in jobs:
        lines.append(fmt.job_brief(j))
        lines.append("")
    bot.send_message(
        chat_id,
        "\n".join(lines)[:3900],
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=kb.jobs_list_keyboard([j["id"] for j in jobs], page, pages),
    )


def show_job_card(bot: TeleBot, db: Database, chat_id: int, job_id: int, message_id: int | None = None):
    uid = db.linked_user_id(chat_id) or 0
    job = db.get_job(job_id, uid)
    if not job:
        text = "Смена не найдена или снята с публикации."
        if message_id:
            bot.edit_message_text(text, chat_id, message_id)
        else:
            bot.send_message(chat_id, text)
        return
    text = fmt.job_card(job)
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML",
                                  disable_web_page_preview=True,
                                  reply_markup=kb.job_card_keyboard(job))
            return
        except Exception:
            pass  # «message is not modified» — отправим новым сообщением
    bot.send_message(chat_id, text, parse_mode="HTML", disable_web_page_preview=True,
                     reply_markup=kb.job_card_keyboard(job))


def show_favorites(bot: TeleBot, db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    if not uid:
        from .handlers_common import ensure_linked
        if not ensure_linked(bot, db, chat_id):
            return
        uid = db.linked_user_id(chat_id)
    jobs = db.list_favorites(uid)
    if not jobs:
        bot.send_message(
            chat_id,
            "⭐ В избранном пусто.\n\nОткройте карточку смены и нажмите «🤍 В избранное» — сохранённые смены появятся здесь.",
        )
        return
    lines = ["⭐ <b>Избранное</b>", ""]
    ids = []
    for j in jobs[:10]:
        lines.append(fmt.job_brief(j))
        lines.append("")
        ids.append(j["id"])
    bot.send_message(
        chat_id,
        "\n".join(lines)[:3900],
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=kb.jobs_list_keyboard(ids, 1, 1),
    )


def start_apply(bot: TeleBot, db: Database, chat_id: int, job_id: int):
    from .handlers_common import ensure_linked
    uid = ensure_linked(bot, db, chat_id)
    if not uid:
        return
    job = db.get_job(job_id, uid)
    if not job:
        bot.send_message(chat_id, "Смена не найдена.")
        return
    store.set(chat_id, S.APPLY_COVER, job_id=job_id)
    bot.send_message(
        chat_id,
        f"✋ Отклик на «<b>{fmt.esc(job['title'])}</b>»\n\n"
        "Добавьте короткую записку работодателю (опыт, когда сможете выйти).\n"
        "Или отправьте /skip — уйдёт стандартное «Готов выйти на смену без опозданий, на связи!».",
        parse_mode="HTML",
    )


def toggle_favorite(bot: TeleBot, db: Database, call, job_id: int):
    from .handlers_common import ensure_linked
    uid = ensure_linked(bot, db, call.message.chat.id)
    if not uid:
        bot.answer_callback_query(call.id, "Сначала привяжите аккаунт")
        return
    is_fav = db.toggle_favorite(uid, job_id)
    bot.answer_callback_query(call.id, "Добавлено в избранное ⭐" if is_fav else "Убрано из избранного")
    # Обновим карточку, чтобы кнопка переключилась
    show_job_card(bot, db, call.message.chat.id, job_id, call.message.message_id)


def handle_callback(bot: TeleBot, db: Database, call) -> bool:
    data = call.data or ""
    chat_id = call.message.chat.id

    if data == "jobs:filters":
        show_jobs_filters(bot, db, chat_id)
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("jobs:cat:"):
        idx = int(data.split(":")[2])
        cat = CATEGORIES[idx] if 0 <= idx < len(CATEGORIES) else None
        cur = get_filter(chat_id)
        # Повторное нажатие снимает категорию
        set_filter(chat_id, category=None if cur.get("category") == cat else cat)
        show_jobs_filters(bot, db, chat_id)
        bot.answer_callback_query(call.id, f"Категория: {cat or 'все'}")
        return True
    if data.startswith("jobs:area:"):
        area = data.split(":")[2]
        set_filter(chat_id, area_type=None if area == "all" else area)
        show_jobs_filters(bot, db, chat_id)
        bot.answer_callback_query(call.id, "Район обновлён")
        return True
    if data.startswith("jobs:date:"):
        date = data.split(":")[2]
        set_filter(chat_id, date_preset=None if date == "all" else date)
        show_jobs_filters(bot, db, chat_id)
        bot.answer_callback_query(call.id, "Дата обновлена")
        return True
    if data == "jobs:reset":
        _filters.pop(chat_id, None)
        show_jobs_filters(bot, db, chat_id)
        bot.answer_callback_query(call.id, "Фильтры сброшены")
        return True
    if data.startswith("jobs:page:"):
        page = int(data.split(":")[2])
        send_jobs_page(bot, db, chat_id, page)
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("job:"):
        job_id = int(data.split(":")[1])
        show_job_card(bot, db, chat_id, job_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("fav:"):
        job_id = int(data.split(":")[1])
        toggle_favorite(bot, db, call, job_id)
        return True
    if data.startswith("apply:"):
        job_id = int(data.split(":")[1])
        start_apply(bot, db, chat_id, job_id)
        bot.answer_callback_query(call.id)
        return True
    if data == "favorites":
        show_favorites(bot, db, chat_id)
        bot.answer_callback_query(call.id)
        return True
    return False
