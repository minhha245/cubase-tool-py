# 🎛️ Cubase Controller Tool - Hậu Setup Live Studio

Bảng điều khiển tiếng Việt cho Cubase với tính năng Auto-Tune Detection theo thời gian thực.

## ✨ Tính năng chính

### 🎵 Auto-Tune Detection
- **DÒ TONE** (Auto-Key): Tự động phát hiện key/scale bằng Auto-Key plugin (click tự động)
- **AUTO RT** (NEW!): Phát hiện key/scale theo thời gian thực không cần plugin
  - Sử dụng AI (CREPE) để phát hiện pitch chính xác cao
  - Tự động gửi MIDI đến Auto-Tune
  - Hoạt động realtime khi bạn đang hát

### 🎚️ Mixer Controls
- **Volume Sliders**: Âm nhạc, Mic, Reverb Long/Short, Delay
- **Mute Buttons**: Nhạc, Mic
- **Effect Buttons**: Vang FX, Fix Méo

### 🎹 Tone/Tune Controls
- **Tone**: Điều chỉnh transpose (+/- 12 semitones)
- **Tune**: Điều chỉnh pitch fine-tuning

### 💾 Other Features
- Auto-save/load settings
- Licensed activation system
- MIDI mapping via loopMIDI

## 📦 Installation

### 1️⃣ Clone hoặc download project
```bash
git clone <repo-url>
cd cubase-tool-py
```

### 2️⃣ Cài đặt Python dependencies

**Option A: Full Installation (Recommended - High Accuracy)**
```bash
pip install -r requirements.txt
```

**Option B: Minimal Installation (No Realtime Detection)**
```bash
pip install customtkinter python-rtmidi pyautogui pygetwindow
```

**Option C: với Aubio thay vì CREPE (Faster but less accurate)**
```bash
pip install customtkinter python-rtmidi pyautogui pygetwindow aubio sounddevice numpy
```

### 3️⃣ Cài đặt loopMIDI
- Download: https://www.tobias-erichsen.de/software/loopmidi.html
- Tạo port mới tên "loopMIDI Port 1"
- Ensure port is running

### 4️⃣ Setup Audio Input (for Realtime Detection)
```bash
python check_audio_devices.py
```
- Xem danh sách audio devices
- Chọn device phù hợp (Microphone hoặc Stereo Mix)
- **HOẶC:** Dùng nút **AUDIO** trong GUI để chọn thiết bị (Recommended!)

### 5️⃣ ~~Configure Device (Optional)~~ - KHÔNG CẦN NỮA!
**Cập nhật mới:** Bạn có thể chọn thiết bị audio trực tiếp trong GUI bằng nút **AUDIO**!  
Xem [AUDIO_DEVICE_SELECTION_GUIDE.md](AUDIO_DEVICE_SELECTION_GUIDE.md) để biết chi tiết.

## 🚀 Usage

### Basic Usage
```bash
python controller_gui.py
```

### First Time Setup
1. Enter activation key: `HAU_SETUP_STUDIO_2025`
2. Program will activate and save license to disk

### Cubase Setup
1. Open Cubase
2. Add MIDI track or enable MIDI input on instrument track
3. Set MIDI input to "loopMIDI Port 1"
4. Map Quick Controls (QC1-QC8) to desired parameters:
   - QC1: Music Volume
   - QC2: Music Mute
   - QC3: Reverb Long
   - QC4: Reverb Short
   - QC5: Tone/Transpose
   - QC6: Tune/Pitch
   - QC7: Delay
   - QC8: (Reserved)

### Auto-Tune Setup (for Realtime Detection)
1. Insert Auto-Tune plugin on vocal track
2. Enable MIDI control in Auto-Tune settings
3. Set Auto-Tune to "Auto" mode
4. Make sure MIDI input is enabled

## 🎤 Using Realtime Auto-Tune

### Chọn Thiết Bị Audio Input (NEW!)
1. Click nút **AUDIO** (màu xanh dương)
2. Chọn thiết bị từ danh sách (Microphone, Stereo Mix, v.v.)
3. Nhấn **🎤 Test** để kiểm tra thiết bị (optional)
4. Nhấn **✓ Áp Dụng** để lưu
5. Thiết bị hiện tại được hiển thị trong khung **🎵 DETECTED KEY**

📖 Xem chi tiết: [AUDIO_DEVICE_SELECTION_GUIDE.md](AUDIO_DEVICE_SELECTION_GUIDE.md)

### Method 1: AUTO RT Button (New!)
1. Click **AUTO RT** button
2. Button turns green: **"ĐANG DÒ RT"**
3. Sing or play music into selected audio input
4. Controller automatically:
   - Detects musical key (C, D, E, etc.)
   - Detects scale (Major/Minor)
   - Sends MIDI to Auto-Tune
   - Updates in real-time
5. Click again to stop

### Method 2: DÒ TONE Button (Classic)
1. Click **DÒ TONE** button
2. Make sure Auto-Key plugin is open in Cubase
3. Controller will:
   - Click "Listen" button
   - Wait 15 seconds
   - Click "Send" button
