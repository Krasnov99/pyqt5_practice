# Подключение к БД SQLite
import sqlite3
import os

DB_FILE = "calendar.db"

class DatabaseManager:
    def __init__(self):
        self.conn = None

    def init_db(self):
        """Создание таблицы событий при первом запуске"""
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                time TEXT NOT NULL,
                type TEXT,
                notes TEXT,
                image_path TEXT
            )
        """)
        self.conn.commit()

    def get_events_by_date(self, date_str):
        """Получение событий на конкретную дату"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events WHERE date = ? ORDER BY time", (date_str,))
        return cursor.fetchall()

    def check_overlap(self, date_str, time_str, event_id=None):
        """Проверка пересечения времени событий"""
        cursor = self.conn.cursor()
        if event_id:
            cursor.execute("SELECT id FROM events WHERE date = ? AND time = ? AND id != ?", (date_str, time_str, event_id))
        else:
            cursor.execute("SELECT id FROM events WHERE date = ? AND time = ?", (date_str, time_str))
        return cursor.fetchone() is not None

    def insert_record(self, data):
        """Добавление нового события"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO events (date, title, time, type, notes, image_path) VALUES (?, ?, ?, ?, ?, ?)",
            (data["date"], data["title"], data["time"], data["type"], data["notes"], data["image_path"])
        )
        self.conn.commit()

    def update_record(self, data):
        """Обновление события"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE events SET date=?, title=?, time=?, type=?, notes=?, image_path=? WHERE id=?",
            (data["date"], data["title"], data["time"], data["type"], data["notes"], data["image_path"], data["id"])
        )
        self.conn.commit()

    def delete_record(self, item_id):
        """Удаление события"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM events WHERE id=?", (item_id,))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
