#!/usr/bin/env python3
"""
Standalone card authentication tester with statistics collection.
Polls for cards in a loop and tests if they can authenticate with the auth key.
Supports retry with card flip for cards with auth issues.
Collects and outputs detailed statistics at the end.
"""

import time
import logging
import board
import busio
from adafruit_pn532.i2c import PN532_I2C

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIFARE_CMD_AUTH_A = 0x60
DEFAULT_KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'  # Factory default key
BLOCK_TO_TEST = 0  # Test authentication on block 0 (manufacturer block)
POLL_TIMEOUT = 5  # Seconds to wait for card


class CardTestResult:
    """Track results for a single card test."""
    def __init__(self):
        self.uid = None
        self.status = None  # "OK", "FAULTY", or "NOT_DETECTED"
        self.attempts = 0
        self.retry_reason = None  # "AUTH_ERROR", "NOT_DETECTED", None


def init_pn532():
    """Initialize I2C and PN532."""
    logger.info("Initializing I2C bus...")
    i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
    time.sleep(0.1)
    
    logger.info("Creating PN532 instance...")
    pn532 = PN532_I2C(i2c, debug=False)
    time.sleep(0.2)
    
    logger.info("Running SAM configuration...")
    pn532.SAM_configuration()
    time.sleep(0.1)
    
    logger.info("PN532 ready!\n")
    return i2c, pn532



def test_card_auth(pn532, attempt_num=1):
    """
    Poll for a card and test authentication.
    Returns: (uid_number, auth_success) or (None, False) if not detected
    """
    logger.info(f"Polling for card ({POLL_TIMEOUT}s timeout)...")
    
    start_time = time.time()
    while (time.time() - start_time) < POLL_TIMEOUT:
        uid = pn532.read_passive_target(timeout=0.5)
        
        if uid is not None:
            # Convert UID to hex number
            uid_number = 0
            for b in uid:
                uid_number = (uid_number << 8) | b
            
            logger.info(f"✓ Card detected! UID: {hex(uid_number)}")
            
            # Test authentication on block 0
            logger.info(f"Testing authentication on block {BLOCK_TO_TEST}...")
            try:
                auth = pn532.mifare_classic_authenticate_block(uid, BLOCK_TO_TEST, MIFARE_CMD_AUTH_A, DEFAULT_KEY)
                
                if auth:
                    logger.info("✓ Authentication SUCCESSFUL with factory default key!")
                    logger.info(f"  Card UID {hex(uid_number)} is compatible with this system.\n")
                    return uid_number, True
                else:
                    logger.warning("✗ Authentication FAILED")
                    logger.warning(f"  Card UID {hex(uid_number)} - auth error detected.\n")
                    return uid_number, False
                    
            except Exception as e:
                logger.error(f"✗ Authentication error: {e}\n")
                return None, False
    
    logger.warning("✗ Timeout: No card detected in field\n")
    return None, None



