# Configuration System Strategy & Implementation Plan

## Configuration Philosophy

### **Recommended Approach: Hybrid Strategy**
- **Sensitive values** (passwords, tokens, IPs) → `.env` file
- **Non-sensitive values** (timeouts, paths, defaults) → `config.py` with sensible defaults
- **All config files** → `app/config/` directory (except `.env` in root)

### **Benefits**:
- ✅ Security: Sensitive data stays in `.env` (gitignored)
- ✅ Convenience: Non-sensitive values have good defaults
- ✅ Flexibility: Easy to override any value via environment
- ✅ Organization: All config files centralized

## Current State Analysis

### **Legacy Items to Remove** 🗑️
```bash
# From .env - No longer used:
HA_BASE_URL=*
HA_WS_URL=*
HA_TOKEN=*
YOUTUBE_ACCESS_TOKEN=*
YOUTUBE_REFRESH_TOKEN=*
YOUTUBE_SCOPE=*
```

### **Subsonic Configuration Issues** 🔧
```python
# INCONSISTENCY FOUND:
config.py:        SUBSONIC_URL = "http://192.168.68.102:4747"  # Default
.env:            # No SUBSONIC_URL specified
subsonic_service: base_url = "http://192.168.68.102:4533"      # Hardcoded fallback!
```

## Proposed Configuration Structure

### **Directory Structure**:
```
/Volumes/Shared/jukebox/
├── .env                           # Sensitive values only
├── app/
│   └── config/
│       ├── config.py              # Main configuration
│       ├── menu_config.json       # UI menus
│       ├── logging_config.py      # Logging setup
│       └── fonts/                 # Font directory
│           ├── opensans/
│           ├── symbolfont/
│           └── Oswald-SemiBold.ttf
```

### **Recommended .env Contents** (Sensitive Only):
```bash
# Database Credentials
DB_PASSWORD=4AllData

# Network Addresses (may be sensitive in production)
DB_HOST=192.168.68.102
SUBSONIC_URL=http://192.168.68.102:4747
LOG_SERVER_HOST=192.168.68.102

# Optional: Override default device for different environments
# DEFAULT_CHROMECAST_DEVICE=Living Room
```

### **Config.py Contents** (Defaults + Environment Loading):
```python
class Config:
    # === NETWORK CONFIGURATION ===
    # Subsonic/Navidrome Settings
    SUBSONIC_URL: str = os.getenv("SUBSONIC_URL", "http://localhost:4747")
    SUBSONIC_USER: str = os.getenv("SUBSONIC_USER", "jukebox") 
    SUBSONIC_PASS: str = os.getenv("SUBSONIC_PASS", "defaultpass")
    SUBSONIC_CLIENT: str = os.getenv("SUBSONIC_CLIENT", "jukebox")
    SUBSONIC_API_VERSION: str = os.getenv("SUBSONIC_API_VERSION", "1.15.0")
    
    # Database Settings
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USERNAME: str = os.getenv("DB_USERNAME", "jukebox")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")  # Required from .env
    DB_NAME: str = os.getenv("DB_NAME", "jukeboxdb")
    
    # === TIMEOUT CONFIGURATION ===
    # Chromecast Operation Timeouts
    CHROMECAST_CONNECT_TIMEOUT: int = int(os.getenv("CHROMECAST_CONNECT_TIMEOUT", "10"))
    CHROMECAST_DISCOVERY_TIMEOUT: int = int(os.getenv("CHROMECAST_DISCOVERY_TIMEOUT", "3"))
    CHROMECAST_WAIT_TIMEOUT: int = int(os.getenv("CHROMECAST_WAIT_TIMEOUT", "10"))
    
    # Network Request Timeouts
    HTTP_REQUEST_TIMEOUT: int = int(os.getenv("HTTP_REQUEST_TIMEOUT", "10"))
    SYSTEM_OPERATION_TIMEOUT: int = int(os.getenv("SYSTEM_OPERATION_TIMEOUT", "5"))
    
    # RFID Hardware Timeouts
    RFID_POLL_INTERVAL: float = float(os.getenv("RFID_POLL_INTERVAL", "1.0"))
    RFID_READ_TIMEOUT: float = float(os.getenv("RFID_READ_TIMEOUT", "5.0"))
    RFID_THREAD_JOIN_TIMEOUT: int = int(os.getenv("RFID_THREAD_JOIN_TIMEOUT", "1"))
    
    # === DEVICE CONFIGURATION ===
    # Default Chromecast Device
    DEFAULT_CHROMECAST_DEVICE: str = os.getenv("DEFAULT_CHROMECAST_DEVICE", "Living Room")
    
    # Display Configuration
    DISPLAY_WIDTH: int = int(os.getenv("DISPLAY_WIDTH", "480"))
    DISPLAY_HEIGHT: int = int(os.getenv("DISPLAY_HEIGHT", "320"))
    DISPLAY_ROTATION: int = int(os.getenv("DISPLAY_ROTATION", "0"))
    
    # === GPIO PIN CONFIGURATION ===
    # (Keep existing GPIO configuration as-is)
    
    # === LOGGING CONFIGURATION ===
    LOG_SERVER_HOST: str = os.getenv("LOG_SERVER_HOST", "localhost")
    LOG_SERVER_PORT: int = int(os.getenv("LOG_SERVER_PORT", "514"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # === PATH CONFIGURATION ===
    # Font Configuration
    FONT_BASE_PATH: str = os.getenv("FONT_BASE_PATH", "app/config/fonts")
    STATIC_FILE_PATH: str = os.getenv("STATIC_FILE_PATH", "static_files")
    
    # Dynamic font definitions using base path
    @classmethod
    def get_font_definitions(cls):
        return [
            {"name": "title", "path": f"{cls.FONT_BASE_PATH}/opensans/OpenSans-Regular.ttf", "size": 20},
            {"name": "info", "path": f"{cls.FONT_BASE_PATH}/opensans/OpenSans-Regular.ttf", "size": 18},
            {"name": "small", "path": f"{cls.FONT_BASE_PATH}/opensans/OpenSans-Regular.ttf", "size": 12},
            {"name": "symbols", "path": f"{cls.FONT_BASE_PATH}/symbolfont/symbolfont.ttf", "size": 24},
            {"name": "oswald_semi_bold", "path": f"{cls.FONT_BASE_PATH}/Oswald-SemiBold.ttf", "size": 24}
        ]
```

