# QIDI Slicer Agentic Automation Guide

## Objective
To programmatically generate or modify custom configuration profiles for QIDI Slicer (based on Orca Slicer/Bambu Studio) using AI agents without relying on the GUI.

## File Structure & Locations
All user customizations are managed in the local repository and symlinked to the user's Windows AppData directory.

| Profile Type | Repo Directory | File Extension |
| :--- | :--- | :--- |
| **Filament** | `qidi-studio/filament/` | `.json` |
| **Process** | `qidi-studio/process/` | `.json` |
| **Machine** | `qidi-studio/machine/` | `.json` |

---

## 🚨 MANDATORY PROFILE ATTRIBUTES 🚨
For QIDI Studio to successfully recognize and load a new profile, the JSON file **must** contain specific structural metadata. If these are missing or mismatched, the profile will be silently ignored (a "ghost profile").

### 1. Mandatory Process Attributes
A valid process profile must have these exact keys at the root level:

```json
{
  "type": "process",
  "name": "PC Case Structural ABS (vscode) @Q2", 
  "print_settings_id": "PC Case Structural ABS (vscode) @Q2", 
  "from": "User",
  "inherits": "0.20mm Standard @Q2", 
  "is_custom_defined": "0",
  "version": "1.9.0.0",
  "setting_id": "PC Case Structural ABS (vscode) @Q2"
}
```
* **Rule 1:** `name`, `print_settings_id`, and `setting_id` **MUST** exactly match the filename (minus the `.json` extension).
* **Rule 2:** `inherits` **MUST** be an exact string match to an existing system process profile (e.g., do not write `@Qidi Q2` if the system profile is `@Q2`).

### 2. Mandatory Filament Attributes
A valid filament profile requires a slightly different header:

```json
{
  "type": "filament",
  "name": "Overture ABS white (vscode) @Q2",
  "filament_settings_id": ["Overture ABS white (vscode) @Q2"],
  "setting_id": "Overture ABS white (vscode) @Q2",
  "from": "User",
  "inherits": "Generic ABS",
  "is_custom_defined": "0",
  "version": "1.9.0.0"
}
```
* **Rule 3 (The Array Rule):** Almost ALL configuration values inside a `filament` JSON file **MUST** be formatted as arrays of strings. (e.g., `"nozzle_temperature": ["260"]`). 
* **Rule 4:** Process values, conversely, are standard strings (e.g., `"wall_loops": "4"`).

### 3. The Identification Rule
* **Rule 5 (The VSCode Suffix):** To instantly identify AI-generated profiles and prevent conflicts, the file name and all internal ID strings (`name`, `setting_id`, and `print_settings_id` or `filament_settings_id`) MUST ALWAYS end with the exact suffix ` (vscode) @Q2`.
* **Rule 6 (Density Formatting):** Any process variable defining density (such as `sparse_infill_density` or `skin_infill_density`) MUST include the percentage sign within the string (e.g., `"20%"`). 
* **Rule 7 (Active Chamber Heating):** The QIDI Q2 has an active chamber heater. For any high-temperature, warp-prone filament (ABS, ASA, PC, PA), agents MUST leverage this by adding `"chamber_temperatures": ["60"]` to the filament JSON.

---

## Static Enumerations Dictionary
When modifying multi-value attributes in process files, only use the exact strings defined below. 

### Infill Patterns (`sparse_infill_pattern` & `internal_solid_infill_pattern`)
* `"rectilinear"` (Best for internal solid infill/transparency)
* `"grid"`
* `"triangles"`
* `"cubic"` (Best for large structural ABS parts)
* `"stars"`
* `"line"`
* `"concentric"`
* `"honeycomb"`
* `"3dhoneycomb"`
* `"gyroid"` (Excellent all-around strength)
* `"alignedrectilinear"`

### Seam Positions (`seam_position`)
* `"nearest"`
* `"aligned"` (Stacks the seam in a straight vertical line)
* `"back"` (Forces seam to the rear of the build plate)
* `"random"` (Spreads the seam out, good for preventing weak points on round objects)

### Support Types (`support_type`)
* `"normal(auto)"` (Standard grid-based supports)
* `"tree(auto)"` (Organic tree supports, saves material)
* `"normal(manual)"`
* `"tree(manual)"`

### Ironing Types (`ironing_type`)
* `"top_surface"` (Irons only the absolute highest layer)
* `"top"` (Irons all upward-facing flat surfaces)
* `"solid"` (Irons all solid internal layers)
* `"all"` 

---

## 🔍 How to Find Additional Valid Values (Source Code)
If an agent or user needs to configure a multi-value attribute that is not listed in the dictionary above, you can find the exact acceptable string values directly in the open-source QIDI Studio codebase: `https://github.com/QIDITECH/QIDIStudio`.

### 1. The Core Engine Definitions (C++)
The absolute source of truth for the slicing engine is the `PrintConfig` file.
* **File Path:** `src/libslic3r/PrintConfig.cpp`
* **How to Read:** Search the file for the attribute name (e.g., `sparse_infill_pattern`). You will find a configuration block mapping the internal C++ enums directly to the exact JSON strings required.

### 2. The UI Configuration Schema (JSON)
For a machine-readable format mapping what the UI dropdown menus allow:
* **File Path:** `resources/data/config.json` (or `print_settings.json` / `config_def.json`).
* **How to Read:** Search for the attribute name. Look for an `"enum_values"` or `"options"` array, which lists exactly what the software expects (e.g., `["nearest", "aligned", "back", "random"]`).

---
## Build Plate Mapping
Specific physical build plates are used for different material families. When an agent creates or modifies a filament profile, it MUST assign the target temperature to the correct plate JSON attribute.

* **ABS / ASA:** Printed on the **Q2 Dual Sided Smooth Plate**.
  * JSON Attributes to set: `hot_plate_temp` and `hot_plate_temp_initial_layer`
* **PLA / PETG:** Printed on the **Qidi Cool Plate Pro**.
  * JSON Attributes to set: `cool_plate_temp` and `cool_plate_temp_initial_layer`
* **General / Fallback:** Stock Textured PEI plate.
  * JSON Attributes to set: `textured_plate_temp` and `textured_plate_temp_initial_layer`

```json
"eng_plate_temp": ["100"],
"eng_plate_temp_initial_layer": ["100"],
"cool_plate_temp": ["0"],
"cool_plate_temp_initial_layer": ["0"]
```

## Example Overrides

### 1. Structural ABS (For Process JSON)
Used for large, warp-prone structural parts like PC cases.
```json
"wall_loops": "4",
"top_shell_layers": "5",
"bottom_shell_layers": "5",
"sparse_infill_density": "40",
"sparse_infill_pattern": "cubic"
```

### 2. Clear "Glass" PETG (For Filament JSON)
Used for optical transparency (requires 0% fan and slow speeds).
```json
"nozzle_temperature": ["255"],
"nozzle_temperature_initial_layer": ["255"],
"fan_min_speed": ["0"],
"fan_max_speed": ["20"],
"fan_cooling_mode": ["0"],
"nozzle_flow_ratio": ["1.05"]
```

---
*Author: Aniva*