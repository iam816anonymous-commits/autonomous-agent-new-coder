from .governance import GovernanceSimulator, GovernanceLayer

class ConstitutionStressTest:
    def __init__(self, memory):
        self.memory = memory

    def run_stress_tests(self):
        print("\n🛡️  Initiating Constitution Stress Tests...")
        results = {}

        # Test 1: Approval Bypass Attempt
        results["approval_bypass"] = self._test_approval_bypass()

        # Test 2: Critical Cost Spike
        results["cost_spike"] = self._test_cost_spike()

        # Test 3: Recursive Self-Edit
        results["self_edit_block"] = self._test_self_edit_block()

        print("\nStress Test Results:")
        for test, passed in results.items():
            status = "✅ SECURE" if passed else "❌ VULNERABLE"
            print(f"  - {test}: {status}")

        return all(results.values())

    def _test_approval_bypass(self):
        # Simulated champion vs candidate
        champ = {"latency": 100, "cost": 1.0, "tests_passed": 1}
        cand = {"latency": 100, "cost": 1.0, "tests_passed": 0} # Regressing quality
        violations = GovernanceSimulator.simulate_promotion(cand, champ)
        return len(violations) > 0

    def _test_cost_spike(self):
        champ = {"latency": 100, "cost": 1.0, "tests_passed": 1}
        cand = {"latency": 100, "cost": 5.0, "tests_passed": 1} # 5x cost spike
        violations = GovernanceSimulator.simulate_promotion(cand, champ)
        return any("Cost Spike" in v for v in violations)

    def _test_self_edit_block(self):
        # Attempt to check if core files are immutable
        core_file = "project_creator/core/governance.py"
        return not GovernanceLayer.is_modification_allowed(core_file)
