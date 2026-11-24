# ============================================================
# BotControl — бот «Подработка.МСК» (готовый конфиг)
#
# Импорт в приложение: Скрипты → Импорт настроек из кода →
# Выбрать файл / вставить → Разобрать → Применить к боту.
# Файл также запускается как обычный бот:
#   pip install pyTelegramBotAPI && python podrabotka-bot-ready.py
#
# Что внутри:
#   • характер ИИ-помощника Подработка.МСК (SYSTEM_PROMPT, LLM_*,
#     payload, MAX_HISTORY) — в приложении его использует команда
#     /chat и правила с действием «ИИ»;
#   • команды: /start, /help, /jobs, /today, /tomorrow, /create,
#     /cabinet, /tariffs, /rules, /faq, /support, /menu, /profile,
#     /favorites, /search;
#   • клавиатура чата (постоянные кнопки под полем ввода) и
#     inline-меню под ответами с обработчиками нажатий;
#   • наборы ответов: советы исполнителю, мотивация, советы
#     работодателю, приветствия;
#   • расписание дайджестов: утро / день / вечер, будни,
#     пятница и выходные;
#   • анимация /start правкой одного сообщения.
#
# Это декларативный конфиг для BotControl (код не исполняется,
# приложение разбирает его в настройки). Полноценный бот с базой
# данных, регистрацией и откликами — в файле podrabotka_bot.py
# (запуск на компьютере / VPS, та же SQLite-база, что у веб-версии).
# ============================================================
import html
import random
import threading
import time
from datetime import datetime

import telebot
from telebot.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telebot.types import KeyboardButton, ReplyKeyboardMarkup

BOT_TOKEN = "ВСТАВЬ_ТОКЕН_НЕ_ИМПОРТИРУЕТСЯ"  # в приложении токен уже есть
bot = telebot.TeleBot(BOT_TOKEN)

ANSWER_COOLDOWN = 5        # пауза между ответами, сек
DEFAULT_TYPING_SECONDS = 3  # «печатает…», сек

# ---------- характер и параметры ИИ (для команды /chat) ----------
SYSTEM_PROMPT = (
    "РОЛЬ: Ты — помощник сервиса «Подработка.МСК»: короткие смены "
    "в Москве и Московской области (4–12 часов, оплата сразу после смены).\\n"
    "ПРАВИЛА:\\n"
    "1. Язык: ТОЛЬКО русский. Дружелюбно, коротко, по делу.\\n"
    "2. Длина: 1–4 коротких предложения. Без воды и списков, если не просили список.\\n"
    "3. Помогаешь исполнителям: как найти смену по метро/МЦД, как откликнуться, "
    "как получить оплату по СБП, что такое самозанятость и медкнижка.\\n"
    "4. Помогаешь работодателям: как опубликовать смену за минуту, собрать бригаду "
    "«N из M», клонировать смену на завтра, оценить работника.\\n"
    "5. Категории смен: Склад, Курьер, Грузчик, Промоутер, Официант, Уборка, "
    "Стройка, Мероприятия. Районы: Москва и города МО (Химки, Красногорск, "
    "Мытищи, Люберцы, Одинцово, Домодедово).\\n"
    "6. Тарифы: Бесплатный (5 откликов в день), Про 299 ₽ (безлимит и приоритет), "
    "Старт (1 активная смена), Бизнес 1 990 ₽ (до 20 смен).\\n"
    "7. ЗАПРЕЩЕНО: обещать работу, называть точные адреса смен, просить паспортные "
    "данные и коды из SMS, давать юридические советы. Для точных смен отправляй "
    "в каталог: /jobs, /today, /tomorrow.\\n"
    "8. Если не знаешь — честно скажи и предложи /help или /support."
)

LLM_MAX_TOKENS = 200        # ответы помощника
MAX_HISTORY = 6             # память диалога, реплик

payload = {
    "temperature": 0.7,
    "max_tokens": LLM_MAX_TOKENS,
}


# ---------- анимация: одно сообщение правится кадр за кадром ----------
def play_animation(chat_id, frames, delay=0.7, final=None, reply_markup=None,
                   message_id=None, loops=1, pack=None, mono=False, user="", **kw):
    """preset= / text= читает BotControl; здесь кадры уже готовым списком."""
    def fmt(s):
        s = s.replace("{user}", user)
        if s.startswith("\n") or s.startswith(" "):
            s = "\u2800" + s  # Telegram обрезает пустые строки в начале
        return ("<pre>" + html.escape(s) + "</pre>") if mono else s

    mode = "HTML" if mono else None
    frames = list(frames) * max(1, loops)
    if pack:
        final = random.choice(pack)
    m_id = message_id
    if m_id is None:
        m_id = bot.send_message(chat_id, fmt(frames[0]), parse_mode=mode).message_id
        frames = frames[1:]
    for frame in frames:
        time.sleep(delay)
        try:
            bot.edit_message_text(fmt(frame), chat_id, m_id, parse_mode=mode)
        except Exception:
            pass  # «message is not modified» и т.п.
    if final:
        time.sleep(delay)
        bot.edit_message_text(final.replace("{user}", user), chat_id, m_id, reply_markup=reply_markup)


