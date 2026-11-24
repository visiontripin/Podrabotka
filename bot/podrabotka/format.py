"""Форматирование сообщений Telegram (parse_mode=HTML)."""

import html
from datetime import datetime

from .constants import (
    APP_STATUS_LABELS,
    CATEGORY_EMOJI,
    JOB_STATUS_LABELS,
    PAYOUT_EMOJI,
    PAYOUT_TYPES,
)


def esc(text) -> str:
    return html.escape(str(text or ""))


def money(amount) -> str:
    try:
        return f"{int(round(float(amount))):,}".replace(",", " ") + " ₽"
    except (TypeError, ValueError):
        return f"{amount} ₽"


def shift_date(iso_date: str) -> str:
    """«Сегодня, 24 ноя» / «Завтра, 25 ноя» / «вт, 26 ноя»."""
    try:
        d = datetime.strptime(iso_date, "%Y-%m-%d")
    except Exception:
        return esc(iso_date)
    today = datetime.now().date()
    delta = (d.date() - today).days
    day_mon = d.strftime("%d %b").lower()
    if delta == 0:
        return f"Сегодня, {day_mon}"
    if delta == 1:
        return f"Завтра, {day_mon}"
    weekdays = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    return f"{weekdays[d.weekday()]}, {day_mon}"


def payout_label(payout_type: str) -> str:
    emoji = PAYOUT_EMOJI.get(payout_type, "💳")
    return f"{emoji} {PAYOUT_TYPES.get(payout_type, 'Прямая выплата')}"


def _yes_no(flag) -> str:
    return "да" if flag else "нет"


def job_card(j: dict, *, for_employer: bool = False) -> str:
    """Полная карточка смены."""
    cat = j.get("category", "")
    cat_emoji = CATEGORY_EMOJI.get(cat, "📋")
    badges = []
    if j.get("is_urgent"):
        badges.append("🔥 Срочно")
    if j.get("is_promoted"):
        badges.append("⭐ Топ-смена")
    if not j.get("experience_required"):
        badges.append("✨ Без опыта")
    if j.get("meal_included"):
        badges.append("🍽 Питание")
    badges_line = " · ".join(badges)

    hourly = int(round((j.get("pay_amount") or 0) / max(1, j.get("duration_hours") or 1)))
    slots_total = j.get("slots_total") or 0
    slots_filled = j.get("slots_filled") or 0
    slots_free = max(0, slots_total - slots_filled)

    parts = [
        f"{cat_emoji} <b>{esc(j.get('title'))}</b>",
    ]
    if badges_line:
        parts.append(badges_line)
    parts.append("")
    parts.append(
        f"💰 <b>{money(j.get('pay_amount'))}</b> / смена · ~{hourly} ₽/час"
    )
    parts.append(f"{payout_label(j.get('payout_type'))}")
    parts.append("")
    parts.append(f"📍 <b>{esc(j.get('metro_station'))}</b> · {int(j.get('walk_minutes') or 0)} мин пешком")
    if j.get("city") and j.get("area_type") == "mo":
        parts.append(f"🏙 {esc(j.get('city'))} (Московская область)")
    parts.append(f"🏠 {esc(j.get('address'))}")
    parts.append("")
    parts.append(
        f"🗓 {shift_date(j.get('shift_date'))}, {esc(j.get('start_time'))}–{esc(j.get('end_time'))} "
        f"({j.get('duration_hours')} ч)"
    )
    parts.append(f"👥 Мест: {slots_filled} из {slots_total}{f' · свободно {slots_free}' if slots_free else ' · набор закрыт'}")
    parts.append("")
    reqs = [
        f"Опыт: {_yes_no(j.get('experience_required'))}",
        f"Медкнижка: {_yes_no(j.get('med_book_required'))}",
        f"СМЗ приветствуется: {_yes_no(j.get('smz_preferred'))}",
    ]
    parts.append("📋 " + " · ".join(reqs))

    employer_name = j.get("employer_company") or j.get("employer_name") or "Работодатель"
    verified = " ✅" if j.get("employer_verified") else ""
    parts.append(
        f"🏢 {esc(employer_name)}{verified} · ★ {j.get('employer_rating', 0)} "
        f"({int(j.get('employer_reviews_count') or 0)} отзывов)"
    )

    desc = (j.get("description") or "").strip()
    if desc:
        parts.append("")
        parts.append(f"📝 {esc(desc[:500])}{'…' if len(desc) > 500 else ''}")

    if for_employer:
        parts.append("")
        parts.append(JOB_STATUS_LABELS.get(j.get("status"), j.get("status", "")))
        parts.append(f"📥 Откликов: {int(j.get('applications_count') or 0)} (ожидают: {int(j.get('pending_applications_count') or 0)})")

    return "\n".join(parts)


def job_brief(j: dict) -> str:
    cat = CATEGORY_EMOJI.get(j.get("category", ""), "📋")
    urgent = " 🔥" if j.get("is_urgent") else ""
    return (
        f"{cat} <b>{esc(j.get('title'))}</b>{urgent}\n"
        f"💰 {money(j.get('pay_amount'))} · {shift_date(j.get('shift_date'))} · {esc(j.get('metro_station'))}"
    )


