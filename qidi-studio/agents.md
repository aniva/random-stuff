# QIDI Slicer (Orca Fork) Profile Configuration Guide

## Objective
To programmatically generate or modify custom profiles for QIDI Slicer (based on Orca Slicer/Bambu Studio) to achieve specific print results (e.g., optical transparency) without relying on the GUI.

## File Structure & Locations
All user customizations are stored in the user's configuration directory.

**Windows Path:** `%AppData%\QIDIStudio\user\default\`  
(Note: If logged in, `default` may be replaced by a numeric User ID).

| Profile Type | Directory | File Extension |
| :--- | :--- | :--- |
| **Filament** | `.../user/default/filament/` | `.json` |
| **Process** | `.../user/default/process/` | `.json` |
| **Machine** | `.../user/default/machine/` | `.json` |

---

## Critical Configuration Rules

### 1. Naming & Inheritance (The "Ghost Profile" Fix)
If a profile does not appear in the slicer dropdown, it is usually due to an incorrect `inherits` value or missing IDs.

*   **Process Profiles:**
    *   Must inherit from a system base like `0.20mm Standard @Q2`.
    *   **Crucial:** Do not use `@Qidi Q2` in the inheritance name if the system preset is just `@Q2`.
    *   **ID Key:** Must use `"print_settings_id"`.
    *   **Type:** Must include `"type": "process"`.

*   **Filament Profiles:**
    *   Must inherit from a generic base like `Generic PETG @Qidi Q2 0.4 nozzle`.
    *   **ID Key:** Must use `"filament_settings_id"`.
    *   **Type:** Must include `"type": "filament"`.

### 2. File Format
*   **Filament Values:** Almost always stored as **Arrays of Strings** (e.g., `"nozzle_temperature": ["255"]`).
*   **Process Values:** Mixed. Scalars are strings (e.g., `"layer_height": "0.24"`), but speeds are often arrays (e.g., `"outer_wall_speed": ["20"]`).

---

## Parameter Reference: Filament
*Derived from `Elegoo Rapit PETG Clear (vscode)` profile.*

| JSON Key | Value Type | Description |
| :--- | :--- | :--- |
| `type` | String | Must be `"filament"`. |
| `filament_settings_id` | Array | Unique ID for the profile. |
| `inherits` | String | Parent profile name. |
| `filament_flow_ratio` | Array | Extrusion multiplier (e.g., `"1.05"`). |
| `nozzle_temperature` | Array | Printing temp (e.g., `"255"`). |
| `nozzle_temperature_initial_layer`| Array | First layer temp. |
| `hot_plate_temp` | Array | Bed temp. |
| `fan_min_speed` | Array | Min cooling fan % (e.g., `"0"`). |
| `fan_max_speed` | Array | Max cooling fan % (e.g., `"20"`). |
| `fan_cooling_mode` | Array | `0` = Manual/Always On, `1` = Auto. |
| `filament_max_volumetric_speed` | Array | Flow limit in mm³/s. |
| `filament_retraction_length` | Array | Retraction distance (mm). |
| `filament_retraction_speed` | Array | Retraction speed (mm/s). |
| `filament_deretraction_speed` | Array | Prime speed (mm/s). |
| `filament_z_hop` | Array | Lift Z height (mm). |
| `filament_z_hop_types` | Array | `Slope Lift`, `Spiral Lift`, `Normal`. |
| `filament_wipe` | Array | `1` = On, `0` = Off. |

---

## Parameter Reference: Process (Print Settings)
*Derived from `Optical Clarity (vscode)` and `- test` dump files.*

### Speed & Precision
| JSON Key | Value Type | Description |
| :--- | :--- | :--- |
| `type` | String | Must be `"process"`. |
| `print_settings_id` | String | Unique ID for the profile. |
| `outer_wall_speed` | Array | Outer perimeter speed (mm/s). |
| `inner_wall_speed` | Array | Inner perimeter speed. |
| `internal_solid_infill_speed` | Array | Solid infill speed. |
| `top_surface_speed` | Array | Top layer speed. |
| `travel_speed` | Array | Non-printing movement speed. |
| `max_travel_detour_distance` | String | Limits detour length for "Avoid Crossing Walls". |

### Dimensions & Layers
| JSON Key | Value Type | Description |
| :--- | :--- | :--- |
| `layer_height` | String | Layer height (mm). |
| `line_width` | String | Default line width. |
| `outer_wall_line_width` | String | Width for outer walls. |
| `top_surface_line_width` | String | Width for top surface. |

### Infill & Patterns
| JSON Key | Value Type | Description |
| :--- | :--- | :--- |
| `sparse_infill_density` | String | Infill % (e.g., `"100%"`). |
| `sparse_infill_pattern` | String | `rectilinear`, `gyroid`, `zig-zag`, etc. |
| `internal_solid_infill_pattern` | String | Pattern for solid internal layers. |
| `top_surface_pattern` | String | Pattern for the very top layer. |
| `bottom_surface_pattern` | String | Pattern for the very bottom layer. |
| `reduce_crossing_wall` | String | `1` = Avoid crossing perimeters (reduces stringing). |

### Ironing (Surface Finish)
| JSON Key | Value Type | Description |
| :--- | :--- | :--- |
| `ironing_type` | String | `top`, `all_top`, `no_ironing`. |
| `ironing_speed` | String | Speed for ironing pass. |
| `ironing_flow` | String | Flow % during ironing (e.g., `"10%"`). |
| `ironing_spacing` | String | Space between ironing passes. |

### Walls & Shells
| JSON Key | Value Type | Description |
| :--- | :--- | :--- |
| `wall_loops` | String | Number of wall perimeters. |
| `top_shell_layers` | String | Number of top solid layers. |
| `bottom_shell_layers` | String | Number of bottom solid layers. |
| `seam_position` | String | `nearest`, `aligned`, `back`, `random`. |

---

## Workflow for Agents

1.  **Analyze Context:** Check `inherits` keys in existing files to determine the correct printer base name (e.g., `@Q2` vs `@Qidi Q2`).
2.  **Determine Target:** Decide if parameters belong to Filament (Cooling, Flow, Temp) or Process (Speed, Infill, Layers).
3.  **Create/Edit JSON:**
    *   Use the exact keys listed above.
    *   Ensure proper Type Casting (Arrays vs Strings).
    *   Always verify the `print_settings_id` matches the filename.
4.  **Save Location:**
    *   Filament -> `.../filament/`
    *   Process -> `.../process/`
5.  **Restart Slicer:** QIDI Slicer must be restarted to index new JSON files.

## Example: Transparent PETG Recipe
To achieve glass-like PETG, apply these overrides:

**Filament:**
```json
"fan_min_speed": ["0"],
"fan_max_speed": ["0"],
"fan_cooling_mode": ["0"],
"nozzle_temperature": ["255"]
```

**Process:**
```json
"layer_height": "0.12",
"outer_wall_speed": ["20"],
"inner_wall_speed": ["20"],
"sparse_infill_density": "100%",
"sparse_infill_pattern": "aligned rectilinear",
"reduce_crossing_wall": "1"
```