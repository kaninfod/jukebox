# RFID Read Process - Logging Flow

This document shows the complete logging output flow for the RFID card read process.

## Expected Log Output (Success Path)

```
======================================================================
1. HARDWARE TRIGGER
   └─ PushButton detected card insertion
2. CHECK MODE
   └─ Encoding mode active: False
   └─ Read mode: card detection will initiate read
3. INSTANTIATE & START READING
   └─ Creating PN532Reader instance
   └─ Calling reader.start_reading() with callback
4. HARDWARE READ PROCESS
   ├─ Initializing I2C bus
   ├─ Creating PN532_I2C instance
   ├─ Running SAM configuration
   └─ PN532 hardware ready
   ├─ Polling for card (5 second timeout)
   │  └─ Card found on poll attempt 3
   ├─ Card detected with UID: 0x12345678
   ├─ Reading configured blocks:
   │  ├─ Reading block 4 (album_id)
   │  │  └─ Value: 42
   │  ├─ Reading block 5 (name)
   │  │  └─ Value: Test Album
   └─ All blocks read successfully
   └─ Calling result_callback()
5. CALLBACK TRIGGERED
   └─ _rfid_read_callback() called with status='success'
6. PROCESS RESULT (Success)
   ├─ UID extracted: 0x12345678
   ├─ Album ID extracted: 42
   └─ Emitting Event(type=EventType.RFID_READ)
   ✓ RFID_READ event emitted successfully
7. CLEANUP
   └─ Calling reader.cleanup()
   ├─ I2C connection closed
   └─ PN532 instance cleaned up
======================================================================
```

## Timeout Path (No Card Detected)

```
======================================================================
1. HARDWARE TRIGGER
   └─ PushButton detected card insertion
2. CHECK MODE
   └─ Encoding mode active: False
   └─ Read mode: card detection will initiate read
3. INSTANTIATE & START READING
   └─ Creating PN532Reader instance
   └─ Calling reader.start_reading() with callback
4. HARDWARE READ PROCESS
   ├─ Initializing I2C bus
   ├─ Creating PN532_I2C instance
   ├─ Running SAM configuration
   └─ PN532 hardware ready
   ├─ Polling for card (5 second timeout)
   └─ Poll timeout after 50 attempts (5s)
   ├─ Timeout: No card detected
   └─ Calling result_callback()
5. CALLBACK TRIGGERED
   └─ _rfid_read_callback() called with status='timeout'
6. PROCESS RESULT (Timeout)
   └─ Card read timeout (5 second threshold exceeded)
   ✓ Error screen queued
7. CLEANUP
   └─ Calling reader.cleanup()
   ├─ I2C connection closed
   └─ PN532 instance cleaned up
======================================================================
```

## Error Path

```
======================================================================
1. HARDWARE TRIGGER
   └─ PushButton detected card insertion
2. CHECK MODE
   └─ Encoding mode active: False
3. INSTANTIATE & START READING
   └─ Creating PN532Reader instance
   └─ Calling reader.start_reading() with callback
4. HARDWARE READ PROCESS
   ├─ Initializing I2C bus
   ❌ Hardware read error: [specific error message]
   └─ Calling result_callback()
5. CALLBACK TRIGGERED
   └─ _rfid_read_callback() called with status='error'
6. PROCESS RESULT (Error)
   └─ Read error: [error details]
   ✓ Error screen queued
7. CLEANUP
   └─ Calling reader.cleanup()
   ├─ I2C connection closed
   └─ PN532 instance cleaned up
======================================================================
```

## Key Logging Points for Debugging Intermittent Failures

1. **Step 4 - Hardware Read**: Look for I2C initialization failures
2. **Polling attempts**: Check if card polling succeeds but takes multiple attempts
3. **Block reading**: Verify all configured blocks are read successfully
4. **Callback execution**: Ensure result_callback is invoked with correct status
5. **Cleanup**: Confirm I2C is properly deinitialized (important for next read attempt)

## Log Levels Used

- `logger.info()` - Major process steps (1-7 phases)
- `logger.debug()` - Detailed hardware operations (indent shows depth)
- `logger.warning()` - Timeouts and non-fatal issues
- `logger.error()` - Exceptions and failures

## Troubleshooting Intermittent Failures

If cards fail to read intermittently:

1. Check Step 4 polling attempts - if very high, I2C bus may be unstable
2. Look for block read failures - individual blocks failing suggests corrupted card data
3. Verify cleanup happens after each read - I2C not deinitialized can cause next read to fail
4. Check for exception logs - review any errors in hardware initialization
