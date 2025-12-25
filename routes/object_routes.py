from flask import Blueprint, request, jsonify, session
from datetime import datetime
import time
from managers.data_manager import db
from managers.fw_manager import get_fw_connection
from panos.objects import AddressObject, AddressGroup, ServiceObject, ServiceGroup
import ipaddress

objects_bp = Blueprint('objects', __name__)

@objects_bp.route('/create-object', methods=['POST'])
def create_object():
    data = request.json
    obj_type = data.get('type')
    value = data.get('value')
    name = data.get('name')

    # --- ולידציה בצד השרת ---
    try:
        if not name or not value:
            return jsonify({"status": "error", "message": "חסרים נתונים (שם או ערך)"}), 400

        # בדיקת IP
        if obj_type == 'address':
            try:
                ipaddress.ip_address(value) # זורק שגיאה אם ה-IP לא תקין (למשל 999.999.999.999)
            except ValueError:
                return jsonify({"status": "error", "message": f"כתובת ה-IP '{value}' אינה תקינה"}), 400

        # בדיקת פורט
        elif obj_type == 'service':
            if not str(value).isdigit():
                return jsonify({"status": "error", "message": "פורט חייב להיות מספר"}), 400
            port_num = int(value)
            if not (1 <= port_num <= 65535):
                return jsonify({"status": "error", "message": f"פורט {port_num} אינו בטווח החוקי (1-65535)"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"שגיאת ולידציה: {str(e)}"}), 400
    # -----------------------

    # אם הכל תקין, ממשיכים כרגיל
    data.update({
        'id': int(time.time() * 1000),
        'requested_by': session.get('user', 'Unknown'),
        'request_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'Pending'
    })
    db.add_pending_object(data)
    return jsonify({"status": "success", "message": "בקשת אובייקט נשלחה לאישור אדמין!"})


@objects_bp.route('/get-pending-objects')
def get_pending_objects():
    if not session.get('is_admin'): return jsonify([])
    return jsonify(db.get_pending_objects())

@objects_bp.route('/get-admin-view-objects')
def get_admin_view_objects():
    if not session.get('is_admin'): return jsonify([])
    pending = [{**o, 'status': 'Pending'} for o in db.get_pending_objects()]
    history = db.get_history_objects()
    return jsonify(pending + history)

@objects_bp.route('/get-my-objects')
def get_my_objects():
    user = session.get('user')
    pending = [dict(o, status='Pending') for o in db.get_pending_objects() if o.get('requested_by') == user]
    history = [o for o in db.get_history_objects() if o.get('requested_by') == user]
    return jsonify(pending + history)

@objects_bp.route('/approve-object/<int:obj_id>', methods=['POST'])
def approve_object(obj_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    
    obj = next((o for o in db.get_pending_objects() if o['id'] == obj_id), None)
    if not obj: return jsonify({"status": "error", "message": "לא נמצא"}), 404

    try:
        fw = get_fw_connection()
        t, n, v = obj['type'], obj['name'], obj['value']
        
        if t == 'address': new = AddressObject(name=n, value=f"{v}/{obj.get('prefix','32')}")
        elif t == 'address-group': new = AddressGroup(name=n, static_value=v.split(','))
        elif t == 'service': new = ServiceObject(name=n, protocol=obj.get('protocol','tcp'), destination_port=v)
        elif t == 'service-group': new = ServiceGroup(name=n, value=v.split(','))
        
        fw.add(new)
        new.create()
        
        db.remove_pending_object(obj_id)
        obj['status'] = 'Approved'
        db.add_history_object(obj)
        return jsonify({"status": "success", "message": "אובייקט נוצר"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)})

@objects_bp.route('/reject-object/<int:obj_id>', methods=['POST'])
def reject_object(obj_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    obj = next((o for o in db.get_pending_objects() if o['id'] == obj_id), None)
    if obj:
        db.remove_pending_object(obj_id)
        obj['status'] = 'Rejected'
        db.add_history_object(obj)
    return jsonify({"status": "success", "message": "נדחה"})

@objects_bp.route('/get-address-objects')
def get_address_objects():
    try:
        fw = get_fw_connection()
        return jsonify({"status": "success", "addresses": sorted([a.name for a in AddressObject.refreshall(fw) if a.name])})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@objects_bp.route('/get-service-objects')
def get_service_objects():
    try:
        fw = get_fw_connection()
        return jsonify({"status": "success", "services": sorted([s.name for s in ServiceObject.refreshall(fw) if s.name])})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500