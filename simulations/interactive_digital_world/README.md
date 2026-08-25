# Interactive Digital World

A public-safe, simulation-only interactive environment for ASA/AOIP internal testing.

## What is implemented

- persistent JSON world state across process restarts;
- 20x20 logical world with a controllable virtual rover;
- manual movement, turning, stop, and bounded auto-patrol;
- virtual light, sensors, irrigation, battery, ambient light, soil moisture, plant health, and virtual pathogen-risk state;
- causal world evolution: commands change world state and later sensor observations reflect those changes;
- reliability-aware smart perception with evidence-conflict detection, confidence, risk, and human-approval escalation;
- SHA-256 hash-chained command/observation evidence;
- local FastAPI control API and browser-based 2D remote dashboard;
- governed synthetic/draft snapshot bridge into the ASA/AOIP knowledge API.

## Safety / evidence boundary

`Internal Test Only` and `simulation_only=true` are mandatory. This module does **not** connect to a real farm, warehouse, street, factory, camera, sensor, actuator, robot, or person. Physical actuation, person tracking, facial recognition, covert monitoring, and real-world action are disabled/not implemented.

`virtual_pathogen_risk` is a state inside the digital world. It is not a medical, agricultural, microbiological, or field diagnosis.

## Run locally

```bash
cd simulations/interactive_digital_world
python -m unittest discover -v
python world.py --ticks 90 --summary runtime/snapshot.json
uvicorn api:app --host 127.0.0.1 --port 8767
```

Then open `http://127.0.0.1:8767/` for the interactive remote.

Runtime state/evidence is generated locally and must not be committed as project evidence without the applicable review and classification.
