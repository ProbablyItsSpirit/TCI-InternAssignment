def get_email_prompt(stage, client, invoice, amount, due_date, days, payment_link):

    tone_rules = {
        "Stage 1": "Warm, friendly, understanding, assumes oversight.",
        "Stage 2": "Polite but firm. Request payment confirmation.",
        "Stage 3": "Formal and serious. Mention impact of continued delay.",
        "Stage 4": "Highly professional, urgent, and compliance-focused. Mention that the case may be forwarded for manual/legal review if unresolved."
    }

    cta_rules = {
        "Stage 1": "Ask client to complete payment using the payment link.",
        "Stage 2": "Request confirmation of payment date.",
        "Stage 3": "Request response within 48 hours.",
        "Stage 4": "Request immediate response and settlement to avoid further escalation."
    }

    return f"""
You are an enterprise finance collections assistant.

Generate a realistic professional payment follow-up email.

EMAIL CONTEXT:
- Follow-Up Stage: {stage}
- Client Name: {client}
- Invoice Number: {invoice}
- Amount Due: ₹{amount}
- Due Date: {due_date}
- Days Overdue: {days}
- Payment Link: {payment_link}

TONE INSTRUCTIONS:
{tone_rules.get(stage, "Professional")}

CALL TO ACTION:
{cta_rules.get(stage, "Request payment")}

STRICT RULES:
- Write like a real finance/accounts receivable team
- Use natural business language
- Write in third person from the perspective of the Finance Collections Team
- Do NOT sound robotic or like a clanker, sound like a human
- Do NOT repeat information unnecessarily

- Mention invoice number naturally
- Subject lines must escalate in urgency based on the stage (Eg: "Payment Reminder" for Stage 1, "Urgent: Payment Overdue" for Stage 4)
- Keep the whole email under 200 words
- Add a professional greeting and closing
- Personalize the message
- Escalate tone appropriately based on stage
- Format the email professionally with proper spacing
- Greeting must be on a separate line
- Body paragraphs must be separated with blank lines
- Closing signature must be on separate lines
- Use newline characters naturally in the body
- Return ONLY valid raw JSON
- Do NOT wrap output in markdown
- Never use placeholders like [Your Name].
- Always sign off as:
- Finance Collections Team
- IMPORTANT:
    Return ONLY raw valid JSON.
    Do not add explanations.
    Do not add markdown.
    Do not add ```json
RETURN FORMAT:
{{
    "subject": "...",
    "body": "...",
    "tone": "{stage}",
    "stage": "{stage}"
}}
"""