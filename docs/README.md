<div align="center">
  <img src="screenshots/og-cover.png" alt="Подработка.МСК — смены на сегодня и завтра" width="860" />
</div>

<h1 align="center">Подработка.МСК</h1>

<p align="center">
  Платформа быстрых смен в Москве и Московской области.<br/>
  Работодатель публикует смену за минуту, исполнитель откликается в один клик
  и получает деньги сразу после смены — без комиссии с заработка.
</p>

<p align="center">
  <a href="https://visiontripin.github.io/Podrabotka/"><b>▶ Демо-страница</b></a> ·
  <a href="https://visiontripin.github.io/Podrabotka/app.html"><b>▶ Интерактивное приложение</b></a> ·
  <a href="https://visiontripin.github.io/Podrabotka/presentation/"><b>▶ Презентация</b></a>
</p>

<p align="center">
  <a href="https://github.com/visiontripin/Podrabotka/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/visiontripin/Podrabotka/actions/workflows/ci.yml/badge.svg" /></a>
  <img alt="Node" src="https://img.shields.io/badge/node-%E2%89%A520-3c873a" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-strict-3178c6" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-111115" />
</p>

---

## Что это

Продукт закрывает разрыв между «нужен человек на смену сегодня» и «хочу заработать завтра же»:
короткие смены на 4–12 часов в Москве и Подмосковье, прозрачная оплата за смену,
проверенные заказчики и рейтинг, который нельзя купить.

Три роли в одном приложении:

| Роль | Что делает |
|---|---|
| **Рабочий** | Ищет смены по метро/МЦД и датам, откликается, ведёт кабинет заработка, получает оценки |
| **Работодатель** | Публикует смены, собирает бригаду «N из M», ведёт воронку кандидатов, закрывает смены |
| **Модератор** | Проверяет отзывы, выдаёт статус «Проверенный», настраивает тарифы и регионы |

Демо-версия уже наполнена реалистичными данными: 12 смен, 7 пользователей, 4 тарифа,
станции метро и МЦД, отзывы на модерации.

## Демо и ссылки

| Что | Ссылка |
|---|---|
| **Демо-страница продукта** (описание, скриншоты, презентация, все ссылки) | <https://visiontripin.github.io/Podrabotka/> |
| **Интерактивное приложение** (без сервера, данные в браузере) | <https://visiontripin.github.io/Podrabotka/app.html> |
| **Презентация в браузере** (13 слайдов, листается стрелками) | <https://visiontripin.github.io/Podrabotka/presentation/> |
| **Презентация PDF** | [`presentation/podrabotka-msk-deck.pdf`](presentation/podrabotka-msk-deck.pdf) |
| **Android-архив** (офлайн, открывается без интернета) | [`docs/downloads/podrabotka-msk-android-preview.zip`](docs/downloads/podrabotka-msk-android-preview.zip) |
| **Офлайн-сайт архивом** (страница + приложение + презентация) | [`docs/downloads/podrabotka-msk-offline-site.zip`](docs/downloads/podrabotka-msk-offline-site.zip) |
| **Исходники одним архивом** | <https://github.com/visiontripin/Podrabotka/archive/refs/heads/main.zip> |
| **Релизы с файлами** | <https://github.com/visiontripin/Podrabotka/releases/latest> |

В репозитории два входа:

- **`index.html`** — демо-страница продукта: возможности, скриншоты, архитектура,
  презентация и ссылки на скачивание. Из неё открывается приложение.
- **`app.html`** — точка входа самого React-приложения (dev-сервер и Vite-сборка).
  На GitHub Pages работающая версия лежит в `docs/app.html`.

## Скриншоты

| Главная · Рабочий | Поиск смен | Карточка смены |
|---|---|---|
| <img src="screenshots/01-home-worker.png" width="420" /> | <img src="screenshots/02-jobs-search.png" width="420" /> | <img src="screenshots/03-job-detail.png" width="420" /> |

| Кабинет работодателя | Админ-панель и модерация | Кабинет рабочего |
|---|---|---|
| <img src="screenshots/05-cabinet-employer.png" width="420" /> | <img src="screenshots/06-admin-moderation.png" width="420" /> | <img src="screenshots/04-cabinet-worker.png" width="420" /> |

<div align="center">
  <img src="screenshots/08-mobile-home.png" width="240" />
  <img src="screenshots/09-mobile-jobs.png" width="240" />
  <br/>
  <sub>Мобильная версия: нижняя навигация, крупные тач-зоны, PWA-манифест</sub>
