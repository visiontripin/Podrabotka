"""Сценарии работодателя: мои смены, создание смены, кандидаты, принятие/отказ/закрытие."""

from __future__ import annotations

from datetime import datetime, timedelta

from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from . import format as fmt
from . import keyboards as kb
from .constants import CATEGORIES, JOB_STATUS_LABELS, PAYOUT_TYPES
from .db import Database
from .handlers_common import ensure_linked
from .states import store
from . import states as S


# ---------- ajudaтели состояния (черновик создаваемой смены) ----------

def _save(chat_id: int, state: str, **fields):
    cur = store.get(chat_id) or {}
    cur.pop("state", None)
    cur.update(fields)
    store.set(chat_id, state, **cur)


def _draft(chat_id: int) -> dict:
    cur = store.get(chat_id) or {}
    return {k: v for k, v in cur.items() if k != "state"} or {}


def _default_draft() -> dict:
    return {
        "category": CATEGORIES[4],  # Склад
        "area_type": "moscow",
        "city": "Москва",
        "metro_station": "Автозаводская",
        "walk_minutes": 7,
        "address": "",
        "shift_date": "",
        "start_time": "09:00",
        "end_time": "18:00",
        "duration_hours": 8,
        "pay_amount": 4000,
        "payout_type": "sbp_instant",
        "slots_total": 1,
        "experience_required": False,
        "med_book_required": False,
        "smz_preferred": False,
        "meal_included": False,
        "is_urgent": False,
        "description": "",
        "requirements": [],
        "title": "",
    }


def _parse_date(text: str):
    t = (text or "").strip().lower()
    today = datetime.now().date()
    if t in ("сегодня", "today", "0"):
        return today.isoformat()
    if t in ("завтра", "tomorrow", "1"):
        return (today + timedelta(days=1)).isoformat()
    if t in ("послезавтра", "2"):
        return (today + timedelta(days=2)).isoformat()
    for f in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(t, f).date().isoformat()
        except ValueError:
            continue
    return None


def _parse_time(text: str):
    parts = (text or "").split()
    if len(parts) != 2:
        return None
    try:
        start = datetime.strptime(parts[0], "%H:%M").time()
        end = datetime.strptime(parts[1], "%H:%M").time()
    except ValueError:
        return None
    return start, end


# ---------- мои смены ----------

