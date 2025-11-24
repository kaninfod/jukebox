# Rotary Encoder Testing Checklist

**Document Version:** 1.0  
**Updated:** November 23, 2025  
**For:** CircuitPython Implementation with Fresh Fixes

---

## Pre-Deployment Checks

### ✅ Code Review
- [x] Updated code removed 150ms debounce
- [x] Logging is comprehensive (DEBUG, INFO, ERROR levels)
- [x] Multi-step handling added (for rapid clicks)
- [x] Thread safety with locks implemented
- [x] Error handling with `exc_info=True` for debugging

### ✅ Physical Setup
Before testing, verify:
- [ ] Encoder is physically connected
- [ ] Pin A wire connected to GPIO **__?__**
- [ ] Pin B wire connected to GPIO **__?__**
- [ ] GND connected properly
- [ ] VCC powered (usually 5V or 3.3V - check spec)
- [ ] Wires are not loose

**Record your pin numbers:** `pin_a = ___, pin_b = ___`

---

## Testing Phases

### Phase 1: Initialization Test (2 minutes)

**Objective:** Verify the encoder initializes without errors

**Steps:**
1. Start the jukebox application
2. Check logs for initialization:
   ```bash
   tail -50 /path/to/app.log | grep "RotaryEncoder"
   ```

**Expected Output:**
```
2025-11-23 14:30:45 INFO: RotaryEncoder initialized on GPIO 17/27 (BCM -> board.D17/board.D27) using CircuitPython rotaryio with detent validation
2025-11-23 14:30:45 DEBUG: Config: bouncetime=5ms, min_interval=2.0ms
2025-11-23 14:30:45 DEBUG: Polling thread started
```

**Pass Criteria:**
- ✅ All three lines appear
- ✅ Pin numbers match your hardware
- ✅ No error messages

**If Failed:**
- Check GPIO pins are correct
- Verify CircuitPython libraries installed: `pip list | grep -i rotary`
- See "Troubleshooting" section

---

### Phase 2: Basic Rotation Test (5 minutes)

**Objective:** Verify encoder detects rotation in both directions

**Steps:**

1. **Slow Clockwise Rotation:**
   - Slowly rotate encoder CW one detent (should hear/feel a click)
   - Check logs for one entry:
     ```bash
     grep "Detent click confirmed" /path/to/app.log | tail -5
     ```

2. **Slow Counter-Clockwise Rotation:**
   - Slowly rotate encoder CCW one detent
   - Check logs again

**Expected Output (combined):**
```
INFO: Detent click confirmed: direction=+1, position=1
INFO: Detent click confirmed: direction=+1, position=2
INFO: Detent click confirmed: direction=-1, position=1
```

**Pass Criteria:**
- ✅ Detects CW rotation (direction=+1)
- ✅ Detects CCW rotation (direction=-1)
- ✅ One log line per physical click
- ✅ Position increments/decrements correctly

**If Failed:**
- Rotation not detected: Check physical connection, GPIO pin numbers
- Wrong direction: Might need to swap pins (see Phase 5)
- Multiple log entries per click: Check for noise/bouncing (Phase 4)

---

### Phase 3: Rapid Rotation Test (3 minutes)

**Objective:** Verify rapid rotations are handled correctly

**Steps:**

1. Count events before test:
   ```bash
   grep "Detent click confirmed" /path/to/app.log | wc -l
   ```
   Record this number: **__________**

2. Rapidly rotate encoder clockwise 10 times

3. Count events after test:
   ```bash
   grep "Detent click confirmed" /path/to/app.log | wc -l
   ```
   Record this number: **__________**

4. Calculate: After - Before = **__________** (should be ~10)

**Pass Criteria:**
- ✅ All 10 clicks detected (9-11 is acceptable)
- ✅ All show direction=+1 for CW
- ✅ No "Bounce suppression" messages (normal for rapid)

**Sample Output:**
```
DEBUG: Bounce suppression (step 1/3): Only 0.5ms since last callback
DEBUG: Bounce suppression (step 2/3): Only 0.3ms since last callback
INFO: Detent click confirmed: direction=+1, position=12
```

**If Getting < 7 clicks for 10 rotations:**
- Sensitivity too high - see "Adjustment: Sensitivity" section

**If Getting > 15 clicks for 10 rotations:**
- Too much bouncing - check physical connection, see "Adjustment: Debounce" section

---

### Phase 4: Direction Consistency Test (5 minutes)

**Objective:** Verify direction is consistent and not inverted

**Steps:**

1. Extract all CW rotations from logs:
   ```bash
   grep "Detent click confirmed.*direction=" /path/to/app.log | grep -c "direction=+1"
   ```
   Record count: **________** (CW clicks)

2. Extract all CCW rotations:
   ```bash
   grep "Detent click confirmed.*direction=" /path/to/app.log | grep -c "direction=-1"
   ```
   Record count: **________** (CCW clicks)

3. Visually inspect logs for consistency:
   ```bash
   grep "Detent click confirmed" /path/to/app.log | tail -20
   ```

