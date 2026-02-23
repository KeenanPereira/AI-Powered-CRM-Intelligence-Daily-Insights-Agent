import json

s = """{
  "dashboard_report": "The Daily Pulse\n📈 New Leads: 15",
  "whatsapp_report": "\n🚀 Daily CRM Pulse\n📈 New Leads: 15"
}"""

try:
    data = json.loads(s, strict=False)
    print("SUCCESS")
    print(data)
except Exception as e:
    print(f"FAILED: {e}")
