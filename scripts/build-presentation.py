#!/usr/bin/env python3
"""
Сборка презентации «Подработка.МСК» из одного источника контента.

Результат:
  presentation/podrabotka-msk-deck.pdf  — 13 слайдов 16:9, шрифты встроены
  presentation/index.html               — те же слайды в браузере (стрелки ← →)

Требования (только для пересборки презентации, не для запуска приложения):
  python3 -m pip install reportlab fonttools brotli

Запуск:  npm run build:presentation   (или python3 scripts/build-presentation.py)
"""

from __future__ import annotations

import base64
import io
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "presentation"
FONT_DIR = ROOT / "src" / "assets" / "fonts"

BRAND = "#D82376"
BRAND_DARK = "#BA1762"
BRAND_SOFT = "#FCE7F1"
BRAND_TINT = "#FDF2F7"
INK = "#111115"
INK_700 = "#34343E"
INK_500 = "#6B7280"
INK_400 = "#9CA3AF"
LINE = "#E8E8EF"
SOFT = "#F7F7FA"
WHITE = "#FFFFFF"

SITE = "https://visiontripin.github.io/Podrabotka"
REPO = "https://github.com/visiontripin/Podrabotka"


# --------------------------------------------------------------------------
# Контент презентации
# --------------------------------------------------------------------------
SPEAKER_SLIDES = [
    {
        "kind": "cover",
        "eyebrow": "Продуктовая презентация · MVP",
        "title": "Подработка.МСК",
        "subtitle": "Платформа быстрых смен в Москве и Московской области",
        "lead": "Работодатель публикует смену за минуту. Исполнитель откликается "
                "в один клик и получает деньги сразу после смены — без комиссии "
                "с заработка.",
        "facts": ["3 роли", "0% комиссии", "Метро и МЦД", "Работает офлайн"],
        "footer": f"{SITE} · {REPO}",
    },
    {
        "kind": "content",
        "eyebrow": "01 · Проблема",
        "title": "Смена нужна сегодня, а не «в следующем месяце»",
        "lead": "Классические job-борды рассчитаны на найм на месяцы. Сменному "
                "персоналу и малому бизнесу нужно закрыть смену за часы.",
        "bullets": [
            ("Работодателю", "Нужен человек на 4–12 часов: склад, зал, доставка, мероприятие. "
                              "Вакансия на HeadHunter висит неделю, смена — сегодня вечером."),
            ("Исполнителю", "Нужен заработок завтра, а не карьера на пять лет. Резюме, "
                            "собеседования и месячный онбординг — барьер, а не помощь."),
            ("Рынку", "Агентства берут 15–30% с фонда оплаты и не работают со сменами "
                      "на один день. Разрыв закрывают чаты и сарафан."),
            ("Итог", "Между «нужен человек через 4 часа» и «ищу подработку на завтра» "
                     "нет прозрачного и быстрого инструмента."),
        ],
        "note": "Гипотеза MVP: если путь «нашёл → откликнулся → вышел → получил деньги» "
                "занимает минуты, а не дни, смены закрываются в тот же день.",
    },
    {
        "kind": "content",
        "eyebrow": "02 · Решение",
        "title": "Смена закрывается в тот же день",
        "lead": "Три роли в одном приложении: витрина смен, кабинет исполнителя "
                "и работодателя, модерация и тарифы.",
        "steps": [
            ("Публикация за минуту", "Название, адрес, дата, часы, оплата. Часовая ставка "
                                     "считается автоматически."),
            ("Поиск рядом с домом", "Фильтры по метро и МЦД, району, датам, оплате "
                                    "и способу выплаты."),
            ("Отклик в один клик", "Сопроводительная записка, лимиты по тарифу, "
                                   "воронка кандидатов у работодателя."),
            ("Выплата после смены", "Закрытие смены фиксирует выплату, заработок "
                                    "и рейтинг обеих сторон."),
        ],
        "note": "Ключевой принцип: 0% комиссии с заработка исполнителя. "
                "Монетизация — тарифы работодателя и PRO-подписка рабочего.",
    },
    {
        "kind": "cards",
        "eyebrow": "03 · Аудитория",
        "title": "Кому это нужно",
        "lead": "Демо-данные: 12 смен, 7 пользователей, 4 тарифа, станции метро и МЦД.",
        "cards": [
            ("Рабочий", "18–35 лет, Москва и МО",
             ["Ищет смены по станции и дате, а не по названию компании",
              "Откликается с телефона в перерыве между делами",
              "Ведёт заработок, рейтинг и историю выходов",
              "Ценит выплату сразу после смены, а не 15-го числа",
              "Нужны честные условия: адрес, часы, ставка — до отклика"],
             "5 откликов в день бесплатно"),
            ("Работодатель", "Малый и средний бизнес",
             ["Склад, ритейл, доставка, HoReCa, промо и мероприятия",
              "Нужны 1–20 человек на смену, часто на завтра",
              "Считает стоимость закрытия смены, а не «бренд работодателя»",
              "Проверяет медкнижку и статус самозанятости",
              "Хочет видеть индекс выходов до принятия"],
             "до 20 активных вакансий"),
            ("Модератор", "Операционная команда",
             ["Проверяет каждый отзыв до публикации",
              "Верифицирует компании и исполнителей",
              "Меняет тарифы и лимиты без деплоя",
              "Открывает регионы: RU, BY, KZ, UZ, AE",
              "Следит за балансом спроса и предложения"],
             "очередь отзывов в реальном времени"),
        ],
        "note": "География старта: Москва и Московская область. В схеме данных с первого "
                "дня есть регионы RU, BY, KZ, UZ, AE с валютами и часовыми поясами.",
    },
    {
        "kind": "flow",
        "eyebrow": "04 · Путь исполнителя",
        "title": "От «нужна подработка» до денег на карте",
        "lead": "Пять шагов, ни один не требует резюме и звонка рекрутёру.",
        "steps": [
            ("Открыл", "Витрина: смены на сегодня и завтра, средняя оплата, "
                       "категории и быстрый выбор района."),
            ("Выбрал", "Фильтры по метро/МЦД, дате, оплате, выплате, «без опыта» "
                       "и проверенным заказчикам."),
            ("Откликнулся", "Записка в один клик. Лимит бесплатного тарифа — "
                            "5 откликов в день, PRO — безлимит."),
            ("Вышел", "Работодатель принял: адрес, время, чат, напоминания."),
            ("Получил", "Смена закрыта — выплата в кабинете, взаимная оценка "
                        "и рост рейтинга."),
        ],
        "metrics": [("1 клик", "на отклик"), ("5 в день", "бесплатный лимит"),
                    ("100%", "оплата за смену"), ("1–5 ★", "честный рейтинг")],
    },
    {
        "kind": "flow",
        "eyebrow": "05 · Путь работодателя",
        "title": "Бригада на смену за один вечер",
        "lead": "Публикация, воронка кандидатов, закрытие смены и оценка — "
                "в одном экране кабинета.",
        "steps": [
            ("Опубликовал", "Форма с авторасчётом ставки в час, командный набор "
                            "«N из M», бейджи «Срочно» и «Питание»."),
            ("Собрал отклики", "Кандидаты с рейтингом, индексом выходов, медкнижкой "
                               "и статусом самозанятости."),
            ("Выбрал", "PRO-исполнители показываются выше. Принятие и отказ — "
                       "одной кнопкой, с уведомлением."),
            ("Закрыл", "Смена закрыта: слоты, выплаты и статистика обновляются. "
                       "Копия смены создаётся на завтра в один клик."),
        ],
        "metrics": [("1 минута", "на публикацию"), ("20", "вакансий на «Бизнес»"),
                    ("3 сценария", "тарифа: 0 / 299 / 1 990 ₽"), ("1 клик", "клонирование")],
    },
    {
        "kind": "content",
        "eyebrow": "06 · Доверие",
        "title": "Рейтинг, который нельзя купить",
        "lead": "Доверие — главный дефицит на рынке сменного персонала. "
                "Поэтому модерация встроена в продукт, а не прикручена сбоку.",
        "bullets": [
            ("Взаимные оценки", "Рабочий и работодатель оценивают друг друга после смены. "
                                "Отзыв виден только после проверки."),
            ("Очередь модерации", "Каждый отзыв проходит одобрение. Рейтинг пересчитывается "
                                  "мгновенно, отклонённые оценки не влияют."),
            ("Индекс выходов", "Show-up rate: доля смен, на которые исполнитель действительно "
                               "вышел. Виден работодателю до принятия."),
            ("Верификация", "Статус «Проверенный» для компаний и исполнителей. "
                            "Медкнижка и самозанятость — в профиле."),
        ],
        "note": "В демо-версии рейтинг работодателя уже 4,9 при 27 свободных местах — "
                "это живые данные сидов, а не картинка.",
    },
    {
        "kind": "table",
        "eyebrow": "07 · Монетизация",
        "title": "Тарифы с реальными лимитами",
        "lead": "Платит тот, кто получает ценность быстрее: работодатель за поток смен, "
                "исполнитель — за приоритет и безлимит.",
        "columns": ["Тариф", "Роль", "Цена", "Лимит"],
        "rows": [
            ["Бесплатный", "Рабочий", "0 ₽", "5 откликов в день"],
            ["Про", "Рабочий", "299 ₽/мес", "Безлимит откликов"],
            ["Старт", "Работодатель", "0 ₽", "1 активная вакансия"],
            ["Бизнес", "Работодатель", "1 990 ₽/мес", "До 20 вакансий"],
        ],
        "bullets": [
            ("Комиссия с заработка", "0% — обещание, которое проверяется в UI "
                                     "и в модели данных."),
            ("Лимиты — не заглушка", "API реально возвращает ошибку TARIFF_LIMIT "
                                     "и предлагает апгрейд."),
            ("Админ может менять", "Цена и лимит любого тарифа редактируются "
                                   "в админ-панели без деплоя."),
        ],
    },
    {
        "kind": "metrics",
        "eyebrow": "08 · Метрики",
        "title": "Что мерим, чтобы понять, что работает",
        "lead": "Метрики MVP разложены по трём этапам воронки смены.",
        "groups": [
            ("Спрос",
             ["Активные смены в день",
              "Свободные места на смену",
              "Средняя оплата смены: 5 033 ₽",
              "Доля смен с бейджем «Срочно»",
              "Категории с дефицитом исполнителей"],
             "Цель пилота: 40 смен в день"),
            ("Отклик",
             ["Конверсия просмотра в отклик",
              "Time-to-fill: часы до полной бригады",
              "Доля откликов PRO-подписчиков",
              "Отказы после принятия",
              "Повторные отклики одного исполнителя"],
             "Цель: бригада за 3 часа"),
            ("Смена",
             ["Show-up rate: целевой уровень 95%",
              "Доля закрытых смен",
              "Повторный выход через 30 дней",
              "Доля отзывов на модерации",
              "Средняя оценка после смены"],
             "Цель: 95% выходов"),
        ],
        "note": "Деньги: ARPU работодателя, конверсия Бесплатный → Бизнес, "
                "доля PRO среди активных исполнителей.",
    },
    {
        "kind": "content",
        "eyebrow": "09 · Архитектура",
        "title": "Один код — два режима",
        "lead": "Full-stack с API и SQLite для разработки; автономная сборка "
                "в один HTML — для GitHub Pages и телефона.",
        "bullets": [
            ("Фронтенд", "React 18, TypeScript strict, Tailwind CSS, lucide-react. "
                         "Шрифты Manrope и Unbounded лежат локально — ноль внешних ассетов."),
            ("Бэкенд", "Node 22, Express, встроенный node:sqlite без нативных зависимостей. "
                       "10 таблиц, сиды, WAL-режим, 22 эндпоинта."),
            ("Офлайн", "browserDb повторяет те же эндпоинты на localStorage. "
                       "Демо живёт на статическом хостинге и с телефона без интернета."),
            ("Проверки", "tsc --noEmit, сборка, статическая сборка, smoke-тест /api/health "
                         "в GitHub Actions."),
        ],
        "note": "Один контракт данных: src/lib/api.ts — единственная точка доступа, "
                "поэтому UI не знает, откуда пришли данные.",
    },
    {
        "kind": "gallery",
        "eyebrow": "10 · Демо",
        "title": "Посмотреть можно прямо сейчас",
        "lead": "Интерактивное демо работает без сервера: данные хранятся в браузере, "
                "роль переключается одним нажатием.",
        "shots": [
            ("screenshots/02-jobs-search.png", "Поиск смен"),
            ("screenshots/05-cabinet-employer.png", "Кабинет работодателя"),
            ("screenshots/06-admin-moderation.png", "Модерация"),
        ],
        "facts": [
            ("Демо", f"{SITE}/app.html"),  # абсолютная ссылка: работает из любого места
            ("Android ZIP", f"{SITE}/downloads/podrabotka-msk-android-preview.zip"),
            ("Код", REPO),
            ("Локально", "npm install && npm run dev → localhost:3000"),
        ],
    },
    {
        "kind": "split",
        "eyebrow": "11 · Дорожная карта",
        "title": "Что дальше",
        "lead": "MVP отвечает на вопрос «работает ли модель». Дальше — инфраструктура "
                "продакшена и выход в новые города.",
        "left_title": "Ближайшие шаги",
        "left": [
            "SMS-аутентификация и сессии вместо демо-заголовка",
            "PostgreSQL и миграции, вынос API в отдельный сервис",
            "Выплаты через СБП и интеграция с самозанятостью",
            "Push-уведомления и realtime-чат",
            "Админ-аналитика: конверсия, стоимость смены, отток",
        ],
        "right_title": "Что уже работает",
        "right": [
            "Три роли и полный цикл смены: публикация → отклик → закрытие",
            "Тарифы с лимитами и апгрейдом",
            "Модерация отзывов и пересчёт рейтингов",
            "Офлайн-сборка и мобильный интерфейс",
            "CI: типы, сборка, smoke-тест API",
        ],
        "note": "Ограничения MVP: демо-аутентификация, платежи не подключены, "
                "SQLite на один инстанс, все данные вымышлены.",
    },
    {
        "kind": "closing",
        "eyebrow": "12 · Итог",
        "title": "Подработка.МСК",
        "subtitle": "Смены на сегодня и завтра — рядом с домом",
        "facts": [
            ("Демо", "Открывается в браузере, без регистрации"),
            ("Презентация", "PDF и HTML-версия в репозитории"),
            ("Исходники", "MIT, Node ≥ 20, TypeScript strict"),
            ("Контакты", REPO),
        ],
        "cta_line": f"{SITE}/app.html",
    },
]


