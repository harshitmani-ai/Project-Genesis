from pathlib import Path

CONSTITUTION_FILE = Path("constitution.md")
COMPANY_MEMORY_FILE = Path("company_memory.md")


def load_company_context():
    constitution = CONSTITUTION_FILE.read_text(encoding="utf-8")
    company_memory = COMPANY_MEMORY_FILE.read_text(encoding="utf-8")

    return f"""
COMPANY CONSTITUTION:
{constitution}

COMPANY MEMORY:
{company_memory}
"""