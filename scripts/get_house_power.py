import json
import os
import requests

# --- CONFIGURATION ---
USERNAME = "email@email.com"
PASSWORD_HASH = "HASHED_PASSWORD"
ZEN_ID = "MY_ZEN_ID"

LOGIN_URL = "https://api.nexblue.com/accounts/get_token"
STATUS_URL = (
    f"https://api.nexblue.com/chargers/command/{ZEN_ID}/detector_status"
)
TOKEN_FILE = "/config/scripts/nexblue_token.json"


def get_id_token():
    """Retrieve cached IdToken or request a new one from NexBlue."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                if "IdToken" in data:
                    return data["IdToken"]
        except Exception:
            pass

    payload = {"username": USERNAME, "password": PASSWORD_HASH}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            LOGIN_URL, json=payload, headers=headers, timeout=10
        )
        if response.status_code == 200:
            res_data = response.json()
            id_token = res_data.get("IdToken")
            if id_token:
                os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
                with open(TOKEN_FILE, "w") as f:
                    json.dump({"IdToken": id_token}, f)
                return id_token
    except Exception:
        pass

    return None


def fetch_power():
    fallback = {"power": 0.0}
    token = get_id_token()

    if not token:
        return fallback

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        res = requests.get(STATUS_URL, headers=headers, timeout=10)

        # Handle expired token: clear cache and retry once
        if res.status_code == 401:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            token = get_id_token()
            if not token:
                return fallback
            headers["Authorization"] = f"Bearer {token}"
            res = requests.get(STATUS_URL, headers=headers, timeout=10)

        if res.status_code == 200:
            data = res.json()
            # Extract 'power_usage' (kW) and convert to Watts (W), keeping the raw sign
            power_kw = data.get("power_usage", 0.0)
            power_w = round(float(power_kw) * 1000, 2)
            return {"power": power_w}

    except Exception:
        pass

    return fallback


if __name__ == "__main__":
    result = fetch_power()
    print(json.dumps(result))
