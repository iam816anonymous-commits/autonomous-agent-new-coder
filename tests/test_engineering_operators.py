import os
import shutil
import tempfile
import unittest
from engine.classifier.models import TaskType, TaskClassificationStatus, TaskClassification
from engine.operators.registry import OperatorRegistry
from engine.operators.context import OperatorContext
from engine.operators.builtin.symbol_rename import SymbolRenameOperator
from engine.operators.builtin.file_move import FileMoveOperator
from engine.operators.errors import ApprovalRequiredError, StaleProposalError
from repository.scan import RepositoryAnalyzer

FIXTURES_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "fixtures"))

class TestOperatorRegistry(unittest.TestCase):
    def test_registry_lookup_and_duplicate_rejection(self):
        reg = OperatorRegistry()
        rename_op = SymbolRenameOperator()
        move_op = FileMoveOperator()

        reg.register(rename_op)
        reg.register(move_op)

        self.assertEqual(reg.get_operator_by_name("SymbolRenameOperator"), rename_op)
        self.assertEqual(reg.get_operator_for_task(TaskType.SYMBOL_RENAME), rename_op)
        self.assertEqual(reg.get_operator_for_task(TaskType.FILE_MOVE), move_op)
        self.assertEqual(len(reg.list_operators()), 2)

        # Duplicate operator registration by name
        with self.assertRaises(ValueError):
            reg.register(SymbolRenameOperator())


class TestSymbolRenameOperator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        # Create sample files for symbol rename testing
        self.utils_path = os.path.join(self.root, "utils.py")
        self.app_path = os.path.join(self.root, "app.py")

        with open(self.utils_path, "w", encoding="utf-8") as f:
            f.write(
                "def calculate_total(a, b):\n"
                "    return a + b\n\n"
                "# calculate_total backup function\n"
                "def my_calculate_total_backup():\n"
                "    return 0\n"
            )

        with open(self.app_path, "w", encoding="utf-8") as f:
            f.write(
                "from utils import calculate_total\n\n"
                "def run():\n"
                "    val = calculate_total(10, 20)\n"
                "    return val\n"
            )

        self.snapshot = RepositoryAnalyzer.analyze(self.root)
        self.op = SymbolRenameOperator()
        self.classification = TaskClassification(
            task_type=TaskType.SYMBOL_RENAME,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"old_name": "calculate_total", "new_name": "calculate_invoice_total"}
        )
        self.context = OperatorContext(
            repository_root=self.root,
            task_id="TASK-TEST-RENAME",
            classification=self.classification,
            repo_snapshot=self.snapshot
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dry_run_modifies_nothing(self):
        plan = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan)

        self.assertTrue(len(proposal.files_to_modify) >= 2)

        # Dry run proposal must not modify actual workspace files
        with open(self.utils_path, "r") as f:
            self.assertIn("def calculate_total(", f.read())
        with open(self.app_path, "r") as f:
            self.assertIn("calculate_total(10, 20)", f.read())

    def test_structural_token_rename_no_false_positives(self):
        plan = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan)

        # Check proposed content for utils.py
        utils_change = next(fc for fc in proposal.files_to_modify if fc.path == "utils.py")
        # 'calculate_total' renamed
        self.assertIn("def calculate_invoice_total(", utils_change.new_content)
        # 'my_calculate_total_backup' MUST NOT be incorrectly modified!
        self.assertIn("def my_calculate_total_backup():", utils_change.new_content)
        # String/comment mentions remain unchanged in token mode
        self.assertIn("# calculate_total backup function", utils_change.new_content)

    def test_approval_boundary_enforcement(self):
        plan = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan)

        # approved=False MUST raise ApprovalRequiredError
        with self.assertRaises(ApprovalRequiredError):
            self.op.apply(self.context, proposal, approved=False)

        # Workspace remains untouched
        with open(self.utils_path, "r") as f:
            self.assertIn("def calculate_total(", f.read())

        # approved=True applies modifications
        res = self.op.apply(self.context, proposal, approved=True)
        self.assertTrue(res.success)

        with open(self.utils_path, "r") as f:
            self.assertIn("def calculate_invoice_total(", f.read())
        with open(self.app_path, "r") as f:
            self.assertIn("calculate_invoice_total(10, 20)", f.read())

    def test_double_apply_protection(self):
        plan = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan)

        res1 = self.op.apply(self.context, proposal, approved=True)
        self.assertTrue(res1.success)

        # Re-applying same proposal returns ALREADY_APPLIED result
        res2 = self.op.apply(self.context, proposal, approved=True)
        self.assertTrue(res2.success)
        self.assertIn("ALREADY_APPLIED", res2.error)

    def test_stale_proposal_rejection(self):
        plan = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan)

        # Modify file after proposal generation to trigger stale hash rejection
        with open(self.utils_path, "a") as f:
            f.write("\n# Manual edit after proposal\n")

        with self.assertRaises(StaleProposalError):
            self.op.apply(self.context, proposal, approved=True)

    def test_ambiguous_symbol_rejection(self):
        # Create second file with identical definition 'calculate_total'
        mod2_path = os.path.join(self.root, "mod2.py")
        with open(mod2_path, "w") as f:
            f.write("def calculate_total(): pass\n")

        snapshot2 = RepositoryAnalyzer.analyze(self.root)
        ctx2 = OperatorContext(
            repository_root=self.root,
            task_id="AMBIGUOUS-TASK",
            classification=self.classification,
            repo_snapshot=snapshot2
        )

        plan = self.op.plan(ctx2)
        proposal = self.op.propose(ctx2, plan)

        # Precondition for unambiguous target should fail
        ambiguous_pre = next(p for p in proposal.preconditions if p.name == "unambiguous_symbol_target")
        self.assertFalse(ambiguous_pre.satisfied)
        self.assertIn("AMBIGUOUS_TARGET", ambiguous_pre.message)
        self.assertEqual(len(proposal.files_to_modify), 0)

    def test_target_collision_rejection(self):
        # Create function 'calculate_invoice_total' to trigger collision
        mod_path = os.path.join(self.root, "existing.py")
        with open(mod_path, "w") as f:
            f.write("def calculate_invoice_total(): pass\n")

        snapshot = RepositoryAnalyzer.analyze(self.root)
        ctx = OperatorContext(
            repository_root=self.root,
            task_id="COLLISION-TASK",
            classification=self.classification,
            repo_snapshot=snapshot
        )

        plan = self.op.plan(ctx)
        proposal = self.op.propose(ctx, plan)

        collision_pre = next(p for p in proposal.preconditions if p.name == "no_target_collision")
        self.assertFalse(collision_pre.satisfied)


