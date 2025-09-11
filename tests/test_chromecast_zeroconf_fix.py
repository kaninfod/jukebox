#!/usr/bin/env python3
"""
Test script to verify Chromecast zeroconf fix.

This script tests that the zeroconf lifecycle is properly managed
to prevent the "Zeroconf instance loop must be running" error.
"""

import sys
import os
import time
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_zeroconf_lifecycle():
    """Test that zeroconf instances are properly managed."""
    try:
        from app.services.pychromecast_service_ondemand import PyChromecastServiceOnDemand
        
        logger.info("=== Testing Zeroconf Lifecycle Management ===")
        
        # Test 1: Service creation and cleanup
        logger.info("Test 1: Service creation and cleanup")
        service = PyChromecastServiceOnDemand("Living Room")
        logger.info("✅ Service created successfully")
        
        # Test 2: Discovery without connection
        logger.info("Test 2: Discovery without connection")
        devices = service.list_chromecasts()
        logger.info(f"✅ Discovery completed, found {len(devices)} devices")
        for device in devices:
            logger.info(f"  - {device['name']} ({device['model']})")
        
        # Test 3: Connection attempt
        logger.info("Test 3: Connection attempt")
        if service.connect("Living Room"):
            logger.info("✅ Connection successful")
            
            # Test 4: Status check
            if service.is_connected():
                logger.info("✅ Status check successful")
            else:
                logger.warning("⚠️  Status check failed")
            
            # Test 5: Disconnect
            logger.info("Test 5: Disconnect")
            service.disconnect()
            logger.info("✅ Disconnection successful")
        else:
            logger.warning("⚠️  Connection failed (device may not be available)")
        
        # Test 6: Device switch (simulated)
        logger.info("Test 6: Device switch simulation")
        if len(devices) > 1:
            target_device = devices[1]['name']
            logger.info(f"Attempting to switch to: {target_device}")
            if service.switch_device(target_device):
                logger.info("✅ Device switch successful")
                service.disconnect()
            else:
                logger.warning("⚠️  Device switch failed")
        else:
            logger.info("ℹ️  Skipping device switch (only one device found)")
        
        # Test 7: Full cleanup
        logger.info("Test 7: Full cleanup")
        service.cleanup()
        logger.info("✅ Full cleanup successful")
        
        logger.info("=== All Tests Completed Successfully ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_manager():
    """Test context manager usage."""
    try:
        from app.services.pychromecast_service_ondemand import PyChromecastServiceOnDemand
        
        logger.info("=== Testing Context Manager ===")
        
        with PyChromecastServiceOnDemand("Living Room") as service:
            logger.info("✅ Context manager entered")
            
            devices = service.list_chromecasts()
            logger.info(f"✅ Discovery in context: found {len(devices)} devices")
            
            # Try connection
            if devices:
                device_name = devices[0]['name']
                if service.connect(device_name):
                    logger.info("✅ Connection in context successful")
                else:
                    logger.warning("⚠️  Connection failed")
        
        logger.info("✅ Context manager exited cleanly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Context manager test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting Chromecast Zeroconf Fix Tests")
    
    success = True
    
    # Run basic lifecycle test
    if not test_zeroconf_lifecycle():
        success = False
    
    # Wait a bit between tests
    time.sleep(2)
    
    # Run context manager test
    if not test_context_manager():
        success = False
    
    if success:
        logger.info("🎉 All tests passed! Zeroconf fix appears to be working.")
    else:
        logger.error("❌ Some tests failed. Check the logs for details.")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
