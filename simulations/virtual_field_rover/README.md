# Virtual Field Rover — Public-Safe Digital Farm

Synthetic-only environmental rover simulation for ASA/AOIP development.

## Safety and evidence boundary

- No real farm coordinates, credentials, company data, customer data, or personal data.
- No facial recognition, person tracking, covert observation, or conversation recording.
- Open-area simulation uses `PRIVACY_YIELD` when synthetic human presence is generated.
- No physical actuation: the code never starts pumps, vehicles, valves, drones, or machinery.
- Ground-truth incident identifiers and synthetic human-presence flags are kept outside evidence payloads.
- Evidence and ASA/AOIP gateway records use local SHA-256 hash chains.
- `real_farm_connected=false` is an explicit invariant of this public repository module.

## Run

```bash
cd simulations/virtual_field_rover
python -m unittest -v test_monitor.py
python monitor.py --cycles 500 --summary runtime/summary.json
```

The scheduled GitHub workflow is a **bounded synthetic monitor**, not a real-farm deployment or a 24/7 service. A real farm requires an authorized edge device or server, approved network path, and explicitly approved sensor adapters; none are configured here.
