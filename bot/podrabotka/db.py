"""Слой доступа к данным Подработка.МСК.

В отличие от веб-сервера (node:sqlite), бот открывает ту же SQLite-базу
через модуль sqlite3 стандартной библиотеки. WAL-режим, включённый
веб-версией, позволяет нескольким читателям и одному писателю работать
одновременно; короткие транзакции BEGIN IMMEDIATE + busy_timeout
исключают конфликты блокировок.

Все функции «обогащают» строки теми же вычисляемыми полями, что и
serializeUser / serializeJobRow на сервере, поэтому Telegram и веб
показывают идентичные данные.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from .config import DB_PATH

BUSY_TIMEOUT_MS = 30000


class BotDBError(Exception):
    pass


class Database:
    def __init__(self, path: Path = DB_PATH):
        self.path = Path(path)
        if not self.path.exists():
            raise BotDBError(
                f"База данных не найдена: {self.path}\n"
                "Сначала запустите веб-версию один раз (npm run dev) — она создаст "
                "и наполнит базу, либо укажите путь через PODRABOTKA_DB_PATH."
            )
        self.init_bot_tables()

    # ---------- низкоуровневые помощники ----------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), timeout=BUSY_TIMEOUT_MS / 1000)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def _tx(self):
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @contextmanager
    def _read(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()

    @staticmethod
    def _row(r) -> dict | None:
        return dict(r) if r is not None else None

    # ---------- служебные таблицы бота ----------
    def init_bot_tables(self):
        with self._tx() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS bot_telegram_links (
                     telegram_id INTEGER PRIMARY KEY,
                     user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                     notify INTEGER NOT NULL DEFAULT 1,
                     created_at TEXT NOT NULL DEFAULT (datetime('now'))
                   )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS bot_meta (
                     key TEXT PRIMARY KEY,
                     value TEXT NOT NULL
                   )"""
            )

    def link_telegram(self, telegram_id: int, user_id: int):
        with self._tx() as conn:
            # Уникальность user_id: сначала отвязываем старый telegram_id этого пользователя
            conn.execute("DELETE FROM bot_telegram_links WHERE user_id = ?", (user_id,))
            conn.execute(
                "INSERT INTO bot_telegram_links (telegram_id, user_id, notify) VALUES (?, ?, 1) "
                "ON CONFLICT(telegram_id) DO UPDATE SET user_id = excluded.user_id",
                (telegram_id, user_id),
            )

    def unlink_telegram(self, telegram_id: int):
        with self._tx() as conn:
            conn.execute("DELETE FROM bot_telegram_links WHERE telegram_id = ?", (telegram_id,))

    def linked_user_id(self, telegram_id: int) -> int | None:
        with self._read() as conn:
            r = conn.execute(
                "SELECT user_id FROM bot_telegram_links WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
            return int(r["user_id"]) if r else None

    def get_notify(self, telegram_id: int) -> bool:
        with self._read() as conn:
            r = conn.execute(
                "SELECT notify FROM bot_telegram_links WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
            return bool(r["notify"]) if r else True

    def set_notify(self, telegram_id: int, on: bool):
        with self._tx() as conn:
            conn.execute(
                "UPDATE bot_telegram_links SET notify = ? WHERE telegram_id = ?",
                (1 if on else 0, telegram_id),
            )

    def toggle_notify(self, telegram_id: int) -> bool:
        with self._tx() as conn:
            r = conn.execute(
                "SELECT notify FROM bot_telegram_links WHERE telegram_id = ?", (telegram_id,)
            ).fetchone()
            if not r:
                raise BotDBError("Аккаунт не привязан")
            new_val = 0 if r["notify"] else 1
            conn.execute(
                "UPDATE bot_telegram_links SET notify = ? WHERE telegram_id = ?",
                (new_val, telegram_id),
            )
            return bool(new_val)

    def get_meta(self, key: str) -> str | None:
        with self._read() as conn:
            r = conn.execute("SELECT value FROM bot_meta WHERE key = ?", (key,)).fetchone()
            return r["value"] if r else None

    def set_meta(self, key: str, value: str):
        with self._tx() as conn:
            conn.execute(
                "INSERT INTO bot_meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    # ---------- пользователи ----------
    def rating_stats(self, user_id: int) -> dict:
        with self._read() as conn:
            r = conn.execute(
                "SELECT COUNT(*) AS cnt, COALESCE(ROUND(AVG(rating), 1), 0) AS avg_rating "
                "FROM reviews WHERE target_user_id = ? AND moderation_status = 'approved'",
                (user_id,),
            ).fetchone()
            return {"rating_avg": float(r["avg_rating"]), "reviews_count": int(r["cnt"])}

    def get_user_by_email(self, email: str) -> dict | None:
        with self._read() as conn:
            return self._row(
                conn.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),)).fetchone()
            )

    def email_exists(self, email: str) -> bool:
        return self.get_user_by_email(email) is not None

    def create_user(self, name: str, email: str, password: str, role: str) -> int:
        if role not in ("worker", "employer"):
            role = "worker"
        tariff = "worker_free" if role == "worker" else "employer_start"
        with self._tx() as conn:
            cur = conn.execute(
                "INSERT INTO users (email, password, role, name, tariff_slug) VALUES (?, ?, ?, ?, ?)",
                (email.strip().lower(), password or "demo1234", role, name.strip(), tariff),
            )
            return int(cur.lastrowid)

    def serialize_user(self, user_id: int) -> dict | None:
        with self._read() as conn:
            u = self._row(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
            if not u:
                return None
            tariff = self._row(
                conn.execute("SELECT * FROM tariffs WHERE slug = ?", (u["tariff_slug"],)).fetchone()
            )
            today = conn.execute(
                "SELECT COUNT(*) AS c FROM applications WHERE worker_id = ? "
                "AND date(created_at) = date('now') AND status != 'cancelled'",
                (user_id,),
            ).fetchone()
            active = conn.execute(
                "SELECT COUNT(*) AS c FROM jobs WHERE employer_id = ? AND status = 'active'", (user_id,)
            ).fetchone()
        stats = self.rating_stats(user_id)
        return {
            "id": u["id"],
            "email": u["email"],
            "role": u["role"],
            "name": u["name"],
            "company_name": u["company_name"] or "",
            "phone": u["phone"] or "",
            "bio": u["bio"] or "",
            "city": u["city"] or "Москва",
            "metro_station": u["metro_station"] or "",
            "skills": json.loads(u["skills_json"] or "[]"),
            "has_med_book": bool(u["has_med_book"]),
            "is_self_employed": bool(u["is_self_employed"]),
            "night_shifts_ok": bool(u["night_shifts_ok"]),
            "is_verified": bool(u["is_verified"]),
            "tariff_slug": u["tariff_slug"],
            "tariff_title": tariff["title"] if tariff else "Бесплатный",
            "tariff_limit": (tariff["limit_value"] if tariff else 5),
            "today_applications_used": int(today["c"]),
            "active_jobs_used": int(active["c"]),
            "earned_total": int(u["earned_total"] or 0),
            "shifts_completed": int(u["shifts_completed"] or 0),
            "show_up_rate": int(u["show_up_rate"] or 100),
            "rating_avg": stats["rating_avg"],
            "reviews_count": stats["reviews_count"],
            "created_at": u["created_at"],
        }

    def list_admin_ids(self) -> list[int]:
        with self._read() as conn:
            rows = conn.execute("SELECT id FROM users WHERE role = 'admin'").fetchall()
            return [int(r["id"]) for r in rows]

    def list_tariffs(self) -> list[dict]:
        with self._read() as conn:
            rows = conn.execute("SELECT * FROM tariffs ORDER BY id ASC").fetchall()
            return [
                {
                    "slug": r["slug"],
                    "title": r["title"],
                    "target_role": r["target_role"],
                    "price_rub": int(r["price_rub"]),
                    "limit_value": r["limit_value"],
                    "description": r["description"],
                    "perks": json.loads(r["perks_json"] or "[]"),
                }
                for r in rows
            ]

    def list_locations(self) -> list[dict]:
        with self._read() as conn:
            rows = conn.execute(
                "SELECT station_name, line_name, line_color, city_name, area_type FROM locations ORDER BY region_id, area_type, id"
            ).fetchall()
            return [dict(r) for r in rows]

    # ---------- смены ----------
    def _base_jobs_sql(self) -> str:
        return """
            SELECT j.*, u.name AS employer_name, u.company_name AS employer_company,
                   u.is_verified AS employer_verified
            FROM jobs j JOIN users u ON u.id = j.employer_id
        """

    def _enrich_job(self, conn, j: dict, user_id: int) -> dict:
        emp = self.rating_stats(j["employer_id"])
        fav = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND job_id = ?", (user_id, j["id"])
        ).fetchone()
        my_app = conn.execute(
            "SELECT id, status FROM applications WHERE worker_id = ? AND job_id = ?", (user_id, j["id"])
        ).fetchone()
        counts = conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_cnt "
            "FROM applications WHERE job_id = ? AND status != 'cancelled'",
            (j["id"],),
        ).fetchone()
        j = dict(j)
        j.update(
            {
                "employer_rating": emp["rating_avg"],
                "employer_reviews_count": emp["reviews_count"],
                "is_favorite": bool(fav),
                "my_application_id": int(my_app["id"]) if my_app else None,
                "my_application_status": my_app["status"] if my_app else None,
                "applications_count": int(counts["total"] or 0),
                "pending_applications_count": int(counts["pending_cnt"] or 0),
            }
        )
        return j

    def list_jobs(self, user_id: int, *, category=None, area_type=None, date_preset=None,
                  min_pay=None, no_experience=False, favorites_only=False, page=1, page_size=5):
        where = ["j.status = 'active'"]
        params: list = []
        if category:
            where.append("j.category = ?")
            params.append(category)
        if area_type and area_type != "all":
            where.append("j.area_type = ?")
            params.append(area_type)
        if date_preset == "today":
            where.append("j.shift_date = date('now', 'localtime')")
        elif date_preset == "tomorrow":
            where.append("j.shift_date = date('now', 'localtime', '+1 day')")
        elif date_preset == "upcoming":
            where.append("j.shift_date >= date('now', 'localtime', '+2 days')")
        if min_pay:
            where.append("j.pay_amount >= ?")
            params.append(int(min_pay))
        if no_experience:
            where.append("j.experience_required = 0")
        if favorites_only:
            where.append("EXISTS (SELECT 1 FROM favorites f WHERE f.user_id = ? AND f.job_id = j.id)")
            params.append(user_id)

        sql = self._base_jobs_sql() + " WHERE " + " AND ".join(where) + \
            " ORDER BY is_promoted DESC, is_urgent DESC, id DESC"
        with self._read() as conn:
            rows = [self._row(r) for r in conn.execute(sql, params).fetchall()]
            items = [self._enrich_job(conn, r, user_id) for r in rows]
        total = len(items)
        pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(page, pages))
        return items[(page - 1) * page_size: page * page_size], total, pages, page

    def get_job(self, job_id: int, user_id: int) -> dict | None:
        with self._read() as conn:
            r = self._row(
                conn.execute(self._base_jobs_sql() + " WHERE j.id = ?", (job_id,)).fetchone()
            )
            if not r:
                return None
            return self._enrich_job(conn, r, user_id)

    def list_my_jobs(self, employer_id: int, include_closed: bool = False) -> list[dict]:
        sql = "SELECT j.*, u.name AS employer_name, u.company_name AS employer_company, u.is_verified AS employer_verified " \
              "FROM jobs j JOIN users u ON u.id = j.employer_id WHERE j.employer_id = ?"
        if not include_closed:
            sql += " AND j.status != 'closed'"
        sql += " ORDER BY CASE j.status WHEN 'active' THEN 0 WHEN 'paused' THEN 1 ELSE 2 END, j.shift_date ASC, j.id DESC"
        with self._read() as conn:
            rows = []
            for r in conn.execute(sql, (employer_id,)).fetchall():
                j = self._row(r)
                counts = conn.execute(
                    "SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending_cnt "
                    "FROM applications WHERE job_id = ? AND status != 'cancelled'",
                    (j["id"],),
                ).fetchone()
                j["applications_count"] = int(counts["total"] or 0)
                j["pending_applications_count"] = int(counts["pending_cnt"] or 0)
                rows.append(j)
            return rows

    def create_job(self, employer_id: int, data: dict):
        user = self.serialize_user(employer_id)
        if not user:
            return None, "Пользователь не найден"
        if user["role"] == "employer" and user["tariff_limit"] is not None:
            if user["active_jobs_used"] >= int(user["tariff_limit"]):
                return None, (
                    f"Достигнут лимит активных смен ({user['tariff_limit']}) на тарифе "
                    f"«{user['tariff_title']}». Перейдите на тариф «Бизнес»."
                )
        loc = None
        if data.get("metro_station"):
            with self._read() as conn:
                loc = self._row(
                    conn.execute(
                        "SELECT line_color, city_name, area_type FROM locations WHERE station_name = ? LIMIT 1",
                        (data["metro_station"],),
                    ).fetchone()
                )
        is_promoted = 1 if user["tariff_slug"] == "employer_business" else 0
        with self._tx() as conn:
            cur = conn.execute(
                """INSERT INTO jobs (
                    employer_id, region_id, area_type, title, category, city, metro_station, metro_color,
                    walk_minutes, address, shift_date, start_time, end_time, duration_hours, pay_amount,
                    currency_symbol, payout_type, slots_total, slots_filled, experience_required,
                    med_book_required, smz_preferred, meal_included, is_urgent, is_promoted,
                    description, requirements_json, status
                ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '₽', ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, 'active')""",
                (
                    employer_id,
                    (loc["area_type"] if loc else data.get("area_type", "moscow")),
                    data["title"].strip(),
                    data.get("category", "Склад"),
                    (loc["city_name"] if loc else data.get("city", "Москва")),
                    data.get("metro_station", "Автозаводская").strip(),
                    (loc["line_color"] if loc else "#D82376"),
                    int(data.get("walk_minutes") or 7),
                    data.get("address", "").strip(),
                    data["shift_date"],
                    data.get("start_time", "09:00"),
                    data.get("end_time", "18:00"),
                    float(data.get("duration_hours") or 8),
                    int(data.get("pay_amount") or 4000),
                    data.get("payout_type", "sbp_instant"),
                    max(1, int(data.get("slots_total") or 1)),
                    1 if data.get("experience_required") else 0,
                    1 if data.get("med_book_required") else 0,
                    1 if data.get("smz_preferred") else 0,
                    1 if data.get("meal_included") else 0,
                    1 if data.get("is_urgent") else 0,
                    is_promoted,
                    (data.get("description") or "Смена от проверенного заказчика. Подробный инструктаж на месте.").strip(),
                    json.dumps(data.get("requirements") or [], ensure_ascii=False),
                ),
            )
            return int(cur.lastrowid), None

    def clone_job(self, employer_id: int, job_id: int):
        user = self.serialize_user(employer_id)
        with self._read() as conn:
            job = self._row(conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())
        if not job:
            return None, "Смена не найдена"
        if job["employer_id"] != employer_id and (not user or user["role"] != "admin"):
            return None, "Это не ваша смена"
        if user and user["role"] == "employer" and user["tariff_limit"] is not None:
            if user["active_jobs_used"] >= int(user["tariff_limit"]):
                return None, (
                    f"Лимит активных смен ({user['tariff_limit']}) исчерпан. Подключите «Бизнес»."
                )
        with self._tx() as conn:
            cur = conn.execute(
                """INSERT INTO jobs (
                    employer_id, region_id, area_type, title, category, city, metro_station, metro_color,
                    walk_minutes, address, shift_date, start_time, end_time, duration_hours, pay_amount,
                    currency_symbol, payout_type, slots_total, slots_filled, experience_required,
                    med_book_required, smz_preferred, meal_included, is_urgent, is_promoted,
                    description, requirements_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now', 'localtime', '+1 day'), ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, 'active')""",
                (
                    employer_id, job["region_id"], job["area_type"], job["title"], job["category"], job["city"],
                    job["metro_station"], job["metro_color"], job["walk_minutes"], job["address"],
                    job["start_time"], job["end_time"], job["duration_hours"], job["pay_amount"],
                    job["currency_symbol"], job["payout_type"], job["slots_total"],
                    job["experience_required"], job["med_book_required"], job["smz_preferred"],
                    job["meal_included"], job["is_urgent"], job["is_promoted"],
                    job["description"], job["requirements_json"],
                ),
            )
            return int(cur.lastrowid), None

    def set_job_status(self, job_id: int, user_id: int, new_status: str):
        if new_status not in ("active", "paused", "closed"):
            return False, "Некорректный статус"
        with self._tx() as conn:
            job = self._row(conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())
            if not job:
                return False, "Смена не найдена"
            u = self._row(conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone())
            if job["employer_id"] != user_id and (not u or u["role"] != "admin"):
                return False, "Нет прав для изменения этой смены"
            conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (new_status, job_id))
            return True, None

    def toggle_favorite(self, user_id: int, job_id: int) -> bool:
        with self._tx() as conn:
            existing = conn.execute(
                "SELECT 1 FROM favorites WHERE user_id = ? AND job_id = ?", (user_id, job_id)
            ).fetchone()
            if existing:
                conn.execute("DELETE FROM favorites WHERE user_id = ? AND job_id = ?", (user_id, job_id))
                return False
            conn.execute(
                "INSERT INTO favorites (user_id, job_id) VALUES (?, ?)", (user_id, job_id)
            )
            return True

    def list_favorites(self, user_id: int) -> list[dict]:
        with self._read() as conn:
            rows = conn.execute(
                self._base_jobs_sql() +
                " JOIN favorites f ON f.job_id = j.id AND f.user_id = ? "
                "ORDER BY f.created_at DESC",
                (user_id,),
            ).fetchall()
            return [self._enrich_job(conn, self._row(r), user_id) for r in rows]

    # ---------- отклики и смена статусов ----------
    def apply_to_job(self, user_id: int, job_id: int, cover_note: str):
        user = self.serialize_user(user_id)
        if not user:
            return {"ok": False, "error": "Аккаунт не найден"}
        if user["role"] != "worker":
            return {
                "ok": False,
                "error": "Откликаться на смены могут только исполнители. "
                         "Если вы работодатель — откройте «📦 Мои смены».",
            }
        with self._read() as conn:
            job = self._row(conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())
        if not job or job["status"] != "active":
            return {"ok": False, "error": "Смена уже закрыта или не найдена"}
        existing = None
        with self._read() as conn:
            existing = self._row(
                conn.execute(
                    "SELECT * FROM applications WHERE job_id = ? AND worker_id = ?", (job_id, user_id)
                ).fetchone()
            )
        if existing and existing["status"] != "cancelled":
            return {"ok": False, "error": "Вы уже откликнулись на эту подработку"}
        if user["tariff_limit"] is not None and user["today_applications_used"] >= int(user["tariff_limit"]):
            return {
                "ok": False,
                "code": "TARIFF_LIMIT",
                "error": (
                    f"Вы использовали все {user['tariff_limit']} бесплатных откликов на сегодня. "
                    "Тариф «Про» (299 ₽/мес) — безлимитные отклики и приоритет в списке."
                ),
            }
        cover = (cover_note or "Готов выйти на смену без опозданий, на связи!").strip()[:500]
        with self._tx() as conn:
            if existing and existing["status"] == "cancelled":
                conn.execute(
                    "UPDATE applications SET status = 'pending', cover_note = ?, updated_at = datetime('now') WHERE id = ?",
                    (cover, existing["id"]),
                )
                app_id = int(existing["id"])
            else:
                cur = conn.execute(
                    "INSERT INTO applications (job_id, worker_id, cover_note, status) VALUES (?, ?, ?, 'pending')",
                    (job_id, user_id, cover),
                )
                app_id = int(cur.lastrowid)
            conn.execute(
                "INSERT INTO notifications (user_id, type, title, body, target_tab) VALUES (?, 'application', ?, ?, 'cabinet')",
                (
                    job["employer_id"],
                    f"Новый отклик: {user['name']}",
                    f"Кандидат откликнулся на смену «{job['title']}» ({job['pay_amount']} ₽).",
                ),
            )
        return {"ok": True, "application_id": app_id}

    def list_applications(self, user_id: int, role: str) -> list[dict]:
        if role == "employer":
            where = "j.employer_id = ?"
            params = [user_id]
        elif role == "admin":
            where = "1 = 1"
            params = []
        else:
            where = "a.worker_id = ?"
            params = [user_id]

        sql = f"""
            SELECT a.*,
                   j.title AS job_title, j.category AS job_category, j.city AS job_city,
                   j.metro_station AS job_metro, j.shift_date AS job_date,
                   j.start_time AS job_start_time, j.end_time AS job_end_time,
                   j.pay_amount AS job_pay_amount, j.payout_type AS job_payout_type,
                   j.employer_id, j.slots_total, j.slots_filled, j.status AS job_status,
                   emp.name AS employer_name, emp.company_name AS employer_company,
                   emp.phone AS employer_phone, emp.is_verified AS employer_verified,
                   w.name AS worker_name, w.phone AS worker_phone, w.metro_station AS worker_metro,
                   w.skills_json AS worker_skills_json, w.has_med_book AS worker_has_med_book,
                   w.is_self_employed AS worker_is_self_employed,
                   w.shifts_completed AS worker_shifts_completed,
                   w.show_up_rate AS worker_show_up_rate,
                   w.tariff_slug AS worker_tariff_slug
            FROM applications a
            JOIN jobs j ON j.id = a.job_id
            JOIN users emp ON emp.id = j.employer_id
            JOIN users w ON w.id = a.worker_id
            WHERE {where}
            ORDER BY CASE WHEN w.tariff_slug = 'worker_pro' THEN 0 ELSE 1 END, a.id DESC
        """
        with self._read() as conn:
            rows = [self._row(r) for r in conn.execute(sql, params).fetchall()]
            out = []
            for r in rows:
                wr = self.rating_stats(r["worker_id"])
                hr = conn.execute(
                    "SELECT 1 FROM reviews WHERE application_id = ? AND author_id = ? LIMIT 1",
                    (r["id"], user_id),
                ).fetchone()
                r["worker_rating"] = wr["rating_avg"]
                r["worker_reviews_count"] = wr["reviews_count"]
                r["worker_skills"] = json.loads(r["worker_skills_json"] or "[]")
                r["has_my_review"] = bool(hr)
                out.append(r)
            return out

    def get_application(self, app_id: int) -> dict | None:
        with self._read() as conn:
            r = self._row(
                conn.execute(
                    """SELECT a.*, j.employer_id, j.title AS job_title, j.pay_amount,
                              j.slots_total, j.slots_filled, j.shift_date, j.start_time, j.end_time,
                              j.metro_station, j.city
                       FROM applications a JOIN jobs j ON j.id = a.job_id WHERE a.id = ?""",
                    (app_id,),
                ).fetchone()
            )
            return r

    def set_application_status(self, app_id: int, actor_id: int, new_status: str):
        with self._tx() as conn:
            app = self._row(
                conn.execute(
                    "SELECT a.*, j.employer_id, j.title AS job_title, j.pay_amount, j.slots_total, j.slots_filled "
                    "FROM applications a JOIN jobs j ON j.id = a.job_id WHERE a.id = ?",
                    (app_id,),
                ).fetchone()
            )
            if not app:
                return {"ok": False, "error": "Отклик не найден"}

            # Отмена самим исполнителем
            if new_status == "cancelled" and app["worker_id"] == actor_id:
                if app["status"] == "accepted" and app["slots_filled"] > 0:
                    conn.execute(
                        "UPDATE jobs SET slots_filled = MAX(0, slots_filled - 1) WHERE id = ?",
                        (app["job_id"],),
                    )
                conn.execute(
                    "UPDATE applications SET status = 'cancelled', updated_at = datetime('now') WHERE id = ?",
                    (app_id,),
                )
                return {"ok": True}

            if app["employer_id"] != actor_id:
                u = conn.execute("SELECT role FROM users WHERE id = ?", (actor_id,)).fetchone()
                if not u or u["role"] != "admin":
                    return {"ok": False, "error": "Только работодатель смены может изменить статус кандидата"}

            if new_status == "accepted" and app["status"] != "accepted":
                if app["slots_filled"] >= app["slots_total"]:
                    return {"ok": False, "error": "Все места в бригаде уже заняты"}
                conn.execute(
                    "UPDATE applications SET status = 'accepted', updated_at = datetime('now') WHERE id = ?",
                    (app_id,),
                )
                conn.execute(
                    "UPDATE jobs SET slots_filled = MIN(slots_total, slots_filled + 1) WHERE id = ?",
                    (app["job_id"],),
                )
                conn.execute(
                    "INSERT INTO notifications (user_id, type, title, body, target_tab) VALUES (?, 'status', 'Вас пригласили на смену!', ?, 'cabinet')",
                    (
                        app["worker_id"],
                        f"Работодатель подтвердил ваш выход на смену «{app['job_title']}» ({app['pay_amount']} ₽).",
                    ),
                )
            elif new_status == "rejected":
                if app["status"] == "accepted" and app["slots_filled"] > 0:
                    conn.execute(
                        "UPDATE jobs SET slots_filled = MAX(0, slots_filled - 1) WHERE id = ?",
                        (app["job_id"],),
                    )
                conn.execute(
                    "UPDATE applications SET status = 'rejected', updated_at = datetime('now') WHERE id = ?",
                    (app_id,),
                )
                conn.execute(
                    "INSERT INTO notifications (user_id, type, title, body, target_tab) VALUES (?, 'status', 'Набор на смену завершён', ?, 'jobs')",
                    (app["worker_id"], f"По смене «{app['job_title']}» набрана полная бригада. Посмотрите свежие смены рядом."),
                )
            elif new_status == "completed":
                already = bool(app["payout_recorded"])
                conn.execute(
                    "UPDATE applications SET status = 'completed', payout_recorded = 1, updated_at = datetime('now') WHERE id = ?",
                    (app_id,),
                )
                if not already:
                    conn.execute(
                        "UPDATE users SET earned_total = earned_total + ?, shifts_completed = shifts_completed + 1 WHERE id = ?",
                        (int(app["pay_amount"]), app["worker_id"]),
                    )
                    conn.execute(
                        "UPDATE users SET shifts_completed = shifts_completed + 1 WHERE id = ?",
                        (app["employer_id"],),
                    )
                    conn.execute(
                        "INSERT INTO notifications (user_id, type, title, body, target_tab) VALUES (?, 'status', ?, ?, 'cabinet')",
                        (
                            app["worker_id"],
                            f"Смена закрыта · +{app['pay_amount']} ₽",
                            f"Смена «{app['job_title']}» успешно завершена. Оцените работодателя для честного рейтинга!",
                        ),
                    )
            else:
                return {"ok": False, "error": "Некорректный статус"}
            return {"ok": True}

    def list_messages(self, app_id: int, limit: int = 8) -> list[dict]:
        with self._read() as conn:
            rows = conn.execute(
                "SELECT m.id, m.sender_id, m.body, m.created_at, u.name AS sender_name, u.role AS sender_role "
                "FROM messages m JOIN users u ON u.id = m.sender_id WHERE m.application_id = ? "
                "ORDER BY m.id DESC LIMIT ?",
                (app_id, limit),
            ).fetchall()
            return list(reversed([self._row(r) for r in rows]))

    def add_message(self, app_id: int, sender_id: int, body: str):
        body = body.strip()
        if not body:
            return {"ok": False, "error": "Введите текст сообщения"}
        with self._tx() as conn:
            app = self._row(
                conn.execute(
                    "SELECT a.*, j.employer_id, j.title AS job_title FROM applications a "
                    "JOIN jobs j ON j.id = a.job_id WHERE a.id = ?",
                    (app_id,),
                ).fetchone()
            )
            if not app:
                return {"ok": False, "error": "Диалог не найден"}
            if sender_id not in (app["worker_id"], app["employer_id"]):
                u = conn.execute("SELECT role FROM users WHERE id = ?", (sender_id,)).fetchone()
                if not u or u["role"] != "admin":
                    return {"ok": False, "error": "Вы не участник этого диалога"}
            conn.execute(
                "INSERT INTO messages (application_id, sender_id, body) VALUES (?, ?, ?)",
                (app_id, sender_id, body[:1000]),
            )
            recipient = app["employer_id"] if sender_id == app["worker_id"] else app["worker_id"]
            sender = conn.execute("SELECT name FROM users WHERE id = ?", (sender_id,)).fetchone()
            conn.execute(
                "INSERT INTO notifications (user_id, type, title, body, target_tab) VALUES (?, 'message', ?, ?, 'cabinet')",
                (
                    recipient,
                    f"Сообщение от {sender['name'] if sender else 'участника'}",
                    f"По смене «{app['job_title']}»: {body[:90]}",
                ),
            )
            return {"ok": True}

    # ---------- отзывы и модерация ----------
    def has_my_review(self, application_id: int, author_id: int) -> bool:
        with self._read() as conn:
            r = conn.execute(
                "SELECT 1 FROM reviews WHERE application_id = ? AND author_id = ? LIMIT 1",
                (application_id, author_id),
            ).fetchone()
            return r is not None

    def add_review(self, author_id: int, app_id: int, rating: int, comment: str):
        author = self.serialize_user(author_id)
        app = self.get_application(app_id)
        if not author or not app:
            return {"ok": False, "error": "Отклик не найден"}
        if author_id == app["worker_id"]:
            target_id = app["employer_id"]
        elif author_id == app["employer_id"]:
            target_id = app["worker_id"]
        else:
            return {"ok": False, "error": "Вы не участник этой смены"}
        rating = min(5, max(1, int(rating)))
        with self._tx() as conn:
            conn.execute(
                """INSERT INTO reviews (
                    job_id, application_id, author_id, target_user_id, author_role,
                    rating, punctuality_ok, paid_on_time, comment, moderation_status
                ) VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, 'pending')""",
                (app["job_id"], app_id, author_id, target_id, author["role"], rating, comment.strip()[:800]),
            )
            for admin_id in self.list_admin_ids():
                conn.execute(
                    "INSERT INTO notifications (user_id, type, title, body, target_tab) VALUES (?, 'review', 'Новый отзыв на модерации', ?, 'admin')",
                    (admin_id, f"{author['name']} оставил оценку {rating}★ — проверьте отзыв в очереди модерации."),
                )
        return {"ok": True}

    def list_pending_reviews(self) -> list[dict]:
        with self._read() as conn:
            rows = conn.execute(
                """SELECT r.*, au.name AS author_name, tu.name AS target_name,
                          tu.role AS target_role, j.title AS job_title
                   FROM reviews r
                   JOIN users au ON au.id = r.author_id
                   JOIN users tu ON tu.id = r.target_user_id
                   JOIN jobs j ON j.id = r.job_id
                   WHERE r.moderation_status = 'pending'
                   ORDER BY r.id ASC"""
            ).fetchall()
            return [self._row(r) for r in rows]

    def moderate_review(self, review_id: int, decision: str):
        if decision not in ("approved", "rejected"):
            return {"ok": False, "error": "Некорректное решение"}
        with self._tx() as conn:
            rev = self._row(conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone())
            if not rev:
                return {"ok": False, "error": "Отзыв не найден"}
            conn.execute(
                "UPDATE reviews SET moderation_status = ? WHERE id = ?", (decision, review_id)
            )
            if decision == "approved":
                conn.execute(
                    "INSERT INTO notifications (user_id, type, title, body, target_tab) VALUES (?, 'review', ?, 'Проверенный отзыв опубликован и учтён в вашем рейтинге.', 'profile')",
                    (rev["target_user_id"], f"Опубликован новый отзыв ({rev['rating']} ★)"),
                )
            return {"ok": True}

    def admin_overview(self) -> dict:
        with self._read() as conn:
            jobs = conn.execute(
                "SELECT COUNT(*) AS cnt, COALESCE(SUM(MAX(slots_total - slots_filled, 0)), 0) AS open_slots, "
                "COALESCE(ROUND(AVG(pay_amount)), 0) AS avg_pay FROM jobs WHERE status = 'active'"
            ).fetchone()
            verified = conn.execute(
                "SELECT COUNT(*) AS cnt FROM users WHERE role = 'employer' AND is_verified = 1"
            ).fetchone()
            pending = conn.execute(
                "SELECT COUNT(*) AS cnt FROM reviews WHERE moderation_status = 'pending'"
            ).fetchone()
            users_cnt = conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
            pending_apps = conn.execute(
                "SELECT COUNT(*) AS cnt FROM applications WHERE status = 'pending'"
            ).fetchone()
            return {
                "open_jobs_count": int(jobs["cnt"]),
                "open_slots_count": int(jobs["open_slots"]),
                "avg_shift_pay": int(jobs["avg_pay"]),
                "verified_employers_count": int(verified["cnt"]),
                "pending_reviews_count": int(pending["cnt"]),
                "total_users_count": int(users_cnt["cnt"]),
                "pending_applications_count": int(pending_apps["cnt"]),
            }

    # ---------- уведомления → Telegram ----------
    def poll_unsent_notifications(self, cursor_id: int) -> list[dict]:
        """Новые уведомления для привязанных пользователей с включённой доставкой."""
        with self._read() as conn:
            rows = conn.execute(
                """SELECT n.*, l.telegram_id
                   FROM notifications n
                   JOIN bot_telegram_links l ON l.user_id = n.user_id
                   WHERE n.id > ? AND l.notify = 1
                   ORDER BY n.id ASC""",
                (cursor_id,),
            ).fetchall()
            return [self._row(r) for r in rows]

    def max_notification_id(self) -> int:
        with self._read() as conn:
            r = conn.execute("SELECT COALESCE(MAX(id), 0) AS m FROM notifications").fetchone()
            return int(r["m"])
