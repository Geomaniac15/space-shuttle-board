import random
import math

# --- GLOBALS & CONSTANTS ---
NODE_NAMES = [
    'Ambient Temperature', 'Sensor Accuracy', 'Launch Pressure', 
    'SRB Internal Temperature', 'SRB Case Integrity', 'Field Joint O-Ring Resilience', 
    'Joint Rotation', 'Primary O-Ring Seal', 'Secondary O-Ring Seal', 
    'Blow-By Erosion', 'Flame Impingement', 'External Tank Integrity', 
    'LH2 Tank Breach', 'Intertank Structure', 'Structural Load Distribution', 
    'Electrical Power', 'Flight Control System', 'Aerodynamic Stress', 
    'Ice Formation Risk', 'Vehicle Survival'
]

NODE_DEPS = {
    'Launch Pressure': ['Sensor Accuracy'],
    'Field Joint O-Ring Resilience': ['Ambient Temperature', 'Launch Pressure'],
    'Joint Rotation': ['Field Joint O-Ring Resilience', 'SRB Internal Temperature'],
    'Primary O-Ring Seal': ['Joint Rotation'],
    'Secondary O-Ring Seal': ['Primary O-Ring Seal'],
    'Blow-By Erosion': ['Secondary O-Ring Seal', 'SRB Case Integrity'],
    'Flame Impingement': ['Blow-By Erosion'],
    'External Tank Integrity': ['Flame Impingement'],
    'LH2 Tank Breach': ['External Tank Integrity'],
    'Structural Load Distribution': ['LH2 Tank Breach', 'Intertank Structure', 'Aerodynamic Stress'],
    'Vehicle Survival': ['Structural Load Distribution'],
    'Flight Control System': ['Electrical Power'],
    'Aerodynamic Stress': ['Flight Control System', 'Ice Formation Risk']
}

SRB_CORRIDOR = {
    'Field Joint O-Ring Resilience', 'Joint Rotation', 'Primary O-Ring Seal',
    'Secondary O-Ring Seal', 'Blow-By Erosion', 'Flame Impingement',
}

# --- UTILITY ---
def sigmoid(x):
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0

class Node:
    __slots__ = ['name', 'baseline', 'dependencies', 'health', 'failed', 'override_active', 'failed_due_to']
    
    def __init__(self, name, baseline=-10.0):
        self.name = name
        self.baseline = baseline
        self.dependencies = []
        self.health = 1.0
        self.failed = False
        self.override_active = False
        self.failed_due_to = None

def build_system():
    nodes = {n: Node(n) for n in NODE_NAMES}
    for child, parents in NODE_DEPS.items():
        nodes[child].dependencies = parents
    return nodes

# --- SIMULATION LOGIC ---
def update_system(nodes, temp_c, override, t):
    # exogenous updates
    nodes['Ambient Temperature'].health = max(0.0, min(1.0, temp_c / 15.0))
    nodes['Ice Formation Risk'].health = 1.0 - sigmoid((5 - temp_c) * 1.0)
    nodes['Sensor Accuracy'].health = max(0.0, 1.0 - 0.02 * max(0, 10 - temp_c))
    nodes['SRB Internal Temperature'].health = max(0.0, 1.0 - 0.03 * max(0, 10 - temp_c))
    
    pressure = sigmoid((t - 8) * 0.7)
    nodes['Launch Pressure'].health = 1.0 - 0.6 * pressure

    base_power = 1.0 - 0.01 * pressure
    noise = 0.03 * random.random()
    nodes['Electrical Power'].health = max(0.0, base_power - noise)
    nodes['SRB Case Integrity'].health = 1.0
    nodes['Intertank Structure'].health = 1.0

    skip_nodes = {
        'Ambient Temperature', 'Sensor Accuracy', 'SRB Internal Temperature',
        'Launch Pressure', 'Electrical Power', 'SRB Case Integrity',
        'Intertank Structure', 'Ice Formation Risk'
    }

    for name, node in nodes.items():
        if name in skip_nodes or node.failed:
            continue

        stress = sum((1.0 - nodes[dep].health) for dep in node.dependencies)
        
        if name == 'Structural Load Distribution':
            stress += 2.0 * (1.0 - nodes['Aerodynamic Stress'].health)
        
        if name == 'Aerodynamic Stress':
            node.health = max(0.8, node.health * 0.98)

        # propagation shock
        if any(nodes[d].failed for d in node.dependencies):
            shock = random.uniform(1.5, 3.0) 
            if override and name in SRB_CORRIDOR and temp_c < 7:
                shock += 0.5
                node.override_active = True
            stress += shock
            node.health *= 0.85

        if name == 'Field Joint O-Ring Resilience' and temp_c < 10:
            cold = 10 - temp_c
            node.baseline = -9.5 + (0.2 * cold)
        else:
            node.baseline = -10.0 

        if override and name in SRB_CORRIDOR:
            stress += 0.5

        logit = node.baseline + 2.5 * stress
        p_fail = sigmoid(logit)

        if random.random() < p_fail:
            node.failed = True
            node.health = 0.0
            for dep in node.dependencies:
                if nodes[dep].failed:
                    node.failed_due_to = dep
                    break
        else:
            node.health = max(0.1, node.health * (1.0 - 0.01 * stress))

def simulate(temp_c=5, override=False, steps=60):
    nodes = build_system()
    for t in range(steps):
        update_system(nodes, temp_c, override, t)
        if nodes['Vehicle Survival'].failed:
            return False
    return True

if __name__ == '__main__':
    temps = [15, 0, 0]
    overrides = [False, False, True]

    for i in range(3):
        temp = temps[i]
        override = overrides[i]
        
        results = [simulate(temp_c=temp, override=override, steps=60) for _ in range(2000)]
        print(f'Temperature: {temp}°C, Override: {override}')
        print(f'Survival rate: {(sum(results) / len(results)) * 100:.1f}%\n')