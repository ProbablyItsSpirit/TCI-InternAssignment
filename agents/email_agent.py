from prompts.prompts import get_email_prompt
from services.llm_service import generate_response

def generate_followup_email(row):

    prompt = get_email_prompt(
        row["stage"],
        row["client_name"],
        row["invoice_no"],
        row["amount"],
        row["due_date"],
        row["days_overdue"],
        row["payment_link"]
    )

    response = generate_response(prompt)

    return response