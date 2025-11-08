import os, json, sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, jsonify
from pywebpush import webpush, WebPushException
from werkzeug.utils import secure_filename

VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": "mailto:you@example.com"}

UPLOAD_FOLDER = 'static/uploads'
DB_PATH = 'database.db'
ALLOWED_EXT = {'png','jpg','jpeg','gif'}
ADMIN_NUMBER = "1430"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = Flask(__name__)
app.secret_key = 'supersecret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# قاعدة البيانات
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscriptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        endpoint TEXT UNIQUE,
        keys TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        body TEXT,
        image TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()
init_db()

# الصفحات
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user')
def user():
    conn = get_db()
    rows = conn.execute('SELECT * FROM notifications ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('user.html', notifications=rows, vapid_public_key=VAPID_PUBLIC_KEY)

@app.route('/admin')
def admin_login():
    return render_template('admin_login.html')

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    number = request.form.get('number','')
    if number != ADMIN_NUMBER:
        flash("الرقم الوظيفي غير صحيح")
        return redirect(url_for('admin_login'))
    conn = get_db()
    rows = conn.execute('SELECT * FROM notifications ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', notifications=rows)

@app.route('/send', methods=['POST'])
def send_notification():
    title = request.form.get('title')
    body = request.form.get('body')
    image = None
    file = request.files.get('image')
    if file and '.' in file.filename:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        image = '/static/uploads/' + filename

    conn = get_db()
    conn.execute('INSERT INTO notifications(title,body,image) VALUES (?,?,?)',(title,body,image))
    conn.commit()
    conn.close()

    conn = get_db()
    subs = conn.execute('SELECT * FROM subscriptions').fetchall()
    conn.close()
    payload={"title":title,"body":body,"image":image}
    for s in subs:
        try:
            keys = json.loads(s['keys'])
            webpush(subscription_info={"endpoint":s['endpoint'],"keys":keys},
                    data=json.dumps(payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS)
        except WebPushException:
            pass
    flash("تم الإرسال")
    return redirect(url_for('admin_panel'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete_notification(id):
    conn = get_db()
    conn.execute('DELETE FROM notifications WHERE id=?',(id,))
    conn.commit(); conn.close()
    flash("تم الحذف")
    return redirect(url_for('admin_panel'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data=request.get_json()
    endpoint=data.get('endpoint')
    keys=data.get('keys')
    conn=get_db()
    conn.execute('INSERT OR REPLACE INTO subscriptions(endpoint,keys) VALUES (?,?)',(endpoint,json.dumps(keys)))
    conn.commit(); conn.close()
    return jsonify({"ok":True})

if __name__=="__main__":
    app.run(debug=True,port=5000)