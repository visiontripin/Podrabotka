# Подработка.МСК — имитационный бот (демо, без базы данных)
#
# Полностью статический конфиг для BotControl:
#  • ни одного import, ни одной f-строки, никакого HTML в ответах;
#  • все тексты ответов — литералы (импортёр видит их целиком);
#  • у каждой inline-кнопки свой литеральный callback_data и своя функция
#    с точным сравнением данных нажатия;
#  • каждое inline-меню объявлено без аргументов и прикреплено reply_markup
#    в команде-разделе;
#  • в файле ровно одна ReplyKeyboardMarkup — chat_keyboard(), прикреплена к /start;
#  • у каждой кнопки нижней клавиатуры своё отдельное текстовое правило.

BOT_TOKEN = "НЕ_ИМПОРТИРУЕТСЯ"

# ---------- 1. Поведение и паузы ----------
ANSWER_COOLDOWN = 15
DEFAULT_TYPING_SECONDS = 3

# ---------- 2. Уточняющие вопросы на незнакомые сообщения ----------
CLARIFY_QUESTIONS = [
    "Не понял, {user} 🙂 Выбери раздел кнопками внизу или открой /help.",
    "Такого раздела в демо нет. Нажми /start — покажу главное меню.",
    "Напиши /examples — там показано, что делает каждая кнопка.",
]

# ---------- 3. Нижняя клавиатура чата (единственная ReplyKeyboardMarkup) ----------
def chat_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("Я ищу подработку (исполнитель)"), KeyboardButton("Я нанимаю (работодатель)"))
    markup.row(KeyboardButton("Найти смену"), KeyboardButton("Откликнуться"))
    markup.row(KeyboardButton("Мои отклики"), KeyboardButton("Мои смены"))
    markup.row(KeyboardButton("Кандидаты"), KeyboardButton("Чаты"))
    markup.row(KeyboardButton("Профиль"), KeyboardButton("Тарифы"))
    markup.row(KeyboardButton("Помощь"))
    return markup

# ---------- 4. Inline-меню (все без аргументов) ----------
def jobs_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🏬 Грузчик на склад — 4500 ₽", callback_data="job:101"))
    markup.row(InlineKeyboardButton("🚴 Курьер доставки еды — 3800 ₽", callback_data="job:102"))
    markup.row(InlineKeyboardButton("🍽 Официант в кафе — 3200 ₽", callback_data="job:103"))
    markup.row(InlineKeyboardButton("🎤 Промоутер в ТЦ — 2900 ₽", callback_data="job:104"))
    markup.row(InlineKeyboardButton("🧹 Уборщик помещений — 3400 ₽", callback_data="job:105"))
    markup.row(InlineKeyboardButton("🌐 Веб-версия", url="https://visiontripin.github.io/Podrabotka/"))
    return markup

def apply_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🏬 Грузчик — 4500 ₽", callback_data="apply:101"))
    markup.row(InlineKeyboardButton("🚴 Курьер — 3800 ₽", callback_data="apply:102"))
    markup.row(InlineKeyboardButton("🍽 Официант — 3200 ₽", callback_data="apply:103"))
    markup.row(InlineKeyboardButton("🎤 Промоутер — 2900 ₽", callback_data="apply:104"))
    markup.row(InlineKeyboardButton("🧹 Уборщик — 3400 ₽", callback_data="apply:105"))
    return markup

def applications_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Отклик #7 — ⏳ Ожидает решения", callback_data="app:7"))
    markup.row(InlineKeyboardButton("Отклик #5 — ✅ Принят", callback_data="app:5"))
    return markup

def my_jobs_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Смена #101 — 🟢 Активна", callback_data="myjob:101"))
    markup.row(InlineKeyboardButton("Смена #103 — ⏸ Пауза", callback_data="myjob:103"))
    return markup

def candidates_menu():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✅ Принять #12", callback_data="cand:accept:12"), InlineKeyboardButton("❌ Отклонить #12", callback_data="cand:reject:12"))
    markup.row(InlineKeyboardButton("✅ Принять #13", callback_data="cand:accept:13"), InlineKeyboardButton("❌ Отклонить #13", callback_data="cand:reject:13"))
    return markup

