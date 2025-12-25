from flask import Blueprint, jsonify, request
import requests
import xml.etree.ElementTree as ET
import time
from config import Config
from managers.data_manager import db
from managers.fw_manager import get_fw_connection
from panos.network import Zone
from panos.objects import ServiceObject, AddressObject, AddressGroup, Tag

# הגדרת ה-Blueprint
ops_bp = Blueprint('ops', __name__)

@ops_bp.route('/get-live-logs')
def get_live_logs():
    """מחזיר את הלוגים שנשמרו בזיכרון (Syslog)"""
    return jsonify(db.traffic_logs)

@ops_bp.route('/commit', methods=['POST'])
def commit_changes():
    """ביצוע Commit לפיירוול"""
    try:
        fw = get_fw_connection()
        job_id = fw.commit(sync=False)
        return jsonify({"status": "success", "message": f"ה-Commit נשלח! (ג'וב מספר {job_id})."})
    except Exception as e:
        # טיפול במצב שבו כבר רץ Commit
        if "705" in str(e) or "704" in str(e):
            return jsonify({"status": "success", "message": "ה-Commit כבר מתבצע ברקע בפיירוול."})
        return jsonify({"status": "error", "message": str(e)}), 500

@ops_bp.route('/job-status/<int:job_id>')
def get_job_status(job_id):
    """בדיקת סטטוס של Commit"""
    try:
        url = f"https://{Config.FW_IP}/api/?type=op&cmd=<show><jobs><id>{job_id}</id></jobs></show>&key={Config.API_KEY}"
        r = requests.get(url, verify=False, timeout=5)
        root = ET.fromstring(r.text)
        job = root.find(".//job")
        if job is not None:
            return jsonify({
                "status": job.findtext("status"),
                "progress": job.findtext("progress"),
                "result": job.findtext("result")
            })
        return jsonify({"status": "not_found"})
    except:
        return jsonify({"status": "error"})

@ops_bp.route('/get-params', methods=['GET'])
def get_params():
    """שליפת פרמטרים (Zones, Services, IPs) עם מנגנון Cache"""
    current_time = time.time()
    
    # בדיקה אם יש מידע ב-Cache והוא מעודכן (פחות מ-300 שניות)
    if db.firewall_cache["data"] and (current_time - db.firewall_cache["last_updated"] < 300):
        return jsonify(db.firewall_cache["data"])
        
    try:
        fw = get_fw_connection()
        
        # שליפת Zones
        zone_list = sorted([z.name for z in Zone.refreshall(fw) if z.name])
        if 'any' not in zone_list: zone_list.insert(0, 'any')
        
        # שליפת Services
        svc_list = sorted([s.name for s in ServiceObject.refreshall(fw) if s.name])
        if 'application-default' not in svc_list: svc_list.insert(0, 'application-default')
        
        # שליפת Addresses + Groups
        full_addr_list = sorted([a.name for a in AddressObject.refreshall(fw) if a.name] + 
                                [g.name for g in AddressGroup.refreshall(fw) if g.name])
        if 'any' not in full_addr_list: full_addr_list.insert(0, 'any')
        
        # שליפת Tags
        try: all_tags = sorted([t.name for t in Tag.refreshall(fw) if t.name])
        except: all_tags = []
        
        # שליפת Applications (דרך API ישיר כי ה-SDK לפעמים כבד)
        try:
            result = fw.xapi.get("/config/predefined/application")
            root = ET.fromstring(result) if isinstance(result, (str, bytes)) else result
            app_list = sorted([entry.get('name') for entry in root.findall('.//entry') if entry.get('name')])
        except: app_list = ["any", "web-browsing", "ssl"]

        response_data = {
            "status": "success", 
            "zones": zone_list, 
            "services": svc_list, 
            "addresses": full_addr_list, 
            "applications": app_list, 
            "tags": all_tags
        }
        
        # עדכון ה-Cache ב-DataManager
        db.firewall_cache["data"] = response_data
        db.firewall_cache["last_updated"] = current_time
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@ops_bp.route('/run-policy-match', methods=['POST'])
def run_policy_match():
    """בדיקת חוקה (Policy Match) מול הפיירוול"""
    data = request.json
    try:
        # חילוץ נתונים מהבקשה
        source = data.get("source_ip", "").strip()
        destination = data.get("destination_ip", "").strip()
        protocol = data.get("protocol", "6").strip() # ברירת מחדל TCP
        port = data.get("port", "443").strip()
        from_zone = data.get("from_zone", "").strip()
        to_zone = data.get("to_zone", "").strip()

        # בניית חלקי ה-XML לפי הצורך
        from_tag = f"<from>{from_zone}</from>" if from_zone and from_zone.lower() != "any" else ""
        to_tag = f"<to>{to_zone}</to>" if to_zone and to_zone.lower() != "any" else ""

        # בניית הפקודה המלאה
        cmd = (f"<test><security-policy-match>"
               f"{from_tag}{to_tag}"
               f"<source>{source}</source><destination>{destination}</destination>"
               f"<protocol>{protocol}</protocol><destination-port>{port}</destination-port>"
               f"</security-policy-match></test>")
        
        # שליחת הבקשה לפיירוול (שימוש ב-Config.FW_IP ו-Config.API_KEY)
        url = f"https://{Config.FW_IP}/api/?type=op&cmd={cmd}&key={Config.API_KEY}&target-vsys=vsys1"
        
        # ביצוע הבקשה
        r = requests.get(url, verify=False, timeout=10)
        
        # פענוח התשובה
        xml_root = ET.fromstring(r.text)
        
        if xml_root.get('status') == 'error':
            error_msg = xml_root.findtext(".//msg/line") or "Firewall rejected the query"
            return jsonify({"status": "error", "message": error_msg}), 400

        entry = xml_root.find(".//entry")
        if entry is not None:
            return jsonify({
                "status": "success", 
                "match": True, 
                "rule_name": entry.get("name"),
                "action": entry.findtext("action") or "allow",
                "from": entry.findtext("from") or from_zone or "any",
                "to": entry.findtext("to") or to_zone or "any",
                "source": entry.findtext("source") or source,
                "destination": entry.findtext("destination") or destination
            })
            
        return jsonify({"status": "success", "match": False})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500