import os
from dotenv import load_dotenv

# Automatically load the .env file globally when this module is imported
load_dotenv()

class Config:
    # Zoho SDK Variables
    ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID")
    ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET")
    ZOHO_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN")
    ZOHO_ACCOUNTS_URL = os.environ.get("ZOHO_ACCOUNTS_URL", "https://accounts.zoho.in")
    ZOHO_API_URL = os.environ.get("ZOHO_API_URL", "https://www.zohoapis.in")

    # Supabase SDK Variables
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

    # Twilio SDK Variables
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")
    TARGET_WHATSAPP_NUMBER = os.environ.get("TARGET_WHATSAPP_NUMBER")

    @classmethod
    def validate(cls):
        """Ensure all critical environment variables are loaded to prevent runtime crashes."""
        missing = []
        for key in ["ZOHO_CLIENT_ID", "ZOHO_CLIENT_SECRET", "ZOHO_REFRESH_TOKEN", "SUPABASE_URL", "SUPABASE_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_NUMBER", "TARGET_WHATSAPP_NUMBER"]:
            if not getattr(cls, key):
                missing.append(key)
        
        if missing:
            raise ValueError(f"Missing critical Environment Variables in .env: {', '.join(missing)}")

# Validate upfront on boot
Config.validate()