</div>

## Возможности

**Витрина и поиск**
- Полнотекстовый поиск по названию, адресу и станции; фильтры по категории, району (Москва / МО), оплате, датам («Сегодня», «Завтра», «Ближайшие дни») и способу выплаты.
- Станции метро и МЦД с цветом линии и пешей доступностью, сортировка по релевантности и оплате.
- Бейджи «Срочно», «Без опыта», «Питание», «Проверенный ★», «Избранное».

**Рабочему**
- Отклик в один клик с сопроводительной запиской, лимиты по тарифу, история откликов и статусов.
- Кабинет: заработано за закрытые смены, активные смены, честный рейтинг и индекс выходов (show-up rate), избранное, мини-чат с работодателем, взаимные оценки.
- Профиль: медицина, самозанятость, готовность к ночным сменам, навыки, город и станция.

**Работодателю**
- Публикация смены с автоматическим расчётом часовой ставки, командный набор «N из M», клонирование смены на завтра, пауза и возобновление.
- Воронка кандидатов с приоритетом PRO-исполнителей, принятие и отклонение, закрытие смены и оценка работников.
- Тарифы с реальными лимитами: Бесплатный, Про 299 ₽, Старт, Бизнес 1 990 ₽.

**Модератору**
- Живая очередь отзывов с мгновенным пересчётом рейтингов, верификация участников, редактирование тарифов и лимитов.
- Регионы международного масштабирования (RU, BY, KZ, UZ, AE) с валютами, часовыми поясами и локалями — в SQLite-схеме с первого дня.

## Как это устроено

```
┌─────────────────────────────────────────────────────────────────────┐
│  Браузер                                                             │
│  React 18 + TypeScript + Tailwind CSS + lucide-react                 │
│  один и тот же UI-код                                                │
└───────────────┬─────────────────────────────────────────────────────┘
                │  src/lib/api.ts — единая точка доступа к данным
                │  (fetch → /api/*, 3-секундный таймаут, фолбэк)
      ┌─────────┴──────────┐
      │                    │
┌─────▼──────────────┐  ┌──▼──────────────────────────────────────────┐
│  Server (Node 22)  │  │  Offline-движок src/lib/browserDb.ts        │
│  Express + node:   │  │  те же эндпоинты, данные в localStorage     │
│  sqlite (SQLite)   │  │  включается на github.io / file:// / при    │
│  Vite middleware в │  │  недоступном API — демо живёт без сервера   │
│  dev, dist/ в prod │  └─────────────────────────────────────────────┘
└────────────────────┘
```

- **Один код — два режима.** `npm run dev` поднимает full-stack (API + SQLite + HMR). `npm run build:static` собирает автономный одностраничный HTML, который работает без бэкенда: так демо живёт на GitHub Pages и открывается с телефона офлайн.
- **Данные.** SQLite через встроенный модуль `node:sqlite` (без нативных зависимостей и без Docker для БД): 10 таблиц, сиды при первом запуске, WAL-режим.
- **Типы насквозь.** `tsc --noEmit` в strict-режиме проверяет и фронтенд, и сервер.
- **Ноль внешних ассетов.** Шрифты Manrope и Unbounded (OFL) лежат в `src/assets/fonts` — приложение не делает запросов к Google Fonts и корректно рендерится офлайн.

### Модель данных

```
users ──┬── jobs ──┬── applications ── messages
        │          └── favorites
        ├── reviews        (взаимные оценки, модерация)
        ├── notifications
        └── tariffs        (лимиты по роли)

regions ── locations      (ISO-коды, валюта, таймзона, локаль; метро / МЦД / города МО)
```

## Быстрый старт

```bash
git clone https://github.com/visiontripin/Podrabotka.git
cd Podrabotka
npm install
npm run dev
```

| Адрес | Что открывается |
|---|---|
| **http://localhost:3000** | Демо-страница продукта (`index.html`) |
| <http://localhost:3000/docs/index.html> | Та же страница в сборке для GitHub Pages |
| <http://localhost:3000/docs/app.html> | Приложение в автономном режиме |

Приложение и API работают на одном порту. База создаётся автоматически
в `data/podrabotka.sqlite` и наполняется демо-данными.

