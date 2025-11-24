# Rotary Encoder Debugging Guide

## Quick Diagnostics

### 1. Verify It's Initialized
```bash
grep "RotaryEncoder initialized" /path/to/app.log
```
**Expected:** Should show initialization with pin mapping and "detent validation" message

**If missing:** Encoder failed to initialize - check GPIO pin numbers and CircuitPython import

---

### 2. Check for Immediate Activity
```bash
# Start app, rotate encoder once CW, watch logs
tail -f /path/to/app.log | grep -E "Detent click|Position change"
```

**Expected after one CW click:**
```
DEBUG: Position change: 0 -> 1 (delta=1, direction=1, steps=1)
INFO: Detent click confirmed: direction=+1, position=1
```

**If nothing appears:** 
- Encoder not detecting rotations
- Check physical connection (loose pins, wrong GPIO numbers)
- Try slower rotation (give it time to detect)

**If bounce suppression appears repeatedly:**
```
DEBUG: Bounce suppression (step 1/1): Only 0.1ms since last callback
```
- Rapid rotations detected within 2ms of each other
- Normal behavior - not a problem

---

### 3. Direction Test

**Rotate clockwise 3 times:**
```bash
grep "direction=" /path/to/app.log | tail -5
```

**Expected: All should show `direction=+1`**
```
INFO: Detent click confirmed: direction=+1, position=1
INFO: Detent click confirmed: direction=+1, position=2
INFO: Detent click confirmed: direction=+1, position=3
```

**If showing `direction=-1` instead:**
- Direction is inverted
- See "Fix Direction" section below

---

### 4. Sensitivity Test

**Quickly rotate encoder 10 times rapidly:**
```bash
grep "Detent click confirmed" /path/to/app.log | wc -l
```

**Expected: ~10 lines** (one per click, some may be suppressed if bounce timing is very tight)

**If < 5 lines:**
- Missing clicks - sensitivity too high or callbacks suppressed
- See "Troubleshooting" section

**If > 15 lines for 10 clicks:**
- Double-counting - might have `divisor` set too low
- Or false triggers from noise

---

## Sample Log Analysis

### Example 1: Normal, Good Behavior
```
2025-11-23 14:32:15 DEBUG: Position change: 0 -> 1 (delta=1, direction=1, steps=1)
2025-11-23 14:32:15 INFO: Detent click confirmed: direction=+1, position=1
2025-11-23 14:32:17 DEBUG: Position change: 1 -> 2 (delta=1, direction=1, steps=1)
2025-11-23 14:32:17 INFO: Detent click confirmed: direction=+1, position=2
2025-11-23 14:32:19 DEBUG: Position change: 2 -> 1 (delta=-1, direction=-1, steps=1)
2025-11-23 14:32:19 INFO: Detent click confirmed: direction=-1, position=1
```
**Status:** ✅ **HEALTHY** - Detects each click, proper direction, good timing

---

### Example 2: Inverted Direction
```
2025-11-23 14:35:10 DEBUG: Position change: 0 -> 1 (delta=1, direction=1, steps=1)
2025-11-23 14:35:10 INFO: Detent click confirmed: direction=+1, position=1
[Rotate CCW]
2025-11-23 14:35:12 DEBUG: Position change: 1 -> 2 (delta=1, direction=1, steps=1)
2025-11-23 14:35:12 INFO: Detent click confirmed: direction=+1, position=2
```
**Status:** ⚠️ **INVERTED** - Both rotations show direction=+1
- **Fix:** Swap encoder pins (see below)

---

### Example 3: Missing Clicks (Excessive Filtering)
```
2025-11-23 14:40:05 DEBUG: Position change: 0 -> 3 (delta=3, direction=1, steps=3)
2025-11-23 14:40:05 DEBUG: Bounce suppression (step 1/3): Only 0.8ms since last callback
2025-11-23 14:40:05 DEBUG: Bounce suppression (step 2/3): Only 0.3ms since last callback
2025-11-23 14:40:05 INFO: Detent click confirmed: direction=+1, position=1
```
**Status:** ⚠️ **DROPS CLICKS** - Rapid rotation (3 clicks) only fires 1 callback
- Position jumped 3, but steps 2-3 suppressed
- **Fix:** Reduce `_min_callback_interval` (see below)

---

### Example 4: No Detection at All
```
[No encoder logs appear in log file]
```
**Status:** ❌ **NO DETECTION**
- **Check:** 
  1. Are GPIO pins physically wired?
  2. Is BCM pin number correct?
  3. Is `divisor=4` correct for your encoder?
  4. Does CircuitPython module import work? (`from ruhrohrotaryio import IncrementalEncoder`)

---

## Troubleshooting

### Problem: Direction Inverted (CW = -1, CCW = +1)

**Option A: Swap the pins** (RECOMMENDED - one line change)
```python
# Find in app/hardware/__init__.py or wherever encoder is instantiated
# Before (pins swapped):
self.encoder = RotaryEncoder(pin_a=17, pin_b=27)

# After (corrected):
self.encoder = RotaryEncoder(pin_a=27, pin_b=17)
```

