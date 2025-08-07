#!/usr/bin/env python3
"""
Script to update oauth.json with values from environment variables.
This ensures OAuth credentials are loaded from .env file.
"""
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_oauth_json():
    """Update oauth.json with environment variables"""
    
    # Get values from environment
    access_token = os.getenv("YOUTUBE_ACCESS_TOKEN", "")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
    scope = os.getenv("YOUTUBE_SCOPE", "https://www.googleapis.com/auth/youtube")
    
    if not access_token or not refresh_token:
        print("❌ Missing YouTube OAuth tokens in environment variables")
        print("Please set YOUTUBE_ACCESS_TOKEN and YOUTUBE_REFRESH_TOKEN in .env file")
        return False
    
    # Create oauth.json content
    oauth_data = {
        "scope": scope,
        "token_type": "Bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": 1754257332,  # Keep existing expiry or update as needed
        "expires_in": 3599
    }
    
    # Write to oauth.json
    try:
        with open("oauth.json", "w") as f:
            json.dump(oauth_data, f, indent=2)
        print("✅ oauth.json updated successfully from environment variables")
        return True
    except Exception as e:
        print(f"❌ Failed to write oauth.json: {e}")
        return False

if __name__ == "__main__":
    update_oauth_json()