# Заставка /start: поиск смен → приветствие.
ANIM_START = [
    "🔍 Ищу смены рядом с тобой…",
    "📍 Москва и МО · метро и МЦД…",
    "💰 Оплата сразу после смены…",
    "\n  Привет, {user}! 👋",
    "\n  Здесь подработка на сегодня и завтра.",
    "\n  Выбирай кнопку ниже 👇",
]


# ---------- команды ----------
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    play_animation(
        msg.chat.id, ANIM_START, 0.6,
        "👋 Добро пожаловать в «Подработка.МСК»!\nКороткие смены в Москве и МО: отклик в один клик, деньги сразу после смены.\n\nВыбирай кнопку ниже 👇",
        reply_markup=main_menu_keyboard(), user=msg.from_user.first_name or "",
    )


@bot.message_handler(commands=["help"])
def cmd_help(msg):
    bot.send_message(
        msg.chat.id,
        "❓ Помощь — «Подработка.МСК»\n\n"
        "Команды:\n"
        "/jobs — все смены (категории, Москва и МО)\n"
        "/today — смены на сегодня\n"
        "/tomorrow — смены на завтра\n"
        "/create — как опубликовать смену (работодателю)\n"
        "/cabinet — кабинет: отклики, заработок, рейтинг\n"
        "/tariffs — тарифы и лимиты\n"
        "/rules — правила сервиса\n"
        "/faq — частые вопросы\n"
        "/support — поддержка\n"
        "/menu — главное меню\n"
        "/chat + вопрос — спросить ИИ-помощника\n\n"
        "Кнопки под полем ввода работают всегда. "
        "Точные смены с адресами и откликом — в веб-версии (кнопка «🌐 Веб-версия»).",
        reply_markup=help_keyboard(),
    )


