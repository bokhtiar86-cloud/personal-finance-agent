import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
# .env
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

df = pd.read_csv("transactions.csv")
print("CSV columns:", df.columns.tolist())
print(df.head())
print("Original Data:")
print(df)

expenses = df[df["amount"] < 0].copy()

def classify_expenses(descriptions):
    prompt = f"""
Classify each transaction into exactly one of these categories:
Food, Transport, Shopping, Subscription, Bills, Other.

Return only a JSON array in this format:
[
  {{"description": "original description", "category": "Food"}}
]

Transactions:
{json.dumps(descriptions, ensure_ascii=False)}
"""
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    return json.loads(response.text)

desc_list = expenses["description"].tolist()
classifications = classify_expenses(desc_list)
cat_map = {item["description"]: item["category"] for item in classifications}
expenses["category"] = expenses["description"].map(cat_map)

print("\nClassified Expenses:")
print(expenses[["description", "amount", "category"]])

print("\nTotal Expenses by Category:")
print(expenses.groupby("category")["amount"].sum().abs())
df["category"] = "Income"
df.loc[expenses.index, "category"] = expenses["category"]
df.to_csv("transactions.csv", index=False)
df["category"] = "Income"
df.loc[expenses.index, "category"] = expenses["category"]
df.to_csv("transactions.csv", index=False)