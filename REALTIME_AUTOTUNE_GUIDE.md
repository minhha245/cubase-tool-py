# Realtime Auto-Tune Detection - Hướng dẫn sử dụng

## 📦 Cài đặt Dependencies

### Cách 1: Cài đặt đầy đủ (Khuyến nghị - Độ chính xác cao nhất)
```bash
pip install crepe tensorflow sounddevice numpy
```

### Cách 2: Cài đặt nhẹ hơn (Nhanh hơn nhưng ít chính xác hơn một chút)
```bash
pip install aubio sounddevice numpy
```

### Cách 3: Cài đặt tất cả từ requirements.txt
```bash
pip install -r requirements.txt
```

## 🎤 Cấu hình Audio Input

### 1. Kiểm tra thiết bị audio
Chạy file `realtime_pitch_detector.py` để xem danh sách thiết bị:
```bash
python realtime_pitch_detector.py
```

Bạn sẽ thấy danh sách như:
```
=== Available Audio Input Devices ===
[0] Microphone (Realtek High Definition Audio) (Channels: 2)
[1] Line In (USB Audio Interface) (Channels: 2)
[2] Stereo Mix (Realtek HD Audio) (Channels: 2)
=====================================
```

### 2. Chọn thiết bị đúng
- **Microphone**: Nếu bạn muốn phát hiện từ mic trực tiếp
- **Line In**: Nếu bạn dùng audio interface
- **Stereo Mix / Loopback**: Nếu bạn muốn phát hiện từ output của Cubase (khuyến nghị!)

### 3. Cấu hình trong code
Mở `controller_gui.py`, tìm dòng:
```python
self.pitch_detector = RealtimePitchDetector(
    midi_callback=self.on_pitch_detected,
    device_index=None  # <-- Thay None bằng số thiết bị, ví dụ: 2
)
```

## 🎵 Cách sử dụng

### 1. Mở loopMIDI
- Đảm bảo loopMIDI port đang chạy (để gửi MIDI đến Cubase)

### 2. Setup Auto-Tune trong Cubase
- Mở Auto-Tune plugin trên track vocal
- Đảm bảo Auto-Tune đang ở chế độ "Auto" mode
- Kiểm tra MIDI input của Auto-Tune đã được kích hoạt

### 3. Chạy Controller
```bash
python controller_gui.py
```

### 4. Sử dụng nút AUTO RT
- Click nút **"AUTO RT"** để bắt đầu dò tone realtime
- Nút sẽ đổi thành **"ĐANG DÒ RT"** (màu xanh lá)
- Hát hoặc phát nhạc vào microphone/input đã chọn
- Controller sẽ tự động:
  - Phát hiện key và scale đang hát
  - Gửi MIDI đến Auto-Tune
  - Cập nhật Auto-Tune theo thời gian thực

### 5. Dừng detection
- Click lại nút **"ĐANG DÒ RT"** để dừng

## 🔧 Tùy chỉnh nâng cao

### Điều chỉnh độ nhạy
Mở `realtime_pitch_detector.py`, tìm:
```python
self.confidence_threshold = 0.5  # Giảm xuống 0.3 nếu muốn nhạy hơn
self.analysis_window = 5.0  # Giảm xuống 3.0 để phản ứng nhanh hơn
```

### Chọn model CREPE
Trong `realtime_pitch_detector.py`:
```python
self.model_capacity = 'tiny'  # Options: 'tiny', 'small', 'medium', 'large', 'full'
```
- `tiny`: Nhanh nhất, ít chính xác nhất
- `small`: Cân bằng (khuyến nghị)
- `full`: Chậm nhất, chính xác nhất

## 📊 So sánh với Auto-Key Plugin

### Auto-Key Plugin (DÒ TONE cũ)
✅ Rất chính xác (sử dụng thuật toán Antares)  
❌ Cần click thủ công  
❌ Không realtime  
❌ Cần mở plugin UI  

### Realtime Detection (AUTO RT mới)
✅ Hoàn toàn tự động  
✅ Realtime (theo dõi liên tục)  
✅ Không cần mở UI  
⚠️ Độ chính xác phụ thuộc vào model (CREPE full ≈ Auto-Key)  

## 🎯 Khuyến nghị sử dụng

1. **Hát live**: Dùng **AUTO RT** - theo dõi liên tục khi bạn hát
2. **Vocal đã thu**: Dùng **DÒ TONE** (Auto-Key) - phân tích một lần chính xác cao
3. **Kết hợp**: Dùng cả hai - AUTO RT khi hát, DÒ TONE để kiểm tra lại

## 🐛 Troubleshooting

### Lỗi: "Realtime Pitch Detector không khả dụng"
- Cài đặt: `pip install crepe tensorflow sounddevice`
- Hoặc: `pip install aubio sounddevice` (phiên bản nhẹ)

### Không phát hiện được âm thanh
- Kiểm tra device_index có đúng không
- Thử nói to hơn hoặc tăng gain của mic
- Kiểm tra Windows Sound Settings

### MIDI không đến Auto-Tune
- Kiểm tra loopMIDI port đang chạy
- Trong Auto-Tune: Enable MIDI input
- Kiểm tra MIDI channel (mặc định: 0)

### Chậm/lag
- Dùng model `tiny` thay vì `full`
- Cài TensorFlow GPU version nếu có GPU NVIDIA
- Hoặc dùng Aubio thay vì CREPE

## 💡 Tips

1. **Tối ưu độ chính xác**: Dùng CREPE model 'medium' hoặc 'full'
2. **Tối ưu tốc độ**: Dùng Aubio hoặc CREPE 'tiny'
3. **Sử dụng Stereo Mix**: Lấy âm thanh từ output của Cubase thay vì mic để tránh nhiễu
4. **Điều chỉnh analysis_window**: 3-5 giây là tối ưu cho vocal

## 📝 Version Log

- v1.0: Thêm realtime pitch detection với CREPE
- Hỗ trợ fallback sang Aubio
- Auto-detect key và scale
- MIDI output tự động đến Auto-Tune
