import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from uuid import uuid4
from services.database_service import (
    init_db,
    log_email,
    fetch_logs,
    fetch_invoices
)
from services.invoice_db_service import (
    update_last_email_sent,
    update_next_followup,
    increment_followup_count,
    should_send_followup
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
df = fetch_invoices()

df["days_overdue"] = df["due_date"].apply(calculate_days_overdue)

df["stage"] = df["days_overdue"].apply(determine_stage)
# Sidebar Filters

st.sidebar.header("Scheduling Controls")

mail_frequency = st.sidebar.selectbox(
    "Send Follow-Up Every",
    [1, 2, 3, 5, 7, 14, 30],
    index=4
)

st.sidebar.caption(
    f"Follow-up emails will be scheduled every {mail_frequency} day(s)"
)

selected_clients = st.sidebar.multiselect(
    "Select Clients To Send",
    df["client_name"].unique(),
    default=df["client_name"].unique()
)

dry_run = st.sidebar.toggle(
    "Dry Run Mode",
    value=True
)

if dry_run:
    st.sidebar.success("Sandbox Mode Enabled")
else:
    st.sidebar.warning("Real Email Sending Enabled")


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

# Color mapping for stages
stage_colors = {
    "Stage 1": "#2ca02c",
    "Stage 2": "#ffcc00",
    "Stage 3": "#ff7f0e",
    "Stage 4": "#d62728",
    "Escalation": "#000000"
}

# Stage distribution (colored by stage)
stage_df = (
    filtered_df.groupby("stage").size().reset_index(name="count")
)

stage_order_df = stage_df.sort_values("count", ascending=False)
ordered_stages = [s for s in stage_order_df["stage"].tolist() if s != "Escalation"]
if "Escalation" in stage_df["stage"].tolist():
    ordered_stages.append("Escalation")

colors_list = [stage_colors.get(s, "#777777") for s in ordered_stages]

stage_chart = alt.Chart(stage_df).mark_bar().encode(
    x=alt.X("stage:N", sort=ordered_stages),
    y="count:Q",
    color=alt.Color(
        "stage:N",
        scale=alt.Scale(domain=ordered_stages, range=colors_list),
        legend=alt.Legend(title="Stage")
    ),
    tooltip=["stage:N", "count:Q"]
).properties(title="Stage Distribution")

st.altair_chart(stage_chart, use_container_width=True)

# Overdue day counts colored by stage (stacked)
overdue_df = (
    filtered_df.groupby(["days_overdue", "stage"]).size().reset_index(name="count")
)

overdue_chart = alt.Chart(overdue_df).mark_bar().encode(
    x=alt.X("days_overdue:O", title="Days Overdue"),
    y=alt.Y("count:Q", title="Count"),
    color=alt.Color(
        "stage:N",
        scale=alt.Scale(domain=list(stage_colors.keys()), range=list(stage_colors.values())),
        legend=alt.Legend(title="Stage")
    ),
    tooltip=["days_overdue:O", "stage:N", "count:Q"]
).properties(title="Overdue Day Counts by Stage")

st.altair_chart(overdue_chart, use_container_width=True)

# Generate Emails

st.subheader("AI Follow-Up Generator")

if st.button("Run Follow-Up Agent"):

    generated_count = 0

    for _, row in df.iterrows():

        if row["stage"] != "Escalation" and row["days_overdue"] > 0:
            # Client Selection Filter
            if row["client_name"] not in selected_clients:
                continue

            # Scheduling Logic
            if not should_send_followup(row.get("next_followup_date")):
                continue
            
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

            # Calculate next follow-up date for scheduling (will be persisted below)
            next_followup_date = (
                datetime.today() + timedelta(days=mail_frequency)
            ).strftime("%Y-%m-%d")

            # Persist scheduling changes to invoices DB
            update_last_email_sent(row["invoice_no"])
            update_next_followup(row["invoice_no"], next_followup_date, mail_frequency)
            increment_followup_count(row["invoice_no"])

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