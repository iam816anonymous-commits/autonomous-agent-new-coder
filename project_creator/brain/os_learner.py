import os
import shutil
import subprocess

from .repository_brain import RepositoryBrain


class OSLearner:
    def __init__(self, brain: RepositoryBrain):
        self.brain = brain

    def learn_from_local(self, local_path, source_type="EXTERNAL"):
        print(f"📂 Brain: Ingesting Local Codebase {local_path} as {source_type}")
        if not os.path.exists(local_path):
            raise Exception(f"Path {local_path} does not exist")

        from project_creator.learning import pattern_learner

        orig_source = getattr(pattern_learner, "current_source", "SELF")
        pattern_learner.current_source = source_type

        knowledge = self.brain.ingest_repository(local_path)
        pattern_learner.current_source = orig_source
        return knowledge

    def learn_from_github(self, repo_url, source_type="EXTERNAL"):
        # P0-2: Git Clone Injection Hardening
        # 1. Strict URL validation
        if not repo_url.startswith("https://github.com/"):
            print(
                f"❌ Brain: Security Rejection. Only https://github.com/ is allowed. Provided: {repo_url}"
            )
            return None

        # 2. Prevent option injection via URL starting with -
        if repo_url.strip().startswith("-"):
            print("❌ Brain: Security Rejection. Malformed URL.")
            return None

        repo_name = repo_url.split("/")[-1].replace(".git", "")
        # Sanitize repo_name to prevent path traversal
        repo_name = "".join(c for c in repo_name if c.isalnum() or c in ("-", "_"))
        temp_path = os.path.join("temp_learn", repo_name)

        print(f"🌍 Brain: Ingesting Open Source {repo_url} as {source_type}")

        try:
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
            # 3. Use -- to separate options from URL, depth 1 for speed
            subprocess.run(
                ["git", "clone", "--depth", "1", "--", repo_url, temp_path], check=True
            )

            # 1. Update Ingestion Context for Source Tracking
            from project_creator.learning import pattern_learner

            orig_source = getattr(pattern_learner, "current_source", "SELF")
            pattern_learner.current_source = source_type

            # 2. Sanitize against prompt injection before ingestion
            self._sanitize_ingestion(temp_path)

            # 3. Extract knowledge
            knowledge = self.brain.ingest_repository(temp_path)

            # 3. Restore original source
            pattern_learner.current_source = orig_source

            return knowledge

        except Exception as e:
            print(f"❌ Brain OS Learn Failed: {e}")
            return None
        finally:
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)

    def _sanitize_ingestion(self, path):
        """Deletes potential prompt injection files from untrusted repos."""
        forbidden_files = ["PROMPT.md", "SYSTEM_PROMPT.md", "INSTRUCTIONS.md"]
        for root, _, files in os.walk(path):
            for f in files:
                if (
                    f.upper() in [ff.upper() for f in forbidden_files]
                    or "IGNORE" in f.upper()
                ):
                    file_path = os.path.join(root, f)
                    os.remove(file_path)
                    print(
                        f"🛡️  OSLearner: Deleted potentially malicious instruction file: {f}"
                    )
