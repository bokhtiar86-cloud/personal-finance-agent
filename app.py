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

st.set_page_config(page_title="Finora | Personal Finance", page_icon="💹", layout="wide")

st.markdown("""
<style>
.stApp {background: radial-gradient(circle at 10% 0%, #12342f 0, transparent 28%), linear-gradient(135deg,#07111f,#0b1424 55%,#0a1020); color:#e5edf7}
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
</style>
""", unsafe_allow_html=True)

def money(n):
    return f"৳{float(n):,.2f}"

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
        raise ValueError("CSV-তে amount (বা value/total) কলাম থাকতে হবে।")
    if "date" not in df: df["date"]=date.today().isoformat()
    if "description" not in df: df["description"]="Imported transaction"
    if "category" not in df: df["category"]="Other"
    if "type" not in df: df["type"]="Expense"
    df["date"]=pd.to_datetime(df["date"],errors="coerce").dt.date
    df["amount"]=pd.to_numeric(df["amount"].astype(str).str.replace(",","",regex=False).str.replace("৳","",regex=False),errors="coerce")
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

def ai_insights(df,budget,month):
    key=api_key()
    if not key:
        return 'API key পাওয়া যায়নি। Streamlit Cloud → Settings → Secrets-এ GEMINI_API_KEY যোগ করুন।'
    if genai is None:
        return "google-genai প্যাকেজ ইনস্টল নেই। requirements.txt পরীক্ষা করুন।"
    x=df.copy()
    if not x.empty:
        x["date"]=pd.to_datetime(x["date"],errors="coerce")
        x=x[x["date"].dt.strftime("%Y-%m")==month]
    inc=float(x.loc[x.type=="Income","amount"].sum()) if not x.empty else 0
    exp=float(x.loc[x.type=="Expense","amount"].sum()) if not x.empty else 0
    cats=x[x.type=="Expense"].groupby("category").amount.sum().sort_values(ascending=False).head(8).to_dict() if not x.empty else {}
    prompt=f"""Act as a careful personal finance coach. In simple English, summarize the user's monthly finances and give 3 practical actions. Currency BDT. Month: {month}; income: {inc}; expenses: {exp}; net cash flow: {inc-exp}; expense budget: {budget}; expense categories: {cats}. Use only these aggregates, do not invent data, and note this is general information, not professional financial advice."""
    try:
        client=genai.Client(api_key=key)
        result=client.models.generate_content(model="gemini-3.8-flash",contents=prompt)
        return result.text or "AI কোনো লেখা ফেরত দেয়নি।"
    except Exception as e:
        return f"Gemini request ব্যর্থ: {e}. API key, model access ও quota পরীক্ষা করুন।"

def ai_chat_answer(df, budget, month, question, history):
    """Answer a user's question using only the selected month's financial totals."""
    key = api_key()
    if not key:
        return "API key পাওয়া যায়নি। Streamlit Cloud → Settings → Secrets-এ GEMINI_API_KEY যোগ করুন।"
    if genai is None:
        return "google-genai প্যাকেজ ইনস্টল নেই। requirements.txt পরীক্ষা করুন।"

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
        f"Selected month: {month}; currency: BDT; total income: {income:.2f}; "
        f"total expenses: {expenses:.2f}; net cash flow: {income-expenses:.2f}; "
        f"monthly expense budget: {budget:.2f}; expenses by category: {categories}."
    )
    conversation = "\n".join(
        f"{item['role'].upper()}: {item['content']}" for item in history[-8:]
    )
    prompt = f"""You are Finora, a careful personal finance coach. Answer the user's question in clear, simple language. Use only the financial facts below; never invent transactions or numbers. If the data cannot answer a question, say so. Currency is Bangladeshi taka (BDT). Give general information, not professional financial advice.

Financial facts: {context}

Recent conversation:
{conversation}

USER'S NEW QUESTION: {question}"""
    try:
        client = genai.Client(api_key=key)
        result = client.models.generate_content(model="gemini-3.8-flash", contents=prompt)
        return result.text or "AI কোনো উত্তর ফেরত দেয়নি। আবার চেষ্টা করুন।"
    except Exception as e:
        return f"Gemini request ব্যর্থ: {e}. কিছুক্ষণ পর আবার চেষ্টা করুন এবং API key/model access পরীক্ষা করুন।"

