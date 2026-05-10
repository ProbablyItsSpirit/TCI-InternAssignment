def get_email_prompt(stage, client, invoice, amount, due_date, days, payment_link):

    return f"""
You are a professional finance collections assistant.

Generate a {stage} follow-up email.

Client Name: {client}
Invoice Number: {invoice}
Amount Due: ₹{amount}
Due Date: {due_date}
Days Overdue: {days}
Payment Link: {payment_link}

Rules:
- Match the tone required for {stage}
- Keep it professional
- Keep under 150 words
- Mention payment clearly
- Avoid hallucinations

Return ONLY valid JSON:
{{
    "subject": "...",
    "body": "...",
    "tone": "{stage}",
    "stage": "{stage}"
}}
"""