4. Auto-Key sends detected key to Auto-Tune

### Which method to use?
- **AUTO RT**: For live singing, continuous monitoring
- **DÒ TONE**: For pre-recorded vocals, one-time detection

## 🔧 Troubleshooting

### "Realtime Pitch Detector không khả dụng"
Install CREPE:
```bash
pip install crepe tensorflow sounddevice numpy
```

Or use Aubio (lighter):
```bash
pip install aubio sounddevice numpy
```

### No audio detected in AUTO RT mode
1. Check audio device with: `python check_audio_devices.py`
2. Ensure correct device_index in `controller_gui.py`
3. Check Windows Sound Settings > Recording
4. Ensure input is not muted and volume is up

### MIDI not reaching Auto-Tune
1. Check loopMIDI port is running
2. In Auto-Tune: Enable MIDI input
3. Check MIDI channel (default: 0)
4. Verify "loopMIDI Port 1" is selected in Cubase MIDI settings

### Slow/Laggy detection
1. Use CREPE 'tiny' or 'small' model instead of 'full'
2. Or switch to Aubio (faster)
3. Install TensorFlow GPU if you have NVIDIA GPU

## 📁 Project Structure

```
cubase-tool-py/
├── controller_gui.py              # Main GUI application
├── realtime_pitch_detector.py     # Realtime pitch detection module
├── CustomController.js            # Cubase MIDI Remote script
├── check_audio_devices.py         # Audio device checker utility
├── requirements.txt               # Python dependencies
├── config.json                    # Saved settings (auto-generated)
├── license.dat                    # License file (auto-generated)
├── AUDIO_DEVICE_SELECTION_GUIDE.md # Guide for audio device selection (NEW!)
├── REALTIME_AUTOTUNE_GUIDE.md     # Detailed guide for RT feature
└── build_exe.bat                  # Build .exe file
```

## 🎯 MIDI CC Mapping

| Control | CC Number | Description |
|---------|-----------|-------------|
| MIC_VOL | 20 | Microphone volume |
| MUSIC_VOL | 21 | Music volume |
| REVERB_LONG | 22 | Long reverb amount |
| REVERB_SHORT | 23 | Short reverb amount |
| MUTE_MIC | 24 | Mute microphone (toggle) |
| MUTE_MUSIC | 25 | Mute music (toggle) |
| DELAY | 26 | Delay effect amount |
| TUNE | 27 | Pitch fine-tune |
| TONE_VAL_SEND | 28 | Tone transpose value |
| DO_TONE | 30 | Trigger Auto-Key detection |
| ~~LAY_TONE~~ | ~~31~~ | (Removed - replaced by AUTO_TUNE_RT) |
| VANG_FX | 32 | Vang effect trigger |
| FIX_MEO | 36 | Fix distortion button |
| AUTO_TUNE_RT | 37 | Realtime auto-tune detection (NEW!) |

## 📚 Additional Resources

- [AUDIO_DEVICE_SELECTION_GUIDE.md](AUDIO_DEVICE_SELECTION_GUIDE.md) - Hướng dẫn chọn thiết bị audio cho AUTO_TUNE_RT (NEW!)
- [REALTIME_AUTOTUNE_GUIDE.md](REALTIME_AUTOTUNE_GUIDE.md) - Chi tiết về tính năng Auto-Tune RT
- [CREPE Documentation](https://github.com/marl/crepe) - Thuật toán pitch detection
- [loopMIDI Download](https://www.tobias-erichsen.de/software/loopmidi.html)

## 🔬 Technical Details

### Pitch Detection Algorithms
1. **CREPE** (Convolutional REpresentation for Pitch Estimation)
   - Deep learning based
   - Extremely accurate (~99% on clean audio)
   - Models: tiny, small, medium, large, full
   - Requires TensorFlow

2. **Aubio** (Fallback)
   - YIN-FFT algorithm
   - Fast and efficient
   - Good accuracy (~95% on clean audio)
   - No deep learning required

### Key Detection Logic
1. Collect pitch samples over time window (default: 5 seconds)
2. Convert frequencies to MIDI note numbers
3. Analyze note distribution using music theory:
   - Major scale pattern: 0, 2, 4, 5, 7, 9, 11 semitones
   - Minor scale pattern: 0, 2, 3, 5, 7, 8, 10 semitones
4. Determine tonic (most common note)
5. Match scale pattern to determine major/minor

### MIDI Communication
- MIDI Note messages for key detection
- Note velocity indicates scale type:
  - 127 = Major scale
  - 64 = Minor scale

## 📄 License

Licensed to: Hậu Setup Live Studio  
Activation Key: `HAU_SETUP_STUDIO_2025`

## 🙏 Credits

- GUI Framework: CustomTkinter
- MIDI Library: python-rtmidi
- Pitch Detection: CREPE (GitHub: marl/crepe) / Aubio
- Virtual MIDI: loopMIDI by Tobias Erichsen

---

**© 2025 Hậu Setup Live Studio**  
Made with ❤️ for Vietnamese music producers
