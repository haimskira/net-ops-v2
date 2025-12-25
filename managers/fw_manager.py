# managers/fw_manager.py
import xml.etree.ElementTree as ET
from panos.firewall import Firewall
from panos.objects import ServiceObject
from panos.policies import SecurityRule
from config import Config
from managers.data_manager import db
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CustomSecurityRule(SecurityRule):
    def __init__(self, *args, **kwargs):
        self._group_tag = kwargs.pop('group_tag', None)
        super(CustomSecurityRule, self).__init__(*args, **kwargs)

    def element_str(self):
        root = super(CustomSecurityRule, self).element_str()
        if isinstance(root, (bytes, str)):
            root = ET.fromstring(root)
        if self._group_tag:
            gt_element = ET.Element('group-tag')
            gt_element.text = self._group_tag
            root.append(gt_element)
        return ET.tostring(root)

def get_fw_connection():
    if not Config.FW_IP or not Config.API_KEY:
        raise ValueError("Missing FW_IP or PA_API_KEY")
    return Firewall(Config.FW_IP, api_key=Config.API_KEY, verify=False, timeout=60)

def ensure_service_object(fw, port, proto):
    proto = proto.lower()
    if not str(port).isdigit(): return port
    obj_name = f"service-{proto}-{port}"
    try:
        svc = ServiceObject(name=obj_name, protocol=proto, destination_port=str(port))
        fw.add(svc)
        svc.create()
    except: pass
    return obj_name

def load_app_ids():
    try:
        fw = get_fw_connection()
        result = fw.xapi.get("/config/predefined/application")
        root = ET.fromstring(result) if isinstance(result, (str, bytes)) else result
        new_map = {}
        for entry in root.findall('.//entry'):
            name = entry.get('name')
            aid = entry.findtext('id') or entry.get('id')
            if name and aid: new_map[str(aid).strip()] = name
        db.app_id_map = new_map # שמירה ב-Data Manager
        print("V App-IDs loaded successfully")
    except Exception as e: print(f"X App-ID Load Error: {e}")