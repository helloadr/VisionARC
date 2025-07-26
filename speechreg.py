import time
import pyaudio
import numpy as np
from faster_whisper import WhisperModel
import webrtcvad
import collections
import sys

# --- Configuration for Faster Whisper ---
MODEL_SIZE = "tiny.en" # 'tiny.en', 'base.en', 'small.en', 'medium.en' etc.
DEVICE = "cpu"        # 'cpu' or 'cuda' (if you have an NVIDIA GPU)
COMPUTE_TYPE = "int8" # 'int8' for CPU (faster), 'float16' for GPU (better accuracy, higher VRAM)

# Load the Faster Whisper model once at the start
print(f"Loading Faster Whisper model: {MODEL_SIZE} on {DEVICE} with {COMPUTE_TYPE} compute type...")
try:
    model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    print("Ensure you have `ffmpeg` installed and your `DEVICE` and `COMPUTE_TYPE` are compatible.")
    sys.exit(1) # Exit if model loading fails

# --- PyAudio & VAD Configuration ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # VAD operates best at 8kHz, 16kHz, or 32kHz. Whisper also likes 16kHz.
FRAME_DURATION_MS = 30 # Duration of audio frames for VAD (10, 20, or 30 ms)
CHUNK_SIZE = int(RATE * FRAME_DURATION_MS / 1000) # Number of samples per frame
# Number of frames to keep in a buffer to check for speech end
# This means we'll keep 0.5 seconds of audio buffer to detect trailing silence
RING_BUFFER_PADDING_MS = 500
RING_BUFFER_SIZE = int(RING_BUFFER_PADDING_MS / FRAME_DURATION_MS)

VAD_AGGRESSIVENESS = 3 # 0 (least aggressive) to 3 (most aggressive)
# Mode 0: Aggressive on speech, very tolerant of noise
# Mode 3: Most aggressive on non-speech. Useful for noisy environments to cut out noise.
# If you miss soft speech, try 0 or 1.

audio_interface = pyaudio.PyAudio()

def takeCommand_natural_convo():
    print("Listening (speak naturally)...")
    stream = None
    
    # We'll use a `collections.deque` (double-ended queue) as a ring buffer
    # to store recent audio frames and detect speech boundaries.
    ring_buffer = collections.deque(maxlen=RING_BUFFER_SIZE)
    voiced_frames = [] # Store actual speech frames

    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)
    
    try:
        stream = audio_interface.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK_SIZE)

        triggered = False # Flag to indicate if speech has started

        while True:
            try:
                # Read audio data in small chunks for real-time VAD
                audio_chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            except IOError as e:
                # Handle input buffer overflow
                if e.errno == pyaudio.paInputOverflowed:
                    # print("Input overflowed. Continuing...") # Can print for debugging
                    continue
                else:
                    raise

            # Check if chunk is valid length before processing with VAD
            # VAD expects 16-bit PCM, so each sample is 2 bytes
            if len(audio_chunk) != CHUNK_SIZE * 2: 
                # This can happen if stream.read returns less than expected, e.g., at end of input.
                # Or if the microphone is disconnecting.
                # print(f"Warning: Audio chunk size mismatch. Expected {CHUNK_SIZE*2}, got {len(audio_chunk)}")
                continue

            is_speech = vad.is_speech(audio_chunk, RATE)

            if not triggered:
                # Not yet triggered (waiting for speech to start)
                ring_buffer.append((audio_chunk, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                
                # If we have enough voiced frames in the buffer, speech has started
                if num_voiced > 0.9 * ring_buffer.maxlen: # E.g., 90% of frames are speech
                    triggered = True
                    # Add buffered frames (that led to trigger) to voiced_frames
                    for f, s in ring_buffer:
                        voiced_frames.append(f)
                    ring_buffer.clear() # Clear buffer as it's now part of actual speech
                    print("Speech detected. Recording...")
            else:
                # Already triggered (speech is ongoing)
                voiced_frames.append(audio_chunk)
                ring_buffer.append((audio_chunk, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                
                # If we have enough unvoiced frames in the buffer, speech has ended
                if num_unvoiced > 0.8 * ring_buffer.maxlen: # E.g., 80% of frames are silence
                    print("Silence detected, stopping recording.")
                    break

        stream.stop_stream()
        stream.close()

        if not voiced_frames:
            print("No speech recorded.")
            return "None"

        # Combine all recorded speech frames
        audio_data_bytes = b''.join(voiced_frames)
        # Convert to float32 for Faster Whisper
        audio_np = np.frombuffer(audio_data_bytes, dtype=np.int16).flatten().astype(np.float32) / 32768.0

        print("Transcribing (instant!)...")
        segments, info = model.transcribe(audio_np, beam_size=5)

        recognized_text = ""
        for segment in segments:
            recognized_text += segment.text + " "
        
        if recognized_text.strip():
            print(f"User said: {recognized_text.strip()}\n")
            return recognized_text.strip().lower()
        else:
            print("Could not understand the audio. Please try again (VAD detected speech, but Whisper got no text).")
            return "None"

    except Exception as e:
        print(f"An error occurred: {e}")
        # Ensure stream is closed in case of error
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
        return "None"

if __name__ == "__main__":
    print("Natural Conversation Speech recognition module started. Say 'exit' to quit.")
    print(f"Current time: {time.strftime('%I:%M:%S %p IST')}")
    while True:
        start_time = time.time()
        query = takeCommand_natural_convo()
        end_time = time.time()

        if query != "None":
            print(f"Processed query: {query}")
            print(f"Total time for turn: {end_time - start_time:.3f} seconds\n")
            
        if query == "exit":
            print("Exiting...")
            break

    audio_interface.terminate() # Clean up PyAudio resources on exit