# utils/config.py
import os
import json
import hashlib

CONFIG_DIR = "config"
EMAIL_CONFIG_FILE = os.path.join(CONFIG_DIR, "email_config.json")
PASSKEY_CONFIG_FILE = os.path.join(CONFIG_DIR, "passkey_config.json")
DEFAULT_PASSKEY = "admin123"

def ensure_config_dir():
    """Ensure config directory exists"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config(file_path):
    """Load configuration from JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_config(file_path, config_data):
    """Save configuration to JSON file"""
    try:
        ensure_config_dir()
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception:
        return False

def hash_passkey(passkey):
    """Hash passkey for secure storage"""
    return hashlib.sha256(passkey.encode()).hexdigest()