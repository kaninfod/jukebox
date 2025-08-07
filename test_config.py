#!/usr/bin/env python3
"""
Quick configuration test script
"""
try:
    from app.config import config
    print("🔧 Configuration Test:")
    print(f"✅ HA URL: {config.HA_BASE_URL}")
    print(f"✅ HA WebSocket: {config.HA_WS_URL}")
    print(f"✅ DB Host: {config.DB_HOST}:{config.DB_PORT}")
    print(f"✅ DB Name: {config.DB_NAME}")
    print(f"✅ Media Player: {config.MEDIA_PLAYER_ENTITY_ID}")
    print(f"✅ Display Power GPIO: {config.DISPLAY_POWER_GPIO}")
    print(f"✅ RFID CS Pin: {config.RFID_CS_PIN}")
    print("✅ All configuration loaded successfully!")
    
    # Test database URL generation
    db_url = config.get_database_url()
    print(f"✅ Database URL: mysql+pymysql://***:***@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    
    # Validate required config
    if config.validate_config():
        print("✅ Configuration validation passed!")
    else:
        print("❌ Configuration validation failed!")
        
except Exception as e:
    print(f"❌ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
