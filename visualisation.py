import pygame
import math
import time
from simulator import build_system, update_system
import random

# -------------------------------
# CONFIG
# -------------------------------

pygame.init()
info = pygame.display.Info()
WIDTH = min(800, info.current_w - 100)
HEIGHT = min(850, info.current_h - 100)

BACKGROUND = (10, 15, 25)

STEPS_TOTAL = 120
FPS = 8

# -------------------------------
# GROUPED SYSTEM SECTIONS
# -------------------------------

SECTIONS = [
    ('SRB CHAIN', [
        'Field Joint O-Ring Resilience',
        'Joint Rotation',
        'Primary O-Ring Seal',
        'Secondary O-Ring Seal',
        'Blow-By Erosion',
        'Flame Impingement',
    ]),
    ('TANK + STRUCTURE', [
        'External Tank Integrity',
        'LH2 Tank Breach',
        'Structural Load Distribution',
        'Vehicle Survival',
        'Intertank Structure',
    ]),
    ('AERO + CONTROL', [
        'Ice Formation Risk',
        'Aerodynamic Stress',
        'Flight Control System',
        'Electrical Power',
    ]),
    ('CONTEXT', [
        'Launch Pressure',
        'Sensor Accuracy',
        'SRB Internal Temperature',
        'SRB Case Integrity',
        'Ambient Temperature',
    ])
]

NODE_LABELS = {
    'Field Joint O-Ring Resilience': 'Field Joint',
    'Joint Rotation': 'Joint Rot',
    'Primary O-Ring Seal': 'Primary Seal',
    'Secondary O-Ring Seal': 'Secondary Seal',
    'Blow-By Erosion': 'Blow-By',
    'Flame Impingement': 'Flame',
    'External Tank Integrity': 'Tank Int',
    'LH2 Tank Breach': 'LH2 Breach',
    'Structural Load Distribution': 'Load Dist',
    'Vehicle Survival': 'Survival',
    'Ice Formation Risk': 'Ice Risk',
    'Aerodynamic Stress': 'Aero',
    'Flight Control System': 'FCS',
    'Electrical Power': 'Power',
    'Launch Pressure': 'Pressure',
    'Sensor Accuracy': 'Sensor',
    'SRB Internal Temperature': 'SRB Temp',
    'SRB Case Integrity': 'Case Int',
    'Intertank Structure': 'Intertank',
    'Ambient Temperature': 'Ambient'
}

# Flatten order for iteration if needed
NODE_ORDER = [name for _, group in SECTIONS for name in group]

# -------------------------------
# VISUAL HELPERS
# -------------------------------

def led_colour(node):
    # failure pulsing red
    if node.failed:
        pulse = 150 + int(50 * math.sin(time.time() * 6))
        return (pulse, 0, 0)
    
    # base colour from health
    elif node.health < 0.6:
        base = (255, 140, 0) # stressed orange
    else:
        base = (140, 180, 230) # healthy blue
    
    # override tint
    if node.override_active:
        # pulse the tint so it's clearly animated
        pulse = int(20 * math.sin(time.time() * 4))
        r, g, b = base
        # add purple tint plus the pulse offset
        r = min(255, r + 100 + pulse)
        b = min(255, b + 100 + pulse)
        return (r, g, b)
    
    return base

def reset_nodes(nodes):
    for node in nodes.values():
        node.health = 1.0
        node.failed = False
        node.override_active = False

# -------------------------------
# MAIN VISUAL LOOP
# -------------------------------

def run_visual():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Shuttle Systems Cascade')

    font = pygame.font.SysFont('consolas', 16)
    header_font = pygame.font.SysFont('consolas', 18, bold=True)

    clock = pygame.time.Clock()

    temp_c = 15
    override = False
    launching = False
    step = 0

    TEMP_STATES = [20, 15, 10, 5, 0]

    # reset_nodes()
    nodes = build_system()

    running = True
    while running:
        screen.fill(BACKGROUND)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    current_index = TEMP_STATES.index(temp_c)
                    temp_c = TEMP_STATES[(current_index + 1) % len(TEMP_STATES)]
                if event.key  == pygame.K_r:
                    temp_c = random.choice(TEMP_STATES)
                if event.key == pygame.K_o:
                    override = not override
                    update_system(nodes, temp_c, override, step)
                if event.key == pygame.K_SPACE:
                    reset_nodes(nodes)
                    launching = True
                    step = 0

        # -----------------------
        # SIMULATION STEP
        # -----------------------
        if launching:
            if step < STEPS_TOTAL and not nodes['Vehicle Survival'].failed:
                update_system(nodes, temp_c, override, step)
                LED_PACKET = []
                for name in NODE_ORDER:
                    node = nodes[name]
                    LED_PACKET.append({
                        'node': node.name,
                        'health': node.health,
                        'failed': node.failed,
                        'override': node.override_active
                    })
                # print(LED_PACKET)
                step += 1
            else:
                launching = False

        # -----------------------
        # DRAW SYSTEM
        # -----------------------

        left_sections = SECTIONS[:2]
        right_sections = SECTIONS[2:]

        column_x = [120, 420]
        start_y = 100
        line_spacing = 32
        section_gap = 25

        for col_index, section_group in enumerate([left_sections, right_sections]):
            y = start_y
            x_led = column_x[col_index]

            for section_title, group in section_group:
                header_surface = header_font.render(section_title, True, (200, 200, 220))
                screen.blit(header_surface, (x_led - 60, y))
                y += 35

                for name in group:
                    node = nodes[name]

                    radius = 14

                    pygame.draw.circle(screen, led_colour(node), (x_led, y), radius)

                    label_surface = font.render(node.name, True, (200, 200, 200))
                    screen.blit(label_surface, (x_led + 30, y - 8))

                    y += line_spacing

                y += section_gap

        # -----------------------
        # STATUS TEXT
        # -----------------------

        status_text = f'TEMP: {temp_c}C   |   OVERRIDE: {override}   |   TIME: T+{step}s'
        status_surface = font.render(status_text, True, (200, 200, 200))
        screen.blit(status_surface, (40, 20))

        if nodes['Vehicle Survival'].failed:
            fail_surface = font.render('VEHICLE LOST', True, (255, 80, 80))
            screen.blit(fail_surface, (40, 45))
        elif not launching and step > 0:
            success_surface = font.render('SURVIVED', True, (120, 255, 120))
            screen.blit(success_surface, (40, 45))

        pygame.display.flip()
        clock.tick(FPS)
        # time.sleep(1.5)

    pygame.quit()


if __name__ == '__main__':
    run_visual()