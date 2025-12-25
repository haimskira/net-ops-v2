import os
import threading
import socket
from datetime import datetime
from flask import Flask, redirect, url_for, session, request

# ייבוא רכיבי המערכת
from managers.models import db_sql
from config import Config
from managers.fw_manager import load_app_ids
from managers.data_manager import db # מופע ה-Singleton

# ייבוא ה-Blueprints
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.rule_routes import rules_bp
from routes.object_routes import objects_bp
from routes.ops_routes import ops_bp

app = Flask(__name__)
app.config.from_object(Config)

# 1. טיפול בתיקיית ה-Database (עבור SQLite)
db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
if db_uri.startswith('sqlite:///'):
    # מחלץ את נתיב הקובץ ומבטיח שהתיקייה קיימת
    db_path = db_uri.replace('sqlite:///', '')
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

# 2. אתחול מסד הנתונים
db_sql.init_app(app)

with app.app_context():
    db_sql.create_all()

# 3. רישום Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(rules_bp)
app.register_blueprint(objects_bp)
app.register_blueprint(ops_bp)

# 4. הגנה על נתיבי המערכת (Login Required)
@app.before_request
def require_login():
    allowed = ['auth.login', 'static']
    if 'user' not in session and request.endpoint not in allowed:
        return redirect(url_for('auth.login'))

# 5. Syslog Listener - המנוע של ה-Live Logs
def syslog_listener():
    """מאזין ללוגים מהפיירוול ומזרים אותם ל-DataManager"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # הקשבה על כל הכתובות בפורט המוגדר
        sock.bind(('0.0.0.0', Config.SYSLOG_PORT))
        print(f"[*] Syslog Listener active on port {Config.SYSLOG_PORT}")
    except Exception as e:
        print(f"[!] Syslog Bind Error: {e}")
        return

    while True:
        try:
            data, _ = sock.recvfrom(4096)
            msg = data.decode('utf-8', errors='ignore')
            
            # פיענוח הפורמט של Palo Alto (CSV)
            parts = msg.split(',')
            if len(parts) > 31:
                raw_app = parts[31].strip()
                # שימוש במיפוי App-ID שנטען ב-FW Manager
                app_name = db.app_id_map.get(raw_app, raw_app)
                
                entry = {
                    "time": datetime.now().strftime("%H:%M:%S"), # שימוש בזמן מקומי לתצוגה חיה
                    "source": parts[7],
                    "destination": parts[8],
                    "app": app_name,
                    "dst_port": parts[25],
                    "protocol": parts[29].lower() if len(parts) > 29 else 'tcp',
                    "src_zone": parts[10],
                    "dst_zone": parts[11],
                    "action": parts[21]
                }
                # הזרקת הלוג לזיכרון המשותף
                db.add_traffic_log(entry)
        except:
            continue

# 6. הפעלה
if __name__ == '__main__':
    # טעינת שמות האפליקציות מהפיירוול לזיכרון
    load_app_ids()
    
    # הפעלת ה-Thread של הלוגים (Daemon מבטיח שהוא ייסגר עם האפליקציה)
    log_thread = threading.Thread(target=syslog_listener, daemon=True)
    log_thread.start()
    
    # הרצת השרת. הערה: use_reloader=False קריטי כדי שה-Thread לא יופעל פעמיים
    app.run(debug=True, host='0.0.0.0', port=5100, use_reloader=False)
    