def main():
    """Main loop for testing cards."""
    logger.info("=" * 70)
    logger.info("CARD AUTHENTICATION TESTER (with flip retry)")
    logger.info("=" * 70)
    logger.info("This script tests if cards can be authenticated with the factory default key.")
    logger.info("If a card has auth errors, you'll be asked to flip it 180 degrees and retry.")
    logger.info("Insert one card at a time to test.\n")
    
    i2c = None
    pn532 = None
    card_results = []
    
    try:
        i2c, pn532 = init_pn532()
        
        while True:
            logger.info("-" * 70)
            input("Insert card, then press ENTER (or Ctrl+C to exit)...")
            logger.info("")
            
            # Wait for magnetic field to stabilize (200-300ms)
            logger.info("   ├─ Waiting 250ms for magnetic field to stabilize...")
            time.sleep(0.25)
            logger.info("   └─ Ready!\n")
            
            result = CardTestResult()
            
            # First attempt
            uid_number, auth_success = test_card_auth(pn532, attempt_num=1)
            result.attempts = 1
            
            if auth_success is True:
                # Success on first try
                result.uid = uid_number
                result.status = "OK"
                logger.info(f"✓ Card {hex(uid_number)} status: OK\n")
                
            elif auth_success is False:
                # Auth failed - ask to flip and retry
                result.uid = uid_number
                result.retry_reason = "AUTH_ERROR"
                logger.warning("Card detected but authentication failed.")
                logger.warning("This might be a card orientation issue.\n")
                
                input("Flip the card 180 degrees and press ENTER to retry (or Ctrl+C to skip)...")
                logger.info("")
                
                uid_number_retry, auth_success_retry = test_card_auth(pn532, attempt_num=2)
                result.attempts = 2
                
                if auth_success_retry is True:
                    # Success after flip!
                    result.status = "OK"
                    logger.info(f"✓ Card {hex(result.uid)} status: OK (after flip)\n")
                else:
                    # Still failed after flip
                    result.status = "FAULTY"
                    logger.error(f"✗ Card {hex(result.uid)} status: FAULTY (auth failed even after flip)\n")
                    
            else:
                # Not detected on first try - ask to reposition and retry
                result.retry_reason = "NOT_DETECTED"
                logger.warning("Card not detected in field.\n")
                
                input("Reposition the card and press ENTER to retry (or Ctrl+C to skip)...")
                logger.info("")
                
                uid_number_retry, auth_success_retry = test_card_auth(pn532, attempt_num=2)
                result.attempts = 2
                
                if auth_success_retry is True:
                    # Success after reposition
                    result.uid = uid_number_retry
                    result.status = "OK"
                    logger.info(f"✓ Card {hex(result.uid)} status: OK (after reposition)\n")
                elif auth_success_retry is False:
                    # Detected but auth failed
                    result.uid = uid_number_retry
                    result.status = "FAULTY"
                    logger.error(f"✗ Card {hex(result.uid)} status: FAULTY (auth failed)\n")
                else:
                    # Still not detected
                    result.status = "NOT_DETECTED"
                    logger.error("✗ Card status: NOT_DETECTED (failed to detect even after retry)\n")
            
            card_results.append(result)
            
            # Show running summary
            ok_count = sum(1 for r in card_results if r.status == "OK")
            faulty_count = sum(1 for r in card_results if r.status == "FAULTY")
            not_detected_count = sum(1 for r in card_results if r.status == "NOT_DETECTED")
            total = len(card_results)
            logger.info(f"RUNNING SUMMARY: {total} cards | {ok_count} OK | {faulty_count} FAULTY | {not_detected_count} NOT_DETECTED")
            logger.info("")
    
    except KeyboardInterrupt:
        logger.info("\n\nExiting...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        # Cleanup
        if pn532:
            try:
                pn532 = None
                logger.info("PN532 cleaned up")
            except:
                pass
        
        if i2c:
            try:
                i2c.deinit()
                logger.info("I2C bus deinitialized")
            except:
                pass
        
        # Print final statistics
        print("\n" + "=" * 70)
        print("FINAL TEST RESULTS")
        print("=" * 70)
        
        if card_results:
            ok_cards = [r for r in card_results if r.status == "OK"]
            faulty_cards = [r for r in card_results if r.status == "FAULTY"]
            not_detected_cards = [r for r in card_results if r.status == "NOT_DETECTED"]
            
            print(f"\nTotal cards tested: {len(card_results)}")
            print(f"  ✓ OK: {len(ok_cards)}")
            print(f"  ✗ FAULTY: {len(faulty_cards)}")
            print(f"  ? NOT_DETECTED: {len(not_detected_cards)}")
            
            if ok_cards:
                print(f"\nCompatible cards (OK):")
                for r in ok_cards:
                    print(f"  ✓ UID: {hex(r.uid)}")
            
            if faulty_cards:
                print(f"\nIncompatible cards (FAULTY):")
                for r in faulty_cards:
                    print(f"  ✗ UID: {hex(r.uid)}")
            
            if not_detected_cards:
                print(f"\nNot detected cards:")
                for r in not_detected_cards:
                    print(f"  ? UID: Not read")
        else:
            print("\nNo cards tested.")
        
        print("\n" + "=" * 70)
        print("Done!")



if __name__ == "__main__":
    main()