def strip_emoji(text: str) -> str:
    """Готовит текст к PDF: убирает эмодзи и заменяет знаки, которых нет в субсетах шрифтов."""
    text = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF]", "", str(text))
    for source, target in {
        "✓": "=",
        "→": "->",
        "›": ">",
        "‹": "<",
        "₽": "руб.",
        "★": "*",
        "☆": "*",
        "≥": "от",
        "≤": "до",
    }.items():
        text = text.replace(source, target)
    return text.strip()


# --------------------------------------------------------------------------
# Шрифты: объединяем latin + cyrillic субсеты и режем до нужного набора знаков
# --------------------------------------------------------------------------
def prepare_fonts() -> dict[str, str]:
    from fontTools import subset
    from fontTools.merge import Merger
    from fontTools.ttLib import TTFont

    charset = set()
    for slide in SPEAKER_SLIDES:
        text = "".join(_collect_text(slide))
        charset.update(text)
    # всегда включаем полные алфавиты: иначе редкая буква (У, Я, Ё) выпадет
    # из сабсета и reportlab подставит чужой глиф
    charset.update(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
        " .,:;!?()[]{}<>/\\-–—_+=*&%#@'\"«»…₽№°"
    )
    charset.discard("\n")
    unicodes = sorted({ord(ch) for ch in charset if ord(ch) > 31})

    cache_dir = ROOT / ".cache-presentation"
    cache_dir.mkdir(exist_ok=True)
    result: dict[str, str] = {}

    for family, weight in [
        ("manrope", "500"),
        ("manrope", "700"),
        ("manrope", "800"),
        ("unbounded", "700"),
        ("unbounded", "800"),
    ]:
        out = cache_dir / f"{family}-{weight}.ttf"
        paths = [
            str(FONT_DIR / f"{family}-latin-{weight}-normal.woff2"),
            str(FONT_DIR / f"{family}-cyrillic-{weight}-normal.woff2"),
        ]
        merged = Merger().merge(paths)
        buf = io.BytesIO()
        merged.save(buf)
        buf.seek(0)

        font = TTFont(buf)
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        opts.recalc_bounds = True
        opts.drop_tables += ["DSIG"]
        sub = subset.Subsetter(options=opts)
        sub.populate(unicodes=unicodes)
        sub.subset(font)

        family_name = "Manrope" if family == "manrope" else "Unbounded"
        subfamily = {"500": "Medium", "700": "Bold", "800": "ExtraBold"}[weight]
        for name_id, value in [
            (1, family_name),
            (2, subfamily),
            (4, f"{family_name} {subfamily}"),
            (6, f"{family_name}-{subfamily}"),
            (16, family_name),
            (17, subfamily),
        ]:
            font["name"].setName(value, name_id, 3, 1, 0x409)
            font["name"].setName(value, name_id, 1, 0, 0)

        font.save(out)
        result[f"{family}-{weight}"] = str(out)

    return result


