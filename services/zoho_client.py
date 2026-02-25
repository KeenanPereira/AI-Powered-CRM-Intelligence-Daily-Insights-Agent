import requests
from core.config import Config

def get_access_token():
    """Generates a short-lived Access Token using the permanent Refresh Token."""
    print("Fetching new Access Token from Zoho...")
    url = f"{Config.ZOHO_ACCOUNTS_URL}/oauth/v2/token"
    # Note: For grabbing an access token from a refresh token, we pass the refresh token
    # parameter and grant_type="refresh_token"
    data = {
        "grant_type": "refresh_token",
        "client_id": Config.ZOHO_CLIENT_ID,
        "client_secret": Config.ZOHO_CLIENT_SECRET,
        "refresh_token": Config.ZOHO_REFRESH_TOKEN
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    
    if "access_token" in result:
        print("✅ Access Token acquired successfully!")
        return result["access_token"]
    else:
        print("❌ Failed to get Access Token:")
        print(result)
        return None

def fetch_incremental_module(access_token, module_name="Leads", last_sync_iso=None):
    """
    Fetches all records created or modified after the last_sync_iso date for ANY module.
    Pulls completely unfiltered JSON payloads for infinite JSONB scalability.
    """
    print(f"\nFetching incremental {module_name} from Zoho CRM (Since: {last_sync_iso or 'Beginning of Time'})...")
    url = f"{Config.ZOHO_API_URL}/crm/v2/{module_name}"
    
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }
    
    if last_sync_iso:
        headers["If-Modified-Since"] = last_sync_iso
    
    # Intentionally removed the 'fields' parameter constraint to fetch the complete data object
    params = {}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        records = data.get("data", [])
        print(f"✅ Successfully fetched {len(records)} updated/new {module_name}!")
        return records
    elif response.status_code == 204 or response.status_code == 304:
        print(f"✅ No new {module_name} modified since last sync.")
        return []
    else:
        print(f"❌ Failed to fetch {module_name} (Status {response.status_code}):")
        print(response.text)
        return []