# ---------- 5. Команды бота ----------
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.send_message(
        msg.chat.id,
        "Привет, {user}! Это демо-бот Подработка.МСК.\n\n"
        "Здесь всё работает в режиме имитации: смены, отклики, кандидаты и чаты — "
        "демонстрационные данные, реальной базы нет.\n\n"
        "👷 Исполнитель: находит смену, откликается, следит за статусом.\n"
        "🏢 Работодатель: публикует смену, смотрит кандидатов, принимает решение.\n\n"
        "Выбери раздел кнопками внизу 👇",
        reply_markup=chat_keyboard(),
    )

@bot.message_handler(commands=["help"])
def cmd_help(msg):
    bot.send_message(
        msg.chat.id,
        "❓ Помощь по демо-боту\n\n"
        "Команды:\n"
        "/start — главное меню\n"
        "/help — эта справка\n"
        "/examples — примеры работы каждой кнопки\n\n"
        "Разделы внизу:\n"
        "🔍 Найти смену — 5 демо-смен с карточками\n"
        "✋ Откликнуться — отклик на выбранную смену\n"
        "📝 Мои отклики — статусы ваших заявок\n"
        "📦 Мои смены — смены работодателя\n"
        "👥 Кандидаты — принять или отклонить\n"
        "💬 Чаты — переписка\n"
        "👤 Профиль — данные демо-аккаунта\n"
        "💰 Тарифы — условия подписки\n"
        "❓ Помощь — этот текст\n\n"
        "Все данные выдуманы, заявки никуда не уходят.",
    )

@bot.message_handler(commands=["examples"])
def cmd_examples(msg):
    bot.send_message(
        msg.chat.id,
        "📖 Примеры работы бота (демо-гид)\n\n"
        "👷 «Я ищу подработку (исполнитель)» — режим исполнителя.\n\n"
        "🔍 «Найти смену» — список из 5 смен. Нажми на смену в меню под сообщением — "
        "карточка откроется в этом же сообщении, а меню останется под ней: "
        "так можно листать смены одну за другой.\n\n"
        "✋ «Откликнуться» — выбери смену, отклик уйдёт работодателю. "
        "Статус станет «⏳ Ожидает решения».\n\n"
        "📝 «Мои отклики» — 2 отклика: #7 ожидает решения, #5 принят. "
        "Нажми на отклик — откроются подробности и контакт работодателя.\n\n"
        "📦 «Мои смены» — смены работодателя: #101 активна, #103 на паузе. "
        "Нажми на смену — карточка с откликами и статусом.\n\n"
        "👥 «Кандидаты» — на смену #101 откликнулись двое. Кнопки «Принять» "
        "и «Отклонить» показывают результат решения.\n\n"
        "💬 «Чаты» — переписка с работодателями.\n\n"
        "👤 «Профиль» — демо-профиль, рейтинг, заработок.\n\n"
        "💰 «Тарифы» — условия для исполнителя и работодателя.\n\n"
        "❓ «Помощь» — команды и разделы бота.",
    )

# ---------- 6. Кнопки нижней клавиатуры (по правилу на каждую) ----------
@bot.message_handler(func=lambda m: m.text == "Я ищу подработку (исполнитель)")
def btn_role_worker(msg):
    bot.send_message(
        msg.chat.id,
        "Режим: 👷 Исполнитель\n\n"
        "Что доступно:\n"
        "🔍 «Найти смену» — 5 смен в Москве с оплатой от 2900 до 4500 ₽.\n"
        "✋ «Откликнуться» — заявка работодателю в один тап.\n"
        "📝 «Мои отклики» — статусы заявок и контакты.\n"
        "💬 «Чаты» — переписка с работодателем.\n\n"
        "Демо-профиль: Алексей Demo · рейтинг 4.9 ★ · 8 закрытых смен.",
    )

