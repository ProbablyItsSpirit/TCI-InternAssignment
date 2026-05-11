import streamlit as st
import pandas as pd
from uuid import uuid4
from services.database_service import (
    init_db,
    log_email,
    fetch_logs
)
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

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid4())

session_id = st.session_state["session_id"]


def highlight_stage(stage):

    colors = {
        "Stage 1": "🟢",
        "Stage 2": "🟡",
        "Stage 3": "🟠",
        "Stage 4": "🔴",
        "Escalation": "⚫"
    }

    return colors.get(stage, "")

init_db()
df = pd.read_csv("invoices.csv")

df["days_overdue"] = df["due_date"].apply(calculate_days_overdue)

df["stage"] = df["days_overdue"].apply(determine_stage)
# Sidebar Filters

st.sidebar.header("Filters")

st.sidebar.write(f"Current Session: {session_id[:8]}")

selected_stage = st.sidebar.selectbox(
    "Filter by Stage",
    ["All"] + list(df["stage"].unique())
)

min_overdue = st.sidebar.slider(
    "Minimum Overdue Days",
    0,
    int(df["days_overdue"].max()),
    0
)

filtered_df = df.copy()

if selected_stage != "All":
    filtered_df = filtered_df[filtered_df["stage"] == selected_stage]

filtered_df = filtered_df[filtered_df["days_overdue"] >= min_overdue]



# Dashboard

st.subheader("Invoice Dashboard")

st.dataframe(filtered_df, use_container_width=True)

# Metrics

total = len(df)

pending = len(df[df["days_overdue"] > 0])

escalated = len(df[df["stage"] == "Escalation"])

col1, col2, col3 = st.columns(3)

col1.metric("Total Invoices", total)

col2.metric("Pending Follow-Ups", pending)

col3.metric("Escalated Cases", escalated)

# Analytics

st.subheader("Analytics")

stage_counts = filtered_df["stage"].value_counts()
st.caption("Stage Distribution")
st.bar_chart(stage_counts)

overdue_counts = filtered_df["days_overdue"].value_counts().sort_index()
st.caption("Overdue Day Counts")
st.bar_chart(overdue_counts)

# Generate Emails

st.subheader("AI Follow-Up Generator")

if st.button("Run Follow-Up Agent"):

    generated_count = 0

    for _, row in df.iterrows():

        if row["stage"] != "Escalation" and row["days_overdue"] > 0:

            email = generate_followup_email(row)
            log_email(
                session_id=session_id,
                client_name=row["client_name"],
                invoice_no=row["invoice_no"],
                stage=row["stage"],
                subject=email["subject"],
                body=email["body"],
                status="DRY_RUN_SUCCESS"
            )

            generated_count += 1

            with st.expander(
                f"{row['client_name']} • {row['invoice_no']} • "
                f"{highlight_stage(row['stage'])} {row['stage']}"
            ):

                st.warning("Payment Pending")

                if row["stage"] == "Stage 4":
                    st.error("Final Reminder Before Escalation")

                st.markdown("### Subject")
                st.markdown(email["subject"])

                st.markdown("### Email Body")
                st.markdown(email["body"])

                st.markdown("### Tone")
                st.info(email["tone"])

                st.markdown("### Invoice Details")

                st.write(f"Amount Due: ₹{row['amount']}")
                st.write(f"Days Overdue: {row['days_overdue']}")
                st.write(f"Due Date: {row['due_date']}")

    st.success(
        f"Dry Run Successful • {generated_count} follow-up emails generated"
    )

# Escalated Cases

st.subheader("Escalated Cases")

escalated_df = df[df["stage"] == "Escalation"]

if not escalated_df.empty:
    st.error("Human Legal Review Required")

st.dataframe(escalated_df)


def build_logs_df(logs):

    logs_df = pd.DataFrame(logs)

    column_names = [
        "ID",
        "Session ID",
        "Client",
        "Invoice",
        "Stage",
        "Subject",
        "Body",
        "Status",
        "Timestamp"
    ]

    logs_df.columns = column_names[:len(logs_df.columns)]

    return logs_df


# Audit Logs

st.subheader("Audit Trail")

logs = fetch_logs()

if logs:

    logs_df = build_logs_df(logs)

    csv = logs_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        "Download Audit Logs CSV",
        csv,
        "audit_logs.csv",
        "text/csv"
    )

    # Clean View Table

    st.dataframe(
        logs_df[
            [
                "Client",
                "Invoice",
                "Stage",
                "Status",
                "Timestamp"
            ]
        ],
        use_container_width=True
    )

    st.subheader("Session Tracking View")

    for current_session_id, group in logs_df.groupby("Session ID", sort=False):

        with st.expander(f"Session {str(current_session_id)[:8]}"):
            st.dataframe(
                group[
                    [
                        "Client",
                        "Invoice",
                        "Stage",
                        "Status",
                        "Timestamp"
                    ]
                ],
                use_container_width=True
            )

    # Detailed Logs

    st.subheader("Detailed Email Logs")

    for _, row in logs_df.iterrows():

        with st.expander(
            f"{row['Client']} • {row['Invoice']} • "
            f"{highlight_stage(row['Stage'])} {row['Stage']}"
        ):

            st.markdown("### Subject")
            st.markdown(row["Subject"])

            st.markdown("### Email Body")
            st.markdown(row["Body"])

            st.markdown("### Status")
            st.info(row["Status"])

            st.markdown("### Timestamp")
            st.write(row["Timestamp"])

else:

    st.info("No logs available.")