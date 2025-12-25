import os
from dotenv import load_dotenv

# טעינת המשתנים מקובץ ה-env
load_dotenv()

IS_DOCKER = os.path.exists('/.dockerenv')

class Config:
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_123')
    
    # Firewall (מושך מ-PA_API_KEY שב-env)
    FW_IP = os.getenv('FW_IP')
    API_KEY = os.getenv('PA_API_KEY') 
    
    # Logging
    SYSLOG_PORT = int(os.getenv('SYSLOG_PORT', 514))
    
    # LDAP (עבור auth.py)
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_DOMAIN = os.getenv('LDAP_DOMAIN')
    LDAP_BASE_DN = os.getenv('LDAP_BASE_DN')
    LDAP_ADMIN_GROUP = os.getenv('LDAP_ADMIN_GROUP')
    LDAP_USER_GROUP = os.getenv('LDAP_USER_GROUP')
    
    # Database
    if IS_DOCKER:
        db_path = '/app/data/netops.db'
    else:
        basedir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(basedir, 'netops.db')
        
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False