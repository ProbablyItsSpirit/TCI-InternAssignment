### Why I selected Task 2
Decided to do Task 2 because I found it more interesting and also has LLM orchestration and backend automation.
I've one day to build this, short on time.

### Phase 1
For AI I am going to use Gemini 1.5 either Locally/or with API.
And for simple UI streamlit ofc.

I'll work on mock data first. 
Generated Mock data like this: 

| invoice_no | client_name | amount | due_date | contact_email | follow_up_count | payment_link |
|---|---|---|---|---|---|---|
| INV-2026-001 | Some Name | AMT | DD-MM-YYYY | xyz@example.com | 1 | https://paymentlink.com/INV-2026-001 |

Replacing gemini api key with open weight llama through Nvidia
Added a basic email model structure for llm

Also a prompts file for the agents. Starting with get_email_prompt which will generate a mail to people who are overdue.
Added email_agent so it can make follow up mails.

Creating escalation agent and then removing the need of using utils.. When a seperatable structure like this is followed, the app becomes easy to edit and modular and get more customization.

Created proper llm service for it's guide

Trying llama3.3 first

#### Test - 1
Amazing till now this is what it generated:

<details>


**Client:** Priya Sharma - INV-2026-002

**Subject:**
Overdue Payment Notification for INV-2026-002

**Body:**
Dear Priya Sharma, this is a follow-up on your overdue payment of ₹78000 for Invoice INV-2026-002. The payment was due on 28-04-2026 and is now 12 days overdue. To avoid further action, please settle the amount immediately using the payment link: https://pay.company.com/INV-2026-002. We appreciate your prompt attention to this matter.

**Tone:** Stage 2

</details>

But this still requires a little prompt update for it's tone. And it kinda sounds like very robotic or ai generated.

#### Test - 2

Changed the mail generation tone successfully
Newly Generated mail:

<details>

**Client:** Priya Sharma - INV-2026-002

**Subject:**
Overdue Payment: INV-2026-002 for ₹78000

**Body:**
Dear Priya Sharma, I hope this email finds you well. I am writing to follow up on the payment for invoice INV-2026-002, which is now 12 days overdue. As per our records, the amount of ₹78000 was due on 28-04-2026. I would appreciate it if you could confirm when we can expect the payment to be made. For your convenience, you can make the payment online using the link https://pay.company.com/INV-2026-002. Please let me know the expected payment date so I can update our records accordingly. I look forward to hearing back from you soon. Best regards, [Your Name] Finance Collections Assistant

**Tone:** 
Polite but firm

**Invoice Details**
Amount Due: ₹78000
Days Overdue: 12
Due Date: 28-04-2026

</details>

But it also generated a mail with placeholder. 
AI hallucinating(sometimes) fixed and removed the place holder problem

### Phase 2
Adding SQLite logging so I can save timestamps and send status and audit trails
Noticed that all mails are right now in first person, changing it to third person


<details>
Karan Patel • INV-2026-008 • Stage 1

Payment Pending

**Subject**
Payment Reminder

**Email Body**
Dear Karan, I hope this email finds you well. I am reaching out regarding your outstanding payment for invoice INV-2026-008, which was due on 09-05-2026. I completely understand that oversights can happen, and I'm more than happy to help resolve this. To avoid any late fees, could you please complete the payment of ₹18000 using our secure payment link: https://pay.company.com/INV-2026-008 at your earliest convenience? If you have any questions or concerns, please don't hesitate to reach out. I'm here to help. Best regards, Finance Collections Team

**Tone**
Warm and friendly

**Invoice Details**
Amount Due: ₹18000

Days Overdue: 1

Due Date: 09-05-2026

</details>

fixed logs saving issue
adding exporting logs button and some color to the importance of stages
Making session_ids to keep track of mailing
streamlit chars are really good way to keep a count and by adding that the dashboard looks clean and professional 

### Phase 3
Now that I am done with building the core mail generating agent I'll work on the scheduling part
I thought of using gmail smtp as it is very simple to use and best implementation if you want to do something like this 

updated the prompt iterations
Instead of using the data csv, i moved it inside the sqllite 

Added more columns to show last mail sent date and follow_up mail freq for every person yet to pay (individual system)
also added next follow up date

Added date and time on top of dashboard

(nvm removed that don't update live)

implemented a whole clock system now based on this: 

```
import streamlit as st
import datetime
import time

st.title("Live Time and Date")

placeholder = st.empty()

# Loop to update time every second
while True:
    now = datetime.datetime.now()
    # Format date and time
    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # Update the placeholder container
    with placeholder.container():
        st.write(f"Current Time: {dt_string}")
        
    time.sleep(1)
```

nvm removed it again, ugly and not that useful

added colors to bar charts 
moved graphs side by side

The sidebar thing was not a good ux 
So I added row based invoice selection directly from dashboard

### Phase 4 - Database & Scheduling Consolidation
Consolidated and unified database schema across `logs.db`. Replaced duplicated `invoice_db_service.py` with single implementation using try/except for safe ALTER TABLE operations. Enhanced `fetch_invoices()` to select all columns including scheduling fields (`next_followup_date`, `last_email_sent`, `followup_frequency_days`). Updated dashboard to display these scheduling columns so users can track email send history and next follow-up dates per invoice.

