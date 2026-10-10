"""Chart payload checks for the supplier fermentation module."""
import unittest
from uuid import uuid4

from fermentation.engine import FermentationProfile, FermentationBatch, Observation, ProcessEvent, TargetPoint
from fermentation.monitoring import monitoring_chart


class MonitoringChartTests(unittest.TestCase):
    def test_chart_preserves_probe_locations_and_events(self):
        org, supplier = uuid4(), uuid4()
        profile = FermentationProfile(
            org_id=org, supplier_id=supplier, name="Farm box profile",
            batch_mass_kg=250, duration_hours=120,
            temperature_envelope=[TargetPoint(hour=0, minimum_c=25, maximum_c=32),
                                  TargetPoint(hour=120, minimum_c=35, maximum_c=48)],
        )
        batch = FermentationBatch(
            org_id=org, supplier_id=supplier, producer_lot_code="FARM-01",
            profile_id=profile.id, profile_revision=profile.revision,
            observations=[
                Observation(hour=24, probe_location="center", temperature_c=35),
                Observation(hour=24, probe_location="surface", temperature_c=28, pulp_ph=4.2),
            ],
            events=[ProcessEvent(hour=24, kind="turn", notes="First turn")],
        )
        payload = monitoring_chart(profile, batch)
        self.assertEqual(len(payload["readings"]), 2)
        self.assertEqual(payload["readings"][0]["probe_location"], "center")
        self.assertEqual(payload["readings"][1]["probe_location"], "surface")
        self.assertEqual(payload["readings"][1]["pulp_ph"], 4.2)
        self.assertEqual(payload["events"][0]["kind"], "turn")
        self.assertIsNone(payload["release_decision"])

    def test_no_target_never_claims_in_spec(self):
        org, supplier = uuid4(), uuid4()
        profile = FermentationProfile(org_id=org, supplier_id=supplier, name="Trial",
                                      batch_mass_kg=100, duration_hours=48)
        batch = FermentationBatch(
            org_id=org, supplier_id=supplier, producer_lot_code="X",
            profile_id=profile.id, profile_revision=1,
            observations=[Observation(hour=3, temperature_c=35)],
        )
        self.assertEqual(monitoring_chart(profile, batch)["readings"][0]["status"], "unassessed")

    def test_wrong_supplier_rejected(self):
        org, supplier = uuid4(), uuid4()
        profile = FermentationProfile(org_id=org, supplier_id=supplier, name="Trial",
                                      batch_mass_kg=100, duration_hours=48)
        batch = FermentationBatch(
            org_id=org, supplier_id=uuid4(), producer_lot_code="X",
            profile_id=profile.id, profile_revision=1)
        with self.assertRaises(ValueError):
            monitoring_chart(profile, batch)


if __name__ == "__main__":
    unittest.main()
