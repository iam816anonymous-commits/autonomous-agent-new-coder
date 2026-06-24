import json

from project_creator.brain.architecture_memory import ArchitectureMemory
from project_creator.brain.pattern_memory import PatternMemory
from project_creator.brain.repair_memory import RepairMemory
from project_creator.learning import DB_PATH


class GeneralizedExperiment:
    def __init__(self):
        self.repair_mem = RepairMemory(DB_PATH)
        self.arch_mem = ArchitectureMemory(DB_PATH)
        self.pattern_mem = PatternMemory(DB_PATH)
        self.results = {}

    def run_dependency_transfer(self):
        print("🧪 Exp 1: Dependency Transfer")
        # 1. Project A: Learn FastAPI fix
        self.repair_mem.store_repair(
            error="ModuleNotFoundError: No module named 'fastapi'",
            traceback="",
            root_cause="Missing dependency",
            repair="Update requirements.txt with fastapi",
        )
        # 2. Project B & C: Check for strategy reuse
        errors = [
            "ModuleNotFoundError: No module named 'sqlalchemy'",
            "ImportError: pydantic not installed",
        ]
        transfer_success = 0
        for err in errors:
            matches = self.repair_mem.retrieve_repairs(err)
            if matches and "requirements.txt" in matches[0]["repair"]:
                transfer_success += 1
                print(f"   ✅ Generalized for '{err}'")
        self.results["dependency_transfer"] = transfer_success / len(errors)

    def run_architecture_transfer(self):
        print("🧪 Exp 2: Architecture Transfer")
        self.arch_mem.store_architecture(
            "FastAPI CRUD", "MVC Pattern", ["fastapi", "sqlalchemy"]
        )
        matches = self.arch_mem.retrieve_similar("FastAPI SaaS platform")
        if matches and "MVC" in matches[0]["architecture"]:
            print("   ✅ Architecture Transfer Success")
            self.results["arch_transfer"] = 1.0
        else:
            self.results["arch_transfer"] = 0.0

    def run_testing_transfer(self):
        print("🧪 Exp 3: Testing Transfer")
        self.pattern_mem.store_framework_pattern("pytest", "fixture", "@pytest.fixture")
        patterns = self.pattern_mem.get_ranked_patterns("pytest")
        if any("fixture" in str(p) for p in patterns):
            print("   ✅ Testing Transfer Success")
            self.results["test_transfer"] = 1.0
        else:
            self.results["test_transfer"] = 0.0

    def finalize(self):
        try:
            from project_creator.core.storage import Storage

            storage = Storage(".")
            storage.write_file(
                "gen_learning_results.json", json.dumps(self.results, indent=2)
            )
        except:
            with open("gen_learning_results.json", "w") as f:
                json.dump(self.results, f, indent=2)


if __name__ == "__main__":
    exp = GeneralizedExperiment()
    exp.run_dependency_transfer()
    exp.run_architecture_transfer()
    exp.run_testing_transfer()
    exp.finalize()
