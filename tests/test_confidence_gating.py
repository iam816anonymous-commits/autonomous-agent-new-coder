import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType, ChangePlan, PlanningStatus
from engine.change_planning.gating import ConfidenceGatingEngine
from repository.semantic.models import ConfidenceLevel

class TestConfidenceGating(unittest.TestCase):
    def test_confidence_gating_ready(self):
        req = ChangeRequest("r1", "intent", ChangeRequestType.FEATURE, "desc", risk_level="LOW")
        plan = ChangePlan("p1", req, discovery_result={"sufficient_evidence": True}, confidence=ConfidenceLevel.HIGH)
        status = ConfidenceGatingEngine.evaluate_gating(plan)
        self.assertEqual(status, PlanningStatus.READY)

    def test_confidence_gating_requires_discovery_on_missing_evidence(self):
        req = ChangeRequest("r2", "intent", ChangeRequestType.FEATURE, "desc")
        plan = ChangePlan("p2", req, discovery_result={"sufficient_evidence": False}, confidence=ConfidenceLevel.HIGH)
        status = ConfidenceGatingEngine.evaluate_gating(plan)
        self.assertEqual(status, PlanningStatus.REQUIRES_DISCOVERY)

if __name__ == "__main__":
    unittest.main()
