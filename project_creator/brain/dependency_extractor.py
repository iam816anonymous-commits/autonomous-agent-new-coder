import os


class DependencyExtractor:
    def __init__(self):
        pass

    def extract_dependencies(self, repo_path):
        dependencies = {"python": [], "javascript": [], "docker": False}

        # Python requirements
        req_file = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(req_file):
            with open(req_file, "r") as f:
                dependencies["python"] = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]

        # JS/TS packages
        pkg_file = os.path.join(repo_path, "package.json")
        if os.path.exists(pkg_file):
            import json

            try:
                with open(pkg_file, "r") as f:
                    data = json.load(f)
                    dependencies["javascript"] = list(
                        data.get("dependencies", {}).keys()
                    )
            except:
                pass

        # Docker detection
        if os.path.exists(os.path.join(repo_path, "Dockerfile")) or os.path.exists(
            os.path.join(repo_path, "docker-compose.yml")
        ):
            dependencies["docker"] = True

        return dependencies
