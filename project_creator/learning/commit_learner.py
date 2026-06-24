import subprocess
from datetime import datetime

from .memory_db import CodingMemory


class CommitLearner:
    def __init__(self, db_path: str, repo_path: str):
        self.memory = CodingMemory(db_path)
        self.repo_path = repo_path

    def learn_history(self, limit=50):
        print(
            f"🕰️  Reality Learning: Analyzing last {limit} commits in {self.repo_path}"
        )
        try:
            # Get commit hashes
            cmd = ["git", "log", f"-n {limit}", "--pretty=format:%H"]
            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True
            )
            hashes = result.stdout.splitlines()

            for h in hashes:
                self._analyze_commit(h)
        except Exception as e:
            print(f"⚠️  CommitLearner Error: {e}")

    def _analyze_commit(self, commit_hash: str):
        try:
            # Get commit metadata
            cmd = ["git", "show", "--quiet", "--pretty=format:%an|%s|%at", commit_hash]
            meta_res = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True
            )
            if not meta_res.stdout:
                return

            author, subject, ts = meta_res.stdout.split("|")
            dt = datetime.fromtimestamp(int(ts))

            # Get changed files
            cmd = ["git", "show", "--name-status", "--pretty=format:", commit_hash]
            files_res = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True
            )

            files_data = []
            for line in files_res.stdout.splitlines():
                if not line.strip():
                    continue
                status, path = line.split(None, 1)

                # Only learn from source files
                if path.endswith((".py", ".js", ".ts", ".tsx")):
                    content = self._get_file_content(commit_hash, path)
                    files_data.append(
                        {"path": path, "type": status, "content": content}
                    )

            self.memory.log_git_commit(
                {
                    "hash": commit_hash,
                    "author": author,
                    "message": subject,
                    "timestamp": dt,
                    "repo_path": self.repo_path,
                    "files": files_data,
                }
            )

        except Exception as e:
            print(f"⚠️  Failed to analyze commit {commit_hash}: {e}")

    def _get_file_content(self, commit_hash, path):
        try:
            cmd = ["git", "show", f"{commit_hash}:{path}"]
            res = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True
            )
            return res.stdout if res.returncode == 0 else None
        except:
            return None
