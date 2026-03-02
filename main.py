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