
import sqlite3

def get_db():
    return sqlite3.connect('bot.db')

def init_db() -> None:
    connection = get_db()
    c = connection.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER UNIQUE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS nominations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nominator_id INTEGER,
            nominee_id INTEGER,
            video_url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            fulfilled INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS fulfillments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomination_id INTEGER,
            fulfilled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    connection.commit()
    connection.close()
