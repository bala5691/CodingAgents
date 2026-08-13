import os

from pathlib import Path
from langchain.tools import tool


IGNORED_DIRECTORIES = {".git", ".idea", ".vscode", "node_modules", "dist", "build", ".next", "__pycache__"}

def build_workspace_tools(workspace_path: str):
    root = Path(workspace_path).resolve()
    root.mkdir(parents=True, exist_ok=True)
    
    changed_files: set[str] = set()

    # --------------------------------------------------
    # SECURITY:
    # Force every requested file to remain under root.
    # --------------------------------------------------

    def resolve_safe_path(relative_path: str) -> Path:
        requested = Path(relative_path)
        if requested.is_absolute():
            raise ValueError( "Absolute paths are not allowed. Use paths relative to the workspace.")

        candidate = (root / requested).resolve()

        try:
            candidate.relative_to(root)
        except ValueError:
            raise ValueError(f"Path escapes workspace: {relative_path}")

        return candidate

    # ==================================================
    # LIST FILES
    # ==================================================
    @tool
    def list_files(path: str = ".") -> str:
        """
        List files under a directory in the project workspace.
        Use paths relative to the workspace root.
        """
        target = resolve_safe_path(path)

        if not target.exists():
            return f"Path does not exist: {path}"

        if target.is_file():
            return str(target.relative_to(root))

        output = []

        for item in sorted(target.rglob("*")):
            relative = item.relative_to(root)
            # Ignore large/generated directories
            if any(part in IGNORED_DIRECTORIES for part in relative.parts):
                continue

            if item.is_file(): output.append(str(relative))

            # Prevent massive context
            if len(output) >= 500: output.append("... output truncated ...")
                break

        if not output:
            return "Workspace is empty."

        return "\n".join(output)


    # ==================================================
    # READ FILE
    # ==================================================
    @tool
    def read_file(path: str) -> str:
        """
        Read a UTF-8 text file from the project workspace.
        """
        target = resolve_safe_path(path)

        if not target.exists():
            return (f"ERROR: file does not exist: {path}")

        if not target.is_file():
            return (f"ERROR: path is not a file: {path}")

        max_size = 200_000
        size = target.stat().st_size

        if size > max_size:
            return (f"ERROR: file is too large ({size} bytes).")

        try:
            return target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return (
                "ERROR: binary/non UTF-8 files "
                "cannot be read using this tool."
            )


    # ==================================================
    # WRITE FILE
    # ==================================================
    @tool
    def write_file(path: str, content: str) -> str:
        """
        Create or completely replace a UTF-8 text file
        inside the project workspace.

        Always provide paths relative to the workspace.
        """
        target = resolve_safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()

        # write temporary file first, then replace.
        temp_path = Path(str(target) + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        os.replace(temp_path, target)

        relative = str(target.relative_to(root))
        changed_files.add(relative)

        operation = ("updated" if existed else "created")

        return (f"SUCCESS: {operation} {relative}")
    

    # ==================================================
    # CREATE DIRECTORY
    # ==================================================
    @tool
    def create_directory(path: str) -> str:
        """
        Create a directory inside the project workspace.
        """
        target = resolve_safe_path(path)
        target.mkdir(parents=True, exist_ok=True)

        return (f"SUCCESS: directory created: {target.relative_to(root)}")

    tools = [list_files, read_file, write_file, create_directory]

    return tools, changed_files