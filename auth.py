import os
from ldap3 import Server, Connection, ALL, SUBTREE
from dotenv import load_dotenv

load_dotenv()

def authenticate_ldap(username, password):
    server_ip = os.getenv('LDAP_SERVER')
    domain = os.getenv('LDAP_DOMAIN')
    base_dn = os.getenv('LDAP_BASE_DN')
    admin_group = os.getenv('LDAP_ADMIN_GROUP', '').lower()
    user_group = os.getenv('LDAP_USER_GROUP', '').lower()
    
    print(f"--- ניסיון התחברות עבור: {username} ---")
    
    try:
        server = Server(server_ip, get_info=ALL)
        user_principal_name = f"{username}@{domain}"
        
        # 1. אימות סיסמה (Bind)
        # הערה: אם זה עובד לך ככה, אין חובה ב-Service Account, אבל מומלץ בהמשך.
        conn = Connection(server, user=user_principal_name, password=password, auto_bind=True)
        print(f"V אימות סיסמה עבר בהצלחה")
            
        # 2. חיפוש המשתמש
        search_filter = f'(&(objectClass=person)(sAMAccountName={username}))'
        conn.search(search_base=base_dn, 
                    search_filter=search_filter, 
                    search_scope=SUBTREE, 
                    attributes=['memberOf', 'displayName'])
        
        if not conn.entries:
            print(f"X משתמש לא נמצא בחיפוש.")
            return False, False

        entry = conn.entries[0]
        
        # --- תיקון קריטי כאן: טיפול ברשימת הקבוצות ---
        raw_groups = []
        if 'memberOf' in entry:
            # אם יש רק קבוצה אחת, ldap3 לפעמים מחזיר מחרוזת במקום רשימה
            val = entry.memberOf.value
            if isinstance(val, str):
                raw_groups = [val]
            else:
                raw_groups = val
        
        print(f"נמצא משתמש: {entry.displayName}")
        print(f"קבוצות שנמצאו (לאחר תיקון):")
        
        user_groups_lower = []
        for g in raw_groups:
            g_lower = str(g).lower()
            user_groups_lower.append(g_lower)
            print(f" - {g_lower}")

        # 3. בדיקת הרשאות מול ה-ENV
        is_admin = admin_group in user_groups_lower
        is_low_user = user_group in user_groups_lower

        if is_admin:
            print(f"V כניסה מאושרת בתור ADMIN")
            return True, True
        elif is_low_user:
            print(f"V כניסה מאושרת בתור USER")
            return True, False
        else:
            print(f"X גישה נדחתה: המשתמש לא חבר ב-{admin_group} וגם לא ב-{user_group}")
            return False, False
            
    except Exception as e:
        print(f"X שגיאה: {e}")
        return False, False
    finally:
        if 'conn' in locals():
            conn.unbind()