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

# dependencies
for node_name, deps in edges.items():
    nodes[node_name].dependencies = deps

def update_system(temp_c=0, override=False):
    for node in nodes.values():
        if node.failed:
            continue

        stress = 0
        for dep in node.dependencies:
            stress += (1 - nodes[dep].health)
        
        # temp effect only on o-rings
        temp_term = 0
        if node.name == 'Field Joint O-Ring Resilience':
            cold = max(0, 5 - temp_c)
            temp_term = cold * 0.5
        
        logit = (
            node.baseline
            + node.health_sensitivity * (1 - node.health)
            + stress
            + temp_term
        )

        p_fail = sigmoid(logit)

        if random.random < p_fail:
            node.failed = True
            node.health = 0.0
        else:
            node.health = max(0, node.health - 0.01 * stress)