**Option B: Invert in callback handler**
```python
# In menu/volume control code that receives callback
def on_encoder_turn(direction, position):
    direction = -direction  # Flip it
    # ... rest of code
```

---

### Problem: Missing Clicks During Rapid Rotation

**Cause:** The 2ms bounce suppression is too aggressive for your encoder speed

**Fix:** Lower the threshold
```python
# In rotaryencoder.py, line ~28:
self._min_callback_interval = 0.001  # 1ms instead of 2ms
```

Then test again - rotate rapidly and check logs for `Bounce suppression`.

**If still missing clicks:** Lower further to `0.0005` (0.5ms) or even `0` (disabled)

---

### Problem: Too Many Callbacks (Bouncing/Flickering)

**Cause:** Electrical noise or encoder contact bouncing

**Options:**

1. **Increase bounce threshold:**
```python
self._min_callback_interval = 0.005  # 5ms instead of 2ms
```

2. **Or try higher divisor:**
```python
# In rotaryencoder.py, line ~50:
self.encoder = rotaryio_IncrementalEncoder(board_pin_a, board_pin_b, divisor=2)
# was divisor=4, try 2 for less aggressive filtering
```

3. **Or check physical connection** - loose wires cause noise

---

### Problem: Initialization Fails with "Import Error"

**Error:** `ModuleNotFoundError: No module named 'ruhrohrotaryio'`

**Check:**
1. Is CircuitPython library installed?
   ```bash
   pip list | grep -i rotary
   ```

2. Is the path correct in your CircuitPython environment?
   ```bash
   python -c "import ruhrohrotaryio; print(ruhrohrotaryio.__file__)"
   ```

3. Are you running on Raspberry Pi with CircuitPython support?
   - If using standard RPi OS with Python 3, this won't work
   - Need Blinka/CircuitPython compatibility layer installed

---

## Log Collection for Debugging

### Capture Detailed Encoder Logs
```bash
# Start your app and let it run for a minute
# Perform various encoder actions: slow rotation, rapid rotation, pauses

# Then extract just encoder activity:
grep "RotaryEncoder\|Detent click\|Position change\|Bounce suppression" \
  /path/to/app.log > /tmp/encoder_debug.log

# Count detent clicks
grep "Detent click confirmed" /tmp/encoder_debug.log | wc -l

# Extract just directions
grep "Detent click confirmed" /tmp/encoder_debug.log | grep -o "direction=[+-][0-9]"
```

### Share for Analysis
When reporting issues, include:
1. **The log file:** `/tmp/encoder_debug.log` (above)
2. **Pin configuration:** What GPIO pins are you using?
3. **Hardware:** What board (Pi 4, Pi 5, etc.) and encoder model (KY-040 variant)?
4. **Symptoms:** What exactly is wrong? (too sensitive, direction wrong, etc.)

---

## Configuration Reference

### Default Settings (From Updated Code)

```python
# Debounce
_min_callback_interval = 0.002  # 2ms

# Polling
time.sleep(0.01)  # Poll every 10ms

# Hardware divisor
divisor = 4  # One count per detent on KY-040
```

### Tuning Guide

| Issue | Adjustment | Effect |
|-------|------------|--------|
| Too many bounces | Increase `_min_callback_interval` to 0.005-0.01 | Filters more noise, less responsive |
| Missing clicks | Decrease `_min_callback_interval` to 0.001 | More sensitive, catches rapid spins |
| Polling latency | Decrease `time.sleep()` to 0.005 | Lower latency, higher CPU |
| Too slow | Increase `time.sleep()` to 0.02 | Less responsive, lower CPU |
| Too many false counts | Increase `divisor` to 2 | Less sensitive, cleaner |
| Too few counts | Decrease `divisor` to 1 | More sensitive, might bounce |

---

## Performance Expectations

### CPU Usage
- Polling thread: **< 1% CPU** (daemon thread, minimal work)
- Callbacks: **Depends on UI** (usually < 1% handling menu/volume)

### Latency
- Detection: **10-20ms** (polling interval + position detection)
- Callback firing: **1-2ms** (direct call, no queuing)

### Accuracy
- Should detect every physical detent click
- Should NOT fire spurious callbacks
- Direction should be 100% consistent

---

## Verification Checklist

- [ ] Encoder initializes (check logs for "initialized on GPIO")
- [ ] Single CW click detected (logs show direction=+1)
- [ ] Single CCW click detected (logs show direction=-1)
- [ ] Rapid 10-click CW: ~10 callbacks fire
- [ ] Rapid 10-click CCW: all show direction=-1
- [ ] No spurious callbacks between intentional rotations
- [ ] Position increments/decrements correctly
- [ ] Cleanup logs appear when app stops

---

## Contact/Debug Info Template

When reporting an issue, please provide:

```
## Rotary Encoder Issue Report

**Problem:** [Describe the issue]

**Hardware:**
- Board: [Pi 4/Pi 5/Other]
- Encoder: [KY-040 variant/Other]
- Pin A: [GPIO number]
- Pin B: [GPIO number]

**Behavior:**
[Describe what happens vs what should happen]

**Recent Logs (first encoder click):**
[Paste 5-10 lines from logs]

**Attempted Fixes:**
[List anything already tried]
```

