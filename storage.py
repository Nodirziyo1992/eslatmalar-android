"""ESLATMALAR — shared, dependency-free SQLite note storage.

Works on desktop Python and on python-for-android. No network dependency.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

AUTHOR = "Mingqulova Rayhona"
CATEGORIES = ("Shaxsiy", "Ish", "Sayohat", "Salomatlik")
MAX_TITLE = 120
MAX_CONTENT = 100_000
MAX_BACKUP_BYTES = 15 * 1024 * 1024


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def current_date() -> str:
    return date.today().isoformat()


def validate_date(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("To‘g‘ri sanani kiriting.")
    try:
        if len(value) != 10 or date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError:
        raise ValueError("Sana YYYY-MM-DD shaklida bo‘lishi kerak.") from None
    return value


def validate_category(value: str) -> str:
    if value not in CATEGORIES:
        raise ValueError("Noto‘g‘ri toifa tanlangan.")
    return value


def check_note(title: str, content: str) -> tuple[str, str]:
    if not isinstance(title, str) or not isinstance(content, str):
        raise ValueError("Sarlavha va matn to‘g‘ri bo‘lishi kerak.")
    title = title.strip()
    content = content.strip()
    if not title and not content:
        raise ValueError("Sarlavha yoki qayd matnini kiriting.")
    if len(title) > MAX_TITLE:
        raise ValueError("Sarlavha 120 ta belgidan oshmasin.")
    if len(content) > MAX_CONTENT:
        raise ValueError("Qayd juda uzun (100 000 belgidan oshmasin).")
    return title or "Sarlavhasiz qayd", content


def normalized(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["is_favorite"] = bool(d["is_favorite"])
    return d


class NotesDB:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(self.path), timeout=10)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA busy_timeout=10000")
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("""CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            event_date TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'Shaxsiy',
            is_favorite INTEGER NOT NULL DEFAULT 0
        )""")
        # Migrate earlier SQLite builds without losing old notes.
        existing = {x["name"] for x in self.con.execute("PRAGMA table_info(notes)")}
        if "event_date" not in existing:
            self.con.execute("ALTER TABLE notes ADD COLUMN event_date TEXT NOT NULL DEFAULT ''")
        if "category" not in existing:
            self.con.execute("ALTER TABLE notes ADD COLUMN category TEXT NOT NULL DEFAULT 'Shaxsiy'")
        if "is_favorite" not in existing:
            self.con.execute("ALTER TABLE notes ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0")
        old = self.con.execute("SELECT id, created_at FROM notes WHERE event_date='' OR event_date IS NULL").fetchall()
        for r in old:
            day = str(r["created_at"])[:10]
            try:
                day = validate_date(day)
            except ValueError:
                day = current_date()
            self.con.execute("UPDATE notes SET event_date=? WHERE id=?", (day, r["id"]))
        self.con.commit()

    def close(self) -> None:
        self.con.close()

    def create(self, title: str, content: str, event_date: str | None = None,
               category: str = "Shaxsiy", favorite: bool = False) -> str:
        title, content = check_note(title, content)
        day = validate_date(event_date or current_date())
        category = validate_category(category)
        identifier = str(uuid.uuid4())
        ts = now_iso()
        with self.con:
            self.con.execute("""INSERT INTO notes
                (id,title,content,created_at,updated_at,event_date,category,is_favorite)
                VALUES (?,?,?,?,?,?,?,?)""",
                (identifier, title, content, ts, ts, day, category, int(favorite)))
        return identifier

    def update(self, identifier: str, title: str, content: str,
               event_date: str | None = None, category: str | None = None) -> bool:
        title, content = check_note(title, content)
        original = self.get(identifier)
        if original is None:
            return False
        day = validate_date(event_date or original["event_date"])
        cat = validate_category(category or original["category"])
        with self.con:
            result = self.con.execute("""UPDATE notes SET title=?, content=?, updated_at=?,
                event_date=?, category=? WHERE id=?""",
                (title, content, now_iso(), day, cat, identifier))
        return result.rowcount == 1

    def delete(self, identifier: str) -> bool:
        with self.con:
            result = self.con.execute("DELETE FROM notes WHERE id=?", (identifier,))
        return result.rowcount == 1

    def favorite(self, identifier: str, enabled: bool | None = None) -> bool:
        original = self.get(identifier)
        if not original:
            return False
        new_value = int(not original["is_favorite"] if enabled is None else enabled)
        with self.con:
            result = self.con.execute("UPDATE notes SET is_favorite=? WHERE id=?", (new_value, identifier))
        return result.rowcount == 1

    def get(self, identifier: str) -> dict | None:
        row = self.con.execute("SELECT * FROM notes WHERE id=?", (identifier,)).fetchone()
        return normalized(row) if row else None

    def list_notes(self, query: str = "", sort: str = "updated_desc",
                   category: str | None = None, favorites: bool = False) -> list[dict]:
        orders = {
            "updated_desc": "updated_at DESC, created_at DESC, id DESC",
            "newest": "created_at DESC, id DESC",
            "oldest": "created_at ASC, id ASC",
            "date": "event_date DESC, updated_at DESC",
            "title": "title COLLATE NOCASE ASC, id ASC",
        }
        order = orders.get(sort, orders["updated_desc"])
        clauses, args = [], []
        if category in CATEGORIES:
            clauses.append("category=?")
            args.append(category)
        if favorites:
            clauses.append("is_favorite=1")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = self.con.execute(f"SELECT * FROM notes{where} ORDER BY {order}", args).fetchall()
        result = [normalized(r) for r in rows]
        if query.strip():
            q = query.casefold().strip()
            result = [r for r in result if q in r["title"].casefold() or q in r["content"].casefold()]
        return result

    def count(self) -> int:
        return self.con.execute("SELECT COUNT(*) FROM notes").fetchone()[0]

    def export_json(self, path: str | Path) -> int:
        notes = self.list_notes()
        obj = {"app": "Eslatmalar", "author": AUTHOR, "version": 2,
               "exportedAt": now_iso(), "notes": notes}
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        return len(notes)

    def import_json(self, path: str | Path) -> tuple[int, int]:
        """Merge a Python backup or earlier HTML export by UUID, atomically."""
        path = Path(path)
        if path.stat().st_size > MAX_BACKUP_BYTES:
            raise ValueError("Zaxira fayli 15 MB dan oshmasin.")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("notes"), list):
            raise ValueError("Zaxira fayli noto‘g‘ri.")
        if data.get("app", "").lower() not in ("eslatmalar", "notes"):
            raise ValueError("Ushbu fayl Eslatmalar zaxirasi emas.")
        if len(data["notes"]) > 10000:
            raise ValueError("Zaxirada eslatmalar soni juda ko‘p.")
        prepared, seen = [], set()
        for record in data["notes"]:
            if not isinstance(record, dict):
                raise ValueError("Zaxira tarkibi noto‘g‘ri.")
            title, content = check_note(record.get("title"), record.get("content"))
            raw_id = record.get("id")
            try:
                identifier = str(uuid.UUID(str(raw_id)))
            except ValueError:
                identifier = str(uuid.uuid4())
            if identifier in seen:
                raise ValueError("Takroriy qayd ID mavjud.")
            seen.add(identifier)
            created = record.get("created_at", record.get("createdAt", now_iso()))
            updated = record.get("updated_at", record.get("updatedAt", created))
            for stamp in (created, updated):
                if not isinstance(stamp, str) or len(stamp) > 64:
                    raise ValueError("Qayd sanasi buzilgan.")
                try:
                    datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                except ValueError:
                    raise ValueError("Qayd vaqti noto‘g‘ri.") from None
            event_date = record.get("event_date", record.get("noteDate", str(created)[:10]))
            event_date = validate_date(event_date)
            category = record.get("category", "Shaxsiy")
            if category not in CATEGORIES:
                category = "Shaxsiy"
            fav = int(bool(record.get("is_favorite", record.get("isFavorite", False))))
            prepared.append((identifier, title, content, created, updated, event_date, category, fav))
        inserted = skipped = 0
        with self.con:
            for row in prepared:
                cur = self.con.execute("""INSERT OR IGNORE INTO notes
                (id,title,content,created_at,updated_at,event_date,category,is_favorite)
                VALUES (?,?,?,?,?,?,?,?)""", row)
                if cur.rowcount:
                    inserted += 1
                else:
                    skipped += 1
        return inserted, skipped
