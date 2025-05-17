
# EAD_testing_v2 Tutorial

This guide provides step-by-step instructions for setting up and running the `EAD_testing_v2` diagram, a simulation framework for Eco-Approach and Departure (EAD) testing using SPaT and MAP messages, GPS data, and an internal velocity planning module.

---

## Project Structure

Key folders and files involved (relative to the project root):

- `EAD_testing_v2.rtd`: RTMaps diagram containing the integrated EAD system
- `DM.py`: Main logic for EAD, generates velocity profiles
- `Map_Matcher.py`: Localizes ego vehicle to lanes and calculates distance to intersection
- `GPS_Generator.py`: Generates GPS trajectories
- `V_c_Generator.py`: Simulates control vehicle velocity
- `test_data_captures/`: Includes PCAP files used for replay
- `MAP_SPAT_Generated/`: Contains generated MAP and SPaT message sets
- `rtmap_v2x/`: Setup dependencies and packages for RTMaps (required before loading `EAD_testing_v2`)
- `Diagrams/`: Contains diagrams such as the AIN state machine used in documentation

---

## Installation & Setup

1. **RTMaps V2X Package Installation**:

   - Before running the diagram, install the required V2X package for RTMaps.
   - A tutorial for installation is included within the repository.
   - Alternatively, use the provided folder `rtmap_v2x/` which contains the necessary RTMaps dependencies and packages.

2. **Python Dependencies**:

   - Install `pyubx2` if using UBX replay:
     ```bash
     pip install pyubx2
     ```
   - Use Visual Studio Code (VSCode) for easier Python debugging.

3. **File Locations**:

   - Ensure all `.py` scripts are in the correct folder paths referenced by RTMaps diagrams.
   - Update GPS file path in `UBX_Player.py` (line 38) to your dataset, e.g.:
     ```python
     filename = "test_data_captures/rawgps.ubx"
     ```

4. **MAP/SPaT Replay**:

   - Use `test_data_captures/capture_data` to simulate MAP and SPaT message replay.
   - You can also forward live messages via OBU scripts like `cw_rsu41_ucr.sh`. A tutorial for live forwarding setup is included in the `rtmap_v2x/` folder.

---

## Running the Simulation

1. **Open** `EAD_testing_v2.rtd` in RTMaps.
2. **Start** the diagram.
   - Make sure each Python or RTMaps component is loaded with the correct local path to the associated script.
3. **Expected Output**:
   - Distance to arrival (from Map Matcher) decreases from ~97m to 0m as vehicle moves.
   - Velocity recommendations will be generated in both m/s and mph.
   - `Engage_signal` activates when EAD is triggered.

---

## Components Overview

### AIN State Machine Integration

The Automated Intersection Navigation (AIN) feature is integrated into the larger Connected and Automated Vehicle (CAV) stack through a state machine. Below is a simplified outline of the state flow:

- **IDLE**: Default state; AIN is inactive and waiting for input.
- **READY_TO_ENGAGE**: AIN has received valid SPaT/MAP and GPS data, matched the vehicle to a lane, and computed a trajectory.
- **ENGAGED**: AIN outputs a velocity profile and sends an `Engage_signal` to the ACC controller.
- **OVERRIDDEN**: AIN is temporarily bypassed (e.g., ACC or brake intervention). It continues monitoring.
- **RECALCULATE**: If the delta between actual speed and recommended speed exceeds a threshold, AIN recomputes the trajectory.
- **DISENGAGED**: AIN is manually or automatically turned off after completing its task or upon system override.

This state machine allows seamless collaboration between AIN, velocity generators, and the broader vehicle control architecture.

### DM (Decision Maker)

- Generates velocity profiles versus time based on signal timing, vehicle state, and distance
- Checks accumulated delta; recomputes if threshold is exceeded
- Outputs time-aligned velocity setpoints

### Map Matcher

