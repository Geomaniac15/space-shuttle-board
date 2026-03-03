import random
import math

class Node:
    def __init__(self, name):
        self.name = name
        self.health = 1.0
        self.failed = False
        self.dependencies = []
        self.baseline = -9.5
        self.health_sensitivity = 5.0
        self.override_sensitivity = 0.0
        self.temp_sensitivity = 0.0
        self.override_active = False

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
    ('Structural Load Distribution', 'Vehicle Survival'): 2.0,
}

exogenous = {
    'Ambient Temperature',
    'Sensor Accuracy',
    'Launch Pressure',
    'Ice Formation Risk'
}

override_bonus = {
    'Field Joint O-Ring Resilience': 2.8,
    'Primary O-Ring Seal': 1.2,
    'Secondary O-Ring Seal': 1.2,
    'Blow-By Erosion': 0.8,
    'Flame Impingement': 0.6,
}

# dependencies
for node_name, deps in edges.items():
    nodes[node_name].dependencies = deps

nodes['Field Joint O-Ring Resilience'].baseline = -5.8
nodes['Blow-By Erosion'].baseline = -6.2
nodes['External Tank Integrity'].baseline = -6.2
nodes['Structural Load Distribution'].baseline = -6.5

# update system
def update_system(temp_c=0, override=False):
    # ice risk from temperature
    cold_factor = sigmoid((1 - temp_c) * 0.5)
    nodes['Ice Formation Risk'].health = 1.0 - cold_factor
    nodes['Ice Formation Risk'].failed = False

    # temperature weakens seal baseline safety
    if temp_c < 5:
        cold = 5 - temp_c
        nodes['Field Joint O-Ring Resilience'].baseline = -5.8 + 0.45*cold + 0.4*cold**2
        nodes['Primary O-Ring Seal'].baseline = -6.2 + 0.15 * cold
        nodes['Secondary O-Ring Seal'].baseline = -6.2 + 0.15 * cold
    else:
        nodes['Field Joint O-Ring Resilience'].baseline = -9.5
        nodes['Primary O-Ring Seal'].baseline = -7.8
        nodes['Secondary O-Ring Seal'].baseline = -7.8

    # direct temperature weakening of SRB seals
    # if temp_c < 5:
    #     cold = 5 - temp_c
    #     nodes['Field Joint O-Ring Resilience'].health *= max(0.0, 1 - 0.05 * cold)
    #     nodes['Primary O-Ring Seal'].health *= max(0.0, 1 - 0.04 * cold)
    #     nodes['Secondary O-Ring Seal'].health *= max(0.0, 1 - 0.04 * cold)

    for node in nodes.values():
        if node.name in exogenous:
            continue

        if node.failed:
            continue

        # compute stresses
        stress = 0.0
        for dep in node.dependencies:
            w = edge_w.get((dep, node.name), 1.0)
            stress += w * (1 - nodes[dep].health)
        
        # propagate failures from dependencies
        if any(nodes[dep].failed for dep in node.dependencies):
            # if any parent has failed, degrade or fail probabilistically
            shock = 2.5
            if override:
                shock += 1.0
            stress += shock
            node.health *= 0.85

            # lower propagation chance to keep survival high at warm temps
            if random.random() < 0.01:
                node.failed = True
                node.health = 0.0
                continue

        # controlled stress-induced weakening (only for key nodes)
        # if node.name in [
        #     'Field Joint O-Ring Resilience',
        #     'Primary O-Ring Seal',
        #     'Secondary O-Ring Seal',
        #     'Blow-By Erosion'
        # ]:
        #     weakening = 0.001 * stress
        #     if temp_c < 5:
        #         weakening += 0.003 * (5 - temp_c)
        #     node.health = max(0.0, node.health - weakening)

        # cold = max(0, 5 - temp_c)
        # cold_stress = 0.0

        # if cold > 0:
        #     if node.name in [
        #         'Joint Rotation',
        #         'Primary O-Ring Seal',
        #         'Secondary O-Ring Seal',
        #         'Blow-By Erosion'
        #     ]:
        #         cold_stress = 0.3 * cold

        # direct temperature weakening of SRB seals (stronger effect)
        # cold = max(0, 10 - temp_c)   # make 10C the softness threshold

        # if cold > 0:
        #     nodes['Field Joint O-Ring Resilience'].health *= max(0.0, 1 - 0.08 * cold)
        #     nodes['Primary O-Ring Seal'].health *= max(0.0, 1 - 0.06 * cold)
        #     nodes['Secondary O-Ring Seal'].health *= max(0.0, 1 - 0.06 * cold)

        # temp effect only on o-rings
        # temp_term = 0
        # if node.name == 'Field Joint O-Ring Resilience':
        #     cold = max(0, 5 - temp_c)
        #     temp_term = cold * 1.5
        # if node.name == 'Secondary O-Ring Seal':
        #     cold = max(0, 5 - temp_c)
        #     temp_term = cold * 0.8
        
        #override_term = override_bonus.get(node.name, 0.0) if override else 0.0
        # override_term = override_bonus.get(node.name, 0.0) if override else 0.0
        override_term = 0.0
        node.override_active = False

        if override and node.name in override_bonus:
            override_term = override_bonus[node.name]
            node.override_active = True
        
        logit = (
            node.baseline
            + node.health_sensitivity * (1 - node.health)
            + stress
            # + temp_term
            # + cold_stress
            + override_term
        )

        p_fail = sigmoid(logit)

        if random.random() < p_fail:
            node.failed = True
            node.health = 0.0
        # convert extreme health drops into failures as well
        
def simulate(temp_c=0, override=False, steps=60):
    # reset
    for node in nodes.values():
        node.health = 1.0
        node.failed = False
        node.override_active = False

    for t in range(steps):
        update_system(temp_c, override)

        if nodes['Vehicle Survival'].failed:
            return False
    
    return True

if __name__ == '__main__':
    # run sims
    temps = [15, 0, 0]
    overrides = [False, False, True]

    for i in range(3):
        temp = temps[i]
        override = overrides[i]

        results = [simulate(temp_c=temp, override=override, steps=60) for _ in range(1000)]
        print(f'Temperature: {temp}C, override: {override}')
        print(f'Survival rate: {sum(results) / len(results)}')
        print()