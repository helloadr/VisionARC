# file: jarvis_gui_voice_assistant.py (pygame animated intro)

import pygame
import threading
import time
import speech_recognition as sr
import math
import random
import tkinter as tk
from tkinter import messagebox

# -----------------------------
# Pygame Initialization Animation (Startup Style)
# -----------------------------
def show_intro_animation():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("JARVIS Initializing")
    clock = pygame.time.Clock()
    center = (300, 200)
    running = True
    start_time = time.time()

    def draw_ring(surface, radius, width, alpha):
        ring_surf = pygame.Surface((600, 400), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (0, 255, 170, alpha), center, radius, width)
        surface.blit(ring_surf, (0, 0))

    while running:
        screen.fill((0, 0, 0))
        t = time.time() - start_time
        for i in range(4):
            phase = (t * 2 + i * 0.8) % 4
            radius = int(40 + phase * 30)
            alpha = max(0, 255 - int(phase * 64))
            draw_ring(screen, radius, 2, alpha)

        pygame.display.flip()
        clock.tick(60)

        if t > 4:  # stop after 4 seconds
            running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

    pygame.quit()


# -----------------------------
# Voice Assistant Class
# -----------------------------
class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS Voice Assistant")
        self.root.geometry("600x500")
        self.root.configure(bg="#000000")

        self.status_label = tk.Label(root, text="JARVIS Ready. Press Start.", font=("Consolas", 16), fg="white", bg="#000000")
        self.status_label.pack(pady=10)

        self.output_text = tk.Text(root, height=5, font=("Consolas", 12), fg="#00FFAA", bg="#111111", wrap="word")
        self.output_text.pack(pady=10, padx=20, fill="x")
        self.output_text.insert(tk.END, "Welcome to JARVIS GUI Assistant\n")

        self.start_button = tk.Button(root, text="Start Listening", font=("Consolas", 14), bg="#00FFAA", fg="black", command=self.listen_thread)
        self.start_button.pack(pady=20)

    def listen_thread(self):
        thread = threading.Thread(target=self.take_command)
        thread.start()

    def take_command(self):
        self.status_label.config(text="Listening...")

        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
            except sr.WaitTimeoutError:
                self.update_output("No speech detected within 5 seconds.")
                self.status_label.config(text="Idle...")
                return

        self.status_label.config(text="Recognizing...")
        try:
            query = r.recognize_google(audio, language='en-in')
            self.update_output(f"You said: {query}")
        except sr.UnknownValueError:
            self.update_output("Sorry, I couldn't understand that.")
        except sr.RequestError as e:
            self.update_output(f"API error: {e}")

        self.status_label.config(text="Idle...")

    def update_output(self, message):
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)


# -----------------------------
# Main Entry Point
# -----------------------------
if __name__ == "__main__":
    show_intro_animation()
    root = tk.Tk()
    app = VoiceAssistantGUI(root)
    root.mainloop()
