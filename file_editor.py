from datetime import datetime
from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).resolve().parent
BACKUP_FOLDER = PROJECT_ROOT / "backups"

ALLOWED_FILE_TYPES = {
    ".py",
    ".txt",
    ".md",
    ".json",
}


def get_safe_project_file(file_name):
    file_path = (PROJECT_ROOT / file_name).resolve()

    if PROJECT_ROOT not in file_path.parents:
        raise ValueError("File must be inside the Project Genesis folder.")

    if file_path.suffix.lower() not in ALLOWED_FILE_TYPES:
        raise ValueError(
            f"File type '{file_path.suffix}' is not allowed."
        )

    return file_path


def create_backup(file_path):
    if not file_path.exists():
        return None

    BACKUP_FOLDER.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_name = (
        f"{file_path.stem}_{timestamp}{file_path.suffix}.backup"
    )

    backup_path = BACKUP_FOLDER / backup_name

    shutil.copy2(file_path, backup_path)

    return backup_path


def update_file(file_name, new_content):
    if not file_name.strip():
        raise ValueError("File name cannot be empty.")

    if not new_content.strip():
        raise ValueError("New file content cannot be empty.")

    file_path = get_safe_project_file(file_name)

    backup_path = create_backup(file_path)

    file_path.write_text(
        new_content,
        encoding="utf-8",
    )

    saved_content = file_path.read_text(encoding="utf-8")

    if saved_content != new_content:
        raise RuntimeError("File verification failed after saving.")

    return {
        "file_path": str(file_path),
        "backup_path": (
            str(backup_path)
            if backup_path
            else None
        ),
        "updated": True,
    }


def main():
    print("=== Project Genesis File Editor ===")

    file_name = input("File to update: ").strip()

    print(
        "\nPaste the complete approved code below."
    )
    print(
        "When finished, type END_OF_FILE on a new line."
    )

    content_lines = []

    while True:
        line = input()

        if line == "END_OF_FILE":
            break

        content_lines.append(line)

    new_content = "\n".join(content_lines) + "\n"

    try:
        result = update_file(
            file_name=file_name,
            new_content=new_content,
        )

        print("\nFile updated successfully.")
        print(f"File: {result['file_path']}")

        if result["backup_path"]:
            print(f"Backup: {result['backup_path']}")
        else:
            print("Backup: No previous file existed.")

    except Exception as error:
        print(f"\nUpdate failed: {error}")


if __name__ == "__main__":
    main()