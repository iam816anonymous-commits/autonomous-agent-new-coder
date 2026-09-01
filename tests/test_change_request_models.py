import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType, ChangePlan, PlanningStatus

class TestChangeRequestModels(unittest.TestCase):
    def test_change_request_instantiation(self):
        req = ChangeRequest(
            request_id="REQ-001",
            user_intent="Add authentication middleware to API",
            request_type=ChangeRequestType.FEATURE,
            description="Add auth middleware"
        )
        self.assertEqual(req.request_id, "REQ-001")
        self.assertEqual(req.request_type, ChangeRequestType.FEATURE)

if __name__ == "__main__":
    unittest.main()
