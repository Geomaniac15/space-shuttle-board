import random
import math
import time
from machine import Pin
from neopixel import NeoPixel

# --- CONFIG ---
LED_PIN       = 5     # GPIO pin for data line
NUM_LEDS      = 20
STEP_DELAY_MS = 400   # ms per step -- 73 steps = ~30s total

np = NeoPixel(Pin(LED_PIN), NUM_LEDS)

# --- NODE NAMES (index = physical LED index on board) ---
NODE_NAMES = [
    'Ambient Temperature',            #  0
    'Ice Formation Risk',             #  1
    'Sensor Accuracy',                #  2
    'Launch Pressure',                #  3
    'Field Joint O-Ring Resilience',  #  4  <-- core failure node
    'SRB Internal Temperature',       #  5
    'Joint Rotation',                 #  6
    'Primary O-Ring Seal',            #  7
    'Secondary O-Ring Seal',          #  8
    'SRB Case Integrity',             #  9
    'Blow-By Erosion',                # 10
    'Flame Impingement',              # 11
    'External Tank Integrity',        # 12
    'LH2 Tank Breach',                # 13
    'Intertank Structure',            # 14
    'Aerodynamic Stress',             # 15
    'Structural Load Distribution',   # 16
    'Electrical Power',               # 17
    'Flight Control System',          # 18
    'Vehicle Survival'                # 19
]

NODE_INDEX = {name: i for i, name in enumerate(NODE_NAMES)}


# --- NODE CLASS ---
class Node:
    __slots__ = [
        'name', 'health', 'failed', 'dependencies',
        'baseline', 'health_sensitivity', 'override_active'
    ]
    def __init__(self, name):
        self.name               = name
        self.health             = 1.0
        self.failed             = False
        self.dependencies       = []
        self.baseline           = -9.5
        self.health_sensitivity = 5.0
        self.override_active    = False


# --- MATHS ---
def sigmoid(x):
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except (OverflowError, ValueError):
        return 0.0 if x < 0 else 1.0


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


# --- O-RING TEMPERATURE CURVE ---
# Based on Thiokol resilience test data shape.
# Steep transition centred at 10C (50F) -- their identified minimum safe temp.
# Near-zero below 0C, full resilience above ~20C.
def oring_resilience(temp_c):
    return max(0.0, min(1.0, sigmoid((temp_c - 10.0) * 0.55)))


# --- GRAPH ---
nodes = {name: Node(name) for name in NODE_NAMES}

edges = {
    'Field Joint O-Ring Resilience': ['Ambient Temperature', 'Launch Pressure'],
    'Joint Rotation':                ['Field Joint O-Ring Resilience', 'SRB Internal Temperature'],
    'Primary O-Ring Seal':           ['Joint Rotation'],
    'Secondary O-Ring Seal':         ['Primary O-Ring Seal'],
    'Blow-By Erosion':               ['Secondary O-Ring Seal', 'SRB Case Integrity'],
    'Flame Impingement':             ['Blow-By Erosion'],
    'External Tank Integrity':       ['Flame Impingement'],
    'LH2 Tank Breach':               ['External Tank Integrity'],
    'Aerodynamic Stress':            ['Ice Formation Risk', 'Flight Control System'],
    'Structural Load Distribution':  ['LH2 Tank Breach', 'Intertank Structure', 'Aerodynamic Stress'],
    'Vehicle Survival':              ['Structural Load Distribution'],
    'Flight Control System':         ['Electrical Power'],
    'Launch Pressure':               ['Sensor Accuracy'],
}

edge_w = {
    ('Blow-By Erosion',    'Flame Impingement'):             2.0,
    ('Flame Impingement',  'External Tank Integrity'):       2.0,
    ('External Tank Integrity', 'LH2 Tank Breach'):          1.7,
    ('LH2 Tank Breach',    'Structural Load Distribution'):  2.2,
    ('Aerodynamic Stress', 'Structural Load Distribution'):  1.5,
    ('Sensor Accuracy',    'Launch Pressure'):               0.6,
    ('Launch Pressure',    'Field Joint O-Ring Resilience'): 0.8,
    ('Electrical Power',   'Flight Control System'):         0.7,
    ('Flight Control System', 'Aerodynamic Stress'):         0.8,
    ('Ice Formation Risk', 'Aerodynamic Stress'):            1.0,
    ('SRB Internal Temperature', 'Joint Rotation'):          1.0,
    ('Field Joint O-Ring Resilience', 'Joint Rotation'):     1.2,
    ('Joint Rotation',     'Primary O-Ring Seal'):           1.2,
    ('Primary O-Ring Seal', 'Secondary O-Ring Seal'):        1.0,
    ('Secondary O-Ring Seal', 'Blow-By Erosion'):            1.3,
    ('SRB Case Integrity', 'Blow-By Erosion'):               1.0,
    ('Intertank Structure', 'Structural Load Distribution'):  1.0,
    ('Structural Load Distribution', 'Vehicle Survival'):    2.0,
}

