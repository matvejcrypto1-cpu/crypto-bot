import sqlite3

DB_NAME = 'bot.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT
            )
        ''')
        conn.commit()

def set_user_lang(user_id: int, lang: str):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (user_id, lang)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang
        ''', (user_id, lang))
        conn.commit()

def get_user_lang(user_id: int) -> str:
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT lang FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else 'en'
