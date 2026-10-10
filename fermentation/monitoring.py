"""Chart-ready fermentation process series; pure calculation, no network or database.

SPDX-License-Identifier: AGPL-3.0-or-later
"""
from .engine import FermentationBatch, FermentationProfile, temperature_assessment


def monitoring_chart(profile: FermentationProfile, batch: FermentationBatch) -> dict:
    """Return plotting data; never infer an ideal temperature curve or release status.

    Client renders this output as time-series lines, envelopes, and event markers.
    Keep sensor positions separate to avoid conflating distinct measurement points.
    """
    evaluations = temperature_assessment(profile, batch)
    by_id = {entry["observation_id"]: entry for entry in evaluations}
    readings = []
    for observation in batch.observations:
        assessed = by_id.get(str(observation.id), {"status": "unassessed"})
        readings.append({
            "id": str(observation.id),
            "hour": observation.hour,
            "probe_location": observation.probe_location,
            "temperature_c": observation.temperature_c,
            "pulp_ph": observation.pulp_ph,
            "bean_ph": observation.bean_ph,
            "source": observation.source,
            "status": assessed["status"] if observation.temperature_c is not None else "not_applicable",
            "minimum_c": assessed.get("minimum_c"),
            "maximum_c": assessed.get("maximum_c"),
        })
    return {
        "schema_version": "1.0",
        "profile_id": str(profile.id),
        "profile_revision": profile.revision,
        "batch_id": str(batch.id),
        "temperature_unit": "C",
        "time_unit": "hour",
        "target_envelope": [
            {"hour": p.hour, "minimum_c": p.minimum_c, "maximum_c": p.maximum_c}
            for p in profile.temperature_envelope
        ],
        "readings": readings,
        "events": [
            {"id": str(event.id), "hour": event.hour, "kind": event.kind, "notes": event.notes}
            for event in batch.events
        ],
        "release_decision": None,
        "notice": "Process envelope checks are informational, not food-safety certification.",
    }
