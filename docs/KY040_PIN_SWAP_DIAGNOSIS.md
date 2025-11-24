# KY-040 Issue - Fresh Analysis

Based on your logs and config, here's what's happening:

---

## Actual Configuration ✓

```
ROTARY_ENCODER_PIN_A = 22  # DT (Data)
ROTARY_ENCODER_PIN_B = 27  # CLK (Clock)
BUTTON_5_GPIO = 17         # SW (Switch/Pushbutton) ✓ CORRECT
```

**This is actually correctly configured!**

---

## The Real Problem 🔴

**Your logs show:**

### When you press the button:
```
Position change: 18 -> 19 (direction=+1)  
Button on GPIO 17 pressed
Button on GPIO 17 short pressed! ← Correct!
```

### When you rotate CW (one click):
```
Position change: 20 -> 21 (direction=+1)
Volume set to 55%  ← Correct, volume increased
```

### When you rotate CCW (one click) - BUT IT SHOWS:
```
Position change: 22 -> 23 (direction=+1)  ← WRONG! Should be direction=-1
Volume set to 65%  ← WRONG! Should decrease not increase
```

**The direction detection is INVERTED for CCW!**

---

## Root Causes

### Possibility 1: Physical Wiring Wrong
The KY-040 DT and CLK pins are SWAPPED.

**Check your physical wiring:**
```
KY-040 Pin → GPIO (Current)    → (Should Be)
DT         → GPIO 22           → GPIO 27?
CLK        → GPIO 27           → GPIO 22?
```

If these are swapped, that's why CCW shows as CW!

### Possibility 2: The divisor=4 Isn't Working
The hardware quadrature decoder might have issues.

### Possibility 3: Pin Mapping Issue
The BCM to board mapping might be wrong (unlikely).

---

## Quick Test

### Test 1: Physical Inspection
**Take a close-up photo of your KY-040 wiring and verify:**
```
KY-040 DT pin  → Actual GPIO (check with multimeter if needed)
KY-040 CLK pin → Actual GPIO
KY-040 SW pin  → GPIO 17 ✓ (probably correct)
```

### Test 2: Software Fix (Try This Now)
**Swap the direction in code to test:**

Edit `/app/hardware/devices/rotaryencoder.py` and change:

```python
# OLD (line ~86-92):
if position_delta > 0:
    direction = 1  # Clockwise
    num_steps = position_delta
elif position_delta < 0:
    direction = -1  # Counter-clockwise
    num_steps = abs(position_delta)

# NEW - TRY THIS (swap them):
if position_delta > 0:
    direction = -1  # Counter-clockwise
    num_steps = position_delta
elif position_delta < 0:
    direction = 1  # Clockwise
    num_steps = abs(position_delta)
```

Then:
1. Restart the app
2. Rotate CW - should now show direction=-1 (opposite)
3. Rotate CCW - should now show direction=+1 (opposite)

**If this FIXES it,** then the physical wiring is swapped.

---

## Most Likely Issue

**GPIO 22 and GPIO 27 are physically swapped on your KY-040 connections.**

The easiest fix is ONE of:

### Option A: Swap in Config (Easy, No Rewiring)
```python
# In .env, change:
ROTARY_ENCODER_PIN_A=27  # was 22
ROTARY_ENCODER_PIN_B=22  # was 27
```
Then restart the app.

### Option B: Swap the Physical Wires (Manual)
Physically move the DT and CLK wires to swap GPIOs.

### Option C: Invert Direction in Code (Hacky)
Keep wires as-is, but flip the direction calculation in code.

---

## What I Need From You

1. **Check your physical wiring** - which GPIO does each KY-040 pin go to?
2. **Try the software fix above** - does swapping direction in code fix it?
3. **Report back** - I'll tell you the best solution

---

## Why This Matters

Right now:
- ✓ Button works correctly (GPIO 17)
- ✓ CW rotation detected (direction=+1)
- ❌ CCW rotation shows as CW (direction=+1, should be -1)
- ❌ Volume goes UP for both CW and CCW

This is a **simple GPIO pin swap issue** - not a code problem!

