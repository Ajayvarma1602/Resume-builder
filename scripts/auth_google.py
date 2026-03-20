#!/usr/bin/env python3
"""
One-time Google OAuth2 setup.
Run this ONCE to authenticate with your Gmail account.
It will open a browser, you log in, and a refresh token is saved to .env.

Usage:
    python scripts/auth_google.py
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv, set_key

BASE_DIR = Path(__file__).parent.parent
ENV_PATH = BASE_DIR / ".env"
CLIENT_SECRET_PATH = BASE_DIR / "google-client-secret.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def main():
    load_dotenv(ENV_PATH) if ENV_PATH.exists() else None

    if not CLIENT_SECRET_PATH.exists():
        print("\n❌  google-client-secret.json not found.")
        print("\nTo get it:")
        print("  1. Go to: https://console.cloud.google.com/apis/credentials")
        print("  2. Click 'Create Credentials' → 'OAuth client ID'")
        print("  3. Application type: Desktop app")
        print("  4. Click Create → Download JSON")
        print(f"  5. Save it as: {CLIENT_SECRET_PATH}")
        print()
        return

    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import google.oauth2.credentials

    print("\n🌐  Opening browser for Google login...")
    print("    Log in with: sskus109@gmail.com\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)

    # Save tokens to .env
    if not ENV_PATH.exists():
        ENV_PATH.write_text("")

    set_key(str(ENV_PATH), "GOOGLE_REFRESH_TOKEN", creds.refresh_token)
    set_key(str(ENV_PATH), "GOOGLE_CLIENT_ID", creds.client_id)
    set_key(str(ENV_PATH), "GOOGLE_CLIENT_SECRET", creds.client_secret)

    print("\n✅  Google authentication successful!")
    print("    Refresh token saved to .env")
    print("\nYou're ready. Now run:")
    print("    python scripts/tailor_resume.py --company 'CompanyName' --role 'Role Title'\n")

if __name__ == "__main__":
    main()
