from pathlib import Path
import py_compile
import re
import shutil

from brain import ask_ai
from file_editor import update_file


TASK_FILE = Path("assistant_task.txt")

PROJECT_FILES = [
    Path("market_intelligence.py"),
    Path("report_saver.py"),
    Path("brain.py"),
    Path("file_editor.py"),
]


def read_project_files():
    project_context = []

    for file_path in PROJECT_FILES:
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
        else:
            content = "FILE NOT FOUND"

        project_context.append(
            f"""
===== FILE: {file_path.name} =====
{content}
===== END FILE =====
"""
        )

    return "\n".join(project_context)


def extract_python_code(response):
    match = re.search(
        r"```python\s*(.*?)```",
        response,
        re.DOTALL,
    )

    if match:
        return match.group(1).strip() + "\n"

    return None


def run_assistant(task):
    project_context = read_project_files()

    prompt = f"""
You are Assistant AI for Project Genesis.

You must work only from the real project files shown below.

Do not invent files, functions, imports, APIs, classes, folders, or architecture.

REAL PROJECT FILES:

{project_context}

TASK:

{task}

Rules:
- Read the real files before answering.
- Preserve existing code unless the task requires a change.
- Modify only the requested file.
- Return the complete updated Python file inside one python code block.
- Do not include additional code blocks.
"""

    return ask_ai(prompt)


def check_python_syntax(file_path):
    try:
        py_compile.compile(
            str(file_path),
            doraise=True,
        )

        return True, None

    except py_compile.PyCompileError as error:
        return False, str(error)


def restore_backup(file_path, backup_path):
    if backup_path:
        shutil.copy2(
            backup_path,
            file_path,
        )

        return True

    return False


def main():
    print("=== Project Genesis Assistant AI ===")

    if not TASK_FILE.exists():
        print("assistant_task.txt not found.")
        return

    task = TASK_FILE.read_text(encoding="utf-8").strip()

    if not task:
        print("assistant_task.txt is empty.")
        return

    result = run_assistant(task)

    print("\n=== Assistant AI Result ===\n")
    print(result)

    code = extract_python_code(result)

    if not code:
        print("\nNo Python code found. Nothing was changed.")
        return

    target_file = input(
        "\nEnter the file name to update, or press Enter to cancel: "
    ).strip()

    if not target_file:
        print("Update cancelled.")
        return

    approval = input(
        f"Type APPROVE to update {target_file}: "
    ).strip()

    if approval != "APPROVE":
        print("Update cancelled.")
        return

    try:
        update_result = update_file(
            file_name=target_file,
            new_content=code,
        )

        file_path = Path(update_result["file_path"])

        print("\nFile updated successfully.")
        print(f"File: {file_path}")

        backup_path = update_result["backup_path"]

        if backup_path:
            print(f"Backup: {backup_path}")
        else:
            print("Backup: No previous file existed.")

        if file_path.suffix.lower() == ".py":
            syntax_ok, syntax_error = check_python_syntax(file_path)

            if syntax_ok:
                print("Syntax check: PASSED")
            else:
                print("Syntax check: FAILED")
                print(syntax_error)

                restored = restore_backup(
                    file_path=file_path,
                    backup_path=backup_path,
                )

                if restored:
                    print("Original file restored from backup.")
                else:
                    print(
                        "No backup was available. "
                        "The invalid file was not restored."
                    )

        else:
            print("Syntax check: Skipped for non-Python file.")

    except Exception as error:
        print(f"\nUpdate failed: {error}")


if __name__ == "__main__":
    main()