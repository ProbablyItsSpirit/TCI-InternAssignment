import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from uuid import uuid4
from services.email_service import send_email
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
    should_send_followup,
    update_invoice_status
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

st.markdown(
    """
    <style>
    div[data-testid="stDataFrame"] table tbody td:first-child,
    div[data-testid="stDataFrame"] table thead th:first-child {
        position: sticky;
        left: 0;
        z-index: 2;
        background: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid4())

if "pending_approvals" not in st.session_state:
    st.session_state["pending_approvals"] = {}

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


def send_prepared_email(row, email, *, dry_run, mail_frequency, session_id):

    email_status = "DRY_RUN_SUCCESS"

    if not dry_run:
        smtp_success = send_email(
            row["contact_email"],
            email["subject"],
            email["body"]
        )

        if smtp_success:
            email_status = "EMAIL_SENT"
            update_invoice_status(row["invoice_no"], "SENT")

            next_followup_date = (
                datetime.today() + timedelta(days=mail_frequency)
            ).strftime("%Y-%m-%d")

            update_last_email_sent(row["invoice_no"])
            update_next_followup(row["invoice_no"], next_followup_date, mail_frequency)
            increment_followup_count(row["invoice_no"])
        else:
            email_status = "EMAIL_FAILED"
            update_invoice_status(row["invoice_no"], "FAILED")

    log_email(
        session_id=session_id,
        client_name=row["client_name"],
        invoice_no=row["invoice_no"],
        stage=row["stage"],
        subject=email["subject"],
        body=email["body"],
        status=email_status
    )

    return email_status


def queue_for_approval(row, email, *, session_id, source):

    invoice_no = row["invoice_no"]
    st.session_state["pending_approvals"][invoice_no] = {
        "row": dict(row),
        "email": dict(email),
        "source": source,
    }

    update_invoice_status(invoice_no, "PENDING")
    log_email(
        session_id=session_id,
        client_name=row["client_name"],
        invoice_no=invoice_no,
        stage=row["stage"],
        subject=email["subject"],
        body=email["body"],
        status="AWAITING_APPROVAL"
    )


def render_test_email_playground():

    st.subheader("Test Email Playground")
    st.caption("Create a custom invoice scenario and generate a follow-up email instantly.")

    stage_options = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Escalation"]

    with st.form("test_email_form"):
        col1, col2 = st.columns(2)

        with col1:
            test_client_name = st.text_input("Client Name", value="Neha Mehta")
            test_invoice_no = st.text_input("Invoice Number", value="INV-TEST-001")
            test_amount = st.number_input("Amount Due", min_value=0, value=145000, step=1000)
            test_stage = st.selectbox("Follow-Up Stage", stage_options, index=3)

        with col2:
            test_due_date = st.date_input("Due Date")
            test_days_overdue = st.number_input("Days Overdue", min_value=0, value=12, step=1)
            test_payment_link = st.text_input(
                "Payment Link",
                value="https://pay.company.com/INV-TEST-001"
            )
            test_contact_email = st.text_input("Recipient Email", value="")

        generate_test_email = st.form_submit_button("Generate Test Email")

    if generate_test_email:
        test_row = {
            "stage": test_stage,
            "client_name": test_client_name,
            "invoice_no": test_invoice_no,
            "amount": int(test_amount),
            "due_date": test_due_date.strftime("%d-%m-%Y"),
            "days_overdue": int(test_days_overdue),
            "payment_link": test_payment_link,
            "contact_email": test_contact_email,
        }

        st.session_state["test_email_payload"] = test_row
        st.session_state["test_email_result"] = generate_followup_email(test_row)

    if "test_email_result" in st.session_state:
        email_result = st.session_state["test_email_result"]
        payload = st.session_state.get("test_email_payload", {})

        st.markdown("### Subject")
        st.write(email_result.get("subject", ""))

        st.markdown("### Email Body")
        st.write(email_result.get("body", ""))

        st.markdown("### Tone")
        st.info(email_result.get("tone", "Unknown"))

        send_test_now = st.toggle("Send this test email", value=False)
        if send_test_now:
            recipient_email = st.text_input(
                "Recipient for Test Send",
                value=payload.get("contact_email", ""),
                key="test_send_recipient"
            )
            if st.button("Send Test Email"):
                if not recipient_email.strip():
                    st.error("Please provide a recipient email address.")
                else:
                    smtp_success = send_email(
                        recipient_email.strip(),
                        email_result.get("subject", "Test Email"),
                        email_result.get("body", "")
                    )
                    if smtp_success:
                        st.success(f"Test email sent to {recipient_email.strip()}")
                    else:
                        st.error(f"Failed to send test email to {recipient_email.strip()}")

init_db()
page = st.sidebar.radio(
    "Page",
    ["Campaign Dashboard", "Test Email Playground"],
    index=0
)

if page == "Test Email Playground":
    render_test_email_playground()
    st.stop()

df = fetch_invoices()
df["Select"] = False
df["days_overdue"] = df["due_date"].apply(calculate_days_overdue)

df["stage"] = df["days_overdue"].apply(determine_stage)
# Sidebar Filters

st.sidebar.header("Scheduling Controls")
stage_filter_order = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Escalation"]
mail_frequency = st.sidebar.selectbox(
    "Send Follow-Up Every",
    [1, 2, 3, 5, 7, 14, 30],
    index=4
)
approval_mode = st.sidebar.toggle(
    "Human Approval Mode",
    value=True
)

st.sidebar.caption(
    f"Follow-up emails will be scheduled every {mail_frequency} day(s)"
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

available_stages = [stage for stage in stage_filter_order if stage in df["stage"].unique()]

selected_stages = st.sidebar.multiselect(
    "Filter by Stages",
    options=["All Stages"] + available_stages,
    default=["All Stages"]
)

min_overdue = st.sidebar.slider(
    "Minimum Overdue Days",
    0,
    int(df["days_overdue"].max()),
    0
)

filtered_df = df.copy()

if "All Stages" not in selected_stages:
    filtered_df = filtered_df[filtered_df["stage"].isin(selected_stages)]

filtered_df = filtered_df[filtered_df["days_overdue"] >= min_overdue]



# Dashboard

st.subheader("Invoice Dashboard")
display_columns = [
    "Select",
    "client_name",
    "invoice_no",
    "amount",
    "due_date",
    "days_overdue",
    "stage",
    "last_email_sent",
    "next_followup_date",
    "follow_up_count",
    "last_status",
    "contact_email",
    "payment_link"
]

# Only show columns that exist in the dataframe
display_columns = [col for col in display_columns if col in filtered_df.columns]

select_all = st.sidebar.checkbox(
    "Select All Visible Invoices"
)
if select_all:
    filtered_df["Select"] = True
edited_df = st.data_editor(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    column_order=display_columns,
    column_config={
        "Select": st.column_config.CheckboxColumn(
            "Select",
            help="Select invoice for follow-up",
            default=False,
        )
    }
)

selected_rows = edited_df[
    edited_df["Select"] == True
]

selected_clients = selected_rows["client_name"].tolist()

st.sidebar.subheader("Selected Clients")

if selected_clients:

    st.sidebar.caption(
        f"{len(selected_clients)} client(s) selected"
    )

    st.sidebar.code(
        ", ".join(selected_clients[:5])
        + (
            " ..."
            if len(selected_clients) > 5
            else ""
        )
    )

else:

    st.sidebar.info("No clients selected")


# Metrics

total = len(df)

pending = len(df[df["days_overdue"] > 0])

escalated = len(df[df["stage"] == "Escalation"])

col1, col2, col3 = st.columns(3)

col1.metric("Total Invoices", total)

col2.metric("Pending Follow-Ups", pending)

col3.metric("Escalated Cases", escalated)
st.subheader("Upcoming Follow-Ups")

upcoming_df = df[
    df["next_followup_date"].notna()
][
    [
        "client_name",
        "invoice_no",
        "next_followup_date",
        "stage"
    ]
]

st.dataframe(
    upcoming_df,
    use_container_width=True
)
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
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.altair_chart(
        stage_chart,
        use_container_width=True
    )

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

with chart_col2:
    st.altair_chart(
        overdue_chart,
        use_container_width=True
    )

# Generate Emails

st.subheader("AI Follow-Up Generator")

st.info(
    f"{len(selected_rows)} invoice(s) selected for follow-up"
)

run_agent = st.sidebar.button(
    "Run Follow-Up Agent",
    use_container_width=True
)

retry_failed_emails = st.sidebar.button(
    "Retry Failed Emails",
    use_container_width=True
)

if run_agent:

    generated_count = 0

    for _, row in selected_rows.iterrows():

        if row["stage"] != "Escalation" and row["days_overdue"] > 0:
            # Client Selection Filter
            if row["client_name"] not in selected_clients:
                continue

            # Scheduling Logic
            if not should_send_followup(row.get("next_followup_date")):
                continue

            email = generate_followup_email(row)

            if approval_mode:
                queue_for_approval(
                    row,
                    email,
                    session_id=session_id,
                    source="campaign"
                )
                email_status = "PENDING"
            else:
                email_status = send_prepared_email(
                    row,
                    email,
                    dry_run=dry_run,
                    mail_frequency=mail_frequency,
                    session_id=session_id
                )

            if email_status == "EMAIL_SENT":
                st.success(
                    f"Email sent to {row['contact_email']}"
                )

            elif email_status == "EMAIL_FAILED":
                st.error(
                    f"Failed sending to {row['contact_email']}"
                )

            elif email_status == "PENDING" and approval_mode:
                st.warning(
                    f"Awaiting approval for {row['contact_email']}"
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

if retry_failed_emails:

    failed_rows = df[
        df["last_status"].fillna("PENDING") == "FAILED"
    ]

    if failed_rows.empty:
        st.info("No failed emails found to retry.")
    else:

        retry_count = 0

        for _, row in failed_rows.iterrows():

            if row["stage"] != "Escalation" and row["days_overdue"] > 0:
                email = generate_followup_email(row)

                if approval_mode:
                    queue_for_approval(
                        row,
                        email,
                        session_id=session_id,
                        source="retry"
                    )
                    email_status = "PENDING"
                else:
                    email_status = send_prepared_email(
                        row,
                        email,
                        dry_run=dry_run,
                        mail_frequency=mail_frequency,
                        session_id=session_id
                    )

                if email_status == "EMAIL_SENT":
                    st.success(
                        f"Retried email sent to {row['contact_email']}"
                    )
                elif email_status == "EMAIL_FAILED":
                    st.error(
                        f"Retry failed for {row['contact_email']}"
                    )
                elif email_status == "PENDING" and approval_mode:
                    st.warning(
                        f"Retry awaiting approval for {row['contact_email']}"
                    )

                retry_count += 1

        st.success(f"Retry process completed for {retry_count} failed email(s).")

if approval_mode and st.session_state["pending_approvals"]:

    st.subheader("Pending Human Approval")

    for invoice_no, payload in list(st.session_state["pending_approvals"].items()):
        row = payload["row"]
        email = payload["email"]

        with st.expander(f"{row['client_name']} • {invoice_no} • Awaiting Approval"):
            st.markdown("### Subject")
            st.markdown(email.get("subject", ""))

            st.markdown("### Email Body")
            st.markdown(email.get("body", ""))

            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button("Approve & Send", key=f"approve_{invoice_no}"):
                    status = send_prepared_email(
                        row,
                        email,
                        dry_run=dry_run,
                        mail_frequency=mail_frequency,
                        session_id=session_id
                    )

                    if status == "EMAIL_SENT":
                        st.success(f"Email sent to {row['contact_email']}")
                    elif status == "DRY_RUN_SUCCESS":
                        st.success(f"Dry run successful for {row['contact_email']}")
                    else:
                        st.error(f"Failed sending to {row['contact_email']}")

                    del st.session_state["pending_approvals"][invoice_no]
                    st.rerun()

            with action_col2:
                if st.button("Reject", key=f"reject_{invoice_no}"):
                    update_invoice_status(invoice_no, "PENDING")
                    log_email(
                        session_id=session_id,
                        client_name=row["client_name"],
                        invoice_no=invoice_no,
                        stage=row["stage"],
                        subject=email.get("subject", ""),
                        body=email.get("body", ""),
                        status="REJECTED_BY_HUMAN"
                    )
                    st.warning(f"Email rejected for {row['contact_email']}")
                    del st.session_state["pending_approvals"][invoice_no]
                    st.rerun()

# Escalated Cases

st.subheader("Escalated Cases")

escalated_df = df[df["stage"] == "Escalation"]

if not escalated_df.empty:
    st.error("Human Legal Review Required")

st.dataframe(escalated_df)

st.subheader("Delivery Analytics")

status_series = df["last_status"].fillna("PENDING")

delivery_col1, delivery_col2, delivery_col3, delivery_col4 = st.columns(4)

delivery_col1.metric("Sent", int((status_series == "SENT").sum()))
delivery_col2.metric("Failed", int((status_series == "FAILED").sum()))
delivery_col3.metric("Pending", int((status_series == "PENDING").sum()))
delivery_col4.metric("Escalated", int((df["stage"] == "Escalation").sum()))


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