class TestFileMoveOperator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.src_rel = "foo.py"
        self.dst_rel = "utils/foo.py"
        self.src_full = os.path.join(self.root, self.src_rel)

        with open(self.src_full, "w", encoding="utf-8") as f:
            f.write("def helper():\n    return 'ok'\n")

        self.snapshot = RepositoryAnalyzer.analyze(self.root)
        self.op = FileMoveOperator()
        self.classification = TaskClassification(
            task_type=TaskType.FILE_MOVE,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"source": self.src_rel, "destination": self.dst_rel}
        )
        self.context = OperatorContext(
            repository_root=self.root,
            task_id="TASK-TEST-MOVE",
            classification=self.classification,
            repo_snapshot=self.snapshot
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_file_move_dry_run_and_apply(self):
        plan = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan)

        self.assertEqual(proposal.files_to_delete, [self.src_rel])
        self.assertEqual(len(proposal.files_to_create), 1)

        # Dry run check: source file still exists, destination not created
        self.assertTrue(os.path.exists(self.src_full))
        self.assertFalse(os.path.exists(os.path.join(self.root, self.dst_rel)))

        # Apply move with approved=True
        res = self.op.apply(self.context, proposal, approved=True)
        self.assertTrue(res.success)

        self.assertFalse(os.path.exists(self.src_full))
        dst_full = os.path.join(self.root, self.dst_rel)
        self.assertTrue(os.path.exists(dst_full))
        with open(dst_full, "r") as f:
            self.assertIn("def helper():", f.read())

    def test_path_traversal_move_rejection(self):
        classification = TaskClassification(
            task_type=TaskType.FILE_MOVE,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"source": "foo.py", "destination": "../../etc/passwd"}
        )
        ctx = OperatorContext(
            repository_root=self.root,
            task_id="TRAVERSAL-MOVE",
            classification=classification,
            repo_snapshot=self.snapshot
        )

        plan = self.op.plan(ctx)
        proposal = self.op.propose(ctx, plan)

        boundary_pre = next(p for p in proposal.preconditions if p.name == "workspace_boundary_valid")
        self.assertFalse(boundary_pre.satisfied)


class TestTargetedRollback(unittest.TestCase):
    def test_rollback_preserves_unrelated_user_changes(self):
        temp_dir = tempfile.TemporaryDirectory()
        root = temp_dir.name

        unrelated_path = os.path.join(root, "unrelated.py")
        target_path = os.path.join(root, "target.py")

        with open(unrelated_path, "w") as f: f.write("# User edits in progress\n")
        with open(target_path, "w") as f: f.write("def foo(): pass\n")

        snapshot = RepositoryAnalyzer.analyze(root)
        op = SymbolRenameOperator()
        ctx = OperatorContext(
            repository_root=root,
            task_id="ROLLBACK-TEST",
            classification=TaskClassification(
                task_type=TaskType.SYMBOL_RENAME,
                status=TaskClassificationStatus.SUPPORTED,
                confidence=0.95,
                extracted_parameters={"old_name": "foo", "new_name": "bar"}
            ),
            repo_snapshot=snapshot
        )

        plan = op.plan(ctx)
        proposal = op.propose(ctx, plan)

        # Apply and then rollback
        op.apply(ctx, proposal, approved=True)
        op.rollback(ctx, proposal)

        # Target file restored
        with open(target_path) as f: self.assertIn("def foo():", f.read())
        # Unrelated user file remains completely intact
        with open(unrelated_path) as f: self.assertIn("# User edits in progress", f.read())

        temp_dir.cleanup()

if __name__ == "__main__":
    unittest.main()
