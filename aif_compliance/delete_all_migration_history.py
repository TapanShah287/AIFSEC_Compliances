import sqlite3
import os

# Path to your SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'db.sqlite3')
DB_PATH = os.path.abspath(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("DELETE FROM django_migrations;")
    print('All migration history deleted successfully.')
except Exception as e:
    print(f'Error deleting migration history: {e}')
finally:
    conn.commit()
    conn.close()
