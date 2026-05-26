import subprocess
import os

class Sandbox:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)

    def _run_git(self, *args):
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            return result
        except:
            return None

    def create_candidate_branch(self, branch_name):
        # Ensure we are in a git repo
        if not os.path.exists(os.path.join(self.project_root, ".git")):
            self._run_git("init")

        # Stash current changes if any
        self._run_git("stash")
        # Create and switch to new branch
        self._run_git("checkout", "-b", branch_name)
        return True

    def merge_to_main(self, branch_name):
        self._run_git("checkout", "main")
        res = self._run_git("merge", branch_name)
        if res and res.returncode == 0:
            self._run_git("branch", "-d", branch_name)
            return True
        return False

    def abort_candidate(self, branch_name):
        self._run_git("checkout", "main")
        self._run_git("branch", "-D", branch_name)
        self._run_git("stash", "pop")
        return True
