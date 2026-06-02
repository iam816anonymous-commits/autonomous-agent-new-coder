from typing import Dict, Any, List

class GenerationCoordinator:
    """
    Handles the high-level orchestration of file generation.
    """
    def __init__(self, coder_agent, validation_manager):
        self.coder = coder_agent
        self.validation_manager = validation_manager

    def generate_project_file(self, file_meta: Dict[str, str], blueprint: Dict, generated_files: Dict, strategy_doc: str = None) -> Dict[str, Any]:
        path = file_meta['path']
        print(f"📝 [GEN] Starting: {path}")

        content = self.coder.generate_file(path, file_meta['description'], blueprint, generated_files, strategy_doc=strategy_doc)

        # Delegate validation and repair to ValidationManager
        return self.validation_manager.run_dry_run(path, content, blueprint, generated_files, strategy_doc=strategy_doc)
