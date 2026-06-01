from project_creator.learning.memory_db import CodingMemory

class PatternMemory:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)

    def store_framework_pattern(self, framework, pattern, content, success_score=1.0):
        # Store in existing patterns table with high priority
        p_type = f"framework_{framework}"
        self.memory.learn_pattern(p_type, content)

    def get_ranked_patterns(self, framework, limit=5):
        p_type = f"framework_{framework}"
        return self.memory.get_top_patterns(p_type, limit=limit)

    def get_security_patterns(self):
        return self.memory.get_top_patterns("security", limit=10)

    def get_testing_patterns(self):
        return self.memory.get_top_patterns("testing", limit=10)
