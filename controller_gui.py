import customtkinter as ctk
import rtmidi
import threading
import time
import os
import json
import ctypes
import uuid
import hashlib
import datetime
import tkinter.messagebox

# Automation Libs
try:
    import pyautogui
    import pygetwindow as gw
except ImportError:
    print("Warning: Automation libs not found. Auto-Key feature disabled.")

# Realtime Pitch Detection
try:
    from realtime_pitch_detector import RealtimePitchDetector
    PITCH_DETECTOR_AVAILABLE = True
except ImportError:
    print("Warning: Realtime pitch detector not available. Install: pip install crepe tensorflow sounddevice")
    PITCH_DETECTOR_AVAILABLE = False

MIDI_PORT_CHECK = "loopMIDI"
CHANNEL = 0 

CC_MAP = {
    "MUSIC_VOL": 21, "MIC_VOL": 20, "REVERB_LONG": 22, "REVERB_SHORT": 23, "TUNE": 27,
    "DELAY": 26,
    "MUTE_MUSIC": 25, "MUTE_MIC": 24, "TONE_VAL_SEND": 28,  # Single CC for Value
    "DO_TONE": 30, "LAY_TONE": 31, "VANG_FX": 32, "FIX_MEO": 36,
    "AUTO_TUNE_RT": 37  # Realtime Auto-Tune Detection
    # REMOVED: LOFI (33), REMIX (34), SAVE (35) - Internal Python Logic Only
    # TONE_DOWN (29) removed, we only use CC 28 for value
}

class MidiHandler:
    def __init__(self):
        self.midiout = rtmidi.MidiOut()
        self.port_name = None
        self.is_connected = False
        self.last_sent = {}
        self.connect()

    def connect(self):
        ports = self.midiout.get_ports()
        for i, name in enumerate(ports):
            if MIDI_PORT_CHECK in name:
                self.midiout.open_port(i)
                self.port_name = name
                self.is_connected = True
                print(f"Connected to {name}")
                return True
        print(f"{MIDI_PORT_CHECK} not found!")
        return False

    def send_cc(self, cc, value):
        if self.is_connected:
            val = max(0, min(127, int(value)))
            if self.last_sent.get(cc) == val:
                return
            self.last_sent[cc] = val
            self.midiout.send_message([0xB0 | CHANNEL, cc, val])
            print(f"MIDI Send: CC {cc} -> Value {val}")

