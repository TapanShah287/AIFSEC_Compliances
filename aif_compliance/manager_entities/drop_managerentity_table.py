import sqlite3
import os

# Path to your SQLite database
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'db.sqlite3')
DB_PATH = os.path.abspath(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute('DROP TABLE IF EXISTS manager_entities_managerentity;')
    print('Table manager_entities_managerentity dropped successfully.')
except Exception as e:
    print(f'Error dropping table: {e}')
finally:
    conn.commit()
    conn.close()
