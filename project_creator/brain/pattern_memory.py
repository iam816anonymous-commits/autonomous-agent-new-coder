from project_creator.learning.memory_db import CodingMemory

class PatternMemory:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)

    def store_pattern(self, name, pattern_type, content, success_score=1.0):
        # We leverage the existing patterns table
        self.memory.learn_pattern(pattern_type, content)

    def get_best_patterns(self, pattern_type, limit=5):
        return self.memory.get_top_patterns(pattern_type, limit=limit)

    def get_idioms(self):
        return self.memory.get_top_patterns('idiom', limit=10)
