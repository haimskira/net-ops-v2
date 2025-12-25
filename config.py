import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_123')
    FW_IP = os.getenv('FW_IP')
    API_KEY = os.getenv('PA_API_KEY')
    SYSLOG_PORT = 514
    SYSLOG_HOST = '0.0.0.0'