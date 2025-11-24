# KY-040 Encoder/Button Configuration Issue - Diagnosis

**Status:** 🔴 CRITICAL - Multiple Configuration Issues Found  
**Date:** November 23, 2025

---

## The Problems (What's Wrong)

### Problem #1: Pushbutton is on GPIO 17, Not Encoder Button GPIO

**Your Config:**
```
ROTARY_ENCODER_PIN_A: 22 (DT - Data)
ROTARY_ENCODER_PIN_B: 27 (CLK - Clock)
BUTTON_5_GPIO: 17 ← THIS IS WRONG FOR ENCODER BUTTON!
```

**The KY-040 has 5 pins:**
1. **+5V** - Power
2. **GND** - Ground
3. **DT** - Data (should be GPIO 22) ✅
4. **CLK** - Clock (should be GPIO 27) ✅
5. **SW** - Switch/Button (should be on a DIFFERENT GPIO) ❌

**Your Log Shows:**
```
Button on GPIO 17 pressed
Button on GPIO 17 short pressed! (0.20s)
```

**This means:** GPIO 17 is currently configured as BUTTON_5, NOT as the encoder pushbutton!

---

### Problem #2: All Rotations Show direction=+1 (Always CW)

**Your Logs Show:**
```
"this is one click CW"
position change: 20 -> 21, direction=+1, payload: direction='CW' ✅

"this is one click CCW"  
position change: 22 -> 23, direction=+1, payload: direction='CW' ❌ Should be direction=-1!
```

**This suggests:** Either the pins are physically swapped, OR the divisor isn't working correctly.

---

### Problem #3: Configuration Inconsistency

The comment says:
```
# Software pins swapped: PIN_A reads DT, PIN_B reads CLK for correct direction
```

But your logs show BOTH CW and CCW always as `direction=+1`, which means either:
- The physical wires are incorrectly connected
- The hardware divisor isn't detecting correctly
- The pin mapping is off

---

## Root Cause Analysis

Looking at your logs more carefully:

**Push on pushbutton:**
```
Position change: 18 -> 19 (delta=1, direction=1)
Button on GPIO 17 pressed
Button on GPIO 17 short pressed!
```

**Single CW click:**
```
Position change: 20 -> 21 (delta=1, direction=1)
```

**Single CCW click (labeled):**
```
Position change: 22 -> 23 (delta=1, direction=1)  ← Should be delta=-1
```

**The encoder is incrementing in BOTH directions!** This is the real issue.

---

## Solutions

### Solution 1: Add Encoder Button to Config (RECOMMENDED)

The KY-040 SW pin should have its own GPIO. You need to:

1. **Identify which GPIO** the KY-040 SW pin is actually wired to
2. **Add it to config.py:**

```python
# In app/config.py, add:
ROTARY_ENCODER_BUTTON_GPIO: int = int(os.getenv("ROTARY_ENCODER_BUTTON_GPIO", "?"))  # Need to find this
```

3. **Update hardware.py** to use it properly (not as BUTTON_5)

### Solution 2: Fix the Direction Issue

Since BOTH directions show as +1, the pins might be:
- **Physically swapped** in your wiring
- **Or the divisor=4 isn't working** as expected

**Test:** Try inverting the direction in the code:

```python
# In rotaryencoder.py, change direction calculation:
if position_delta > 0:
    direction = -1  # Flip it
    num_steps = position_delta
elif position_delta < 0:
    direction = 1  # Flip it
    num_steps = abs(position_delta)
```

Then test again and report back.

---

## What You Should Do NOW

### Immediate Action: Identify the Wires

**What are the 5 KY-040 pins wired to?**

```
KY-040 Pin  →  Raspberry Pi GPIO  (Current Status)
+5V         →  5V power
GND         →  GND
DT (Data)   →  GPIO 22            ✅ Correct
CLK (Clock) →  GPIO 27            ✅ Correct  
SW (Button) →  GPIO ?? (UNKNOWN)   ❌ Not in config!
```

**FIND OUT:** What GPIO is the SW (pushbutton) pin wired to?

---

## Why This Matters

1. **GPIO 17 is BUTTON_5** - Not the encoder button
2. **The encoder button isn't being tracked separately** - It's on some unknown GPIO
3. **Direction is always +1** - Something is fundamentally wrong with the quadrature detection

---

## Next Steps

1. **Check your physical wiring** - Take a photo and identify:
   - Which GPIO is the encoder's SW pin connected to?
   - Verify DT is on 22, CLK is on 27

2. **Tell me the GPIO numbers:**
   - Encoder DT pin → GPIO ___
   - Encoder CLK pin → GPIO ___
   - Encoder SW pin → GPIO ___

3. **Once you provide this,** I'll update the config and fix the code

---

## Quick Diagnostic

Can you run this to see what's happening:

```bash
# Tell me what these show:
grep "ROTARY_ENCODER\|BUTTON" /Volumes/jukeplayer/jukebox/.env | grep -v "#"

# And show me the physical KY-040 pin connections in a photo or description
```

---

## Summary

| Issue | Status | Fix |
|-------|--------|-----|
| GPIO 17 is BUTTON_5, not encoder button | 🔴 Critical | Identify correct SW pin GPIO |
| Direction always shows CW | 🔴 Critical | May need to swap pins or invert direction |
| Encoder and pushbutton mixed up | 🔴 Critical | Separate configs needed |

**I can't fix this until you tell me which GPIO the encoder SW (pushbutton) is wired to.**

