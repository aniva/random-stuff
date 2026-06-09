# Chamber Light Auto-On Customization

## Problem
Newer QIDI firmware/software updates automatically turn off the chamber light when a print finishes. This makes it difficult to see the finished print on the build plate.

## Solution
We modified the custom printer profile [Q2 0.4 nozzle 01.json](file:///wsl.localhost/Ubuntu/home/me/repos/random-stuff/qidi-studio/machine/Q2%200.4%20nozzle%2001.json) to override the default `machine_end_gcode`. 

The override sequence runs the exact Klipper commands to:
1. Complete the standard print ending steps (turning off heaters, unloading filament, parking head).
2. Explicitly force the chamber light back on via the Klipper command `SET_PIN PIN=caselight VALUE=1`.

## Modification Details

The `machine_end_gcode` was set as follows:
```gcode
DISABLE_BOX_HEATER
M141 S0
M140 S0
BUFFER_MONITORING ENABLE=0
DISABLE_ALL_SENSOR
G1 E-3 F1800
G0 Z{max_layer_z + 3} F600
UNLOAD_FILAMENT T=[current_extruder]
G0 Y270 F12000
G0 X90 Y270 F12000
{if max_layer_z < max_print_height / 2}G1 Z{max_print_height / 2 + 10} F600{else}G1 Z{min(max_print_height, max_layer_z + 3)}{endif}
M104 S0
SET_PIN PIN=caselight VALUE=1
```

## How to Apply Changes
1. **Restart QIDI Studio:** Since QIDI Studio automatically picks up changes to symbolic-linked user profiles on startup, simply close and reopen QIDI Studio.
2. **Select the Profile:** Ensure you are using the custom profile **`Q2 0.4 nozzle 01`** when slicing.
3. **Verify:** Slice a model and verify in the G-code preview (or test print) that `SET_PIN PIN=caselight VALUE=1` appears at the end of the file.
