from flask import Blueprint, request, jsonify, session
from datetime import datetime
import time
from managers.data_manager import db
from managers.fw_manager import get_fw_connection, CustomSecurityRule, ensure_service_object
from panos.policies import Rulebase
from managers.models import RuleRequest # ייבוא המודל לצורך שאילתות ישירות במידת הצורך

rules_bp = Blueprint('rules', __name__)

@rules_bp.route('/create-rule', methods=['POST'])
def create_rule():
    data = request.json
    try:
        data['requested_by'] = session.get('user', 'Unknown')
        # ה-ID נוצר אוטומטית ב-DB כ-Primary Key, אז לא חייבים ליצור ידנית
        db.add_pending_rule(data)
        return jsonify({"status": "success", "message": "החוקה נשלחה לאישור אדמין!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@rules_bp.route('/get-admin-view-rules')
def get_admin_view_rules():
    if not session.get('is_admin'): return jsonify([])
    rules = db.get_admin_view_rules()
    # המרת אובייקטי SQLAlchemy למילונים לצורך JSON
    return jsonify([r.to_dict() if hasattr(r, 'to_dict') else {c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rules])

@rules_bp.route('/get-my-requests')
def get_my_requests():
    user = session.get('user')
    rules = db.get_user_requests(user)
    return jsonify([{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rules])

@rules_bp.route('/approve-single-rule/<int:rule_id>', methods=['POST'])
def approve_single_rule(rule_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    
    # שליפת הבקשה מה-DB באמצעות SQLAlchemy
    from managers.models import RuleRequest
    rule_req = RuleRequest.query.get(rule_id)
    
    if not rule_req or rule_req.status != 'Pending':
        return jsonify({"status": "error", "message": "בקשה לא נמצאה או שכבר טופלה"}), 404

    try:
        fw = get_fw_connection()
        rulebase = Rulebase()
        fw.add(rulebase)
        
        svc_name = ensure_service_object(fw, str(rule_req.service_port), rule_req.protocol or 'tcp')
        final_rule_name = f"{rule_req.rule_name}_{int(time.time() % 10000)}"
        
        new_rule = CustomSecurityRule(
            name=final_rule_name,
            fromzone=[rule_req.from_zone], tozone=[rule_req.to_zone],
            source=[rule_req.source_ip], destination=[rule_req.destination_ip],
            application=[rule_req.application], service=[svc_name],
            tag=[rule_req.tag] if rule_req.tag and rule_req.tag != "None" else [],
            action='allow', group_tag=rule_req.group_tag
        )
        rulebase.add(new_rule)
        new_rule.create()

        # עדכון הסטטוס ב-DB ל-Approved
        db.update_rule_status(rule_id, 'Approved', session.get('user'), final_name=final_rule_name)
        
        return jsonify({"status": "success", "message": f"החוקה {final_rule_name} נוצרה."})
    except Exception as e: 
        return jsonify({"status": "error", "message": str(e)}), 500

@rules_bp.route('/reject-single-rule/<int:rule_id>', methods=['POST'])
def reject_single_rule(rule_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    
    data = request.json
    reason = data.get('reason', 'לא צוינה סיבה')
    admin_name = session.get('user', 'Admin')

    success = db.update_rule_status(rule_id, 'Rejected', admin_name, notes=reason)
    if success:
        return jsonify({"status": "success", "message": "החוקה נדחתה"})
    return jsonify({"status": "error", "message": "בקשה לא נמצאה"}), 404