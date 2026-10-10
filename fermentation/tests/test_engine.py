"""Unit tests for fermentation models and monitoring decisions."""
import unittest
from uuid import uuid4

from pydantic import ValidationError

from fermentation.engine import (
    FermentationBatch, FermentationProfile, Observation, ProcessEvent, TargetPoint,
    temperature_assessment,
)


class FermentationEngineTests(unittest.TestCase):
    def setUp(self):
        self.org = uuid4()
        self.supplier = uuid4()
        self.profile = FermentationProfile(
            org_id=self.org, supplier_id=self.supplier, name="Cooperative box trial", batch_mass_kg=400,
            duration_hours=120, status="approved",
            temperature_envelope=[
                TargetPoint(hour=0, minimum_c=25, maximum_c=32),
                TargetPoint(hour=60, minimum_c=40, maximum_c=48),
                TargetPoint(hour=120, minimum_c=36, maximum_c=45),
            ],
        )

    def test_interpolated_envelope(self):
        batch = FermentationBatch(
            org_id=self.org, supplier_id=self.supplier, producer_lot_code='COOP-001', profile_id=self.profile.id, profile_revision=1,
            observations=[Observation(hour=30, temperature_c=36),
                          Observation(hour=90, temperature_c=52)],
            events=[ProcessEvent(hour=48, kind="turn")],
        )
        result = temperature_assessment(self.profile, batch)
        self.assertEqual(result[0]["status"], "within_envelope")
        self.assertEqual(result[1]["status"], "outside_envelope")

    def test_missing_target_returns_unassessed(self):
        self.profile.temperature_envelope = []
        batch = FermentationBatch(org_id=self.org, profile_id=self.profile.id,
                                  profile_revision=1, observations=[Observation(hour=20, pulp_ph=4, temperature_c=35)])
        self.assertEqual(temperature_assessment(self.profile, batch)[0]["status"], "unassessed")

    def test_revision_and_tenant_mismatch_rejected(self):
        batch = FermentationBatch(org_id=uuid4(), supplier_id=self.supplier, producer_lot_code='COOP-001', profile_id=self.profile.id,
                                  profile_revision=1)
        with self.assertRaises(ValueError):
            temperature_assessment(self.profile, batch)

    def test_invalid_measurement_and_targets_rejected(self):
        with self.assertRaises(ValidationError):
            Observation(hour=5)
        with self.assertRaises(ValidationError):
            TargetPoint(hour=5, minimum_c=55, maximum_c=35)
        with self.assertRaises(ValidationError):
            FermentationProfile(org_id=self.org, supplier_id=self.supplier, name="invalid", batch_mass_kg=50,
                                duration_hours=72, temperature_envelope=[
                                    TargetPoint(hour=24, minimum_c=30, maximum_c=40),
                                    TargetPoint(hour=12, minimum_c=30, maximum_c=40),
                                ])

    def test_draft_json_roundtrip(self):
        restored = FermentationProfile.model_validate_json(self.profile.model_dump_json())
        self.assertEqual(restored.id, self.profile.id)
        self.assertEqual(restored.temperature_envelope[1].hour, 60)


if __name__ == "__main__":
    unittest.main()
