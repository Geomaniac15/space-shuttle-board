import random
import math

# UTILITY
def sigmoid(x):
    return 1 / (1 + math.exp(-x))

class Node:
    def __init__(self, name, baseline=-8.0):
        self.name = name
        self.baseline = baseline
        self.dependencies = []
        self.health = 1.0
        self.failed = False
        self.override_active = False
        self.failed_due_to = None


# build graph
def build_system():
    nodes = {}

    # core nodes
    names = [
        'Ambient Temperature',
        'Sensor Accuracy',
        'Launch Pressure',
        'SRB Internal Temperature',
        'SRB Case Integrity',
        'Field Joint O-Ring Resilience',
        'Joint Rotation',
        'Primary O-Ring Seal',
        'Secondary O-Ring Seal',
        'Blow-By Erosion',
        'Flame Impingement',
        'External Tank Integrity',
        'LH2 Tank Breach',
        'Intertank Structure',
        'Structural Load Distribution',
        'Electrical Power',
        'Flight Control System',
        'Aerodynamic Stress',
        'Ice Formation Risk',
        'Vehicle Survival'
    ]

    for n in names:
        nodes[n] = Node(n)

    # dependencies (based on my diagram)
    deps = {
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

    for child, parents in deps.items():
        nodes[child].dependencies = parents

    return nodes

# update step
SRB_CORRIDOR = {
    'Field Joint O-Ring Resilience',
    'Joint Rotation',
    'Primary O-Ring Seal',
    'Secondary O-Ring Seal',
    'Blow-By Erosion',
    'Flame Impingement',
}

def update_system(nodes, temp_c, override, t):

    # exogenous updates

    # ambient temperature
    nodes['Ambient Temperature'].health = max(0, min(1, (temp_c + 5) / 25))

    # ice formation
    ice = sigmoid((5 - temp_c) * 1.0)
    nodes['Ice Formation Risk'].health = 1 - ice

    # sensor accuracy degrades slightly in cold
    nodes['Sensor Accuracy'].health = max(0, 1 - 0.02 * max(0, 10 - temp_c))

    # SRB internal temperature
    nodes['SRB Internal Temperature'].health = max(0, 1 - 0.03 * max(0, 10 - temp_c))

    # launch pressure ramp
    pressure = sigmoid((t - 8) * 0.7)
    nodes['Launch Pressure'].health = 1 - 0.6 * pressure

    # small random fluctuation
    # electrical power degradation + fluctuation
    base_power = 1 - 0.01 * pressure
    noise = 0.03 * random.random()
    nodes['Electrical Power'].health = max(0.0, base_power - noise)

    # SRB case baseline
    nodes['SRB Case Integrity'].health = 1.0

    # intertank structure baseline
    nodes['Intertank Structure'].health = 1.0


    # node failure logic

    for node in nodes.values():

        if node.name in [
            'Ambient Temperature',
            'Sensor Accuracy',
            'SRB Internal Temperature',
            'Launch Pressure',
            'Electrical Power',
            'SRB Case Integrity',
            'Intertank Structure',
            'Ice Formation Risk'
        ]:
            continue

        if node.failed:
            continue

        stress = 0

        # dependency stress
        for dep in node.dependencies:
            stress += (1 - nodes[dep].health)
        
        if node.name == 'Structural Load Distribution':
            aero_stress = 2.0 * (1 - nodes['Aerodynamic Stress'].health)
            stress += aero_stress
        
        if node.name == 'Aerodynamic Stress':
            node.health *= 0.97

        # propagation shock
        if any(nodes[d].failed for d in node.dependencies):
            shock = 2.0
            if override and node.name in SRB_CORRIDOR and temp_c < 7:
                shock += 0.5
                node.override_active = True
            stress += shock
            node.health *= 0.85

        # temperature sensitivity for O-ring
        if node.name == 'Field Joint O-Ring Resilience' and temp_c < 5:
            cold = 5 - temp_c
            node.baseline = -5.8 + 0.45 * cold + 0.4 * cold**2
        else:
            node.baseline = -9.5

        # override bonus
        if override and node.name in SRB_CORRIDOR:
            stress += 0.5

        # failure probability
        logit = node.baseline + 3.5 * stress
        p_fail = sigmoid(logit)

        if random.random() < p_fail:
            node.failed = True
            node.health = 0
            for dep in node.dependencies:
                if nodes[dep].failed:
                    node.failed_due_to = dep
                    break
        else:
            node.health *= (1 - 0.02 * stress)


# simulator
def simulate(temp_c=5, override=False, steps=40):
    nodes = build_system()

    for t in range(steps):
        update_system(nodes, temp_c, override, t)
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