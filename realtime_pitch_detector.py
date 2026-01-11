"""
Realtime Pitch Detection Module
Uses CREPE for accurate pitch detection and key/scale analysis
Sends MIDI to Auto-Tune plugin via loopMIDI
"""

import numpy as np
import sounddevice as sd
import threading
import time
from collections import Counter
import queue
import sys

# Fix Windows console encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# Pitch detection
try:
    import crepe
    USE_CREPE = True
    print("[OK] Using CREPE (High Accuracy)")
except ImportError:
    try:
        import aubio
        USE_CREPE = False
        print("[OK] Using AUBIO (Fast, Good Accuracy)")
    except ImportError:
        raise ImportError("Please install: pip install crepe tensorflow sounddevice (or aubio)")

# MIDI Note to Key mapping
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Auto-Tune MIDI Key Mapping (C=0, C#=1, ... B=11)
AUTOTUNE_KEY_MAP = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

# Auto-Tune Scale Types (0=Major, 1=Minor)
SCALE_TYPES = {'major': 0, 'minor': 1}


class RealtimePitchDetector:
    """Detects musical key and scale in realtime from audio input"""
    
    def __init__(self, midi_callback=None, device_index=None, is_loopback=False):
        """
        Args:
            midi_callback: Function to call when key/scale detected. Signature: callback(key, scale)
            device_index: Audio device index (None = default device)
            is_loopback: If True, capture from OUTPUT device (WASAPI loopback mode)
                        If False, capture from INPUT device (normal mode)
        """
        self.midi_callback = midi_callback
        self.device_index = device_index
        self.is_loopback = is_loopback
        
        # Audio settings
        self.sample_rate = 16000  # CREPE works best at 16kHz
        self.buffer_size = 1024
        
        # Detection settings
        self.is_running = False
        self.detection_thread = None
        self.audio_queue = queue.Queue()
        
        # Analysis window (collect pitches for X seconds)
        self.analysis_window = 5.0  # seconds
        self.pitch_history = []
        self.last_detected_key = None
        self.last_detected_scale = None
        
        # Confidence threshold
        self.confidence_threshold = 0.5  # For CREPE
        
        # Initialize detector based on available library
        if USE_CREPE:
            self.init_crepe()
        else:
            self.init_aubio()
    
    def init_crepe(self):
        """Initialize CREPE-based detection"""
        print("Initializing CREPE pitch detector...")
        self.model_capacity = 'tiny'  # Options: 'tiny', 'small', 'medium', 'large', 'full'
        # 'tiny' is fastest, 'full' is most accurate but slower
        # For realtime, use 'tiny' or 'small'
    
    def init_aubio(self):
        """Initialize Aubio-based detection (fallback)"""
        print("Initializing AUBIO pitch detector...")
        self.aubio_pitch = aubio.pitch("yinfft", self.buffer_size, self.buffer_size, self.sample_rate)
        self.aubio_pitch.set_unit("Hz")
        self.aubio_pitch.set_silence(-40)
    
    def freq_to_midi_note(self, freq):
        """Convert frequency (Hz) to MIDI note number"""
        if freq <= 0:
            return None
        midi_note = 69 + 12 * np.log2(freq / 440.0)
        return int(round(midi_note))
    
    def midi_note_to_name(self, midi_note):
        """Convert MIDI note number to note name (e.g., 60 -> 'C')"""
        if midi_note is None:
            return None
        return NOTE_NAMES[midi_note % 12]
    
    def analyze_key_and_scale(self, pitches):
        """
        Analyze a collection of pitches to determine key and scale
        
        Args:
            pitches: List of MIDI note numbers
        
        Returns:
            (key, scale) tuple, e.g., ('C', 'major')
        """
        if len(pitches) < 10:  # Need enough samples
            return None, None
        
        # Count note occurrences (only the pitch class, not octave)
        note_counts = Counter([p % 12 for p in pitches])
        
        # Get the most common notes
        most_common = note_counts.most_common()
        
        if not most_common:
            return None, None
        
        # Simple key detection: most common note is likely the tonic
        tonic = most_common[0][0]
        key_name = NOTE_NAMES[tonic]
        
        # Scale detection (major vs minor)
        # Major scale intervals: 0, 2, 4, 5, 7, 9, 11 (semitones from tonic)
        # Minor scale intervals: 0, 2, 3, 5, 7, 8, 10
        
        major_pattern = {0, 2, 4, 5, 7, 9, 11}
        minor_pattern = {0, 2, 3, 5, 7, 8, 10}
        
        # Normalize notes relative to detected tonic
        relative_notes = set((note - tonic) % 12 for note, count in most_common if count > 1)
        
        # Calculate match scores
        major_score = len(relative_notes & major_pattern)
        minor_score = len(relative_notes & minor_pattern)
        
        # Determine scale
        if major_score >= minor_score:
            scale = 'major'
        else:
            scale = 'minor'
        
        return key_name, scale
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - receives audio chunks"""
        if status:
            print(f"Audio status: {status}")
        
        # Add audio chunk to queue for processing
        self.audio_queue.put(indata.copy())
    
    def audio_callback_loopback(self, indata, frames, time_info, status):
        """Callback for WASAPI loopback stream - receives raw audio bytes"""
        if status:
            print(f"Audio status: {status}")
        
        # Convert bytes to numpy array (int16 stereo)
        import numpy as np
        audio_array = np.frombuffer(indata, dtype=np.int16)
        
        # Reshape to stereo (2 channels)
        audio_stereo = audio_array.reshape(-1, 2)
        
        # Convert to mono (average left and right)
        audio_mono = audio_stereo.mean(axis=1)
        
        # Normalize to float32 [-1, 1]
        audio_float = audio_mono.astype(np.float32) / 32768.0
        
        # Reshape to match expected format (samples, channels)
        audio_formatted = audio_float.reshape(-1, 1)
        
        # Add to queue
        self.audio_queue.put(audio_formatted)
    
    def process_audio_crepe(self):
        """Process audio using CREPE"""
        accumulated_audio = []
        
        while self.is_running:
            try:
                # Get audio chunk from queue (timeout to check is_running periodically)
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Accumulate audio (CREPE needs larger chunks)
                accumulated_audio.extend(audio_chunk[:, 0])  # Mono
                
                # Process when we have enough samples (e.g., 1 second)
                min_samples = self.sample_rate * 1  # 1 second
                
                if len(accumulated_audio) >= min_samples:
                    audio_data = np.array(accumulated_audio[:min_samples])
                    
                    # Run CREPE
                    time_stamps, frequencies, confidence, activation = crepe.predict(
                        audio_data,
                        self.sample_rate,
                        model_capacity=self.model_capacity,
                        viterbi=True,
                        step_size=100  # ms between predictions
                    )
                    
                    # Filter by confidence
                    valid_freqs = frequencies[confidence > self.confidence_threshold]
                    
                    # Convert to MIDI notes
                    for freq in valid_freqs:
                        if freq > 0:
                            midi_note = self.freq_to_midi_note(freq)
                            if midi_note:
                                self.pitch_history.append(midi_note)
                    
                    # Keep only recent history
                    max_history = int(self.analysis_window * len(valid_freqs) / (len(time_stamps) + 1))
                    if len(self.pitch_history) > max_history:
                        self.pitch_history = self.pitch_history[-max_history:]
                    
                    # Analyze key/scale periodically
                    if len(self.pitch_history) >= 20:
                        key, scale = self.analyze_key_and_scale(self.pitch_history)
                        
                        if key and scale:
                            # Only send if changed
                            if key != self.last_detected_key or scale != self.last_detected_scale:
                                print(f"[DETECTED] {key} {scale}")
                                self.last_detected_key = key
                                self.last_detected_scale = scale
                                
                                # Send MIDI
                                if self.midi_callback:
                                    self.midi_callback(key, scale)
                    
                    # Remove processed samples
                    accumulated_audio = accumulated_audio[min_samples:]
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"CREPE processing error: {e}")
                import traceback
                traceback.print_exc()
    
    def process_audio_aubio(self):
        """Process audio using Aubio (fallback)"""
        while self.is_running:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Convert to float32 for aubio
                audio_float = audio_chunk[:, 0].astype(np.float32)
                
                # Detect pitch
                pitch = self.aubio_pitch(audio_float)[0]
                
                if pitch > 0:
                    midi_note = self.freq_to_midi_note(pitch)
                    if midi_note:
                        self.pitch_history.append(midi_note)
                
                # Keep only recent history
                max_history = int(self.analysis_window * self.sample_rate / self.buffer_size)
                if len(self.pitch_history) > max_history:
                    self.pitch_history = self.pitch_history[-max_history:]
                
                # Analyze periodically
                if len(self.pitch_history) >= 20:
                    key, scale = self.analyze_key_and_scale(self.pitch_history)
                    
                    if key and scale:
                        if key != self.last_detected_key or scale != self.last_detected_scale:
                            print(f"[DETECTED] {key} {scale}")
                            self.last_detected_key = key
                            self.last_detected_scale = scale
                            
                            if self.midi_callback:
                                self.midi_callback(key, scale)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Aubio processing error: {e}")
    
    def start(self):
        """Start realtime pitch detection"""
        if self.is_running:
            print("Already running!")
            return
        
        print("Starting realtime pitch detection...")
        self.is_running = True
        self.pitch_history = []
        
        # Start audio input stream
        try:
            if self.is_loopback:
                # Use soundcard library for reliable Loopback/WASAPI capture
                import soundcard as sc
                
                print(f"[MODE] Loopback (soundcard lib) (capturing from OUTPUT device: {self.device_index})")
                
                # Get the default speaker or specific speaker
                try:
                    # Input devices in soundcard include loopbacks if configured
                    # But for system output capture, we usually want sc.get_microphone(..., include_loopback=True)
                    # OR sc.default_speaker().recorder()
                    
                    # NOTE: mapping device_index from sounddevice to soundcard is tricky
                    # For now, let's try to get default speaker loopback which is what users usually want
                    
                    # Get default speaker loopback recorder
                    self.mic = sc.default_speaker()
                    print(f"[DEVICE] Default Speaker Loopback: {self.mic.name}")
                    
                    # Start recording in a separate thread because soundcard blocks or needs a context manager
                    self.stop_event = threading.Event()
                    
                    def loopback_record_thread():
                        try:
                            # Record at 44100 or 48000
                            sr = 44100
                            self.sample_rate = sr
                            
                            with self.mic.recorder(samplerate=sr) as recorder:
                                while not self.stop_event.is_set():
                                    # Record chunk
                                    data = recorder.record(numframes=1024)
                                    # data is (frames, channels) float32
                                    
                                    # Mix to mono if stereo
                                    if data.shape[1] > 1:
                                        mono_data = np.mean(data, axis=1)
                                    else:
                                        mono_data = data[:, 0]
                                        
                                    # Add to queue
                                    # Reshape to (frames, 1) for consistency
                                    self.audio_queue.put(mono_data.reshape(-1, 1))
                                    
                        except Exception as e:
                            print(f"Loopback recording error: {e}")
                            
                    self.loopback_thread = threading.Thread(target=loopback_record_thread, daemon=True)
                    self.loopback_thread.start()
                    print(f"[OK] Loopback recording started")
                    
                except Exception as e:
                    print(f"[ERROR] Soundcard loopback init failed: {e}")
                    self.is_running = False
                    return
            else:
                # Normal INPUT mode
                print(f"[MODE] Normal INPUT (device: {self.device_index or 'default'})")
                self.stream = sd.InputStream(
                    device=self.device_index,
                    channels=1,
                    samplerate=self.sample_rate,
                    blocksize=self.buffer_size,
                    callback=self.audio_callback
                )
                self.stream.start()
                print(f"[OK] Audio stream started (device: {self.device_index or 'default'})")

        except Exception as e:

            print(f"[ERROR] Failed to start audio stream: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False
            return
        
        # Start processing thread
        if USE_CREPE:
            target_func = self.process_audio_crepe
        else:
            target_func = self.process_audio_aubio
        
        self.detection_thread = threading.Thread(target=target_func, daemon=True)
        self.detection_thread.start()
        print("[OK] Detection thread started")
    
    def stop(self):
        """Stop realtime pitch detection"""
        if not self.is_running:
            return
        
        print("Stopping pitch detection...")
        self.is_running = False
        
        # Stop audio stream
        if hasattr(self, 'stream'):
            try:
                self.stream.stop()
                self.stream.close()
            except: pass
        
        # Stop soundcard loopback if running
        if hasattr(self, 'stop_event'):
            self.stop_event.set()
        
        # Wait for thread to finish
        if self.detection_thread:
            self.detection_thread.join(timeout=2.0)
            
        print("[OK] Stopped")
    
    @staticmethod
    def list_audio_devices():
        """List available audio input devices"""
        devices = sd.query_devices()
        print("\n=== Available Audio Input Devices ===")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"[{i}] {device['name']} (Channels: {device['max_input_channels']})")
        print("=====================================\n")
        return devices


# Testing
if __name__ == "__main__":
    # List devices
    RealtimePitchDetector.list_audio_devices()
    
    # Test callback
    def test_callback(key, scale):
        print(f">>> MIDI Send: {key} {scale}")
    
    # Create detector
    detector = RealtimePitchDetector(midi_callback=test_callback)
    
    print("\n[MIC] Starting pitch detection... (sing or play music)")
    print("Press Ctrl+C to stop\n")
    
    detector.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        detector.stop()
