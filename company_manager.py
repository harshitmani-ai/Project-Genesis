from pathlib import Path


MEMORY_FOLDER = Path("company_memory")


def read_memory_file(file_name):
    path = MEMORY_FOLDER / file_name

    if not path.exists():
        return "No information available."

    content = path.read_text(encoding="utf-8").strip()

    if not content:
        return "No information available."

    return content


def main():
    print("=== Company Memory ===")

    files = {
        "1": "mission.md",
        "2": "constitution.md",
        "3": "products.md",
        "4": "roadmap.md",
        "5": "revenue.md",
        "6": "decisions.md",
    }

    while True:
        print("\nChoose:")
        print("1. Mission")
        print("2. Constitution")
        print("3. Products")
        print("4. Roadmap")
        print("5. Revenue")
        print("6. Decisions")
        print("0. Exit")

        choice = input("\nChoice: ").strip()

        if choice == "0":
            print("Company Memory closed.")
            break

        if choice not in files:
            print("Invalid choice.")
            continue

        print("\n----------------------------")
        print(read_memory_file(files[choice]))
        print("----------------------------")


if __name__ == "__main__":
    main()