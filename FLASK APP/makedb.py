import sqlite3

conn = sqlite3.connect('mydatabase.db')

c = conn.cursor()
c.execute('ALTER TABLE users ADD COLUMN id INTEGER NOT NULL UNIQUE AUTO_INCREMENT')

conn.commit()
conn.close()