from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db_sql = SQLAlchemy()

class RuleRequest(db_sql.Model):
    __tablename__ = 'rule_requests'
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    rule_name = db_sql.Column(db_sql.String(100), nullable=False)
    requested_by = db_sql.Column(db_sql.String(50), nullable=False) # שם היוזר
    from_zone = db_sql.Column(db_sql.String(50))
    to_zone = db_sql.Column(db_sql.String(50))
    source_ip = db_sql.Column(db_sql.String(100))
    destination_ip = db_sql.Column(db_sql.String(100))
    service_port = db_sql.Column(db_sql.String(20))
    protocol = db_sql.Column(db_sql.String(10), default='tcp')
    application = db_sql.Column(db_sql.String(50))
    tag = db_sql.Column(db_sql.String(50))
    group_tag = db_sql.Column(db_sql.String(50))
    
    # ניהול סטטוס
    status = db_sql.Column(db_sql.String(20), default='Pending') # Pending, Approved, Rejected
    request_time = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    processed_by = db_sql.Column(db_sql.String(50)) # שם האדמין שאישר/דחה
    admin_notes = db_sql.Column(db_sql.Text) # סיבת דחייה או הערות
    final_rule_name = db_sql.Column(db_sql.String(120)) # השם הסופי שנוצר בפועל

class ObjectRequest(db_sql.Model):
    __tablename__ = 'object_requests'
    id = db_sql.Column(db_sql.Integer, primary_key=True)
    obj_type = db_sql.Column(db_sql.String(30)) # address, service, etc.
    name = db_sql.Column(db_sql.String(100))
    value = db_sql.Column(db_sql.String(200))
    prefix = db_sql.Column(db_sql.String(10))
    protocol = db_sql.Column(db_sql.String(10))
    requested_by = db_sql.Column(db_sql.String(50))
    status = db_sql.Column(db_sql.String(20), default='Pending')
    request_time = db_sql.Column(db_sql.DateTime, default=datetime.utcnow)
    admin_notes = db_sql.Column(db_sql.Text)