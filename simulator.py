import random
import math
import matplotlib.pyplot as plt
import time

# --- ANSI Color Codes for the Terminal ---
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

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

    # make sure override indicators are cleared before updating
    for node in nodes.values():
        node.override_active = False

    for name, node in nodes.items():
        if name in skip_nodes or node.failed:
            continue

        # if global override is on, mark SRB corridor nodes so they pulse
        if override and name in SRB_CORRIDOR:
            node.override_active = True

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

def plot_survival_rates(simulations_per_temp=500):
    temperatures = list(range(-10, 21))
    normal_survival = []
    override_survival = []

    print(f"Simulating {simulations_per_temp} launches per temperature. This might take a few seconds...")
    
    for temp in temperatures:
        # simulate standard operations
        results_normal = [simulate(temp_c=temp, override=False, steps=60) for _ in range(simulations_per_temp)]
        normal_survival.append((sum(results_normal) / simulations_per_temp) * 100)
        
        # simulate with override active
        results_override = [simulate(temp_c=temp, override=True, steps=60) for _ in range(simulations_per_temp)]
        override_survival.append((sum(results_override) / simulations_per_temp) * 100)

    # --- plotting the data ---
    plt.figure(figsize=(10, 6))
    
    # drawing
    plt.plot(temperatures, normal_survival, marker='o', label='Standard Launch', color='#1f77b4', linewidth=2)
    plt.plot(temperatures, override_survival, marker='x', label='Override Active', color='#d62728', linewidth=2, linestyle='--')
    
    # formatting
    plt.title('Vehicle Survival Probability vs. Ambient Temperature', fontsize=14, fontweight='bold')
    plt.xlabel('Ambient Temperature (°C)', fontsize=12)
    plt.ylabel('Survival Probability (%)', fontsize=12)
    
    plt.xticks(temperatures)
    plt.yticks(range(0, 101, 10))
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend(fontsize=11)
    
    # highlight the freezing point
    plt.axvline(x=0, color='gray', linestyle='-', alpha=0.3)
    plt.text(0.2, 50, 'Freezing Point (0°C)', rotation=90, color='gray', alpha=0.7)
    
    plt.tight_layout()
    plt.show()

def generate_post_flight_report(nodes, vehicle_survived, crew_survived):
    print(f"\n{BLUE}=== POST-FLIGHT ANALYSIS REPORT ==={RESET}")
    
    failed_nodes = [node for node in nodes.values() if node.failed]
    
    # three possible outcomes
    if vehicle_survived and crew_survived:
        print(f"{GREEN}MISSION OUTCOME: SUCCESS{RESET}")
        print(f"Total Component Failures: {len(failed_nodes)}")
        if failed_nodes:
            print(f"Non-Critical Failures Logged: {', '.join(n.name for n in failed_nodes)}")
    
    elif not vehicle_survived and crew_survived:
        print(f"{YELLOW}MISSION OUTCOME: ABORT SUCCESSFUL (CREW SAVED, MISSION FAILED){RESET}")
        print(f"Total Components Destroyed Before Abort: {len(failed_nodes)}")
        
    else:
        print(f"{RED}MISSION OUTCOME: LOSS OF VEHICLE (CREW LOST){RESET}")
        print(f"Total Components Destroyed: {len(failed_nodes)}")
        
    # print the cascade chain if anything broke
    if failed_nodes:
        root_causes = [n.name for n in failed_nodes if n.failed_due_to is None]
        
        print(f"\n{YELLOW}--- ROOT CAUSE ANALYSIS ---{RESET}")
        if root_causes:
            print(f"Primary Failure Origin(s): {', '.join(root_causes)}")
        else:
            print("Primary Failure Origin: Undetermined systemic cascade.")
            
        print(f"\n{YELLOW}--- CASCADE CHAIN ---{RESET}")
        for n in failed_nodes:
            if n.failed_due_to:
                print(f" -> {n.name} critically failed due to loss of {n.failed_due_to}")
                
    print(f"{BLUE}==================================={RESET}\n")

def mission_control_feed(temp_c=0, override=True, steps=60):
    print(f"\n{BLUE}=== CAPCOM: INITIATING LAUNCH SEQUENCE ==={RESET}")
    print(f"AMBIENT TEMP: {temp_c}°C | OVERRIDE: {override}\n")
    
    nodes = build_system()
    
    alerted_warnings = set()
    alerted_critical = set()
    
    # track states for the final report
    vehicle_survived = True
    crew_survived = True
    
    for t in range(steps):
        update_system(nodes, temp_c, override, t)
        
        print(f"T+{t:02d}s ", end="", flush=True)
        time.sleep(0.2) # delay
        
        step_events = []
        
        for name, node in nodes.items():
            if node.failed and name not in alerted_critical:
                cause = f" (Cascade from {node.failed_due_to})" if node.failed_due_to else ""
                step_events.append(f"{RED}CRITICAL ALARM: {name} FAILED!{cause}{RESET}")
                alerted_critical.add(name)
            elif not node.failed and node.health < 0.6 and name not in alerted_warnings:
                step_events.append(f"{YELLOW}WARNING: {name} integrity degrading ({node.health*100:.1f}%){RESET}")
                alerted_warnings.add(name)

        if not step_events:
            print(f"{GREEN}NOMINAL{RESET}")
        else:
            print(" | ".join(step_events))

        # --- FLIGHT COMPUTER ABORT LOGIC ---
        # if fire breaches the SRB or power is critically low, pull the plug
        if nodes['Blow-By Erosion'].failed or nodes['Electrical Power'].health < 0.2:
            print(f"\n{YELLOW}!!! MASTER ALARM: CRITICAL CASCADE DETECTED !!!{RESET}")
            print(f"{YELLOW}FLIGHT COMPUTERS: INITIATING EMERGENCY ABORT.{RESET}")
            print(f"{YELLOW}CAPCOM: RTLS ABORT TRIGGERED. SEPARATING ORBITER.{RESET}")
            
            vehicle_survived = False
            crew_survived = True
            break # break the loop to save the crew
            
        # stop the simulation if the vehicle is lost instantly
        if nodes['Vehicle Survival'].failed:
            print(f"\n{RED}=================================================={RESET}")
            print(f"{RED}FLIGHT DYNAMICS OFFICER: WE HAVE LOSS OF VEHICLE.{RESET}")
            print(f"{RED}=================================================={RESET}")
            
            vehicle_survived = False
            crew_survived = False
            break

    # if the loop finishes without breaking, we reached orbit
    if vehicle_survived and crew_survived:
        print(f"\n{GREEN}=================================================={RESET}")
        print(f"{GREEN}CAPCOM: MECO CONFIRMED. VEHICLE HAS REACHED ORBIT.{RESET}")
        print(f"{GREEN}=================================================={RESET}")

    # generate the final report based on how the loop ended
    generate_post_flight_report(nodes, vehicle_survived, crew_survived)
    return vehicle_survived

def main_sim():
    temps = [15, 0, 0]
    overrides = [False, False, True]

    for i in range(3):
        temp = temps[i]
        override = overrides[i]
        
        results = [simulate(temp_c=temp, override=override, steps=60) for _ in range(2000)]
        print(f'Temperature: {temp}°C, Override: {override}')
        print(f'Survival rate: {(sum(results) / len(results)) * 100:.1f}%\n')

if __name__ == '__main__':
    # main_sim()
    # plot_survival_rates()
    mission_control_feed(temp_c=0, override=True, steps=60)
