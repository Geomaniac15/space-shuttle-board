import random
import math

class Node:
    def __init__(self, name):
        self.name = name
        self.health = 1.0
        self.failed = False
        self.dependencies = []
        self.baseline = -8.0
        self.health_sensitivity = 5.0
        self.override_sensitivity = 0.0
        self.temp_sensitivity = 0.0

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

# create nodes
nodes = {name: Node(name) for name in [
    'Ambient Temperature',
    'Ice Formation Risk',
    'Sensor Accuracy',
    'Launch Pressure',
    'Field Joint O-Ring Resilience',
    'SRB Internal Temperature',
    'Joint Rotation',
    'Primary O-Ring Seal',
    'Secondary O-Ring Seal',
    'SRB Case Integrity',
    'Blow-By Erosion',
    'Flame Impingement',
    'External Tank Integrity',
    'LH2 Tank Breach',
    'Intertank Structure',
    'Aerodynamic Stress',
    'Structural Load Distribution',
    'Electrical Power',
    'Flight Control System',
    'Vehicle Survival'
]}

# dependency edges
edges = {
    'Field Joint O-Ring Resilience': ['Ambient Temperature', 'Launch Pressure'],
    'Joint Rotation': ['Field Joint O-Ring Resilience', 'SRB Internal Temperature'],
    'Primary O-Ring Seal': ['Joint Rotation'],
    'Secondary O-Ring Seal': ['Primary O-Ring Seal'],
    'Blow-By Erosion': ['Secondary O-Ring Seal', 'SRB Case Integrity'],
    'Flame Impingement': ['Blow-By Erosion'],
    'External Tank Integrity': ['Flame Impingement'],
    'LH2 Tank Breach': ['External Tank Integrity'],
    'Aerodynamic Stress': ['Ice Formation Risk', 'Flight Control System'],
    'Structural Load Distribution': ['LH2 Tank Breach', 'Intertank Structure', 'Aerodynamic Stress'],
    'Vehicle Survival': ['Structural Load Distribution'],
    'Flight Control System': ['Electrical Power'],
    'Launch Pressure': ['Sensor Accuracy'],
}

# edge weights 
edge_w ={
    ('Blow-By Erosion', 'Flame Impingement'): 2.0,
    ('Flame Impingement', 'External Tank Integrity'): 2.0,
    ('External Tank Integrity', 'LH2 Tank Breach'): 1.7,
    ('LH2 Tank Breach', 'Structural Load Distribution'): 2.2,
    ('Aerodynamic Stress', 'Structural Load Distribution'): 1.5,

    # softer couplings
    ('Sensor Accuracy', 'Launch Pressure'): 0.6,
    ('Launch Pressure', 'Field Joint O-Ring Resilience'): 0.8,
    ('Electrical Power', 'Flight Control System'): 0.7,
    ('Flight Control System', 'Aerodynamic Stress'): 0.8,
    ('Ice Formation Risk', 'Aerodynamic Stress'): 1.0,

    ('SRB Internal Temperature', 'Joint Rotation'): 1.0,
    ('Field Joint O-Ring Resilience', 'Joint Rotation'): 1.2,
    ('Joint Rotation', 'Primary O-Ring Seal'): 1.2,
    ('Primary O-Ring Seal', 'Secondary O-Ring Seal'): 1.0,
    ('Secondary O-Ring Seal', 'Blow-By Erosion'): 1.3,
    ('SRB Case Integrity', 'Blow-By Erosion'): 1.0,
    ('Intertank Structure', 'Structural Load Distribution'): 1.0,
    ('Structural Load Distribution', 'Vehicle Survival'): 2.5,
}

# dependencies
for node_name, deps in edges.items():
    nodes[node_name].dependencies = deps

# update system
def update_system(temp_c=0, override=False):
    for node in nodes.values():
        if node.failed:
            continue

        # compute stresses
        stress = 0.0
        for dep in node.dependencies:
            w = edge_w.get((dep, node_name), 1.0)
            stress += w * (1 - nodes[dep].health)
        
        # temp effect only on o-rings
        temp_term = 0
        if node.name == 'Field Joint O-Ring Resilience':
            cold = max(0, 5 - temp_c)
            temp_term = cold * 0.7
        
        logit = (
            node.baseline
            + node.health_sensitivity * (1 - node.health)
            + stress
            + temp_term
        )

        p_fail = sigmoid(logit)

        if random.random() < p_fail:
            node.failed = True
            node.health = 0.0
        else:
            node.health = max(0, node.health - 0.01 * stress)

def simulate(temp_c=0, override=False, steps=200):
    # reset
    for node in nodes.values():
        node.health = 1.0
        node.failed = False

    for t in range(steps):
        update_system(temp_c, override)

        if nodes['Vehicle Survival'].failed:
            return False
    
    return True

# run sims
temps = [15, 0, 0]
overrides = [False, False, True]

for i in range(3):
    temp = temps[i]
    override = overrides[i]

    results = [simulate(temp_c=temp, override=override) for _ in range(100)]
    print(f'Temperature: {temp}C, override: {override}')
    print(f'Survival rate: {sum(results) / len(results)}')
    print()