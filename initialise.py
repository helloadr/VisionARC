# sagi_hud_animation.py

import pygame
import math
import sys
import random
import time
import subprocess

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 300
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("System Initialization Animation")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CYAN = (0, 255, 255)
DARK_BLUE = (10, 50, 80)

# Fonts
font = pygame.font.SysFont("Consolas", 38, bold=True)

def draw_segmented_progress_bar(surface, x, y, width, height, segments, filled_segments):
    segment_width = width // segments
    gap = 4
    for i in range(segments):
        rect = pygame.Rect(x + i * segment_width + gap // 2, y, segment_width - gap, height)
        color = CYAN if i < filled_segments else DARK_BLUE
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, WHITE, rect, 2)

def main():
    running = True
    progress = 0
    max_segments = 20

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        SCREEN.fill(BLACK)

        # Draw glowing border frame style
        pygame.draw.rect(SCREEN, WHITE, pygame.Rect(50, 40, 700, 80), 2)
        pygame.draw.line(SCREEN, CYAN, (50, 120), (750, 120), 2)
        pygame.draw.rect(SCREEN, WHITE, pygame.Rect(100, 150, 600, 40), 2)

        # Draw text
        text = font.render(f"INITIATING SYSTEM 1....", True, CYAN)
        SCREEN.blit(text, (WIDTH // 2 - text.get_width() // 2, 60))

        # Draw segmented progress bar
        draw_segmented_progress_bar(SCREEN, 100, 150, 600, 40, max_segments, progress)

        pygame.display.flip()
        time.sleep(0.25)

        progress += 1
        if progress > max_segments:
            running = False
    subprocess.run(["python", "main.py"])  # Start the main application
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
