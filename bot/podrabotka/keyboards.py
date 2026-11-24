"""Reply и Inline клавиатуры."""

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from .config import WEB_URL
from .constants import CATEGORIES, CATEGORY_EMOJI, PAYOUT_TYPES

BTN_JOBS = "🔍 Найти смену"
BTN_TODAY = "📅 Сегодня"
BTN_TOMORROW = "📅 Завтра"
BTN_FAVORITES = "⭐ Избранное"
BTN_APPLICATIONS = "📝 Мои отклики"
BTN_MY_JOBS = "📦 Мои смены"
BTN_CREATE_JOB = "➕ Создать смену"
BTN_CANDIDATES = "👥 Кандидаты"
BTN_CHATS = "💬 Чаты"
BTN_CABINET = "👤 Кабинет"
BTN_PROFILE = "👤 Профиль"
BTN_TARIFFS = "💰 Тарифы"
BTN_HELP = "❓ Помощь"
BTN_OVERVIEW = "📊 Обзор"
BTN_MODERATION = "🛡 Модерация"


def reply_keyboard(role: str | None) -> ReplyKeyboardMarkup:
    """Главное меню под полем ввода по роли пользователя."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True, is_persistent=True)
    if role == "employer":
        kb.row(KeyboardButton(BTN_MY_JOBS), KeyboardButton(BTN_CREATE_JOB))
        kb.row(KeyboardButton(BTN_CANDIDATES), KeyboardButton(BTN_CHATS))
        kb.row(KeyboardButton(BTN_CABINET), KeyboardButton(BTN_TARIFFS))
        kb.row(KeyboardButton(BTN_PROFILE), KeyboardButton(BTN_HELP))
    elif role == "admin":
        kb.row(KeyboardButton(BTN_OVERVIEW), KeyboardButton(BTN_MODERATION))
        kb.row(KeyboardButton(BTN_CABINET), KeyboardButton(BTN_HELP))
    elif role == "worker":
        kb.row(KeyboardButton(BTN_JOBS), KeyboardButton(BTN_TODAY), KeyboardButton(BTN_TOMORROW))
        kb.row(KeyboardButton(BTN_FAVORITES), KeyboardButton(BTN_APPLICATIONS))
        kb.row(KeyboardButton(BTN_CHATS), KeyboardButton(BTN_CABINET))
        kb.row(KeyboardButton(BTN_PROFILE), KeyboardButton(BTN_TARIFFS), KeyboardButton(BTN_HELP))
    else:
        # Не привязан
        kb.row(KeyboardButton("🔗 Привязать аккаунт"), KeyboardButton("📝 Регистрация"))
        kb.row(KeyboardButton(BTN_JOBS), KeyboardButton(BTN_TARIFFS), KeyboardButton(BTN_HELP))
    return kb


def link_prompt_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("🔗 Привязать существующий аккаунт", callback_data="link:start"),
    )
    kb.row(
        InlineKeyboardButton("📝 Создать аккаунт в боте", callback_data="register:start"),
    )
    kb.row(
        InlineKeyboardButton("🌐 Сначала посмотреть сайт", url=WEB_URL),
    )
    return kb


def jobs_filter_keyboard(active_category: str | None, active_area: str | None, active_date: str | None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    # Категории — сетка 2×4
    for i in range(0, len(CATEGORIES), 2):
        row = []
        for j in range(i, min(i + 2, len(CATEGORIES))):
            cat = CATEGORIES[j]
            mark = "• " if active_category == cat else ""
            row.append(InlineKeyboardButton(f"{mark}{CATEGORY_EMOJI.get(cat, '')} {cat}", callback_data=f"jobs:cat:{j}"))
        kb.row(*row)
    kb.row(
        InlineKeyboardButton(f"{'• ' if active_area in (None, 'all') else ''}Все районы", callback_data="jobs:area:all"),
        InlineKeyboardButton(f"{'• ' if active_area == 'moscow' else ''}Москва", callback_data="jobs:area:moscow"),
        InlineKeyboardButton(f"{'• ' if active_area == 'mo' else ''}МО", callback_data="jobs:area:mo"),
    )
    kb.row(
        InlineKeyboardButton(f"{'• ' if active_date in (None, 'all') else ''}Все даты", callback_data="jobs:date:all"),
        InlineKeyboardButton(f"{'• ' if active_date == 'today' else ''}Сегодня", callback_data="jobs:date:today"),
        InlineKeyboardButton(f"{'• ' if active_date == 'tomorrow' else ''}Завтра", callback_data="jobs:date:tomorrow"),
    )
    if active_category or (active_area not in (None, "all")) or (active_date not in (None, "all")):
        kb.row(InlineKeyboardButton("🔄 Сбросить фильтры", callback_data="jobs:reset"))
    kb.row(InlineKeyboardButton("🔍 Показать результаты", callback_data="jobs:page:1"))
    return kb


def jobs_list_keyboard(job_ids, page: int, pages: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for jid in job_ids:
        kb.row(InlineKeyboardButton(f"👉 Открыть смену #{jid}", callback_data=f"job:{jid}"))
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton("◀ Назад", callback_data=f"jobs:page:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page}/{pages}", callback_data="noop"))
    if page < pages:
        nav.append(InlineKeyboardButton("Вперёд ▶", callback_data=f"jobs:page:{page + 1}"))
    kb.row(*nav)
    kb.row(InlineKeyboardButton("🎛 Фильтры", callback_data="jobs:filters"),
           InlineKeyboardButton("🌐 Веб-версия", url=WEB_URL))
    return kb


def job_card_keyboard(job: dict) -> InlineKeyboardMarkup:
    jid = job["id"]
    kb = InlineKeyboardMarkup()
    my_status = job.get("my_application_status")
    if my_status:
        label = {
            "pending": "⏳ Вы откликнулись — открыть отклик",
            "accepted": "✅ Вы приняты — открыть отклик",
            "completed": "🏁 Смена завершена — открыть отклик",
            "rejected": "⛔ Отказ / бригада набрана",
            "cancelled": "🚫 Вы отменили — откликнуться снова",
        }.get(my_status, "Вы откликнулись")
        kb.row(InlineKeyboardButton(label, callback_data=f"myapp:{job['my_application_id']}"))
    else:
        kb.row(InlineKeyboardButton("✋ Откликнуться на смену", callback_data=f"apply:{jid}"))
    fav = "💚 В избранном" if job.get("is_favorite") else "🤍 В избранное"
    kb.row(
        InlineKeyboardButton(fav, callback_data=f"fav:{jid}"),
        InlineKeyboardButton("◀ К списку", callback_data="jobs:page:1"),
    )
    kb.row(InlineKeyboardButton("🌐 Открыть в веб-версии", url=WEB_URL))
    return kb


def application_card_keyboard(a: dict, perspective: str) -> InlineKeyboardMarkup:
    aid = a["id"]
    kb = InlineKeyboardMarkup()
    if perspective == "worker":
        if a["status"] in ("pending", "accepted"):
            kb.row(InlineKeyboardButton("🚫 Отменить отклик", callback_data=f"cancel:{aid}"))
        if a["status"] != "cancelled":
            kb.row(InlineKeyboardButton("💬 Чат с работодателем", callback_data=f"chat:{aid}"))
        if a["status"] == "completed" and not a.get("has_my_review"):
            kb.row(InlineKeyboardButton("⭐ Оценить работодателя", callback_data=f"review:{aid}"))
    else:
        if a["status"] == "pending":
            kb.row(
                InlineKeyboardButton("✅ Принять", callback_data=f"accept:{aid}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"reject:{aid}"),
            )
        if a["status"] == "accepted":
            kb.row(InlineKeyboardButton("🏁 Завершить смену и выплатить", callback_data=f"complete:{aid}"))
        if a["status"] != "cancelled":
            kb.row(InlineKeyboardButton("💬 Чат с исполнителем", callback_data=f"chat:{aid}"))
        if a["status"] == "completed" and not a.get("has_my_review"):
            kb.row(InlineKeyboardButton("⭐ Оценить исполнителя", callback_data=f"review:{aid}"))
    kb.row(InlineKeyboardButton("🌐 Веб-версия", url=WEB_URL))
    return kb


def applications_list_keyboard(app_ids, prefix="app") -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for aid in app_ids:
        kb.row(InlineKeyboardButton(f"Отклик #{aid}", callback_data=f"myapp:{aid}"))
    return kb


def my_jobs_keyboard(job_ids) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for jid in job_ids:
        kb.row(InlineKeyboardButton(f"Смена #{jid}", callback_data=f"myjob:{jid}"))
    return kb


def my_job_card_keyboard(j: dict) -> InlineKeyboardMarkup:
    jid = j["id"]
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton(
            f"👥 Кандидаты ({int(j.get('applications_count') or 0)})",
            callback_data=f"candidates:{jid}",
        )
    )
    if j.get("status") == "active":
        kb.row(InlineKeyboardButton("⏸ Приостановить набор", callback_data=f"pausejob:{jid}"))
    elif j.get("status") == "paused":
        kb.row(InlineKeyboardButton("▶️ Возобновить набор", callback_data=f"resumejob:{jid}"))
    kb.row(
        InlineKeyboardButton("📋 Клонировать на завтра", callback_data=f"clone:{jid}"),
        InlineKeyboardButton("⛔ Закрыть смену", callback_data=f"closejob:{jid}"),
    )
    kb.row(InlineKeyboardButton("🌐 Веб-версия", url=WEB_URL))
    return kb


def candidates_list_keyboard(app_ids) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for aid in app_ids:
        kb.row(InlineKeyboardButton(f"👷 Отклик #{aid} — открыть", callback_data=f"myapp:{aid}"))
    return kb


def chat_actions_keyboard(app_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✍️ Написать сообщение", callback_data=f"sendmsg:{app_id}"),
        InlineKeyboardButton("🔄 Обновить", callback_data=f"chat:{app_id}"),
    )
    kb.row(InlineKeyboardButton("🌐 Веб-версия", url=WEB_URL))
    return kb


def confirm_unlink_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Да, отвязать", callback_data="unlink:confirm"),
        InlineKeyboardButton("Отмена", callback_data="unlink:cancel"),
    )
    return kb


def moderation_keyboard(review_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("✔ Одобрить и опубликовать", callback_data=f"mod:{review_id}:approved"),
        InlineKeyboardButton("✖ Отклонить", callback_data=f"mod:{review_id}:rejected"),
    )
    return kb


def category_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    for i in range(0, len(CATEGORIES), 2):
        row = []
        for j in range(i, min(i + 2, len(CATEGORIES))):
            row.append(InlineKeyboardButton(f"{CATEGORY_EMOJI.get(CATEGORIES[j], '')} {CATEGORIES[j]}",
                                           callback_data=f"cj:cat:{j}"))
        kb.row(*row)
    return kb


def area_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Москва", callback_data="cj:area:moscow"),
        InlineKeyboardButton("Московская область", callback_data="cj:area:mo"),
    )
    return kb


def stations_keyboard(locations, area: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    filtered = [l for l in locations if l["area_type"] == area]
    loc_indices = [locations.index(l) for l in filtered]
    for i in range(0, len(loc_indices), 2):
        row = []
        for idx in loc_indices[i:i + 2]:
            row.append(InlineKeyboardButton(locations[idx]["station_name"][:38], callback_data=f"cj:station:{idx}"))
        kb.row(*row)
    kb.row(InlineKeyboardButton("✏️ Указать свою станцию", callback_data="cj:station:other"))
    return kb


def date_choice_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("Сегодня", callback_data="cj:date:0"),
        InlineKeyboardButton("Завтра", callback_data="cj:date:1"),
        InlineKeyboardButton("Послезавтра", callback_data="cj:date:2"),
    )
    kb.row(InlineKeyboardButton("📅 Другая дата (ДД.ММ.ГГГГ)", callback_data="cj:date:other"))
    return kb


def payout_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    items = list(PAYOUT_TYPES.items())
    for i in range(0, len(items), 2):
        kb.row(*[
            InlineKeyboardButton(label, callback_data=f"cj:payout:{key}")
            for key, label in items[i:i + 2]
        ])
    return kb


def slots_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(*[InlineKeyboardButton(str(n), callback_data=f"cj:slots:{n}") for n in (1, 2, 3, 4, 5)])
    kb.row(*[InlineKeyboardButton(str(n), callback_data=f"cj:slots:{n}") for n in (8, 10, 15, 20)])
    return kb


def requirements_keyboard(draft: dict) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()

    def mark(flag):
        return "✅" if flag else "▫️"

    kb.row(
        InlineKeyboardButton(f"{mark(draft.get('experience_required'))} Нужен опыт", callback_data="cj:req:experience_required"),
        InlineKeyboardButton(f"{mark(draft.get('med_book_required'))} Медкнижка", callback_data="cj:req:med_book_required"),
    )
    kb.row(
        InlineKeyboardButton(f"{mark(draft.get('smz_preferred'))} СМЗ приветствуется", callback_data="cj:req:smz_preferred"),
        InlineKeyboardButton(f"{mark(draft.get('meal_included'))} Питание включено", callback_data="cj:req:meal_included"),
    )
    kb.row(
        InlineKeyboardButton(f"{mark(draft.get('is_urgent'))} 🔥 Срочно", callback_data="cj:req:is_urgent"),
    )
    kb.row(InlineKeyboardButton("➡️ Готово, продолжить", callback_data="cj:req:done"))
    return kb


def role_choice_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("👷 Я ищу подработку (исполнитель)", callback_data="register:role:worker"),
    )
    kb.row(
        InlineKeyboardButton("🏢 Я нанимаю (работодатель)", callback_data="register:role:employer"),
    )
    return kb


def web_button_text() -> str:
    return f"🌐 Веб-версия: {WEB_URL}"