def show_my_jobs(bot: TeleBot, db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    if not uid:
        if not ensure_linked(bot, db, chat_id):
            return
        uid = db.linked_user_id(chat_id)
    jobs = db.list_my_jobs(uid)
    if not jobs:
        bot.send_message(
            chat_id,
            "📦 У вас пока нет смен. Создайте первую — кнопкой «➕ Создать смену».",
            reply_markup=kb.reply_keyboard("employer"),
        )
        return
    lines = ["📦 <b>Мои смены</b>", ""]
    ids = []
    for j in jobs[:20]:
        status = JOB_STATUS_LABELS.get(j.get("status"), j.get("status"))
        lines.append(
            f"• <b>{fmt.esc(j.get('title'))}</b> — {fmt.money(j.get('pay_amount'))} · "
            f"{fmt.shift_date(j.get('shift_date'))} · {fmt.esc(j.get('metro_station'))}\n"
            f"  {status} · откликов: {int(j.get('applications_count') or 0)} (ожидают: {int(j.get('pending_applications_count') or 0)})"
        )
        lines.append("")
        ids.append(j["id"])
    bot.send_message(
        chat_id,
        "\n".join(lines)[:3900],
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=kb.my_jobs_keyboard(ids),
    )


def show_my_job_card(bot: TeleBot, db: Database, chat_id: int, job_id: int, message_id: int | None = None):
    uid = db.linked_user_id(chat_id)
    if not uid:
        if not ensure_linked(bot, db, chat_id):
            return
        uid = db.linked_user_id(chat_id)
    job = db.get_job(job_id, uid)
    if not job or job.get("employer_id") != uid:
        text = "Смена не найдена или не относится к вашим."
        if message_id:
            try:
                bot.edit_message_text(text, chat_id, message_id)
            except Exception:
                bot.send_message(chat_id, text)
        else:
            bot.send_message(chat_id, text)
        return
    text = fmt.job_card(job, for_employer=True)
    if message_id:
        try:
            bot.edit_message_text(
                text, chat_id, message_id, parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=kb.my_job_card_keyboard(job),
            )
            return
        except Exception:
            pass
    bot.send_message(
        chat_id, text, parse_mode="HTML", disable_web_page_preview=True,
        reply_markup=kb.my_job_card_keyboard(job),
    )


# ---------- кандидаты ----------

def show_candidates(bot: TeleBot, db: Database, chat_id: int, job_id: int):
    uid = db.linked_user_id(chat_id)
    if not uid:
        if not ensure_linked(bot, db, chat_id):
            return
        uid = db.linked_user_id(chat_id)
    job = db.get_job(job_id, uid)
    if not job or job.get("employer_id") != uid:
        bot.send_message(chat_id, "Смена не найдена или не ваша.")
        return
    apps = [a for a in db.list_applications(uid, "employer") if a["job_id"] == job_id]
    pending = [a for a in apps if a["status"] == "pending"]
    others = [a for a in apps if a["status"] != "pending"]
    ordered = pending + others
    if not ordered:
        bot.send_message(
            chat_id,
            f"👥 По смене «{fmt.esc(job['title'])}» пока нет откликов.",
        )
        return
    header = f"👥 <b>Кандидаты на «{fmt.esc(job['title'])}»</b> ({len(ordered)})\n\n" \
             "Первые — ожидающие решения. Откройте отклика, чтобы принять или отклонить."
    ids = [a["id"] for a in ordered[:10]]
    bot.send_message(
        chat_id, header, parse_mode="HTML",
        reply_markup=kb.candidates_list_keyboard(ids),
    )


# ---------- создание смены ----------

def start_create_job(bot: TeleBot, db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    if not uid:
        if not ensure_linked(bot, db, chat_id):
            return
        uid = db.linked_user_id(chat_id)
    store.set(chat_id, S.CJ_TITLE, **_default_draft())
    bot.send_message(
        chat_id,
        "➕ <b>Создание смены</b>\n\n"
        "Шаг 1/9 — как называется смена? (например, «Грузчик на склад Wildberries»)\n"
        "Отправьте /menu — отменить.",
        parse_mode="HTML",
    )


def handle_create_state(bot: TeleBot, db: Database, msg, state: str):
    chat_id = msg.chat.id
    text = (msg.text or "").strip()

    if state == S.CJ_TITLE:
        if len(text) < 3:
            bot.send_message(chat_id, "Название слишком короткое. Придумайте имя смены.")
            return
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["title"] = text
        store.set(chat_id, S.CJ_DESC, **cur)
        bot.send_message(
            chat_id,
            "Шаг 2/9 — краткое описание смены (что нужно делать, условия). "
            "Можно оставить пустым — отправьте «-».",
        )
        return

    if state == S.CJ_DESC:
        desc = None if text in ("-", "") else text
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["description"] = desc or ""
        store.set(chat_id, S.CJ_DATE_TEXT, **cur)
        bot.send_message(
            chat_id,
            "Шаг 3/9 — дата смены. Напишите «сегодня», «завтра», «послезавтра\" "
            "или дату в формате ДД.ММ.ГГГГ (например, 25.12.2026).",
        )
        return

    if state == S.CJ_DATE_TEXT:
        iso = _parse_date(text)
        if not iso:
            bot.send_message(chat_id, "Не понял дату. Пришлите «сегодня», «завтра\" или 25.12.2026.")
            return
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["shift_date"] = iso
        store.set(chat_id, S.CJ_STATION_TEXT, **cur)
        bot.send_message(
            chat_id,
            "Шаг 4/9 — станция метро (например, «Автозаводская»). "
            "Или укажите район Московской области текстом.",
        )
        return

    if state == S.CJ_STATION_TEXT:
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["metro_station"] = text
        cur["city"] = "Москва"
        cur["area_type"] = "mo" if "область" in text.lower() else "moscow"
        store.set(chat_id, S.CJ_TIME, **cur)
        bot.send_message(
            chat_id,
            "Шаг 5/9 — время смены в формате «09:00 18:00\" (начала и конца).",
        )
        return

    if state == S.CJ_TIME:
        parsed = _parse_time(text)
        if not parsed:
            bot.send_message(chat_id, "Формат времени неверный. Пример: 09:00 18:00")
            return
        start, end = parsed
        duration = max(1, round((end.hour - start.hour) + (end.minute - start.minute) / 60, 1))
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["start_time"] = start.strftime("%H:%M")
        cur["end_time"] = end.strftime("%H:%M")
        cur["duration_hours"] = duration
        store.set(chat_id, S.CJ_PAY, **cur)
        bot.send_message(
            chat_id,
            "Шаг 6/9 — оплата за смену (рублей, цифрами). Например: 4000",
        )
        return

    if state == S.CJ_PAY:
        try:
            pay = int(float(text.replace(" ", "").replace("₽", "")))
        except ValueError:
            bot.send_message(chat_id, "Введите сумму цифрами, например 4000.")
            return
        if pay < 100:
            bot.send_message(chat_id, "Слишком мало. Введите корректную сумму.")
            return
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["pay_amount"] = pay
        store.set(chat_id, S.CJ_ADDRESS, **cur)
        bot.send_message(
            chat_id,
            "Шаг 7/9 — адрес точки/workplace (улица, дом). "
            "Можно пропустить — отправьте «-\".",
        )
        return

    if state == S.CJ_ADDRESS:
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["address"] = "" if text in ("-", "") else text
        store.set(chat_id, S.CJ_DESC, **cur)  # reuse, now jump to confirm
        _show_create_confirm(bot, chat_id)
        return

    # Неизвестное состояние — сброс
    store.clear(chat_id)
    bot.send_message(chat_id, "Создание смены отменено. Начните заново через «➕ Создать смену».")


def _show_create_confirm(bot: TeleBot, chat_id: int):
    d = _draft(chat_id) or _default_draft()
    def yes_no(flag):
        return "✅" if flag else "▫️"
    lines = [
        "➕ <b>Создание смены — проверьте перед публикацией</b>",
        "",
        f"📝 {fmt.esc(d.get('title'))}",
        f"📋 Категория: {d.get('category')} · {d.get('area_type')} · {fmt.esc(d.get('metro_station'))}",
        f"🗓 {fmt.shift_date(d.get('shift_date'))} · {d.get('start_time')}–{d.get('end_time')} ({d.get('duration_hours')} ч)",
        f"💰 {fmt.money(d.get('pay_amount'))} · {PAYOUT_TYPES.get(d.get('payout_type'), d.get('payout_type'))}",
        f"👥 Мест: {d.get('slots_total')}",
        f"Адрес: {fmt.esc(d.get('address') or '—')}",
        f"{yes_no(d.get('experience_required'))} Опыт · {yes_no(d.get('med_book_required'))} Медкнижка · "
        f"{yes_no(d.get('smz_preferred'))} СМЗ · {yes_no(d.get('meal_included'))} Питание · "
        f"{yes_no(d.get('is_urgent'))} Срочно",
    ]
    kbmark = InlineKeyboardMarkup()
    kbmark.row(
        InlineKeyboardButton("📋 Категория", callback_data="cj:choose:category"),
        InlineKeyboardButton("🏙 Район", callback_data="cj:choose:area"),
    )
    kbmark.row(
        InlineKeyboardButton("💳 Выплата", callback_data="cj:choose:payout"),
        InlineKeyboardButton("👥 Места", callback_data="cj:choose:slots"),
    )
    kbmark.row(
        InlineKeyboardButton("⚙ Требования", callback_data="cj:choose:reqs"),
        InlineKeyboardButton("🏙 Станция", callback_data="cj:choose:station"),
    )
    kbmark.row(
        InlineKeyboardButton("✅ Опубликовать смену", callback_data="cj:confirm"),
        InlineKeyboardButton("❌ Отменить", callback_data="cj:cancel"),
    )
    bot.send_message(chat_id, "\n".join(lines), parse_mode="HTML", reply_markup=kbmark)


# ---------- callbacks ----------

def handle_callback(bot: TeleBot, db: Database, call) -> bool:
    data = call.data or ""
    chat_id = call.message.chat.id

    # --- создание смены: ветка cj: --- 
    if data == "cj:choose:category":
        bot.send_message(chat_id, "Выберите категорию:", reply_markup=kb.category_keyboard())
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("cj:cat:"):
        idx = int(data.split(":")[2])
        cat = CATEGORIES[idx] if 0 <= idx < len(CATEGORIES) else None
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["category"] = cat or CATEGORIES[4]
        store.set(chat_id, S.CJ_DESC, **cur)  # state arbitrary; keep in confirm flow
        bot.answer_callback_query(call.id, f"Категория: {cat}")
        _show_create_confirm(bot, chat_id)
        return True
    if data.startswith("cj:area:"):
        area = data.split(":")[2]
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["area_type"] = area
        cur["city"] = "Московская область" if area == "mo" else "Москва"
        store.set(chat_id, S.CJ_DESC, **cur)
        bot.answer_callback_query(call.id, "Район обновлён")
        _show_create_confirm(bot, chat_id)
        return True
    if data == "cj:choose:area":
        bot.send_message(chat_id, "Выберите район:", reply_markup=kb.area_keyboard())
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("cj:station:"):
        sel = data.split(":")[2]
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        if sel == "other":
            store.set(chat_id, S.CJ_STATION_TEXT, **cur)
            bot.edit_message_text("Введите название станции или района текстом:", chat_id, call.message.message_id)
            bot.answer_callback_query(call.id)
            return True
        locations = db.list_locations()
        idx = int(sel)
        if 0 <= idx < len(locations):
            loc = locations[idx]
            cur["metro_station"] = loc["station_name"]
            cur["city"] = loc["city_name"]
            cur["area_type"] = loc["area_type"]
            store.set(chat_id, S.CJ_DESC, **cur)
            bot.answer_callback_query(call.id, f"Станция: {loc['station_name']}")
            _show_create_confirm(bot, chat_id)
            return True
        bot.answer_callback_query(call.id, "Станция не найдена")
        return True
    if data == "cj:choose:station":
        locations = db.list_locations()
        area = (_draft(chat_id) or {}).get("area_type", "moscow")
        bot.send_message(chat_id, "Выберите станцию метро:", reply_markup=kb.stations_keyboard(locations, area))
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("cj:date:"):
        sel = data.split(":")[2]
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        if sel == "other":
            store.set(chat_id, S.CJ_DATE_TEXT, **cur)
            bot.edit_message_text("Введите дату в формате ДД.ММ.ГГГГ:", chat_id, call.message.message_id)
            bot.answer_callback_query(call.id)
            return True
        today = datetime.now().date()
        offset = int(sel)
        cur["shift_date"] = (today + timedelta(days=offset)).isoformat()
        store.set(chat_id, S.CJ_DESC, **cur)
        bot.answer_callback_query(call.id, "Дата обновлена")
        _show_create_confirm(bot, chat_id)
        return True
    if data == "cj:choose:date":
        bot.send_message(chat_id, "Выберите дату:", reply_markup=kb.date_choice_keyboard())
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("cj:payout:"):
        payout = data.split(":")[2]
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["payout_type"] = payout
        store.set(chat_id, S.CJ_DESC, **cur)
        bot.answer_callback_query(call.id, PAYOUT_TYPES.get(payout, payout))
        _show_create_confirm(bot, chat_id)
        return True
    if data == "cj:choose:payout":
        bot.send_message(chat_id, "Способ выплаты:", reply_markup=kb.payout_keyboard())
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("cj:slots:"):
        slots = int(data.split(":")[2])
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur["slots_total"] = slots
        store.set(chat_id, S.CJ_DESC, **cur)
        bot.answer_callback_query(call.id, f"Мест: {slots}")
        _show_create_confirm(bot, chat_id)
        return True
    if data == "cj:choose:slots":
        bot.send_message(chat_id, "Сколько мест в бригаде:", reply_markup=kb.slots_keyboard())
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("cj:req:"):
        field = data.split(":")[2]
        if field == "done":
            _show_create_confirm(bot, chat_id)
            bot.answer_callback_query(call.id)
            return True
        cur = store.get(chat_id) or {}
        cur.pop("state", None)
        cur[field] = not cur.get(field, False)
        store.set(chat_id, S.CJ_DESC, **cur)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=kb.requirements_keyboard(cur))
        bot.answer_callback_query(call.id)
        return True
    if data == "cj:choose:reqs":
        bot.send_message(chat_id, "Требования к исполнителю:", reply_markup=kb.requirements_keyboard(_draft(chat_id)))
        bot.answer_callback_query(call.id)
        return True
    if data == "cj:confirm":
        return _create_job(bot, db, chat_id, call)
    if data == "cj:cancel":
        store.clear(chat_id)
        bot.edit_message_text("Создание смены отменено.", chat_id, call.message.message_id)
        bot.answer_callback_query(call.id, "Отменено")
        return True

    # --- управление сменой работодателя ---
    if data.startswith("myjob:"):
        job_id = int(data.split(":")[1])
        show_my_job_card(bot, db, chat_id, job_id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("pausejob:"):
        job_id = int(data.split(":")[1])
        ok, err = db.set_job_status(job_id, db.linked_user_id(chat_id), "paused")
        bot.answer_callback_query(call.id, "Набор приостановлен ⏸" if ok else f"⚠️ {err}")
        show_my_job_card(bot, db, chat_id, job_id, call.message.message_id)
        return True
    if data.startswith("resumejob:"):
        job_id = int(data.split(":")[1])
        ok, err = db.set_job_status(job_id, db.linked_user_id(chat_id), "active")
        bot.answer_callback_query(call.id, "Набор возобновлён ▶️" if ok else f"⚠️ {err}")
        show_my_job_card(bot, db, chat_id, job_id, call.message.message_id)
        return True
    if data.startswith("clone:"):
        job_id = int(data.split(":")[1])
        uid = db.linked_user_id(chat_id)
        new_id, err = db.clone_job(uid, job_id)
        bot.answer_callback_query(call.id, f"Склонено → смена #{new_id}" if new_id else f"⚠️ {err}")
        if new_id:
            show_my_job_card(bot, db, chat_id, new_id)
        return True
    if data.startswith("closejob:"):
        job_id = int(data.split(":")[1])
        ok, err = db.set_job_status(job_id, db.linked_user_id(chat_id), "closed")
        bot.answer_callback_query(call.id, "Смена закрыта ⛔" if ok else f"⚠️ {err}")
        show_my_job_card(bot, db, chat_id, job_id, call.message.message_id)
        return True
    if data.startswith("candidates:"):
        job_id = int(data.split(":")[1])
        show_candidates(bot, db, chat_id, job_id)
        bot.answer_callback_query(call.id)
        return True

    # --- решения по кандидатам (откликам) ---
    if data.startswith("accept:"):
        app_id = int(data.split(":")[1])
        res = db.set_application_status(app_id, db.linked_user_id(chat_id), "accepted")
        bot.answer_callback_query(call.id, "Принято ✅" if res.get("ok") else f"⚠️ {res.get('error')}")
        from .handlers_common import show_application_card
        show_application_card(bot, db, chat_id, app_id)
        return True
    if data.startswith("reject:"):
        app_id = int(data.split(":")[1])
        res = db.set_application_status(app_id, db.linked_user_id(chat_id), "rejected")
        bot.answer_callback_query(call.id, "Отклонено ❌" if res.get("ok") else f"⚠️ {res.get('error')}")
        from .handlers_common import show_application_card
        show_application_card(bot, db, chat_id, app_id)
        return True
    if data.startswith("complete:"):
        app_id = int(data.split(":")[1])
        res = db.set_application_status(app_id, db.linked_user_id(chat_id), "completed")
        bot.answer_callback_query(call.id, "Смена завершена 🏁" if res.get("ok") else f"⚠️ {res.get('error')}")
        from .handlers_common import show_application_card
        show_application_card(bot, db, chat_id, app_id)
        return True

    return False


def _create_job(bot: TeleBot, db: Database, chat_id: int, call) -> bool:
    uid = db.linked_user_id(chat_id)
    if not uid:
        bot.answer_callback_query(call.id, "Сначала привяжите аккаунт")
        return True
    d = _draft(chat_id) or _default_draft()
    data = {
        "title": d.get("title", "").strip() or "Смена",
        "category": d.get("category", CATEGORIES[4]),
        "metro_station": d.get("metro_station", "Автозаводская"),
        "city": d.get("city", "Москва"),
        "area_type": d.get("area_type", "moscow"),
        "address": d.get("address", ""),
        "walk_minutes": int(d.get("walk_minutes") or 7),
        "shift_date": d.get("shift_date") or datetime.now().date().isoformat(),
        "start_time": d.get("start_time", "09:00"),
        "end_time": d.get("end_time", "18:00"),
        "duration_hours": float(d.get("duration_hours") or 8),
        "pay_amount": int(d.get("pay_amount") or 4000),
        "payout_type": d.get("payout_type", "sbp_instant"),
        "slots_total": int(d.get("slots_total") or 1),
        "experience_required": bool(d.get("experience_required")),
        "med_book_required": bool(d.get("med_book_required")),
        "smz_preferred": bool(d.get("smz_preferred")),
        "meal_included": bool(d.get("meal_included")),
        "is_urgent": bool(d.get("is_urgent")),
        "description": d.get("description", ""),
        "requirements": d.get("requirements") or [],
    }
    job_id, err = db.create_job(uid, data)
    store.clear(chat_id)
    if err:
        bot.edit_message_text(f"⚠️ Не удалось создать смену: {err}", chat_id, call.message.message_id)
        bot.answer_callback_query(call.id, "Ошибка")
        return True
    bot.edit_message_text(
        f"✅ Смена #{job_id} опубликована! Она появилась в каталоге и в «Мои смены».",
        chat_id, call.message.message_id,
    )
    bot.answer_callback_query(call.id, "Опубликовано ✅")
    show_my_jobs(bot, db, chat_id)
    return True