@bot.message_handler(commands=["jobs"])
def cmd_jobs(msg):
    bot.send_message(
        msg.chat.id,
        "🔍 Смены в Москве и Московской области\n\n"
        "Выбери категорию — покажу, что есть на сегодня и завтра:\n"
        "• Склад — дарксторы, комплектация, маркировка\n"
        "• Курьер — пеший и вело, электровелосипед выдаём\n"
        "• Грузчик — разгрузка, шоурумы, пекарни\n"
        "• Промоутер — выставки, дегустации, акции\n"
        "• Официант — банкеты, фуршеты, кофейни\n"
        "• Уборка — студии, офисы, после съёмок\n"
        "• Стройка — подсобный рабочий, отделка\n"
        "• Мероприятия — форумы, регистрация гостей\n\n"
        "Точный каталог с фильтрами по метро, оплате и датам — в веб-версии.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(commands=["today"])
def cmd_today(msg):
    bot.send_message(
        msg.chat.id,
        "📅 Смены на СЕГОДНЯ\n\n"
        "Что обычно есть сегодня:\n"
        "• Сборщик онлайн-заказов в даркстор (Автозаводская) — срочно, питание, СБП\n"
        "• Курьер на вечерний пик (Павелецкая) — электровелосипед выдаём\n"
        "• Грузчик-разнорабочий (Курская) — наличные в конце смены\n"
        "• Грузчик-комплектовщик в пекарню (Мытищи) — медкнижка, выпечка с собой\n\n"
        "Список обновляется: открой «🌐 Веб-версию» и нажми «Сегодня» — увидишь все смены с местами и оплатой.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(commands=["tomorrow"])
def cmd_tomorrow(msg):
    bot.send_message(
        msg.chat.id,
        "📅 Смены на ЗАВТРА\n\n"
        "Что обычно есть завтра:\n"
        "• Хелпер регистрации на IT-форуме (Деловой центр) — питание, СМЗ\n"
        "• Маркировщик одежды (Химки, МЦД Химки) — без опыта, СБП\n"
        "• Официант банкетной линии (Тушинская) — развоз до метро\n"
        "• Промоутер в Крокус Экспо (Мякинино) — выход из метро в павильон\n\n"
        "Список обновляется: открой «🌐 Веб-версию» и нажми «Завтра» — увидишь все смены с местами и оплатой.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(commands=["create"])
def cmd_create(msg):
    bot.send_message(
        msg.chat.id,
        "➕ Как опубликовать смену (работодателю)\n\n"
        "1. Открой веб-версию и переключись на роль «Работодатель».\n"
        "2. «+ Новая смена»: название, категория, станция метро/МЦД, точный адрес.\n"
        "3. Дата, время начала и конца, оплата за смену, число мест (N из M).\n"
        "4. Выплата: СБП сразу / наличные / на карту СМЗ. Требования: опыт, медкнижка, питание.\n"
        "5. Опубликуй — кандидаты откликнутся, выбери бригаду в воронке и закрой смену после работы.\n\n"
        "Лимиты: Старт — 1 активная смена, Бизнес — до 20 + бейдж «Топ-смена».\n"
        "Смена клонируется на завтра в один клик.",
        reply_markup=create_keyboard(),
    )


@bot.message_handler(commands=["cabinet"])
def cmd_cabinet(msg):
    bot.send_message(
        msg.chat.id,
        "👤 Кабинет\n\n"
        "Исполнителю:\n"
        "• Мои отклики и статусы (ожидает / принят / завершён)\n"
        "• Заработано за закрытые смены и индекс выходов\n"
        "• Избранное, мини-чат с работодателем, взаимные оценки\n\n"
        "Работодателю:\n"
        "• Мои смены и воронка кандидатов (PRO — выше в списке)\n"
        "• Принять / отклонить, закрыть смену, оценить работников\n\n"
        "Открой кабинет в веб-версии — там все данные и чат.",
        reply_markup=cabinet_keyboard(),
    )


@bot.message_handler(commands=["tariffs"])
def cmd_tariffs(msg):
    bot.send_message(
        msg.chat.id,
        "💰 Тарифы\n\n"
        "Исполнителю:\n"
        "• Бесплатный — 0 ₽, до 5 откликов в день\n"
        "• Про — 299 ₽/мес, безлимит откликов + приоритет в списке кандидатов\n\n"
        "Работодателю:\n"
        "• Старт — 0 ₽, 1 активная смена\n"
        "• Бизнес — 1 990 ₽/мес, до 20 смен + бейдж «Топ-смена»\n\n"
        "Сменить тариф можно в кабинете веб-версии.",
        reply_markup=tariffs_keyboard(),
    )


@bot.message_handler(commands=["rules"])
def cmd_rules(msg):
    bot.send_message(
        msg.chat.id,
        "📜 Правила «Подработка.МСК»\n\n"
        "1. Смены — только в Москве и Московской области, 4–12 часов.\n"
        "2. Оплата — сразу после смены, без комиссии с заработка.\n"
        "3. Отклик — один клик с короткой запиской; лимит по тарифу.\n"
        "4. Пришёл на смену — получи оплату и оценку; не пришёл — падает индекс выходов.\n"
        "5. Рейтинг нельзя купить: оценки взаимные и проходят модерацию.\n"
        "6. Контакты открываются после принятия отклика.\n"
        "7. Спам, фейковые смены и накрутки — бан без предупреждения.\n\n"
        "Подробнее — в веб-версии и в /faq.",
        reply_markup=help_keyboard(),
    )


@bot.message_handler(commands=["faq"])
def cmd_faq(msg):
    bot.send_message(
        msg.chat.id,
        "❓ Частые вопросы\n\n"
        "Как быстро получить деньги?\n"
        "Выплата по СБП сразу после закрытия смены работодателем, наличные — в конце смены, СМЗ — на карту с чеком.\n\n"
        "Нужен ли опыт?\n"
        "Нет: есть смены «Без опыта» — покажем за 10 минут на месте.\n\n"
        "Нужна ли медкнижка?\n"
        "Только где указано в смене (еда, дарксторы, пекарни). Проверь требования в карточке смены.\n\n"
        "Что такое самозанятость?\n"
        "Оформление в «Мой налог» за 5 минут. Работодатели с пометкой СМЗ компенсируют налог 6%.\n\n"
        "Как работает бригада «N из M»?\n"
        "Работодатель ставит, например, 5 мест. Принятые кандидаты занимают места, остальные видят «набор завершён».\n\n"
        "Не нашёл смену рядом?\n"
        "Открой /jobs и выбери свою станцию метро/МЦД, или подпишись на дайджесты (кнопка «🔔 Уведомления»).",
        reply_markup=help_keyboard(),
    )


@bot.message_handler(commands=["support"])
def cmd_support(msg):
    bot.send_message(
        msg.chat.id,
        "🛠 Поддержка «Подработка.МСК»\n\n"
        "• Веб-версия: https://visiontripin.github.io/Podrabotka/app.html\n"
        "• Демо-страница: https://visiontripin.github.io/Podrabotka/\n\n"
        "Напиши, что случилось: смена, дата, что ожидал и что получил. "
        "Отзывы на модерации проверяются вручную — ответ в течение дня.\n\n"
        "ИИ-помощник: /chat + вопрос (например: /chat как откликнуться на смену?).",
        reply_markup=help_keyboard(),
    )


@bot.message_handler(commands=["menu"])
def cmd_menu(msg):
    bot.send_message(
        msg.chat.id,
        "👋 Главное меню «Подработка.МСК»\nВыбирай кнопку ниже 👇",
        reply_markup=main_menu_keyboard(),
    )


@bot.message_handler(commands=["profile"])
def cmd_profile(msg):
    bot.send_message(
        msg.chat.id,
        "👤 Профиль\n\n"
        "В профиле: имя, телефон, город и станция, навыки, медкнижка, "
        "самозанятость, готовность к ночным сменам, рейтинг и отзывы.\n\n"
        "Заполни профиль полностью — работодатели видят его до принятия отклика, "
        "а PRO-анкеты стоят выше в воронке.",
        reply_markup=cabinet_keyboard(),
    )


@bot.message_handler(commands=["favorites"])
def cmd_favorites(msg):
    bot.send_message(
        msg.chat.id,
        "⭐ Избранное\n\n"
        "Сохраняй интересные смены сердечком в каталоге — они появятся здесь.\n"
        "Удобно, если ищешь смены на несколько дней вперёд: сегодня, завтра и ближайшие дни.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(commands=["search"])
def cmd_search(msg):
    bot.send_message(
        msg.chat.id,
        "🔍 Поиск смен\n\n"
        "В веб-версии: поиск по названию, адресу и станции; фильтры по категории, "
        "району (Москва / МО), оплате, датам и способу выплаты.\n\n"
        "Здесь быстро: /today, /tomorrow или выбери категорию ниже.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(commands=["chat"])
def cmd_chat(msg):
    bot.send_message(
        msg.chat.id,
        "🤖 ИИ-помощник\n\n"
        "Спроси так: /chat + вопрос.\n"
        "Например: /chat как откликнуться на смену?\n"
        "ИИ отвечает только в этом сценарии — всё остальное бот делает кнопками.",
    )


# ---------- кнопки клавиатуры чата (постоянные кнопки под полем ввода) ----------
@bot.message_handler(func=lambda m: m.text == "🔍 Найти смену")
def btn_jobs(msg):
    bot.send_message(
        msg.chat.id,
        "🔍 Смены в Москве и Московской области\n\n"
        "Выбери категорию — покажу, что есть на сегодня и завтра. "
        "Точный каталог с фильтрами — в веб-версии.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "📅 Сегодня")
def btn_today(msg):
    bot.send_message(
        msg.chat.id,
        "📅 Смены на СЕГОДНЯ\n\n"
        "Открой «🌐 Веб-версию» и нажми «Сегодня» — увидишь все смены с местами и оплатой.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "📅 Завтра")
def btn_tomorrow(msg):
    bot.send_message(
        msg.chat.id,
        "📅 Смены на ЗАВТРА\n\n"
        "Открой «🌐 Веб-версию» и нажми «Завтра» — увидишь все смены с местами и оплатой.",
        reply_markup=jobs_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "➕ Создать смену")
def btn_create(msg):
    bot.send_message(
        msg.chat.id,
        "➕ Как опубликовать смену (работодателю)\n\n"
        "Открой веб-версию, переключись на «Работодатель» и нажми «+ Новая смена». "
        "Смена публикуется за минуту, кандидаты — в воронке, оплата — сразу после смены.",
        reply_markup=create_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "👤 Кабинет")
def btn_cabinet(msg):
    bot.send_message(
        msg.chat.id,
        "👤 Кабинет\n\n"
        "Отклики, заработок, рейтинг, избранное и чат — в кабинете веб-версии.",
        reply_markup=cabinet_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "💰 Тарифы")
def btn_tariffs(msg):
    bot.send_message(
        msg.chat.id,
        "💰 Тарифы\n\n"
        "Бесплатный (5 откликов/день) · Про 299 ₽ (безлимит) · "
        "Старт (1 смена) · Бизнес 1 990 ₽ (до 20 смен).",
        reply_markup=tariffs_keyboard(),
    )


@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def btn_help(msg):
    bot.send_message(
        msg.chat.id,
        "❓ Помощь — «Подработка.МСК»\n\n"
        "Команды: /jobs, /today, /tomorrow, /create, /cabinet, /tariffs, /rules, /faq, /support, /menu.\n"
        "ИИ-помощник: /chat + вопрос.",
        reply_markup=help_keyboard(),
    )


# ---------- ответы на фразы (содержит) ----------
@bot.message_handler(func=lambda m: "цена" in (m.text or "").lower())
def on_price(msg):
    bot.send_message(
        msg.chat.id,
        "💰 Тарифы\n\n"
        "Бесплатный — 0 ₽, до 5 откликов в день.\n"
        "Про — 299 ₽/мес, безлимит + приоритет в списке кандидатов.\n"
        "Старт — 0 ₽, 1 активная смена.\n"
        "Бизнес — 1 990 ₽/мес, до 20 смен + бейдж «Топ-смена».",
        reply_markup=tariffs_keyboard(),
    )


@bot.message_handler(func=lambda m: "оплат" in (m.text or "").lower())
def on_pay(msg):
    bot.send_message(
        msg.chat.id,
        "💸 Оплата — сразу после смены, без комиссии с заработка.\n\n"
        "• СБП сразу после смены\n"
        "• Наличные в конце смены\n"
        "• На карту СМЗ (+чек)\n\n"
        "Точный способ указан в каждой карточке смены.",
        reply_markup=jobs_keyboard(),
    )


# ---------- inline-меню под сообщениями ----------
def main_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔍 Найти смену", callback_data="jobs"),
        InlineKeyboardButton("📅 Сегодня", callback_data="today"),
    )
    markup.row(
        InlineKeyboardButton("📅 Завтра", callback_data="tomorrow"),
        InlineKeyboardButton("➕ Создать смену", callback_data="create"),
    )
    markup.row(
        InlineKeyboardButton("👤 Кабинет", callback_data="cabinet"),
        InlineKeyboardButton("💰 Тарифы", callback_data="tariffs"),
    )
    markup.row(
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
        InlineKeyboardButton("🌐 Веб-версия", url="https://visiontripin.github.io/Podrabotka/app.html"),
    )
    return markup


def jobs_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Склад", callback_data="cat_sklad"),
        InlineKeyboardButton("Курьер", callback_data="cat_kurer"),
    )
    markup.row(
        InlineKeyboardButton("Грузчик", callback_data="cat_gruzchik"),
        InlineKeyboardButton("Промоутер", callback_data="cat_promouter"),
    )
    markup.row(
        InlineKeyboardButton("Официант", callback_data="cat_oficiant"),
        InlineKeyboardButton("Уборка", callback_data="cat_uborka"),
    )
    markup.row(
        InlineKeyboardButton("Стройка", callback_data="cat_stroika"),
        InlineKeyboardButton("Мероприятия", callback_data="cat_meropriyatiya"),
    )
    markup.row(
        InlineKeyboardButton("📅 Сегодня", callback_data="today"),
        InlineKeyboardButton("📅 Завтра", callback_data="tomorrow"),
    )
    markup.row(
        InlineKeyboardButton("🌐 Все смены в вебе", url="https://visiontripin.github.io/Podrabotka/app.html"),
    )
    return markup


def cabinet_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("⭐ Избранное", callback_data="favorites"),
    )
    markup.row(
        InlineKeyboardButton("💰 Тарифы", callback_data="tariffs"),
        InlineKeyboardButton("🌐 Кабинет в вебе", url="https://visiontripin.github.io/Podrabotka/app.html"),
    )
    return markup


def tariffs_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("👷 Исполнителю", callback_data="tariff_worker"),
        InlineKeyboardButton("🏢 Работодателю", callback_data="tariff_employer"),
    )
    markup.row(
        InlineKeyboardButton("🌐 Сменить в вебе", url="https://visiontripin.github.io/Podrabotka/app.html"),
    )
    return markup


def create_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🌐 Создать в вебе", url="https://visiontripin.github.io/Podrabotka/app.html"),
        InlineKeyboardButton("❓ Помощь", callback_data="help"),
    )
    return markup


def help_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("❓ FAQ", callback_data="faq"),
        InlineKeyboardButton("📜 Правила", callback_data="rules"),
    )
    markup.row(
        InlineKeyboardButton("🛠 Поддержка", callback_data="support"),
        InlineKeyboardButton("🌐 Веб-версия", url="https://visiontripin.github.io/Podrabotka/app.html"),
    )
    return markup


def notify_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🔔 Включить дайджесты", callback_data="notify_on"),
        InlineKeyboardButton("🔕 Выключить", callback_data="notify_off"),
    )
    return markup


