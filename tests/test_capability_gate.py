from app.capability_gate import CapabilityGate, GateState, operational


def test_gate_blocks_when_capability_is_unavailable() -> None:
    gate = CapabilityGate(False, False, False, False, False, False, False)
    assert gate.evaluate() is GateState.BLOCKED
    assert not operational(gate)


def test_gate_stops_at_first_missing_control() -> None:
    gate = CapabilityGate(True, True, True, True, True, False, False)
    assert gate.evaluate() is GateState.EXECUTED
    assert not operational(gate)


def test_gate_requires_evidence_before_operational() -> None:
    gate = CapabilityGate(True, True, True, True, True, True, False)
    assert gate.evaluate() is GateState.TESTED
    assert not operational(gate)


def test_gate_reaches_operational_only_when_all_controls_pass() -> None:
    gate = CapabilityGate(True, True, True, True, True, True, True)
    assert gate.evaluate() is GateState.OPERATIONAL
    assert operational(gate)
