"""Администраторская панель: обзор платформы и модерация отзывов."""

from __future__ import annotations

from telebot import TeleBot

from . import format as fmt
from .db import Database
from .handlers_common import ensure_linked


def show_overview(bot: TeleBot, db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    if not uid:
        if not ensure_linked(bot, db, chat_id):
            return
        uid = db.linked_user_id(chat_id)
    user = db.serialize_user(uid)
    if not user or user.get("role") != "admin":
        bot.send_message(chat_id, "🛡 Этот раздел доступен только модератору/администратору.")
        return
    stats = db.admin_overview()
    text = (
        "📊 <b>Обзор платформы «Подработка.МСК»</b>\n\n"
        f"👥 Пользователей: <b>{stats['total_users_count']}</b>\n"
        f"🟢 Активных смен: <b>{stats['open_jobs_count']}</b> (свободных мест: {stats['open_slots_count']})\n"
        f"💰 Средняя оплата за смену: <b>{fmt.money(stats['avg_shift_pay'])}</b>\n"
        f"✅ Верифицированных работодателей: <b>{stats['verified_employers_count']}</b>\n"
        f"📥 Откликов в ожидании: <b>{stats['pending_applications_count']}</b>\n"
        f"🛡 Отзывов на модерации: <b>{stats['pending_reviews_count']}</b>\n"
    )
    from . import keyboards as kb
    kbmark = kb.InlineKeyboardMarkup()
    kbmark.row(
        kb.InlineKeyboardButton("🛡 Модерация отзывов", callback_data="admin:moderation"),
        kb.InlineKeyboardButton("🌐 Веб-версия", callback_data="noop"),
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kbmark)


def show_moderation(bot: TeleBot, db: Database, chat_id: int):
    uid = db.linked_user_id(chat_id)
    if not uid:
        if not ensure_linked(bot, db, chat_id):
            return
        uid = db.linked_user_id(chat_id)
    user = db.serialize_user(uid)
    if not user or user.get("role") != "admin":
        bot.send_message(chat_id, "🛡 Этот раздел доступен только модератору/администратору.")
        return
    reviews = db.list_pending_reviews()
    if not reviews:
        bot.send_message(chat_id, "🛡 Очередь модерации пуста — новых отзывов нет.")
        return
    lines = ["🛡 <b>Отзывы на модерации</b>", ""]
    from . import keyboards as kb
    kbmark = kb.InlineKeyboardMarkup()
    for r in reviews[:15]:
        lines.append(
            f"• <b>Отзыв #{r['id']}</b> — {fmt.esc(r['author_name'])} → {fmt.esc(r['target_name'])}\n"
            f"  {fmt.esc(r['job_title'])} · оценка {r['rating']} ★\n"
            f"  «{fmt.esc(r.get('comment') or '')[:160]}»"
        )
        lines.append("")
        kbmark.row(
            kb.InlineKeyboardButton(f"✔ Одобрить #{r['id']}", callback_data=f"mod:{r['id']}:approved"),
            kb.InlineKeyboardButton(f"✖ Отклонить #{r['id']}", callback_data=f"mod:{r['id']}:rejected"),
        )
    bot.send_message(chat_id, "\n".join(lines)[:3900], parse_mode="HTML", reply_markup=kbmark)


def handle_callback(bot: TeleBot, db: Database, call) -> bool:
    data = call.data or ""
    chat_id = call.message.chat.id

    if data == "admin:moderation":
        show_moderation(bot, db, chat_id)
        bot.answer_callback_query(call.id)
        return True
    if data.startswith("mod:"):
        uid = db.linked_user_id(chat_id)
        user = db.serialize_user(uid) if uid else None
        if not user or user.get("role") != "admin":
            bot.answer_callback_query(call.id, "🛡 Только для модератора")
            return True
        _, review_id, decision = data.split(":")
        review_id = int(review_id)
        res = db.moderate_review(review_id, decision)
        if res.get("ok"):
            verb = "одобрен и опубликован" if decision == "approved" else "отклонён"
            bot.answer_callback_query(call.id, f"Отзыв {verb} ✅")
            show_moderation(bot, db, chat_id)
        else:
            bot.answer_callback_query(call.id, f"⚠️ {res.get('error')}")
        return True
    if data == "noop":
        bot.answer_callback_query(call.id)
        return True
    return False
