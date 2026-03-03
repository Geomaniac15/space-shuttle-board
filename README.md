Challenger O-Ring Failure Simulator
-----------------------------------

A physical and software simulation of the Space Shuttle Challenger SRB O-ring failure risk, designed to demonstrate how environmental and engineering factors propagate through a system and lead to catastrophic failure.

The project models relationships between temperature, structural behaviour, seal performance, and vehicle survival using a simplified probabilistic system inspired by the real engineering analysis of the 1986 Challenger disaster.

The output is visualised through LED indicators showing whether the simulated shuttle survives or fails under given launch conditions.


Overview
--------

The Challenger disaster occurred on 28 January 1986 when the Space Shuttle broke apart 73 seconds after launch due to failure in the Solid Rocket Booster (SRB) field joint O-rings.

Low ambient temperatures caused the rubber O-rings to lose elasticity, preventing them from sealing the booster joint properly. Hot combustion gases escaped, leading to structural failure of the external tank and vehicle breakup.

This project simulates the chain of dependencies that influence that failure.

Instead of a single rule, the system models a network of engineering variables where each influences the next.

The result is a probabilistic estimate of vehicle survival.


System Architecture
-------------------

The simulation is built around 20 system nodes representing different engineering or environmental variables.

Examples include:
- Ambient temperature
- Sensor accuracy
- Launch pressure
- SRB internal temperature
- Field joint O-ring resilience
- Joint rotation
- Blow-by erosion
- External tank integrity
- Aerodynamic stress
- Vehicle survival

Each node contributes probabilistically to the next stage of the system.

The final node outputs the probability of vehicle survival.


Node Network
------------

The simulation includes the following nodes:

``` bash
Ambient Temperature
Sensor Accuracy
Launch Pressure
SRB Internal Temperature
SRB Case Integrity
Field Joint O-Ring Resilience
Joint Rotation
Primary O-Ring Seal
Secondary O-Ring Seal
Blow-By Erosion
Flame Impingement
External Tank Integrity
LH2 Tank Breach
Intertank Structure
Structural Load Distribution
Electrical Power
Flight Control System
Aerodynamic Stress
Ice Formation Risk
Vehicle Survival
```

Hardware
--------

The physical build uses:

- Microcontroller (ESP32 or Arduino compatible board)
- Addressable LEDs (WS2812 / FastLED)
- Push button for launch trigger
- Power supply
- Optional display panel

LED states represent the outcome:

- Green  : Vehicle survives
- Orange : Risk detected
- Red    : Catastrophic failure
- Blue   : System idle / awaiting launch


Software
--------

The system software performs the following steps:

1. Read environmental inputs (temperature and override flags)
2. Calculate system probabilities
3. Propagate values through the node network
4. Compute final vehicle survival probability
5. Trigger LED output

The simulation includes a temperature-based penalty system reflecting the behaviour of SRB O-rings.

Example behaviour:

- Temperature 15°C  -> ~95–99% survival probability
- Temperature 5°C   -> Moderate risk
- Temperature 0°C   -> High failure probability
- 0°C with override -> Very high failure probability


Simulation Mode
---------------

A Python/Pygame simulation was also developed to visualise the node network before deploying to hardware.

This allows:
- Testing probability behaviour
- Visualising node dependencies
- Adjusting coefficients
- Debugging the model


Launch Sequence
---------------

1. System boots
2. LEDs indicate idle state
3. Environmental conditions are set
4. Launch button is pressed
5. Survival probability is calculated
6. LED outcome is displayed


Purpose
-------

This project demonstrates several concepts:

- Systems engineering
- Failure propagation
- Probabilistic modelling
- Human decision risk
- Physical computing
- Engineering ethics

It illustrates how complex engineering failures rarely come from a single cause, but instead emerge from interacting systems and environmental conditions.


Future Improvements
-------------------

Potential extensions include:

- Bayesian network modelling
- Real-time parameter adjustment
- Graphical interface
- Telemetry display
- Historical launch condition presets
- Multiple SRB joint modelling


Inspiration
-----------

- NASA Rogers Commission Report
- Truth, Lies, and O-Rings – Allan J. McDonald
- Historical SRB engineering analysis


Disclaimer
----------

This project is an educational simulation and not an exact engineering reproduction of the Space Shuttle SRB system.

The real vehicle involved thousands of interacting variables far beyond the scope of this model.


Author
------

George