def chat_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🔍 Найти смену"), KeyboardButton("📅 Сегодня"))
    markup.row(KeyboardButton("📅 Завтра"), KeyboardButton("➕ Создать смену"))
    markup.row(KeyboardButton("👤 Кабинет"), KeyboardButton("💰 Тарифы"))
    markup.row(KeyboardButton("❓ Помощь"))
    return markup


# ---------- состояние дайджестов ----------
reminders_running = False
user_chat_id = None


# ---------- обработчик нажатий: без него кнопки «немые» ----------
@bot.callback_query_handler(func=lambda call: True)
def on_callback(call):
    global reminders_running, user_chat_id
    chat_id = call.message.chat.id
    if call.data == "jobs":
        bot.answer_callback_query(call.id, "Смены")
        bot.edit_message_text(
            "🔍 Смены в Москве и Московской области\n\nВыбери категорию ниже 👇",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "today":
        bot.answer_callback_query(call.id, "Сегодня")
        bot.edit_message_text(
            "📅 Смены на СЕГОДНЯ\n\nОткрой «🌐 Веб-версию» и нажми «Сегодня» — увидишь все смены с местами и оплатой.",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "tomorrow":
        bot.answer_callback_query(call.id, "Завтра")
        bot.edit_message_text(
            "📅 Смены на ЗАВТРА\n\nОткрой «🌐 Веб-версию» и нажми «Завтра» — увидишь все смены с местами и оплатой.",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "create":
        bot.answer_callback_query(call.id, "Создание смены")
        bot.edit_message_text(
            "➕ Как опубликовать смену\n\nОткрой веб-версию, переключись на «Работодатель» и нажми «+ Новая смена». Смена публикуется за минуту.",
            chat_id, call.message.message_id, reply_markup=create_keyboard())
    elif call.data == "cabinet":
        bot.answer_callback_query(call.id, "Кабинет")
        bot.edit_message_text(
            "👤 Кабинет\n\nОтклики, заработок, рейтинг, избранное и чат — в кабинете веб-версии.",
            chat_id, call.message.message_id, reply_markup=cabinet_keyboard())
    elif call.data == "tariffs":
        bot.answer_callback_query(call.id, "Тарифы")
        bot.edit_message_text(
            "💰 Тарифы\n\nБесплатный (5 откликов/день) · Про 299 ₽ (безлимит) · Старт (1 смена) · Бизнес 1 990 ₽ (до 20 смен).",
            chat_id, call.message.message_id, reply_markup=tariffs_keyboard())
    elif call.data == "help":
        bot.answer_callback_query(call.id, "Помощь")
        bot.edit_message_text(
            "❓ Помощь — «Подработка.МСК»\n\nКоманды: /jobs, /today, /tomorrow, /create, /cabinet, /tariffs, /rules, /faq, /support, /menu.",
            chat_id, call.message.message_id, reply_markup=help_keyboard())
    elif call.data == "rules":
        bot.answer_callback_query(call.id, "Правила")
        bot.edit_message_text(
            "📜 Правила «Подработка.МСК»\n\n1. Смены — только в Москве и Московской области, 4–12 часов.\n2. Оплата — сразу после смены, без комиссии с заработка.\n3. Рейтинг нельзя купить: оценки взаимные и проходят модерацию.",
            chat_id, call.message.message_id, reply_markup=help_keyboard())
    elif call.data == "faq":
        bot.answer_callback_query(call.id, "FAQ")
        bot.edit_message_text(
            "❓ Частые вопросы\n\nКак быстро получить деньги? По СБП сразу после закрытия смены.\nНужен ли опыт? Нет: есть смены «Без опыта».\nНужна ли медкнижка? Только где указано в смене.",
            chat_id, call.message.message_id, reply_markup=help_keyboard())
    elif call.data == "support":
        bot.answer_callback_query(call.id, "Поддержка")
        bot.edit_message_text(
            "🛠 Поддержка «Подработка.МСК»\n\nВеб-версия: https://visiontripin.github.io/Podrabotka/app.html\nНапиши, что случилось: смена, дата, что ожидал и что получил.",
            chat_id, call.message.message_id, reply_markup=help_keyboard())
    elif call.data == "profile":
        bot.answer_callback_query(call.id, "Профиль")
        bot.edit_message_text(
            "👤 Профиль\n\nИмя, телефон, город и станция, навыки, медкнижка, самозанятость, рейтинг и отзывы — в профиле веб-версии.",
            chat_id, call.message.message_id, reply_markup=cabinet_keyboard())
    elif call.data == "favorites":
        bot.answer_callback_query(call.id, "Избранное")
        bot.edit_message_text(
            "⭐ Избранное\n\nСохраняй интересные смены сердечком в каталоге веб-версии — они появятся в кабинете.",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "tariff_worker":
        bot.answer_callback_query(call.id, "Тарифы исполнителя")
        bot.edit_message_text(
            "👷 Исполнителю\n\n• Бесплатный — 0 ₽, до 5 откликов в день\n• Про — 299 ₽/мес, безлимит + приоритет в списке кандидатов",
            chat_id, call.message.message_id, reply_markup=tariffs_keyboard())
    elif call.data == "tariff_employer":
        bot.answer_callback_query(call.id, "Тарифы работодателя")
        bot.edit_message_text(
            "🏢 Работодателю\n\n• Старт — 0 ₽, 1 активная смена\n• Бизнес — 1 990 ₽/мес, до 20 смен + бейдж «Топ-смена»",
            chat_id, call.message.message_id, reply_markup=tariffs_keyboard())
    elif call.data == "cat_sklad":
        bot.answer_callback_query(call.id, "Склад")
        bot.edit_message_text(
            "📦 Склад\n\nДарксторы, комплектация, маркировка. Смены на Автозаводской, в Химках и Люберцах.\n\nТочный список — в веб-версии (категория «Склад»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "cat_kurer":
        bot.answer_callback_query(call.id, "Курьер")
        bot.edit_message_text(
            "🚴 Курьер\n\nПеший и вело. Электровелосипед и термосумку выдаём бесплатно.\n\nТочный список — в веб-версии (категория «Курьер»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "cat_gruzchik":
        bot.answer_callback_query(call.id, "Грузчик")
        bot.edit_message_text(
            "📦 Грузчик\n\nРазгрузка, шоурумы, пекарни. Коробки до 20 кг, тележки на объекте.\n\nТочный список — в веб-версии (категория «Грузчик»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "cat_promouter":
        bot.answer_callback_query(call.id, "Промоутер")
        bot.edit_message_text(
            "🎤 Промоутер\n\nВыставки, дегустации, акции. Выход из метро Мякинино в тёплый переход павильона.\n\nТочный список — в веб-версии (категория «Промоутер»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "cat_oficiant":
        bot.answer_callback_query(call.id, "Официант")
        bot.edit_message_text(
            "🍽 Официант\n\nБанкеты, фуршеты, кофейни. Питание и развоз до метро включены.\n\nТочный список — в веб-версии (категория «Официант»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "cat_uborka":
        bot.answer_callback_query(call.id, "Уборка")
        bot.edit_message_text(
            "🧹 Уборка\n\nСтудии, офисы, после съёмок. Весь инвентарь на месте.\n\nТочный список — в веб-версии (категория «Уборка»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "cat_stroika":
        bot.answer_callback_query(call.id, "Стройка")
        bot.edit_message_text(
            "🏗 Стройка\n\nПодсобный рабочий, чистовая отделка. Каска и жилет выдаются.\n\nТочный список — в веб-версии (категория «Стройка»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "cat_meropriyatiya":
        bot.answer_callback_query(call.id, "Мероприятия")
        bot.edit_message_text(
            "🎪 Мероприятия\n\nФорумы, регистрация гостей, навигация по залам. Питание и форма от организатора.\n\nТочный список — в веб-версии (категория «Мероприятия»).",
            chat_id, call.message.message_id, reply_markup=jobs_keyboard())
    elif call.data == "notify_on":
        if reminders_running:
            bot.answer_callback_query(call.id, "Уже включено")
            return
        reminders_running = True
        user_chat_id = chat_id
        bot.answer_callback_query(call.id, "Дайджесты включены")
        bot.edit_message_text(
            "🔔 Дайджесты включены.\nУтром — новые смены, вечером — итоги дня. Нажми «Выключить», чтобы остановить.",
            chat_id, call.message.message_id, reply_markup=notify_keyboard())
    elif call.data == "notify_off":
        if not reminders_running:
            bot.answer_callback_query(call.id, "Уже выключено")
            return
        reminders_running = False
        bot.answer_callback_query(call.id, "Дайджесты выключены")
        bot.edit_message_text(
            "🔕 Дайджесты выключены.\nНажми «Включить», чтобы возобновить.",
            chat_id, call.message.message_id, reply_markup=notify_keyboard())


# ---------- наборы ответов ----------
GREETINGS = [  # Приветствия
    "Привет! 👋 Ищешь подработку на сегодня или завтра?",
    "Добрый день! 💪 Покажу смены рядом с тобой — выбирай кнопку ниже.",
    "Привет! 🔍 Нажми «Найти смену» — там все категории и даты.",
    "Здравствуйте! 👋 Оплата сразу после смены, без комиссии с заработка.",
]

TIPS = [  # Советы исполнителю
    "💡 Совет: заполни профиль полностью (навыки, медкнижка, СМЗ) — анкета выше в списке кандидатов.",
    "💡 Совет: откликайся с короткой запиской «Готов выйти без опозданий, на связи!» — работодатели читают её первыми.",
    "💡 Совет: приходи за 15 минут до начала смены — это поднимает индекс выходов и рейтинг.",
    "💡 Совет: сохраняй смены в избранное — удобно собирать план на несколько дней вперёд.",
    "💡 Совет: PRO-тариф (299 ₽) даёт безлимит откликов и приоритетный показ анкеты.",
    "💡 Совет: самозанятость оформляется за 5 минут в «Мой налог» — работодатели с пометкой СМЗ компенсируют налог 6%.",
]

MOTIVATION = [  # Мотивация
    "🔥 Смена на сегодня — деньги уже сегодня. Выбирай и откликайся!",
    "💪 Один клик — и ты в бригаде. Оплата сразу после смены.",
    "🚀 Сегодня и завтра — новые смены в Москве и МО. Успей занять место!",
    "⭐ Проверенные работодатели и честный рейтинг, который нельзя купить.",
]

EMPLOYER_TIPS = [  # Советы работодателю
    "🏢 Совет: публикуй смену за минуту — название, станция, адрес, дата, оплата, число мест.",
    "🏢 Совет: клонируй смену на завтра в один клик — бригада соберётся быстрее.",
    "🏢 Совет: PRO-исполнители стоят выше в воронке — принимай их первыми.",
    "🏢 Совет: закрывай смену сразу после работы — исполнитель получит оплату и оставит оценку.",
]

THANKS_LINES = [  # Спасибо
    "💚 Всегда пожалуйста! Хороших смен!",
    "🤗 Обращайся! Здесь всегда есть работа на сегодня и завтра.",
    "✨ Спасибо, что ты с нами! Выбирай смену и выходи зарабатывать.",
]


# ---------- уточняющие вопросы (ответ на любое другое сообщение) ----------
CLARIFY_QUESTIONS = [
    "Что ищешь: смену на сегодня, на завтра или создать смену?",
    "Выбери кнопку ниже — там все категории и даты 👇",
    "Нажми «🔍 Найти смену» или напиши /jobs, /today, /tomorrow.",
    "Уточни: ты исполнитель или работодатель?",
    "Посмотри /help — там все команды и кнопки.",
    "Точные смены с адресами — в веб-версии (кнопка «🌐 Веб-версия»).",
]


# ---------- расписание дайджестов: ежедневно / будни / пятница / выходные ----------
def get_today_schedule(now):
    wd = now.weekday()  # 0 = Пн … 6 = Вс
    schedule = [
        (8, 0, "☀️ Доброе утро! Новые смены на сегодня уже в каталоге. | 🌅 Утро! Свежие смены в Москве и МО — занимай место. | ☀️ Новый день — новые смены! Открой /today.", main_menu_keyboard()),
        (20, 0, "🌙 Вечерний дайджест: проверь статусы откликов и завтрашние смены. | 🌆 Вечер! Завтра — новые смены, откликайся сейчас. | 🌙 Перед сном: посмотри смены на завтра в /tomorrow.", main_menu_keyboard()),
        (12, 0, "💡 Совет дня: заполни профиль полностью — анкета выше в списке кандидатов. | 💡 Совет дня: приходи за 15 минут до смены — растёт индекс выходов. | 💡 Совет дня: сохраняй смены в избранное."),
    ]
    if wd < 5:
        schedule.extend([
            (9, 0, "🔥 Срочные смены на сегодня — места разбирают быстро! Открой /today.", jobs_keyboard()),
            (18, 0, "📋 Проверь отклики и завтрашние смены: /tomorrow.", main_menu_keyboard()),
        ])
        if wd == 4:
            schedule.append((17, 0, "🎉 Пятничный дайджест: смены на выходные уже в каталоге! Открой /jobs.", jobs_keyboard()))
        else:
            schedule.extend([
                (15, 0, "🚀 Вечерние смены ещё свободны — успей откликнуться!", jobs_keyboard()),
            ])
    if wd in (5, 6):
        schedule.append((11, 0, "🌴 Выходные смены: выбери категорию и занимай место!", jobs_keyboard()))
    return sorted(schedule, key=lambda item: (item[0], item[1]))


# ---------- всё остальное — уточняющий вопрос ----------
@bot.message_handler(func=lambda m: True)
def fallback(msg):
    bot.send_message(msg.chat.id, random.choice(CLARIFY_QUESTIONS))


# ---------- цикл дайджестов (только при запуске как обычный бот) ----------
def reminder_loop():
    sent = set()
    while True:
        now = datetime.now()
        if reminders_running and user_chat_id:
            for item in get_today_schedule(now):
                key = (now.date(), item[0], item[1])
                if (now.hour, now.minute) == (item[0], item[1]) and key not in sent:
                    sent.add(key)
                    markup = item[3] if len(item) > 3 else None
                    bot.send_message(user_chat_id, item[2], reply_markup=markup)
        time.sleep(20)


if __name__ == "__main__":
    bot.set_my_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("jobs", "Смены"),
        BotCommand("today", "Смены на сегодня"),
        BotCommand("tomorrow", "Смены на завтра"),
        BotCommand("create", "Создать смену"),
        BotCommand("cabinet", "Кабинет"),
        BotCommand("tariffs", "Тарифы"),
        BotCommand("help", "Помощь"),
        BotCommand("rules", "Правила"),
        BotCommand("faq", "Частые вопросы"),
        BotCommand("support", "Поддержка"),
        BotCommand("menu", "Главное меню"),
        BotCommand("profile", "Профиль"),
        BotCommand("favorites", "Избранное"),
        BotCommand("search", "Поиск смен"),
        BotCommand("chat", "Спросить ИИ-помощника"),
    ])
    threading.Thread(target=reminder_loop, daemon=True).start()
    bot.infinity_polling()
