import os
import shutil
import subprocess
from .repository_brain import RepositoryBrain

class OSLearner:
    def __init__(self, brain: RepositoryBrain):
        self.brain = brain

    def learn_from_github(self, repo_url):
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        temp_path = os.path.join("temp_learn", repo_name)

        print(f"🌍 Brain: Ingesting Open Source {repo_url}")

        try:
            if os.path.exists(temp_path): shutil.rmtree(temp_path)
            # Clone with depth 1 to save time
            subprocess.run(["git", "clone", "--depth", "1", repo_url, temp_path], check=True)

            # Extract knowledge
            knowledge = self.brain.ingest_repository(temp_path)

            # Lessons learned
            return knowledge

        except Exception as e:
            print(f"❌ Brain OS Learn Failed: {e}")
            return None
        finally:
            if os.path.exists(temp_path):
                shutil.rmtree(temp_path)
                print(f"🗑️ Brain: Cleaned up {temp_path}")
