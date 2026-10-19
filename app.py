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

st.set_page_config(page_title="Team 7 | Personal Finance", page_icon="💹", layout="wide")

st.markdown("""
<style>
/* Universal fix for all inputs and text fields */
input, textarea, select, [data-baseweb="input"] * {
    color: #111827 !important;
    background-color: #ffffff !important;
    -webkit-text-fill-color: #111827 !important;
}
.stTextInput input, 
.stNumberInput input, 
.stDateInput input, 
[data-baseweb="input"] input {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    background-color: #ffffff !important;
    box-shadow: 0 0 0px 1000px #ffffff inset !important;
}
/* Make input text clearly visible */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stChatInput textarea,
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    background-color: #ffffff !important;
    caret-color: #111827 !important;
}

.stChatInput textarea::placeholder,
.stTextInput input::placeholder,
[data-baseweb="textarea"] textarea::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}
.stApp {background: radial-gradient(circle at 10% 0%, #12342f 0, transparent 28%), linear-gradient(135deg,#07111f,#0b1424 55%,#0a1020); color:#e5edf7}
/* Gentle motion effects: no extra packages required */
@keyframes team7FadeUp { from {opacity:0; transform:translateY(14px)} to {opacity:1; transform:translateY(0)} }
@keyframes team7Glow { 0%,100% {box-shadow:0 0 0 rgba(52,211,153,0)} 50% {box-shadow:0 0 22px rgba(52,211,153,.12)} }
@keyframes team7Shimmer { 0% {background-position:0% 50%} 100% {background-position:200% 50%} }
@keyframes robotFloat { 0%,100% {transform:translateY(0) rotate(-1deg)} 50% {transform:translateY(-8px) rotate(1deg)} }
@keyframes robotWave { 0%,100% {transform:rotate(8deg)} 50% {transform:rotate(-18deg)} }
@keyframes robotBlink { 0%,45%,50%,100% {transform:scaleY(1)} 47% {transform:scaleY(.12)} }
.team7-robot-wrap {display:flex;align-items:center;gap:18px;padding:16px 20px;margin:8px 0 14px;border:1px solid #2b5260;border-radius:20px;background:linear-gradient(110deg,rgba(15,54,62,.9),rgba(17,34,54,.92));}
.team7-robot {position:relative;width:90px;height:96px;flex:0 0 90px;animation:robotFloat 3.2s ease-in-out infinite;}
.robot-antenna {position:absolute;left:43px;top:0;width:4px;height:15px;background:#9caec2;border-radius:4px}
.robot-antenna:before {content:'';position:absolute;left:-4px;top:-5px;width:12px;height:12px;border-radius:50%;background:#34d399;box-shadow:0 0 10px #34d399}
.robot-head {position:absolute;left:9px;top:14px;width:72px;height:52px;border:3px solid #9aabbc;border-radius:17px 17px 14px 14px;background:linear-gradient(145deg,#e4b65c,#b9792d);box-shadow:inset 0 -5px 0 rgba(80,45,14,.16)}
.robot-face {position:absolute;left:8px;top:8px;width:50px;height:29px;border-radius:10px;background:#122435;display:flex;align-items:center;justify-content:center;gap:13px}
.robot-eye {width:10px;height:13px;border-radius:50%;background:#61f4d0;box-shadow:0 0 8px #61f4d0;animation:robotBlink 4.8s infinite}
.robot-body {position:absolute;left:21px;top:69px;width:48px;height:25px;border:3px solid #9aabbc;border-radius:10px;background:#d79a43}
.robot-body:after {content:'★';position:absolute;left:15px;top:1px;color:#173447;font-size:13px}
.robot-arm {position:absolute;right:-2px;top:68px;width:19px;height:7px;border-radius:6px;background:#d79a43;transform-origin:3px 4px;animation:robotWave 1.8s ease-in-out infinite}
.robot-copy {color:#e5edf7;font-size:1rem;font-weight:700}.robot-copy small {display:block;color:#a9c3d0;font-size:.84rem;font-weight:400;margin-top:4px}
@media (prefers-reduced-motion: reduce) {.team7-robot,.robot-arm,.robot-eye {animation:none !important}}
.hero {animation:team7FadeUp .65s ease-out both, team7Glow 5s ease-in-out 1s infinite}
.metric {animation:team7FadeUp .55s ease-out both; transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease}
div[data-testid="column"]:nth-child(1) .metric {animation-delay:.06s}
div[data-testid="column"]:nth-child(2) .metric {animation-delay:.14s}
div[data-testid="column"]:nth-child(3) .metric {animation-delay:.22s}
div[data-testid="column"]:nth-child(4) .metric {animation-delay:.30s}
.metric:hover {transform:translateY(-4px);border-color:#34d399;box-shadow:0 10px 28px rgba(0,0,0,.18)}
.stButton>button,.stDownloadButton>button {transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease}
.stButton>button:hover,.stDownloadButton>button:hover {transform:translateY(-2px);box-shadow:0 7px 18px rgba(52,211,153,.18);border-color:#34d399}
[data-testid="stTabs"] button {transition:color .18s ease,background-color .18s ease}
[data-testid="stAlert"],div[data-testid="stForm"],div[data-testid="stChatMessage"] {animation:team7FadeUp .35s ease-out both}
@media (prefers-reduced-motion: reduce) { *,*::before,*::after {animation-duration:.01ms !important;animation-iteration-count:1 !important;transition-duration:.01ms !important;scroll-behavior:auto !important} }
[data-testid="stSidebar"]{background:#091525;border-right:1px solid #26374a}
.block-container{max-width:1450px;padding-top:1.5rem}
.hero{padding:1.5rem;border:1px solid #294154;border-radius:22px;background:linear-gradient(110deg,#10362f,#13243a 65%,#102033);margin-bottom:1rem}
.hero h1{color:#f8fafc;margin:.3rem 0}.hero p{color:#a9b8cc;margin:0}
.eyebrow{color:#34d399;font-weight:800;letter-spacing:.16em;font-size:.8rem}
.metric{background:linear-gradient(145deg,#142236,#0c1727);border:1px solid #29394d;border-radius:18px;padding:1rem 1.1rem;min-height:112px}
.mlabel{color:#9fb0c5;font-size:.82rem}.mvalue{color:#f8fafc;font-size:clamp(1.25rem,2.5vw,1.85rem);font-weight:750;margin:.35rem 0}
.mnote{color:#34d399;font-size:.78rem}
div[data-testid="stForm"]{border:1px solid #26374a;border-radius:16px;padding:1rem}
.stButton>button,.stDownloadButton>button{border-radius:10px;font-weight:700;min-height:2.6rem}
hr{border-color:#26374a}
/* Ensure button text and background are always visible */
.stButton>button, .stDownloadButton>button {
    color: #ffffff !important;
    background-color: #10b981 !important;
    border: 1px solid #34d399 !important;
}

/* Button hover state color */
.stButton>button:hover, .stDownloadButton>button:hover {
    color: #ffffff !important;
    background-color: #059669 !important;
    border-color: #6ee7b7 !important;
}
/* Make all text and captions in the sidebar clearly visible */
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaption {
    color: #f8fafc !important;
}

/* Fix text color for top tabs */
[data-testid="stTabs"] button {
    color: #cbd5e1 !important;
    font-weight: 600 !important;
}

/* Color for the selected or active tab */
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #34d399 !important;
}

/* Keep form labels and general text clear and legible */
.stTextInput label, .stNumberInput label, .stSelectbox label, .stDateInput label {
    color: #f8fafc !important;
}
/* Make text inside the date input visible */
[data-testid="stDateInput"] input,
[data-baseweb="input"] input {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}
/* Fix date input and calendar popup text and background visibility */
[data-baseweb="calendar"] *, 
[data-testid="stDateInput"] input,
div[data-baseweb="popover"] * {
    color: #111827 !important;
}

[data-baseweb="calendar"], div[data-baseweb="popover"] {
    background-color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

def money(n):
    return f"$ {float(n):,.2f}"

def normalize(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["date","description","category","type","amount"])
    df=df.copy()
    df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
    aliases={"date":["date","transaction_date","datetime"],"description":["description","details","note","merchant","title"],"category":["category","group"],"type":["type","transaction_type","income_expense"],"amount":["amount","value","total","taka"]}
    rename={}
    for target,opts in aliases.items():
        for opt in opts:
            if opt in df.columns:
                rename[opt]=target
                break
    df=df.rename(columns=rename)
    if "amount" not in df.columns:
        raise ValueError("The CSV must contain an amount (or value/total) column.")
    if "date" not in df: df["date"]=date.today().isoformat()
    if "description" not in df: df["description"]="Imported transaction"
    if "category" not in df: df["category"]="Other"
    if "type" not in df: df["type"]="Expense"
    df["date"]=pd.to_datetime(df["date"],errors="coerce").dt.date
    df["amount"] = pd.to_numeric(
    df["amount"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace("USD ", "", regex=False)
    .str.replace("$", "", regex=False)
    .str.strip(),
    errors="coerce",
)
    df["type"]=df["type"].astype(str).str.strip().str.lower().map({"income":"Income","in":"Income","salary":"Income","earning":"Income","expense":"Expense","expenses":"Expense","out":"Expense","spending":"Expense"}).fillna("Expense")
    df["description"]=df["description"].fillna("Transaction").astype(str)
    df["category"]=df["category"].fillna("Other").astype(str)
    return df.dropna(subset=["date","amount"]).query("amount >= 0")[["date","description","category","type","amount"]].reset_index(drop=True)

def api_key():
    try:
        k=st.secrets.get("GEMINI_API_KEY","") or st.secrets.get("GOOGLE_API_KEY","")
        if k: return k
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

def generate_with_fallback(client, prompt):
    """Use one lightweight model first to avoid slow sequential fallback attempts."""
    try:
        result = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )
        return result.text or "The AI did not return any text. Please try again."
    except Exception as exc:
        return (
            "Gemini could not respond. Please try again in a moment. "
            "If this keeps happening, check your API key, model access, and quota in Google AI Studio. "
            f"Error: {str(exc)[:250]}"
        )

def ai_insights(df,budget,month):
    key=api_key()
    if not key:
        return 'API key not found. Add GEMINI_API_KEY in Streamlit Cloud → Settings → Secrets.'
    if genai is None:
        return "The google-genai package is not installed. Check requirements.txt."
    x=df.copy()
    if not x.empty:
        x["date"]=pd.to_datetime(x["date"],errors="coerce")
        x=x[x["date"].dt.strftime("%Y-%m")==month]
    inc=float(x.loc[x.type=="Income","amount"].sum()) if not x.empty else 0
    exp=float(x.loc[x.type=="Expense","amount"].sum()) if not x.empty else 0
    cats=x[x.type=="Expense"].groupby("category").amount.sum().sort_values(ascending=False).head(8).to_dict() if not x.empty else {}
    prompt=f"""Act as a careful personal finance coach. In simple English, summarize the user's monthly finances and give 3 practical actions. Currency USD ($). Month: {month}; income: {inc}; expenses: {exp}; net cash flow: {inc-exp}; expense budget: {budget}; expense categories: {cats}. Use only these aggregates, do not invent data."""
    try:
        client=genai.Client(api_key=key)
        return generate_with_fallback(client, prompt)
    except Exception as e:
        return f"Gemini request failed: {e}. check the API key, model access, and quota."

def ai_chat_answer(df, budget, month, question, history):
    """Answer a user's question using only the selected month's financial totals."""
    key = api_key()
    if not key:
        return "API key not found. Add GEMINI_API_KEY in Streamlit Cloud → Settings → Secrets."
    if genai is None:
        return "The google-genai package is not installed. Check requirements.txt."

    x = df.copy()
    if not x.empty:
        x["date"] = pd.to_datetime(x["date"], errors="coerce")
        x = x[x["date"].dt.strftime("%Y-%m") == month]
    income = float(x.loc[x.type == "Income", "amount"].sum()) if not x.empty else 0
    expenses = float(x.loc[x.type == "Expense", "amount"].sum()) if not x.empty else 0
    categories = (x[x.type == "Expense"].groupby("category").amount.sum().sort_values(ascending=False).to_dict()
                  if not x.empty else {})

    # Send financial totals and category totals only; transaction descriptions are not sent.
    context = (
        f"Selected month: {month}; currency: USD ($); total income: {income:.2f}; "
        f"total expenses: {expenses:.2f}; net cash flow: {income-expenses:.2f}; "
        f"monthly expense budget: {budget:.2f}; expenses by category: {categories}."
    )
    conversation = "\n".join(
        f"{item['role'].upper()}: {item['content']}" for item in history[-8:]
    )
    prompt = f"""You are Team 7, a friendly animated robot and careful personal finance coach. Start only the first greeting of a new conversation with: "Welcome to our new innovation! I'm your Team 7 robot. Ask me anything about your income, expenses, or budget." Do not repeat the welcome in every reply. Answer the user's question in clear, simple language. Use only the financial facts below; never invent transactions or numbers. If the data cannot answer a question, say so Currency is US dollars (USD). Display all monetary amounts with the $ symbol.

Financial facts: {context}

Recent conversation:
{conversation}

USER'S NEW QUESTION: {question}"""
    try:
        client = genai.Client(api_key=key)
        return generate_with_fallback(client, prompt)
    except Exception as e:
        return f"Gemini request failed: {e}. Please try again and check the API key and model access."

if "transactions" not in st.session_state:
    st.session_state.transactions=pd.DataFrame(columns=["date","description","category","type","amount"])
if "budget" not in st.session_state: st.session_state.budget=150.0
if "insights" not in st.session_state: st.session_state.insights=""
if "chat_messages" not in st.session_state: st.session_state.chat_messages=[]

with st.sidebar:
    st.markdown("## 💹 Team 7")
    st.caption("PERSONAL FINANCE AGENT")
    chosen=st.date_input("Select month",value=date.today().replace(day=1))
    month=chosen.strftime("%Y-%m")
    st.number_input(
    "Monthly expense budget (USD)",
    min_value=0.0,
    step=10.0,
    format="%.2f",
    key="budget",
)
    st.markdown("---")
    st.caption("Do not include personal account or card information in the CSV.")

st.markdown(f'<div class="hero"><div class="eyebrow">YOUR MONEY, IN FOCUS</div><h1>Personal Finance Dashboard</h1><p>Track cash flow, understand spending, and make confident money decisions · {month}</p></div>',unsafe_allow_html=True)

alltx=st.session_state.transactions.copy()
if not alltx.empty:
    alltx["date"]=pd.to_datetime(alltx["date"],errors="coerce").dt.date
    mtx=alltx[pd.to_datetime(alltx["date"]).dt.strftime("%Y-%m")==month].copy()
else: mtx=alltx.copy()
income=float(mtx.loc[mtx.type=="Income","amount"].sum()) if not mtx.empty else 0
expense=float(mtx.loc[mtx.type=="Expense","amount"].sum()) if not mtx.empty else 0
net=income-expense
budget=float(st.session_state.budget)
used=expense/budget*100 if budget else 0
left=budget-expense

cols=st.columns(4)
cards=[("TOTAL INCOME",money(income),"Money coming in"),("TOTAL EXPENSES",money(expense),"Money going out"),("NET CASH FLOW",money(net),"Income minus expenses"),("BUDGET LEFT",money(left),f"{used:.1f}% budget used")]
for col,(label,value,note) in zip(cols,cards):
    col.markdown(f'<div class="metric"><div class="mlabel">{label}</div><div class="mvalue">{value}</div><div class="mnote">{note}</div></div>',unsafe_allow_html=True)

overview,transactions,ai,csvtab=st.tabs(["📊 Overview","🧾 Transactions","✨ AI Insights","📤 Import CSV"])

with overview:
    a,b=st.columns([1.25,1],gap="large")
    with a:
        st.subheader("Income vs. expenses")
        cash=pd.DataFrame({"Type":["Income","Expense"],"Amount":[income,expense]})
        fig=px.bar(cash,x="Type",y="Amount",color="Type",color_discrete_map={"Income":"#34d399","Expense":"#fb7185"},template="plotly_dark",text_auto=",.0f")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=5,r=5,t=10,b=5),showlegend=False,xaxis_title="",yaxis_title="Amount (USD)")
        st.plotly_chart(fig,use_container_width=True)
    with b:
        st.subheader("Monthly budget")
        st.progress(min(max(used/100,0),1) if budget else 0)
        st.write(f"**{used:.1f}% used** · {money(expense)} of {money(budget)}")
        if budget and expense>budget: st.error(f"Budget exceeded by {money(expense-budget)}।")
        elif budget: st.success(f"Remaining within budget: {money(left)}।")
        else: st.info("Set a budget in the sidebar.")
        st.subheader("Spending by category")
        expenses=mtx[mtx.type=="Expense"] if not mtx.empty else mtx
        if not expenses.empty:
            cats=expenses.groupby("category",as_index=False).amount.sum().sort_values("amount",ascending=False)
            pie=px.pie(cats,names="category",values="amount",hole=.62,template="plotly_dark",color_discrete_sequence=px.colors.sequential.Teal)
            pie.update_layout(paper_bgcolor="rgba(0,0,0,0)",margin=dict(l=0,r=0,t=5,b=0))
            st.plotly_chart(pie,use_container_width=True)
        else: st.info("Add expenses to see the category chart.")
    st.subheader("Recent transactions")
    if mtx.empty: st.info("Add a transaction in the Transactions tab or import a CSV.")
    else:
        recent=mtx.sort_values("date",ascending=False).head(5).copy()
        recent["date"]=recent["date"].astype(str)
        st.dataframe(recent,use_container_width=True,hide_index=True)

