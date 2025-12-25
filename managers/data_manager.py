# managers/data_manager.py

class DataManager:
    def __init__(self):
        # --- אזור הזיכרון הזמני (בעתיד יוחלף בטבלאות DB) ---
        self.traffic_logs = []
        self.app_id_map = {}
        
        self.pending_rules = []
        self.approved_history = []
        
        self.pending_objects = []
        self.object_history = []
        
        # Cache לא צריך DB, הוא נשאר בזיכרון
        self.firewall_cache = {"data": None, "last_updated": 0}

    # --- פונקציות לניהול חוקות ---
    def add_pending_rule(self, rule):
        # בעתיד: INSERT INTO pending_rules ...
        self.pending_rules.append(rule)

    def get_pending_rules(self):
        # בעתיד: SELECT * FROM pending_rules
        return self.pending_rules

    def remove_pending_rule(self, rule_id):
        self.pending_rules = [r for r in self.pending_rules if r.get('id') != rule_id]

    def add_history_rule(self, rule):
        self.approved_history.append(rule)

    def get_history_rules(self):
        return self.approved_history

    # --- פונקציות לניהול אובייקטים ---
    def add_pending_object(self, obj):
        self.pending_objects.append(obj)

    def get_pending_objects(self):
        return self.pending_objects

    def remove_pending_object(self, obj_id):
        self.pending_objects = [o for o in self.pending_objects if o.get('id') != obj_id]

    def add_history_object(self, obj):
        self.object_history.append(obj)
        
    def get_history_objects(self):
        return self.object_history

    # --- לוגים ---
    def add_traffic_log(self, log_entry):
        self.traffic_logs.insert(0, log_entry)
        if len(self.traffic_logs) > 100:
            self.traffic_logs.pop()

# יצירת מופע יחיד (Singleton) זמין לכל הקבצים
db = DataManager()