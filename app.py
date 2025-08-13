import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from core.tools import DataWorkspace
from core.agent import AnalystAgent
from core.models import ToolCall, ChartSpec

load_dotenv()
st.set_page_config(page_title="Data Analyst Agent", layout="wide")

st.title("🧠 Data Analyst Agent")
st.write("Upload a CSV/Excel file, ask questions in English, and get answers with tables & charts.")

ws = DataWorkspace()

uploaded = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])
example = st.checkbox("Use example dataset")

df = None
if uploaded is not None:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
elif example:
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=30, freq="D"),
        "visits": (pd.Series(range(30))*10 + 100).astype(int),
        "channel": ["Organic","Paid","Email","Social"]*7 + ["Organic","Paid"]
    })

if df is not None:
    ws.register_df(df, name="data")
    st.success(f"Loaded data with {len(df)} rows and {df.shape[1]} columns.")
    with st.expander("Preview (first 10 rows)"):
        st.dataframe(df.head(10))
else:
    st.info("Upload a file or tick the example to proceed.")

st.divider()

question = st.text_input("What would you like to know? (e.g., 'Show average visits by channel as a bar chart')")
run = st.button("Ask the Agent", disabled=(df is None or not question))

if run:
    agent = AnalystAgent(ws)
    plan = agent.plan(question)
    st.caption("**Agent reasoning:** " + (plan.reasoning or ""))

    results = agent.run_plan(plan.plan)

    for idx, out in enumerate(results, start=1):
        tool = out.get("tool")
        st.subheader(f"Step {idx}: {tool}")
        if tool in ("sql.query","table.show"):
            st.code(out.get("sql",""), language="sql")
            st.dataframe(out["result"])
        elif tool == "eda.summary":
            st.json(out["result"])
        elif tool == "chart.make":
            st.plotly_chart(out["figure"], use_container_width=True)
        else:
            st.write(out)

    if plan.answer_note:
        st.info(plan.answer_note)

st.divider()

st.markdown("""
### Tips
- Column names will be normalized (spaces 👉 underscores).
- You can ask for charts: "bar", "line", "scatter", "histogram", or "box".
- Examples:
  - *"What are the top 10 categories by sales?"*
  - *"Trend of visits over time as a line chart"*
  - *"Group by channel and show average visits as a bar chart"*
""")