with transactions:
    st.subheader("Add a transaction")
    with st.form("add_tx",clear_on_submit=True):
        c1,c2=st.columns(2)
        with c1:
            txdate=st.date_input("Date",value=date.today())
            desc=st.text_input("Description",placeholder="e.g. Salary, groceries")
            typ=st.selectbox("Type",["Expense","Income"])
        with c2:
            amount = st.number_input(
                "Amount (USD)",
                min_value=0.0,
                step=10.0,
                format="%.2f",
                key="transaction_amount_input",
            )
            category = st.selectbox(
                "Category",
                [
                    "Food", "Transport", "Housing", "Bills",
                    "Shopping", "Health", "Education", "Salary",
                    "Freelance", "Savings", "Other"
                ]
            )
        submit=st.form_submit_button("＋ Add transaction",use_container_width=True)
        if submit:
            if not desc.strip() or amount<=0: st.error("Enter a description and an amount greater than zero.")
            else:
                row=pd.DataFrame([{"date":txdate,"description":desc.strip(),"category":category,"type":typ,"amount":amount}])
                st.session_state.transactions=pd.concat([st.session_state.transactions,row],ignore_index=True)
                st.success("Transaction added.")
                st.rerun()
    st.divider()
    st.subheader("Transaction history")
    st.caption("Edit cells directly, then save. Select rows to delete.")

    if st.session_state.transactions.empty:
        st.info("There are no transactions yet.")
    else:
        tx = st.session_state.transactions.copy().reset_index(drop=True)
        tx.insert(0, "Select", False)

        edited = st.data_editor(
            tx,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="transaction_history_editor",
            column_config={
                "Select": st.column_config.CheckboxColumn("Select"),
                "date": st.column_config.DateColumn("Date"),
                "description": st.column_config.TextColumn("Description"),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    options=[
                        "Food", "Transport", "Housing", "Bills",
                        "Shopping", "Health", "Education", "Salary",
                        "Freelance", "Savings", "Other"
                    ],
                ),
                "type": st.column_config.SelectboxColumn(
                    "Type", options=["Income", "Expense"]
                ),
                "amount": st.column_config.NumberColumn(
                    "Amount (USD)", min_value=0.0, format="%.2f"
                ),
            },
        )

        save_col, delete_col = st.columns(2)

        with save_col:
            if st.button("💾 Save edits", key="save_tx_edits"):
                try:
                    saved = normalize(edited.drop(columns=["Select"]))
                    st.session_state.transactions = saved
                    st.session_state.insights = ""
                    st.session_state.chat_messages = []
                    st.success("Transactions updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Could not save: {e}")

        with delete_col:
            if st.button("🗑️ Delete selected", key="delete_tx_rows"):
                selected = edited["Select"].fillna(False).astype(bool)

                if selected.any():
                    st.session_state.transactions = (
                        edited.loc[~selected]
                        .drop(columns=["Select"])
                        .pipe(normalize)
                        .reset_index(drop=True)
                    )
                    st.session_state.insights = ""
                    st.session_state.chat_messages = []
                    st.rerun()
                else:
                    st.warning("Please select at least one transaction.")

        st.download_button(
            "⬇ Download updated CSV",
            data=st.session_state.transactions.to_csv(index=False).encode("utf-8-sig"),
            file_name="transactions.csv",
            mime="text/csv",
        )

