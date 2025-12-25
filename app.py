import threading
import socket
from flask import Flask, redirect, url_for, session, request
from config import Config
from managers.fw_manager import load_app_ids
from managers.data_manager import db

# ייבוא ה-Blueprints
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.rule_routes import rules_bp
from routes.object_routes import objects_bp
from routes.ops_routes import ops_bp

app = Flask(__name__)
app.config.from_object(Config)

# הרכבת המערכת
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(rules_bp)
app.register_blueprint(objects_bp)
app.register_blueprint(ops_bp)

@app.before_request
def require_login():
    # שים לב: נקודות הקצה משתנות לפי שם ה-Blueprint
    allowed = ['auth.login', 'static']
    if 'user' not in session and request.endpoint not in allowed:
        return redirect(url_for('auth.login'))

def syslog_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: sock.bind((Config.SYSLOG_HOST, Config.SYSLOG_PORT))
    except: return
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            msg = data.decode('utf-8', errors='ignore')
            parts = msg.split(',')
            if len(parts) > 31:
                raw_app = parts[31].strip()
                app_name = db.app_id_map.get(raw_app, raw_app)
                entry = {
                    "time": parts[1], "source": parts[7], "destination": parts[8],
                    "app": app_name, "dst_port": parts[25],
                    "protocol": parts[29].lower() if len(parts)>29 else 'tcp',
                    "src_zone": parts[10], "dst_zone": parts[11], "action": parts[21]
                }
                db.add_traffic_log(entry)
        except: continue

if __name__ == '__main__':
    load_app_ids()
    threading.Thread(target=syslog_listener, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5100, use_reloader=False)