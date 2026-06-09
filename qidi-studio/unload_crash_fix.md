# Filament Unload Crash Fix

## Problem
When using the printer with an external spool (mounted on the back **Rack**), the active slot variable in Klipper is set to `slot-1` (or `-1` internally). 

If you attempt to run the unload filament sequence from QIDI Studio (the "Device" tab) or via screen controls, QIDI Studio sends the Klipper command:
```gcode
E_UNLOAD slot=3  # or another slot number
```
The compiled Klipper C-extension (`box_extras.so`) intercepts this command via its `button_extruder_unload` method. Instead of using the requested slot, it queries the currently active toolhead slot. Since the active slot is `-1` (no Box slot is active), Klipper attempts to look up a config object named `'-1'`. Because no config object named `'-1'` exists in `printer.cfg`, Klipper raises a fatal configuration exception:
```
configparser.Error: Unknown config object '-1'
```
This causes Klipper to shut down immediately, turning off heaters and halting the printer.

---

## Solution
We modified the printer's [box.cfg](file:///wsl.localhost/Ubuntu/home/me/repos/random-stuff/qidi-studio/printer_config/box.cfg) file to intercept the `E_UNLOAD` command using a Klipper G-code macro wrapper:

```klipper
[gcode_macro E_UNLOAD]
rename_existing: BASE_E_UNLOAD
gcode:
    {% set active_slot = printer.save_variables.variables.slot_sync|default("slot-1") %}
    {% if active_slot == "slot-1" %}
        M118 Active slot is slot-1 (Rack/External). Intercepting E_UNLOAD to prevent Klipper crash.
        # Run the safe manual cutter and retraction sequence
        CUT_FILAMENT_1
        MOVE_TO_TRASH
        G92 E0 
        G1 E-60 F300
    {% else %}
        BASE_E_UNLOAD {% for p in params %}{'%s=%s ' % (p, params[p])}{% endfor %}
    {% endif %}
```

### How it works:
1. **Safety Check:** The macro checks Klipper's saved variable `slot_sync` (which tracks the active slot).
2. **External Spool (Rack) Active:** If the active slot is `slot-1` (meaning you are printing from the external spool), the macro bypasses the buggy compiled `BASE_E_UNLOAD` command. Instead, it directly runs the manual cut and retract commands (`CUT_FILAMENT_1`, `MOVE_TO_TRASH`, `G1 E-60 F300`). This unloads the filament successfully without crashing Klipper.
3. **Box Spool Active:** If any valid Box slot is active (e.g. `slot0` through `slot3`), the macro passes the command along to the original compiled `BASE_E_UNLOAD` handler to process the Box rewind sequence normally.

---

## How to Apply and Verify
1. **Deploy to Printer:**
   Upload the modified `box.cfg` back to the printer and restart Klipper by running:
   ```bash
   python qidi-studio/scripts/sync_printer.py push
   ```
2. **Verify:**
   * Make sure your printer is using the external Rack (active slot is `-1` / `slot-1`).
   * Press **UNLOAD** in QIDI Studio or from the screen.
   * The printer should safely execute the cut and retraction sequence, printing a message to the console:
     `Active slot is slot-1 (Rack/External). Intercepting E_UNLOAD to prevent Klipper crash.`
   * The printer will remain online and will NOT throw the "Unknown config object" error anymore.