# nodes driven by physics directly, not the propagation model
EXOGENOUS = {
    'Ambient Temperature', 'Sensor Accuracy', 'Launch Pressure',
    'Ice Formation Risk', 'SRB Internal Temperature',
    'SRB Case Integrity', 'Intertank Structure', 'Electrical Power',
}

# failure probability penalty when launch commit override is active --
# represents Thiokol engineers being overruled by management
OVERRIDE_BONUS = {
    'Field Joint O-Ring Resilience': 2.8,
    'Primary O-Ring Seal':           1.2,
    'Secondary O-Ring Seal':         1.2,
    'Blow-By Erosion':               0.8,
    'Flame Impingement':             0.6,
}

SRB_CORRIDOR = {
    'Field Joint O-Ring Resilience', 'Joint Rotation',
    'Primary O-Ring Seal', 'Secondary O-Ring Seal',
    'Blow-By Erosion', 'Flame Impingement',
}

for node_name, deps in edges.items():
    nodes[node_name].dependencies = deps

# tuned baselines
nodes['Field Joint O-Ring Resilience'].baseline = -5.8
nodes['Blow-By Erosion'].baseline               = -6.2
nodes['External Tank Integrity'].baseline       = -6.2
nodes['Structural Load Distribution'].baseline  = -6.5


# --- SLAG SEAL STATE ---
# After primary O-ring fails at ignition, aluminium oxide slag temporarily
# reseals the joint -- this is why the vehicle survived for 72 seconds.
# The seal breaks at max-Q. This dict is reset on each run.
slag = {'active': False, 'broken': False}


# --- SIMULATION STEP ---
def update_system(temp_c, override, t):

    # ----- EXOGENOUS NODES -----

    # O-ring resilience via Thiokol curve -- the central physics of the disaster
    nodes['Field Joint O-Ring Resilience'].health = oring_resilience(temp_c)

    # Ice risk steep below freezing
    nodes['Ice Formation Risk'].health = 1.0 - sigmoid((5.0 - temp_c) * 0.7)
    nodes['Ice Formation Risk'].failed = False

    # Sensor accuracy degrades slightly in cold
    nodes['Sensor Accuracy'].health = max(0.0, 1.0 - 0.015 * max(0, 12 - temp_c))

    # SRB internal temp tied to ambient -- cold propellant burns less uniformly,
    # raising joint stress. This is a real contributing factor.
    srb_penalty = max(0.0, (10.0 - temp_c) / 20.0)
    nodes['SRB Internal Temperature'].health = max(0.0, 1.0 - srb_penalty)

    # Pressure ramps through ignition sequence
    pressure = sigmoid((t - 8) * 0.7)
    nodes['Launch Pressure'].health  = 1.0 - 0.6 * pressure
    nodes['Electrical Power'].health = max(0.0, 1.0 - 0.01 * pressure - 0.03 * random.random())
    nodes['SRB Case Integrity'].health   = 1.0
    nodes['Intertank Structure'].health  = 1.0

    # ----- TIMED PHYSICAL EVENTS -----

    # T+52s: wind shear -- real telemetry showed the vehicle pitching hard.
    # Thiokol engineers had flagged this as a risk amplifier at low temps.
    if t == 52:
        nodes['Aerodynamic Stress'].health    *= 0.55
        nodes['Flight Control System'].health *= 0.80

    # T+60s: max-Q (maximum dynamic pressure).
    # Breaks the temporary slag seal and reinitialises blow-by.
    if t == 60:
        if slag['active'] and not slag['broken']:
            slag['broken'] = True
            slag['active'] = False
            nodes['Blow-By Erosion'].failed = True
            nodes['Blow-By Erosion'].health = 0.0
        nodes['Aerodynamic Stress'].health          *= 0.60
        nodes['Structural Load Distribution'].health *= 0.85

    # ----- SLAG SEAL ACTIVATION -----
    # Primary O-ring has blown but erosion hasn't propagated yet -- slag forms.
    if (nodes['Primary O-Ring Seal'].failed
            and not nodes['Blow-By Erosion'].failed
            and not slag['active']
            and not slag['broken']):
        slag['active'] = True

    # ----- PROPAGATION MODEL -----
    for node in nodes.values():
        if node.name in EXOGENOUS:
            continue
        if node.failed:
            continue

        # Slag seal suppresses blow-by propagation while holding
        if slag['active'] and node.name == 'Blow-By Erosion':
            continue

        # Weighted stress sum from parent nodes
        stress = 0.0
        for dep in node.dependencies:
            w = edge_w.get((dep, node.name), 1.0)
            stress += w * (1.0 - nodes[dep].health)

        # Hard-failure shock when a parent has completely failed
        if any(nodes[dep].failed for dep in node.dependencies):
            shock = random.uniform(2.2, 3.2)
            if override and node.name in SRB_CORRIDOR:
                shock += 0.4
            stress += shock
            node.health *= 0.85

            if random.random() < 0.012:
                node.failed = True
                node.health = 0.0
                continue

        # Override penalty -- management overruling Thiokol engineers
        override_term        = 0.0
        node.override_active = False
        if override and node.name in OVERRIDE_BONUS:
            override_term        = OVERRIDE_BONUS[node.name]
            node.override_active = True

        logit = (
            node.baseline
            + node.health_sensitivity * (1.0 - node.health)
            + stress
            + override_term
        )

        if random.random() < sigmoid(logit):
            node.failed = True
            node.health = 0.0


