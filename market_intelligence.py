from report_saver import save_market_report
from brain import ask_ai
from memory import load_company_context


def market_research(query):
    company_context = load_company_context()

    prompt = f"""
You are Market Intelligence AI for Project Genesis.

Company Context:
{company_context}

Research this market:

{query}

==========================
MISSION
==========================

Your only responsibility is to collect and organize market evidence.

You are NOT allowed to:

- Recommend products
- Recommend markets
- Suggest what the company should build
- Make business decisions
- Act like a CEO
- Guess missing information

==========================
RULES
==========================

1. Never invent facts.
2. Never invent statistics.
3. Never invent reports.
4. Never invent surveys.
5. Never invent URLs.
6. Never invent company data.
7. Separate facts from assumptions.
8. If something cannot be confirmed, write: "Unknown"
9. If a source cannot be verified, write: "Unverified"
10. Never call something verified unless the original source was accessed.
11. If evidence is unavailable, write: "Evidence not available."
12. Do not write recommendations.
13. Do not suggest future actions.
14. Do not explain what Genesis should do.
15. Stay neutral.

==========================
RETURN FORMAT
==========================

# 1. Market Summary

Short objective overview.

# 2. Evidence Claims

For every claim include:

- Claim
- Source Name
- Report / Article Title
- Publication Year
- URL, if available
- Verification Status

# 3. Unknown Information

List everything that could not be confirmed.

# 4. Competitors

For every competitor include:

- Company
- Product
- Website, if known

# 5. Customer Problems

List only problems supported by evidence.

# 6. Source Verification Status

## Confirmed Sources

- ...

## Sources Requiring Verification

- ...

Return only the report.

Do not add introductions.
Do not add conclusions.
Do not make recommendations.
"""

    return ask_ai(prompt)


def main():
    print("=== Market Intelligence AI ===")

    query = input("Market to research: ").strip()

    if not query:
        print("Please enter a market to research.")
        return

    result = market_research(query)

    print()
    print(result)

    saved_path = save_market_report(query, result)
    print(f"\nReport saved to: {saved_path}")


if __name__ == "__main__":
    main()