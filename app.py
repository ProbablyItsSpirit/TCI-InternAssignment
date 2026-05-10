import streamlit as st
import pandas as pd
from utils import calculate_days_overdue, determine_stage

st.set_page_config(page_title="Finance Follow-Up Agent", layout="wide")

st.title("Finance Credit Follow-Up Email Agent")

df = pd.read_csv("invoices.csv")

df["days_overdue"] = df["due_date"].apply(calculate_days_overdue)
df["stage"] = df["days_overdue"].apply(determine_stage)

st.subheader("Invoice Dashboard")
st.dataframe(df)