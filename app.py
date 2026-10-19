import os
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass
try:
    from google import genai
except Exception:
    genai = None

st.set_page_config(page_title="Finora | Personal Finance", page_icon="💹", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 10% 0%,#12342f 0,transparent 28%),linear-gradient(135deg,#07111f,#0b1424 55%,#0a1020);color:#f3f7fc}
[data-testid="stSidebar"]{background:#0b1728;border-right:1px solid #2a4055}
[data-testid="stSidebar"] *{color:#f3f7fc!important}
.block-container{max-width:1450px;padding-top:1.5rem;padding-bottom:3rem}
/* High-contrast fields: dark text on white backgrounds */
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stChatInput textarea,[data-baseweb="input"] input,[data-baseweb="textarea"] textarea,[data-testid="stDateInput"] input{color:#111827!important;-webkit-text-fill-color:#111827!important;background:#fff!important;caret-color:#111827!important;opacity:1!important}
.stTextInput input::placeholder,.stTextArea textarea::placeholder,.stChatInput textarea::placeholder,[data-baseweb="textarea"] textarea::placeholder{color:#526174!important;-webkit-text-fill-color:#526174!important;opacity:1!important}
[data-testid="stDateInput"] button{color:#111827!important;background:#fff!important}
label,[data-testid="stWidgetLabel"],[data-testid="stCaptionContainer"],.stMarkdown,.stText,p,li,small{color:#edf3fb}
[data-testid="stCaptionContainer"] p{color:#d3deeb!important}
[data-testid="stWidgetLabel"] p,label p{color:#f3f7fc!important}
.hero{padding:1.5rem;border:1px solid #315164;border-radius:22px;background:linear-gradient(110deg,#103b33,#13243a 65%,#102033);margin-bottom:1rem}
.hero h1{color:#fff;margin:.3rem 0}.hero p{color:#e0eaf5;margin:0}.eyebrow{color:#6cf0b7;font-weight:800;letter-spacing:.16em;font-size:.8rem}
.metric{background:linear-gradient(145deg,#17283e,#0e1b2d);border:1px solid #344b61;border-radius:18px;padding:1rem 1.1rem;min-height:112px}
.mlabel{color:#d3deeb;font-size:.82rem}.mvalue{color:#fff;font-size:clamp(1.25rem,2.5vw,1.85rem);font-weight:750;margin:.35rem 0}.mnote{color:#8cf5c1;font-size:.82rem}
div[data-testid="stForm"]{border:1px solid #344b61;border-radius:16px;padding:1rem}
.stButton>button,.stDownloadButton>button{border-radius:10px;font-weight:700;min-height:2.6rem}.stButton>button:hover,.stDownloadButton>button:hover{border-color:#6cf0b7}
hr{border-color:#344b61}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
</style>
""", unsafe_allow_html=True)


def money(value):
    """Format an amount as USD. This changes display, not the underlying amount."""
    return f"${float(value):,.2f}"


def normalize(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "description", "category", "type", "amount"])
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    aliases = {
        "date": ["date", "transaction_date", "datetime"],
        "description": ["description", "details", "note", "merchant", "title"],
        "category": ["category", "group"],
        "type": ["type", "transaction_type", "income_expense"],
        "amount": ["amount", "value", "total", "taka"],
    }
    rename = {}
    for target, options in aliases.items():
        for option in options:
            if option in df.columns:
                rename[option] = target
                break
    df = df.rename(columns=rename)
    if "amount" not in df.columns:
        raise ValueError("The CSV must contain an amount (or value/total) column.")
    if "date" not in df: df["date"] = date.today().isoformat()
    if "description" not in df: df["description"] = "Imported transaction"
    if "category" not in df: df["category"] = "Other"
    if "type" not in df: df["type"] = "Expense"
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    amount = df["amount"].astype(str).str.replace(",", "", regex=False)
    for currency in ("BDT", "USD", "$"):
        amount = amount.str.replace(currency, "", regex=False)
    df["amount"] = pd.to_numeric(amount.str.strip(), errors="coerce")
    type_map = {"income":"Income","in":"Income","salary":"Income","earning":"Income","expense":"Expense","expenses":"Expense","out":"Expense","spending":"Expense"}
    df["type"] = df["type"].astype(str).str.strip().str.lower().map(type_map).fillna("Expense")
    df["description"] = df["description"].fillna("Transaction").astype(str)
    df["category"] = df["category"].fillna("Other").astype(str)
    return df.dropna(subset=["date", "amount"]).query("amount >= 0")[["date", "description", "category", "type", "amount"]].reset_index(drop=True)


def api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("GOOGLE_API_KEY", "")
        if key: return key
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def generate_with_fallback(client, prompt):
    try:
        result = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return result.text or "The AI did not return any text. Please try again."
    except Exception as exc:
        return f"Gemini could not respond. Check your API key, model access, and quota. Details: {str(exc)[:250]}"


def month_totals(df, month):
    x = df.copy()
    if not x.empty:
        x["date"] = pd.to_datetime(x["date"], errors="coerce")
        x = x[x["date"].dt.strftime("%Y-%m") == month].copy()
    income = float(x.loc[x.type == "Income", "amount"].sum()) if not x.empty else 0.0
    expense = float(x.loc[x.type == "Expense", "amount"].sum()) if not x.empty else 0.0
    return x, income, expense


def ai_insights(df, budget, month):
    key = api_key()
    if not key: return "API key not found. Add GEMINI_API_KEY in Streamlit Cloud → app settings → Secrets."
    if genai is None: return "The google-genai package is not installed. Check requirements.txt."
    x, income, expense = month_totals(df, month)
    categories = x[x.type == "Expense"].groupby("category").amount.sum().sort_values(ascending=False).head(8).to_dict() if not x.empty else {}
    prompt = f"Act as a careful personal finance coach. In simple English, summarize monthly finances and give 3 practical actions. Currency is US dollars (USD). Month: {month}; income: {income}; expenses: {expense}; net cash flow: {income-expense}; monthly expense budget: {budget}; expense categories: {categories}. Use only these aggregates; do not invent data."
    try:
        return generate_with_fallback(genai.Client(api_key=key), prompt)
    except Exception as exc:
        return f"Gemini request failed: {exc}. Check API key, model access, and quota."


def ai_chat_answer(df, budget, month, question, history):
    key = api_key()
    if not key: return "API key not found. Add GEMINI_API_KEY in Streamlit Cloud → app settings → Secrets."
    if genai is None: return "The google-genai package is not installed. Check requirements.txt."
    x, income, expense = month_totals(df, month)
    categories = x[x.type == "Expense"].groupby("category").amount.sum().sort_values(ascending=False).to_dict() if not x.empty else {}
    context = f"Selected month: {month}; currency: USD; total income: {income:.2f}; total expenses: {expense:.2f}; net cash flow: {income-expense:.2f}; monthly expense budget: {budget:.2f}; expenses by category: {categories}."
    conversation = "\n".join(f"{item['role'].upper()}: {item['content']}" for item in history[-8:])
    prompt = f"You are Team 7, a friendly personal finance coach. Answer in clear, simple English. Use only these financial facts; never invent transactions or numbers. All amounts are US dollars (USD).\nFinancial facts: {context}\nRecent conversation:\n{conversation}\nUSER'S NEW QUESTION: {question}"
    try:
        return generate_with_fallback(genai.Client(api_key=key), prompt)
    except Exception as exc:
        return f"Gemini request failed: {exc}. Check API key and model access."


# Session data is temporary; persistent storage has not been added.
if "transactions" not in st.session_state:
    st.session_state.transactions = pd.DataFrame(columns=["date", "description", "category", "type", "amount"])
if "budget" not in st.session_state: st.session_state.budget = 150.0
if "insights" not in st.session_state: st.session_state.insights = ""
if "chat_messages" not in st.session_state: st.session_state.chat_messages = []

with st.sidebar:
    st.markdown("## 💹 Finora · Team 7")
    st.caption("PERSONAL FINANCE AGENT")
    st.markdown("### Reporting month")
    chosen = st.date_input(
        "Select any date in the month",
        value=date.today().replace(day=1),
        help="Choose any date in the month you want to review.",
        format="YYYY-MM-DD",
    )
    month = chosen.strftime("%Y-%m")
    st.success(f"Selected month: {chosen.strftime('%B %Y')}")
    st.session_state.budget = st.number_input(
        "Monthly expense budget (USD)", min_value=0.0,
        value=float(st.session_state.budget), step=50.0, format="%.2f",
        help="Enter your budget in US dollars.",
    )
    st.markdown("---")
    st.caption("Privacy: Do not include personal account or card information in CSV files.")

st.markdown(f'<div class="hero"><div class="eyebrow">YOUR MONEY, IN FOCUS</div><h1>Personal Finance Dashboard</h1><p>Track cash flow, understand spending, and make confident money decisions · {month}</p></div>', unsafe_allow_html=True)
alltx = st.session_state.transactions.copy()
mtx, income, expense = month_totals(alltx, month)
net = income - expense
budget = float(st.session_state.budget)
used = expense / budget * 100 if budget > 0 else 0.0
left = budget - expense

cols = st.columns(4)
cards = [("TOTAL INCOME", money(income), "Money coming in"), ("TOTAL EXPENSES", money(expense), "Money going out"), ("NET CASH FLOW", money(net), "Income minus expenses"), ("BUDGET LEFT", money(left), f"{used:.1f}% of budget used")]
for col, (label, value, note) in zip(cols, cards):
    col.markdown(f'<div class="metric"><div class="mlabel">{label}</div><div class="mvalue">{value}</div><div class="mnote">{note}</div></div>', unsafe_allow_html=True)

overview, transactions, ai, csvtab = st.tabs(["📊 Overview", "🧾 Transactions", "✨ AI Insights", "📤 Import CSV"])

with overview:
    a, b = st.columns([1.25, 1], gap="large")
    with a:
        st.subheader("Income vs. expenses")
        cash = pd.DataFrame({"Type": ["Income", "Expense"], "Amount": [income, expense]})
        fig = px.bar(cash, x="Type", y="Amount", color="Type", color_discrete_map={"Income":"#34d399", "Expense":"#fb7185"}, template="plotly_dark", text_auto=",.2f")
        fig.update_traces(hovertemplate="%{x}<br>$%{y:,.2f}<extra></extra>")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5,r=5,t=10,b=5), showlegend=False, xaxis_title="", yaxis_title="Amount (USD)")
        st.plotly_chart(fig, use_container_width=True)
    with b:
        st.subheader("Monthly budget")
        st.progress(min(max(used / 100, 0), 1) if budget else 0)
        st.write(f"**{used:.1f}% used** · {money(expense)} of {money(budget)}")
        if budget and expense > budget: st.error(f"Budget exceeded by {money(expense-budget)}.")
        elif budget: st.success(f"Remaining within budget: {money(left)}.")
        else: st.info("Set a budget in the sidebar.")
        st.subheader("Spending by category")
        expense_rows = mtx[mtx.type == "Expense"] if not mtx.empty else mtx
        if not expense_rows.empty:
            cats = expense_rows.groupby("category", as_index=False).amount.sum().sort_values("amount", ascending=False)
            pie = px.pie(cats, names="category", values="amount", hole=.62, template="plotly_dark", color_discrete_sequence=px.colors.sequential.Teal)
            pie.update_traces(hovertemplate="%{label}<br>$%{value:,.2f}<extra></extra>")
            pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=5,b=0))
            st.plotly_chart(pie, use_container_width=True)
        else: st.info("Add expenses to see the category chart.")
    st.subheader("Recent transactions")
    if mtx.empty: st.info("Add a transaction in the Transactions tab or import a CSV.")
    else:
        recent = mtx.sort_values("date", ascending=False).head(5).copy()
        recent["date"] = recent["date"].astype(str)
        recent["amount"] = recent["amount"].map(money)
        st.dataframe(recent, use_container_width=True, hide_index=True)

with transactions:
    st.subheader("Add a transaction")
    with st.form("add_tx", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            txdate = st.date_input("Date", value=date.today(), key="tx_date")
            desc = st.text_input("Description", placeholder="e.g. Salary, groceries")
            typ = st.selectbox("Type", ["Expense", "Income"])
        with c2:
            amount = st.number_input("Amount (USD)", min_value=0.0, step=10.0, format="%.2f", help="Enter the amount in US dollars.")
            category = st.selectbox("Category", ["Food", "Transport", "Housing", "Bills", "Shopping", "Health", "Education", "Salary", "Freelance", "Savings", "Other"])
        submitted = st.form_submit_button("＋ Add transaction", use_container_width=True)
        if submitted:
            if not desc.strip() or amount <= 0: st.error("Enter a description and an amount greater than zero.")
            else:
                row = pd.DataFrame([{"date":txdate, "description":desc.strip(), "category":category, "type":typ, "amount":amount}])
                st.session_state.transactions = pd.concat([st.session_state.transactions, row], ignore_index=True)
                st.success("Transaction added.")
                st.rerun()
    st.divider()
    st.subheader("Transaction history")
    st.caption("Transactions are stored in this Streamlit session and may not persist after the session ends.")
    if alltx.empty: st.info("There are no transactions yet.")
    else:
        shown = alltx.copy()
        shown["date"] = shown["date"].astype(str)
        shown["amount"] = shown["amount"].map(money)
        st.dataframe(shown, use_container_width=True, hide_index=True)
        if st.button("Clear all transactions"):
            st.session_state.transactions = pd.DataFrame(columns=["date", "description", "category", "type", "amount"])
            st.rerun()
        export = alltx.copy()
        export["date"] = export["date"].astype(str)
        st.download_button("⬇ Download transaction CSV", data=export.to_csv(index=False).encode("utf-8-sig"), file_name=f"transactions-{month}.csv", mime="text/csv")

with ai:
    st.subheader("AI Financial Coach")
    st.caption("Only selected-month totals and category totals are sent to Gemini; transaction descriptions are not sent.")
    if st.button("✨ Generate AI insights", type="primary"):
        with st.spinner("Generating financial summary..."):
            st.session_state.insights = ai_insights(alltx, budget, month)
    if st.session_state.insights: st.markdown(st.session_state.insights)
    else: st.info("Click the button to generate AI insights.")
    st.divider()
    st.subheader("💬 Ask Team 7")
    st.write("Ask a question about your income, expenses, or budget. For example: How much of my budget is left?")
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])
    question = st.chat_input("Type your question here...")
    if question:
        st.session_state.chat_messages.append({"role":"user", "content":question})
        with st.chat_message("user"): st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Team 7 is preparing a response..."):
                answer = ai_chat_answer(alltx, budget, month, question, st.session_state.chat_messages[:-1])
            st.markdown(answer)
        st.session_state.chat_messages.append({"role":"assistant", "content":answer})
    if st.session_state.chat_messages and st.button("Clear chat"):
        st.session_state.chat_messages = []
        st.rerun()

with csvtab:
    st.subheader("Import transactions from CSV")
    st.write("Required column: `amount`. Recommended columns: `date, description, category, type, amount`.")
    st.info("Imported amounts are treated as USD. This app does not convert BDT amounts to USD automatically.")
    template = pd.DataFrame([
        {"date":date.today().isoformat(), "description":"Monthly salary", "category":"Salary", "type":"Income", "amount":3000.00},
        {"date":date.today().isoformat(), "description":"Groceries", "category":"Food", "type":"Expense", "amount":250.00},
    ])
    st.download_button("⬇ Download sample CSV", data=template.to_csv(index=False).encode("utf-8-sig"), file_name="finance-template-usd.csv", mime="text/csv")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    mode = st.radio("Import method", ["Replace current transactions", "Append to current transactions"], horizontal=True)
    if uploaded is not None:
        try:
            incoming = normalize(pd.read_csv(uploaded))
            st.write(f"{len(incoming)} valid transaction(s) found")
            preview = incoming.copy()
            preview["date"] = preview["date"].astype(str)
            preview["amount"] = preview["amount"].map(money)
            st.dataframe(preview.head(10), use_container_width=True, hide_index=True)
            if st.button("Import transactions", type="primary"):
                if mode.startswith("Replace"): st.session_state.transactions = incoming
                else: st.session_state.transactions = pd.concat([st.session_state.transactions, incoming], ignore_index=True)
                st.success("CSV imported successfully.")
                st.rerun()
        except Exception as exc: st.error(f"Error reading CSV: {exc}")

st.divider()
st.caption("Finora · Team 7 · Personal Finance Agent · Streamlit + Gemini")
