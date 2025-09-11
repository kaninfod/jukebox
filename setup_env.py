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
        "DB_PASSWORD",
        "SUBSONIC_USER",
        "SUBSONIC_PASS"
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

def validate_subsonic_config():
    """Validate Subsonic configuration"""
    try:
        # Try to import dotenv, but don't fail if it's missing
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("⚠️  python-dotenv not available, reading .env manually")
            # Manual .env parsing as fallback
            if os.path.exists('.env'):
                with open('.env') as f:
                    for line in f:
                        if '=' in line and not line.startswith('#'):
                            key, value = line.strip().split('=', 1)
                            os.environ[key] = value
        
        subsonic_url = os.getenv("SUBSONIC_URL", "")
        subsonic_user = os.getenv("SUBSONIC_USER", "") 
        subsonic_pass = os.getenv("SUBSONIC_PASS", "")
        
        if not all([subsonic_url, subsonic_user, subsonic_pass]):
            print("❌ Missing Subsonic configuration in environment variables")
            print("   Required: SUBSONIC_URL, SUBSONIC_USER, SUBSONIC_PASS")
            return False
        
        print("✅ Subsonic configuration validated")
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate Subsonic config: {e}")
        return False

def install_dependencies():
    """Install required Python packages with proper handling for externally managed environments"""
    print("📦 Installing Python dependencies...")
    
    # Try different installation methods for externally managed environments
    install_commands = [
        "pip install -r requirements.txt --break-system-packages",
        "pip3 install -r requirements.txt --break-system-packages", 
        "python3 -m pip install -r requirements.txt --break-system-packages"
    ]
    
    success = False
    for cmd in install_commands:
        print(f"🔄 Trying: {cmd}")
        result = os.system(cmd)
        if result == 0:
            success = True
            break
    
    if success:
        print("✅ Dependencies installed successfully")
    else:
        print("⚠️  Package installation had issues, but continuing...")
        print("💡 You may need to run: sudo ./install_service.sh")
        print("   The service script handles system packages properly.")

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
    
    # Validate Subsonic configuration
    if not validate_subsonic_config():
        print("⚠️  Subsonic configuration may not work properly")
    
    print("\n🎉 Environment setup complete!")
    print("🚀 You can now start the jukebox service")

if __name__ == "__main__":
    main()