midi = MidiHandler()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Dark")
        self.col_bg = "#1a1a1a"
        self.col_btn_purple = "#6a4c9c"
        self.col_btn_green = "#4caf50"
        self.col_btn_red = "#d32f2f"
        self.col_btn_orange = "#f57c00"
        self.col_btn_yellow = "#fbc02d"
        self.col_text_green = "#4caf50"
        self.col_text_yellow = "#fbc02d"
        
        # LICENSE CHECK
        if self.validate_license():
            self.init_main_app()
        else:
            self.init_activation_screen()

    # --- LICENSE LOGIC ---
    def get_hwid(self):
        return str(uuid.getnode())

    def get_expected_key(self):
        return "HAU_SETUP_STUDIO_2025"

    def generate_token(self):
        raw = f"{self.get_expected_key()}|{self.get_hwid()}"
        return hashlib.md5(raw.encode()).hexdigest()

    def validate_license(self):
        if not os.path.exists("license.dat"): return False
        try:
            with open("license.dat", "r") as f:
                saved_token = f.read().strip()
            return saved_token == self.generate_token()
        except: return False

    def init_activation_screen(self):
        self.title("KÍCH HOẠT BẢN QUYỀN")
        self.geometry("400x250")
        self.resizable(False, False)
        
        frame = ctk.CTkFrame(self, fg_color=self.col_bg)
        frame.pack(expand=True, fill="both")
        
        ctk.CTkLabel(frame, text="NHẬP KEY KÍCH HOẠT", font=("Arial", 18, "bold"), text_color="#4caf50").pack(pady=(40, 20))
        
        self.entry_key = ctk.CTkEntry(frame, placeholder_text="Nhập Key (Ví dụ: HAU_SETUP...)", width=300, justify="center", show="*")
        self.entry_key.pack(pady=10)
        
        ctk.CTkButton(frame, text="KÍCH HOẠT", fg_color="#4caf50", width=120, height=35, command=self.activate_license).pack(pady=20)
        
        ctk.CTkLabel(frame, text="Hậu Setup Live Studio © 2025", font=("Arial", 10), text_color="#555").pack(side="bottom", pady=10)

    def activate_license(self):
        user_key = self.entry_key.get().strip()
        expected = self.get_expected_key()
        
        if user_key == expected:
            try:
                token = self.generate_token()
                with open("license.dat", "w") as f:
                    f.write(token)
                
                tkinter.messagebox.showinfo("Thành công", "Kích hoạt bản quyền theo máy thành công!")
                
                for widget in self.winfo_children():
                    widget.destroy()
                self.init_main_app()
                
            except Exception as e:
                tkinter.messagebox.showerror("Lỗi", f"Không thể lưu license: {e}")
        else:
            tkinter.messagebox.showerror("Lỗi", "Key không đúng!")


    # --- MAIN APP LOGIC ---
    def init_main_app(self):
        self.title("BẢNG ĐIỀU KHIỂN TIẾNG VIỆT - Hậu Setup Live Studio")
        self.geometry("850x350")
        self.resizable(False, False)
        self.configure(fg_color=self.col_bg)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=1)

        self.btn_widgets = {} 
        self.btn_states = {}  
        self.btn_colors = {}
        
        self.slider_widgets = {}
        self.slider_labels = {}
        
        # Realtime Pitch Detector
        self.pitch_detector = None
        self.is_auto_tune_running = False
        self.audio_device_index = None  # Will be set by user in settings
        self.audio_device_name = "Default Device"  # Display name for current device
        self.is_loopback = False  # True if capturing from OUTPUT device
        
        if PITCH_DETECTOR_AVAILABLE:
            # Initially use default device (None)
            # User can change via AUDIO button
            self.pitch_detector = RealtimePitchDetector(
                midi_callback=self.on_pitch_detected,
                device_index=self.audio_device_index,
                is_loopback=self.is_loopback
            )
        
        # Detected key/scale display
        self.detected_key = None
        self.detected_scale = None

        self.setup_left_panel()
        self.setup_center_panel()
        self.setup_right_panel()
        
        self.load_settings()

    def setup_left_panel(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)
        
        btns = [
            ("DÒ TONE", self.col_btn_purple, "DO_TONE"),
            ("AUTO RT", self.col_btn_purple, "AUTO_TUNE_RT"),  # Realtime Auto-Tune
            ("NHẠC", self.col_btn_green, "MUTE_MUSIC"),
            ("MIC", self.col_btn_green, "MUTE_MIC"),
            ("VANG", self.col_btn_red, "VANG_FX"),
            ("AUDIO", "#2196f3", "AUDIO_SETTINGS"),  # Audio Input Settings
            ("REMIX", self.col_btn_red, "REMIX"),
            ("LƯU", self.col_btn_yellow, "SAVE")
        ]

        for i, (text, color, cc_key) in enumerate(btns):
            self.btn_states[cc_key] = False
            self.btn_colors[cc_key] = color
            
            cmd = lambda k=cc_key: self.on_btn_toggle(k)
            
            if cc_key == "DO_TONE":
                cmd = self.start_autokey
            elif cc_key == "AUTO_TUNE_RT":
                cmd = self.toggle_auto_tune_rt
            elif cc_key == "AUDIO_SETTINGS":
                cmd = self.show_audio_settings
            elif cc_key == "SAVE":
                cmd = self.save_settings

            btn = ctk.CTkButton(
                frame, text=text, fg_color=color, 
                font=("Arial", 11, "bold"), height=28, width=75,
                hover_color=self.adjust_color(color),
                command=cmd
            )
            self.btn_widgets[cc_key] = btn
            
            r = i // 2
            c = i % 2
            btn.grid(row=r, column=c, padx=3, pady=4, sticky="ew")

    def setup_center_panel(self):
        frame = ctk.CTkFrame(self, fg_color="transparent", border_width=1, border_color="#333")
        frame.grid(row=0, column=1, sticky="nsew", padx=2, pady=10)

        sliders = [
            ("ÂM NHẠC", "MUSIC_VOL", self.col_btn_green),
            ("ÂM MIC", "MIC_VOL", self.col_btn_orange),
            ("VANG DÀI", "REVERB_LONG", "#888"),
            ("VANG NGẮN", "REVERB_SHORT", "#888"),
            ("Delay", "DELAY", "#888"),
        ]

        for i, (label_text, cc_key, color) in enumerate(sliders):
            lbl = ctk.CTkLabel(frame, text=label_text, font=("Arial", 10, "bold"), text_color=self.col_btn_yellow, width=70, anchor="w")
            lbl.grid(row=i, column=0, padx=5, pady=5)
            
            slider = ctk.CTkSlider(
                frame, from_=0, to=127, number_of_steps=127, 
                progress_color=color, height=16,
                command=lambda val, k=cc_key: self.on_slider_change(val, k)
            )
            slider.set(100)
            slider.grid(row=i, column=1, padx=2, pady=5, sticky="ew")
            self.slider_widgets[cc_key] = slider 
            
            val_lbl = ctk.CTkLabel(frame, text="79%", font=("Arial", 10), width=35)
            val_lbl.grid(row=i, column=2, padx=2, pady=5)
            self.slider_labels[cc_key] = val_lbl

        bottom_frame = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_frame.grid(row=len(sliders), column=0, columnspan=3, pady=5)
        
        opt = ctk.CTkOptionMenu(bottom_frame, values=["NHẠC TRẺ", "BOLERO", "REMIX"], fg_color="#1f77b4", height=24, font=("Arial", 11))
        opt.pack(side="left", padx=5)
        
        btn_fix = ctk.CTkButton(bottom_frame, text="Fix Méo", fg_color="#d32f2f", width=60, height=24, font=("Arial", 11), command=lambda: self.on_btn_click("FIX_MEO"))
        btn_fix.pack(side="left", padx=5)
        self.btn_widgets["FIX_MEO"] = btn_fix
        self.btn_colors["FIX_MEO"] = "#d32f2f"

    def setup_right_panel(self):
        frame = ctk.CTkFrame(self, fg_color="#101010", corner_radius=10, border_color="#444", border_width=2)
        frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=10)
        
        ctk.CTkLabel(frame, text="TONE / TUNE", font=("Arial", 12, "bold"), text_color="white").pack(pady=5)
        
        tone_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tone_frame.pack(pady=2)
        
        ctk.CTkButton(tone_frame, text="TONE", fg_color=self.col_btn_green, width=50, height=24, font=("Arial", 11)).pack(side="left", padx=3)
        btn_down = ctk.CTkButton(tone_frame, text="-", width=30, height=24, fg_color="#333", command=lambda: self.on_btn_click("TONE_DOWN"))
        btn_down.pack(side="left", padx=1)
        self.btn_widgets["TONE_DOWN"] = btn_down
        self.btn_colors["TONE_DOWN"] = "#333"
        
        self.tone_val = ctk.CTkLabel(tone_frame, text="0.0", font=("Arial", 14, "bold"), width=40, text_color="#00e676")
        self.tone_val.pack(side="left", padx=3)
        
        btn_up = ctk.CTkButton(tone_frame, text="+", width=30, height=24, fg_color="#333", command=lambda: self.on_btn_click("TONE_UP"))
        btn_up.pack(side="left", padx=1)
        self.btn_widgets["TONE_UP"] = btn_up
        self.btn_colors["TONE_UP"] = "#333"

        tune_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tune_frame.pack(pady=10, fill="x", padx=5)
        
        ctk.CTkButton(tune_frame, text="TUNE", fg_color=self.col_btn_green, width=50, height=24, font=("Arial", 11)).pack(side="left")
        
        self.tune_slider = ctk.CTkSlider(tune_frame, from_=0, to=127, progress_color="#d32f2f", height=16)
        self.tune_slider.pack(side="left", padx=5, fill="x", expand=True)
        self.tune_slider.configure(command=lambda v: self.on_slider_change(v, "TUNE"))
        self.slider_widgets["TUNE"] = self.tune_slider
        
        # === REALTIME KEY DETECTION DISPLAY ===
        detect_frame = ctk.CTkFrame(frame, fg_color="#1a1a1a", corner_radius=8, border_color="#00e676", border_width=1)
        detect_frame.pack(pady=10, padx=5, fill="x")
        
        ctk.CTkLabel(
            detect_frame, 
            text="🎵 DETECTED KEY", 
            font=("Arial", 10, "bold"), 
            text_color="#00e676"
        ).pack(pady=(5, 2))
        
        # Key/Scale display
        self.key_display = ctk.CTkLabel(
            detect_frame,
            text="---",
            font=("Arial", 20, "bold"),
            text_color="#ffffff",
            width=120
        )
        self.key_display.pack(pady=2)
        
        self.scale_display = ctk.CTkLabel(
            detect_frame,
            text="Waiting...",
            font=("Arial", 11),
            text_color="#888888",
            width=120
        )
        self.scale_display.pack(pady=(0, 2))
        
        # Audio device display
        self.audio_device_display = ctk.CTkLabel(
            detect_frame,
            text=f"🎤 {self.audio_device_name}",
            font=("Arial", 9),
            text_color="#2196f3",
            width=120,
            wraplength=110
        )
        self.audio_device_display.pack(pady=(0, 5))
        
        ctk.CTkLabel(frame, text="BẢNG ĐIỀU KHIỂN TIẾNG VIỆT", font=("Arial", 11, "bold"), text_color=self.col_text_yellow).pack(side="bottom", pady=2)
        ctk.CTkLabel(frame, text="Hậu Setup Live Studio", font=("Arial", 10, "bold"), text_color=self.col_text_green).pack(side="bottom", pady=2)

    def adjust_color(self, hex_color, factor=0.8):
        return hex_color

    def on_btn_toggle(self, key):
        cur_state = self.btn_states.get(key, False)
        new_state = not cur_state
        self.btn_states[key] = new_state
        
        btn = self.btn_widgets.get(key)
        orig_color = self.btn_colors.get(key)
        
        if btn:
            if new_state: # ON
                btn.configure(fg_color="#F0F0F0", text_color="#000000")
            else: # OFF
                btn.configure(fg_color=orig_color, text_color="#FFFFFF")
                
            cc = CC_MAP.get(key)
            if cc:
                midi.send_cc(cc, 127)
                self.after(50, lambda: midi.send_cc(cc, 0))

    def on_btn_click(self, key):
        # Default behavior: Flash but NO MIDI for TONE_UP/TONE_DOWN here
        if key not in ["TONE_UP", "TONE_DOWN"]:
            cc = CC_MAP.get(key)
            if cc:
                midi.send_cc(cc, 127)
                self.after(100, lambda: midi.send_cc(cc, 0))
            
        btn = self.btn_widgets.get(key)
        if btn:
            orig = self.btn_colors.get(key, "#333")
            btn.configure(fg_color="#ffffff", text_color="black")
            self.after(150, lambda: btn.configure(fg_color=orig, text_color="white"))

        if key == "TONE_UP":
            try:
                cur = float(self.tone_val.cget("text"))
                new_val = min(12.0, cur + 1.0)
                self.tone_val.configure(text=f"{new_val:.1f}")
                
                # Send VALUE to CC 28
                # Map -12..12 -> 0..127
                midi_val = int(64 + new_val * (63.5/12)) # 0 -> 64, 12 -> 127.5, -12 -> 0.5
                midi_val = max(0, min(127, midi_val))
                midi.send_cc(CC_MAP.get("TONE_VAL_SEND"), midi_val)
            except: pass
        elif key == "TONE_DOWN":
            try:
                cur = float(self.tone_val.cget("text"))
                new_val = max(-12.0, cur - 1.0)
                self.tone_val.configure(text=f"{new_val:.1f}")
                
                # Send VALUE to CC 28
                midi_val = int(64 + new_val * (63.5/12))
                midi_val = max(0, min(127, midi_val))
                midi.send_cc(CC_MAP.get("TONE_VAL_SEND"), midi_val)
            except: pass

    def on_slider_change(self, value, key):
        cc = CC_MAP.get(key)
        if cc:
            midi.send_cc(cc, value)
        
        if key in self.slider_labels:
            percent = int((value / 127) * 100)
            self.slider_labels[key].configure(text=f"{percent}%")

    def save_settings(self):
        # Trigger visual feedback (Flash) but NO MIDI
        btn = self.btn_widgets.get("SAVE")
        if btn:
            orig = self.btn_colors.get("SAVE", "#333")
            btn.configure(fg_color="#ffffff", text_color="black")
            self.after(150, lambda: btn.configure(fg_color=orig, text_color="white"))
        
        data = {
            "toggles": self.btn_states,
            "sliders": {k: v.get() for k, v in self.slider_widgets.items()}
        }
        try:
            with open("config.json", "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print("Đã lưu cấu hình vào config.json")
        except Exception as e:
            print(f"Lỗi lưu file: {e}")

    def load_settings(self):
        if not os.path.exists("config.json"): return
        try:
            print("Đang tải cấu hình...")
            with open("config.json", "r", encoding='utf-8') as f:
                data = json.load(f)
            
            sliders_data = data.get("sliders", {})
            for k, v in sliders_data.items():
                if k in self.slider_widgets:
                    self.slider_widgets[k].set(v)
                    self.on_slider_change(v, k)

            toggles_data = data.get("toggles", {})
            for k, v in toggles_data.items():
                if k in self.btn_widgets and k not in ["DO_TONE", "SAVE"]:
                    if self.btn_states.get(k, False) != v:
                         self.on_btn_toggle(k)
        except Exception as e:
            print(f"Lỗi load config: {e}")

    def start_autokey(self):
        print("Bắt đầu Dò Tone...")
        # Gửi CC ON (127)
        cc = CC_MAP.get("DO_TONE")
        if cc: midi.send_cc(cc, 127)
        
        btn = self.btn_widgets.get("DO_TONE")
        if btn: btn.configure(text="ĐANG DÒ...", fg_color="#F0F0F0", text_color="black")
        
        threading.Thread(target=self.auto_detect_tone_thread, daemon=True).start()

    def auto_detect_tone_thread(self):
        try:
            original_pos = pyautogui.position()

            print("[1/3] Focus Cubase...")
            cubase_wins = gw.getWindowsWithTitle('Cubase')
            if not cubase_wins:
                print("❌ Không thấy Cubase! Hãy mở Cubase.")
                return
            
            main_win = cubase_wins[0]
            try:
                if main_win.isMinimized: main_win.restore()
                main_win.activate()
                import ctypes
                hwnd = main_win._hWnd
                ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
            except Exception as e:
                print(f"Warning Focus: {e}")
            
            time.sleep(1.0) 

            target_win = None
            for t in gw.getAllTitles():
                if "Auto-Key" in t:
                    wins = gw.getWindowsWithTitle(t)
                    if wins and wins[0].width > 50: 
                        target_win = wins[0]
                        break
            
            if not target_win:
                print("❌ Không thấy Plugin Auto-Key! Hãy mở Plugin lên màn hình.")
                return

            try: target_win.activate()
            except: pass
            time.sleep(0.5)

            cx = target_win.left + int(target_win.width / 2)
            cy = target_win.top + int(target_win.height * 0.32)
            sy = target_win.top + int(target_win.height * 0.62)

            print(f"Click Listen ({cx}, {cy})...")
            pyautogui.click(cx, cy)
            
            print("Đang nghe (15s)...")
            time.sleep(15)

            print(f"Click Send ({cx}, {sy})...")
            pyautogui.click(cx, sy)
            
            pyautogui.moveTo(original_pos)
            print("✅ Xong quy trình!")

        except Exception as e:
            print(f"Lỗi: {e}")
        finally:
            cc = CC_MAP.get("DO_TONE")
            if cc: midi.send_cc(cc, 0)
            
            btn = self.btn_widgets.get("DO_TONE")
            orig_col = self.btn_colors.get("DO_TONE", self.col_btn_purple)
            if btn: btn.configure(text="DÒ TONE", fg_color=orig_col, text_color="white")
    
    def show_audio_settings(self):
        """Show dialog to select audio input/output device"""
        import sounddevice as sd
        
        # Create popup window
        dialog = ctk.CTkToplevel(self)
        dialog.title("Chọn Nguồn Audio cho AUTO_TUNE_RT")
        dialog.geometry("700x550")
        dialog.resizable(False, False)
        dialog.configure(fg_color=self.col_bg)
        
        # Make it modal
        dialog.grab_set()
        dialog.focus()
        
        # Header
        header_frame = ctk.CTkFrame(dialog, fg_color="#2a2a2a")
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text="� Chọn Nguồn Audio cho AUTO_TUNE_RT",
            font=("Arial", 16, "bold"),
            text_color="#00e676"
        ).pack(pady=5)
        
        mode_text = "LOOPBACK (Bắt Output)" if self.is_loopback else "INPUT (Mic)"
        ctk.CTkLabel(
            header_frame,
            text=f"Hiện tại: {self.audio_device_name} [{mode_text}]",
            font=("Arial", 10),
            text_color="#fbc02d"
        ).pack(pady=(0, 5))
        
        # INFO BOX
        info_frame = ctk.CTkFrame(dialog, fg_color="#1a3a1a", border_color="#4caf50", border_width=1)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text="💡 TIP: Chọn OUTPUT (Speakers/Headphones) để bắt nhạc từ Cubase/YouTube!",
            font=("Arial", 9),
            text_color="#4caf50",
            wraplength=650
        ).pack(pady=5)
        
        # Get all devices
        devices = sd.query_devices()
        
        # Separate INPUT and OUTPUT devices
        input_devices = []
        output_devices = []
        
        # Process devices
        for i, device in enumerate(devices):
            device_name = device['name']
            
            # INPUT devices
            if device['max_input_channels'] > 0:
                if i == sd.default.device[0]:
                    device_name_input = device_name + " [MẶC ĐỊNH]"
                else:
                    device_name_input = device_name
                input_devices.append((i, False, device_name_input))  # (index, is_loopback, name)
            
            # OUTPUT devices  
            if device['max_output_channels'] > 0:
                if i == sd.default.device[1]:
                    device_name_output = device_name + " [MẶC ĐỊNH]"
                else:
                    device_name_output = device_name
                output_devices.append((i, True, device_name_output))  # (index, is_loopback, name)
        
        # Scrollable frame for devices
        scroll_frame = ctk.CTkScrollableFrame(
            dialog,
            fg_color="#101010",
            height=320
        )
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Variable to store selected device (value = (device_index, is_loopback))
        # We use a string to encode both values: "index_loopback"
        current_value = f"{self.audio_device_index if self.audio_device_index is not None else -1}_{1 if self.is_loopback else 0}"
        selected_device = ctk.StringVar(value=current_value)
        
        # === OUTPUT DEVICES SECTION ===
        output_label_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2a2a")
        output_label_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            output_label_frame,
            text="🔊 OUTPUT DEVICES (Speakers/Headphones) - Để bắt nhạc từ Cubase/Browser",
            font=("Arial", 11, "bold"),
            text_color="#ff9800",
            anchor="w"
        ).pack(fill="x", padx=10, pady=5)
        
        for device_idx, is_loopback, device_name in output_devices:
            radio_value = f"{device_idx}_1"  # is_loopback = True = 1
            
            radio_frame = ctk.CTkFrame(scroll_frame, fg_color="#1a1a1a", corner_radius=5)
            radio_frame.pack(fill="x", padx=5, pady=2)
            
            radio = ctk.CTkRadioButton(
                radio_frame,
                text=f"🔊 {device_name}",
                variable=selected_device,
                value=radio_value,
                font=("Arial", 10),
                text_color="#ffffff",
                fg_color="#ff9800",
                hover_color="#ffb74d"
            )
            radio.pack(anchor="w", padx=10, pady=6)
        
        # Separator
        ctk.CTkFrame(scroll_frame, height=2, fg_color="#444").pack(fill="x", padx=20, pady=10)
        
        # === INPUT DEVICES SECTION ===
        input_label_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2a2a")
        input_label_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            input_label_frame,
            text="🎤 INPUT DEVICES (Microphone/Line In) - Để bắt giọng hát/nhạc cụ",
            font=("Arial", 11, "bold"),
            text_color="#2196f3",
            anchor="w"
        ).pack(fill="x", padx=10, pady=5)
        
        for device_idx, is_loopback, device_name in input_devices:
            radio_value = f"{device_idx}_0"  # is_loopback = False = 0
            
            radio_frame = ctk.CTkFrame(scroll_frame, fg_color="#1a1a1a", corner_radius=5)
            radio_frame.pack(fill="x", padx=5, pady=2)
            
            radio = ctk.CTkRadioButton(
                radio_frame,
                text=f"🎤 {device_name}",
                variable=selected_device,
                value=radio_value,
                font=("Arial", 10),
                text_color="#ffffff",
                fg_color="#2196f3",
                hover_color="#42a5f5"
            )
            radio.pack(anchor="w", padx=10, pady=6)
        
        # Button frame
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        def apply_selection():
            """Apply the selected device"""
            selected_value = selected_device.get()
            
            # Parse "index_loopback"
            parts = selected_value.split("_")
            device_idx = int(parts[0])
            is_loopback = bool(int(parts[1]))
            
            # Store device index
            self.audio_device_index = None if device_idx == -1 else device_idx
            self.is_loopback = is_loopback
            
            # Find device name
            all_devices = output_devices if is_loopback else input_devices
            for idx, loop, name in all_devices:
                if idx == device_idx:
                    self.audio_device_name = name.replace(" [MẶC ĐỊNH]", "")
                    break
            
            # Add mode prefix
            mode_prefix = "[OUTPUT] " if is_loopback else "[INPUT] "
            display_name = mode_prefix + self.audio_device_name
            
            # If auto-tune is running, restart with new device
            if self.is_auto_tune_running and PITCH_DETECTOR_AVAILABLE:
                print(f"🔄 Đang chuyển sang: {display_name}")
                
                # Stop current detector
                self.pitch_detector.stop()
                
                # Create new detector with selected device
                self.pitch_detector = RealtimePitchDetector(
                    midi_callback=self.on_pitch_detected,
                    device_index=self.audio_device_index,
                    is_loopback=self.is_loopback
                )
                
                # Start new detector
                self.pitch_detector.start()
                print(f"✅ Đã chuyển sang: {display_name}")
            else:
                # Just update the detector instance for next time
                if PITCH_DETECTOR_AVAILABLE:
                    self.pitch_detector = RealtimePitchDetector(
                        midi_callback=self.on_pitch_detected,
                        device_index=self.audio_device_index,
                        is_loopback=self.is_loopback
                    )
            
            # Update audio device display label
            if hasattr(self, 'audio_device_display'):
                self.audio_device_display.configure(text=f"{'🔊' if is_loopback else '🎤'} {self.audio_device_name}")
            
            mode_text = "LOOPBACK (Output)" if is_loopback else "INPUT (Mic)"
            tkinter.messagebox.showinfo(
                "Thành công",
                f"✓ Đã chọn: {self.audio_device_name}\n"
                f"✓ Mode: {mode_text}\n"
                f"✓ Index: {self.audio_device_index if self.audio_device_index is not None else 'Default'}\n\n"
                f"{'📢 Bây giờ sẽ bắt âm thanh từ OUTPUT (Loa/Tai nghe)!' if is_loopback else '🎤 Bây giờ sẽ bắt âm thanh từ INPUT (Microphone)!'}"
            )
            
            dialog.destroy()
        
        # Buttons
        ctk.CTkButton(
            btn_frame,
            text="✓ ÁP DỤNG",
            fg_color="#4caf50",
            hover_color="#66bb6a",
            font=("Arial", 13, "bold"),
            height=38,
            width=140,
            command=apply_selection
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="✕ HỦY",
            fg_color="#666",
            hover_color="#888",
            font=("Arial", 13, "bold"),
            height=38,
            width=140,
            command=dialog.destroy
        ).pack(side="right", padx=5)
    
    def toggle_auto_tune_rt(self):
        """Toggle realtime auto-tune detection"""
        if not PITCH_DETECTOR_AVAILABLE or not self.pitch_detector:
            tkinter.messagebox.showerror(
                "Lỗi", 
                "Realtime Pitch Detector không khả dụng!\n\n"
                "Cài đặt: pip install crepe tensorflow sounddevice"
            )
            return
        
        if self.is_auto_tune_running:
            # Stop detection
            print("Stopping realtime auto-tune...")
            self.pitch_detector.stop()
            self.is_auto_tune_running = False
            
            # Update button
            btn = self.btn_widgets.get("AUTO_TUNE_RT")
            if btn:
                btn.configure(
                    text="AUTO RT", 
                    fg_color=self.col_btn_purple, 
                    text_color="white"
                )
            
            # Reset display
            if hasattr(self, 'key_display') and hasattr(self, 'scale_display'):
                self.key_display.configure(text="---", text_color="#888888")
                self.scale_display.configure(text="Waiting...", text_color="#888888")
            
            # Send MIDI OFF
            cc = CC_MAP.get("AUTO_TUNE_RT")
            if cc:
                midi.send_cc(cc, 0)
        else:
            # Start detection
            print("🎤 Starting realtime auto-tune detection...")
            self.pitch_detector.start()
            self.is_auto_tune_running = True
            
            # Update button
            btn = self.btn_widgets.get("AUTO_TUNE_RT")
            if btn:
                btn.configure(
                    text="ĐANG DÒ RT", 
                    fg_color="#00e676", 
                    text_color="black"
                )
            
            # Send MIDI ON
            cc = CC_MAP.get("AUTO_TUNE_RT")
            if cc:
                midi.send_cc(cc, 127)
    
    def on_pitch_detected(self, key, scale):
        """
        Callback when pitch detector detects a key/scale
        Sends MIDI to Auto-Tune plugin
        
        Args:
            key: Musical key (e.g., 'C', 'D#', 'A')
            scale: Scale type ('major' or 'minor')
        """
        print(f"🎵 Detected: {key} {scale} -> Sending to Auto-Tune...")
        
        # Update GUI display (thread-safe)
        self.detected_key = key
        self.detected_scale = scale
        
        # Update labels (use after() for thread-safety)
        self.after(0, self.update_key_display, key, scale)
        
        # Auto-Tune accepts MIDI notes to set the key
        # We'll send MIDI note-on messages
        # MIDI Note format: C4 = 60, C#4 = 61, etc.
        
        # Map key to MIDI note (using octave 4 as reference)
        key_to_midi = {
            'C': 60, 'C#': 61, 'Db': 61,
            'D': 62, 'D#': 63, 'Eb': 63,
            'E': 64, 
            'F': 65, 'F#': 66, 'Gb': 66,
            'G': 67, 'G#': 68, 'Ab': 68,
            'A': 69, 'A#': 70, 'Bb': 70,
            'B': 71
        }
        
        midi_note = key_to_midi.get(key)
        if midi_note is None:
            print(f"⚠️ Unknown key: {key}")
            return
        
        # For Auto-Tune, we can:
        # 1. Send MIDI note to set the key
        # 2. Use velocity to indicate major (127) vs minor (64)
        velocity = 127 if scale == 'major' else 64
        
        # Send Note ON
        try:
            if midi.is_connected:
                # Note ON: 0x90 | channel, note, velocity
                midi.midiout.send_message([0x90 | CHANNEL, midi_note, velocity])
                time.sleep(0.05)  # Short delay
                # Note OFF: 0x80 | channel, note, 0
                midi.midiout.send_message([0x80 | CHANNEL, midi_note, 0])
                print(f"✓ Sent MIDI: Note {midi_note} ({key}), Velocity {velocity} ({scale})")
        except Exception as e:
            print(f"❌ MIDI send error: {e}")
    
    def update_key_display(self, key, scale):
        """
        Update GUI to show detected key and scale
        Must be called from main GUI thread
        """
        if hasattr(self, 'key_display') and hasattr(self, 'scale_display'):
            # Update key display
            self.key_display.configure(
                text=f"{key}",
                text_color="#00e676"  # Bright green for detected key
            )
            
            # Update scale display with emoji
            scale_text = "Major ⬆" if scale == "major" else "Minor ⬇"
            scale_color = "#fbc02d" if scale == "major" else "#2196f3"  # Yellow for major, blue for minor
            
            self.scale_display.configure(
                text=scale_text,
                text_color=scale_color
            )
            
            # Flash effect (optional)
            self.after(100, lambda: self.key_display.configure(text_color="#ffffff"))

    def on_closing(self):
        # Stop pitch detector if running
        if hasattr(self, 'pitch_detector') and self.pitch_detector and self.is_auto_tune_running:
            print("Stopping pitch detector...")
            self.pitch_detector.stop()
        
        self.destroy()
        os._exit(0)

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