if "transactions" not in st.session_state:
    st.session_state.transactions=pd.DataFrame(columns=["date","description","category","type","amount"])
if "budget" not in st.session_state: st.session_state.budget=15000.0
if "insights" not in st.session_state: st.session_state.insights=""
if "chat_messages" not in st.session_state: st.session_state.chat_messages=[]

with st.sidebar:
    st.markdown("## 💹 Finora")
    st.caption("PERSONAL FINANCE AGENT")
    chosen=st.date_input("মাস নির্বাচন করুন",value=date.today().replace(day=1))
    month=chosen.strftime("%Y-%m")
    st.session_state.budget=st.number_input("Monthly expense budget (৳)",min_value=0.0,value=float(st.session_state.budget),step=500.0)
    st.markdown("---")
    st.caption("CSV-তে ব্যক্তিগত account/card তথ্য রাখবেন না।")

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
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=5,r=5,t=10,b=5),showlegend=False,xaxis_title="",yaxis_title="Amount (BDT)")
        st.plotly_chart(fig,use_container_width=True)
    with b:
        st.subheader("Monthly budget")
        st.progress(min(max(used/100,0),1) if budget else 0)
        st.write(f"**{used:.1f}% used** · {money(expense)} of {money(budget)}")
        if budget and expense>budget: st.error(f"Budget ছাড়িয়েছে {money(expense-budget)}।")
        elif budget: st.success(f"Budget-এর মধ্যে বাকি {money(left)}।")
        else: st.info("Sidebar থেকে budget নির্ধারণ করুন।")
        st.subheader("Spending by category")
        expenses=mtx[mtx.type=="Expense"] if not mtx.empty else mtx
        if not expenses.empty:
            cats=expenses.groupby("category",as_index=False).amount.sum().sort_values("amount",ascending=False)
            pie=px.pie(cats,names="category",values="amount",hole=.62,template="plotly_dark",color_discrete_sequence=px.colors.sequential.Teal)
            pie.update_layout(paper_bgcolor="rgba(0,0,0,0)",margin=dict(l=0,r=0,t=5,b=0))
            st.plotly_chart(pie,use_container_width=True)
        else: st.info("খরচ যোগ করলে category chart দেখা যাবে।")
    st.subheader("Recent transactions")
    if mtx.empty: st.info("Transactions tab-এ transaction যোগ করুন বা CSV import করুন।")
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
            amount=st.number_input("Amount (BDT)",min_value=0.0,step=100.0)
            category=st.selectbox("Category",["Food","Transport","Housing","Bills","Shopping","Health","Education","Salary","Freelance","Savings","Other"])
        submit=st.form_submit_button("＋ Add transaction",use_container_width=True)
        if submit:
            if not desc.strip() or amount<=0: st.error("Description দিন এবং amount শূন্যের বেশি দিন।")
            else:
                row=pd.DataFrame([{"date":txdate,"description":desc.strip(),"category":category,"type":typ,"amount":amount}])
                st.session_state.transactions=pd.concat([st.session_state.transactions,row],ignore_index=True)
                st.success("Transaction যোগ হয়েছে।")
                st.rerun()
    st.divider()
    st.subheader("Transaction history")
    st.caption("এই সংস্করণে transaction session-এ থাকে; app restart হলে স্থায়ীভাবে সংরক্ষিত নাও থাকতে পারে।")
    if alltx.empty: st.info("এখনও transaction নেই।")
    else:
        edited=st.data_editor(alltx,use_container_width=True,hide_index=True,num_rows="dynamic",column_config={"type":st.column_config.SelectboxColumn("Type",options=["Income","Expense"]),"amount":st.column_config.NumberColumn("Amount (BDT)",min_value=0.0)})
        if st.button("Save transaction changes"):
            try:
                st.session_state.transactions=normalize(edited)
                st.success("Transaction আপডেট হয়েছে।")
                st.rerun()
            except Exception as e: st.error(str(e))
        st.download_button("⬇ Download transaction CSV",data=alltx.to_csv(index=False).encode("utf-8-sig"),file_name=f"transactions-{month}.csv",mime="text/csv")

