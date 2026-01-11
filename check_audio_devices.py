"""
Audio Device Checker
Quick script to list and test audio input devices
"""

import sounddevice as sd
import numpy as np
import time
import sys

# Fix Windows console encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

def list_devices():
    """List all audio devices"""
    print("\n" + "="*60)
    print("DANH SÁCH THIẾT BỊ AUDIO")
    print("="*60)
    
    devices = sd.query_devices()
    
    print("\n📥 THIẾT BỊ INPUT (Microphone, Line In, etc.):")
    print("-" * 60)
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            default_marker = " [MẶC ĐỊNH]" if i == sd.default.device[0] else ""
            print(f"[{i:2d}] {device['name']}{default_marker}")
            print(f"     Channels: {device['max_input_channels']}, "
                  f"Sample Rate: {device['default_samplerate']} Hz")
    
    print("\n📤 THIẾT BỊ OUTPUT (Speakers, Headphones, etc.):")
    print("-" * 60)
    for i, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            default_marker = " [MẶC ĐỊNH]" if i == sd.default.device[1] else ""
            print(f"[{i:2d}] {device['name']}{default_marker}")
            print(f"     Channels: {device['max_output_channels']}, "
                  f"Sample Rate: {device['default_samplerate']} Hz")
    
    print("\n" + "="*60)
    return devices

def test_input_device(device_index=None, duration=5):
    """
    Test an input device by recording audio and showing levels
    
    Args:
        device_index: Device index to test (None = default)
        duration: Recording duration in seconds
    """
    print(f"\n🎤 Testing input device {device_index or 'DEFAULT'}...")
    print(f"⏱️  Recording for {duration} seconds...")
    print("🔊 Speak or make noise into the microphone!\n")
    
    sample_rate = 44100
    channels = 1
    
    levels = []
    
    def audio_callback(indata, frames, time_info, status):
        """Callback to process audio chunks"""
        if status:
            print(f"Status: {status}")
        # Calculate RMS level
        rms = np.sqrt(np.mean(indata**2))
        levels.append(rms)
        
        # Visual level indicator
        bar_length = int(rms * 100)
        bar = "█" * min(bar_length, 50)
        print(f"\rLevel: {bar:<50} {rms:.4f}", end='', flush=True)
    
    try:
        with sd.InputStream(
            device=device_index,
            channels=channels,
            samplerate=sample_rate,
            callback=audio_callback
        ):
            time.sleep(duration)
        
        print("\n\n✅ Test complete!")
        
        if levels:
            avg_level = np.mean(levels)
            max_level = np.max(levels)
            
            print(f"📊 Statistics:")
            print(f"   Average Level: {avg_level:.4f}")
            print(f"   Peak Level: {max_level:.4f}")
            
            if max_level < 0.01:
                print("⚠️  WARNING: Very low audio level! Check:")
                print("   - Microphone is connected")
                print("   - Microphone is not muted")
                print("   - Windows audio input level is up")
            elif max_level < 0.05:
                print("⚠️  Audio level is low. Consider increasing input gain.")
            else:
                print("✓ Audio level looks good!")
        
    except Exception as e:
        print(f"\n❌ Error testing device: {e}")

def find_stereo_mix():
    """Try to find Stereo Mix or similar loopback device"""
    print("\n🔍 Searching for Stereo Mix / Loopback device...")
    
    devices = sd.query_devices()
    loopback_keywords = ['stereo mix', 'wave out mix', 'loopback', 'what u hear']
    
    found_devices = []
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            name_lower = device['name'].lower()
            for keyword in loopback_keywords:
                if keyword in name_lower:
                    found_devices.append((i, device['name']))
                    break
    
    if found_devices:
        print("✅ Found loopback device(s):")
        for idx, name in found_devices:
            print(f"   [{idx}] {name}")
        print("\n💡 Tip: Use this device to capture Cubase output!")
        print("   Enable in Windows Sound Settings > Recording > Stereo Mix > Enable")
    else:
        print("❌ No loopback device found.")
        print("💡 Enable 'Stereo Mix' in Windows Sound Settings:")
        print("   1. Right-click speaker icon > Sounds")
        print("   2. Recording tab")
        print("   3. Right-click empty area > Show Disabled Devices")
        print("   4. Enable 'Stereo Mix'")

if __name__ == "__main__":
    print("""
==============================================================
         AUDIO DEVICE CHECKER - Hau Setup Studio
==============================================================
""")
    
    # List all devices
    devices = list_devices()
    
    # Find stereo mix
    find_stereo_mix()
    
    # Interactive test
    print("\n" + "="*60)
    print("INTERACTIVE TEST")
    print("="*60)
    
    while True:
        try:
            choice = input("\nEnter device number to test (or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                print("👋 Goodbye!")
                break
            
            device_idx = int(choice)
            
            # Validate device
            if device_idx < 0 or device_idx >= len(devices):
                print(f"❌ Invalid device number. Must be 0-{len(devices)-1}")
                continue
            
            if devices[device_idx]['max_input_channels'] == 0:
                print("❌ This device has no input channels!")
                continue
            
            # Test device
            test_input_device(device_idx, duration=5)
            
        except ValueError:
            print("❌ Please enter a valid number or 'q'")
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
