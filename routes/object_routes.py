from flask import Blueprint, request, jsonify, session
from datetime import datetime
import time
import ipaddress
from managers.data_manager import db
from managers.fw_manager import get_fw_connection
from managers.models import ObjectRequest, db_sql
from panos.objects import AddressObject, AddressGroup, ServiceObject, ServiceGroup

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

        # בדיקת IP (רק אם זה אובייקט מסוג כתובת בודדת)
        if obj_type == 'address':
            try:
                ipaddress.ip_address(value)
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

    # שמירה ב-Database
    try:
        data['requested_by'] = session.get('user', 'Unknown')
        db.add_pending_object(data)
        return jsonify({"status": "success", "message": "בקשת אובייקט נשלחה לאישור אדמין!"})
    except Exception as e:
        return jsonify({"status": "error", "message": f"שגיאה בשמירה ל-DB: {str(e)}"}), 500


@objects_bp.route('/get-admin-view-objects')
def get_admin_view_objects():
    if not session.get('is_admin'): return jsonify([])
    objs = db.get_admin_objects()
    return jsonify([{c.name: getattr(o, c.name) for c in o.__table__.columns} for o in objs])


@objects_bp.route('/get-my-objects')
def get_my_objects():
    user = session.get('user')
    objs = db.get_user_objects(user)
    return jsonify([{c.name: getattr(o, c.name) for c in o.__table__.columns} for o in objs])


@objects_bp.route('/approve-object/<int:obj_id>', methods=['POST'])
def approve_object(obj_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    
    # שליפת האובייקט מה-DB
    obj_req = ObjectRequest.query.get(obj_id)
    if not obj_req or obj_req.status != 'Pending':
        return jsonify({"status": "error", "message": "אובייקט לא נמצא או כבר טופל"}), 404

    try:
        fw = get_fw_connection()
        t, n, v = obj_req.obj_type, obj_req.name, obj_req.value
        new_fw_obj = None
        
        if t == 'address':
            # אם אין פריפיקס, נשים 32 כברירת מחדל
            val_with_mask = f"{v}/{obj_req.prefix}" if obj_req.prefix else f"{v}/32"
            new_fw_obj = AddressObject(name=n, value=val_with_mask)
            
        elif t == 'address-group':
            # המרה של מחרוזת פסיקים לרשימה עבור הפנאוס
            members = [m.strip() for m in v.split(',')]
            new_fw_obj = AddressGroup(name=n, static_value=members)
            
        elif t == 'service':
            new_fw_obj = ServiceObject(name=n, protocol=obj_req.protocol or 'tcp', destination_port=str(v))
            
        elif t == 'service-group':
            members = [m.strip() for m in v.split(',')]
            new_fw_obj = ServiceGroup(name=n, static_value=members)
        
        if new_fw_obj:
            fw.add(new_fw_obj)
            new_fw_obj.create()
            
            # עדכון סטטוס ב-DB ל-Approved
            db.update_object_status(obj_id, 'Approved', notes="Object created successfully in Firewall")
            return jsonify({"status": "success", "message": f"האובייקט {n} נוצר בהצלחה."})
        
        return jsonify({"status": "error", "message": "סוג אובייקט לא מוכר"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"שגיאת תקשורת מול הפיירוול: {str(e)}"}), 500


@objects_bp.route('/reject-object/<int:obj_id>', methods=['POST'])
def reject_object(obj_id):
    if not session.get('is_admin'): return jsonify({"status": "error"}), 403
    
    # קבלת סיבת הדחייה מה-JSON
    data = request.json or {}
    reason = data.get('reason', 'נדחה על ידי אדמין')
    
    success = db.update_object_status(obj_id, 'Rejected', notes=reason)
    if success:
        return jsonify({"status": "success", "message": "האובייקט נדחה וסיבת הדחייה נשמרה"})
    
    return jsonify({"status": "error", "message": "אובייקט לא נמצא"}), 404


@objects_bp.route('/get-address-objects')
def get_address_objects():
    """שליפת אובייקטים קיימים מהפיירוול לצורך בחירה לקבוצה"""
    try:
        fw = get_fw_connection()
        return jsonify({
            "status": "success", 
            "addresses": sorted([a.name for a in AddressObject.refreshall(fw) if a.name])
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@objects_bp.route('/get-service-objects')
def get_service_objects():
    """שליפת אובייקטי שירות קיימים מהפיירוול לצורך בחירה לקבוצה"""
    try:
        fw = get_fw_connection()
        return jsonify({
            "status": "success", 
            "services": sorted([s.name for s in ServiceObject.refreshall(fw) if s.name])
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500