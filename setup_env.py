#!/usr/bin/env python3
"""
Environment setup helper for the jukebox project.
This script helps validate and manage environment configuration.
"""
import os
import sys
import json
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found!")
        print("📋 Please copy .env.example to .env and fill in your values:")
        print("   cp .env.example .env")
        return False
    
    print("✅ .env file found")
    
    # Check for required variables
    required_vars = [
        "HA_TOKEN",
        "HA_BASE_URL", 
        "DB_PASSWORD",
        "YOUTUBE_ACCESS_TOKEN",
        "YOUTUBE_REFRESH_TOKEN"
    ]
    
    missing_vars = []
    with open(env_file) as f:
        env_content = f.read()
        for var in required_vars:
            if f"{var}=" not in env_content or f"{var}=your_" in env_content or f"{var}=http://your-" in env_content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or placeholder values for: {', '.join(missing_vars)}")
        print("📝 Please update your .env file with actual values")
        return False
    
    print("✅ All required environment variables are configured")
    return True

def update_oauth_json():
    """Update oauth.json from environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        access_token = os.getenv("YOUTUBE_ACCESS_TOKEN", "")
        refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
        scope = os.getenv("YOUTUBE_SCOPE", "https://www.googleapis.com/auth/youtube")
        
        if not access_token or not refresh_token:
            print("❌ Missing YouTube OAuth tokens in environment variables")
            return False
        
        oauth_data = {
            "scope": scope,
            "token_type": "Bearer",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": 1754257332,
            "expires_in": 3599
        }
        
        with open("oauth.json", "w") as f:
            json.dump(oauth_data, f, indent=2)
        
        print("✅ oauth.json updated from environment variables")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update oauth.json: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing Python dependencies...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependencies installed")

def main():
    """Main setup function"""
    print("🎵 Jukebox Environment Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    install_dependencies()
    
    # Check environment file
    if not check_env_file():
        print("\n📋 Setup Steps:")
        print("1. Copy .env.example to .env: cp .env.example .env")
        print("2. Edit .env file with your actual values")
        print("3. Run this setup script again")
        sys.exit(1)
    
    # Update oauth.json
    if not update_oauth_json():
        print("⚠️  OAuth configuration may not work properly")
    
    print("\n🎉 Environment setup complete!")
    print("🚀 You can now start the jukebox service")

if __name__ == "__main__":
    main()