- Matches ego vehicle to correct lane using GPS and MAP
- Computes distance to intersection stop line
- Handles edge cases and multiple nodes

### Green Window Estimator

- Calculate current and/or next green window

### GPS & V_c Generators

- Simulate vehicle motion in closed-loop
- Allow for testing acceleration/deceleration behavior

---

## Testing Tips

- Start with static inputs, then test closed-loop with feedback.
- Use `print()` flags in `DM.py` and `Map_Matcher.py` for debugging.
- Save velocity profiles by uncommenting the `TODO` marker  in `DM.py`. The saved profiles will be written to the path defined in that block, which can be modified in the code (default path: `./velocity_profile_output.txt`).

---

## Known Issues & TODOs

- Improve localization across multiple intersections.
- Refactor lane association with signal groups in GWE.
- Immediate forward frequencies for MAP have a ceiling limit based on the map size; exceeding it may corrupt the payload.
- Reduce MAPData size to prevent decoder crashes.
- Merge profile visualization for offline analysis.
- Refactor lane association with signal groups in GWE.
- Reduce MAPData size to prevent decoder crashes.
- Merge profile visualization for offline analysis.

---

## Development Log & Additional Notes

### 3/9/2025

- Updated Map.xpl to remove third lane and add nodes 3 & 4.
- Updated `MapMatcher.py`:
  - Input adjustments (lines 35–59)
  - Optional inputs via `AllowEmptyInput` (line 82)
  - Fixed comment to reference ingress not egress (line 98)
  - Relaxed node count requirements (line 117)
  - Enhanced `get_lane_gps` (line 121)
  - Road link algorithm updated to use first and last nodes (line 123)
  - Fixed heading calculation (line 279)
  - Corrected distance to stop line logic (line 288)

### TODOs (from 3/9)

- Create valid MAPData and GPS files for testing
- Create PythonBridge for MAP/GPS replay
- Refine Eco-Departure logic

### 3/11/2025

- Created PythonBridge using `pyubx2` for GPS replay
- How to run:
  - Install `pyubx2`
  - In `UBX_Player.py`, update path to `rawgps.ubx`
  - Run `ubx_decoding` diagram, verify lat/lon outputs

### 4/11/2025

- Generated MAP/SPaT messages in `MAP_SPAT_Generated/`
- Captured OBU messages via Wireshark (`test_data_captures/`)
- Refined MAP/SPaT decoders and `Map_Matcher`
- Created `GPS_Generator.py` for testing
- Added debug flags in MM for edge cases

### 4/12/2025

- Built and tested `EAD_testing_v2.rtd`
- Validated with `V2X_Test_041225_SPaT_MAP.pcap`
- Verified integration with GWE

### 5/1/2025

- Merged DMSI and DMTG into DM
- Added `Engage_signal` to DM
- Velocity profiles generated and aligned with timestamp
- Auto-recalculation based on velocity delta
- `V_c_Generator` simulates realistic vehicle speeds
- `GPS_Generator` updated for geolocation realism
- Developed EAD-ACC integration state machine

### Additional TODOs

- Improve distance accumulation logic in MapMatcher
- Handle ego localization across multiple intersections
- Associate lane ID with green window phase in GWE

---

## Reference

This project’s algorithm design and implementation are partially based on the GlidePath Prototype framework as detailed in the following paper:

**Altan, O. D., Wu, G., Barth, M. J., Boriboonsomsin, K., & Stark, J. A.** (2017). *GlidePath: Eco-Friendly Automated Approach and Departure at Signalized Intersections*. IEEE Transactions on Intelligent Vehicles, 2(4), 266–277. [DOI: 10.1109/TIV.2017.2767289](https://doi.org/10.1109/TIV.2017.2767289)

A copy of this paper is included in the repository folder for reference: `GlidePath_Eco-Friendly_Automated_Approach_and_Departure_at_Signalized_Intersections.pdf`

Please refer to this document for theoretical background and trajectory planning methods including scenario classification and profile generation.