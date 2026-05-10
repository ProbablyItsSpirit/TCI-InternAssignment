from datetime import datetime

def calculate_days_overdue(due_date):
    due = datetime.strptime(due_date, "%Y-%m-%d")
    today = datetime.today()
    return (today - due).days

def determine_stage(days):
    if 1 <= days <= 7:
        return "Stage 1"
    elif 8 <= days <= 14:
        return "Stage 2"
    elif 15 <= days <= 21:
        return "Stage 3"
    elif 22 <= days <= 30:
        return "Stage 4"
    elif days > 30:
        return "Escalation"
    else:
        return "Not Due"
    