**Pass Criteria:**
- ✅ CW rotations all show direction=+1
- ✅ CCW rotations all show direction=-1
- ✅ No direction=0 entries
- ✅ Directions never switch mid-rotation

**If Direction Inverted:**
- CW showing -1, CCW showing +1
- **Fix:** Swap encoder pins (one-line code change)
  ```python
  # In app/hardware/__init__.py or wherever RotaryEncoder instantiated:
  # Before: RotaryEncoder(pin_a=17, pin_b=27)
  # After:  RotaryEncoder(pin_a=27, pin_b=17)
  ```
- Redeploy and re-test

---

### Phase 5: UI Integration Test (10 minutes)

**Objective:** Verify encoder actually controls UI (volume, menu, etc.)

**Steps:**

1. **Volume Control (if applicable):**
   - Rotate CW - volume should increase
   - Rotate CCW - volume should decrease
   - Check that UI updates match rotations

2. **Menu Navigation (if applicable):**
   - Rotate CW - menu should advance
   - Rotate CCW - menu should go back
   - Verify highlighting moves with rotation

3. **Check for Lag:**
   - Rotate slowly - UI should follow immediately
   - UI should not feel sluggish or delayed

**Pass Criteria:**
- ✅ UI responds to every rotation
- ✅ CW/CCW directions match UI behavior
- ✅ No lag or delay between rotation and UI update
- ✅ No spurious UI changes (unwanted increments)

**If UI Not Responding:**
- Encoder logs show clicks, but UI doesn't
- Check: Is callback properly connected to UI handler?
- Debug: Add logs in UI handler code

**If UI Feels Sluggish:**
- Check CPU usage: is app overloaded?
- Check logs: are there many "Bounce suppression" messages?
- See "Adjustment: Polling Interval" section

---

## Sensitivity Adjustments

### Symptom: Too Many Clicks (Bouncing)
**Problem:** Rapidly clicking for single rotation, or clicking when stopped
**Cause:** Electrical noise or encoder contact bouncing

**Fix Option 1 - Increase Debounce (RECOMMENDED):**
```python
# File: app/hardware/devices/rotaryencoder.py
# Line ~28
self._min_callback_interval = 0.005  # Increase from 0.002 to 0.005 (5ms)
```

**Fix Option 2 - Change Divisor:**
```python
# File: app/hardware/devices/rotaryencoder.py
# Line ~50
self.encoder = rotaryio_IncrementalEncoder(board_pin_a, board_pin_b, divisor=2)
# Change from divisor=4 to divisor=2 (less sensitive)
```

---

### Symptom: Too Few Clicks (Missing Clicks)
**Problem:** Rapid rotations lose clicks, or need to hold longer between clicks
**Cause:** Debounce time too high (was the 150ms problem!)

**Fix - Decrease Debounce:**
```python
# File: app/hardware/devices/rotaryencoder.py
# Line ~28
self._min_callback_interval = 0.001  # Decrease from 0.002 to 0.001 (1ms)
```

**If Still Missing Clicks:**
```python
# Try disabling debounce entirely:
self._min_callback_interval = 0  # No time-based filtering
```

---

### Symptom: Sluggish Response
**Problem:** Noticeable lag between rotation and UI update
**Cause:** 10ms polling interval too large, or overloaded hardware

**Fix Option 1 - Reduce Polling Interval:**
```python
# File: app/hardware/devices/rotaryencoder.py
# Line ~117 (in _poll_position)
time.sleep(0.005)  # Change from 0.01 to 0.005 (poll more frequently)
```

**Fix Option 2 - Check System Load:**
```bash
# Is the app doing too much?
top -b -n 1 | head -20

# Check if other processes are consuming CPU
ps aux | head -20
```

---

## Troubleshooting

### Encoder Doesn't Detect Rotations

**Checklist:**
- [ ] Is encoder physically plugged in?
- [ ] Are GPIO pins correct? (Check schematic)
- [ ] Is CircuitPython library installed?
  ```bash
  pip list | grep -i rotary
  ```
- [ ] Is app logging to file? (Can you see other app logs?)
- [ ] Does initialization log appear? (If not, something failed)

**Debug Steps:**
1. Check initialization:
   ```bash
   tail -100 /path/to/app.log | grep -i "RotaryEncoder\|rotary"
   ```
2. If no logs: Check if application is running
3. If init error: Check CircuitPython is properly installed

---

### Direction is Backwards

**Symptom:** CW rotation shows direction=-1, CCW shows direction=+1

**Quick Fix:** Swap encoder pins (one line change)
```python
# Find in your code:
encoder = RotaryEncoder(pin_a=17, pin_b=27)

# Change to:
encoder = RotaryEncoder(pin_a=27, pin_b=17)

# Redeploy and test
```

**Alternative Fix:** Invert in callback handler (if you prefer)
```python
def on_encoder_turn(direction, position):
    direction = -direction  # Flip it
    # ... rest of code
```

