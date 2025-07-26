# sagi_hud_animation.py

import pygame
import math
import sys
import random

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 800
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SAGI HUD Animation")

# Colors
BLACK = (10, 10, 10)
WHITE = (200, 200, 200)
GREY = (100, 100, 100)
LIGHT_GREY = (150, 150, 150)
CYAN = (0, 255, 255)

# Clock for FPS control
clock = pygame.time.Clock()
FPS = 60

CENTER = (WIDTH // 2, HEIGHT // 2)

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
    pygame.draw.circle(glow_surf, (0, 255, 255, alpha), CENTER, radius, width=2)
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

def draw_text_center(surface, text, pos, font_size=32, color=WHITE):
    font = pygame.font.SysFont("Consolas", font_size, bold=True)
    rendered = font.render(text, True, color)
    glow = font.render(text, True, CYAN)
    rect = rendered.get_rect(center=pos)
    for offset in [(-1,0),(1,0),(0,-1),(0,1)]:
        glow_rect = glow.get_rect(center=(pos[0]+offset[0], pos[1]+offset[1]))
        surface.blit(glow, glow_rect)
    surface.blit(rendered, rect)

def main():
    running = True
    frame_count = 0
    rotation = 0

    appear_intervals = [60, 120, 180, 240]  # frame delays for each circle

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        SCREEN.fill(BLACK)

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
            draw_dotted_circle(SCREEN, CENTER, 320, 60, 2, rotation * 0.5, GREY, alpha)
        if frame_count >= appear_intervals[1]:
            alpha = min((frame_count - appear_intervals[1]) * 5, 255)
            draw_dotted_circle(SCREEN, CENTER, 280, 40, 3, -rotation * 0.7, LIGHT_GREY, alpha)
        if frame_count >= appear_intervals[2]:
            alpha = min((frame_count - appear_intervals[2]) * 5, 255)
            draw_random_dots(SCREEN, CENTER, 250, 80, 3, rotation, alpha)
        if frame_count >= appear_intervals[3]:
            alpha = min((frame_count - appear_intervals[3]) * 5, 255)
            draw_rotating_arcs(SCREEN, CENTER, 200, rotation, alpha)

            inner_rings = [90, 65, 40]
            arc_lengths = [2.5, 1.8, 3.0]
            for i, rad in enumerate(inner_rings):
                start = (rotation * (1.5 - i * 0.5)) % (2 * math.pi)
                end = start + arc_lengths[i] * 1.7
                draw_arc(SCREEN, WHITE, CENTER, rad, start, end, 2)

        draw_text_center(SCREEN, "SAGI amn", CENTER, font_size=40, color=WHITE)

        if frame_count > max(appear_intervals):
            rotation += 0.02

        frame_count += 1
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
