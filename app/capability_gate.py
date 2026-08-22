from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GateState(str, Enum):
    DISCOVERED = "Discovered"
    AVAILABLE = "Available"
    ELIGIBLE = "Eligible"
    AUTHORIZED = "Authorized"
    CONNECTED = "Connected"
    EXECUTED = "Executed"
    TESTED = "Tested"
    EVIDENCED = "Evidenced"
    OPERATIONAL = "Operational"
    BLOCKED = "Blocked"


@dataclass(frozen=True)
class CapabilityGate:
    available: bool
    eligible: bool
    authorized: bool
    connected: bool
    executed: bool
    tested: bool
    evidenced: bool

    def evaluate(self) -> GateState:
        checks = (
            (self.available, GateState.AVAILABLE),
            (self.eligible, GateState.ELIGIBLE),
            (self.authorized, GateState.AUTHORIZED),
            (self.connected, GateState.CONNECTED),
            (self.executed, GateState.EXECUTED),
            (self.tested, GateState.TESTED),
            (self.evidenced, GateState.EVIDENCED),
        )
        reached = GateState.DISCOVERED
        for passed, state in checks:
            if not passed:
                return reached if reached != GateState.DISCOVERED else GateState.BLOCKED
            reached = state
        return GateState.OPERATIONAL


def operational(gate: CapabilityGate) -> bool:
    return gate.evaluate() is GateState.OPERATIONAL
