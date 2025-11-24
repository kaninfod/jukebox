# KY-040 Pin Swap Fix - Applied ✅

**Status:** Fix Applied and Ready to Test  
**Date:** November 23, 2025

---

## What Was Wrong

Looking at your logs:
- ✓ Pushbutton works (GPIO 17)
- ✓ CW rotation detected
- ❌ **CCW also shows as CW** (direction=+1 always)
- ❌ **Volume goes UP for both directions**

**Root Cause:** GPIO 22 and GPIO 27 were SWAPPED

---

## What I Fixed

### The Change (In `.env`):

```diff
- ROTARY_ENCODER_PIN_A=22    # Was DT
- ROTARY_ENCODER_PIN_B=27    # Was CLK

+ ROTARY_ENCODER_PIN_A=27    # Now DT
+ ROTARY_ENCODER_PIN_B=22    # Now CLK
```

**That's it! One simple swap.**

---

## How to Test It

1. **Restart your jukebox app**
2. **Rotate CW once** → Check logs:
   ```
   direction=+1  ← Should still be +1
   Volume UP     ← Should increase
   ```
3. **Rotate CCW once** → Check logs:
   ```
   direction=-1  ← Should NOW be -1 (was +1 before)
   Volume DOWN   ← Should decrease
   ```

---

## Expected Behavior After Fix

### Push Encoder Button:
```
Button on GPIO 17 pressed ✓
Button on GPIO 17 short pressed!
Rotary encoder button was pressed!
BUTTON_PRESSED event
```

### Rotate CW (Right):
```
Position change: X -> X+1 (delta=+1, direction=+1)
Detent click confirmed: direction=+1
ROTARY_ENCODER event: direction='CW'
Volume INCREASES
```

### Rotate CCW (Left):
```
Position change: X -> X-1 (delta=-1, direction=-1)
Detent click confirmed: direction=-1
ROTARY_ENCODER event: direction='CCW'
Volume DECREASES
```

---

## If It Still Doesn't Work

If after restart you STILL see all directions as +1:

**Option 1: Physical Pin Swap**
- The GPIO pins might be wired to the wrong physical pins
- Check: Is GPIO 22 actually wired to KY-040 DT?
- Check: Is GPIO 27 actually wired to KY-040 CLK?

**Option 2: Invert Direction in Code**
If pins can't be changed physically, edit:
```python
# File: /app/hardware/devices/rotaryencoder.py
# Around line 86-92, in _poll_position()

# Change this:
if position_delta > 0:
    direction = 1
    num_steps = position_delta
elif position_delta < 0:
    direction = -1
    num_steps = abs(position_delta)

# To this:
if position_delta > 0:
    direction = -1  # Flip
    num_steps = position_delta
elif position_delta < 0:
    direction = 1   # Flip
    num_steps = abs(position_delta)
```

---

## Summary

| Component | Status | Action |
|-----------|--------|--------|
| Pushbutton (GPIO 17) | ✓ Working | None - already correct |
| Config Pin Swap | ✅ Applied | Restart app to use |
| CW Rotation | ✓ Working | Should continue to work |
| CCW Rotation | ❌ Was wrong → ✅ Should now be fixed | Test after restart |

---

## What to Do

1. **Restart the app** (so `.env` changes take effect)
2. **Test both directions** (CW and CCW)
3. **Report back** if it works or if you need the code-level fix

The pushbutton confusion was a misunderstanding - GPIO 17 IS correctly the encoder button (BUTTON_5). The real issue was the DT/CLK pins being swapped!