@bot.message_handler(func=lambda m: m.text == "Я нанимаю (работодатель)")
def btn_role_employer(msg):
    bot.send_message(
        msg.chat.id,
        "Режим: 🏢 Работодатель\n\n"
        "Что доступно:\n"
        "📦 «Мои смены» — активные и приостановленные смены.\n"
        "👥 «Кандидаты» — отклики с решением «Принять» или «Отклонить».\n"
        "💬 «Чаты» — переписка с исполнителями.\n"
        "💰 «Тарифы» — тарифы для работодателя.\n\n"
        "Демо-аккаунт: ООО «Логистика-М» · 2 активные смены · 2 отклика в ожидании.",
    )

@bot.message_handler(func=lambda m: m.text == "Найти смену")
def btn_find_jobs(msg):
    bot.send_message(
        msg.chat.id,
        "🔍 Смены в Москве — демо-подборка на 24–26 ноября\n\n"
        "1. 🏬 Грузчик на склад Wildberries — 4500 ₽\n"
        "   Автозаводская · 25.11 · 09:00–18:00 · мест: 2 из 5\n\n"
        "2. 🚴 Курьер доставки еды — 3800 ₽\n"
        "   Китай-город · 24.11 · 12:00–21:00 · мест: 1 из 3\n\n"
        "3. 🍽 Официант в кафе — 3200 ₽\n"
        "   Тверская · 26.11 · 17:00–23:00 · мест: 4 из 6\n\n"
        "4. 🎤 Промоутер в ТЦ — 2900 ₽\n"
        "   ВДНХ · 24.11 · 10:00–16:00 · мест: 0 из 2\n\n"
        "5. 🧹 Уборщик помещений — 3400 ₽\n"
        "   Парк Победы · 25.11 · 08:00–12:00 · мест: 1 из 3\n\n"
        "Нажми на смену ниже — карточка появится в этом же сообщении 👇",
        reply_markup=jobs_menu(),
    )

@bot.message_handler(func=lambda m: m.text == "Откликнуться")
def btn_apply(msg):
    bot.send_message(
        msg.chat.id,
        "✋ Отклик на смену\n\n"
        "Выбери смену, на которую хочешь откликнуться. В демо-режиме заявка "
        "никуда не уходит, но бот покажет ровно то, что увидел бы исполнитель.\n\n"
        "Свободные места есть на четырёх сменах из пяти 👇",
        reply_markup=apply_menu(),
    )

@bot.message_handler(func=lambda m: m.text == "Мои отклики")
def btn_my_applications(msg):
    bot.send_message(
        msg.chat.id,
        "📝 Мои отклики — 2\n\n"
        "#7 — Курьер доставки еды\n"
        "⏳ Ожидает решения · 3800 ₽ · 24.11.2026, 12:00–21:00\n\n"
        "#5 — Промоутер в ТЦ\n"
        "✅ Принят · 2900 ₽ · 26.11.2026, 10:00–16:00\n\n"
        "Нажми на отклик ниже, чтобы открыть подробности 👇",
        reply_markup=applications_menu(),
    )

@bot.message_handler(func=lambda m: m.text == "Мои смены")
def btn_my_jobs(msg):
    bot.send_message(
        msg.chat.id,
        "📦 Мои смены (работодатель)\n\n"
        "#101 — Грузчик на склад Wildberries\n"
        "🟢 Активна · 4500 ₽ · 25.11.2026 · 09:00–18:00\n"
        "Откликов: 2 (в ожидании: 2)\n\n"
        "#103 — Официант в кафе\n"
        "⏸ Пауза · 3200 ₽ · 26.11.2026 · 17:00–23:00\n"
        "Откликов: 0\n\n"
        "Нажми на смену ниже 👇",
        reply_markup=my_jobs_menu(),
    )

@bot.message_handler(func=lambda m: m.text == "Кандидаты")
def btn_candidates(msg):
    bot.send_message(
        msg.chat.id,
        "👥 Кандидаты на смену #101\n"
        "Грузчик на склад Wildberries · 25.11.2026 · 4500 ₽\n\n"
        "1. #12 Алексей Demo — 4.9 ★\n"
        "   8 закрытых смен · опыт склада 3 месяца · ⏳ Ожидает решения\n\n"
        "2. #13 Мария Д. — 4.7 ★\n"
        "   5 закрытых смен · медкнижка есть · ⏳ Ожидает решения\n\n"
        "Выбери решение кнопками ниже 👇",
        reply_markup=candidates_menu(),
    )

