from flask import Blueprint, request, jsonify, session
from datetime import datetime
import time
from managers.data_manager import db
from managers.fw_manager import get_fw_connection, CustomSecurityRule, ensure_service_object
from panos.policies import Rulebase

rules_bp = Blueprint('rules', __name__)

@rules_bp.route('/create-rule', methods=['POST'])
def create_rule():
    data = request.json
    try:
        data['id'] = int(time.time() * 1000)
        data['requested_by'] = session.get('user', 'Unknown')
        data['request_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.add_pending_rule(data)
        return jsonify({"status": "success", "message": "החוקה נשלחה לאישור אדמין!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@rules_bp.route('/get-pending-rules', methods=['GET'])
def get_pending_rules():
    return jsonify(db.get_pending_rules())

@rules_bp.route('/get-admin-view-rules')
def get_admin_view_rules():
    if not session.get('is_admin'): return jsonify([])
    # איחוד רשימות לצורך תצוגה
    pending = [{**r, 'status': 'Pending'} for r in db.get_pending_rules()]
    history = db.get_history_rules()
    return jsonify(pending + history)

@rules_bp.route('/get-my-requests')
def get_my_requests():
    user = session.get('user')
    pending = [dict(r, status='Pending') for r in db.get_pending_rules() if r.get('requested_by') == user]
    history = [r for r in db.get_history_rules() if r.get('requested_by') == user]
    return jsonify(pending + history)

@rules_bp.route('/approve-single-rule/<int:rule_id>', methods=['POST'])
def approve_single_rule(rule_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    
    # חיפוש החוקה ב-DB
    rule_data = next((r for r in db.get_pending_rules() if r.get('id') == rule_id), None)
    if not rule_data: return jsonify({"status": "error", "message": "לא נמצא"}), 404

    try:
        fw = get_fw_connection()
        rulebase = Rulebase()
        fw.add(rulebase)
        svc_name = ensure_service_object(fw, str(rule_data['service_port']), rule_data.get('protocol', 'tcp'))
        
        final_rule_name = f"{rule_data['rule_name']}_{int(time.time() % 10000)}"
        
        new_rule = CustomSecurityRule(
            name=final_rule_name,
            fromzone=[rule_data['from_zone']], tozone=[rule_data['to_zone']],
            source=[rule_data['source_ip']], destination=[rule_data['destination_ip']],
            application=[rule_data['application']], service=[svc_name],
            tag=[rule_data.get('tag')] if rule_data.get('tag') != "None" else [],
            action='allow', group_tag=rule_data.get('group_tag')
        )
        rulebase.add(new_rule)
        new_rule.create()

        # עדכון DB: העברה להיסטוריה
        db.remove_pending_rule(rule_id)
        rule_data['status'] = 'Approved'
        rule_data['final_name'] = final_rule_name
        db.add_history_rule(rule_data)
        
        return jsonify({"status": "success", "message": f"החוקה {final_rule_name} נוצרה."})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@rules_bp.route('/reject-single-rule/<int:rule_id>', methods=['POST'])
def reject_single_rule(rule_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    rule_data = next((r for r in db.get_pending_rules() if r.get('id') == rule_id), None)
    if rule_data:
        db.remove_pending_rule(rule_id)
        rule_data['status'] = 'Rejected'
        db.add_history_rule(rule_data)
        return jsonify({"status": "success", "message": "החוקה נדחתה"})
    return jsonify({"status": "error"}), 404

@rules_bp.route('/update-pending-rule/<int:rule_id>', methods=['POST'])
def update_pending_rule(rule_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    data = request.json
    for rule in db.get_pending_rules():
        if rule['id'] == rule_id:
            rule.update(data) # מעדכן את האובייקט בזיכרון
            return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 404