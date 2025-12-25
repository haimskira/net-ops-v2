from managers.models import db_sql, RuleRequest, ObjectRequest
from datetime import datetime

class DataManager:
    def __init__(self):
        # לוגים ו-Cache נשארים בזיכרון (כי הם זמניים ומהירים)
        self.traffic_logs = []
        self.app_id_map = {}
        self.firewall_cache = {"data": None, "last_updated": 0}

    # --- ניהול חוקות (Rules) ---
    
    def add_pending_rule(self, data):
        """שמירת בקשת חוקה חדשה ב-DB"""
        new_rule = RuleRequest(
            rule_name=data.get('rule_name'),
            requested_by=data.get('requested_by'),
            from_zone=data.get('from_zone'),
            to_zone=data.get('to_zone'),
            source_ip=data.get('source_ip'),
            destination_ip=data.get('destination_ip'),
            service_port=data.get('service_port'),
            protocol=data.get('protocol', 'tcp'),
            application=data.get('application'),
            tag=data.get('tag'),
            group_tag=data.get('group_tag'),
            status='Pending'
        )
        db_sql.session.add(new_rule)
        db_sql.session.commit()

    def get_admin_view_rules(self):
        """אדמין רואה הכל - קודם את הממתינים ואז את ההיסטוריה"""
        return RuleRequest.query.order_by(RuleRequest.request_time.desc()).all()

    def get_user_requests(self, username):
        """משתמש רואה רק את הבקשות שלו"""
        return RuleRequest.query.filter_by(requested_by=username).order_by(RuleRequest.request_time.desc()).all()

    def update_rule_status(self, rule_id, status, admin_name, final_name=None, notes=None):
        """עדכון סטטוס חוקה (אישור/דחייה) עם הערות אדמין"""
        rule = RuleRequest.query.get(rule_id)
        if rule:
            rule.status = status
            rule.processed_by = admin_name
            rule.admin_notes = notes
            if final_name:
                rule.final_rule_name = final_name
            db_sql.session.commit()
            return True
        return False

    # --- ניהול אובייקטים (Objects) ---

    def add_pending_object(self, data):
        new_obj = ObjectRequest(
            obj_type=data.get('type'),
            name=data.get('name'),
            value=data.get('value'),
            prefix=data.get('prefix'),
            protocol=data.get('protocol'),
            requested_by=data.get('requested_by'),
            status='Pending'
        )
        db_sql.session.add(new_obj)
        db_sql.session.commit()

    def get_admin_objects(self):
        return ObjectRequest.query.order_by(ObjectRequest.request_time.desc()).all()

    def get_user_objects(self, username):
        return ObjectRequest.query.filter_by(requested_by=username).order_by(ObjectRequest.request_time.desc()).all()

    def update_object_status(self, obj_id, status, notes=None):
        obj = ObjectRequest.query.get(obj_id)
        if obj:
            obj.status = status
            obj.admin_notes = notes
            db_sql.session.commit()
            return True
        return False

    # --- ניהול לוגים (Traffic Logs) ---

    def add_traffic_log(self, log_entry):
        """הוספת לוג חדש לראש הרשימה והגבלת גודל ל-100 לוגים"""
        self.traffic_logs.insert(0, log_entry)
        if len(self.traffic_logs) > 100:
            self.traffic_logs.pop()

# Singleton instance
db = DataManager()