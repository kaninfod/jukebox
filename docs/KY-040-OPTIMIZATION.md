# KY-040 Rotary Encoder Optimization Guide

## 🎛️ KY-040 Characteristics

The KY-040 rotary encoder module is known for:
- **Signal bounce** due to mechanical contacts
- **Noisy transitions** during rotation
- **Inconsistent timing** between detent positions

## 🔧 Implemented Improvements

### 1. **Enhanced Debouncing**
- **Software debouncing** with stability checking
- **Minimum interval timing** (10ms) between reads
- **Multiple stable readings** required before accepting change

### 2. **Proper Quadrature Decoding**
- **Gray code sequence** for accurate direction detection
- **State transition table** for KY-040 specific patterns
- **Eliminates false direction changes**

### 3. **Optimized Configuration**
```bash
# In .env file for fine-tuning:
ENCODER_BOUNCETIME=5        # Hardware debounce (ms)
ROTARY_ENCODER_PIN_A=6      # CLK pin
ROTARY_ENCODER_PIN_B=5      # DT pin
```

## 🧪 Testing Your Encoder

Run the test script to verify performance:
```bash
python3 test_rotary_encoder.py
```

### Expected Results:
- **Smooth rotation**: No duplicate steps during slow turns
- **Responsive**: Fast turns register correctly  
- **Accurate direction**: CW/CCW detection is consistent
- **No missed steps**: Each detent registers once

## 🎯 Troubleshooting

### Problem: Still experiencing bounce
**Solution**: Increase `ENCODER_BOUNCETIME` to 10-15ms

### Problem: Encoder feels sluggish
**Solution**: Decrease `ENCODER_BOUNCETIME` to 2-3ms

### Problem: Wrong direction detection
**Solution**: Swap Pin A and Pin B in configuration

### Problem: Missed steps during fast rotation
**Solution**: Check wiring and ensure good connections

## ⚡ Hardware Tips

### Wiring Quality
- Use **short, shielded wires** to reduce interference
- Ensure **solid connections** to prevent intermittent contact
- Add **pull-up resistors** (10kΩ) if problems persist

### Power Supply
- Ensure **clean 3.3V/5V** supply to the encoder
- Consider **decoupling capacitors** (100nF) near the encoder

### Physical Installation
- **Secure mounting** to prevent mechanical wobble
- **Clean contacts** if encoder feels gritty
- Consider **encoder with better build quality** for critical applications