def _collect_text(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _collect_text(value)
    elif isinstance(node, (list, tuple)):
        for item in node:
            yield from _collect_text(item)


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
W, H = 1280.0, 720.0
MARGIN = 74.0
CONTENT_W = W - MARGIN * 2


def build_pdf(fonts: dict[str, str]) -> Path:
    """Раскладка по потоку: блоки идут друг за другом, карточки растягиваются
    на доступную высоту — поэтому слайды заполняются равномерно."""
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont as RLTTFont
    from reportlab.pdfgen import canvas

    pdfmetrics.registerFont(RLTTFont("Manrope-Medium", fonts["manrope-500"]))
    pdfmetrics.registerFont(RLTTFont("Manrope-Bold", fonts["manrope-700"]))
    pdfmetrics.registerFont(RLTTFont("Manrope-ExtraBold", fonts["manrope-800"]))
    pdfmetrics.registerFont(RLTTFont("Unbounded-Bold", fonts["unbounded-700"]))
    pdfmetrics.registerFont(RLTTFont("Unbounded-ExtraBold", fonts["unbounded-800"]))

    out_path = OUT_DIR / "podrabotka-msk-deck.pdf"
    c = canvas.Canvas(str(out_path), pagesize=(W, H))
    c.setTitle("Подработка.МСК — платформа быстрых смен")
    c.setAuthor("Подработка.МСК")
    c.setSubject("Продуктовая презентация MVP")
    c.setKeywords("подработка, смены, Москва, маркетплейс, MVP")

    def color(hex_value: str):
        return HexColor(hex_value)

    def text_of(value) -> str:
        return strip_emoji(value)

    def wrap(text: str, font: str, size: float, width: float) -> list[str]:
        words = text_of(text).split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if pdfmetrics.stringWidth(candidate, font, size) <= width or not current:
                current = candidate
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw_paragraph(text, x, y, width, font, size, hex_color, leading=None, max_lines=24):
        leading = leading or size * 1.45
        lines = wrap(text, font, size, width)
        c.setFont(font, size)
        c.setFillColor(color(hex_color))
        for index, line in enumerate(lines[:max_lines]):
            c.drawString(x, y - index * leading, line)
        return y - min(len(lines), max_lines) * leading

    def draw_eyebrow(text, x, y):
        c.setFont("Unbounded-Bold", 9.5)
        c.setFillColor(color(BRAND))
        c.drawString(x, y, text_of(text).upper())

    def slide_background(soft=False, dark=False):
        c.setFillColor(color(INK if dark else (SOFT if soft else WHITE)))
        c.rect(0, 0, W, H, stroke=0, fill=1)
        c.setFillColor(color("#15151C" if dark else BRAND_SOFT))
        for index in range(30):
            c.setFillAlpha(0.10 if dark else 0.05)
            c.circle(W - 30 - index * 9, H + 40 - index * 9, 250 - index * 7, stroke=0, fill=1)
        c.setFillAlpha(1)

    def footer(page_num: int, dark=False):
        c.setStrokeColor(color("#2A2A33" if dark else LINE))
        c.setLineWidth(0.8)
        c.line(MARGIN, 52, W - MARGIN, 52)
        c.setFont("Manrope-Medium", 9.5)
        c.setFillColor(color("#8A8A99" if dark else INK_400))
        c.drawString(MARGIN, 34, "Подработка.МСК · платформа быстрых смен")
        c.drawRightString(W - MARGIN, 34, f"{page_num:02d} / {len(SPEAKER_SLIDES):02d}")

    def image_cover(path: Path, x, y, w, h, radius=0):
        image = ImageReader(str(path))
        iw, ih = image.getSize()
        scale = max(w / iw, h / ih)
        dw, dh = iw * scale, ih * scale
        c.saveState()
        p = c.beginPath()
        if radius:
            p.roundRect(x, y, w, h, radius)
        else:
            p.rect(x, y, w, h)
        c.clipPath(p, stroke=0, fill=0)
        c.drawImage(image, x + (w - dw) / 2, y + (h - dh) / 2, width=dw, height=dh, mask="auto")
        c.restoreState()

    def card(x, y, w, h, fill=WHITE, border=LINE, radius=14, shadow=True):
        if shadow:
            c.setFillColor(HexColor("#111115"))
            c.setFillAlpha(0.03)
            c.roundRect(x + 2, y - 3, w, h, radius, stroke=0, fill=1)
            c.setFillAlpha(1)
        c.setFillColor(color(fill))
        c.setStrokeColor(color(border))
        c.setLineWidth(1)
        c.roundRect(x, y, w, h, radius, stroke=1, fill=1)

    def page_layout(page_num: int, eyebrow_text: str, title_text: str):
        """Возвращает Y верхней границы контентной области."""
        draw_eyebrow(eyebrow_text, MARGIN, H - 84)
        title_size = 31
        title_lines = wrap(title_text, "Unbounded-Bold", title_size, CONTENT_W - 170)
        c.setFont("Unbounded-Bold", title_size)
        c.setFillColor(color(INK))
        y = H - 138
        for line in title_lines:
            c.drawString(MARGIN, y, line)
            y -= title_size * 1.2
        return y - 4

    def lead_block(y, lead: str, width_ratio=0.78):
        return draw_paragraph(text_of(lead), MARGIN, y, CONTENT_W * width_ratio,
                              "Manrope-Medium", 13.5, INK_500, leading=19.6) - 6

    def note_block(note: str, dark=False):
        if not note:
            return
        c.setFillColor(color("#1A1A22" if dark else BRAND_TINT))
        c.setStrokeColor(color("#2A2A33" if dark else BRAND_SOFT))
        c.roundRect(MARGIN, 66, CONTENT_W, 42, 10, stroke=1, fill=1)
        draw_paragraph(text_of(note), MARGIN + 16, 90, CONTENT_W - 32, "Manrope-Medium", 10.4,
                       "#C9C9D4" if dark else INK_500, leading=13.4, max_lines=2)

    def metric_tiles(y, items, height=74):
        """Полоса «значение + подпись»; y — верхняя граница."""
        gap = 12
        w = (CONTENT_W - gap * (len(items) - 1)) / len(items)
        for index, (value, label) in enumerate(items):
            x = MARGIN + index * (w + gap)
            card(x, y - height, w, height, fill=BRAND_TINT, border=BRAND_SOFT, radius=12, shadow=False)
            c.setFont("Unbounded-ExtraBold", 17)
            c.setFillColor(color(BRAND_DARK))
            c.drawString(x + 16, y - 32, text_of(value))
            c.setFont("Manrope-Medium", 10.2)
            c.setFillColor(color(INK_500))
            c.drawString(x + 16, y - 51, text_of(label))
        return y - height

    def item_card(x, y, w, h, label, text, label_font="Unbounded-Bold", label_size=11.4,
                  body_size=10.9, accent=True):
        card(x, y, w, h)
        inner_x = x + 20
        inner_w = w - 40
        inner_top = y + h - 26
        if accent:
            c.setFillColor(color(BRAND))
            c.roundRect(inner_x - 8, inner_top - 11, 3.4, 15, 1.7, stroke=0, fill=1)
        c.setFont(label_font, label_size)
        c.setFillColor(color(INK))
        c.drawString(inner_x + (6 if accent else 0), inner_top - 11, text_of(label))
        draw_paragraph(text, inner_x + (6 if accent else 0), inner_top - 33, inner_w - (6 if accent else 0),
                       "Manrope-Medium", body_size, INK_500, leading=body_size * 1.4,
                       max_lines=max(2, int((h - 52) / (body_size * 1.4))))

    page = 0
    for slide in SPEAKER_SLIDES:
        page += 1
        kind = slide["kind"]
        dark = kind == "cover"
        slide_background(soft=kind in {"cards", "metrics", "split"}, dark=dark)

        # ---------------------------------------------------------------- COVER
        if kind == "cover":
            draw_eyebrow(slide["eyebrow"], MARGIN, H - 96)
            c.setFont("Unbounded-ExtraBold", 54)
            c.setFillColor(color(WHITE))
            c.drawString(MARGIN, H - 178, text_of(slide["title"]))
            c.setFont("Unbounded-Bold", 24)
            c.setFillColor(color("#F5A8CC"))
            for index, line in enumerate(wrap(slide["subtitle"], "Unbounded-Bold", 24, 520)):
                c.drawString(MARGIN, H - 226 - index * 30, line)

            c.setStrokeColor(color("#3A3A46"))
            c.setLineWidth(1)
            c.line(MARGIN, H - 296, MARGIN + 96, H - 296)
            draw_paragraph(slide["lead"], MARGIN, H - 336, 500, "Manrope-Medium", 14,
                           "#C9C9D4", leading=20.4)

            x = MARGIN
            for fact in slide["facts"]:
                label = text_of(fact)
                width = pdfmetrics.stringWidth(label, "Manrope-Bold", 11) + 28
                c.setFillColor(color("#22222B"))
                c.setStrokeColor(color("#3A3A46"))
                c.roundRect(x, H - 452, width, 30, 15, stroke=1, fill=1)
                c.setFont("Manrope-Bold", 11)
                c.setFillColor(color("#F5A8CC"))
                c.drawCentredString(x + width / 2, H - 443, label)
                x += width + 9

            card(MARGIN + 560, 118, 572, 430, fill="#FFFFFF", border="#2A2A33", radius=16, shadow=False)
            image_cover(ROOT / "screenshots" / "01-home-worker.png", MARGIN + 562, 120, 568, 426, radius=15)
            c.setFont("Manrope-Medium", 10)
            c.setFillColor(color("#8A8A99"))
            c.drawString(MARGIN, 84, text_of(slide["footer"]))
            footer(page, dark=True)
            c.showPage()
            continue

        top = page_layout(page, slide["eyebrow"], slide["title"])
        if slide.get("lead"):
            top = lead_block(top, slide["lead"])

        note = slide.get("note")
        floor = 132 if note else 96
        top = top - 22
        available = top - floor

        # ---------------------------------------------------------------- CONTENT
        if kind == "content":
            items = slide.get("bullets") or slide.get("steps") or []
            rows = max(1, (len(items) + 1) // 2)
            gap_x, gap_y = 20, 14
            col_w = (CONTENT_W - gap_x) / 2
            row_h = min(132, (available - gap_y * (rows - 1)) / rows)
            for index, (label, text) in enumerate(items):
                cx = MARGIN + (index % 2) * (col_w + gap_x)
                cy = top - row_h - (index // 2) * (row_h + gap_y)
                item_card(cx, cy, col_w, row_h, label, text)

        # ---------------------------------------------------------------- CARDS
        elif kind == "cards":
            gap = 20
            cw = (CONTENT_W - gap * 2) / 3
            ch = min(available, 336)
            cy = top - ch
            for index, card_data in enumerate(slide["cards"]):
                role, audience, items = card_data[0], card_data[1], card_data[2]
                highlight = card_data[3] if len(card_data) > 3 else None
                cx = MARGIN + index * (cw + gap)
                card(cx, cy, cw, ch, border=BRAND_SOFT if index == 1 else LINE)
                badge = text_of(role).upper()
                badge_w = pdfmetrics.stringWidth(badge, "Manrope-ExtraBold", 9) + 24
                c.setFillColor(color(BRAND_SOFT))
                c.roundRect(cx + 20, cy + ch - 48, badge_w, 23, 11.5, stroke=0, fill=1)
                c.setFont("Manrope-ExtraBold", 9)
                c.setFillColor(color(BRAND_DARK))
                c.drawString(cx + 32, cy + ch - 41, badge)

                c.setFont("Unbounded-Bold", 13.5)
                c.setFillColor(color(INK))
                c.drawString(cx + 20, cy + ch - 80, text_of(audience))

                y = cy + ch - 110
                for item in items:
                    c.setFillColor(color(BRAND))
                    c.circle(cx + 24, y + 3.4, 2.5, stroke=0, fill=1)
                    y = draw_paragraph(item, cx + 34, y, cw - 58, "Manrope-Medium", 10.6,
                                       INK_700, leading=14.2, max_lines=2) - 5

                if highlight:
                    chip = text_of(highlight)
                    chip_w = pdfmetrics.stringWidth(chip, "Manrope-Bold", 9.4) + 26
                    c.setFillColor(color(BRAND_TINT))
                    c.setStrokeColor(color(BRAND_SOFT))
                    c.roundRect(cx + 20, cy + 18, chip_w, 28, 14, stroke=1, fill=1)
                    c.setFont("Manrope-Bold", 9.4)
                    c.setFillColor(color(BRAND_DARK))
                    c.drawCentredString(cx + 20 + chip_w / 2, cy + 27, chip)
            top = cy - 18

        # ---------------------------------------------------------------- FLOW
        elif kind == "flow":
            steps = slide["steps"]
            gap = 13
            cw = (CONTENT_W - gap * (len(steps) - 1)) / len(steps)
            ch = min(available - 92, 208)
            cy = top - ch
            for index, (label, text) in enumerate(steps):
                cx = MARGIN + index * (cw + gap)
                card(cx, cy, cw, ch)
                c.setFont("Unbounded-ExtraBold", 14.5)
                c.setFillColor(color(BRAND))
                c.drawString(cx + 16, cy + ch - 34, f"{index + 1:02d}")
                c.setStrokeColor(color(LINE))
                c.setLineWidth(0.7)
                c.line(cx + 16, cy + ch - 44, cx + cw - 16, cy + ch - 44)
                c.setFont("Unbounded-Bold", 11.2)
                c.setFillColor(color(INK))
                for line_index, line in enumerate(wrap(label, "Unbounded-Bold", 11.2, cw - 32)):
                    c.drawString(cx + 16, cy + ch - 64 - line_index * 16, line)
                draw_paragraph(text, cx + 16, cy + ch - 96, cw - 32, "Manrope-Medium", 10.3,
                               INK_500, leading=13.8, max_lines=max(3, int((ch - 110) / 13.8)))
                if index < len(steps) - 1:
                    c.setFillColor(color(BRAND))
                    c.setFont("Manrope-Bold", 15)
                    c.drawString(cx + cw + 1.5, cy + ch / 2 - 3, ">")
            if slide.get("metrics"):
                metric_tiles(cy - 20, slide["metrics"], height=86)

        # ---------------------------------------------------------------- TABLE
        elif kind == "table":
            columns = slide["columns"]
            rows = slide["rows"]
            col_ratios = [0.30, 0.24, 0.20, 0.26]
            head_h = 34
            c.setFillColor(color(SOFT))
            c.roundRect(MARGIN, top - head_h, CONTENT_W, head_h, 8, stroke=0, fill=1)
            x = MARGIN + 16
            for index, name in enumerate(columns):
                c.setFont("Manrope-ExtraBold", 9.4)
                c.setFillColor(color(INK_500))
                c.drawString(x, top - 21, text_of(name).upper())
                x += CONTENT_W * col_ratios[index]

            row_y = top - head_h
            row_h = 46
            for row in rows:
                c.setStrokeColor(color(LINE))
                c.setLineWidth(0.7)
                c.line(MARGIN, row_y - row_h, MARGIN + CONTENT_W, row_y - row_h)
                x = MARGIN + 16
                for col_index, cell in enumerate(row):
                    primary = col_index == 0
                    c.setFont("Manrope-Bold" if primary else "Manrope-Medium", 11.6)
                    c.setFillColor(color(INK if primary else INK_700))
                    c.drawString(x, row_y - 28, text_of(cell))
                    x += CONTENT_W * col_ratios[col_index]
                row_y -= row_h

            bullets = slide.get("bullets") or []
            if bullets:
                bw = (CONTENT_W - 2 * 16) / 3
                bh = min(148, row_y - 24 - floor)
                for index, (label, text) in enumerate(bullets):
                    bx = MARGIN + index * (bw + 16)
                    card(bx, row_y - 24 - bh, bw, bh, fill=BRAND_TINT, border=BRAND_SOFT, radius=12,
                         shadow=False)
                    c.setFont("Unbounded-Bold", 10.4)
                    c.setFillColor(color(BRAND_DARK))
                    c.drawString(bx + 16, row_y - 24 - bh + bh - 24, text_of(label))
                    draw_paragraph(text, bx + 16, row_y - 24 - bh + bh - 48, bw - 32,
                                   "Manrope-Medium", 10.2, INK_500, leading=13.6, max_lines=4)

        # ---------------------------------------------------------------- METRICS
        elif kind == "metrics":
            groups = slide["groups"]
            gap = 20
            cw = (CONTENT_W - gap * 2) / 3
            ch = min(available, 296)
            cy = top - ch
            for index, group_data in enumerate(groups):
                group, items = group_data[0], group_data[1]
                target = group_data[2] if len(group_data) > 2 else None
                cx = MARGIN + index * (cw + gap)
                card(cx, cy, cw, ch)
                c.setFont("Unbounded-Bold", 13)
                c.setFillColor(color(INK))
                c.drawString(cx + 20, cy + ch - 36, text_of(group))
                c.setFillColor(color(BRAND))
                c.roundRect(cx + 20, cy + ch - 48, 36, 3, 1.5, stroke=0, fill=1)
                y = cy + ch - 76
                for item in items:
                    c.setFillColor(color(BRAND))
                    c.circle(cx + 24, y + 3.4, 2.4, stroke=0, fill=1)
                    y = draw_paragraph(item, cx + 34, y, cw - 58, "Manrope-Medium", 10.9, INK_700,
                                       leading=14.4, max_lines=2) - 6
                if target:
                    chip = text_of(target)
                    chip_w = pdfmetrics.stringWidth(chip, "Manrope-Bold", 9.2) + 26
                    c.setFillColor(color(BRAND_TINT))
                    c.setStrokeColor(color(BRAND_SOFT))
                    c.roundRect(cx + 20, cy + 18, chip_w, 28, 14, stroke=1, fill=1)
                    c.setFont("Manrope-Bold", 9.2)
                    c.setFillColor(color(BRAND_DARK))
                    c.drawCentredString(cx + 20 + chip_w / 2, cy + 27, chip)

        # ---------------------------------------------------------------- GALLERY
        elif kind == "gallery":
            shots = slide["shots"]
            gap = 16
            sw = (CONTENT_W - gap * (len(shots) - 1)) / len(shots)
            sh = min(available - 90, 300)
            sy = top - sh
            for index, (path, _label) in enumerate(shots):
                sx = MARGIN + index * (sw + gap)
                card(sx, sy, sw, sh, radius=12, shadow=False)
                image_cover(ROOT / path, sx + 1, sy + 1, sw - 2, sh - 2, radius=11)

            facts = slide["facts"]
            fy = sy - 18
            fw = (CONTENT_W - 3 * 14) / 4
            for index, (label, value) in enumerate(facts):
                fx = MARGIN + index * (fw + 14)
                card(fx, fy - 62, fw, 62, fill=BRAND_TINT, border=BRAND_SOFT, radius=11, shadow=False)
                c.setFont("Manrope-ExtraBold", 8.8)
                c.setFillColor(color(INK_500))
                c.drawString(fx + 14, fy - 24, text_of(label).upper())
                c.setFont("Manrope-Bold", 9.4)
                c.setFillColor(color(BRAND_DARK))
                for line_index, line in enumerate(wrap(value, "Manrope-Bold", 9.4, fw - 28)[:2]):
                    c.drawString(fx + 14, fy - 40 - line_index * 12, line)

        # ---------------------------------------------------------------- SPLIT
        elif kind == "split":
            col_w = (CONTENT_W - 24) / 2
            ch = min(available, 338)
            cy = top - ch
            for index, (heading, items) in enumerate(
                [(slide["left_title"], slide["left"]), (slide["right_title"], slide["right"])]
            ):
                cx = MARGIN + index * (col_w + 24)
                card(cx, cy, col_w, ch, border=BRAND_SOFT if index == 1 else LINE)
                c.setFont("Unbounded-Bold", 12.4)
                c.setFillColor(color(BRAND_DARK if index == 1 else INK))
                c.drawString(cx + 20, cy + ch - 36, text_of(heading))
                y = cy + ch - 66
                for item in items:
                    if index == 0:
                        c.setFillColor(color(BRAND))
                        c.circle(cx + 24, y + 3.6, 2.6, stroke=0, fill=1)
                        y = draw_paragraph(item, cx + 36, y, col_w - 58, "Manrope-Medium", 10.7,
                                           INK_700, leading=14.4, max_lines=3) - 6
                    else:
                        c.setStrokeColor(color(BRAND))
                        c.setLineWidth(1.4)
                        tick = c.beginPath()
                        tick.moveTo(cx + 21, y + 3)
                        tick.lineTo(cx + 24, y)
                        tick.lineTo(cx + 29, y + 7)
                        c.drawPath(tick, stroke=1, fill=0)
                        y = draw_paragraph(item, cx + 36, y, col_w - 58, "Manrope-Medium", 10.7,
                                           INK_700, leading=14.4, max_lines=3) - 6

        # ---------------------------------------------------------------- CLOSING
        elif kind == "closing":
            size = 40
            c.setFont("Unbounded-ExtraBold", size)
            c.setFillColor(color(INK))
            for index, line in enumerate(wrap(slide["subtitle"], "Unbounded-ExtraBold", size, CONTENT_W - 150)):
                c.drawString(MARGIN, top - 20 - index * 50, line)

            c.setFillColor(color(BRAND))
            c.roundRect(MARGIN, top - 96, 92, 5, 2.5, stroke=0, fill=1)

            y = top - 148
            for label, value in slide["facts"]:
                c.setFont("Manrope-ExtraBold", 9)
                c.setFillColor(color(INK_400))
                c.drawString(MARGIN, y, text_of(label).upper())
                c.setFont("Manrope-Bold", 12)
                c.setFillColor(color(INK_700))
                c.drawString(MARGIN + 150, y, text_of(value))
                y -= 32

            c.setFillColor(color(BRAND_TINT))
            c.setStrokeColor(color(BRAND_SOFT))
            c.roundRect(MARGIN, 132, 600, 64, 14, stroke=1, fill=1)
            c.setFont("Unbounded-Bold", 14)
            c.setFillColor(color(BRAND_DARK))
            c.drawString(MARGIN + 22, 158, text_of(slide["cta_line"]))

            card(W - MARGIN - 388, 118, 388, 220, radius=14, shadow=False)
            image_cover(ROOT / "screenshots" / "og-cover.png", W - MARGIN - 387, 119, 386, 218, radius=13)

        note_block(note, dark=dark)
        footer(page, dark=dark)
        c.showPage()

    c.save()
    return out_path


# --------------------------------------------------------------------------
# HTML-версия
# --------------------------------------------------------------------------
def font_face_css(fonts: dict[str, str]) -> str:
    from fontTools.ttLib import TTFont

    faces = []
    for key, family, weight in [
        ("manrope-500", "Manrope", 500),
        ("manrope-700", "Manrope", 700),
        ("manrope-800", "Manrope", 800),
        ("unbounded-700", "Unbounded", 700),
        ("unbounded-800", "Unbounded", 800),
    ]:
        ttf = TTFont(fonts[key])
        buf = io.BytesIO()
        ttf.flavor = "woff2"
        ttf.save(buf)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        faces.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%d;font-display:swap;"
            "src:url(data:font/woff2;base64,%s) format('woff2')}" % (family, weight, encoded)
        )
    return "\n".join(faces)


HTML_CSS = """
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;height:100%;background:#0C0C11;color:#111115;
  font-family:'Manrope',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
body{overflow:hidden}
.deck{height:100%;width:100%;display:grid;place-items:center}
.slide-stage{position:relative;width:min(100vw,177.78vh);height:min(56.25vw,100vh);
  box-shadow:0 30px 80px rgba(0,0,0,.5);background:#fff;overflow:hidden}
.slide{position:absolute;inset:0;padding:6.2% 5.9% 5.6%;display:none;flex-direction:column;
  background:#fff;color:#111115}
.slide.active{display:flex;animation:fade .28s ease-out both}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.slide::after{content:'';position:absolute;right:-12%;top:-34%;width:52%;height:92%;
  background:radial-gradient(closest-side,rgba(252,231,241,.85),rgba(252,231,241,0) 72%);
  pointer-events:none}
.slide.soft{background:#F7F7FA}
.slide.dark{background:#111115;color:#fff}
.slide.dark::after{background:radial-gradient(closest-side,rgba(216,35,118,.22),rgba(216,35,118,0) 70%)}
.eyebrow{font-family:'Unbounded',sans-serif;font-weight:700;font-size:.79vw;letter-spacing:.14em;
  text-transform:uppercase;color:#D82376;margin-bottom:1.4vh}
.slide.dark .eyebrow{color:#F5A8CC}
h2{font-family:'Unbounded',sans-serif;font-weight:700;font-size:2.14vw;line-height:1.18;
  letter-spacing:-.025em;margin:0 0 1.4vh;max-width:88%}
.lead{font-size:1.02vw;line-height:1.62;color:#6B7280;max-width:74%;margin:0 0 2.6vh}
.slide.dark .lead{color:#C9C9D4}
.body{flex:1;min-height:0;position:relative;z-index:1}
.note{margin-top:auto;font-size:.79vw;line-height:1.55;color:#6B7280;background:#FDF2F7;
  border:1px solid #FCE7F1;border-radius:.7vw;padding:1.1vh 1.3vw}
.slide.dark .note{background:#1A1A22;border-color:#2A2A33;color:#C9C9D4}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:1.5vw}
.card{background:#fff;border:1px solid #E8E8EF;border-radius:1vw;padding:1.8vh 1.5vw;
  box-shadow:0 2px 14px rgba(17,17,21,.04)}
.card h3{font-family:'Unbounded',sans-serif;font-size:.92vw;margin:0 0 .7vh;font-weight:700;
  letter-spacing:-.01em}
.card h3::before{content:'';display:inline-block;width:.26vw;height:.85vw;background:#D82376;
  border-radius:.2vw;margin-right:.6vw;vertical-align:-.08vw}
.card p{margin:0;font-size:.83vw;line-height:1.62;color:#6B7280}
.cards3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.4vw;height:100%}
.cards3 .card{display:flex;flex-direction:column;padding:2.1vh 1.6vw}
.badge{align-self:flex-start;font-size:.68vw;font-weight:800;letter-spacing:.1em;
  text-transform:uppercase;color:#BA1762;background:#FCE7F1;border-radius:1vw;
  padding:.45vh .8vw;margin-bottom:1.5vh}
.cards3 .card h3{font-size:1.06vw;margin-bottom:.35vh}
.cards3 .card .aud{font-size:.75vw;color:#9CA3AF;margin-bottom:1.6vh}
.cards3 ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:.85vh}
.cards3 li{position:relative;padding-left:1vw;font-size:.82vw;line-height:1.5;color:#34343E}
.cards3 li::before{content:'';position:absolute;left:0;top:.55em;width:.32vw;height:.32vw;
  border-radius:50%;background:#D82376}
.flow{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:1vw;height:auto}
.flow .card{padding:1.9vh 1vw;position:relative}
.flow .num{font-family:'Unbounded',sans-serif;font-weight:800;font-size:.95vw;color:#D82376}
.flow h3{font-size:.88vw;margin:.5vh 0 .8vh;line-height:1.3}
.flow h3::before{display:none}
.flow p{font-size:.76vw;line-height:1.55}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:.8vw;margin-top:1.7vh}
.metric{background:#FDF2F7;border:1px solid #FCE7F1;border-radius:.75vw;padding:1.2vh 1vw}
.metric b{display:block;font-family:'Unbounded',sans-serif;font-size:1.02vw;color:#BA1762;
  letter-spacing:-.02em}
.metric span{font-size:.72vw;color:#6B7280}
table{width:100%;border-collapse:collapse;font-size:.86vw}
th{text-align:left;font-size:.68vw;letter-spacing:.09em;text-transform:uppercase;color:#6B7280;
  background:#F7F7FA;padding:.9vh .9vw;border-radius:.4vw}
td{padding:1.15vh .9vw;border-bottom:1px solid #E8E8EF;color:#34343E}
td:first-child{font-weight:800;color:#111115}
.triple{display:grid;grid-template-columns:repeat(3,1fr);gap:1vw;margin-top:2.2vh}
.triple .card{background:#FDF2F7;border-color:#FCE7F1}
.triple h3{font-size:.82vw;color:#BA1762}
.triple h3::before{display:none}
.triple p{font-size:.76vw}
.groups{display:grid;grid-template-columns:repeat(3,1fr);gap:1.4vw;height:100%}
.groups .card{padding:2vh 1.5vw}
.groups h3{font-size:1vw}
.groups .rule{width:2.4vw;height:.2vw;background:#D82376;border-radius:1vw;margin:.2vh 0 1.6vh}
.groups ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:1.1vh}
.groups li{position:relative;padding-left:1vw;font-size:.82vw;line-height:1.5;color:#34343E}
.groups li::before{content:'';position:absolute;left:0;top:.55em;width:.32vw;height:.32vw;
  border-radius:50%;background:#D82376}
.gallery{display:grid;grid-template-columns:repeat(3,1fr);gap:1vw;height:56%}
.gallery figure{margin:0;border:1px solid #E8E8EF;border-radius:.9vw;overflow:hidden;background:#fff}
.gallery img{width:100%;height:100%;object-fit:cover}
.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:.9vw;margin-top:1.6vh}
.facts div{background:#FDF2F7;border:1px solid #FCE7F1;border-radius:.7vw;padding:1.1vh 1vw}
.facts b{display:block;font-size:.64vw;letter-spacing:.1em;text-transform:uppercase;color:#6B7280;
  margin-bottom:.4vh}
.facts span{font-size:.72vw;color:#BA1762;word-break:break-all}
.split{display:grid;grid-template-columns:1fr 1fr;gap:1.4vw;height:100%}
.split .card{padding:2.1vh 1.6vw}
.split ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:1.35vh}
.split li{position:relative;padding-left:1.5vw;font-size:.84vw;line-height:1.5;color:#34343E}
.split li::before{content:'→';position:absolute;left:0;color:#D82376;font-weight:800}
.split .card.ok{border-color:#FCE7F1;background:#FFFBFD}
.split .card.ok li::before{content:'✓'}
.cover{background:#111115;color:#fff;justify-content:center}
.cover h2{font-size:3.6vw;margin-bottom:.6vh;max-width:none}
.cover .sub{font-family:'Unbounded',sans-serif;font-size:1.32vw;color:#F5A8CC;margin-bottom:2.4vh;
  font-weight:700;letter-spacing:-.01em}
.cover .lead{color:#C9C9D4;max-width:44%;font-size:.98vw}
.cover .rule{width:6vw;height:.25vw;background:#3A3A46;margin:2vh 0}
.cover .pills{display:flex;gap:.6vw;margin-top:2.6vh}
.pill{border:1px solid #3A3A46;background:#22222B;color:#F5A8CC;border-radius:2vw;
  padding:.7vh 1.1vw;font-size:.74vw;font-weight:700}
.cover .browser{position:absolute;right:5.9%;top:50%;transform:translateY(-50%);
  width:44%;border-radius:1vw;overflow:hidden;border:1px solid #2A2A33;
  box-shadow:0 30px 60px rgba(0,0,0,.5);background:#fff}
.cover .browser img{width:100%;display:block}
.cover .foot{position:absolute;left:5.9%;bottom:9%;font-size:.72vw;color:#8A8A99}
.closing .brandmark{font-family:'Unbounded',sans-serif;font-weight:800;font-size:2.6vw;
  letter-spacing:-.035em;margin-top:4vh}
.closing .brandmark b{color:#D82376}
.closing h2{font-size:2.9vw;margin:1.6vh 0 1.2vh}
.closing .rule{width:7vw;height:.28vw;background:#D82376;margin-bottom:3.4vh}
.closing dl{display:grid;grid-template-columns:10vw 1fr;gap:1.5vh 0;margin:0;font-size:.88vw}
.closing dt{font-size:.66vw;letter-spacing:.11em;text-transform:uppercase;color:#9CA3AF;
  align-self:center}
.closing dd{margin:0;font-weight:700;color:#34343E;word-break:break-all}
.closing .cta{position:absolute;left:5.9%;bottom:12%;background:#FDF2F7;border:1px solid #FCE7F1;
  border-radius:.9vw;padding:1.6vh 1.8vw;font-family:'Unbounded',sans-serif;font-weight:700;
  font-size:1.02vw;color:#BA1762}
.closing .og{position:absolute;right:5.9%;bottom:12%;width:30%;border-radius:.9vw;
  border:1px solid #E8E8EF;box-shadow:0 18px 40px rgba(17,17,21,.12)}
.footer{position:absolute;left:5.9%;right:5.9%;bottom:2.6%;display:flex;justify-content:space-between;
  font-size:.7vw;color:#9CA3AF;border-top:1px solid #E8E8EF;padding-top:1.1vh}
.slide.dark .footer{color:#8A8A99;border-color:#2A2A33}
.nav{position:fixed;left:50%;bottom:14px;transform:translateX(-50%);display:flex;align-items:center;
  gap:10px;background:rgba(20,20,26,.86);backdrop-filter:blur(10px);border:1px solid #2A2A33;
  border-radius:999px;padding:7px 12px;color:#EDEDF2;font-size:12px;z-index:10}
.nav button{background:transparent;border:0;color:#EDEDF2;font-size:15px;cursor:pointer;
  width:28px;height:28px;border-radius:50%;display:grid;place-items:center}
.nav button:hover{background:#2A2A33}
.nav .pos{min-width:52px;text-align:center;font-variant-numeric:tabular-nums}
.nav .bar{width:120px;height:3px;background:#2A2A33;border-radius:2px;overflow:hidden}
.nav .bar i{display:block;height:100%;width:8%;background:#D82376;transition:width .25s ease}
.hint{position:fixed;left:18px;bottom:16px;color:#6B7280;font-size:11px;z-index:10}
@media (max-width:820px){.hint{display:none}}
@media print{
  body{overflow:visible;background:#fff}
  .nav,.hint{display:none}
  .slide-stage{width:100%;height:auto;box-shadow:none}
  .slide{position:relative;display:flex !important;height:56.25vw;page-break-after:always;
    animation:none}
  @page{size:landscape;margin:0}
}
"""

HTML_JS = """
const slides=[...document.querySelectorAll('.slide')];
const pos=document.querySelector('.nav .pos');
const bar=document.querySelector('.nav .bar i');
let index=0;
function show(next){
  index=Math.max(0,Math.min(slides.length-1,next));
  slides.forEach((s,i)=>s.classList.toggle('active',i===index));
  pos.textContent=(index+1)+' / '+slides.length;
  bar.style.width=(((index+1)/slides.length)*100)+'%';
}
document.querySelector('.nav .prev').addEventListener('click',()=>show(index-1));
document.querySelector('.nav .next').addEventListener('click',()=>show(index+1));
document.addEventListener('keydown',(event)=>{
  if(['ArrowRight','ArrowDown','PageDown',' '].includes(event.key)){event.preventDefault();show(index+1);}
  if(['ArrowLeft','ArrowUp','PageUp'].includes(event.key)){event.preventDefault();show(index-1);}
  if(event.key==='Home')show(0);
  if(event.key==='End')show(slides.length-1);
});
document.addEventListener('click',(event)=>{
  if(event.target.closest('a,button'))return;
  show(index + (event.clientX > window.innerWidth/2 ? 1 : -1));
});
show(0);
"""


def esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_slide_html(slide: dict) -> str:
    kind = slide["kind"]
    classes = ["slide"]
    if kind == "cover":
        classes.append("cover")
    if kind in {"cards", "metrics", "split"}:
        classes.append("soft")
    body = ""

    if kind == "cover":
        pills = "".join(f'<span class="pill">{esc(p)}</span>' for p in slide["facts"])
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <div class="sub">{esc(slide['subtitle'])}</div>
  <div class="rule"></div>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="pills">{pills}</div>
  <div class="browser"><img src="../screenshots/01-home-worker.png" alt="Главный экран приложения"></div>
  <div class="foot">{esc(slide['footer'])}</div>"""
    elif kind == "content":
        grid = "".join(
            f'<div class="card"><h3>{esc(label)}</h3><p>{esc(text)}</p></div>'
            for label, text in (slide.get("bullets") or slide.get("steps") or [])
        )
        note = f'<div class="note">{esc(slide["note"])}</div>' if slide.get("note") else ""
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="body"><div class="grid2">{grid}</div></div>
  {note}"""
    elif kind == "cards":
        cards = "".join(
            f"""<div class="card">
        <span class="badge">{esc(role)}</span>
        <h3>{esc(audience)}</h3>
        <div class="aud">в демо-данных есть готовый профиль</div>
        <ul>{''.join(f'<li>{esc(i)}</li>' for i in items)}</ul>
      </div>"""
            for role, audience, items, *_rest in slide["cards"]
        )
        note = f'<div class="note">{esc(slide["note"])}</div>' if slide.get("note") else ""
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="body"><div class="cards3">{cards}</div></div>
  {note}"""
    elif kind == "flow":
        steps = "".join(
            f'<div class="card"><div class="num">{i + 1:02d}</div>'
            f"<h3>{esc(label)}</h3><p>{esc(text)}</p></div>"
            for i, (label, text) in enumerate(slide["steps"])
        )
        metrics = "".join(
            f'<div class="metric"><b>{esc(value)}</b><span>{esc(label)}</span></div>'
            for value, label in slide.get("metrics", [])
        )
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="body"><div class="flow">{steps}</div><div class="metrics">{metrics}</div></div>"""
    elif kind == "table":
        head = "".join(f"<th>{esc(c)}</th>" for c in slide["columns"])
        rows = "".join(
            "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>"
            for row in slide["rows"]
        )
        extra = "".join(
            f'<div class="card"><h3>{esc(label)}</h3><p>{esc(text)}</p></div>'
            for label, text in slide.get("bullets", [])
        )
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="body">
    <table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>
    <div class="triple">{extra}</div>
  </div>"""
    elif kind == "metrics":
        groups = "".join(
            f'<div class="card"><h3>{esc(name)}</h3><div class="rule"></div>'
            f"<ul>{''.join(f'<li>{esc(i)}</li>' for i in items)}</ul></div>"
            for name, items, *_rest in slide["groups"]
        )
        note = f'<div class="note">{esc(slide["note"])}</div>' if slide.get("note") else ""
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="body"><div class="groups">{groups}</div></div>
  {note}"""
    elif kind == "gallery":
        figures = "".join(
            f'<figure><img src="../{esc(path)}" alt="{esc(label)}"></figure>'
            for path, label in slide["shots"]
        )
        facts = "".join(
            f"<div><b>{esc(label)}</b><span>{esc(value)}</span></div>"
            for label, value in slide["facts"]
        )
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="body"><div class="gallery">{figures}</div><div class="facts">{facts}</div></div>"""
    elif kind == "split":
        body = f"""
  <div class="eyebrow">{esc(slide['eyebrow'])}</div>
  <h2>{esc(slide['title'])}</h2>
  <p class="lead">{esc(slide['lead'])}</p>
  <div class="body"><div class="split">
    <div class="card"><h3>{esc(slide['left_title'])}</h3>
      <ul>{''.join(f'<li>{esc(i)}</li>' for i in slide['left'])}</ul></div>
    <div class="card ok"><h3>{esc(slide['right_title'])}</h3>
      <ul>{''.join(f'<li>{esc(i)}</li>' for i in slide['right'])}</ul></div>
  </div></div>
  <div class="note">{esc(slide['note'])}</div>"""
    elif kind == "closing":
        rows = "".join(
            f"<dt>{esc(label)}</dt><dd>{esc(value)}</dd>" for label, value in slide["facts"]
        )
        body = f"""
  <div class="body">
    <div class="eyebrow">{esc(slide['eyebrow'])}</div>
    <div class="brandmark">Подработка.<b>МСК</b></div>
    <h2>{esc(slide['subtitle'])}</h2>
    <div class="rule"></div>
    <dl>{rows}</dl>
    <div class="cta">{esc(slide['cta_line'])}</div>
    <img class="og" src="../screenshots/og-cover.png" alt="Обложка проекта">
  </div>"""

    footer = (
        '<div class="footer"><span>Подработка.МСК · платформа быстрых смен</span>'
        f"<span>{SPEAKER_SLIDES.index(slide) + 1:02d} / {len(SPEAKER_SLIDES):02d}</span></div>"
    )
    return f'<section class="{" ".join(classes)}">{body}{footer}</section>'


def build_html(fonts: dict[str, str]) -> Path:
    css_fonts = font_face_css(fonts)
    slides = "\n".join(render_slide_html(slide) for slide in SPEAKER_SLIDES)
    html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Подработка.МСК — презентация</title>
<meta name="description" content="Презентация продукта Подработка.МСК: платформа быстрых смен в Москве и Московской области. 13 слайдов.">
<link rel="icon" href="../screenshots/og-cover.png">
<style>
{css_fonts}
{HTML_CSS}
</style>
</head>
<body>
<main class="deck">
  <div class="slide-stage">
{slides}
  </div>
</main>
<nav class="nav" aria-label="Навигация по слайдам">
  <button class="prev" type="button" aria-label="Предыдущий слайд">‹</button>
  <span class="pos">1 / {len(SPEAKER_SLIDES)}</span>
  <button class="next" type="button" aria-label="Следующий слайд">›</button>
  <span class="bar"><i></i></span>
</nav>
<div class="hint">← →  листать · P — печать · <a href="podrabotka-msk-deck.pdf" style="color:#D82376">PDF</a> · <a href="../index.html" style="color:#D82376">демо-страница</a></div>
<script>{HTML_JS}</script>
</body>
</html>
"""
    path = OUT_DIR / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fonts = prepare_fonts()
    pdf_path = build_pdf(fonts)
    html_path = build_html(fonts)
    print(f"{pdf_path.relative_to(ROOT)}  {pdf_path.stat().st_size // 1024} KB")
    print(f"{html_path.relative_to(ROOT)}  {html_path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
