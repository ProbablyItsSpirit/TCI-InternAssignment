import streamlit as st
import pandas as pd

from agents.escalation_agent import (
    calculate_days_overdue,
    determine_stage
)

from agents.email_agent import generate_followup_email

st.set_page_config(
    page_title="Finance Follow-Up Agent",
    layout="wide"
)

st.title("Finance Credit Follow-Up Email Agent")

df = pd.read_csv("invoices.csv")

df["days_overdue"] = df["due_date"].apply(calculate_days_overdue)

df["stage"] = df["days_overdue"].apply(determine_stage)

# Dashboard

st.subheader("Invoice Dashboard")

st.dataframe(df)

# Metrics

total = len(df)

pending = len(df[df["days_overdue"] > 0])

escalated = len(df[df["stage"] == "Escalation"])

col1, col2, col3 = st.columns(3)

col1.metric("Total Invoices", total)

col2.metric("Pending Follow-Ups", pending)

col3.metric("Escalated Cases", escalated)

# Generate Emails

st.subheader("AI Follow-Up Generator")

if st.button("Run Follow-Up Agent"):

    for _, row in df.iterrows():

        if row["stage"] != "Escalation" and row["days_overdue"] > 0:

            email = generate_followup_email(row)

            with st.expander(f"{row['client_name']} - {row['invoice_no']}"):

                st.write(f"### Subject")
                st.write(email["subject"])

                st.write(f"### Body")
                st.write(email["body"])

                st.write(f"### Tone")
                st.write(email["tone"])

# Escalated Cases

st.subheader("Escalated Cases")

escalated_df = df[df["stage"] == "Escalation"]

st.dataframe(escalated_df)