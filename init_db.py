import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Создаем таблицу шаблонов с дополнительным столбцом content_field
    c.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content_field INTEGER NOT NULL DEFAULT 0
        );
    ''')

    # Создаем таблицу для полей шаблонов
    c.execute('''
        CREATE TABLE IF NOT EXISTS fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        );
    ''')

    # Создаем таблицу для экземпляров шаблонов
    c.execute('''
        CREATE TABLE IF NOT EXISTS template_instances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER,
            content TEXT,
            FOREIGN KEY (template_id) REFERENCES templates(id)
        );
    ''')

    # Создаем таблицу для значений полей экземпляров шаблонов
    c.execute('''
        CREATE TABLE IF NOT EXISTS instance_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id INTEGER,
            field_name TEXT NOT NULL,
            field_value TEXT NOT NULL,
            FOREIGN KEY (instance_id) REFERENCES template_instances(id)
        );
    ''')

    # Проверяем наличие столбца 'completed' в таблице 'instance_fields'
    c.execute("PRAGMA table_info(instance_fields)")
    columns = [col[1] for col in c.fetchall()]
    if 'completed' not in columns:
        c.execute('''
            ALTER TABLE instance_fields ADD COLUMN completed INTEGER DEFAULT 0;
        ''')

    # Создаем таблицу для содержимого электронных писем
    c.execute('''
        CREATE TABLE IF NOT EXISTS email_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            instance_id INTEGER,
            email_field_name TEXT,
            content TEXT,
            FOREIGN KEY (instance_id) REFERENCES template_instances(id)
        );
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
