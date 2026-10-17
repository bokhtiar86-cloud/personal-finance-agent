import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(
    page_title="Personal Finance Agent",
    page_icon="💰"
)

st.title("💰 Personal Finance Agent")
st.write("Ask questions about your spending.")

uploaded_file = st.file_uploader(
    "Upload your transactions CSV",
    type=["csv"]
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Your Transactions")
    st.dataframe(df, use_container_width=True)

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(
            df["amount"], errors="coerce"
        )

        expenses = df[df["amount"] < 0]["amount"].abs().sum()
        income = df[df["amount"] > 0]["amount"].sum()

        col1, col2 = st.columns(2)
        col1.metric("Total Expenses", f"{expenses:.2f}")
        col2.metric("Total Income", f"{income:.2f}")

    question = st.chat_input("Ask about your finances...")

    if question:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            st.error("GEMINI_API_KEY not found in .env")
        else:
            try:
                client = genai.Client(api_key=api_key)

                prompt = f"""
                Answer the user's question using only this transaction data.
                Do not invent missing information.

                Transaction data:
                {df.to_json(orient="records", date_format="iso")}

                User question: {question}
                """

                with st.spinner("Analyzing your transactions..."):
                    response = client.models.generate_content(
                        model="gemini-flash-latest",
                        contents=prompt
                    )

                st.markdown(response.text or "No response received.")

            except Exception as e:
                st.error(f"Something went wrong: {e}")
else:
    st.info("Upload your transactions.csv file to get started.")