import os
from .collector import collector
from .event_bus import bus
from .memory_db import CodingMemory
from .pattern_learner import PatternLearner
from .repo_learner import RepoLearner
from .commit_learner import CommitLearner
from .failure_learner import FailureLearner

# Default DB Path
DB_PATH = os.path.join(os.path.expanduser("~"), ".jules_memory.db")

# Initialize shared components
memory = CodingMemory(DB_PATH)
pattern_learner = PatternLearner(DB_PATH)
failure_learner = FailureLearner(DB_PATH)

def initialize_reality_learning(workspace_root: str):
    """
    Bootstrap the Reality Learning Engine for a specific workspace.
    """
    repo = RepoLearner(workspace_root)
    commit = CommitLearner(DB_PATH, workspace_root)

    # 1. Scan existing files to learn style
    repo.scan_workspace()

    # 2. Analyze git history if available
    if os.path.exists(os.path.join(workspace_root, ".git")):
        commit.learn_history(limit=50)

    return repo, commit