with ai:
    st.subheader("AI Financial Coach")
    st.caption("Only monthly income totals, expense totals, and category totals are sent to Gemini; transaction descriptions are not sent.")
    if st.button("✨ Generate AI insights",type="primary"):
        with st.spinner("Generating financial summary..."):
            st.session_state.insights=ai_insights(alltx,budget,month)
    if st.session_state.insights: st.markdown(st.session_state.insights)
    else: st.info("Click the button to generate AI insights.")

    st.divider()
    st.markdown("""
    <div class="team7-robot-wrap">
      <div class="team7-robot" aria-label="Animated Team 7 robot">
        <div class="robot-antenna"></div>
        <div class="robot-head"><div class="robot-face"><span class="robot-eye"></span><span class="robot-eye"></span></div></div>
        <div class="robot-body"></div><div class="robot-arm"></div>
      </div>
      <div class="robot-copy">Welcome to our new innovation! 🤖<small>I'm the Team 7 robot. Ask me about your income, expenses, or budget.</small></div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🤖 Talk to Team 7", type="primary", key="talk_to_team7"):
        st.session_state.robot_welcome = True
    if st.session_state.get("robot_welcome", False):
        st.info("Welcome to our new innovation! I'm your Team 7 robot. Ask me anything about your income, expenses, or budget.")
    st.subheader("💬 Ask Team 7")
    st.write("Ask any question about your income and expenses. For example: How much of my budget is left? Or which category has the highest spending?")
    st.caption("Privacy: Only the selected month’s total income, total expenses, budget, and category totals are sent in chat. Transaction descriptions are not sent.")
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Type your question here...")
    if question:
        st.session_state.chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Team 7 is preparing a response..."):
                answer = ai_chat_answer(alltx, budget, month, question, st.session_state.chat_messages[:-1])
            st.markdown(answer)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
    if st.session_state.chat_messages and st.button("Clear chat"):
        st.session_state.chat_messages=[]
        st.rerun()

with csvtab:
    st.subheader("Import transactions from CSV")
    st.write("Recommended columns: date, description, category, type, amount. The amount column is required.")
    template=pd.DataFrame([{"date":date.today().isoformat(),"description":"Monthly salary","category":"Salary","type":"Income","amount":30000},{"date":date.today().isoformat(),"description":"Groceries","category":"Food","type":"Expense","amount":2500}])
    st.download_button("⬇ Download sample CSV",data=template.to_csv(index=False).encode("utf-8-sig"),file_name="finance-template.csv",mime="text/csv")
    uploaded=st.file_uploader("Choose a CSV file",type=["csv"])
    mode=st.radio("Import method",["Replace current transactions","Append to current transactions"],horizontal=True)
    if uploaded:
        try:
            incoming=normalize(pd.read_csv(uploaded))
            st.write(f"{len(incoming)} valid transaction(s) found")
            st.dataframe(incoming.head(10),use_container_width=True,hide_index=True)
            if st.button("Import transactions",type="primary"):
                if mode.startswith("Replace"):
                    st.session_state.transactions=incoming
                else:
                    st.session_state.transactions=pd.concat([st.session_state.transactions,incoming],ignore_index=True)
                st.success("CSV imported successfully.")
                st.rerun()
        except Exception as e: st.error(f"Error reading CSV: {e}")

st.divider()
st.caption("Team 7 · Personal Finance Agent · Streamlit + Gemini")
