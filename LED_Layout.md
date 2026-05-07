**SRB chain** (right side of the image, on/near the SRB body)

| Node | Placement |
|---|---|
| Field Joint O-Ring Resilience | The aft field joint, roughly 2/3 down the SRB where the casing segments meet |
| Joint Rotation | Just above Field Joint, same segment boundary |
| Primary O-Ring Seal | Overlapping the same joint, maybe 5mm above Joint Rotation |
| Secondary O-Ring Seal | Same cluster, 5mm above Primary |
| SRB Internal Temperature | Mid-body of the SRB, inward from the seals |
| SRB Case Integrity | Upper third of the SRB body |
| Blow-By Erosion | Below the field joint, where combustion gas would escape |
| Flame Impingement | Bottom of the SRB, near the nozzle exit, where the plume hits the ET strut |

**Tank + structure** (on the external tank, centre of the image)

| Node | Placement |
|---|---|
| External Tank Integrity | On the ET body, just left of where the SRB flame would hit it |
| LH2 Tank Breach | Lower half of the ET (the LH2 tank occupies the bottom ~2/3) |
| Intertank Structure | The band/section visually separating the upper LOX dome from the lower LH2 tank |
| Structural Load Distribution | The orbiter-ET attach strut area, where the orbiter meets the tank |
| Vehicle Survival | Dead centre of the whole vehicle, or on the orbiter fuselage |

**Aero + control** (on the orbiter)

| Node | Placement |
|---|---|
| Electrical Power | Aft fuselage of the orbiter, near the engines |
| Flight Control System | Mid-fuselage / avionics bay |
| Aerodynamic Stress | The nose or leading wing edge of the orbiter |
| Ice Formation Risk | On the ET surface, upper section, where ice was visible pre-launch |

**Context / exogenous** (margins or base of the poster)

| Node | Placement |
|---|---|
| Ambient Temperature | Bottom corner, outside the vehicle entirely |
| Sensor Accuracy | Near the base of the ET, where the pressure sensors sit |
| Launch Pressure | Bottom corner, outside the vehicle |

The SRB seal cluster (Field Joint through Blow-By) can realistically be 5 LEDs within a 3cm strip since they're all at the same physical joint. 

Update the `LED_MAP` array in the `.ino` once LEDs placed.