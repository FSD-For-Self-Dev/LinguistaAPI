import sqlite3

with open("sqlite.ddl", "r") as file:
    ddl_query = file.read()

# Подключение к базе данных SQLite
conn = sqlite3.connect('sqlite3.db')
cursor = conn.cursor()

# Выполнение DDL-запроса для создания таблицы
cursor.executescript(ddl_query)

# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()