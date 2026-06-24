from typing import Any, Dict, List


class RepositoryComparison:
    """
    Compares two or more repository knowledge cards to identify differences
    in architectural and operational patterns.
    """

    def compare(self, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(repos) < 2:
            return {"error": "At least two repositories are required for comparison."}

        repo_a = repos[0]
        repo_b = repos[1]

        comparison = {
            "repositories": [r.get("repository") for r in repos],
            "architecture": {
                "match": repo_a.get("architecture") == repo_b.get("architecture"),
                "diff": f"{repo_a.get('repository')}: {repo_a.get('architecture')} vs {repo_b.get('repository')}: {repo_b.get('architecture')}",
            },
            "patterns": {
                "shared": list(
                    set(repo_a.get("patterns", [])) & set(repo_b.get("patterns", []))
                ),
                "unique_to_a": list(
                    set(repo_a.get("patterns", [])) - set(repo_b.get("patterns", []))
                ),
                "unique_to_b": list(
                    set(repo_b.get("patterns", [])) - set(repo_a.get("patterns", []))
                ),
            },
            "complexity_delta": repo_a.get("complexity_score", 0)
            - repo_b.get("complexity_score", 0),
            "dependencies": {
                "shared": list(
                    set(repo_a.get("dependencies", []))
                    & set(repo_b.get("dependencies", []))
                ),
                "exclusive_a": list(
                    set(repo_a.get("dependencies", []))
                    - set(repo_b.get("dependencies", []))
                ),
                "exclusive_b": list(
                    set(repo_b.get("dependencies", []))
                    - set(repo_a.get("dependencies", []))
                ),
            },
        }

        return comparison
