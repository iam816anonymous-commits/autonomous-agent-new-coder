import os
import shutil
import subprocess
from .repository_brain import RepositoryBrain

class OSLearner:
    def __init__(self, brain: RepositoryBrain):
        self.brain = brain

    def ingest_os_project(self, git_url):
        repo_name = git_url.split("/")[-1].replace(".git", "")
        temp_dir = f"temp_os_{repo_name}"

        print(f"🌍 Cloning {git_url} for learning...")
        try:
            subprocess.run(["git", "clone", "--depth", "1", git_url, temp_dir], check=True)

            # Learn patterns and architecture
            findings = self.brain.learn_repository(temp_dir)
            print(f"✅ Learned from {repo_name}: {findings['architecture']['type']}")

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"🗑️ Cleaned up {temp_dir}")