@bot.message_handler(func=lambda m: m.text == "Чаты")
def btn_chats(msg):
    bot.send_message(
        msg.chat.id,
        "💬 Чаты — демо\n\n"
        "ИП Смирнов А.В. · смена «Курьер доставки еды»\n"
        "Вы: Добрый день! Готов выйти на смену 24 ноября.\n"
        "Работодатель: Отлично, ждём в 12:00 у метро Китай-город.\n\n"
        "Кафе «Уют» · смена «Официант»\n"
        "Вы: Здравствуйте, подскажите форму одежды.\n"
        "Работодатель: Чёрный верх и брюки, фартук выдаём на месте.\n\n"
        "В демо-режиме отправка сообщений имитируется.",
    )

@bot.message_handler(func=lambda m: m.text == "Профиль")
def btn_profile(msg):
    bot.send_message(
        msg.chat.id,
        "👤 Профиль — демо\n\n"
        "Имя: Алексей Demo\n"
        "Роль: 👷 Исполнитель и 🏢 Работодатель\n"
        "Email: alexey.demo@example.com\n"
        "Рейтинг: 4.9 ★ (12 отзывов)\n"
        "Закрытых смен: 8\n"
        "Заработано: 28 500 ₽\n\n"
        "Все данные выдуманы — это имитация.",
    )

@bot.message_handler(func=lambda m: m.text == "Тарифы")
def btn_tariffs(msg):
    bot.send_message(
        msg.chat.id,
        "💰 Тарифы — демо\n\n"
        "👷 Исполнителю:\n"
        "• Бесплатный — до 5 откликов в день\n"
        "• Про — 299 ₽/мес, отклики без лимита и приоритет в подборке\n\n"
        "🏢 Работодателю:\n"
        "• Старт — до 5 активных смен\n"
        "• Бизнес — без лимита, кандидаты в один экран\n\n"
        "Оплата в демо не подключена.",
    )

@bot.message_handler(func=lambda m: m.text == "Помощь")
def btn_help_txt(msg):
    bot.send_message(
        msg.chat.id,
        "❓ Помощь по демо-боту\n\n"
        "🔍 Найти смену — 5 смен с карточками\n"
        "✋ Откликнуться — заявка на смену\n"
        "📝 Мои отклики — статусы заявок\n"
        "📦 Мои смены — смены работодателя\n"
        "👥 Кандидаты — принять или отклонить\n"
        "💬 Чаты — переписка\n"
        "👤 Профиль — демо-аккаунт\n"
        "💰 Тарифы — условия подписки\n\n"
        "Команды: /start · /help · /examples\n"
        "Все данные выдуманы, реальной базы нет.",
    )

