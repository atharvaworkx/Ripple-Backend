"""Unified diff parser for git patches."""

import re
from typing import List, Dict, Any, Tuple

HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

def parse_unified_diff(diff_text: str) -> List[Dict[str, Any]]:
    """
    Parse unified diff text into structured file modifications and changed line ranges.
    Returns list of dicts:
    [
        {
            "old_path": "billing/pricing.py",
            "new_path": "billing/pricing.py",
            "is_new": False,
            "is_deleted": False,
            "changed_lines_old": [(start, end), ...],
            "changed_lines_new": [(start, end), ...]
        }
    ]
    """
    if not diff_text:
        return []

    files: List[Dict[str, Any]] = []
    current_file: Dict[str, Any] = None
    lines = diff_text.splitlines()

    for line in lines:
        if line.startswith("diff --git"):
            if current_file:
                files.append(current_file)
            
            # Extract paths
            parts = line.split(" ")
            old_path = parts[2].lstrip("a/").strip() if len(parts) > 2 else ""
            new_path = parts[3].lstrip("b/").strip() if len(parts) > 3 else ""

            current_file = {
                "old_path": old_path,
                "new_path": new_path,
                "is_new": False,
                "is_deleted": False,
                "changed_lines_old": [],
                "changed_lines_new": [],
                "patch_snippet": []
            }
        elif current_file is not None:
            if line.startswith("new file mode"):
                current_file["is_new"] = True
            elif line.startswith("deleted file mode"):
                current_file["is_deleted"] = True
            elif line.startswith("--- a/"):
                current_file["old_path"] = line[6:].strip()
            elif line.startswith("+++ b/"):
                current_file["new_path"] = line[6:].strip()
            elif line.startswith("@@"):
                current_file["patch_snippet"].append(line)
                match = HUNK_HEADER_REGEX.match(line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1

                    old_end = old_start + max(old_count - 1, 0)
                    new_end = new_start + max(new_count - 1, 0)

                    current_file["changed_lines_old"].append((old_start, old_end))
                    current_file["changed_lines_new"].append((new_start, new_end))
            elif line.startswith("+") or line.startswith("-") or line.startswith(" "):
                if len(current_file["patch_snippet"]) < 60:
                    current_file["patch_snippet"].append(line)

    if current_file:
        files.append(current_file)

    return files
