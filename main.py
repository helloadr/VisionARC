import pygame
import sys
import math
import threading
import queue
import time
from datetime import datetime
import random # For varied chatbot responses

# --- Text-to-Speech (TTS) Library ---
import pyttsx3

# Initialize Pygame
pygame.init()

# --- Screen Dimensions ---
WIDTH, HEIGHT = 1200, 900
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SAGI AI Assistant")

# Colors
BLACK = (10, 10, 10)
WHITE = (200, 200, 200)
GREY = (100, 100, 100)
LIGHT_GREY = (150, 150, 150)
CYAN = (0, 255, 255)
GREEN = (0, 200, 0) # For SAGI's responses
BLUE = (50, 50, 255) # For general information

clock = pygame.time.Clock()
FPS = 60

# Adjust CENTER for the new screen dimensions, primarily for the animation
CENTER_X_ANIMATION = WIDTH - (WIDTH // 4)
CENTER_Y = HEIGHT // 2
CENTER_ANIMATION = (CENTER_X_ANIMATION, CENTER_Y)

# --- Speech Recognition Imports and Configuration ---
import pyaudio
import numpy as np
from faster_whisper import WhisperModel
import webrtcvad
import collections

# --- Configuration for Faster Whisper ---
MODEL_SIZE = "tiny.en" # 'tiny.en', 'base.en', 'small.en', 'medium.en' etc.
DEVICE = "cpu"        # 'cpu' or 'cuda' (if you have an NVIDIA GPU)
COMPUTE_TYPE = "int8" # 'int8' for CPU (faster), 'float16' for GPU (better accuracy, higher VRAM)

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
RING_BUFFER_PADDING_MS = 500
RING_BUFFER_SIZE = int(RING_BUFFER_PADDING_MS / FRAME_DURATION_MS)

VAD_AGGRESSIVENESS = 3 # 0 (least aggressive) to 3 (most aggressive)

audio_interface = pyaudio.PyAudio()

# --- Initialize Text-to-Speech Engine (pyttsx3) ---
try:
    engine = pyttsx3.init()
    # You can change voice, rate, and volume here
    # Example to list voices and set one (uncomment to use):
    # voices = engine.getProperty('voices')
    # for voice in voices:
    #     print(f"Voice ID: {voice.id}, Name: {voice.name}, Languages: {voice.languages}")
    # engine.setProperty('voice', voices[0].id) # Try changing index for different voices
    engine.setProperty('rate', 170) # Speed of speech
    engine.setProperty('volume', 0.9) # Volume (0.0 to 1.0)
    print("pyttsx3 engine initialized.")
except Exception as e:
    print(f"Error initializing pyttsx3 engine: {e}")
    print("Ensure you have a TTS engine installed on your system (e.g., eSpeak, Microsoft SAPI5).")
    engine = None # Set to None if initialization fails

# --- TTS Function with pyttsx3 ---
def speak_thread_func(text_to_speak, speak_done_event):
    if engine:
        engine.say(text_to_speak)
        engine.runAndWait()
    speak_done_event.set() # Signal that speaking is done

# --- Speech Recognition Function (No changes here, it's robust) ---
def takeCommand_natural_convo():
    print("Listening (speak naturally)...")
    stream = None
    ring_buffer = collections.deque(maxlen=RING_BUFFER_SIZE)
    voiced_frames = []
    vad = webrtcvad.Vad(VAD_AGGRESSIVENESS)

    try:
        stream = audio_interface.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK_SIZE)
        triggered = False
        while True:
            try:
                audio_chunk = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            except IOError as e:
                if e.errno == pyaudio.paInputOverflowed:
                    continue
                else:
                    raise

            if len(audio_chunk) != CHUNK_SIZE * 2:
                continue

            is_speech = vad.is_speech(audio_chunk, RATE)

            if not triggered:
                ring_buffer.append((audio_chunk, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > 0.9 * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        voiced_frames.append(f)
                    ring_buffer.clear()
                    print("Speech detected. Recording...")
            else:
                voiced_frames.append(audio_chunk)
                ring_buffer.append((audio_chunk, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > 0.8 * ring_buffer.maxlen:
                    print("Silence detected, stopping recording.")
                    break

        stream.stop_stream()
        stream.close()

        if not voiced_frames:
            print("No speech recorded.")
            return "None"

        audio_data_bytes = b''.join(voiced_frames)
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
        print(f"An error occurred in speech recognition: {e}")
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
        return "None"

# --- Animation Drawing Functions (No changes, they use CENTER_ANIMATION) ---
def draw_arc(surface, color, center, radius, start_angle, end_angle, width=3):
    rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    rect.center = center
    pygame.draw.arc(surface, color, rect, start_angle, end_angle, width)

def draw_dotted_circle(surface, center, radius, dot_count, dot_radius, rotation_offset, color, alpha=255):
    angle_gap = 2 * math.pi / dot_count
    for i in range(dot_count):
        angle = i * angle_gap + rotation_offset
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        pygame.draw.circle(surface, (*color[:3], alpha), (int(x), int(y)), dot_radius)

def draw_glow_ring(surface, radius, alpha):
    glow_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (0, 255, 255, alpha), CENTER_ANIMATION, radius, width=2)
    surface.blit(glow_surf, (0, 0))

def draw_rotating_arcs(surface, center, base_radius, offset_rot, alpha):
    speeds = [0.015, -0.01, 0.012, -0.007]
    arc_lengths = [2.5, 1.8, 3.0, 2.2]
    arc_widths = [4, 5, 3, 6]
    arc_colors = [WHITE, GREY, LIGHT_GREY, CYAN]
    for i in range(len(speeds)):
        rot = offset_rot * speeds[i]
        start_ang = rot
        end_ang = rot + arc_lengths[i]
        col = (*arc_colors[i][:3], alpha)
        arc_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_arc(arc_surf, col, center, base_radius + i * 30, start_ang, end_ang, arc_widths[i])
        surface.blit(arc_surf, (0, 0))

def draw_random_dots(surface, center, radius, count, dot_radius, offset_rot, alpha):
    angle_gap = 2 * math.pi / count
    for i in range(count):
        angle = i * angle_gap + offset_rot
        visible = math.sin(i * 0.5 + offset_rot * 5) > 0
        if visible:
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            pygame.draw.circle(surface, (LIGHT_GREY[0], LIGHT_GREY[1], LIGHT_GREY[2], alpha), (int(x), int(y)), dot_radius)

def draw_text(surface, text, pos, font_size=16, color=WHITE, align='left'): # Default font size now 16 (smaller)
    font = pygame.font.SysFont("Consolas", font_size, bold=True)
    rendered = font.render(text, True, color)
    glow = font.render(text, True, CYAN) # Glow color remains CYAN

    rect = rendered.get_rect()
    if align == 'center':
        rect.center = pos
    elif align == 'left':
        rect.midleft = pos
    elif align == 'right':
        rect.midright = pos

    for offset in [(-1,0),(1,0),(0,-1),(0,1)]:
        glow_rect = glow.get_rect()
        if align == 'center':
            glow_rect.center = (pos[0]+offset[0], pos[1]+offset[1])
        elif align == 'left':
            glow_rect.midleft = (pos[0]+offset[0], pos[1]+offset[1])
        elif align == 'right':
            glow_rect.midright = (pos[0]+offset[0], pos[1]+offset[1])
        surface.blit(glow, glow_rect)
    surface.blit(rendered, rect)

# --- Enhanced Chatbot Logic for a more "chatty" experience ---
def get_sagi_response(query):
    query = query.lower()
    
    # Greetings
    if any(phrase in query for phrase in ["hello", "hi", "hey"]):
        return random.choice(["Hello there! It's a pleasure to assist you. How can I help today?",
                              "Hi! I'm SAGI. How can I be of service?",
                              "Greetings! What's on your mind?"])
    
    # How are you?
    elif any(phrase in query for phrase in ["how are you", "how are you doing", "what's up"]):
        return random.choice(["As an AI, I don't experience emotions, but I am fully operational and ready to serve.",
                              "I am functioning optimally, thank you for asking! How may I assist you?",
                              "All systems nominal. Ready for your commands!"])

    # Time and Date
    elif "time" in query:
        now = datetime.now()
        current_time = now.strftime("%I:%M %p")
        return f"The current time is {current_time}."
    elif any(phrase in query for phrase in ["date", "today's date"]):
        now = datetime.now()
        current_date = now.strftime("%A, %B %d, %Y")
        return f"Today is {current_date}."

    # Identity
    elif any(phrase in query for phrase in ["your name", "who are you"]):
        return random.choice(["My name is SAGI, your AI assistant. I'm here to make your life easier.",
                              "I am SAGI, designed to assist you with information and tasks.",
                              "You can call me SAGI. I'm an artificial intelligence at your service."])
    
    # Capabilities
    elif any(phrase in query for phrase in ["what can you do", "help me", "your capabilities"]):
        return random.choice([
            "I can answer your questions about time and date, offer greetings, and engage in basic conversation. What would you like to explore?",
            "My current functions include providing time and date information, simple chat, and listening for your commands. How can I be helpful?",
            "I am programmed to assist with common queries and information retrieval. Feel free to ask me anything within my scope."
        ])

    # Goodbyes
    elif any(phrase in query for phrase in ["goodbye", "bye", "exit", "quit", "see you"]):
        return random.choice(["Goodbye! It was a pleasure interacting with you. Have a great day!",
                              "Farewell! Feel free to call upon me anytime you need assistance.",
                              "See you later! I'll be here if you need me."])
    
    # Affirmatory/Thanks
    elif any(phrase in query for phrase in ["thank you", "thanks", "ok", "okay"]):
        return random.choice(["You're most welcome! I'm glad I could assist.",
                              "My pleasure!",
                              "Anytime!"])

    # Basic questions / General knowledge (very limited without external data)
    elif "weather" in query:
        return "I cannot directly check the weather at the moment, as I'm not connected to external weather services."
    elif "fact" in query or "tell me something" in query:
        return random.choice([
            "Did you know that honey never spoils?",
            "A group of owls is called a parliament.",
            "The shortest war in history lasted only 38 to 45 minutes, between Britain and Zanzibar in 1896."
        ])
    
    # Fallback / Unrecognized
    else:
        fallback_responses = [
            "I'm not quite sure how to respond to that. Could you try rephrasing your question?",
            "That's an interesting thought, but I don't have information on that yet. Is there anything else I can help with?",
            "My apologies, I didn't quite catch that, or it's beyond my current capabilities. Can you please repeat?",
            "I am constantly learning! For now, I can primarily assist with questions about time, date, and general conversation. How about asking me about the time?",
            "I am an AI designed for specific tasks. While I'd love to help with everything, some topics are still outside my current programming."
        ]
        return random.choice(fallback_responses) # Randomly select from fallback responses


# --- Speech Recognition Thread Function ---
def speech_recognition_thread(speech_to_gui_queue, gui_to_speech_queue, speaking_status_event):
    while True:
        # Wait until SAGI is done speaking before listening again
        speaking_status_event.wait() # Blocks if SAGI is speaking (event is cleared)
        speaking_status_event.clear() # Clear it right after SAGI is done, indicating it's listening

        query = takeCommand_natural_convo()
        if query != "None":
            speech_to_gui_queue.put(f"User: {query}")
            
            response = get_sagi_response(query)
            speech_to_gui_queue.put(f"SAGI: {response}")
            gui_to_speech_queue.put(response) # Send response to GUI for speaking

            if any(phrase in query for phrase in ["exit", "quit", "goodbye", "bye", "see you"]):
                speech_to_gui_queue.put("STOP_GUI") # Signal to stop the GUI
                break
        else:
            # Only update status if nothing was said and SAGI isn't speaking
            if speaking_status_event.is_set(): # If speaking_done_event is set, means SAGI isn't speaking
                speech_to_gui_queue.put("User: ...") # Indicate listening or no input
            
        time.sleep(0.1)

# --- Main GUI Loop ---
def main():
    running = True
    frame_count = 0
    rotation = 0
    appear_intervals = [60, 120, 180, 240]

    # Queues for communication
    speech_to_gui_queue = queue.Queue() # Speech thread sends recognized text/responses to GUI
    gui_to_speech_queue = queue.Queue() # GUI thread sends text to TTS engine

    # Event to synchronize listening and speaking
    # Set initially to allow listening right away
    speaking_done_event = threading.Event()
    speaking_done_event.set()

    # Start the speech recognition thread
    speech_thread = threading.Thread(target=speech_recognition_thread,
                                     args=(speech_to_gui_queue, gui_to_speech_queue, speaking_done_event),
                                     daemon=True)
    speech_thread.start()

    text_display_history = []
    MAX_HISTORY_LINES = 20 # More lines for even smaller text
    current_status = "Initializing..."

    # Initial greeting from SAGI
    now = datetime.now()
    current_date_str = now.strftime("%A, %B %d, %Y")
    current_time_str = now.strftime("%I:%M %p") # No timezone added automatically by datetime.
    
    # If the current location is Bhubaneswar, Odisha, India, and current time is 2:21 AM IST.
    # We can hardcode IST for the greeting, but a real solution needs timezone library.
    current_time_with_tz = f"{current_time_str} IST" 

    greeting_text = (
        f"Hello! The current date is {current_date_str} and the time is {current_time_with_tz}. "
        "I am SAGI, your dedicated AI assistant, ready to assist you 24/7. "
        "How may I help you today?"
    )
    text_display_history.append("SAGI: " + greeting_text)
    # Speak the greeting
    if engine: # Only speak if engine initialized
        speaking_done_event.clear() # Clear the event immediately before speaking
        greeting_speak_thread = threading.Thread(target=speak_thread_func, args=(greeting_text, speaking_done_event))
        greeting_speak_thread.start()

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- Process messages from speech recognition thread ---
        try:
            while True:
                message = speech_to_gui_queue.get_nowait()
                if message == "STOP_GUI":
                    running = False
                    break
                text_display_history.append(message)
                if len(text_display_history) > MAX_HISTORY_LINES:
                    text_display_history.pop(0) # Remove oldest line
                # Update current status based on the latest message
                if message.startswith("User:"):
                    current_status = f"User: {message[6:]}"
                elif message.startswith("SAGI:"):
                    current_status = f"SAGI: {message[6:]}"
                elif message == "User: ...":
                    current_status = "Listening..."
                else:
                    current_status = message
        except queue.Empty:
            pass

        # --- Process responses from GUI for speaking ---
        try:
            while True:
                response_to_speak = gui_to_speech_queue.get_nowait()
                if engine: # Only speak if engine initialized
                    speak_thread = threading.Thread(target=speak_thread_func, args=(response_to_speak, speaking_done_event))
                    speaking_done_event.clear() # Clear the event before starting speech
                    speak_thread.start()
        except queue.Empty:
            pass

        SCREEN.fill(BLACK)

        # --- Draw HUD elements (Animation on the right) ---
        if frame_count >= appear_intervals[0]:
            alpha = min((frame_count - appear_intervals[0]) * 5, 255)
            draw_glow_ring(SCREEN, 160, alpha)
        if frame_count >= appear_intervals[1]:
            alpha = min((frame_count - appear_intervals[1]) * 5, 255)
            draw_glow_ring(SCREEN, 200, alpha)
        if frame_count >= appear_intervals[2]:
            alpha = min((frame_count - appear_intervals[2]) * 5, 255)
            draw_glow_ring(SCREEN, 250, alpha)
        if frame_count >= appear_intervals[3]:
            alpha = min((frame_count - appear_intervals[3]) * 5, 255)
            draw_glow_ring(SCREEN, 300, alpha)

        if frame_count >= appear_intervals[0]:
            alpha = min((frame_count - appear_intervals[0]) * 5, 255)
            draw_dotted_circle(SCREEN, CENTER_ANIMATION, 320, 60, 2, rotation * 0.5, GREY, alpha)
        if frame_count >= appear_intervals[1]:
            alpha = min((frame_count - appear_intervals[1]) * 5, 255)
            draw_dotted_circle(SCREEN, CENTER_ANIMATION, 280, 40, 3, -rotation * 0.7, LIGHT_GREY, alpha)
        if frame_count >= appear_intervals[2]:
            alpha = min((frame_count - appear_intervals[2]) * 5, 255)
            draw_random_dots(SCREEN, CENTER_ANIMATION, 250, 80, 3, rotation, alpha)
        if frame_count >= appear_intervals[3]:
            alpha = min((frame_count - appear_intervals[3]) * 5, 255)
            draw_rotating_arcs(SCREEN, CENTER_ANIMATION, 200, rotation, alpha)
            inner_rings = [90, 65, 40]
            arc_lengths = [2.5, 1.8, 3.0]
            for i, rad in enumerate(inner_rings):
                start = (rotation * (1.5 - i * 0.5)) % (2 * math.pi)
                end = start + arc_lengths[i] * 1.7
                draw_arc(SCREEN, WHITE, CENTER_ANIMATION, rad, start, end, 2)

        # --- Draw Text (SAGI, conversation history, and status on the left) ---
        draw_text(SCREEN, "S. A. G. I.", (50, 50), font_size=24, color=WHITE, align='left') # Adjusted font size for title

        text_start_y = 90 # Adjusted starting Y position for conversation history
        line_height = 18 # Even smaller line height for text history
        for i, text_line in enumerate(text_display_history):
            if text_line.startswith("User:"):
                text_to_display = text_line[6:] # Remove "User: " prefix
                draw_text(SCREEN, text_to_display, (50, text_start_y + i * line_height), font_size=14, color=WHITE, align='left') # Smaller font for history
            elif text_line.startswith("SAGI:"):
                text_to_display = text_line[6:] # Remove "SAGI: " prefix
                draw_text(SCREEN, text_to_display, (70, text_start_y + i * line_height), font_size=14, color=GREEN, align='left') # Smaller font, indented, green color
            else:
                draw_text(SCREEN, text_line, (50, text_start_y + i * line_height), font_size=14, color=LIGHT_GREY, align='left')

        draw_text(SCREEN, f"Current Status: {current_status}", (50, HEIGHT - 50), font_size=16, color=CYAN, align='left') # Adjusted font size for status

        if frame_count > max(appear_intervals):
            rotation += 0.02

        frame_count += 1
        pygame.display.flip()

    pygame.quit()
    if audio_interface:
        audio_interface.terminate()
    if engine: # Cleanly stop the pyttsx3 engine
        engine.stop()
    sys.exit()

if __name__ == "__main__":
    main()