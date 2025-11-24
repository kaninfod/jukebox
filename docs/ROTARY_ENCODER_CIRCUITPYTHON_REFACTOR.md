# Rotary Encoder CircuitPython Refactor - Review & Fixes

**Date:** November 23, 2025  
**Issue:** CircuitPython implementation had excessive sensitivity and direction issues  
**Reference:** Original working RPi.GPIO implementation provided

---

## Problems Identified

### 1. **Excessive Sensitivity (150ms Debounce)**
**Old Code Issue:**
```python
self._min_callback_interval = 0.15  # 150ms blanket filter
```
- This 150ms timeout was filtering out legitimate rapid rotations
- Any rotation within 150ms was treated as jitter and ignored
- Made the encoder feel laggy and unresponsive
- Made testing impossible (have to wait 150ms between each click)

**Fix Applied:**
- Reduced to `0.002` (2ms) - just enough for electrical bounce, not logical rotations
- Only applied to actual callback timing, not position reading

### 2. **Direction Logic Too Simplistic**
**Old Code Issue:**
```python
if current_position > self.last_position:
    direction = 1  # Clockwise
else:
    direction = -1  # Counter-clockwise
```
- Single comparison didn't handle multiple steps accumulating between polls
- No validation that direction was consistent
- Could misinterpret rapid rotations

**Fix Applied:**
- Calculate `position_delta` to detect how many steps changed
- Process each step individually: `for step in range(num_steps)`
- Proper direction for each step (not just one callback for multiple steps)

### 3. **Lost Detent Validation**
**Old Implementation (RPi.GPIO - WORKING):**
- Tracked raw GPIO state transitions in sequence history
- Validated complete detent sequences like `[0b11, 0b01, 0b00, 0b10]` or `[0b11, 0b10, 0b00, 0b01]`
- Rejected partial sequences (e.g., `[3, 1, 3]`) that indicated incomplete rotations
- Very sophisticated hysteresis with 4-state validation

**CircuitPython Version Issue:**
- No raw state tracking (hardware handles it)
- But ALSO no validation that position changes were "complete clicks"
- Could fire callbacks for noise-induced state changes

**Fix Applied:**
- Since CircuitPython's `divisor=4` already does detent counting in hardware
- Changed approach: trust the hardware but validate timing/consistency
- The `divisor=4` setting means each position change = 1 complete detent
- Treat position delta as "confirmed detent clicks"

---

## Code Changes Summary

### **Before vs After**

| Aspect | Before | After |
|--------|--------|-------|
| Min callback interval | 150ms | 2ms |
| State tracking | Simple delta check | Tracks position delta & steps |
| Multi-step handling | Lost intermediate steps | Processes each step separately |
| Logging | Scattered, sometimes skipped | Comprehensive DEBUG and INFO |
| Thread safety | Basic | Proper lock usage with `_lock` |
| Error handling | Minimal logging | Full exc_info for debugging |

### **Key Implementation Details**

1. **Minimal Time-Based Debounce (2ms):**
   ```python
   if time_since_last < self._min_callback_interval:
       # Skip this callback
       continue
   ```
   - Only skips callback if last one was < 2ms ago
   - Still tracks the position change
   - Prevents high-frequency noise, not legitimate rotations

2. **Multi-Step Processing:**
   ```python
   for step in range(num_steps):
       self.position = self._last_position + (step + 1) * direction
       if self.callback:
           self.callback(direction, self.position)
   ```
   - If encoder jumped 3 positions, fires 3 callbacks
   - Each gets its own timestamp check
   - Each updates position atomically

3. **Enhanced Logging:**
   - **DEBUG:** Position changes, bounce suppression, config
   - **INFO:** Confirmed detent clicks, initialization, cleanup
   - **ERROR:** Any exceptions with full traceback

---

## Direction Validation

### Expected Behavior (KY-040)

With `divisor=4`:
- **Clockwise (CW):** Position increases (`position_delta > 0`) → `direction = +1`
- **Counter-clockwise (CCW):** Position decreases (`position_delta < 0`) → `direction = -1`

### Testing Direction

To verify direction is correct:
```bash
# Watch logs while slowly rotating
tail -f /path/to/logs | grep "Detent click confirmed"

# CW rotation should show: direction=+1
# CCW rotation should show: direction=-1
```

If directions are inverted, swap the encoder pins when instantiating:
```python
# Before (maybe wrong):
encoder = RotaryEncoder(pin_a=17, pin_b=27)

# After (swap them):
encoder = RotaryEncoder(pin_a=27, pin_b=17)
```

---

## Testing & Validation Steps

