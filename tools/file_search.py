import os

HOME_DIR = os.path.expanduser("~")

MAX_RESULTS = 20
MAX_DEPTH = 6
SKIP_DIRS = {"venv", "node_modules", "__pycache__", ".git", "AppData", "$Recycle.Bin"}


def file_search(filename: str) -> str:
    """
    Search for files by name within the user's home folder (includes
    Desktop, Documents, Downloads, Pictures, etc). Does not touch system
    folders outside the user's profile, and cannot delete or open files.

    Args:
        filename: Full or partial filename to search for (case-insensitive).

    Returns:
        A list of matching file paths, capped at 20 results.
    """
    filename = filename.strip().lower()

    if not filename:
        return "I need a filename or part of one to search for."

    matches = []

    for root, dirs, files in os.walk(HOME_DIR):
        depth = root[len(HOME_DIR):].count(os.sep)
        if depth >= MAX_DEPTH:
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for f in files:
            if filename in f.lower():
                matches.append(os.path.join(root, f))
                if len(matches) >= MAX_RESULTS:
                    break

        if len(matches) >= MAX_RESULTS:
            break

    if not matches:
        return f"No files found matching '{filename}'."

    return f"Found {len(matches)} file(s):\n" + "\n".join(matches)
