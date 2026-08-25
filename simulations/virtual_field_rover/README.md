# Virtual Field Rover — Public-Safe Digital Farm

Synthetic-only environmental rover simulation for ASA/AOIP development.

## Flexible farm design

- Modular layout so storage, rover dock, irrigation areas, and decorative elements can be rearranged without changing the safety model.
- Distributed storage instead of one central cabinet.
- Protected storage is integrated with the decor, restricted to authorized access, and explicitly excludes hazardous materials.
- Rover dock is weather-protected in the simulation and cannot dispatch the rover autonomously.
- Utility routes are represented as integrated with the decor rather than left visually exposed.

## Resilience modes

The synthetic monitor now chooses a fail-safe operating mode on every cycle:

- `NORMAL` — network, battery, and sensor health are sufficient.
- `LOCAL_FALLBACK` — network is unavailable; local rules continue without an external AI call.
- `ENERGY_SAVER` — synthetic battery is low.
- `DEGRADED_SENSOR` — too few valid sensors are available.
- `PRIVACY_YIELD` — synthetic human presence is generated in the open-area zone.

These modes are decision-support states only. They do not start pumps, move vehicles, unlock storage, or operate physical equipment.

## OpenAI advisory boundary

The simulation emits an `ai_advisory_contract` that is compatible with a future approved OpenAI decision-support path. The current public simulation does **not** call OpenAI, does not send farm data externally, and does not allow AI to control locks, machinery, irrigation, drones, or the rover. Any future provider connection must use approved data scope, environment-backed secrets, and human verification.

## Safety and evidence boundary

- No real farm coordinates, credentials, company data, customer data, or personal data.
- No facial recognition, person tracking, covert observation, or conversation recording.
- Open-area simulation uses `PRIVACY_YIELD` when synthetic human presence is generated.
- No physical actuation: the code never starts pumps, vehicles, valves, drones, or machinery.
- Ground-truth incident identifiers and synthetic human-presence flags are kept outside evidence payloads.
- Evidence and ASA/AOIP gateway records use local SHA-256 hash chains.
- `real_farm_connected=false` is an explicit invariant of this public repository module.
- `openai_advisory.external_call_made=false` is an explicit invariant of this simulation.

## Run

```bash
cd simulations/virtual_field_rover
python -m unittest -v test_monitor.py
python monitor.py --cycles 500 --summary runtime/summary.json
```

The scheduled GitHub workflow is a **bounded synthetic monitor**, not a real-farm deployment or a 24/7 service. A real farm requires an authorized edge device or server, approved network path, and explicitly approved sensor adapters; none are configured here.
