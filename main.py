from pathlib import Path

from brain import ask_ai
from memory import load_company_context

MEMORY_FILE = Path("user.txt")

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("Finally... we meet.")
print()

if MEMORY_FILE.exists():
    name = MEMORY_FILE.read_text(encoding="utf-8").strip()
    print(f"Welcome back, {name}.")
else:
    name = input("What should I call you? ").strip() or "Partner"
    MEMORY_FILE.write_text(name, encoding="utf-8")
    print(f"I'll remember you, {name}.")

print("I'm Project Genesis.")
print("Type 'exit' to stop.")
print()

while True:
    command = input(f"{name}: ").strip()

    if command.lower() == "exit":
        print("Genesis: Until next time.")
        break

    if not command:
        continue

    try:
        company_context = load_company_context()

        prompt = f"""
You are Project Genesis, Harshit's AI business partner.

{company_context}

Harshit's request:
{command}

Give practical, simple, step-by-step answers.
"""

        response = ask_ai(prompt)

        print()
        print("Genesis:")
        print(response)
        print()

    except Exception as error:
        print()
        print("Genesis could not contact the AI brain.")
        print("Error:", error)
        print()