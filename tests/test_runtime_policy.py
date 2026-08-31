import os
import tempfile
import unittest
from engine.runtime.policy import RuntimePolicy
from engine.runtime.models import ExecutionCapability
from engine.runtime.errors import PolicyViolationError, WorkingDirectoryEscapeError, NetworkPolicyViolationError

class TestRuntimePolicy(unittest.TestCase):
    def setUp(self):
        self.policy = RuntimePolicy()

    def test_blocked_executables(self):
        blocked = ["bash", "sh", "zsh", "cmd", "powershell", "curl", "wget"]
        for b in blocked:
            with self.assertRaises(PolicyViolationError):
                self.policy.validate_executable(b)

    def test_working_directory_boundary(self):
        temp_dir = tempfile.TemporaryDirectory()
        repo_root = temp_dir.name

        # Valid subfolder inside repo_root
        sub_dir = os.path.join(repo_root, "src")
        os.makedirs(sub_dir, exist_ok=True)
        valid = self.policy.validate_working_directory(repo_root, "src")
        self.assertEqual(valid, os.path.realpath(sub_dir))

        # Attempt path traversal escape outside repo_root
        with self.assertRaises(WorkingDirectoryEscapeError):
            self.policy.validate_working_directory(repo_root, "../../etc")

        temp_dir.cleanup()

    def test_symlink_escape_prevention(self):
        temp_dir = tempfile.TemporaryDirectory()
        repo_root = temp_dir.name
        outside_dir = tempfile.TemporaryDirectory()

        # Symlink pointing outside workspace root
        link_path = os.path.join(repo_root, "escaped_link")
        try:
            os.symlink(outside_dir.name, link_path)
            with self.assertRaises(WorkingDirectoryEscapeError):
                self.policy.validate_working_directory(repo_root, "escaped_link")
        except OSError:
            pass # Symlinks may require privileges on some test platforms

        temp_dir.cleanup()
        outside_dir.cleanup()

    def test_secret_environment_scrubbing_and_redaction(self):
        fake_env = {
            "PATH": "/usr/bin",
            "PYTHONPATH": "/app",
            "AWS_SECRET_ACCESS_KEY": "super_secret_aws_key",
            "OPENAI_API_KEY": "sk-secret1234567890123456",
            "USER_TOKEN": "token-xyz"
        }
        sanitized = self.policy.sanitize_environment(fake_env)

        self.assertIn("PATH", sanitized)
        self.assertIn("PYTHONPATH", sanitized)
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", sanitized)
        self.assertNotIn("OPENAI_API_KEY", sanitized)
        self.assertNotIn("USER_TOKEN", sanitized)

        text = "Failed connect with key sk-secret1234567890123456 and AWS_SECRET_ACCESS_KEY=super_secret_aws_key"
        redacted = self.policy.redact_text(text, parent_env=fake_env)
        self.assertNotIn("sk-secret1234567890123456", redacted)
        self.assertNotIn("super_secret_aws_key", redacted)
        self.assertIn("[REDACTED_SECRET]", redacted)

    def test_network_capability_rejection(self):
        with self.assertRaises(NetworkPolicyViolationError):
            self.policy.validate_capabilities([ExecutionCapability.NETWORK_ACCESS])

if __name__ == "__main__":
    unittest.main()
