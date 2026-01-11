# Hướng Dẫn Chọn Thiết Bị Audio Input cho AUTO_TUNE_RT

## Tổng Quan
Tính năng này cho phép bạn chọn nguồn audio input từ danh sách các thiết bị âm thanh của hệ thống để AUTO_TUNE_RT có thể phát hiện key từ nguồn âm thanh mong muốn.

### Giao Diện Dialog Chọn Thiết Bị
![Audio Device Selector](C:/Users/minhha/.gemini/antigravity/brain/2b85eba7-1e0d-43a8-b4b9-0da87f0361b1/audio_device_selector_ui_1768143136675.png)

### Hiển Thị Thiết Bị Trong Main Window
![Device Display in Main Window](C:/Users/minhha/.gemini/antigravity/brain/2b85eba7-1e0d-43a8-b4b9-0da87f0361b1/main_window_device_display_1768143163408.png)

## Cách Sử Dụng

### 1. Mở Dialog Chọn Thiết Bị
- Nhấn nút **"AUDIO"** (màu xanh dương) trên bảng điều khiển bên trái
- Một cửa sổ mới sẽ hiện ra với danh sách tất cả các thiết bị audio input

### 2. Chọn Thiết Bị
- Các thiết bị input có sẵn sẽ được liệt kê dưới dạng radio buttons
- Thiết bị mặc định của hệ thống sẽ được đánh dấu **[MẶC ĐỊNH]**
- Chọn thiết bị bạn muốn sử dụng bằng cách click vào radio button tương ứng

### 3. Test Thiết Bị (Tùy Chọn)
- Nhấn nút **"🎤 Test"** để kiểm tra thiết bị đã chọn
- Một cửa sổ test sẽ hiện ra và ghi âm trong 3 giây
- Bạn sẽ thấy thanh progress bar hiển thị mức độ âm thanh
- Nếu không có âm thanh, kiểm tra:
  - Thiết bị đã được kết nối chưa
  - Thiết bị có bị tắt tiếng không
  - Volume của thiết bị trong Windows

### 4. Áp Dụng
- Nhấn nút **"✓ Áp Dụng"** để lưu thiết bị đã chọn
- Nếu AUTO_TUNE_RT đang chạy:
  - Hệ thống sẽ tự động dừng detector hiện tại
  - Tạo detector mới với thiết bị vừa chọn
  - Khởi động lại detector
- Nếu AUTO_TUNE_RT chưa chạy:
  - Thiết bị sẽ được lưu và sử dụng khi bạn bật AUTO_TUNE_RT lần sau

### 5. Kiểm Tra Thiết Bị Đang Sử Dụng
- Trong khung **"🎵 DETECTED KEY"** bên phải, bạn sẽ thấy tên thiết bị đang sử dụng
- Hiển thị ở dòng dưới cùng với icon 🎤

## Các Thiết Bị Thường Dùng

### Microphone (Input từ mic)
- Dùng để phát hiện key từ giọng hát/nhạc cụ qua microphone
- Chọn thiết bị microphone của bạn trong danh sách

### Stereo Mix / Loopback (Input từ output hệ thống)
- Dùng để phát hiện key từ âm thanh đang phát trên máy tính (Cubase, YouTube, Spotify, v.v.)
- **Cách bật Stereo Mix trên Windows:**
  1. Click phải vào icon loa → Sounds
  2. Tab "Recording"
  3. Click phải vào vùng trống → "Show Disabled Devices"
  4. Click phải vào "Stereo Mix" → Enable
  5. Set as Default nếu muốn

### Virtual Audio Cable
- Nếu dùng các phần mềm như VB-Audio Virtual Cable, JACK, v.v.
- Chọn virtual device tương ứng trong danh sách

## Lưu Ý
1. **Nếu AUTO_TUNE_RT đang chạy:** Khi đổi thiết bị, hệ thống sẽ tự động restart để áp dụng thiết bị mới
2. **Default Device:** Nếu chọn "Default Input Device", hệ thống sẽ sử dụng thiết bị mặc định của Windows
3. **Độ Trễ:** Khi chuyển thiết bị, có thể có độ trễ nhỏ khi hệ thống khởi động lại detector
4. **Lỗi:** Nếu thiết bị không hoạt động, kiểm tra:
   - Driver đã cài đặt chưa
   - Thiết bị có được enable trong Windows Sound Settings không
   - Có ứng dụng nào khác đang sử dụng thiết bị không

## Workflow Khuyến Nghị

### Cho Vocal/Instrument Live
1. Chọn thiết bị Microphone của bạn
2. Test để đảm bảo âm thanh OK
3. Áp Dụng
4. Bật AUTO_TUNE_RT

### Cho Youtube/Spotify/Cubase Output
1. Enable Stereo Mix trong Windows (xem hướng dẫn trên)
2. Chọn "Stereo Mix" trong danh sách
3. Test để đảm bảo âm thanh OK
4. Áp Dụng
5. Bật AUTO_TUNE_RT
6. Phát nhạc/video và hệ thống sẽ tự động phát hiện key

## Troubleshooting

### Không thấy âm thanh khi test
- Kiểm tra volume trong Windows Sound Settings
- Đảm bảo không có app nào khác đang sử dụng thiết bị
- Restart chương trình nếu cần

### Không có Stereo Mix trong danh sách
- Xem hướng dẫn bật Stereo Mix ở trên
- Một số card âm thanh không hỗ trợ Stereo Mix
- Có thể dùng Virtual Audio Cable thay thế

### Key detection không chính xác
- Kiểm tra xem có chọn đúng thiết bị không
- Đảm bảo âm thanh input đủ lớn (dùng Test để kiểm tra)
- Tránh nhiễu nền quá lớn

## Video Demo
_(Có thể thêm link video demo nếu có)_

---
**Hậu Setup Live Studio © 2025**
