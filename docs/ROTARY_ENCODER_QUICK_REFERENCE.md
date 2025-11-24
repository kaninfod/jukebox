# Rotary Encoder - Quick Reference Card

**Print this or bookmark for quick lookup while testing**

---

## The Problem (What Was Wrong)

```
❌ 150ms debounce (75x too high)  →  Encoder feels dead
❌ No multi-click handling        →  Loses clicks during rapid rotation
❌ Minimal logging                →  Can't debug what's wrong
❌ Inverted/wrong direction       →  UI goes backward
```

---

## The Solution (What We Fixed)

```
✅ 2ms debounce (appropriate)     →  Responsive, testable
✅ Multi-step processing         →  All clicks counted
✅ Comprehensive logging         →  DEBUG/INFO/ERROR visible
✅ Better direction handling     →  Correct behavior, easy to fix if inverted
```

---

## Quick Test Commands

```bash
# 1. Check if initialized
tail -50 /path/to/app.log | grep "RotaryEncoder initialized"

# 2. Count total clicks
grep "Detent click confirmed" /path/to/app.log | wc -l

# 3. Show last 5 clicks
grep "Detent click confirmed" /path/to/app.log | tail -5

# 4. Count CW clicks (direction=+1)
grep "direction=+1" /path/to/app.log | wc -l

# 5. Count CCW clicks (direction=-1)
grep "direction=-1" /path/to/app.log | wc -l

# 6. Watch in real-time
tail -f /path/to/app.log | grep "Detent click"

# 7. Save debug report
grep -E "RotaryEncoder|Detent|Position|ERROR" /path/to/app.log > /tmp/encoder_report.txt
```

---

## Expected Logs (Good = These Patterns)

| Situation | Log Pattern |
|-----------|------------|
| **Init OK** | `INFO: RotaryEncoder initialized` |
| **CW Click** | `INFO: Detent click confirmed: direction=+1` |
| **CCW Click** | `INFO: Detent click confirmed: direction=-1` |
| **Rapid Clicks** | Multiple lines, each with `direction=+1` or `-1` |
| **Position Track** | `position=1` then `position=2` then `position=3` |

---

## Bad Logs (These Mean Problems)

| Pattern | Problem | Fix |
|---------|---------|-----|
| No init log | Not initialized | Check GPIO pins, CircuitPython install |
| No activity | Not detecting rotation | Check physical wires |
| Only `direction=+1` when rotating both ways | Direction inverted | Swap encoder pins |
| Many `Bounce suppression` | Electrical noise | Check wires, increase debounce |
| Few clicks for many rotations | Too much filtering | Decrease debounce |

---

## One-Line Fixes

### Fix 1: Direction Inverted
**File:** `app/hardware/devices/rotaryencoder.py` or wherever encoder instantiated

```python
# BEFORE: RotaryEncoder(pin_a=17, pin_b=27)
# AFTER:  RotaryEncoder(pin_a=27, pin_b=17)  # Swap pins
```

### Fix 2: Too Much Bouncing
**File:** `app/hardware/devices/rotaryencoder.py`

```python
# Line ~28, CHANGE:
self._min_callback_interval = 0.005  # Increase from 0.002
```

### Fix 3: Missing Clicks
**File:** `app/hardware/devices/rotaryencoder.py`

```python
# Line ~28, CHANGE:
self._min_callback_interval = 0.001  # Decrease from 0.002
```

### Fix 4: Sluggish Response
**File:** `app/hardware/devices/rotaryencoder.py`

```python
# Line ~117, CHANGE:
time.sleep(0.005)  # Decrease from 0.01
```

---

## Testing Flow

```
┌─ Start App
│
├─ Check Initialization Log
│  └─ Should show: "RotaryEncoder initialized"
│
├─ Rotate CW Once
│  └─ Should show: "direction=+1"
│
├─ Rotate CCW Once
│  └─ Should show: "direction=-1"
│
├─ Rapid 10 Rotations
│  └─ Should show: ~10 clicks
│
└─ UI Should Respond
   └─ Volume changes, menu moves, etc.
```

**If ANY step fails → Check debugging guide (separate doc)**

---

## Configuration Cheat Sheet

| Setting | Location | Default | Effect |
|---------|----------|---------|--------|
| Debounce | Line ~28 | 0.002 | Lower = more clicks, more noise |
| Polling | Line ~117 | 0.01 | Lower = lower latency, higher CPU |
| Divisor | Line ~50 | 4 | Higher = less sensitive |