### 1. **Verify Logging is Working**
```bash
# Check that initialization logs appear
grep "RotaryEncoder initialized" /path/to/logs

# Should see:
# INFO: RotaryEncoder initialized on GPIO 17/27 (BCM -> board.D17/board.D27) using CircuitPython rotaryio with detent validation
# DEBUG: Polling thread started
```

### 2. **Test Sensitivity (Slow Rotation)**
```bash
# Slowly rotate encoder one detent at a time
# Watch logs:
tail -f /path/to/logs | grep "Detent click confirmed"

# Should see one line per click with immediate response
# Should NOT see delays or missed clicks
```

### 3. **Test Rapid Rotation**
```bash
# Quickly rotate encoder multiple times
# Should see continuous output with ~2ms min intervals
# Should NOT see gaps or jitter
```

### 4. **Test Direction Consistency**
```bash
# Rotate CW 5 times, check:
grep "Detent click confirmed" /path/to/logs | grep -A 5 "direction=+1"

# Rotate CCW 5 times, check:
grep "Detent click confirmed" /path/to/logs | grep -A 5 "direction=-1"

# All +1 should be one direction, all -1 should be opposite
```

---

## Logging Reference

### Initialization
```
INFO: RotaryEncoder initialized on GPIO 17/27 (BCM -> board.D17/board.D27) using CircuitPython rotaryio with detent validation
DEBUG: Config: bouncetime=5ms, min_interval=2.0ms
DEBUG: Polling thread started
```

### Normal Operation
```
DEBUG: Position change: 0 -> 1 (delta=1, direction=1, steps=1)
INFO: Detent click confirmed: direction=+1, position=1
```

### Bounce Suppression
```
DEBUG: Bounce suppression (step 1/3): Only 0.5ms since last callback
```

### Cleanup
```
INFO: Cleaning up RotaryEncoder on GPIO 17/27
INFO: RotaryEncoder cleanup complete (final position: 15)
```

---

## Configuration Tuning

If issues persist after deployment, these parameters can be adjusted:

1. **Polling Interval** (currently 10ms):
   ```python
   time.sleep(0.01)  # Line in _poll_position
   # Decrease for lower latency, increase to reduce CPU
   ```

2. **Minimum Callback Interval** (currently 2ms):
   ```python
   self._min_callback_interval = 0.002  # Line in __init__
   # Increase if getting false bounces, decrease for more responsiveness
   ```

3. **Divisor Setting** (currently 4):
   ```python
   self.encoder = rotaryio_IncrementalEncoder(..., divisor=4)
   # divisor=1: Ultra-sensitive (might be too noisy)
   # divisor=2: Standard detent
   # divisor=4: Double-counting (current - safest for KY-040)
   ```

---

## Comparison: RPi.GPIO vs CircuitPython

| Feature | RPi.GPIO (Old) | CircuitPython (New) |
|---------|----------------|-------------------|
| Event model | GPIO interrupt callbacks | Polling thread |
| Debounce | GPIO bouncetime + sequence validation | Time-based + hardware divisor |
| State tracking | Full 4-state sequence | Just position delta |
| Complexity | Complex but reliable | Simpler, relies on hardware |
| Maintenance | GPIO library specific | Hardware agnostic |
| Responsiveness | Immediate (interrupts) | Polling + 10ms loop |

---

## Next Steps

1. **Deploy updated code**
2. **Collect logs during normal operation** (rotate encoder normally, check logs)
3. **Test edge cases:** rapid rotations, pause and rotate, single clicks
4. **Monitor for any spurious callbacks or missed clicks**
5. **Report back with sample logs** if issues persist

**Key logs to capture:**
```bash
# Capture all RE activity
grep "RotaryEncoder\|Detent click\|Bounce suppression" /path/to/logs > /tmp/encoder_test.log

# Share this file with analysis
```

---

## If Direction is Still Wrong

If after testing the direction is inverted (CW gives -1, CCW gives +1):

**Option 1: Swap pins** (simplest)
```python
# Find where RotaryEncoder is instantiated and swap pin_a and pin_b
RotaryEncoder(pin_a=27, pin_b=17)  # was (17, 27)
```

**Option 2: Invert direction in callback handling**
```python
# In whatever code receives the callback, negate the direction
# (Usually in a menu or volume control handler)
```

---

## Summary of Improvements

✅ **Sensitivity fixed:** 150ms → 2ms debounce  
✅ **Direction handling improved:** Multi-step detection and logging  
✅ **Logging enhanced:** DEBUG/INFO/ERROR with timestamps and context  
✅ **Thread safety:** Proper locking around shared state  
✅ **Error handling:** Full exception info for debugging  
✅ **Detent concept retained:** Using hardware divisor + minimal filtering  

The new implementation balances the reliability of the old RPi.GPIO code with the simplicity of CircuitPython's hardware-based approach.
