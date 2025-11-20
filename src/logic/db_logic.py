import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional


DB_NAME = "receipts.db"  # имя файла базы данных


class Database:
    """Класс для работы с базой данных чеков"""

    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self._init_db()

    # ---------------- ИНИЦИАЛИЗАЦИЯ ----------------
    def _init_db(self):
        """Создает таблицу, если она отсутствует"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                amount REAL,
                product TEXT,
                store TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    # ---------------- ЗАПИСЬ ----------------
    def add_purchase(self, data: Dict[str, Any]) -> None:
        """
        Добавляет покупку в базу.
        Ожидает словарь:
        {
            "user_id": int,
            "username": str,
            "first_name": str,
            "last_name": str,
            "amount": float,
            "product": str,
            "store": str
        }
        """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO purchases (user_id, username, first_name, last_name, amount, product, store)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("user_id"),
            data.get("username"),
            data.get("first_name"),
            data.get("last_name"),
            data.get("amount"),
            data.get("product"),
            data.get("store")
        ))
        conn.commit()
        conn.close()

    # ---------------- ПОЛУЧЕНИЕ ----------------
    def get_user_purchases(self, user_id: int) -> List[Dict[str, Any]]:
        """Возвращает все покупки пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT amount, product, store, created_at
            FROM purchases
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "amount": row[0],
                "product": row[1],
                "store": row[2],
                "created_at": row[3]
            }
            for row in rows
        ]

    def get_all_purchases(self) -> List[Dict[str, Any]]:
        """Возвращает все покупки"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, user_id, username, amount, product, store, created_at
            FROM purchases
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "user_id": row[1],
                "username": row[2],
                "amount": row[3],
                "product": row[4],
                "store": row[5],
                "created_at": row[6]
            }
            for row in rows
        ]

    # ---------------- УДАЛЕНИЕ / ОЧИСТКА ----------------
    def clear_user_purchases(self, user_id: int) -> None:
        """Удаляет все покупки пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM purchases WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

