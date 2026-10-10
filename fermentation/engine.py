"""Cocoa fermentation domain model; no persistence, secrets, or hardware dependencies.

SPDX-License-Identifier: AGPL-3.0-or-later
This is new CocoaCraft code, designed to coexist with the retained Artisan source.
"""
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_DURATION_HOURS = 336  # 14 days; configurable process plans must fit this envelope.


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class TargetPoint(StrictModel):
    hour: float = Field(ge=0, le=MAX_DURATION_HOURS)
    minimum_c: float = Field(ge=-10, le=90)
    maximum_c: float = Field(ge=-10, le=90)

    @model_validator(mode="after")
    def ordered_limits(self):
        if self.minimum_c > self.maximum_c:
            raise ValueError("Minimum temperature cannot exceed maximum")
        return self


class FermentationProfile(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    supplier_id: UUID
    name: str = Field(min_length=1, max_length=160)
    status: Literal["draft", "approved", "archived"] = "draft"
    revision: int = Field(default=1, ge=1)
    origin: str = Field(default="", max_length=200)
    variety: str = Field(default="", max_length=200)
    method: Literal["box", "heap", "basket", "tray", "other"] = "box"
    batch_mass_kg: float = Field(gt=0, le=100000)
    duration_hours: float = Field(gt=0, le=MAX_DURATION_HOURS)
    temperature_envelope: list[TargetPoint] = Field(default_factory=list, max_length=100)
    notes: str = Field(default="", max_length=4000)

    @model_validator(mode="after")
    def check_envelope(self):
        hours = [p.hour for p in self.temperature_envelope]
        if any(b <= a for a, b in zip(hours, hours[1:])):
            raise ValueError("Target hours must strictly increase")
        if hours and hours[-1] > self.duration_hours:
            raise ValueError("Targets must fall within the duration")
        return self


class Observation(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    hour: float = Field(ge=0, le=MAX_DURATION_HOURS)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    probe_location: str = Field(default="", max_length=120)
    temperature_c: float | None = Field(default=None, ge=-10, le=90)
    pulp_ph: float | None = Field(default=None, ge=0, le=14)
    bean_ph: float | None = Field(default=None, ge=0, le=14)
    source: Literal["manual", "sensor", "import"] = "manual"
    notes: str = Field(default="", max_length=1000)

    @model_validator(mode="after")
    def require_measurement(self):
        if all(v is None for v in (self.temperature_c, self.pulp_ph, self.bean_ph)):
            raise ValueError("An observation needs at least one measurement")
        return self


class ProcessEvent(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    hour: float = Field(ge=0, le=MAX_DURATION_HOURS)
    kind: Literal["turn", "sample", "inspection", "observation", "start", "finish", "deviation"]
    notes: str = Field(default="", max_length=2000)


class FermentationBatch(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    id: UUID = Field(default_factory=uuid4)
    org_id: UUID
    supplier_id: UUID
    producer_lot_code: str = Field(min_length=1, max_length=160)
    supplier_lot_review_id: UUID | None = None
    profile_id: UUID
    profile_revision: int = Field(ge=1)
    status: Literal["planned", "running", "completed", "held"] = "planned"
    source_lot_id: UUID | None = None
    observations: list[Observation] = Field(default_factory=list, max_length=10000)
    events: list[ProcessEvent] = Field(default_factory=list, max_length=1000)

    @model_validator(mode="after")
    def chronological_record(self):
        hours = [o.hour for o in self.observations]
        if any(b < a for a, b in zip(hours, hours[1:])):
            raise ValueError("Observations must be chronological")
        return self


def temperature_assessment(profile: FermentationProfile, batch: FermentationBatch) -> list[dict]:
    """Compare actual temperatures to interpolated approved target envelope.

    No target points means no automatic pass/fail decision. This is process
    monitoring, not a microbiological safety or product release determination.
    """
    if profile.id != batch.profile_id or profile.org_id != batch.org_id or profile.supplier_id != batch.supplier_id or profile.revision != batch.profile_revision:
        raise ValueError("Batch must reference this organization, profile and revision")
    points = profile.temperature_envelope
    out = []
    for obs in batch.observations:
        if obs.temperature_c is None:
            continue
        if not points or obs.hour < points[0].hour or obs.hour > points[-1].hour:
            out.append({"observation_id": str(obs.id), "status": "unassessed"})
            continue
        left = points[0]
        right = points[-1]
        for index in range(len(points) - 1):
            if points[index].hour <= obs.hour <= points[index + 1].hour:
                left, right = points[index], points[index + 1]
                break
        weight = 0 if right.hour == left.hour else (obs.hour - left.hour) / (right.hour - left.hour)
        low = left.minimum_c + weight * (right.minimum_c - left.minimum_c)
        high = left.maximum_c + weight * (right.maximum_c - left.maximum_c)
        out.append({"observation_id": str(obs.id), "status": "within_envelope" if low <= obs.temperature_c <= high else "outside_envelope",
                    "minimum_c": round(low, 3), "maximum_c": round(high, 3)})
    return out