---

## Files to Know

```
Code:        /app/hardware/devices/rotaryencoder.py
Docs:        /docs/ROTARY_ENCODER_*.md
- Summary:   ROTARY_ENCODER_FIX_SUMMARY.md (START HERE)
- Testing:   ROTARY_ENCODER_TESTING_CHECKLIST.md (TESTING)
- Debug:     ROTARY_ENCODER_DEBUGGING_GUIDE.md (TROUBLESHOOT)
- Deep:      ROTARY_ENCODER_CIRCUITPYTHON_REFACTOR.md
- Compare:   ROTARY_ENCODER_RPiGPIO_VS_CIRCUITPYTHON.md
```

---

## Common Scenarios

### Scenario 1: Encoder Initializes but Doesn't Detect Rotation
```
Check:
□ Are GPIO pins physically connected?
□ Are you using correct pin numbers?
□ Is CircuitPython library installed?
  python3 -c "import ruhrohrotaryio; print('OK')"
□ Try rotating more slowly
```

### Scenario 2: Direction Backwards
```
Quick Fix: Swap encoder pins (one line change)
BEFORE: RotaryEncoder(pin_a=17, pin_b=27)
AFTER:  RotaryEncoder(pin_a=27, pin_b=17)
```

### Scenario 3: Rapid Rotation Loses Clicks
```
Check logs:
grep "Bounce suppression" /path/to/app.log | wc -l

If many: Lower debounce (line ~28 from 0.002 to 0.001)
If few:  Rotation is probably fine, just slow
```

### Scenario 4: Encoder Feels Sluggish
```
Lower polling interval (line ~117 from 0.01 to 0.005)
OR check if app CPU is overloaded (ps aux)
```

---

## Logging Levels (What You'll See)

| Level | Example | Means |
|-------|---------|-------|
| **DEBUG** | `Position change: 0 -> 1` | Detailed state tracking (normal) |
| **INFO** | `Detent click confirmed: direction=+1` | Click happened (what you want to see) |
| **ERROR** | `Failed to initialize rotary encoder` | Something broke |

---

## PIN REFERENCE

**Your Hardware:**

| Pin | Function | GPIO Number |
|-----|----------|-------------|
| A | Encoder Phase A | **__________** |
| B | Encoder Phase B | **__________** |
| GND | Ground | (shared with system GND) |
| VCC | Power | (3.3V or 5V - check encoder spec) |

**Write these down to avoid confusion!**

---

## Success Checklist ✅

- [ ] Encoder initializes (check logs)
- [ ] CW rotation detected (direction=+1)
- [ ] CCW rotation detected (direction=-1)
- [ ] 10 rapid clicks = ~10 log entries
- [ ] UI responds to rotation
- [ ] No spurious clicks when idle
- [ ] Direction is consistent

**If all checked:** ✅ Ready to deploy!

---

## Call Stack (For Debugging Code)

```
User rotates encoder
    ↓
CircuitPython hardware detects quadrature
    ↓
rotaryio module decodes (with divisor=4)
    ↓
position changes
    ↓
_poll_position() loop detects delta
    ↓
_min_callback_interval check (2ms min)
    ↓
callback fired to UI handler
    ↓
UI updates (volume, menu, etc.)
```

**Time breakdown:**
- Hardware detection: <1ms
- Polling loop: up to 10ms
- Callback: <1ms
- UI update: varies
- **Total user latency: ~10-20ms** (imperceptible)

---

## Before/After Comparison

```
BEFORE (Broken):
Rotate slowly  → Wait 150ms → Maybe something happens
Rotate fast    → Most clicks lost
Logs           → Can't see what's wrong
UI             → Feels dead

AFTER (Fixed):
Rotate slowly  → Immediate response
Rotate fast    → All clicks counted
Logs           → Shows exactly what's happening
UI             → Feels responsive
```

---

## Emergency Rollback

If you need to go back to the old version:

```bash
# The old version is here (your attachment):
# rotaryencoder.py (from attachment)

# Just restore it and it should work as before
# (but with the 150ms debounce issue)
```

---

## Contact/Support

When reporting issues, provide:

```
Issue: _________________________________
Hardware: Pi 4 / Pi 5 / Other: _________
Pins: A=_____ B=_____
Symptom: ______________________________

Logs (last 10):
[Paste here]
```

---

**Last Updated:** November 23, 2025
**Version:** 1.0 (Initial Release)