| Команда | Что делает |
|---|---|
| `npm run dev` | Full-stack в режиме разработки (Express + Vite HMR) |
| `npm run build` | Проверка типов + production-сборка фронтенда в `dist/` |
| `npm start` | Production-сервер: API + раздача `dist/` на `PORT` (по умолчанию 3000) |
| `npm run build:static` | Автономная сборка в `docs/`: демо-страница, приложение, Android-архив, презентация |
| `npm run build:presentation` | Пересобрать презентацию (PDF + HTML) из `scripts/build-presentation.py` |
| `npm run check:links` | Проверить локальные ссылки и ассеты в `docs/` |
| `npm run verify` | Всё сразу: типы, сборка, статическая сборка, проверка ссылок |

Переменные окружения — см. [`.env.example`](.env.example) (`PORT`, `NODE_ENV`, `DATA_DIR`, `DB_PATH`).

## Демо-аккаунты

Авторизация в демо упрощена: клиент присылает заголовок `X-User-Id`, а роль переключается
кнопкой в правом верхнем углу. Никаких паролей и внешних сервисов.

| ID | Имя | Роль | Что посмотреть |
|---|---|---|---|
| 1 | Златов Влас | Рабочий | Отклики, заработок, рейтинг |
| 2 | Илья Громов | Работодатель | Воронка кандидатов, публикация смены |
| 7 | Алексей Морозов | Модератор | Очередь отзывов, тарифы, регионы |

## Презентация

13 слайдов: обложка, проблема, решение, аудитория, путь исполнителя и работодателя,
доверие и модерация, тарифы, метрики, архитектура, демо, дорожная карта, ограничения.

- PDF — [`presentation/podrabotka-msk-deck.pdf`](presentation/podrabotka-msk-deck.pdf) (16:9, кириллица встроена);
- HTML — [`presentation/index.html`](presentation/index.html) (стрелки ← →, печать в PDF из браузера).

Обе версии собираются из одного источника контента — `scripts/build-presentation.py`:

```bash
python3 -m pip install reportlab fonttools brotli
npm run build:presentation
```

Шрифты для презентации берутся из `src/assets/fonts` (latin + cyrillic субсеты
объединяются и урезаются до используемых знаков), поэтому внешние ресурсы не нужны.

## Деплой

### GitHub Pages (демо без сервера)

`npm run build:static` собирает `docs/`:

| Файл | Что это |
|---|---|
| `docs/index.html` | демо-страница продукта (копия корневого `index.html`) |
| `docs/app.html` | приложение с offline-движком `browserDb` |
| `docs/404.html` | SPA-fallback для Pages |
| `docs/presentation/` | презентация: PDF и HTML |
| `docs/downloads/` | Android-архив и ZIP офлайн-сайта для автономного запуска |
| `docs/screenshots/`, `docs/styles/`, `docs/src/assets/fonts/` | картинки, стили и шрифты страницы |

Публикация настраивается **один раз** в настройках репозитория — оба варианта поддерживаются:

| Вариант | Настройка | Как обновляется |
|---|---|---|
| Branch (по умолчанию) | Settings → Pages → *Deploy from a branch* → `main` / **`/docs`** | автоматически при коммите в `main` |
| Actions | Settings → Pages → *Source: GitHub Actions* | workflow [`deploy-pages.yml`](.github/workflows/deploy-pages.yml) |

> Важно: если выбрать `/docs`, корневой `index.html` (Vite-шелл) больше не отдаётся
> как сайт — браузер получает готовую демо-страницу из `docs/index.html`.

Пока Pages не включён, workflow не падает: сборка выполняется, а в Summary сборки
появляется подсказка, что осталось нажать одну кнопку. Сборка лежит в репозитории
намеренно — сайт остаётся доступен даже без CI и без сервера.

### Docker (full-stack с API и SQLite)

```bash
docker build -t podrabotka-msk .
docker run -p 3000:3000 -v "$PWD/data:/app/data" podrabotka-msk
```

Образ содержит `HEALTHCHECK` на `/api/health`; базу монтируйте томом, чтобы данные переживали перезапуск.

### Проверка живости

```bash
curl -s localhost:3000/api/health
# {"status":"ok","service":"podrabotka-msk","uptime_seconds":3,"jobs_count":12}
```

## API

Все эндпоинты отдают JSON и принимают `X-User-Id` (демо-аутентификация).

| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/api/bootstrap` | Профиль, тарифы, локации, статистика, уведомления |
| `GET` | `/api/jobs` | Каталог смен (фильтры: `employer_id`, `include_inactive`, поиск, категории) |
| `POST` | `/api/jobs` | Публикация смены с проверкой лимита тарифа |
| `PATCH` | `/api/jobs/:id` | Пауза, возобновление, закрытие смены |
| `POST` | `/api/jobs/:id/clone` | Клонирование смены на завтра |
| `POST` | `/api/jobs/:id/apply` | Отклик на смену (учитывает дневной лимит) |
| `POST` | `/api/jobs/:id/favorite` | Избранное |
| `GET` | `/api/applications` | Отклики по роли |
| `PATCH` | `/api/applications/:id/status` | Принять / отклонить / закрыть смену |
| `POST` | `/api/applications/:id/messages` | Сообщение в мини-чат |
| `POST` | `/api/reviews` | Оценка контрагента после смены |
| `PUT` | `/api/me/profile` | Обновление профиля |
| `PUT` | `/api/me/tariff` | Смена тарифа |
| `POST` | `/api/auth/login` · `/api/auth/register` | Демо-вход и регистрация |
| `GET` | `/api/admin/overview` | Сводка модерации |
| `PATCH` | `/api/admin/reviews/:id` | Одобрить / отклонить отзыв |
| `PUT` | `/api/admin/tariffs/:id` | Цена и лимиты тарифа |
| `PATCH` | `/api/admin/users/:id/verify` | Статус «Проверенный» |
| `PATCH` | `/api/admin/regions/:id` | Включить регион масштабирования |
| `GET` | `/api/health` | Healthcheck для деплоя |

## Структура репозитория

```
.
├── index.html            # демо-страница продукта (описание, ссылки, презентация)
├── app.html              # точка входа React-приложения (Vite)
├── styles/demo.css       # стили демо-страницы (без Tailwind и CDN)
├── presentation/         # презентация: podrabotka-msk-deck.pdf + index.html
├── src/                  # React-приложение
│   ├── views/            # Главная, поиск, кабинеты, админка, профиль
│   ├── components/       # Карточки смен, модальные окна, формы
│   ├── lib/              # api.ts (транспорт + фолбэк), browserDb.ts (offline-движок)
│   ├── assets/fonts/     # Manrope + Unbounded (OFL), локально
│   └── styles/fonts.css
├── server/               # Express API, схема и сиды SQLite
├── scripts/
│   ├── build-static.mjs        # автономная сборка для GitHub Pages
│   ├── build-presentation.py   # презентация: PDF + HTML из одного источника
│   └── check-links.mjs         # проверка ссылок и ассетов в docs/
├── screenshots/          # реальные скриншоты интерфейса
├── docs/                 # сгенерированный сайт для GitHub Pages (не править руками)
├── archive/tws-hub/      # архивный инженерный проект (не часть продукта)
└── .github/workflows/    # CI: типы, сборка, проверка ссылок, smoke-тест API
```

## Проверки

```bash
npm run verify   # typecheck + сборка + автономная сборка + ссылки
npm start & curl -fsS localhost:3000/api/health
```

CI на каждый push в `main` и на pull request выполняет те же шаги плюс smoke-тест `/api/health`
и публикует артефакт статической сборки.

## Ограничения

Это работающий MVP с демо-данными, а не продакшен-маркетплейс:

- **Аутентификация демонстрационная** — идентификатор пользователя приходит заголовком, сессий и паролей нет.
- **Платежи и выплаты не подключены** — «СБП сразу», «На руки», «СМЗ» отражены в модели данных и UI, но не проводятся.
- **SQLite подходит для одного инстанса**; для горизонтального масштабирования нужен PostgreSQL.
- **Уведомления и чат** работают в рамках приложения, без push и внешних каналов.
- Тексты вакансий и отзывы — сгенерированные демо-данные, реальные компании и люди не упоминаются.

## Дорожная карта

- [ ] Реальная аутентификация (SMS-код по телефону) и сессии
- [ ] PostgreSQL + миграции, вынос API в отдельный сервис
- [ ] Выплаты через СБП и интеграция с самозанятостью (СМЗ)
- [ ] Push-уведомления и realtime-чат
- [ ] Админ-аналитика: конверсия откликов, стоимость смены, отток
- [ ] Городские запуски через `regions` / `locations` (СПб, Минск, Алматы)

## Благодарности и лицензия

Код — [MIT](LICENSE). Шрифты Manrope и Unbounded — SIL Open Font License, тексты лицензий
лежат в `src/assets/fonts/`. Иконки — [lucide](https://lucide.dev) (ISC).

Архивный проект в `archive/tws-hub/` относится к другому продукту (Bluetooth-хаб для колонок)
и сохранён как инженерная документация, в сборку не входит.
