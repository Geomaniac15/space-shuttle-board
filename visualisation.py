import pygame
import time

from main import update_system, nodes

# led order
NODE_ORDER = [
    'Field Joint O-Ring Resilience',
    'Joint Rotation',
    'Primary O-Ring Seal',
    'Secondary O-Ring Seal',
    'Blow-By Erosion',
    'Flame Impingement',
    'External Tank Integrity',
    'LH2 Tank Breach',
    'Structural Load Distribution',
    'Vehicle Survival',
    'Ice Formation Risk',
    'Aerodynamic Stress',
    'Flight Control System',
    'Electrical Power',
    'Launch Pressure',
    'Sensor Accuracy',
    'SRB Internal Temperature',
    'SRB Case Integrity',
    'Intertank Structure',
    'Ambient Temperature',
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

# colour mapping
def led_colour(node):
    if node.failed:
        return (200, 0, 0)      # red
    elif node.health < 0.6:
        return (255, 140, 0)    # amber
    else:
        return (180, 220, 255)  # cold white

def reset_nodes():
    for node in nodes.values():
        node.health = 1.0
        node.failed = False

def run_visual_sim():
    pygame.init()
    WIDTH, HEIGHT = 500, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Shuttle Systems Cascade')

    font = pygame.font.SysFont('consolas', 16)

    clock = pygame.time.Clock()

    temp_c = 15
    override = False

    running = True
    launching = False
    step = 0
    steps_total = 60

    reset_nodes()

    while running:
        screen.fill((15, 15, 20))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:
                    temp_c = 0 if temp_c == 15 else 15
                if event.key == pygame.K_o:
                    override = not override
                if event.key == pygame.K_SPACE:
                    reset_nodes()
                    launching = True
                    step = 0
        
        # sim step
        if launching:
            if step < steps_total and not nodes['Vehicle Survival'].failed:
                update_system(temp_c, override)
                step += 1
            else:
                launching = False
        
        # draw led strip
        top_margin = 100
        spacing = (HEIGHT - 200) // len(NODE_ORDER)

        for i, name in enumerate(NODE_ORDER):
            node = nodes[name]
            x = 150
            y = top_margin + i * spacing

            radius = 14

            pygame.draw.circle(screen, led_colour(node), (x, y), radius)

            #label = NODE_LABELS[name]
            label = node.name
            label_surface = font.render(label, True, (200, 200, 200))
            screen.blit(label_surface, (x + 30, y - 8))
        
        # status text
        status_text = f'TEMP: {temp_c}C | OVERRIDE: {override}'
        text_surface = font.render(status_text, True, (200, 200, 200))
        screen.blit(text_surface, (20, 20))

        if nodes['Vehicle Survival'].failed:
            fail_text = font.render('VEHICLE LOST', True, (255, 80, 80))
            screen.blit(fail_text, (20, 50))
        elif not launching and step > 0:
            success_text = font.render('SURVIVED', True, (120, 255, 120))
            screen.blit(success_text, (20, 50))

        pygame.display.flip()
        clock.tick(8)   # controls animation speed

    pygame.quit()


if __name__ == '__main__':
    run_visual_sim()
