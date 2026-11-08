"""Automated persistence tests, no Kivy/Tkinter needed."""
import json
import sqlite3
import uuid
from pathlib import Path

import pytest

from storage import NotesDB, validate_date, CATEGORIES


@pytest.fixture
def db(tmp_path):
    instance = NotesDB(tmp_path / "notes.db")
    yield instance
    instance.close()


def test_create_note(db):
    key = db.create("Uchrashuv", "Muhokama", "2026-11-10")
    row = db.get(key)
    assert row["title"] == "Uchrashuv"
    assert row["content"] == "Muhokama"
    assert row["event_date"] == "2026-11-10"
    assert db.count() == 1


def test_empty_rejected(db):
    with pytest.raises(ValueError):
        db.create("", " ")
    assert db.count() == 0


def test_default_title(db):
    row = db.get(db.create("", "Matn"))
    assert row["title"] == "Sarlavhasiz qayd"


def test_max_title(db):
    with pytest.raises(ValueError):
        db.create("A" * 121, "x")


def test_too_long_content(db):
    with pytest.raises(ValueError):
        db.create("X", "b" * 100001)


def test_update_preserves_created(db):
    nid = db.create("Avval", "1", "2026-11-10")
    before = db.get(nid)
    assert db.update(nid, "Keyin", "2", "2026-12-20")
    after = db.get(nid)
    assert after["title"] == "Keyin"
    assert after["created_at"] == before["created_at"]
    assert after["event_date"] == "2026-12-20"


def test_update_missing(db):
    assert not db.update(str(uuid.uuid4()), "a", "b")


def test_delete_irreversible(db):
    nid = db.create("abc", "def")
    assert db.delete(nid)
    assert db.get(nid) is None
    assert not db.delete(nid)


def test_delete_specific_only(db):
    first = db.create("Bir", "A")
    second = db.create("Ikki", "B")
    db.delete(first)
    assert db.get(second)["title"] == "Ikki"


def test_duplicate_titles_get_different_uuids(db):
    a = db.create("Bir xil", "A")
    b = db.create("Bir xil", "B")
    assert a != b


def test_categories(db):
    for cat in CATEGORIES:
        db.create(cat, "x", category=cat)
        assert len(db.list_notes(category=cat)) == 1
    with pytest.raises(ValueError):
        db.create("a", "b", category="boshqa")


def test_search_uzbek_casefold(db):
    db.create("Muhim QAYD", "kalendar")
    assert len(db.list_notes(query="qayd")) == 1
    assert len(db.list_notes(query="KALEN")) == 1
    assert len(db.list_notes(query="yo‘q")) == 0


def test_favorite_toggle(db):
    key = db.create("a", "b")
    assert db.list_notes(favorites=True) == []
    assert db.favorite(key)
    assert len(db.list_notes(favorites=True)) == 1
    db.favorite(key, False)
    assert not db.get(key)["is_favorite"]


def test_sort_title(db):
    db.create("Zebra", "a")
    db.create("Alifbo", "b")
    assert [n["title"] for n in db.list_notes(sort="title")] == ["Alifbo", "Zebra"]


def test_sort_date(db):
    db.create("Eski", "a", "2026-01-01")
    db.create("Yangi", "b", "2026-12-30")
    assert db.list_notes(sort="date")[0]["title"] == "Yangi"


def test_date_validation(db):
    assert validate_date("2028-02-29") == "2028-02-29"
    with pytest.raises(ValueError):
        validate_date("2027-02-29")
    with pytest.raises(ValueError):
        validate_date("13/05/2026")


def test_export_import_roundtrip(db, tmp_path):
    db.create("Asosiy", "O‘zbekcha matn", "2026-11-08", "Sayohat", True)
    target = tmp_path / "backup.json"
    assert db.export_json(target) == 1
    assert json.loads(target.read_text(encoding="utf-8"))["author"] == "Mingqulova Rayhona"
    other = NotesDB(tmp_path / "other.db")
    try:
        assert other.import_json(target) == (1, 0)
        note = other.list_notes()[0]
        assert note["category"] == "Sayohat"
        assert note["event_date"] == "2026-11-08"
        assert note["is_favorite"] is True
        assert other.import_json(target) == (0, 1)
    finally:
        other.close()


def test_legacy_html_import(db, tmp_path):
    file = tmp_path / "html.json"
    file.write_text(json.dumps({"app": "Eslatmalar", "notes": [{
        "id": str(uuid.uuid4()), "title": "Veb qayd", "content": "old",
        "createdAt": "2026-11-08T12:00:00.000Z", "updatedAt": "2026-11-08T12:15:00.000Z",
        "noteDate": "2026-11-20"}]}), encoding="utf-8")
    assert db.import_json(file) == (1, 0)
    assert db.list_notes()[0]["event_date"] == "2026-11-20"


def test_invalid_backup_atomic(db, tmp_path):
    file = tmp_path / "corrupt.json"
    file.write_text(json.dumps({"app":"Eslatmalar", "notes": [
        {"id":str(uuid.uuid4()),"title":"Okay", "content":"yes", "createdAt":"2026-11-08T10:00:00Z", "noteDate":"2026-11-08"},
        {"title":"Bad", "content":"", "createdAt":"not a date", "noteDate":"2026-13-08"}
    ]}), encoding="utf-8")
    with pytest.raises(ValueError):
        db.import_json(file)
    assert db.count() == 0


def test_persistent_after_reopen(tmp_path):
    file = tmp_path / "test.db"
    a = NotesDB(file)
    key = a.create("Doimiy", "Yozuv")
    a.close()
    b = NotesDB(file)
    try:
        assert b.get(key)["content"] == "Yozuv"
    finally:
        b.close()


def test_migration_from_old_schema(tmp_path):
    file = tmp_path / "old.db"
    con = sqlite3.connect(file)
    con.execute("""CREATE TABLE notes (
        id TEXT PRIMARY KEY, title TEXT, content TEXT, created_at TEXT, updated_at TEXT)""")
    con.execute("INSERT INTO notes VALUES (?,?,?,?,?)",
                (str(uuid.uuid4()), "Old", "text", "2026-03-15T00:00:00+00:00", "2026-03-15T00:00:00+00:00"))
    con.commit()
    con.close()
    db = NotesDB(file)
    try:
        assert db.list_notes()[0]["event_date"] == "2026-03-15"
        assert db.list_notes()[0]["category"] == "Shaxsiy"
    finally:
        db.close()


def test_prevent_sql_injection(db):
    db.create("normal", "text")
    assert db.list_notes(query="'; DROP TABLE notes;") == []
    assert db.count() == 1


def test_all_dates_for_calendar(db):
    key = db.create("Holiday", "scheduled", "2027-01-01")
    assert db.get(key)["event_date"] == "2027-01-01"
