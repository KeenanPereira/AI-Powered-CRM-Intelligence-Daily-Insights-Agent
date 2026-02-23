import logging
from twilio.rest import Client
from core.config import Config

# Initialize Twilio Client
twilio_client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

def send_whatsapp_message(body: str, to_number: str = None) -> bool:
    """
    Sends a WhatsApp message via the Twilio Sandbox.
    
    Args:
        body: The markdown text to send (e.g., the AI Briefing).
        to_number: The recipient's number. Defaults to TARGET_WHATSAPP_NUMBER in .env.
        
    Returns:
        True if the message was queued successfully, False otherwise.
    """
    if not to_number:
        to_number = Config.TARGET_WHATSAPP_NUMBER
        
    if not to_number:
        logging.error("No target WhatsApp number provided.")
        return False
        
    # Twilio requires WhatsApp numbers to be prefixed with 'whatsapp:'
    from_whatsapp = f"whatsapp:{Config.TWILIO_WHATSAPP_NUMBER}"
    to_whatsapp = f"whatsapp:{to_number}"
    
    try:
        logging.info(f"Attempting to dispatch WhatsApp message to {to_whatsapp}...")
        message = twilio_client.messages.create(
            body=body,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        logging.info(f"✅ WhatsApp message successfully queued! Message SID: {message.sid}")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to send WhatsApp message: {e}")
        return False