with ai:
    st.subheader("AI financial coach")
    st.caption("Gemini-তে শুধু মাসিক মোট আয়, খরচ এবং category totals পাঠানো হয়; transaction description পাঠানো হয় না।")
    if st.button("✨ Generate AI insights",type="primary"):
        with st.spinner("Financial summary তৈরি হচ্ছে..."):
            st.session_state.insights=ai_insights(alltx,budget,month)
    if st.session_state.insights: st.markdown(st.session_state.insights)
    else: st.info("AI insight তৈরি করতে বাটনে চাপুন।")

    st.divider()
    st.subheader("💬 Ask Finora")
    st.write("আপনার আয়-ব্যয় সম্পর্কে নিজের মতো প্রশ্ন লিখুন। যেমন: আমার বাজেট কত বাকি? বা কোন খাতে খরচ বেশি?")
    st.caption("গোপনীয়তা: চ্যাটে শুধু নির্বাচিত মাসের মোট আয়, মোট খরচ, বাজেট ও category totals পাঠানো হয়। লেনদেনের বিবরণ পাঠানো হয় না।")
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("এখানে আপনার প্রশ্ন লিখুন…")
    if question:
        st.session_state.chat_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Finora উত্তর তৈরি করছে..."):
                answer = ai_chat_answer(alltx, budget, month, question, st.session_state.chat_messages[:-1])
            st.markdown(answer)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
    if st.session_state.chat_messages and st.button("চ্যাট মুছে ফেলুন"):
        st.session_state.chat_messages=[]
        st.rerun()
    st.caption("এটি সাধারণ তথ্যভিত্তিক সহায়তা; পেশাদার আর্থিক পরামর্শ নয়।")

with csvtab:
    st.subheader("Import transactions from CSV")
    st.write("প্রস্তাবিত columns: `date, description, category, type, amount`. `amount` অবশ্যই থাকতে হবে।")
    template=pd.DataFrame([{"date":date.today().isoformat(),"description":"Monthly salary","category":"Salary","type":"Income","amount":30000},{"date":date.today().isoformat(),"description":"Groceries","category":"Food","type":"Expense","amount":2500}])
    st.download_button("⬇ Download sample CSV",data=template.to_csv(index=False).encode("utf-8-sig"),file_name="finance-template.csv",mime="text/csv")
    uploaded=st.file_uploader("CSV file বেছে নিন",type=["csv"])
    mode=st.radio("Import method",["Replace current transactions","Append to current transactions"],horizontal=True)
    if uploaded:
        try:
            incoming=normalize(pd.read_csv(uploaded))
            st.write(f"{len(incoming)} valid transaction(s) পাওয়া গেছে")
            st.dataframe(incoming.head(10),use_container_width=True,hide_index=True)
            if st.button("Import transactions",type="primary"):
                if mode.startswith("Replace"):
                    st.session_state.transactions=incoming
                else:
                    st.session_state.transactions=pd.concat([st.session_state.transactions,incoming],ignore_index=True)
                st.success("CSV import হয়েছে।")
                st.rerun()
        except Exception as e: st.error(f"CSV পড়তে সমস্যা: {e}")

st.divider()
st.caption("Finora · Personal Finance Agent · Streamlit + Gemini")
