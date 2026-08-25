from __future__ import annotations

import asyncio
import hmac
import json
import os
import re
from contextlib import asynccontextmanager
from typing import Literal

from agents import Agent, ModelSettings, RunConfig, Runner
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, model_validator

from .capability_gate import CapabilityGate, GateState

_MIN_API_TOKEN_LENGTH = 32
_DEFAULT_MODEL = "gpt-5.6-sol"
_DEFAULT_AI_TIMEOUT_SECONDS = 30.0
_DEFAULT_AI_QUEUE_TIMEOUT_SECONDS = 1.0
_DEFAULT_AI_MAX_CONCURRENCY = 2
_MAX_AI_MAX_CONCURRENCY = 4

FarmStatus = Literal["normal", "watch", "attention"]
Connectivity = Literal["online", "degraded", "offline"]
DataOrigin = Literal["synthetic", "public"]


class FarmPolicy(BaseModel):
    """Configurable pre-pilot monitoring thresholds.

    These are generic monitoring defaults, not crop-specific agronomic limits.
    A real pilot should replace them with approved site/crop-specific values.
    """

    temperature_min_c: float = Field(default=5.0, ge=-20.0, le=70.0)
    temperature_max_c: float = Field(default=45.0, ge=-20.0, le=70.0)
    humidity_min_pct: float = Field(default=20.0, ge=0.0, le=100.0)
    humidity_max_pct: float = Field(default=90.0, ge=0.0, le=100.0)
    soil_moisture_min_pct: float = Field(default=20.0, ge=0.0, le=100.0)
    soil_moisture_max_pct: float = Field(default=85.0, ge=0.0, le=100.0)
    battery_watch_pct: float = Field(default=35.0, ge=0.0, le=100.0)
    battery_attention_pct: float = Field(default=15.0, ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_ranges(self) -> "FarmPolicy":
        if self.temperature_min_c >= self.temperature_max_c:
            raise ValueError("temperature_min_c must be lower than temperature_max_c")
        if self.humidity_min_pct >= self.humidity_max_pct:
            raise ValueError("humidity_min_pct must be lower than humidity_max_pct")
        if self.soil_moisture_min_pct >= self.soil_moisture_max_pct:
            raise ValueError("soil_moisture_min_pct must be lower than soil_moisture_max_pct")
        if self.battery_attention_pct >= self.battery_watch_pct:
            raise ValueError("battery_attention_pct must be lower than battery_watch_pct")
        return self


class FarmObservationRequest(BaseModel):
    temperature_c: float = Field(ge=-20.0, le=70.0)
    humidity_pct: float = Field(ge=0.0, le=100.0)
    soil_moisture_pct: float = Field(ge=0.0, le=100.0)
    battery_pct: float = Field(ge=0.0, le=100.0)
    connectivity: Connectivity = "online"
    data_origin: DataOrigin = "synthetic"
    policy: FarmPolicy = Field(default_factory=FarmPolicy)


class FarmAssessmentResponse(BaseModel):
    status: FarmStatus
    alerts: list[str] = Field(default_factory=list, max_length=12)
    advisory: list[str] = Field(default_factory=list, max_length=12)
    recommended_data_mode: Literal["live", "degraded_sync", "buffer_locally_then_sync"]
    control_mode: Literal["monitor_only"] = "monitor_only"
    external_actuation: Literal[False] = False
    telemetry_storage: Literal["not_implemented"] = "not_implemented"


class FarmAIOutput(BaseModel):
    status: FarmStatus
    advisory: str = Field(min_length=1, max_length=1500)
    priority_actions: list[str] = Field(default_factory=list, max_length=5)


class FarmAIAssessmentResponse(FarmAssessmentResponse):
    ai_advisory: str
    priority_actions: list[str] = Field(default_factory=list, max_length=5)
    model: str


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _bounded_float_env(name: str, default: float, minimum: float, maximum: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=f"Invalid {name} configuration") from exc
    if not minimum <= value <= maximum:
        raise HTTPException(
            status_code=503,
            detail=f"{name} must be between {minimum} and {maximum}",
        )
    return value


def _ai_timeout_seconds() -> float:
    return _bounded_float_env(
        "SMART_FARM_OPENAI_TIMEOUT_SECONDS",
        _DEFAULT_AI_TIMEOUT_SECONDS,
        0.05,
        60.0,
    )


def _ai_queue_timeout_seconds() -> float:
    return _bounded_float_env(
        "SMART_FARM_OPENAI_QUEUE_TIMEOUT_SECONDS",
        _DEFAULT_AI_QUEUE_TIMEOUT_SECONDS,
        0.05,
        5.0,
    )


def _ai_max_concurrency() -> int:
    raw = os.getenv("SMART_FARM_OPENAI_MAX_CONCURRENCY")
    if raw is None:
        return _DEFAULT_AI_MAX_CONCURRENCY
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError("Invalid SMART_FARM_OPENAI_MAX_CONCURRENCY configuration") from exc
    if not 1 <= value <= _MAX_AI_MAX_CONCURRENCY:
        raise RuntimeError(
            "SMART_FARM_OPENAI_MAX_CONCURRENCY must be between "
            f"1 and {_MAX_AI_MAX_CONCURRENCY}"
        )
    return value


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    app_instance.state.ai_provider_semaphore = asyncio.Semaphore(_ai_max_concurrency())
    yield


app = FastAPI(
    title="ASA Smart Farm AI",
    version="0.1.0",
    description=(
        "Pre-pilot smart-farm monitoring and advisory service. "
        "Monitoring only; no physical actuation or production control."
    ),
    lifespan=lifespan,
)


def require_api_auth(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("ASA_API_BEARER_TOKEN", "")
    if len(expected) < _MIN_API_TOKEN_LENGTH:
        raise HTTPException(status_code=503, detail="API authentication is not securely configured")

    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supplied = authorization[len(prefix) :].strip()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credential",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _runtime_gate() -> CapabilityGate:
    return CapabilityGate(
        available=_env_flag("ASA_GATE_AVAILABLE"),
        eligible=_env_flag("ASA_GATE_ELIGIBLE"),
        authorized=_env_flag("ASA_GATE_AUTHORIZED"),
        connected=_env_flag("ASA_GATE_CONNECTED"),
        executed=_env_flag("ASA_GATE_EXECUTED"),
        tested=_env_flag("ASA_GATE_TESTED"),
        evidenced=_env_flag("ASA_GATE_EVIDENCED"),
    )


def _model_name() -> str:
    model = os.getenv(
        "SMART_FARM_OPENAI_MODEL",
        os.getenv("ASA_OPENAI_MODEL", _DEFAULT_MODEL),
    ).strip()
    if not re.fullmatch(r"[A-Za-z0-9._:-]{2,80}", model):
        raise HTTPException(status_code=503, detail="Invalid OpenAI model configuration")
    return model


def _require_ai_runtime() -> None:
    gate_state = _runtime_gate().evaluate()
    if gate_state is not GateState.OPERATIONAL:
        raise HTTPException(status_code=503, detail=f"Capability gate: {gate_state.value}")
    if not _env_flag("SMART_FARM_OPENAI_ENABLED", default=False):
        raise HTTPException(status_code=503, detail="Smart Farm OpenAI path is disabled")
    if not _env_flag("ASA_OPENAI_DATA_TERMS_CONFIRMED", default=False):
        raise HTTPException(status_code=503, detail="OpenAI data-terms confirmation gate is closed")
    if len(os.getenv("OPENAI_API_KEY", "").strip()) < 20:
        raise HTTPException(status_code=503, detail="OpenAI API authentication is not configured")


def _status_rank(value: FarmStatus) -> int:
    return {"normal": 0, "watch": 1, "attention": 2}[value]


def _evaluate(payload: FarmObservationRequest) -> FarmAssessmentResponse:
    policy = payload.policy
    alerts: list[str] = []
    advisory: list[str] = []
    severity = 0

    if not policy.temperature_min_c <= payload.temperature_c <= policy.temperature_max_c:
        alerts.append("temperature_outside_selected_range")
        advisory.append("Verify the temperature sensor and inspect the environment manually.")
        severity = max(severity, 1)

    if not policy.humidity_min_pct <= payload.humidity_pct <= policy.humidity_max_pct:
        alerts.append("humidity_outside_selected_range")
        advisory.append("Verify the humidity sensor and inspect the environment manually.")
        severity = max(severity, 1)

    if not policy.soil_moisture_min_pct <= payload.soil_moisture_pct <= policy.soil_moisture_max_pct:
        alerts.append("soil_moisture_outside_selected_range")
        advisory.append("Verify the soil-moisture reading before changing any equipment settings.")
        severity = max(severity, 1)

    if payload.battery_pct <= policy.battery_attention_pct:
        alerts.append("battery_critical_for_monitoring")
        advisory.append("Prioritize safe charging or a manual inspection of the monitoring unit.")
        severity = 2
    elif payload.battery_pct <= policy.battery_watch_pct:
        alerts.append("battery_low_for_monitoring")
        advisory.append("Plan charging and reduce nonessential monitoring workload if supported locally.")
        severity = max(severity, 1)

    if payload.connectivity == "offline":
        alerts.append("connectivity_offline")
        advisory.append("Keep decisions local and queue telemetry for later synchronization if local storage exists.")
        severity = 2
        data_mode: Literal["live", "degraded_sync", "buffer_locally_then_sync"] = "buffer_locally_then_sync"
    elif payload.connectivity == "degraded":
        alerts.append("connectivity_degraded")
        advisory.append("Prefer local monitoring and delayed synchronization until connectivity is stable.")
        severity = max(severity, 1)
        data_mode = "degraded_sync"
    else:
        data_mode = "live"

    status: FarmStatus = ("normal", "watch", "attention")[severity]
    if not advisory:
        advisory.append("Readings are inside the selected pre-pilot monitoring ranges.")

    return FarmAssessmentResponse(
        status=status,
        alerts=alerts,
        advisory=advisory,
        recommended_data_mode=data_mode,
    )


def _build_agent(model: str) -> Agent:
    return Agent(
        name="ASA Smart Farm Advisory Agent",
        instructions=(
            "You are a monitoring-only smart-farm advisory agent for a Discovery / Pre-Pilot system. "
            "Use only the structured observation, policy, deterministic status, and alerts supplied. "
            "Do not invent sensor readings, crop requirements, or actions already performed. "
            "Never issue or recommend autonomous commands to motors, pumps, valves, locks, doors, "
            "drones, vehicles, lasers, or other physical actuators. Do not provide concealment or "
            "surveillance guidance. Recommend only safe observation, verification, maintenance, "
            "manual inspection, data-quality checks, and escalation when needed. "
            "Do not downgrade a deterministic safety status. Keep advice concise."
        ),
        model=model,
        output_type=FarmAIOutput,
        model_settings=ModelSettings(
            store=False,
            parallel_tool_calls=False,
            max_tokens=700,
            verbosity="low",
        ),
    )


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "asa-smart-farm-ai",
        "control_mode": "monitor_only",
        "external_actuation": False,
        "ai_enabled": _env_flag("SMART_FARM_OPENAI_ENABLED", default=False),
    }


@app.post(
    "/api/v1/farm/observe",
    response_model=FarmAssessmentResponse,
    dependencies=[Depends(require_api_auth)],
)
def observe(payload: FarmObservationRequest) -> FarmAssessmentResponse:
    """Deterministic, local-first monitoring assessment. No OpenAI call is made."""
    return _evaluate(payload)


@app.post(
    "/api/v1/farm/ai-assess",
    response_model=FarmAIAssessmentResponse,
    dependencies=[Depends(require_api_auth)],
)
async def ai_assess(payload: FarmObservationRequest) -> FarmAIAssessmentResponse:
    """Optional AI advisory over public/synthetic monitoring data only."""
    _require_ai_runtime()
    deterministic = _evaluate(payload)
    model = _model_name()
    agent = _build_agent(model)

    packet = {
        "observation": {
            "temperature_c": payload.temperature_c,
            "humidity_pct": payload.humidity_pct,
            "soil_moisture_pct": payload.soil_moisture_pct,
            "battery_pct": payload.battery_pct,
            "connectivity": payload.connectivity,
            "data_origin": payload.data_origin,
        },
        "policy": payload.policy.model_dump(),
        "deterministic_status": deterministic.status,
        "alerts": deterministic.alerts,
        "constraints": {
            "control_mode": "monitor_only",
            "external_actuation": False,
            "telemetry_storage": "not_implemented",
        },
    }
    prompt = json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    semaphore = getattr(app.state, "ai_provider_semaphore", None)
    if semaphore is None:
        raise HTTPException(status_code=503, detail="AI provider concurrency gate is unavailable")

    try:
        await asyncio.wait_for(semaphore.acquire(), timeout=_ai_queue_timeout_seconds())
    except TimeoutError as exc:
        raise HTTPException(status_code=503, detail="AI provider concurrency limit reached") from exc

    try:
        try:
            result = await asyncio.wait_for(
                Runner.run(
                    agent,
                    prompt,
                    run_config=RunConfig(
                        tracing_disabled=True,
                        trace_include_sensitive_data=False,
                    ),
                ),
                timeout=_ai_timeout_seconds(),
            )
            output = result.final_output
            if not isinstance(output, FarmAIOutput):
                output = FarmAIOutput.model_validate(output)
        except TimeoutError as exc:
            raise HTTPException(status_code=504, detail="OpenAI smart-farm request timed out") from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail="OpenAI smart-farm request failed") from exc
    finally:
        semaphore.release()

    final_status = output.status
    if _status_rank(final_status) < _status_rank(deterministic.status):
        final_status = deterministic.status

    return FarmAIAssessmentResponse(
        status=final_status,
        alerts=deterministic.alerts,
        advisory=deterministic.advisory,
        recommended_data_mode=deterministic.recommended_data_mode,
        ai_advisory=output.advisory,
        priority_actions=output.priority_actions,
        model=model,
    )
