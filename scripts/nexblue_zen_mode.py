import sys
import json
import requests
 
# Set your NexBlue credentials and Zen ID here
USERNAME = "email@email.com"
PASSWORD = "hashed_password" # Needs to be determined with web browser dev tools
 
# API Endpoints
TOKEN_URL = "https://api.nexblue.com/accounts/get_token"
COMMAND_URL = f"https://api.nexblue.com/accounts/place/PLACE_ID" # Needs to be determined with web browser dev tools
 
# Mode Mappings
MODE_MAP = {
    "dynamic": 1,      # Dynamic Load Balance (Full Grid Speed at night)
    "solaronly": 2,    # Solar Surplus Only (Zero grid import, pauses under 6A)
    "solarfirst": 3    # Solar Surplus First (Prioritizes solar, 6A grid fallback)
}
 
def get_id_token():
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }
    headers = {"Content-Type": "application/json"}
 
    response = requests.post(TOKEN_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
 
    # Extract token (Handles raw string token or JSON token dicts)
    if isinstance(data, dict):
        return data.get("IdToken") or data.get("access_token") or data.get("token")
    return str(data)
 
def set_zen_mode(token, lb_mode_int):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
 
    # POST payload to update the LB_mode on the Zen
    payload = {
        "work_mode": lb_mode_int
    }
 
    response = requests.put(COMMAND_URL, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()
 
def main():
    if len(sys.argv) < 2:
        print("Usage: python nexblue_zen_mode.py [dynamic|solaronly|solarfirst]")
        sys.exit(1)
 
    requested_mode = sys.argv[1].lower()
    if requested_mode not in MODE_MAP:
        print(f"Invalid mode '{requested_mode}'. Choose from: dynamic, solaronly, solarfirst")
        sys.exit(1)
 
    target_lb_mode = MODE_MAP[requested_mode]
 
    try:
        print("Fetching fresh authentication token...")
        token = get_id_token()
 
        print(f"Setting NexBlue Zen LB_mode to {target_lb_mode} ({requested_mode})...")
        result = set_zen_mode(token, target_lb_mode)
        print("Success! Response from Zen:", json.dumps(result))
 
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err.response.text}")
        sys.exit(1)
    except Exception as err:
        print(f"An error occurred: {err}")
        sys.exit(1)
 
if __name__ == "__main__":
    main()
