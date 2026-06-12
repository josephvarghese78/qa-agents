import httpx
import json
import time
import sys
import os
from datetime import datetime

COPILOT_CLIENT_ID = ""
CLIENT_SECRET=""

GITHUB_DEVICE_CODE_URL    = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL   = "https://github.com/login/oauth/access_token"
COPILOT_TOKEN_URL         = "https://api.github.com/copilot_internal/v2/token"
COPILOT_MODELS_URL        = "https://api.githubcopilot.com/models"

# Headers that mimic the VS Code Copilot extension (required by Copilot API)
COPILOT_HEADERS = {
    "Editor-Version":        "vscode/1.95.0",
    "Editor-Plugin-Version": "copilot-chat/0.22.4",
    "User-Agent":            "GithubCopilot/1.155.0",
    "Accept":                "application/json",
}
SSL_VERIFY=False


def get_token():

    if os.path.exists(".oath_token"):
        with open(".oath_token", "r") as f:
            token = f.read().strip()
            if token:
                print(" ✅ Token loaded from file.")
                return token
    else:
        resp=httpx.post(url=GITHUB_DEVICE_CODE_URL
                        ,data={"client_id": COPILOT_CLIENT_ID, "scope": "read:user"},
                        headers={"Accept": "application/json"},
                        verify=SSL_VERIFY)

        device_code=resp.json()["device_code"]
        verification_uri=resp.json()["verification_uri"]
        interval=resp.json().get("interval", 5)
        user_code=resp.json()["user_code"]

        print(device_code, verification_uri, user_code)

        while True:
            time.sleep(interval)
            resp = httpx.post(
                GITHUB_ACCESS_TOKEN_URL,
                data={
                    "client_id": COPILOT_CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
                verify=SSL_VERIFY,
                timeout=15,
            )
            resp.raise_for_status()
            body = resp.json()
            error = body.get("error", "")

            if "access_token" in body:
                print(" ✅ Authorised!")
                with open(".oath_token", "w") as f:
                    f.write(body["access_token"])
                return body["access_token"]
            elif error == "authorization_pending":
                print(".", end="", flush=True)
            elif error == "slow_down":
                interval += 5
                print("s", end="", flush=True)
            elif error == "expired_token":
                raise RuntimeError("Device code expired. Please run the script again.")
            elif error == "access_denied":
                raise RuntimeError("Access denied by user.")
            else:
                raise RuntimeError(f"Unexpected error: {body}")



