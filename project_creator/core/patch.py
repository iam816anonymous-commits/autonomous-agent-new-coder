import difflib

class PatchManager:
    @staticmethod
    def generate_diff(old_content, new_content, file_path):
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}"
        )
        return "".join(diff)

    @staticmethod
    def preview_patch(patch):
        print("\n" + "="*60)
        print(f"📦 PATCH PROPOSAL for: {patch['file']}")
        print(f"REASON: {patch['reason']}")
        print(f"RISK: {patch['risk'].upper()}")
        print(f"AFFECTED TESTS: {', '.join(patch['tests'])}")
        print("="*60)

        print("\n--- DIFF ---")
        diff = PatchManager.generate_diff(patch['old_content'], patch['new_content'], patch['file'])
        # Simplified colorized diff (if terminal supports)
        for line in diff.splitlines():
            if line.startswith('+'):
                print(f"\033[32m{line}\033[0m") # Green
            elif line.startswith('-'):
                print(f"\033[31m{line}\033[0m") # Red
            else:
                print(line)
        print("-" * 30 + "\n")