# ---------- 7. Inline-кнопки: карточки смен ----------
@bot.callback_query_handler(func=lambda call: call.data == "job:101")
def cb_job_101(call):
    bot.answer_callback_query(call.id, "Грузчик на склад — 4500 ₽")
    bot.edit_message_text(
        "🏬 Грузчик на склад Wildberries ✅\n\n"
        "💰 4500 ₽ за смену, оплата в день работы\n"
        "📍 Автозаводская · 25.11.2026 · 09:00–18:00\n"
        "👥 Свободно мест: 2 из 5\n"
        "🏢 ООО «Логистика-М» · проверенный работодатель\n\n"
        "📝 Разгрузка и погрузка товара на складе. Перчатки и жилет выдаём, "
        "обувь — на нескользящей подошве.\n\n"
        "📋 Требования: опыт от 3 месяцев, медкнижка не нужна\n\n"
        "Хочешь эту смену — нажми «Откликнуться» в клавиатуре внизу.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=jobs_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "job:102")
def cb_job_102(call):
    bot.answer_callback_query(call.id, "Курьер доставки еды — 3800 ₽")
    bot.edit_message_text(
        "🚴 Курьер доставки еды\n\n"
        "💰 3800 ₽ за смену, оплата сразу после смены\n"
        "📍 Китай-город · 24.11.2026 · 12:00–21:00\n"
        "👥 Свободно мест: 1 из 3\n"
        "🏢 ИП Смирнов А.В.\n\n"
        "📝 Доставка заказов по центру Москвы. Самокат или велосипед "
        "предоставляем, терминал выдаём на смену.\n\n"
        "📋 Требования: смартфон с интернетом, паспорт, опыт не нужен\n\n"
        "Хочешь эту смену — нажми «Откликнуться» в клавиатуре внизу.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=jobs_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "job:103")
def cb_job_103(call):
    bot.answer_callback_query(call.id, "Официант в кафе — 3200 ₽")
    bot.edit_message_text(
        "🍽 Официант в кафе ✅\n\n"
        "💰 3200 ₽ за смену плюс чаевые\n"
        "📍 Тверская · 26.11.2026 · 17:00–23:00\n"
        "👥 Свободно мест: 4 из 6\n"
        "🏢 Кафе «Уют» · проверенный работодатель\n\n"
        "📝 Обслуживание гостей в уютном кафе на Тверской. Обучение на месте, "
        "смена с наставником.\n\n"
        "📋 Требования: коммуникабельность, чёрная одежда, медкнижка\n\n"
        "Хочешь эту смену — нажми «Откликнуться» в клавиатуре внизу.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=jobs_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "job:104")
def cb_job_104(call):
    bot.answer_callback_query(call.id, "Промоутер в ТЦ — 2900 ₽")
    bot.edit_message_text(
        "🎤 Промоутер в ТЦ\n\n"
        "💰 2900 ₽ за смену\n"
        "📍 ВДНХ · 24.11.2026 · 10:00–16:00\n"
        "👥 Свободно мест: 0 из 2 — места закончились\n"
        "🏢 Агентство «Ярмарка»\n\n"
        "📝 Раздача листовок и консультация гостей торгового центра. "
        "Фирменную футболку выдаём на месте.\n\n"
        "📋 Требования: активная позиция, чистая речь, опыт не нужен\n\n"
        "Мест нет, но отклик попадёт в лист ожидания: нажми «Откликнуться».",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=jobs_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "job:105")
def cb_job_105(call):
    bot.answer_callback_query(call.id, "Уборщик помещений — 3400 ₽")
    bot.edit_message_text(
        "🧹 Уборщик помещений ✅\n\n"
        "💰 3400 ₽ за смену\n"
        "📍 Парк Победы · 25.11.2026 · 08:00–12:00\n"
        "👥 Свободно мест: 1 из 3\n"
        "🏢 ООО «Чистый дом» · проверенный работодатель\n\n"
        "📝 Поддержание чистоты в офисном центре. Инструмент и моющие "
        "средства выдаются на месте.\n\n"
        "📋 Требования: медкнижка, опыт уборки от 6 месяцев, пунктуальность\n\n"
        "Хочешь эту смену — нажми «Откликнуться» в клавиатуре внизу.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=jobs_menu(),
    )

# ---------- 8. Inline-кнопки: отклики ----------
@bot.callback_query_handler(func=lambda call: call.data == "apply:101")
def cb_apply_101(call):
    bot.answer_callback_query(call.id, "Отклик отправлен ✅")
    bot.edit_message_text(
        "✅ Отклик отправлен\n\n"
        "🏬 Грузчик на склад Wildberries\n"
        "💰 4500 ₽ · 📍 Автозаводская\n"
        "🗓 25.11.2026 · 09:00–18:00\n"
        "🏢 ООО «Логистика-М»\n\n"
        "Статус: ⏳ Ожидает решения\n\n"
        "Работодатель увидит отклик в разделе «Кандидаты» и напишет в чат. "
        "Следи за статусом в «Мои отклики».",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=apply_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "apply:102")
def cb_apply_102(call):
    bot.answer_callback_query(call.id, "Отклик отправлен ✅")
    bot.edit_message_text(
        "✅ Отклик отправлен\n\n"
        "🚴 Курьер доставки еды\n"
        "💰 3800 ₽ · 📍 Китай-город\n"
        "🗓 24.11.2026 · 12:00–21:00\n"
        "🏢 ИП Смирнов А.В.\n\n"
        "Статус: ⏳ Ожидает решения\n\n"
        "Это смена на сегодня — работодатель обычно отвечает в течение часа. "
        "Следи за статусом в «Мои отклики».",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=apply_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "apply:103")
def cb_apply_103(call):
    bot.answer_callback_query(call.id, "Отклик отправлен ✅")
    bot.edit_message_text(
        "✅ Отклик отправлен\n\n"
        "🍽 Официант в кафе\n"
        "💰 3200 ₽ · 📍 Тверская\n"
        "🗓 26.11.2026 · 17:00–23:00\n"
        "🏢 Кафе «Уют»\n\n"
        "Статус: ⏳ Ожидает решения\n\n"
        "Не забудь про чёрную одежду — это указано в требованиях смены.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=apply_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "apply:104")
def cb_apply_104(call):
    bot.answer_callback_query(call.id, "Мест нет — лист ожидания")
    bot.edit_message_text(
        "⛔ Свободных мест не осталось\n\n"
        "🎤 Промоутер в ТЦ\n"
        "💰 2900 ₽ · 📍 ВДНХ · 24.11.2026\n"
        "👥 Занято: 2 из 2\n\n"
        "Ты в листе ожидания: если кто-то откажется, работодатель напишет "
        "тебе первому.\n\n"
        "Пока можно посмотреть другие смены 👇",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=apply_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "apply:105")
def cb_apply_105(call):
    bot.answer_callback_query(call.id, "Отклик отправлен ✅")
    bot.edit_message_text(
        "✅ Отклик отправлен\n\n"
        "🧹 Уборщик помещений\n"
        "💰 3400 ₽ · 📍 Парк Победы\n"
        "🗓 25.11.2026 · 08:00–12:00\n"
        "🏢 ООО «Чистый дом»\n\n"
        "Статус: ⏳ Ожидает решения\n\n"
        "Медкнижка обязательна — возьми её на смену.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=apply_menu(),
    )

# ---------- 9. Inline-кнопки: мои отклики ----------
@bot.callback_query_handler(func=lambda call: call.data == "app:7")
def cb_app_7(call):
    bot.answer_callback_query(call.id, "Отклик #7")
    bot.edit_message_text(
        "📝 Отклик #7 — ⏳ Ожидает решения\n\n"
        "🚴 Курьер доставки еды\n"
        "💰 3800 ₽ · 📍 Китай-город\n"
        "🗓 24.11.2026 · 12:00–21:00\n"
        "🏢 ИП Смирнов А.В.\n"
        "📞 +7 (999) 123-45-67\n\n"
        "Что дальше: работодатель смотрит отклики до 11:00, "
        "после этого статус сменится на «Принят» или «Отказ».\n\n"
        "Статус в демо не меняется — это имитация.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=applications_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "app:5")
def cb_app_5(call):
    bot.answer_callback_query(call.id, "Отклик #5")
    bot.edit_message_text(
        "📝 Отклик #5 — ✅ Принят\n\n"
        "🎤 Промоутер в ТЦ\n"
        "💰 2900 ₽ · 📍 ВДНХ\n"
        "🗓 26.11.2026 · 10:00–16:00\n"
        "🏢 Агентство «Ярмарка»\n"
        "📞 +7 (999) 987-65-43\n\n"
        "Что дальше: приди за 15 минут до начала, вход со стороны "
        "центрального атриума. Фирменную футболку выдадут на месте.\n\n"
        "Контакт и адрес сохранены в чате.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=applications_menu(),
    )

# ---------- 10. Inline-кнопки: смены работодателя ----------
@bot.callback_query_handler(func=lambda call: call.data == "myjob:101")
def cb_myjob_101(call):
    bot.answer_callback_query(call.id, "Смена #101")
    bot.edit_message_text(
        "📦 Смена #101 — 🟢 Активна\n\n"
        "🏬 Грузчик на склад Wildberries\n"
        "💰 4500 ₽ · 📍 Автозаводская\n"
        "🗓 25.11.2026 · 09:00–18:00 · мест: 2 из 5\n\n"
        "👥 Откликов: 2 (в ожидании: 2)\n"
        "• #12 Алексей Demo — 4.9 ★\n"
        "• #13 Мария Д. — 4.7 ★\n\n"
        "Решения по кандидатам — в разделе «Кандидаты».",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=my_jobs_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "myjob:103")
def cb_myjob_103(call):
    bot.answer_callback_query(call.id, "Смена #103")
    bot.edit_message_text(
        "📦 Смена #103 — ⏸ Пауза\n\n"
        "🍽 Официант в кафе\n"
        "💰 3200 ₽ · 📍 Тверская\n"
        "🗓 26.11.2026 · 17:00–23:00 · мест: 4 из 6\n\n"
        "Смена скрыта из подборки: новые отклики не приходят, "
        "уже собранные остаются.\n\n"
        "В демо-режиме возобновление не меняет данные — это имитация.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=my_jobs_menu(),
    )

# ---------- 11. Inline-кнопки: кандидаты ----------
@bot.callback_query_handler(func=lambda call: call.data == "cand:accept:12")
def cb_cand_accept_12(call):
    bot.answer_callback_query(call.id, "Кандидат #12 принят ✅")
    bot.edit_message_text(
        "✅ Кандидат принят\n\n"
        "Смена #101 «Грузчик на склад Wildberries» · 25.11.2026 · 09:00–18:00\n\n"
        "Принят: #12 Алексей Demo — 4.9 ★\n"
        "💰 4500 ₽ · 📍 Автозаводская\n\n"
        "Исполнителю отправлено уведомление в чат, "
        "смена появилась в его «Мои отклики».\n\n"
        "Остался второй кандидат — решение можно принять ниже.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=candidates_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "cand:reject:12")
def cb_cand_reject_12(call):
    bot.answer_callback_query(call.id, "Кандидат #12 отклонён")
    bot.edit_message_text(
        "❌ Отклик отклонён\n\n"
        "Смена #101 «Грузчик на склад Wildberries» · 25.11.2026\n\n"
        "Отклонён: #12 Алексей Demo — 4.9 ★\n\n"
        "Исполнитель получил вежливый отказ и может откликнуться "
        "на другие смены. Место осталось свободным.\n\n"
        "Второй кандидат ждёт решения ниже.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=candidates_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "cand:accept:13")
def cb_cand_accept_13(call):
    bot.answer_callback_query(call.id, "Кандидат #13 принят ✅")
    bot.edit_message_text(
        "✅ Кандидат принят\n\n"
        "Смена #101 «Грузчик на склад Wildberries» · 25.11.2026 · 09:00–18:00\n\n"
        "Принята: #13 Мария Д. — 4.7 ★\n"
        "💰 4500 ₽ · 📍 Автозаводская\n\n"
        "Исполнителю отправлено уведомление в чат. "
        "Медкнижка у кандидата уже есть — можно выходить на смену.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=candidates_menu(),
    )

@bot.callback_query_handler(func=lambda call: call.data == "cand:reject:13")
def cb_cand_reject_13(call):
    bot.answer_callback_query(call.id, "Кандидат #13 отклонён")
    bot.edit_message_text(
        "❌ Отклик отклонён\n\n"
        "Смена #101 «Грузчик на склад Wildberries» · 25.11.2026\n\n"
        "Отклонена: #13 Мария Д. — 4.7 ★\n\n"
        "Исполнитель получил вежливый отказ, место осталось свободным.\n\n"
        "Первый кандидат ещё ждёт решения ниже.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=candidates_menu(),
    )

# ---------- 12. Главное меню команд Telegram ----------
bot.set_my_commands([
    BotCommand("start", "Главное меню"),
    BotCommand("help", "Справка"),
    BotCommand("examples", "Примеры работы кнопок"),
])