# --- RESET ---
def reset_nodes():
    for node in nodes.values():
        node.health          = 1.0
        node.failed          = False
        node.override_active = False
    nodes['Field Joint O-Ring Resilience'].baseline = -5.8
    nodes['Blow-By Erosion'].baseline               = -6.2
    nodes['External Tank Integrity'].baseline       = -6.2
    nodes['Structural Load Distribution'].baseline  = -6.5
    slag['active'] = False
    slag['broken'] = False


# --- LED COLOUR ---
# Smooth interpolation: green -> amber -> red as health drops.
# Brightness also scales with health so partial failures visibly dim.
def health_to_colour(node):
    if node.failed:
        return (255, 0, 0)

    if node.override_active:
        return (0, 60, 255)   # blue for override-penalised SRB corridor nodes

    h = max(0.0, min(1.0, node.health))

    if h >= 0.5:
        t = (1.0 - h) * 2.0          # 0 at h=1.0, 1 at h=0.5
        r = int(lerp(0,   255, t))
        g = int(lerp(180, 110, t))
        b = 0
    else:
        t = (0.5 - h) * 2.0          # 0 at h=0.5, 1 at h=0.0
        r = 255
        g = int(lerp(110, 0, t))
        b = 0

    brightness = max(0.25, h)
    return (int(r * brightness), int(g * brightness), int(b * brightness))


def write_leds():
    for name, node in nodes.items():
        np[NODE_INDEX[name]] = health_to_colour(node)
    np.write()


def all_leds(colour):
    for i in range(NUM_LEDS):
        np[i] = colour
    np.write()


# --- SEQUENCES ---
def boot_sequence():
    '''Sequential green startup simulating system readiness check.'''
    all_leds((0, 0, 0))
    for i in range(NUM_LEDS):
        np[i] = (0, 180, 0)
        np.write()
        time.sleep_ms(80)
    time.sleep_ms(600)
    all_leds((0, 0, 0))
    time.sleep_ms(400)


def flash_outcome(survived):
    colour = (0, 200, 0) if survived else (255, 0, 0)
    for _ in range(6):
        all_leds(colour)
        time.sleep_ms(250)
        all_leds((0, 0, 0))
        time.sleep_ms(180)
    if not survived:
        all_leds((40, 0, 0))   # dim red hold on loss of vehicle
        np.write()


# --- MAIN RUN ---
def run(temp_c=0, override=False, steps=73):
    reset_nodes()
    boot_sequence()
    write_leds()
    time.sleep_ms(1000)

    for t in range(steps):
        update_system(temp_c, override, t)
        write_leds()
        time.sleep_ms(STEP_DELAY_MS)

        if nodes['Vehicle Survival'].failed:
            flash_outcome(survived=False)
            return False

    flash_outcome(survived=True)
    return True


# --- ENTRY POINT ---
# Actual Challenger launch conditions: -0.6C ambient, override active
LAUNCH_TEMP_C   = -1
LAUNCH_OVERRIDE = True

run(temp_c=LAUNCH_TEMP_C, override=LAUNCH_OVERRIDE, steps=73)