def application_line(a: dict, *, perspective: str) -> str:
    status = APP_STATUS_LABELS.get(a.get("status"), a.get("status"))
    if perspective == "worker":
        other = a.get("employer_company") or a.get("employer_name") or "Работодатель"
    else:
        other = a.get("worker_name") or "Исполнитель"
    return (
        f"{status} — <b>{esc(a.get('job_title'))}</b>\n"
        f"🗓 {shift_date(a.get('job_date'))}, {esc(a.get('job_start_time'))}–{esc(a.get('job_end_time'))} · 💰 {money(a.get('job_pay_amount'))}\n"
        f"{'🏢 Кому' if perspective == 'worker' else '👷 От кого'}: {esc(other)}"
    )


def application_detail_employer(a: dict) -> str:
    skills = ", ".join(a.get("worker_skills") or []) or "не указаны"
    med = "есть" if a.get("worker_has_med_book") else "нет"
    smz = "есть" if a.get("worker_is_self_employed") else "нет"
    pro = " (PRO)" if a.get("worker_tariff_slug") == "worker_pro" else ""
    parts = [
        f"👷 <b>{esc(a.get('worker_name'))}</b>{pro}",
        f"★ {a.get('worker_rating', 0)} ({int(a.get('worker_reviews_count') or 0)} отзывов) · Индекс выходов: {a.get('worker_show_up_rate', 100)}% · Закрытых смен: {a.get('worker_shifts_completed', 0)}",
        f"📍 {esc(a.get('worker_metro') or '—')} · Навыки: {esc(skills)}",
        f"Медкнижка: {med} · Самозанятость: {smz}",
    ]
    phone = a.get("worker_phone") or ""
    if phone and a.get("status") == "accepted":
        parts.append(f"📞 Телефон: {esc(phone)}")
    note = (a.get("cover_note") or "").strip()
    if note:
        parts.append(f"\n📝 Записка: «{esc(note)}»")
    return "\n".join(parts)


def chat_history_text(messages: list[dict], my_user_id: int) -> str:
    if not messages:
        return "<i>Пока пусто. Напишите первое сообщение!</i>"
    lines = []
    for m in messages:
        who = "Вы" if m["sender_id"] == my_user_id else esc(m.get("sender_name") or "Участник")
        when = str(m.get("created_at") or "")[5:16]
        lines.append(f"<b>{who}</b> <i>{when}</i>\n{esc(m.get('body'))}")
    return "\n\n".join(lines)


def profile_text(u: dict) -> str:
    skills = ", ".join(u.get("skills") or []) or "не указаны"
    role = {"worker": "👷 Исполнитель", "employer": "🏢 Работодатель", "admin": "🛡 Модератор"}.get(u.get("role"), u.get("role"))
    verified = " ✅" if u.get("is_verified") else ""
    parts = [
        f"👤 <b>{esc(u.get('name'))}</b>{verified}",
        f"{role} · {esc(u.get('email'))}",
        f"📍 {esc(u.get('city'))}, {esc(u.get('metro_station'))}" if u.get("metro_station") else f"📍 {esc(u.get('city'))}",
    ]
    company = u.get("company_name") or ""
    if company:
        parts.append(f"🏢 {esc(company)}")
    parts.append("")
    parts.append(f"⭐ Рейтинг: <b>{u.get('rating_avg', 0)}</b> ({u.get('reviews_count', 0)} отзывов)")
    parts.append(f"🏁 Закрытых смен: {u.get('shifts_completed', 0)} · Индекс выходов: {u.get('show_up_rate', 100)}%")
    if u.get("role") == "worker":
        parts.append(f"💰 Заработано всего: <b>{money(u.get('earned_total', 0))}</b>")
        parts.append(f"Медкнижка: {_yes_no(u.get('has_med_book'))} · СМЗ: {_yes_no(u.get('is_self_employed'))} · Ночные смены: {_yes_no(u.get('night_shifts_ok'))}")
        parts.append(f"Навыки: {esc(skills)}")
        parts.append(f"Откликов сегодня: {u.get('today_applications_used', 0)}/{u.get('tariff_limit') if u.get('tariff_limit') is not None else '∞'}")
    else:
        parts.append(f"Активных смен: {u.get('active_jobs_used', 0)}/{u.get('tariff_limit') if u.get('tariff_limit') is not None else '∞'}")
    tariff_line = f"💼 Тариф: <b>{esc(u.get('tariff_title'))}</b>"
    parts.append(tariff_line)
    return "\n".join(parts)


def tariffs_text(tariffs: list[dict], current_slug: str | None = None) -> str:
    parts = ["💰 <b>Тарифы «Подработка.МСК»</b>", ""]
    worker = [t for t in tariffs if t["target_role"] == "worker"]
    employer = [t for t in tariffs if t["target_role"] == "employer"]
    parts.append("<b>👷 Исполнителю</b>")
    for t in worker:
        mark = " ✅ (ваш)" if current_slug == t["slug"] else ""
        limit = f"до {t['limit_value']} откликов/день" if t["limit_value"] else "безлимит откликов"
        parts.append(f"• <b>{esc(t['title'])}</b> — {t['price_rub']} ₽/мес · {limit}{mark}")
    parts.append("")
    parts.append("<b>🏢 Работодателю</b>")
    for t in employer:
        mark = " ✅ (ваш)" if current_slug == t["slug"] else ""
        limit = f"до {t['limit_value']} активных смен" if t["limit_value"] else "без лимита"
        parts.append(f"• <b>{esc(t['title'])}</b> — {t['price_rub']} ₽/мес · {limit}{mark}")
    parts.append("")
    parts.append("Тариф меняется в веб-версии (раздел «Профиль» → тариф).")
    return "\n".join(parts)
