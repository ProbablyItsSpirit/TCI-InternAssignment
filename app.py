import pandas as pd
from utils import calculate_days_overdue, determine_stage

df = pd.read_csv("invoices.csv")

df["days_overdue"] = df["due_date"].apply(calculate_days_overdue)
df["stage"] = df["days_overdue"].apply(determine_stage)

print(df)