from flask import Flask, render_template, request, redirect, url_for, g, jsonify
import sqlite3

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM templates")
    templates = cur.fetchall()
    return render_template('index.html', templates=templates)

@app.route('/create_template', methods=['GET', 'POST'])
def create_template():
    if request.method == 'POST':
        name = request.form['template_name']
        content_field = 'content_field' in request.form
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO templates (name, content_field) VALUES (?, ?)", (name, content_field))
        template_id = cur.lastrowid
        field_names = request.form.getlist('field_names[]')
        field_types = request.form.getlist('field_types[]')
        for field_name, field_type in zip(field_names, field_types):
            cur.execute("INSERT INTO fields (template_id, field_name, field_type) VALUES (?, ?, ?)", (template_id, field_name, field_type))
        db.commit()
        return redirect(url_for('index'))
    return render_template('create_template.html')




@app.route('/view/<int:template_id>')
def view_template(template_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT name, content_field FROM templates WHERE id = ?", (template_id,))
    template = cur.fetchone()
    cur.execute("SELECT field_name, field_type FROM fields WHERE template_id = ?", (template_id,))
    fields = cur.fetchall()

    # Получаем последний экземпляр шаблона
    cur.execute("SELECT * FROM template_instances WHERE template_id = ? ORDER BY id DESC LIMIT 1", (template_id,))
    instance = cur.fetchone()
    instance_fields = []
    email_contents = []
    if instance:
        cur.execute("SELECT field_name, field_value, completed FROM instance_fields WHERE instance_id = ?",
                    (instance['id'],))
        instance_fields = cur.fetchall()
        cur.execute("SELECT email_field_name, content FROM email_contents WHERE instance_id = ?", (instance['id'],))
        email_contents = cur.fetchall()

    return render_template('view_template.html', template=template, fields=fields, instance=instance,
                           instance_fields=instance_fields, email_contents=email_contents)


@app.route('/run/<int:template_id>', methods=['GET', 'POST'])
def run_template(template_id):
    db = get_db()
    cur = db.cursor()
    if request.method == 'POST':
        cur.execute("INSERT INTO template_instances (template_id) VALUES (?)", (template_id,))
        instance_id = cur.lastrowid

        for field_name, field_value in request.form.items():
            if field_name.startswith('content_'):
                email_field_name = field_name[len('content_'):]
                cur.execute("INSERT INTO email_contents (instance_id, email_field_name, content) VALUES (?, ?, ?)",
                            (instance_id, email_field_name, field_value))
            else:
                cur.execute("INSERT INTO instance_fields (instance_id, field_name, field_value) VALUES (?, ?, ?)",
                            (instance_id, field_name, field_value))

        db.commit()
        return redirect(url_for('index'))
    else:
        cur.execute("SELECT name FROM templates WHERE id = ?", (template_id,))
        template_name = cur.fetchone()['name']
        cur.execute("SELECT field_name, field_type FROM fields WHERE template_id = ?", (template_id,))
        fields = cur.fetchall()

        # Получаем последнюю заполненную форму для текущего шаблона
        cur.execute("SELECT * FROM template_instances WHERE template_id = ? ORDER BY id DESC LIMIT 1", (template_id,))
        instance = cur.fetchone()

        instance_fields = []
        email_contents = []
        if instance:
            cur.execute("SELECT field_name, field_value, completed FROM instance_fields WHERE instance_id = ?",
                        (instance['id'],))
            instance_fields = cur.fetchall()
            cur.execute("SELECT email_field_name, content FROM email_contents WHERE instance_id = ?", (instance['id'],))
            email_contents = cur.fetchall()

        # Если instance пустой, передаем None для instance_id
        instance_id = instance['id'] if instance else None

        return render_template('run_template.html', template_name=template_name, fields=fields,
                               instance_fields=instance_fields, email_contents=email_contents, instance_id=instance_id)


@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.get_json()
    instance_id = data['instance_id']
    field_name = data['field_name']
    completed = data['completed']
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE instance_fields SET completed = ? WHERE instance_id = ? AND field_name = ?", (completed, instance_id, field_name))
    db.commit()
    return jsonify({'status': 'success'})

@app.route('/update_field_type', methods=['POST'])
def update_field_type():
    data = request.get_json()
    field_id = data['field_id']
    new_field_type = data['new_field_type']
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE fields SET field_type = ? WHERE id = ?", (new_field_type, field_id))
    db.commit()
    return jsonify({'status': 'success'})


def process_email_content(email_field_name, content, cursor, instance_id):
    # Сохранение содержимого письма
    cursor.execute("INSERT INTO email_contents (instance_id, email_field_name, content) VALUES (?, ?, ?)", (instance_id, email_field_name, content))

if __name__ == '__main__':
    app.run(debug=True)
