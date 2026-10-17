import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API key
load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# Load transaction data
df = pd.read_csv("transactions.csv")
df["date"] = pd.to_datetime(df["date"])
df["amount"] = pd.to_numeric(df["amount"])


# TOOL 1: Total spending in a category
def get_total_spending(category: str, month: str) -> dict:
    """Calculate total expenses for a category in YYYY-MM format."""

    data = df.copy()
    data.columns = data.columns.str.strip().str.lower()

    if "category" not in data.columns:
        return {
            "error": "Category column missing from transactions.csv"
        }

    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    data["category"] = data["category"].fillna("").astype(str).str.strip()

    mask = (
        (data["amount"] < 0)
        & (data["date"].dt.strftime("%Y-%m") == month)
        & (data["category"].str.casefold() == category.strip().casefold())
    )

    total = round(data.loc[mask, "amount"].abs().sum(), 2)

    return {
        "category": category,
        "month": month,
        "total_spending": total
    
    }


# TOOL 2: Top spending categories
def get_top_categories(month: str) -> dict:
    """Return spending categories ranked by total spending."""
    data = df[
        (df["amount"] < 0)
        & (df["date"].dt.strftime("%Y-%m") == month)
    ]

    totals = (
        data.assign(amount=data["amount"].abs())
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    return {
        "month": month,
        "top_categories": [
            {"category": category, "total": round(total, 2)}
            for category, total in totals.items()
        ]
    }


# TOOL 3: Compare spending between two months
def compare_months(month1: str, month2: str) -> dict:
    """Compare total expenses for two months in YYYY-MM format."""

    def monthly_total(month):
        data = df[
            (df["amount"] < 0)
            & (df["date"].dt.strftime("%Y-%m") == month)
        ]
        return round(data["amount"].abs().sum(), 2)

    total1 = monthly_total(month1)
    total2 = monthly_total(month2)

    return {
        "month1": month1,
        "spending1": total1,
        "month2": month2,
        "spending2": total2,
        "difference": round(total2 - total1, 2)
    }


# Register tools for Gemini
tools = [
    get_total_spending,
    get_top_categories,
    compare_months
]

# Ask Gemini a question
question = input("Ask about your expenses: ")

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=question,
    config=types.GenerateContentConfig(
        tools=tools,
        temperature=0
    )
)

# Execute tool calls and send results back to Gemini
while response.function_calls:
    results = []

    for call in response.function_calls:
        print(f"Calling tool: {call.name}")

        if call.name == "get_total_spending":
            result = get_total_spending(**call.args)

        elif call.name == "get_top_categories":
            result = get_top_categories(**call.args)

        elif call.name == "compare_months":
            result = compare_months(**call.args)

        else:
            result = {"error": "Unknown tool"}

        results.append(
            types.Part.from_function_response(
                name=call.name,
                response=result,
                id=call.id
            )
        )

    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=question)]
            ),
            response.candidates[0].content,
            types.Content(role="user", parts=results)
        ],
        config=types.GenerateContentConfig(
            tools=tools,
            temperature=0
        )
    )

print("\nAssistant:")
print(response.text)