## Implementation Steps

### **Step 1: Clean .env File**
Remove legacy variables:
```bash
# Remove these lines from .env:
HA_BASE_URL=*
HA_WS_URL=*  
HA_TOKEN=*
YOUTUBE_ACCESS_TOKEN=*
YOUTUBE_REFRESH_TOKEN=*
YOUTUBE_SCOPE=*
```

Add missing required variables:
```bash
# Add to .env:
SUBSONIC_URL=http://192.168.68.102:4747
LOG_SERVER_HOST=192.168.68.102
```

### **Step 2: Update config.py**
- Add timeout configuration section with descriptions
- Add logging server configuration
- Fix font path system
- Add default device configuration

### **Step 3: Create config directory structure**
```bash
mkdir -p app/config/fonts
mv fonts/* app/config/fonts/
```

### **Step 4: Update service files**
- Fix subsonic_service.py to use config values consistently
- Update logging_config.py to use config values
- Replace hardcoded timeouts with config values
- Replace hardcoded "Living Room" with config.DEFAULT_CHROMECAST_DEVICE

### **Step 5: Update .env.example**
Create clean example with only necessary variables.

## Configuration Usage Guidelines

### **When to use .env vs config.py defaults:**

**Use .env for:**
- Passwords and tokens ✅
- IP addresses and URLs ✅  
- Environment-specific overrides ✅
- Deployment-specific values ✅

**Use config.py defaults for:**
- Timeout values ✅
- Path configurations ✅
- Hardware settings ✅
- Application behavior settings ✅

### **Configuration Access Pattern:**
```python
# Good - All services use config object:
from app.config import config

class SomeService:
    def __init__(self):
        self.timeout = config.HTTP_REQUEST_TIMEOUT
        self.device = config.DEFAULT_CHROMECAST_DEVICE

# Bad - Hardcoded values:
def connect():
    timeout = 10  # Should be config.CHROMECAST_CONNECT_TIMEOUT
    device = "Living Room"  # Should be config.DEFAULT_CHROMECAST_DEVICE
```

## Benefits of This Approach

1. **Security**: Sensitive data stays in .env (gitignored)
2. **Simplicity**: Most config has sensible defaults
3. **Flexibility**: Any value can be overridden via environment
4. **Documentation**: Timeout descriptions explain usage
5. **Consistency**: All services use same config pattern
6. **Organization**: Config files centralized in app/config/
7. **Maintainability**: Single source of truth for all settings

## Validation Strategy

After implementation:
- [ ] All services use config object (no hardcoded values)
- [ ] All timeouts are configurable  
- [ ] All network addresses come from config
- [ ] Font system uses relative paths
- [ ] Default device is configurable
- [ ] Logging server is configurable
- [ ] .env contains only sensitive values
- [ ] .env.example is complete and accurate



Next - I need to test the "portability" / installability of the app.
I will install the app on a clean RPI4 runnung rasbian 64bit.

For that I need to review whether we have all dependencies in check. The requirements.txt is central, but if there are other things then let's handle that too.

I also need an installation guide that should work by simply following it - for that, do a review of all the installation scripts