---

### Getting Spurious Clicks (Noise)

**Symptom:** Random clicks when encoder is not being touched

**Likely Causes:**
1. Loose GPIO wires (EMI susceptible)
2. Long wire runs (noise pickup)
3. Encoder contact quality issue

**Fixes:**
1. **Check connections:** Reseat all wires firmly
2. **Shorten wires:** If possible, move encoder closer
3. **Add filtering:** Increase debounce (see "Sensitivity Adjustments")
4. **Check power:** Ensure encoder has stable 3.3V/5V supply

---

### Logs Not Appearing

**Symptom:** Encoder initialization log doesn't appear

**Checklist:**
- [ ] Is logging configured in app? 
  ```bash
  grep -r "logging.basicConfig\|getLogger" /path/to/app/ | head -5
  ```
- [ ] Is log file writable?
  ```bash
  touch /path/to/app.log && echo "Test" >> /path/to/app.log && rm /path/to/app.log
  ```
- [ ] Is app actually running?
  ```bash
  ps aux | grep -i jukebox
  ```
- [ ] Is CircuitPython import working?
  ```bash
  python3 -c "from ruhrohrotaryio import IncrementalEncoder; print('OK')"
  ```

---

## Log Capture for Analysis

### Basic Capture (Copy-Paste)
```bash
# Extract last 100 lines from app log
tail -100 /path/to/app.log | grep -E "RotaryEncoder|Detent click|Position change|Bounce"
```

### Detailed Capture (With Metadata)
```bash
# Capture with timestamps and context
echo "=== ROTARY ENCODER DEBUG LOG ===" > /tmp/re_debug.log
echo "Timestamp: $(date)" >> /tmp/re_debug.log
echo "GPIO Setup: Pin A=17, Pin B=27" >> /tmp/re_debug.log  # Update these
echo "=== Initialization ===" >> /tmp/re_debug.log
grep "RotaryEncoder" /path/to/app.log | head -5 >> /tmp/re_debug.log
echo "=== Last 50 Clicks ===" >> /tmp/re_debug.log
grep "Detent click confirmed" /path/to/app.log | tail -50 >> /tmp/re_debug.log
echo "=== Errors (if any) ===" >> /tmp/re_debug.log
grep "ERROR\|error\|Error" /path/to/app.log | grep -i "encoder\|rotary" >> /tmp/re_debug.log

# View result
cat /tmp/re_debug.log
```

---

## Sign-Off Checklist

After completing all tests, initial sign-off requires:

- [ ] **Phase 1 PASSED:** Encoder initializes without errors
- [ ] **Phase 2 PASSED:** CW and CCW rotations detected correctly
- [ ] **Phase 3 PASSED:** Rapid rotations counted accurately
- [ ] **Phase 4 PASSED:** Direction consistent throughout
- [ ] **Phase 5 PASSED:** UI responds appropriately to encoder
- [ ] **No Phase Issues:** All symptoms resolved without blockers

### If All Passed:
✅ **READY FOR PRODUCTION**

Document completion:
```
Date: _________________
Tester: _________________
Hardware: _________________
Notes: _________________
```

### If Issues Remain:
⚠️ **NEEDS INVESTIGATION**

Gather debug info:
1. Save detailed log capture (see section above)
2. Document the specific failure
3. Try one adjustment from "Sensitivity Adjustments"
4. Re-test and report results

---

## Quick Reference: Common Commands

```bash
# Show all encoder activity in real-time
tail -f /path/to/app.log | grep -E "RotaryEncoder|Detent|Position"

# Count total clicks
grep "Detent click confirmed" /path/to/app.log | wc -l

# Show only CW clicks
grep "direction=+1" /path/to/app.log | wc -l

# Show only CCW clicks
grep "direction=-1" /path/to/app.log | wc -l

# Show timeline of clicks
grep "Detent click confirmed" /path/to/app.log | cut -d' ' -f1-2

# Find any errors
grep -i "error" /path/to/app.log | grep -i "encoder\|rotary"

# Save detailed debug report
grep -E "RotaryEncoder|Detent|Position|ERROR" /path/to/app.log > /tmp/encoder_report.txt
```

---

## Success Indicators

✅ **What Good Logs Look Like:**
```
INFO: RotaryEncoder initialized on GPIO 17/27
DEBUG: Position change: 0 -> 1 (delta=1, direction=1, steps=1)
INFO: Detent click confirmed: direction=+1, position=1
DEBUG: Position change: 1 -> 0 (delta=-1, direction=-1, steps=1)
INFO: Detent click confirmed: direction=-1, position=0
```

❌ **What Bad Logs Look Like:**
```
ERROR: Failed to initialize rotary encoder
[No activity for 5 minutes]
DEBUG: Bounce suppression (step 1/5): [repeating]
INFO: Detent click confirmed: direction=+1
INFO: Detent click confirmed: direction=+1
INFO: Detent click confirmed: direction=-1  [should not change mid-run]
```

